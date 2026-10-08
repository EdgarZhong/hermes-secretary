"""Durable opaque Conversation ownership, separate from Hermes routing locators."""

import json
import time
import uuid

from hermes_state_common import _RESET_END_REASONS
from hermes_state_compression import _CHAIN_CAP, _CHAIN_STEP_SQL


class ConversationIdentityError(ValueError):
    """A missing/unprovable locator or conflicting aliases fail closed."""


class SecretaryIdentityMixin:
    def secretary_reconcile_session_conn(self, conn, session_id):
        """A native no-op against a vanished Session remains a no-op."""
        if conn.execute("SELECT 1 FROM sessions WHERE id=?", (session_id,)).fetchone() is not None:
            self.notebook_reselect_pointer_conn(conn, self.resolve_conversation_ref_conn(conn, session_id))

    def secretary_session_created_conn(self, conn, session_id, *, branch_point_message_uid=None):
        """Freeze locators only at a proven native INSERT, never at an old-row upsert."""
        session = self._secretary_session_conn(conn, session_id)
        config = session.get("model_config")
        config = json.loads(config) if isinstance(config, str) else (config or {})
        if config.get("_branched_from"):
            return self.secretary_inherit_branch_conn(
                conn, config["_branched_from"], session_id, through_message_uid=branch_point_message_uid)
        locator = None
        if session.get("session_key") and not self._is_explicit_fork_child_row(session) and session["source"] not in {"tool", "subagent"}:
            generation = conn.execute(
                "SELECT generation FROM conversation_generations WHERE source=? AND session_key=?",
                (session["source"], session["session_key"]),
            ).fetchone()
            locator = (session["source"], session["session_key"], int(generation[0]) if generation else 0)
        return self.resolve_conversation_ref_conn(conn, session_id, locator)

    def _secretary_session_conn(self, conn, session_id):
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if row is None:
            raise ConversationIdentityError("Session does not exist")
        return dict(row)

    def _compression_ancestors_conn(self, conn, session_id):
        """Hermes compression-only ancestry on the caller's connection."""
        current = self._secretary_session_conn(conn, session_id)
        path, seen = [current["id"]], {current["id"]}
        for _ in range(_CHAIN_CAP):
            parent_id = current.get("parent_session_id")
            if not parent_id or parent_id in seen or self._is_explicit_fork_child_row(current, include_reset=True):
                break
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (parent_id,)).fetchone()
            if row is None or row["end_reason"] != "compression":
                break
            current = dict(row)
            seen.add(parent_id)
            path.append(parent_id)
        return list(reversed(path))

    def _compression_path_conn(self, conn, session_id):
        """Use native tip preference, then its actual ancestry (never a stale sibling)."""
        ancestors = self._compression_ancestors_conn(conn, session_id)
        current, seen = ancestors[0], set()
        for _ in range(_CHAIN_CAP):
            seen.add(current)
            row = conn.execute(_CHAIN_STEP_SQL, (current,)).fetchone()
            if row is None or row["id"] in seen:
                break
            current = row["id"]
        return self._compression_ancestors_conn(conn, current)

    @staticmethod
    def _declared_alias(locator):
        if not isinstance(locator, (tuple, list)) or len(locator) != 3:
            raise ConversationIdentityError("Declared locator requires source, key and generation")
        source, key, generation = locator
        if not isinstance(source, str) or not source.strip() or not isinstance(key, str) or not key.strip():
            raise ConversationIdentityError("Declared source/key must be nonempty")
        if isinstance(generation, bool) or not isinstance(generation, int) or generation < 0:
            raise ConversationIdentityError("Declared generation must be a nonnegative integer")
        return source.strip(), key.strip(), generation

    def _trusted_declared_locator_conn(self, conn, session, binding, supplied):
        """Never recalculate an old Session's generation from today's peer counter."""
        if self._is_explicit_fork_child_row(session) or session.get("source") in {"tool", "subagent"}:
            if supplied is not None:
                raise ConversationIdentityError("Child Session cannot declare parent Conversation")
            return None
        if binding is not None and binding["declared_generation"] is not None:
            stored = (binding["declared_source"], binding["declared_key"], binding["declared_generation"])
            if supplied is not None and self._declared_alias(supplied) != stored:
                raise ConversationIdentityError("Session already belongs to another declared generation")
            return stored
        if supplied is None:
            # The DB cannot prove an unregistered historical Session's birth generation.
            return None
        locator = self._declared_alias(supplied)
        source, key, generation = locator
        if session.get("source") != source or (session.get("session_key") and session["session_key"] != key):
            raise ConversationIdentityError("Declared locator does not match Session ownership")
        if session.get("end_reason") in _RESET_END_REASONS:
            raise ConversationIdentityError("A retired Conversation cannot claim the current generation")
        row = conn.execute(
            "SELECT generation FROM conversation_generations WHERE source = ? AND session_key = ?",
            (source, key),
        ).fetchone()
        if generation != (int(row[0]) if row else 0):
            raise ConversationIdentityError("Declared generation is no longer current")
        return locator

    def resolve_conversation_ref_conn(self, conn, session_id, trusted_declared_locator=None):
        session = self._secretary_session_conn(conn, session_id)
        ancestors = self._compression_ancestors_conn(conn, session_id)
        bindings = conn.execute(
            "SELECT * FROM secretary_session_bindings WHERE session_id IN (%s)" % ",".join("?" for _ in ancestors),
            ancestors,
        ).fetchall()
        binding = next((row for row in bindings if row["session_id"] == session_id), None)
        inherited = binding or next((row for row in bindings if row["declared_generation"] is not None), None)
        declared = self._trusted_declared_locator_conn(conn, session, inherited, trusted_declared_locator)
        aliases = [("compression_root", ancestors[0])]
        if declared is not None:
            aliases.append(("declared", json.dumps(declared, ensure_ascii=False, separators=(",", ":"))))
        known = {row["conversation_ref"] for row in bindings}
        for kind, value in aliases:
            row = conn.execute(
                "SELECT conversation_ref FROM secretary_conversation_aliases WHERE alias_kind = ? AND alias_value = ?",
                (kind, value),
            ).fetchone()
            if row:
                known.add(row[0])
        if len(known) > 1:
            raise ConversationIdentityError("Trusted Conversation aliases conflict; refusing automatic merge")
        ref = next(iter(known)) if known else "conv_" + uuid.uuid4().hex
        now = time.time()
        conn.execute("INSERT OR IGNORE INTO secretary_conversations VALUES (?, ?)", (ref, now))
        for kind, value in aliases:
            conn.execute("INSERT OR IGNORE INTO secretary_conversation_aliases VALUES (?, ?, ?, ?)", (kind, value, ref, now))
        for sid in ancestors:
            conn.execute(
                "INSERT INTO secretary_session_bindings VALUES (?, ?, ?, ?, ?) "
                "ON CONFLICT(session_id) DO UPDATE SET declared_source=COALESCE(declared_source,excluded.declared_source), "
                "declared_key=COALESCE(declared_key,excluded.declared_key), "
                "declared_generation=COALESCE(declared_generation,excluded.declared_generation)",
                (sid, ref, *(declared or (None, None, None))),
            )
        return ref

    def resolve_conversation_ref(self, session_id, trusted_declared_locator=None):
        return self._execute_write(lambda conn: self.resolve_conversation_ref_conn(conn, session_id, trusted_declared_locator))

    def resolve_conversation_route_conn(self, conn, conversation_ref):
        """Return a proven current physical Session; stale declared generations are inert."""
        bindings = conn.execute(
            "SELECT * FROM secretary_session_bindings WHERE conversation_ref = ?", (conversation_ref,),
        ).fetchall()
        candidates = []
        for binding in bindings:
            row = conn.execute("SELECT * FROM sessions WHERE id = ?", (binding["session_id"],)).fetchone()
            if row is None:
                continue
            if binding["declared_generation"] is not None:
                generation = conn.execute(
                    "SELECT generation FROM conversation_generations WHERE source = ? AND session_key = ?",
                    (binding["declared_source"], binding["declared_key"]),
                ).fetchone()
                if (int(generation[0]) if generation else 0) != binding["declared_generation"]:
                    continue
            path = self._compression_path_conn(conn, binding["session_id"])
            tip = self._secretary_session_conn(conn, path[-1])
            owner = conn.execute(
                "SELECT conversation_ref FROM secretary_session_bindings WHERE session_id = ?", (tip["id"],),
            ).fetchone()
            if owner and owner[0] != conversation_ref:
                raise ConversationIdentityError("Compression tip belongs to another Conversation")
            if tip.get("end_reason") in _RESET_END_REASONS:
                continue
            candidates.append(tip)
        if not candidates:
            return None
        tips = {row["id"]: row for row in candidates}
        # A declared host may mint a physical Session per response. Their known alias
        # proves common ownership; route to the newest physical continuation.
        return max(tips.values(), key=lambda row: (row.get("started_at") or 0, row["id"]))

    def resolve_conversation_route(self, conversation_ref):
        with self._read_ctx() as conn:
            return self.resolve_conversation_route_conn(conn, conversation_ref)
