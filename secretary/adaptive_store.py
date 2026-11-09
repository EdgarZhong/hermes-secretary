"""Bounded audit events and atomic adaptive plans in Secretary-owned sidecars."""
from __future__ import annotations

import json
import time

MAX_HISTORY_EVENTS = 65536

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
CREATE TABLE IF NOT EXISTS secretary_adaptive_imports (
 conversation_ref TEXT NOT NULL, import_id TEXT NOT NULL, declaration TEXT NOT NULL,
 imported_at REAL NOT NULL, receipt TEXT NOT NULL, replaced_by TEXT,
 PRIMARY KEY(conversation_ref,import_id));
CREATE TABLE IF NOT EXISTS secretary_adaptive_import_events (
 conversation_ref TEXT NOT NULL, origin_profile TEXT NOT NULL,
 origin_conversation TEXT NOT NULL, origin_event_id TEXT NOT NULL,
 at REAL NOT NULL, available_at REAL NOT NULL, payload TEXT NOT NULL,
 PRIMARY KEY(conversation_ref,origin_profile,origin_conversation,origin_event_id));
CREATE TABLE IF NOT EXISTS secretary_adaptive_import_members (
 conversation_ref TEXT NOT NULL, import_id TEXT NOT NULL, origin_profile TEXT NOT NULL,
 origin_conversation TEXT NOT NULL, origin_event_id TEXT NOT NULL,
 PRIMARY KEY(conversation_ref,import_id,origin_profile,origin_conversation,origin_event_id));
CREATE TABLE IF NOT EXISTS secretary_adaptive_refresh (
 conversation_ref TEXT PRIMARY KEY, revision INTEGER NOT NULL,
 evaluated_revision INTEGER NOT NULL DEFAULT 0, requested_at REAL NOT NULL);
CREATE TABLE IF NOT EXISTS secretary_adaptive_retention (
 conversation_ref TEXT PRIMARY KEY, discarded_through REAL, retained_count INTEGER NOT NULL);
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
    if conn.execute("SELECT 1 FROM secretary_adaptive_retention WHERE conversation_ref=?", (ref,)).fetchone() is None:
        conn.execute("INSERT INTO secretary_adaptive_retention (conversation_ref,retained_count) "
                     "SELECT ?,COUNT(*) FROM secretary_adaptive_events WHERE conversation_ref=?", (ref, ref))
    inserted = conn.execute("INSERT OR IGNORE INTO secretary_adaptive_events "
                            "(conversation_ref,event_id,at,kind,payload) VALUES (?,?,?,?,?)",
                            (ref, event["event_id"], event["at"], event["kind"], payload)).rowcount
    # Only a real eviction advances the evidence floor. Ordinary writes must
    # preserve coverage whose start predates the first stored event.
    conn.execute("UPDATE secretary_adaptive_retention SET retained_count=retained_count+? "
                 "WHERE conversation_ref=?", (inserted, ref))
    count = conn.execute("SELECT retained_count FROM secretary_adaptive_retention WHERE conversation_ref=?",
                         (ref,)).fetchone()[0]
    if count > MAX_HISTORY_EVENTS:
        floor = conn.execute("SELECT MAX(at) FROM (SELECT at FROM secretary_adaptive_events "
                             "WHERE conversation_ref=? ORDER BY at DESC,id DESC LIMIT -1 OFFSET ?)",
                             (ref, MAX_HISTORY_EVENTS)).fetchone()[0]
        conn.execute("UPDATE secretary_adaptive_retention SET discarded_through="
                     "MAX(COALESCE(discarded_through,?),?),retained_count=? WHERE conversation_ref=?",
                     (floor, floor, MAX_HISTORY_EVENTS, ref))
        conn.execute("DELETE FROM secretary_adaptive_events WHERE conversation_ref=? AND id IN "
                     "(SELECT id FROM secretary_adaptive_events WHERE conversation_ref=? "
                     "ORDER BY at DESC,id DESC LIMIT -1 OFFSET ?)", (ref, ref, MAX_HISTORY_EVENTS))
    if inserted and event['kind'] in {'turn_end', 'maintenance_sample'}:
        request_refresh_conn(conn, ref, event['at'])
    return bool(inserted)


