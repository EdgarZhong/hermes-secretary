"""One transactional Heartbeat definition per stable Conversation in its owning state.db."""

from __future__ import annotations

from dataclasses import dataclass
import time

_STATE_COLUMNS = ("prompt", "interval_seconds", "status", "created_at", "last_fired_at", "fire_count")


def _state(row):
    from hermes_cli.heartbeat import HeartbeatState

    if row is None or row["status"] == "cleared":
        return None
    state = HeartbeatState(**{name: row[name] for name in _STATE_COLUMNS})
    state._conversation_heartbeat = True
    return state


def enabled_for_db(db):
    from secretary.heartbeat import ui_heartbeat_enabled
    from secretary.noting_scope import owning_db_scope

    with owning_db_scope(db):
        return ui_heartbeat_enabled()


@dataclass(frozen=True)
class HeartbeatClaim:
    revision: int
    last_fired_at: float
    fire_count: int


class ConversationHeartbeatStore:
    def __init__(self, db, session_id):
        self.db, self.session_id = db, session_id
        self.conversation_ref = (db.resolve_conversation_ref(session_id)
                                 if db.get_session(session_id) is not None else None)

    def _row(self, conn):
        return conn.execute("SELECT * FROM secretary_heartbeats WHERE conversation_ref=?",
                            (self.conversation_ref,)).fetchone()

    def load(self):
        with self.db._read_ctx() as conn:
            return _state(self._row(conn))

    def save(self, state):
        """Explicit definition replacement; never a claim/refund path."""
        if not self.conversation_ref:
            raise ValueError("Heartbeat requires a stored Conversation")
        values = tuple(getattr(state, name) for name in _STATE_COLUMNS)
        self.db._execute_write(lambda conn: conn.execute(
            "INSERT INTO secretary_heartbeats (conversation_ref,prompt,interval_seconds,status,created_at,"
            "last_fired_at,fire_count) VALUES (?,?,?,?,?,?,?) ON CONFLICT(conversation_ref) DO UPDATE SET "
            "prompt=excluded.prompt,interval_seconds=excluded.interval_seconds,status=excluded.status,"
            "created_at=excluded.created_at,last_fired_at=excluded.last_fired_at,fire_count=excluded.fire_count,"
            "revision=secretary_heartbeats.revision+1", (self.conversation_ref, *values)))
        return state

    def set_status(self, status, *, reanchor=False):
        now = time.time()
        def update(conn):
            row = self._row(conn)
            if row is None or row["status"] == "cleared":
                return None
            conn.execute("UPDATE secretary_heartbeats SET status=?,last_fired_at=?,revision=revision+1 "
                         "WHERE conversation_ref=?", (status, now if reanchor else row["last_fired_at"], self.conversation_ref))
            return row if status == "cleared" else self._row(conn)
        return _state(self.db._execute_write(update))

    def claim(self, now=None):
        from secretary.heartbeat_route import heartbeat_route_conn

        moment = time.time() if now is None else now
        def update(conn):
            row = self._row(conn)
            if (row is None or row["status"] != "active"
                    or moment - (row["last_fired_at"] or row["created_at"]) < row["interval_seconds"]):
                return None
            route = heartbeat_route_conn(self.db, conn, self.conversation_ref)
            if route is None or route["id"] != self.session_id:
                return None
            conn.execute("UPDATE secretary_heartbeats SET last_fired_at=?,fire_count=fire_count+1,revision=revision+1 "
                         "WHERE conversation_ref=?", (moment, self.conversation_ref))
            current = self._row(conn)
            return _state(current), HeartbeatClaim(current["revision"], row["last_fired_at"], row["fire_count"])
        return self.db._execute_write(update)

    def claim_is_current(self, claim):
        from secretary.heartbeat_route import heartbeat_route_conn

        with self.db._read_ctx() as conn:
            row = self._row(conn)
            if not row or row["status"] != "active" or row["revision"] != claim.revision:
                return False
            route = heartbeat_route_conn(self.db, conn, self.conversation_ref)
            return bool(route and route["id"] == self.session_id)

    def refund(self, claim):
        def update(conn):
            cursor = conn.execute(
                "UPDATE secretary_heartbeats SET last_fired_at=?,fire_count=?,revision=revision+1 "
                "WHERE conversation_ref=? AND status='active' AND revision=?",
                (claim.last_fired_at, claim.fire_count, self.conversation_ref, claim.revision))
            return cursor.rowcount == 1
        return self.db._execute_write(update)


def due_conversations(db, *, now=None):
    moment = time.time() if now is None else now
    with db._read_ctx() as conn:
        return [row[0] for row in conn.execute(
            "SELECT conversation_ref FROM secretary_heartbeats WHERE status='active' "
            "AND ?-CASE WHEN last_fired_at=0 THEN created_at ELSE last_fired_at END>=interval_seconds",
            (moment,)).fetchall()]
