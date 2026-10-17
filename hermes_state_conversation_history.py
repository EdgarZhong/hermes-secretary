"""Narrow read-only ownership/path helpers for conversation_history.

The owning host supplies an Agent, never a model-supplied DB, Profile or Session.
The only transcript authority is the existing History Foreground projection.
"""

from contextlib import contextmanager
from dataclasses import dataclass
import json
from pathlib import Path

from agent.message_visibility import model_visible_messages
from hermes_state_secretary_identity import ConversationIdentityError


class HistoryError(ValueError):
    def __init__(self, code, message, next_action, *, field=None):
        super().__init__(message)
        self.code, self.message, self.next_action, self.field = code, message, next_action, field

    def result(self):
        error = {"code": self.code, "message": self.message, "next_action": self.next_action}
        if self.field is not None:
            error["field"] = self.field
        return {"success": False, "error": error}


def denied():
    return HistoryError("scope_denied", "This History scope is not authorized for the current caller.",
                        "Use the current allowed Conversation; do not retry through another tool.")


def scope_denied_for_target(*, target, noting=False):
    """The actionable boundary when the target is merely outside the default scope."""
    if noting:
        return HistoryError(
            "scope_denied", "Noting can read only its bound parent Conversation.",
            "Keep the bound parent; cross-Conversation retry is not available to Noting.",
        )
    return HistoryError(
        "scope_denied", f"Conversation {target} is outside the default current-Conversation scope.",
        "If it is an authorized same-Profile Conversation, retry with cross_conversation=true; "
        "otherwise stay in the current Conversation.",
    )


def unavailable_source():
    return HistoryError("source_unavailable", "The requested source is not available on the authorized current path.",
                        "Search for specific evidence in the allowed scope; keep it unknown if it cannot be found.")


def _same_database(first, second):
    if first is second and first is not None:
        return True
    a, b = getattr(first, "db_path", None), getattr(second, "db_path", None)
    return a is not None and b is not None and Path(a).resolve() == Path(b).resolve()


def owning_history_db(agent):
    """Runtime qualification is independent of Noting and Memory enable settings."""
    from secretary.noting_runtime import is_main_conversation_agent

    db = getattr(agent, "_session_db", None)
    if db is None or not getattr(db, "db_path", None) or not getattr(agent, "session_id", None):
        raise denied()
    if getattr(agent, "_secretary_noting_child", False):
        history_db = getattr(agent, "_secretary_history_db", None)
        if not _same_database(db, history_db):
            raise denied()
        return history_db
    if not is_main_conversation_agent(agent):
        raise denied()
    return db


@contextmanager
def history_read_snapshot(db):
    """Pin candidate cursors and path checks without committing someone else's transaction."""
    with db._read_ctx() as conn:
        owns_transaction = not conn.in_transaction
        if owns_transaction:
            conn.execute("BEGIN")
        try:
            yield conn
        finally:
            if owns_transaction:
                conn.rollback()  # Ends the read snapshot; no binding/index repair occurred.


@dataclass(frozen=True)
class HistoryScope:
    conversation_ref: str
    noting: bool


def resolve_history_scope_conn(db, conn, agent):
    """Resolve established host ownership only; a missing binding is never repaired."""
    noting = bool(getattr(agent, "_secretary_noting_child", False))
    if noting:
        ref = getattr(agent, "_secretary_parent_conversation_ref", None)
        parent_id = getattr(agent, "_parent_session_id", None)
        if not isinstance(ref, str) or not ref or not parent_id:
            raise denied()
        task = conn.execute(
            "SELECT a.conversation_ref FROM secretary_noting_children c "
            "JOIN secretary_noting_admissions a ON a.admission_id=c.admission_id "
            "WHERE c.child_session_id=? AND c.status='running' AND c.finished_at IS NULL",
            (agent.session_id,),
        ).fetchall()
        if len(task) != 1 or task[0][0] != ref:
            raise HistoryError("state_conflict", "No running Noting task is bound to this History caller.",
                               "Continue only through the runtime-bound task; do not supply a task ID.")
        try:
            parent_ref = db.resolve_conversation_ref_conn(conn, parent_id, read_only=True)
        except ConversationIdentityError as exc:
            raise denied() from exc
        if parent_ref != ref:
            raise denied()
        return HistoryScope(ref, True)
    try:
        ref = db.resolve_conversation_ref_conn(conn, agent.session_id, read_only=True)
    except ConversationIdentityError as exc:
        raise denied() from exc
    bound = getattr(agent, "_secretary_conversation_ref", None)
    if not ref or (bound is not None and bound != ref):
        raise denied()
    return HistoryScope(ref, False)