def history_conn(conn, ref, now, *, limit=MAX_HISTORY_EVENTS):
    limit = min(MAX_HISTORY_EVENTS, max(1, limit))
    rows = conn.execute("SELECT payload FROM secretary_adaptive_events WHERE conversation_ref=? "
                        "AND at<=? ORDER BY at DESC,id DESC LIMIT ?",
                        (ref, now, limit)).fetchall()
    events = [json.loads(row[0]) for row in reversed(rows)]
    floor = conn.execute("SELECT discarded_through FROM secretary_adaptive_retention WHERE conversation_ref=?",
                         (ref,)).fetchone()
    discarded = floor[0] if floor else None
    if len(events) == limit:
        omitted = conn.execute('SELECT at FROM secretary_adaptive_events WHERE conversation_ref=? AND at<=? '
                               'ORDER BY at DESC,id DESC LIMIT 1 OFFSET ?', (ref, now, limit)).fetchone()
        if omitted:
            discarded = max(discarded or omitted[0], omitted[0])
    if discarded is not None:
        # Crossing coverage cannot certify an evicted arrival as silence. Also
        # applies to an in-memory observer that later extends the same span.
        for event in events:
            if event.get('kind') == 'coverage':
                event['start_at'] = max(event.get('start_at', event['at']), discarded)
    return events


def history(db, ref, now, *, limit=MAX_HISTORY_EVENTS):
    with db._read_ctx() as conn:
        return history_conn(conn, ref, now, limit=limit)


def request_refresh_conn(conn, ref, at):
    conn.execute("INSERT INTO secretary_adaptive_refresh(conversation_ref,revision,requested_at) VALUES (?,1,?) "
                 "ON CONFLICT(conversation_ref) DO UPDATE SET revision=revision+1,requested_at=excluded.requested_at",
                 (ref, at))


def refresh_conn(conn, ref):
    row = conn.execute("SELECT * FROM secretary_adaptive_refresh WHERE conversation_ref=?", (ref,)).fetchone()
    return dict(row) if row else None


def acknowledge_refresh_conn(conn, ref, revision):
    conn.execute("UPDATE secretary_adaptive_refresh SET evaluated_revision=MAX(evaluated_revision,?) "
                 "WHERE conversation_ref=?", (revision, ref))


def refresh_plan(db, ref, *, at, expected_period, decision, config, context_epoch, revision, guard):
    """Reevaluate the same Idle cycle; a consumed or invalidated cycle stays spent."""
    def write(conn):
        if db.noting_idle_state_conn(conn, ref) != expected_period or not guard(conn):
            return False
        prior = plan_conn(conn, ref)
        same_cycle = bool(prior and expected_period
                          and prior['finished_at'] == expected_period['last_turn_finished_at'])
        # disabled is an adaptive no-maintenance recommendation, not acceptance
        # of Idle work. consumed/invalidated and native trigger markers remain final.
        disabled = bool(prior and prior['status'] == 'disabled'
                        and expected_period and prior['finished_at'] == expected_period['last_turn_finished_at'])
        rearm = bool(expected_period and expected_period['last_turn_finished_at'] is not None
                     and (expected_period['trigger_produced_at'] is None or disabled)
                     and (expected_period['last_turn_started_at'] is None
                          or expected_period['last_turn_started_at'] < expected_period['last_turn_finished_at'])
                     and not (same_cycle and (prior['status'] in {'consumed', 'invalidated'}
                                          or prior['status'] == 'pending'
                                          and prior['decision'].get('due_at') is not None
                                          and prior['decision']['due_at'] <= at)))
        if rearm:
            enabled = decision['threshold_tokens'] is not None and decision['delay_seconds'] is not None
            due = at + decision['delay_seconds'] if enabled else None
            conn.execute("UPDATE secretary_noting_idle_state SET due_at=?,trigger_produced_at=?,updated_at=? "
                         "WHERE conversation_ref=?", (due, None if enabled else at, at, ref))
            payload = {**decision, 'context_epoch': context_epoch, 'due_at': due}
            conn.execute("INSERT INTO secretary_adaptive_plans VALUES (?,?,?,?,?,?) "
                         "ON CONFLICT(conversation_ref) DO UPDATE SET generation=excluded.generation,status=excluded.status,"
                         "finished_at=excluded.finished_at,config_version=excluded.config_version,payload=excluded.payload",
                         (ref, prior['generation'] + 1 if prior else 1, 'pending' if enabled else 'disabled',
                          expected_period['last_turn_finished_at'], config['config_version'], json.dumps(payload, allow_nan=False)))
        adopt_mode_conn(conn, ref, decision['mode'], config)
        acknowledge_refresh_conn(conn, ref, revision)
        return True
    return db._execute_write(write)


