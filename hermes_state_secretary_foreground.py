"""Canonical current-path History/Full projections of Hermes-owned transcript rows."""

import json
import time

from agent.context_compressor import ContextCompressor, MODEL_ONLY_DISPLAY_METADATA_KEY, split_user_originated_turn
from hermes_state_secretary_identity import ConversationIdentityError


class SecretaryForegroundMixin:
    def _foreground_sessions_conn(self, conn, conversation_ref):
        rows = conn.execute(
            "SELECT session_id FROM secretary_session_bindings WHERE conversation_ref = ?", (conversation_ref,),
        ).fetchall()
        paths = []
        seen_roots = set()
        for row in rows:
            if conn.execute("SELECT 1 FROM sessions WHERE id = ?", (row[0],)).fetchone() is None:
                continue
            path = self._compression_path_conn(conn, row[0])
            if path[0] not in seen_roots:
                seen_roots.add(path[0])
                paths.append(path)
        paths.sort(key=lambda path: conn.execute("SELECT started_at FROM sessions WHERE id = ?", (path[0],)).fetchone()[0])
        return [sid for path in paths for sid in path]

    def _foreground_source_rows_conn(self, conn, conversation_ref):
        """Frozen branch references plus live path rows; no copied transcript content."""
        rows = []
        inherited = conn.execute(
            "SELECT m.*, b.is_compaction AS inherited_compaction FROM secretary_branch_messages b "
            "JOIN messages m ON m.id = b.message_id WHERE b.conversation_ref = ? "
            "AND NOT EXISTS(SELECT 1 FROM secretary_branch_exclusions x "
            "WHERE x.conversation_ref=b.conversation_ref AND x.message_uid=b.message_uid) ORDER BY b.position",
            (conversation_ref,),
        ).fetchall()
        for row in inherited:
            item = dict(row)
            item["_inherited"] = True
            rows.append(item)
        frozen_ids = {row["id"] for row in inherited}
        frozen_by_uid = {row["message_uid"]: row for row in rows}
        for sid in self._foreground_sessions_conn(conn, conversation_ref):
            for row in conn.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY id", (sid,)):
                source = frozen_by_uid.get(row["message_uid"])
                if row["id"] in frozen_ids:
                    continue
                if source is not None:
                    source["_branch_valid"] = bool(row["active"] or row["compacted"])
                    source["_branch_live_override"] = dict(row)
                    continue
                rows.append(dict(row))
        return rows

    def secretary_exclude_branch_path_conn(self, conn, session_id, *, from_message_id=None, clear_all=False, kept_messages=(), active_only=False):
        """Native branch rewrites retire inherited UIDs; deleting seed rows cannot resurrect them."""
        ref = self.resolve_conversation_ref_conn(conn, session_id)
        if conn.execute("SELECT 1 FROM secretary_branch_freezes WHERE conversation_ref=?", (ref,)).fetchone() is None:
            return
        if clear_all:
            kept = {message.get("message_uid") for message in kept_messages}
            candidates = (conn.execute("SELECT message_uid FROM messages WHERE session_id=? AND active=1", (session_id,))
                          if active_only else conn.execute("SELECT message_uid FROM secretary_branch_messages WHERE conversation_ref=?", (ref,)))
            uids = [row[0] for row in candidates if row[0] not in kept]
        else:
            uids = [row[0] for row in conn.execute(
                "SELECT message_uid FROM messages WHERE session_id=? AND active=1 AND id>=?", (session_id, from_message_id))]
        conn.executemany("INSERT OR IGNORE INTO secretary_branch_exclusions VALUES (?, ?)", [(ref, uid) for uid in uids])

    def secretary_clear_messages(self, session_id):
        def clear(conn):
            if conn.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone() is None:
                return
            self.secretary_exclude_branch_path_conn(conn, session_id, clear_all=True)
            self.secretary_preserve_session_sources_conn(conn, [session_id])
            conn.execute("DELETE FROM messages WHERE session_id=?", (session_id,))
            conn.execute("UPDATE sessions SET message_count=0, tool_call_count=0 WHERE id=?", (session_id,))
            self.secretary_reconcile_session_conn(conn, session_id)
        self._execute_write(clear)

    def secretary_preserve_branch_sources_conn(self, conn, message_ids, *, deleting_session_ids=()):
        """Use Hermes native versions only when a mutation would destroy a surviving branch's raw source."""
        deleting = set(deleting_session_ids)
        for message_id in message_ids:
            references = conn.execute(
                "SELECT DISTINCT conversation_ref FROM secretary_branch_messages WHERE message_id=?", (message_id,),
            ).fetchall()
            for reference in references:
                branches = conn.execute(
                    "SELECT s.id FROM secretary_session_bindings b JOIN sessions s ON s.id=b.session_id "
                    "WHERE b.conversation_ref=? ORDER BY s.started_at DESC", (reference[0],),
                ).fetchall()
                target = next((row[0] for row in branches if row[0] not in deleting), None)
                if target is None:
                    continue
                self._clone_message_rows(conn, [message_id], session_id=target)
                clone_id = conn.execute("SELECT MAX(id) FROM messages WHERE session_id=?", (target,)).fetchone()[0]
                conn.execute("UPDATE messages SET active=0, compacted=0 WHERE id=?", (clone_id,))
                conn.execute("UPDATE secretary_branch_messages SET message_id=? WHERE conversation_ref=? AND message_id=?",
                             (clone_id, reference[0], message_id))

    def secretary_preserve_session_sources_conn(self, conn, session_ids, *, deleting_sessions=False, active_only=False):
        ids = [row[0] for sid in session_ids for row in conn.execute(
            "SELECT m.id FROM messages m WHERE m.session_id=? "
            "AND (?=0 OR m.active=1) "
            "AND EXISTS(SELECT 1 FROM secretary_branch_messages b WHERE b.message_id=m.id)", (sid, int(active_only)))]
        self.secretary_preserve_branch_sources_conn(
            conn, ids, deleting_session_ids=session_ids if deleting_sessions else ())

    def secretary_set_user_content(self, session_id, row_id, content):
        def mutate(conn):
            row = conn.execute("SELECT 1 FROM messages WHERE id=? AND session_id=? AND role='user' AND active=1",
                               (row_id, session_id)).fetchone()
            if row is None:
                return 0
            self.secretary_preserve_branch_sources_conn(conn, [row_id])
            count = conn.execute("UPDATE messages SET content=? WHERE id=?", (self._encode_content(content), row_id)).rowcount
            self.notebook_reselect_pointer_conn(conn, self.resolve_conversation_ref_conn(conn, session_id))
            return count
        return self._execute_write(mutate)

    def _project_foreground_row(self, row, conversation_ref, *, full):
        uid = row.get("message_uid")
        if not isinstance(uid, str) or not uid:
            raise ConversationIdentityError("Transcript row has no canonical message_uid")
        content = self._decode_content(row["content"])
        metadata = self._decode_display_metadata(row.get("display_metadata")) or {}
        message = {"role": row["role"], "content": content, "display_kind": row.get("display_kind"),
                   "display_metadata": metadata, "_compressed_summary": bool(row.get("_compressed_summary"))}
        handoff, live = split_user_originated_turn(message)
        compaction = handoff is not None or bool(row.get("_compressed_summary"))
        if compaction and row["role"] != "user":
            live = ContextCompressor._strip_context_summary_handoff_message(message)
        if not full:
            if row["role"] == "system" or metadata.get(MODEL_ONLY_DISPLAY_METADATA_KEY):
                return None
            if compaction:
                if live is None:
                    return None
                content = live["content"]
        return {
            "id": row["id"], "message_id": row["id"], "message_uid": uid,
            "message_identity": {"conversation_ref": conversation_ref, "message_uid": uid},
            "timestamp": row["timestamp"], "role": row["role"], "content": content,
            "is_compaction": compaction and full, "has_user_turn": live is not None if compaction else row["role"] == "user",
            "session_id": row["session_id"],
            "display_kind": row.get("display_kind"), "display_metadata": metadata,
        }

    def _foreground_conn(self, conn, conversation_ref, *, full):
        rows = self._foreground_source_rows_conn(conn, conversation_ref)
        # The most recent physical generation decides validity AND path position:
        # a surviving tail follows its compaction boundary, and retired copies do not revive.
        winners = {}
        for index, row in enumerate(rows):
            uid = row.get("message_uid")
            winners[uid] = (index, row)
        result = []
        for _, row in sorted(winners.values(), key=lambda item: item[0]):
            if not row.get("_branch_valid", True):
                continue
            if not row.get("_inherited") and not (row.get("active") or row.get("compacted")):
                continue
            override = row.get("_branch_live_override")
            original = self._project_foreground_row(row, conversation_ref, full=full)
            carrier = full and original is not None and original["is_compaction"]
            projected = original if carrier else self._project_foreground_row(override or row, conversation_ref, full=full)
            if projected is not None:
                projected["path_position"] = len(result)
                result.append(projected)
                if full and projected["is_compaction"]:
                    live = self._project_foreground_row(override or row, conversation_ref, full=False)
                    if live is not None:
                        live["path_position"] = len(result)
                        result.append(live)
        return result

    def get_history_foreground_conn(self, conn, conversation_ref):
        return self._foreground_conn(conn, conversation_ref, full=False)

    def get_full_foreground_conn(self, conn, conversation_ref):
        rows = self._foreground_conn(conn, conversation_ref, full=True)
        snapshots = {}
        for snapshot in conn.execute(
            "SELECT * FROM secretary_notebook_snapshots WHERE conversation_ref=? ORDER BY created_at, rowid",
            (conversation_ref,),
        ):
            snapshots.setdefault(snapshot["anchor_message_uid"], []).append(dict(snapshot))
        for row in rows:
            if row["is_compaction"] or row["role"] == "system":
                continue
            annotations = []
            for snapshot in snapshots.get(row["message_uid"], ()):
                annotations.append({"kind": "noting_anchor", "message_identity": row["message_identity"],
                                    "snapshot_id": snapshot["snapshot_id"]})
                annotations.append({"kind": "notebook_snapshot", "snapshot_id": snapshot["snapshot_id"],
                                    "anchor": row["message_identity"], "payload": json.loads(snapshot["payload_json"]),
                                    "trigger_type": snapshot["trigger_type"], "runtime_profile": snapshot["runtime_profile"],
                                    "created_at": snapshot["created_at"]})
            if annotations:
                row["audit_annotations"] = annotations
        return rows

    def get_history_foreground(self, session_id=None, *, conversation_ref=None):
        ref = conversation_ref or self.resolve_conversation_ref(session_id)
        with self._read_ctx() as conn:
            return self.get_history_foreground_conn(conn, ref)

    def get_full_foreground(self, session_id=None, *, conversation_ref=None):
        ref = conversation_ref or self.resolve_conversation_ref(session_id)
        with self._read_ctx() as conn:
            return self.get_full_foreground_conn(conn, ref)

    def anchor_position_conn(self, conn, conversation_ref, message_uid):
        for row in self.get_full_foreground_conn(conn, conversation_ref):
            if row["message_uid"] == message_uid and row["role"] != "system" and not row["is_compaction"]:
                return row["path_position"]
        return None

    def get_foreground_anchor_conn(self, conn, conversation_ref):
        rows = self.get_full_foreground_conn(conn, conversation_ref)
        if not rows or rows[-1]["is_compaction"] or rows[-1]["role"] == "system":
            return None
        return rows[-1]["message_identity"]

    def get_foreground_anchor(self, session_id=None, *, conversation_ref=None):
        ref = conversation_ref or self.resolve_conversation_ref(session_id)
        with self._read_ctx() as conn:
            return self.get_foreground_anchor_conn(conn, ref)

    def normalize_message_identity_conn(self, conn, conversation_ref, message_id):
        """Physical IDs remain usable only when they prove a current logical row."""
        row = conn.execute("SELECT message_uid FROM messages WHERE id = ?", (message_id,)).fetchone()
        if row is None:
            raise ConversationIdentityError("Unknown message_id")
        for projected in self.get_history_foreground_conn(conn, conversation_ref):
            if projected["message_uid"] == row[0]:
                # UID alone is not proof: a copied UID in another Conversation is distinct.
                source_ids = {source["id"] for source in self._foreground_source_rows_conn(conn, conversation_ref)}
                if message_id in source_ids:
                    return projected["message_identity"]
        raise ConversationIdentityError("message_id is outside current Conversation path")

    def inherit_foreground_branch_conn(self, conn, parent_session_id, branch_session_id, *, through_message_uid=None):
        parent_ref = self.resolve_conversation_ref_conn(conn, parent_session_id)
        branch = self._secretary_session_conn(conn, branch_session_id)
        if not self._is_explicit_fork_child_row(branch) or branch_session_id == parent_session_id:
            raise ConversationIdentityError("Foreground inheritance requires an explicit branch")
        cfg = branch.get("model_config")
        cfg = json.loads(cfg) if isinstance(cfg, str) else (cfg or {})
        if cfg.get("_branched_from") != branch.get("parent_session_id"):
            raise ConversationIdentityError("Delegate/tool children cannot inherit main Foreground")
        if cfg.get("_branched_from") != parent_session_id:
            raise ConversationIdentityError("Caller parent differs from the native branch parent")
        branch_ref = self.resolve_conversation_ref_conn(conn, branch_session_id)
        existing = conn.execute("SELECT * FROM secretary_branch_freezes WHERE conversation_ref=?", (branch_ref,)).fetchone()
        if existing:
            if through_message_uid is not None and existing["through_message_uid"] != through_message_uid:
                raise ConversationIdentityError("Branch Foreground is already frozen at another point")
            return branch_ref
        rows = self.get_full_foreground_conn(conn, parent_ref)
        if through_message_uid is not None:
            index = next((i for i, row in enumerate(rows) if row["message_uid"] == through_message_uid
                          and not row["is_compaction"] and row["role"] != "system"), None)
            if index is None:
                raise ConversationIdentityError("Branch point is outside parent path")
            rows = rows[:index + 1]
        # A composite carrier yields a boundary and ordinary projection from ONE source row.
        source_rows = list({row["message_id"]: row for row in rows}.values())
        conn.executemany(
            "INSERT INTO secretary_branch_messages VALUES (?, ?, ?, ?, ?)",
            [(branch_ref, i, row["message_id"], row["message_uid"], int(row["is_compaction"])) for i, row in enumerate(source_rows)],
        )
        conn.execute("INSERT INTO secretary_branch_freezes VALUES (?, ?, ?, ?)",
                     (branch_ref, parent_session_id, through_message_uid, time.time()))
        return branch_ref

    def inherit_foreground_branch(self, parent_session_id, branch_session_id, *, through_message_uid=None):
        return self._execute_write(lambda conn: self.inherit_foreground_branch_conn(
            conn, parent_session_id, branch_session_id, through_message_uid=through_message_uid))

    def secretary_inherit_branch_conn(self, conn, parent_session_id, branch_session_id, *, through_message_uid=None):
        branch_ref = self.resolve_conversation_ref_conn(conn, branch_session_id)
        frozen = conn.execute("SELECT 1 FROM secretary_branch_freezes WHERE conversation_ref=?", (branch_ref,)).fetchone()
        if frozen:
            # Still validate the caller's ownership; idempotence never masks a forged parent.
            self.inherit_foreground_branch_conn(conn, parent_session_id, branch_session_id,
                                                through_message_uid=through_message_uid)
            return None
        branch_ref = self.inherit_foreground_branch_conn(conn, parent_session_id, branch_session_id,
                                                        through_message_uid=through_message_uid)
        self.notebook_inherit_branch_conn(conn, self.resolve_conversation_ref_conn(conn, parent_session_id), branch_ref)
        return branch_ref

    def secretary_inherit_branch(self, parent_session_id, branch_session_id):
        """Branch bootstrap (02 §2.7): freeze the parent path and seed the Branch Notebook.

        Insert-once per branch — safe to call on every identity (re)initialization; a branch
        whose foreground is already frozen returns None without touching anything.
        """

        return self._execute_write(lambda conn: self.secretary_inherit_branch_conn(conn, parent_session_id, branch_session_id))