class HistoryPaths:
    """Cache only paths of actual candidates/anchors, not every Profile transcript."""

    def __init__(self, db, conn, scope):
        self.db, self.conn, self.scope = db, conn, scope
        self._paths = {}
        self._by_uid = {}
        self._fork_of = {}

    def _user_owned(self, ref):
        from secretary.noting_runtime import _CHILD_SOURCES, _NON_MAIN_PLATFORMS, _delegate_child_row

        bindings = self.conn.execute(
            "SELECT s.* FROM secretary_session_bindings b JOIN sessions s ON s.id=b.session_id "
            "WHERE b.conversation_ref=?", (ref,),
        ).fetchall()
        if not bindings:
            return False
        excluded = set(_CHILD_SOURCES) | set(_NON_MAIN_PLATFORMS) | {"review", "background_review", "btw"}
        # Do not infer ownership from a role=user prompt in a background Session.
        for binding in bindings:
            row = dict(binding)
            if not isinstance(row.get("source"), str) or not row["source"].strip() or row["source"].strip().lower() in excluded:
                return False
            if _delegate_child_row(row):
                return False
            ancestors = self.db._compression_ancestors_conn(self.conn, row["id"])
            root = self.db._secretary_session_conn(self.conn, ancestors[0])
            config = root.get("model_config") or {}
            if isinstance(config, str):
                try:
                    config = json.loads(config)
                except ValueError as exc:
                    raise unavailable_source() from exc
            if not isinstance(config, dict):
                raise unavailable_source()
            parent = root.get("parent_session_id")
            if parent and not self.db._is_explicit_fork_child_row(root, include_reset=True):
                return False
            if self.db.resolve_conversation_ref_conn(self.conn, row["id"], read_only=True) != ref:
                raise unavailable_source()
        return True

    def require_current_owner(self):
        """Authorize the caller with metadata before Search, without reading its transcript."""
        try:
            if not self._user_owned(self.scope.conversation_ref):
                raise denied()
        except ConversationIdentityError as exc:
            raise denied() from exc

    def rows(self, ref):
        """One common legal path for Search and Read, including both visibility filters."""
        if ref in self._paths:
            return self._paths[ref]
        try:
            if not self._user_owned(ref):
                self._paths[ref] = None
                return None
            rows = [row for row in model_visible_messages(self.db.get_history_foreground_conn(self.conn, ref))
                    if row.get("kind") == "message" and row.get("display_kind") != "hidden"
                    and row.get("role") in {"user", "assistant", "tool", "system"}]
        except ConversationIdentityError as exc:
            raise unavailable_source() from exc
        # The native real-user predicate also admits steer, not framework/reminder
        # carriers. A user-owned Session plus real interaction establishes a user
        # Conversation; a DB binding or synthetic user role alone does not.
        if not any(row["role"] == "user" and row.get("display_kind") in (None, "", "steer") for row in rows):
            self._paths[ref] = None
            return None
        if any(not isinstance(row.get("message_uid"), str) or not row["message_uid"].strip() for row in rows):
            raise unavailable_source()
        self._paths[ref] = rows
        self._by_uid[ref] = {row["message_uid"]: row for row in rows}
        return rows

    def require(self, ref):
        rows = self.rows(ref)
        if rows is None:
            raise denied()
        return rows

    def memberships(self, candidate, *, cross_conversation, exclude_current=False):
        """Expand only metadata of a physical hit, including frozen fork references."""
        rows = self.conn.execute(
            "SELECT conversation_ref FROM secretary_session_bindings WHERE session_id=? "
            "UNION SELECT b.conversation_ref FROM secretary_branch_messages b "
            "WHERE b.message_id=? AND NOT EXISTS(SELECT 1 FROM secretary_branch_exclusions x "
            "WHERE x.conversation_ref=b.conversation_ref AND x.message_uid=b.message_uid) "
            "ORDER BY conversation_ref", (candidate["session_id"], candidate["id"]),
        ).fetchall()
        refs = [row[0] for row in rows]
        current = self.scope.conversation_ref
        if not cross_conversation:
            return [current] if current in refs else []
        if exclude_current:
            return [ref for ref in refs if ref != current]
        if current in refs:
            refs.remove(current)
            refs.insert(0, current)
        return refs

    def fork_of(self, ref):
        """The authorized parent Conversation Ref for an explicit branch/reset, else None."""
        if ref in self._fork_of:
            return self._fork_of[ref]
        parent_ref = None
        try:
            rows = self.conn.execute(
                "SELECT s.* FROM secretary_session_bindings b JOIN sessions s ON s.id=b.session_id "
                "WHERE b.conversation_ref=? ORDER BY s.started_at", (ref,),
            ).fetchall()
            if rows:
                root_id = self.db._compression_ancestors_conn(self.conn, rows[0]["id"])[0]
                root = self.db._secretary_session_conn(self.conn, root_id)
                if root and self.db._is_explicit_fork_child_row(root, include_reset=True):
                    parent_id = root.get("parent_session_id")
                    if parent_id:
                        candidate = self.db.resolve_conversation_ref_conn(
                            self.conn, parent_id, read_only=True)
                        if candidate and candidate != ref and self._user_owned(candidate):
                            parent_ref = candidate
        except (ConversationIdentityError, HistoryError):
            parent_ref = None
        self._fork_of[ref] = parent_ref
        return parent_ref

    def winner(self, ref, uid):
        if self.rows(ref) is None:
            return None
        return self._by_uid[ref].get(uid)

    def source_row(self, row):
        """Point-read canonical source metadata; never hydrate an unauthorized candidate."""
        source = self.conn.execute(
            "SELECT content, tool_name, tool_calls FROM messages WHERE id=? AND message_uid=?",
            (row["id"], row["message_uid"]),
        ).fetchone()
        if source is None:
            raise unavailable_source()
        return dict(source)
