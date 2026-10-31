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
            row = self._row(conn)
            state = _state(row)
            if state is not None:
                interval = _effective_interval(self.db, conn, self.conversation_ref, row)
                state._adaptive_interval_seconds = interval
                state._adaptive_infinite = interval is None
                if not state.created_at:
                    state.created_at = _effective_anchor(self.db, conn, self.conversation_ref, row)
            return state

    def save(self, state):
        """Explicit definition replacement; never a claim/refund path."""
        if not self.conversation_ref:
            raise ValueError("Heartbeat requires a stored Conversation")
        values = tuple(getattr(state, name) for name in _STATE_COLUMNS)
        def write(conn):
            conn.execute("DELETE FROM secretary_adaptive_heartbeats WHERE conversation_ref=?", (self.conversation_ref,))
            return conn.execute(
            "INSERT INTO secretary_heartbeats (conversation_ref,prompt,interval_seconds,status,created_at,"
            "last_fired_at,fire_count) VALUES (?,?,?,?,?,?,?) ON CONFLICT(conversation_ref) DO UPDATE SET "
            "prompt=excluded.prompt,interval_seconds=excluded.interval_seconds,status=excluded.status,"
            "created_at=excluded.created_at,last_fired_at=excluded.last_fired_at,fire_count=excluded.fire_count,"
            "revision=secretary_heartbeats.revision+1", (self.conversation_ref, *values))
        self.db._execute_write(write)
        return state

    def set_status(self, status, *, reanchor=False):
        now = time.time()
        def update(conn):
            row = self._row(conn)
            if row is None or row["status"] == "cleared":
                return None
            from secretary.adaptive_store import settle_claim_conn
            settle_claim_conn(conn, self.conversation_ref)
            conn.execute("UPDATE secretary_heartbeats SET status=?,last_fired_at=?,revision=revision+1 "
                         "WHERE conversation_ref=?", (status, now if reanchor else row["last_fired_at"], self.conversation_ref))
            return row if status == "cleared" else self._row(conn)
        return _state(self.db._execute_write(update))

    def claim(self, now=None):
        from secretary.heartbeat_route import heartbeat_route_conn

        moment = time.time() if now is None else now
        def update(conn):
            row = self._row(conn)
            interval = _effective_interval(self.db, conn, self.conversation_ref, row) if row else None
            if (row is None or row["status"] != "active" or interval is None
                    or moment - _effective_anchor(self.db, conn, self.conversation_ref, row) < interval):
                return None
            if _adaptive_priority_held(self.db, conn, self.conversation_ref, moment, self.session_id):
                return None
            route = heartbeat_route_conn(self.db, conn, self.conversation_ref)
            if route is None or route["id"] != self.session_id:
                return None
            conn.execute("UPDATE secretary_heartbeats SET last_fired_at=?,fire_count=fire_count+1,revision=revision+1 "
                         "WHERE conversation_ref=?", (moment, self.conversation_ref))
            current = self._row(conn)
            from secretary.adaptive_config import for_db
            from secretary.adaptive_store import register_claim_conn
            config = for_db(self.db)
            if config:
                register_claim_conn(conn, self.conversation_ref, current["revision"], config, interval)
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
            if cursor.rowcount == 1:
                from secretary.adaptive_store import settle_claim_conn
                settle_claim_conn(conn, self.conversation_ref, claim.revision)
            return cursor.rowcount == 1
        return self.db._execute_write(update)



def _effective_interval(db, conn, ref, row):
    from secretary.adaptive_config import for_db
    from secretary.adaptive_store import heartbeat_conn
    config = for_db(db)
    adaptive = heartbeat_conn(conn, ref) if config else None
    if adaptive and (adaptive["config_version"] == config["config_version"] or adaptive["claim_revision"] is not None):
        return adaptive["interval_seconds"]
    return row["interval_seconds"]


