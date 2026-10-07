"""Canonical current-path History/Full projections of Hermes-owned transcript rows."""

import json

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
            "JOIN messages m ON m.id = b.message_id WHERE b.conversation_ref = ? ORDER BY b.position",
            (conversation_ref,),
        ).fetchall()
        for row in inherited:
            item = dict(row)
            item["_inherited"] = True
            rows.append(item)
        for sid in self._foreground_sessions_conn(conn, conversation_ref):
            rows.extend(dict(row) for row in conn.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY id", (sid,)))
        return rows

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
            if not row.get("_inherited") and not (row.get("active") or row.get("compacted")):
                continue
            projected = self._project_foreground_row(row, conversation_ref, full=full)
            if projected is not None:
                projected["path_position"] = len(result)
                result.append(projected)
                if full and projected["is_compaction"]:
                    live = self._project_foreground_row(row, conversation_ref, full=False)
                    if live is not None:
                        live["path_position"] = len(result)
                        result.append(live)
        return result

    def get_history_foreground_conn(self, conn, conversation_ref):
        return self._foreground_conn(conn, conversation_ref, full=False)

    def get_full_foreground_conn(self, conn, conversation_ref):
        return self._foreground_conn(conn, conversation_ref, full=True)

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
        branch_ref = self.resolve_conversation_ref_conn(conn, branch_session_id)
        existing = conn.execute("SELECT 1 FROM secretary_branch_messages WHERE conversation_ref = ? LIMIT 1", (branch_ref,)).fetchone()
        if existing:
            raise ConversationIdentityError("Branch Foreground is already frozen")
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
        return branch_ref

    def inherit_foreground_branch(self, parent_session_id, branch_session_id, *, through_message_uid=None):
        return self._execute_write(lambda conn: self.inherit_foreground_branch_conn(
            conn, parent_session_id, branch_session_id, through_message_uid=through_message_uid))
