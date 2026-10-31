"""Bounded audit events and atomic adaptive plans in Secretary-owned sidecars."""
from __future__ import annotations

import json
import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS secretary_adaptive_events (
 id INTEGER PRIMARY KEY, conversation_ref TEXT NOT NULL, event_id TEXT NOT NULL,
 at REAL NOT NULL, kind TEXT NOT NULL, payload TEXT NOT NULL,
 UNIQUE(conversation_ref,event_id));
CREATE INDEX IF NOT EXISTS idx_adaptive_event_time ON secretary_adaptive_events(conversation_ref,at,id);
CREATE TABLE IF NOT EXISTS secretary_adaptive_plans (
 conversation_ref TEXT PRIMARY KEY, generation INTEGER NOT NULL, status TEXT NOT NULL,
 finished_at REAL NOT NULL, config_version TEXT NOT NULL, payload TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS secretary_adaptive_heartbeats (
 conversation_ref TEXT PRIMARY KEY, mode TEXT NOT NULL, interval_seconds REAL,
 config_version TEXT NOT NULL, claim_revision INTEGER, pending TEXT, fallback_anchor REAL NOT NULL);
"""


def init_schema(cursor):
    for statement in SCHEMA.split(";"):
        if statement.strip():
            cursor.execute(statement)


def event_conn(conn, ref, event):
    payload = json.dumps(event, allow_nan=False, separators=(",", ":"))
    prior = conn.execute("SELECT payload FROM secretary_adaptive_events WHERE conversation_ref=? AND event_id=?",
                         (ref, event["event_id"])).fetchone()
    if prior is not None:
        existing = json.loads(prior[0])
        if {key: value for key, value in existing.items() if key != "at"} != {key: value for key, value in event.items() if key != "at"}:
            existing.update(source="unknown", verified=False, conflict=True)
            conn.execute("UPDATE secretary_adaptive_events SET payload=? WHERE conversation_ref=? AND event_id=?",
                         (json.dumps(existing, allow_nan=False, separators=(",", ":")), ref, event["event_id"]))
        return False
    inserted = conn.execute("INSERT OR IGNORE INTO secretary_adaptive_events "
                            "(conversation_ref,event_id,at,kind,payload) VALUES (?,?,?,?,?)",
                            (ref, event["event_id"], event["at"], event["kind"], payload)).rowcount
    # Composite owner/time index bounds both reads and retention; at most 2048 rows per owner.
    conn.execute("DELETE FROM secretary_adaptive_events WHERE conversation_ref=? AND id IN "
                 "(SELECT id FROM secretary_adaptive_events WHERE conversation_ref=? "
                 "ORDER BY at DESC,id DESC LIMIT -1 OFFSET 2048)", (ref, ref))
    return bool(inserted)


def history(db, ref, now, *, limit=2048):
    with db._read_ctx() as conn:
        rows = conn.execute("SELECT payload FROM secretary_adaptive_events WHERE conversation_ref=? "
                            "AND at<=? ORDER BY at DESC,id DESC LIMIT ?", (ref, now, min(2048, max(1, limit)))).fetchall()
    return [json.loads(row[0]) for row in reversed(rows)]


def plan_conn(conn, ref):
    row = conn.execute("SELECT * FROM secretary_adaptive_plans WHERE conversation_ref=?", (ref,)).fetchone()
    return {**dict(row), "decision": json.loads(row["payload"])} if row else None


def heartbeat_conn(conn, ref):
    row = conn.execute("SELECT * FROM secretary_adaptive_heartbeats WHERE conversation_ref=?", (ref,)).fetchone()
    return dict(row) if row else None


def adopt_mode_conn(conn, ref, mode, config):
    interval = config["hot_interval_seconds"] if mode == "hot" else config.get("business_interval_seconds")
    current = heartbeat_conn(conn, ref)
    payload = json.dumps({"mode": mode, "interval_seconds": interval, "config_version": config["config_version"]})
    if current and current["claim_revision"] is not None:
        conn.execute("UPDATE secretary_adaptive_heartbeats SET pending=? WHERE conversation_ref=?", (payload, ref))
        return
    conn.execute("INSERT INTO secretary_adaptive_heartbeats "
                 "(conversation_ref,mode,interval_seconds,config_version,fallback_anchor) VALUES (?,?,?,?,?) "
                 "ON CONFLICT(conversation_ref) DO UPDATE SET mode=excluded.mode,"
                 "interval_seconds=excluded.interval_seconds,config_version=excluded.config_version,pending=NULL",
                 (ref, mode, interval, config["config_version"], config.get("_configured_at", time.time())))


def settle_claim_conn(conn, ref, revision=None):
    row = heartbeat_conn(conn, ref)
    if not row or revision is not None and row["claim_revision"] != revision:
        return
    pending = json.loads(row["pending"]) if row["pending"] else row
    conn.execute("UPDATE secretary_adaptive_heartbeats SET mode=?,interval_seconds=?,config_version=?,"
                 "claim_revision=NULL,pending=NULL WHERE conversation_ref=?",
                 (pending["mode"], pending["interval_seconds"], pending["config_version"], ref))


def invalidate_conn(db, conn, ref, at):
    row = plan_conn(conn, ref)
    if row is None or row["status"] != "pending":
        return False
    conn.execute("UPDATE secretary_adaptive_plans SET status='invalidated' WHERE conversation_ref=?", (ref,))
    conn.execute("UPDATE secretary_noting_idle_state SET trigger_produced_at=?,updated_at=? "
                 "WHERE conversation_ref=? AND last_turn_finished_at=? AND trigger_produced_at IS NULL",
                 (at, at, ref, row["finished_at"]))
    return True


def commit_plan(db, ref, *, at, expected_period, decision, config, context_epoch):
    """Three outputs, matching Idle period and mode are one native write transaction."""
    def write(conn):
        if db.noting_idle_state_conn(conn, ref) != expected_period:
            return False
        prior = plan_conn(conn, ref)
        generation = prior["generation"] + 1 if prior else 1
        enabled = decision["threshold_tokens"] is not None and decision["delay_seconds"] is not None
        due = at + decision["delay_seconds"] if enabled else None
        db.noting_idle_turn_finished_conn(conn, ref, at, due_at=due)
        if not enabled:
            conn.execute("UPDATE secretary_noting_idle_state SET trigger_produced_at=? WHERE conversation_ref=?", (at, ref))
        payload = {**decision, "context_epoch": context_epoch, "due_at": due}
        conn.execute("INSERT INTO secretary_adaptive_plans VALUES (?,?,?,?,?,?) "
                     "ON CONFLICT(conversation_ref) DO UPDATE SET generation=excluded.generation,status=excluded.status,"
                     "finished_at=excluded.finished_at,config_version=excluded.config_version,payload=excluded.payload",
                     (ref, generation, "pending" if enabled else "disabled", at, config["config_version"], json.dumps(payload, allow_nan=False)))
        adopt_mode_conn(conn, ref, decision["mode"], config)
        return True
    return db._execute_write(write)


def native_mode_conn(conn, ref):
    """Policy fallback restores configured native interval without breaking a live claim."""
    row = heartbeat_conn(conn, ref)
    if not row:
        return
    if row["claim_revision"] is None:
        conn.execute("DELETE FROM secretary_adaptive_heartbeats WHERE conversation_ref=?", (ref,))
        return
    hb = conn.execute("SELECT interval_seconds FROM secretary_heartbeats WHERE conversation_ref=?", (ref,)).fetchone()
    payload = json.dumps({"mode": "business", "interval_seconds": hb[0] if hb else None, "config_version": "native"})
    conn.execute("UPDATE secretary_adaptive_heartbeats SET pending=? WHERE conversation_ref=?", (payload, ref))


def consume_plan_conn(conn, ref, finished_at):
    """Mirror the existing native once-only acceptance in its original transaction."""
    conn.execute("UPDATE secretary_adaptive_plans SET status='consumed' WHERE conversation_ref=? "
                 "AND finished_at=? AND status='pending'", (ref, finished_at))


def register_claim_conn(conn, ref, revision, config, native_interval):
    """Even the first/native-mode claim must fence subsequent automatic mode changes."""
    row = heartbeat_conn(conn, ref)
    if not row:
        conn.execute("INSERT INTO secretary_adaptive_heartbeats "
                     "(conversation_ref,mode,interval_seconds,config_version,claim_revision,fallback_anchor) "
                     "VALUES (?,'business',?,'native',?,?)",
                     (ref, native_interval, revision, config.get("_configured_at", time.time())))
    elif row["config_version"] != config["config_version"] and row["claim_revision"] is None:
        conn.execute("UPDATE secretary_adaptive_heartbeats SET mode='business',interval_seconds=?,"
                     "config_version='native',claim_revision=?,pending=NULL WHERE conversation_ref=?",
                     (native_interval, revision, ref))
    else:
        conn.execute("UPDATE secretary_adaptive_heartbeats SET claim_revision=? WHERE conversation_ref=?", (revision, ref))