def imported_history_conn(conn, ref, now):
    """Frozen training cohorts only; never includes or changes live local history."""
    rows = conn.execute(
        "SELECT e.*,MIN(i.imported_at) AS imported_at FROM secretary_adaptive_import_events e "
        "JOIN secretary_adaptive_import_members m USING "
        "(conversation_ref,origin_profile,origin_conversation,origin_event_id) "
        "JOIN secretary_adaptive_imports i USING (conversation_ref,import_id) "
        "WHERE e.conversation_ref=? AND e.at<=? AND e.available_at<=? AND i.imported_at<=? "
        "AND COALESCE(json_extract(i.declaration,'$.kind'),'') != 'same_conversation_bootstrap' "
        "AND json_extract(e.payload,'$.bootstrap_schema') IS NULL "
        "GROUP BY e.origin_profile,e.origin_conversation,e.origin_event_id ORDER BY e.at,e.origin_event_id",
        (ref, now, now, now)).fetchall()
    receipts = [json.loads(row[0]) for row in conn.execute(
        "SELECT receipt FROM secretary_adaptive_imports WHERE conversation_ref=? AND imported_at<=? AND replaced_by IS NULL "
        "AND COALESCE(json_extract(declaration,'$.kind'),'') != 'same_conversation_bootstrap' "
        "ORDER BY imported_at,import_id", (ref, now))]
    cohorts = {}
    for row in rows:
        key = row["origin_profile"], row["origin_conversation"]
        cohort = cohorts.setdefault(key, dict(origin_profile=key[0], origin_conversation=key[1],
                                               events=[], receipts=[], retained_start_at=row["at"]))
        cohort["events"].append({**json.loads(row["payload"]), "origin_profile": key[0],
                                 "origin_conversation": key[1], "origin_event_id": row["origin_event_id"],
                                 "imported_at": row["imported_at"]})
    for cohort in cohorts.values():
        cohort["receipts"] = receipts
    return list(cohorts.values())


def imported_history(db, ref, now):
    """Read source-separated frozen evidence, fenced by event and import knowability."""
    with db._read_ctx() as conn:
        return imported_history_conn(conn, ref, now)


def plan_conn(conn, ref):
    row = conn.execute("SELECT * FROM secretary_adaptive_plans WHERE conversation_ref=?", (ref,)).fetchone()
    return {**dict(row), "decision": json.loads(row["payload"])} if row else None


def heartbeat_conn(conn, ref):
    row = conn.execute("SELECT * FROM secretary_adaptive_heartbeats WHERE conversation_ref=?", (ref,)).fetchone()
    return dict(row) if row else None


def adopt_mode_conn(conn, ref, mode, config):
    interval = config["hot_interval_seconds"] if mode == "hot" else (
        None if mode == "standby" else config.get("business_interval_seconds"))
    remember_heartbeat_config_conn(conn, ref, config)
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


def commit_plan(db, ref, *, at, expected_period, decision, config, context_epoch, expected_revision=None, guard=None):
    """Three outputs, matching Idle period and mode are one native write transaction."""
    def write(conn):
        if db.noting_idle_state_conn(conn, ref) != expected_period or (guard is not None and not guard(conn)):
            return False
        refresh = refresh_conn(conn, ref)
        if expected_revision is not None and (refresh["revision"] if refresh else 0) != expected_revision:
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
        refresh = refresh_conn(conn, ref)
        if refresh:
            acknowledge_refresh_conn(conn, ref, refresh["revision"])
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


def restore_native_idle(db, ref, *, expected_plan, expected_period, recheck):
    """Retire only the same unconsumed adaptive cycle, preserving its native clock.

    recheck runs inside this transaction and returns the current native delay only
    while the current contract still rejects this plan; None means leave it alone.
    """
    def write(conn):
        plan, period = plan_conn(conn, ref), db.noting_idle_state_conn(conn, ref)
        if (not plan or plan['status'] != 'pending' or not period
                or plan['generation'] != expected_plan['generation']
                or plan['config_version'] != expected_plan['config_version']
                or period != expected_period or period['trigger_produced_at'] is not None
                or plan['finished_at'] != period['last_turn_finished_at']):
            return False
        delay = recheck(conn, plan, period)
        if delay is None:
            return False
        conn.execute("UPDATE secretary_adaptive_plans SET status='invalidated' WHERE conversation_ref=?",
                     (ref,))
        conn.execute('UPDATE secretary_noting_idle_state SET due_at=?,updated_at=? WHERE conversation_ref=?',
                     (period['last_turn_finished_at'] + delay, time.time(), ref))
        return True
    return db._execute_write(write)


def remember_heartbeat_config_conn(conn, ref, config):
    """Freeze only a target's configured numeric period, on existing writes."""
    from secretary.adaptive_features import number
    hot = number(config.get('hot_interval_seconds'), minimum=60)
    source = config.get('_hot_interval_source')
    if hot is None or not source:
        return
    event_conn(conn, ref, dict(event_id='heartbeat-config:' + config['config_version'],
                               at=config.get('_configured_at', time.time()), kind='heartbeat_config',
                               source='framework', verified=True, hot_interval_seconds=hot,
                               provenance=source, config_version=config['config_version'],
                               model_identity=config.get('model_identity'),
                               model_contract=config.get('model_contract')))