def _adaptive_idle_precedes(db, conn, ref, now, session_id):
    from secretary.adaptive_config import for_db
    from secretary.adaptive_store import plan_conn
    config = for_db(db)
    if config is None:
        return False
    plan = plan_conn(conn, ref)
    period = db.noting_idle_state_conn(conn, ref)
    if (not plan or not period or plan["status"] != "pending" or period["trigger_produced_at"] is not None
            or plan["config_version"] != config["config_version"]
            or plan["finished_at"] != period["last_turn_finished_at"]):
        return False
    decision = plan["decision"]
    path = conn.execute("SELECT rewind_count FROM sessions WHERE id=?", (session_id,)).fetchone()
    if not path or decision.get("context_path") != [session_id, path[0]]:
        return False
    if (decision.get("due_at") is None or decision["due_at"] > now
            or decision.get("threshold_tokens") is None
            or decision["context_epoch"] != db.noting_compaction_interval_conn(conn, ref)):
        return False
    row = conn.execute("SELECT payload FROM secretary_adaptive_events WHERE conversation_ref=? "
                       "AND kind IN ('turn_end','context_read') AND at<=? ORDER BY at DESC,id DESC LIMIT 1", (ref, now)).fetchone()
    import json
    observed = json.loads(row[0]) if row else {}
    if (observed.get("conflict") or observed.get("model_key") != decision.get("model_key")
            or observed.get("context_contract") != decision.get("context_contract")):
        return False
    usage = observed.get("context_tokens")
    return usage is not None and usage >= decision["threshold_tokens"]


def due_conversations(db, *, now=None):
    moment = time.time() if now is None else now
    from secretary.adaptive_config import for_db
    config = for_db(db)
    with db._read_ctx() as conn:
        if config is None:
            return [row[0] for row in conn.execute(
                "SELECT conversation_ref FROM secretary_heartbeats WHERE status='active' "
                "AND ?-CASE WHEN last_fired_at=0 THEN created_at ELSE last_fired_at END>=interval_seconds",
                (moment,)).fetchall()]
        return [row[0] for row in conn.execute(
            "SELECT h.conversation_ref FROM secretary_heartbeats h LEFT JOIN secretary_adaptive_heartbeats a "
            "ON a.conversation_ref=h.conversation_ref WHERE h.status='active' AND "
            "?-CASE WHEN h.last_fired_at=0 THEN CASE WHEN h.created_at=0 AND "
            "(a.config_version=? OR a.claim_revision IS NOT NULL) THEN a.fallback_anchor ELSE h.created_at END "
            "ELSE h.last_fired_at END >= "
            "CASE WHEN a.config_version=? OR a.claim_revision IS NOT NULL THEN a.interval_seconds ELSE h.interval_seconds END",
            (moment, config["config_version"], config["config_version"])).fetchall()]


def _adaptive_priority_held(db, conn, ref, now, session_id):
    from secretary.adaptive_config import for_db
    from secretary.noting_scope import scheduler_settings_for_db
    if for_db(db) is None:
        return False
    if scheduler_settings_for_db(db).enabled and conn.execute(
            "SELECT 1 FROM secretary_schedule_registry WHERE conversation_ref=? AND state='pending' "
            "AND enabled=1 AND delivery_semantics='user_reminder' AND next_run_at<=? LIMIT 1",
            (ref, now)).fetchone() is not None:
        return True
    return _adaptive_idle_precedes(db, conn, ref, now, session_id)


def _effective_anchor(db, conn, ref, row):
    anchor = row["last_fired_at"] or row["created_at"]
    if anchor:
        return anchor
    from secretary.adaptive_config import for_db
    from secretary.adaptive_store import heartbeat_conn
    config = for_db(db)
    mode = heartbeat_conn(conn, ref) if config else None
    if mode and (mode["config_version"] == config["config_version"] or mode["claim_revision"] is not None):
        return mode["fallback_anchor"]
    return anchor
