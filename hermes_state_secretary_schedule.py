"""Independent Conversation Schedule definitions and durable occurrence accounting.

Only Secretary-owned tables change. All *_conn functions participate in the caller's
existing transaction; they never commit, open another connection, or acquire host locks.
C6 must revalidate and bind carriers INSIDE native transcript append transactions and
apply the independent Scheduler gate before new admission. ACK requires actual carriage
and a successful provider response at the existing caller; a claim alone is not delivery.
No migration of the former Notebook-owned registry is attempted.
"""

import json
import uuid

from secretary.scheduler_time import (
    epoch as _now,
    epoch_to_utc_iso,
    iso_to_epoch,
    schedule_advance_epoch,
    schedule_initial_next_run as schedule_initial_next_run,
    validate_canonical_schedule,
)

SCHEDULE_STATE_PENDING = "pending"
SCHEDULE_STATE_DONE = "done"
SCHEDULE_STATE_CANCELLED = "cancelled"
REMINDER_STATUS_PENDING = "pending"
REMINDER_STATUS_DELIVERED = "delivered"

SECRETARY_SCHEDULE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS secretary_schedule_registry (
    schedule_id TEXT PRIMARY KEY,
    conversation_ref TEXT NOT NULL REFERENCES secretary_conversations(conversation_ref),
    profile TEXT,
    name TEXT NOT NULL DEFAULT '',
    expression TEXT NOT NULL,
    canonical_schedule TEXT NOT NULL,
    delivery_semantics TEXT NOT NULL,
    reminder_text TEXT NOT NULL,
    generation INTEGER NOT NULL DEFAULT 1,
    sequence INTEGER NOT NULL DEFAULT 1,
    state TEXT NOT NULL DEFAULT 'pending',
    enabled INTEGER NOT NULL DEFAULT 1,
    next_run_at REAL,
    last_fired_at REAL,
    once_consumed_at REAL,
    last_delivery_at REAL,
    last_delivery_outcome TEXT,
    claim_owner TEXT,
    claim_token TEXT,
    claim_attempts INTEGER NOT NULL DEFAULT 0,
    claim_expires_at REAL,
    updated_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_secretary_sched_owner
    ON secretary_schedule_registry(conversation_ref, schedule_id);
CREATE INDEX IF NOT EXISTS idx_secretary_sched_due
    ON secretary_schedule_registry(state, enabled, next_run_at);
CREATE TABLE IF NOT EXISTS secretary_pending_reminders (
    reminder_id TEXT PRIMARY KEY,
    conversation_ref TEXT NOT NULL,
    schedule_id TEXT,
    schedule_generation INTEGER,
    schedule_sequence INTEGER,
    origin_instant INTEGER NOT NULL DEFAULT 0,
    dedup_key TEXT NOT NULL DEFAULT '',
    delivery_semantics TEXT NOT NULL,
    source_timestamp REAL NOT NULL,
    content TEXT NOT NULL,
    entry_payload TEXT,
    carrier_content TEXT,
    carrier_message_uid TEXT,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at REAL NOT NULL,
    delivered_at REAL,
    acknowledged_at REAL
);
CREATE INDEX IF NOT EXISTS idx_secretary_reminder_pending
    ON secretary_pending_reminders(conversation_ref, status);
CREATE INDEX IF NOT EXISTS idx_secretary_reminder_dedup
    ON secretary_pending_reminders(conversation_ref, dedup_key, status);
CREATE INDEX IF NOT EXISTS idx_secretary_reminder_schedule
    ON secretary_pending_reminders(schedule_id, schedule_generation, status);
"""


class ScheduleError(ValueError):
    """Diagnosable, safe tool failure; callers roll back the complete operation."""

    def __init__(self, code, message, next_action, *, field=None, details=None):
        super().__init__(message)
        self.error = {"code": code, "message": message, "next_action": next_action}
        if field is not None:
            self.error["field"] = field
        if details is not None:
            self.error["details"] = details


def init_secretary_schedule_schema(cursor):
    for statement in SECRETARY_SCHEDULE_SCHEMA_SQL.split(";"):
        if statement.strip():
            cursor.execute(statement)


def render_source_timestamp(timestamp, *, profile_home=None):
    from hermes_time import format_timestamp

    return format_timestamp(timestamp, profile_home=profile_home)


def _canonical_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def schedule_definition_conn(conn, conversation_ref, schedule_id):
    """Owner-scoped current definition; absent/foreign IDs are indistinguishable."""
    row = conn.execute(
        "SELECT * FROM secretary_schedule_registry WHERE conversation_ref=? AND schedule_id=?",
        (conversation_ref, schedule_id),
    ).fetchone()
    return dict(row) if row is not None else None


def schedule_current_claim_conn(conn, claim, *, now):
    """Revalidate the precise current definition, occurrence and unexpired lease.

    Returns its current row or None for a stale witness. Database errors propagate;
    they must not be treated as an empty or successfully delivered occurrence.
    """
    row = schedule_definition_conn(conn, claim.get("conversation_ref"), claim.get("schedule_id"))
    if row is None or row["state"] != SCHEDULE_STATE_PENDING or not row["enabled"]:
        return None
    keys = ("generation", "sequence", "claim_token", "next_run_at")
    if not row["claim_token"] or any(row[key] != claim.get(key) for key in keys):
        return None
    timestamp = _now(now)
    if (row["next_run_at"] is None or row["next_run_at"] > timestamp
            or row["claim_expires_at"] is None or row["claim_expires_at"] <= timestamp):
        return None
    return row


def schedule_due_scan_conn(conn, *, now, limit=50, profile=None, conversation_ref=None):
    sql = (
        "SELECT * FROM secretary_schedule_registry WHERE state='pending' AND enabled=1 "
        "AND next_run_at IS NOT NULL AND next_run_at<=? "
        "AND (claim_token IS NULL OR claim_expires_at IS NULL OR claim_expires_at<=?)"
    )
    params = [_now(now), _now(now)]
    if profile is not None:
        sql += " AND profile=?"
        params.append(profile)
    if conversation_ref is not None:
        sql += " AND conversation_ref=?"
        params.append(conversation_ref)
    sql += " ORDER BY next_run_at, schedule_id LIMIT ?"
    params.append(int(limit))
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def schedule_claim_conn(conn, schedule_id, *, owner, now, lease_seconds,
                        conversation_ref=None, expected_generation=None):
    """One atomic lease winner; optional scan witness prevents claiming a new definition."""
    timestamp, lease = _now(now), _now(lease_seconds)
    if not isinstance(owner, str) or not owner or lease <= 0:
        raise ValueError("A claim requires an owner and a positive finite lease")
    sql = (
        "UPDATE secretary_schedule_registry SET claim_owner=?, claim_token=?, "
        "claim_attempts=claim_attempts+1, claim_expires_at=?, updated_at=? "
        "WHERE schedule_id=? AND state='pending' AND enabled=1 "
        "AND next_run_at IS NOT NULL AND next_run_at<=? "
        "AND (claim_token IS NULL OR claim_expires_at IS NULL OR claim_expires_at<=?)"
    )
    token = uuid.uuid4().hex
    params = [owner, token, timestamp + lease, timestamp, schedule_id, timestamp, timestamp]
    if conversation_ref is not None:
        sql += " AND conversation_ref=?"
        params.append(conversation_ref)
    if expected_generation is not None:
        sql += " AND generation=?"
        params.append(expected_generation)
    if conn.execute(sql, params).rowcount != 1:
        return None
    return dict(conn.execute("SELECT * FROM secretary_schedule_registry WHERE schedule_id=?", (schedule_id,)).fetchone())


def occurrence_key(row):
    return f"{row['schedule_id']}:{row['sequence']}:{epoch_to_utc_iso(row['next_run_at'])}"


def occurrence_payload(row):
    payload = {"schedule_id": row["schedule_id"], "content": row["reminder_text"],
               "delivery_mode": "instant" if row["delivery_semantics"] == "user_reminder" else "deferred"}
    if row["name"]:
        payload["name"] = row["name"]
    return payload


def reminder_append_pending_conn(
    conn, conversation_ref, content, *, source_timestamp, schedule_id=None, dedup_key=None,
    delivery_semantics="system_reminder", entry_payload=None, now=None,
    schedule_generation=None, schedule_sequence=None, origin_instant=False,
):
    """Durable occurrence insert. Scheduled callers must supply a current definition witness.

    Normal due workers use schedule_queue_pending_conn, which also settles their lease
    atomically. Unscheduled internal notices retain the existing generic pending lane.
    """
    if schedule_id is not None:
        current = schedule_definition_conn(conn, conversation_ref, schedule_id)
        if (current is None or not current["enabled"] or current["state"] != SCHEDULE_STATE_PENDING
                or current["generation"] != schedule_generation or current["sequence"] != schedule_sequence):
            raise ScheduleError("state_conflict", "The Schedule definition changed before queueing.",
                                "Discard the stale occurrence and let the normal due scan retry.")
    key = dedup_key if dedup_key is not None else (schedule_id or "")
    if key:
        previous = conn.execute(
            "SELECT reminder_id FROM secretary_pending_reminders "
            "WHERE conversation_ref=? AND dedup_key=? ORDER BY created_at LIMIT 1",
            (conversation_ref, key),
        ).fetchone()
        if previous is not None:
            return previous["reminder_id"]
    reminder_id = "rem_" + uuid.uuid4().hex
    conn.execute(
        "INSERT INTO secretary_pending_reminders "
        "(reminder_id,conversation_ref,schedule_id,schedule_generation,schedule_sequence,origin_instant,"
        "dedup_key,delivery_semantics,source_timestamp,content,entry_payload,status,created_at) "
        "VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
        (reminder_id, conversation_ref, schedule_id, schedule_generation, schedule_sequence,
         int(bool(origin_instant)), key, delivery_semantics, iso_to_epoch(source_timestamp), content,
         _canonical_json(entry_payload) if entry_payload is not None else None,
         REMINDER_STATUS_PENDING, _now(now)),
    )
    return reminder_id


def _require_native_carrier_conn(conn, conversation_ref, uid, content):
    row = conn.execute(
        "SELECT m.role, m.content FROM messages m JOIN secretary_session_bindings b "
        "ON b.session_id=m.session_id WHERE b.conversation_ref=? AND m.message_uid=? "
        "AND m.active=1 ORDER BY m.id DESC LIMIT 1",
        (conversation_ref, uid),
    ).fetchone()
    if row is None or row["role"] != "user" or row["content"] != content:
        raise ScheduleError("state_conflict", "The native Reminder carrier is not durably bound to this Conversation.",
                            "Persist and bind the exact carrier in the same native transaction.")


def schedule_carrier_durable_conn(conn, conversation_ref, schedule_id, uid, content):
    """C6 witness recovery: prove the receipt and native row, NOT today's mutable definition.

    A legitimate pause/delete after native commit does not invalidate that commit.
    Compaction may retire the carrier from active context without undoing durability.
    """
    return conn.execute(
        "SELECT 1 FROM secretary_pending_reminders p WHERE p.conversation_ref=? AND p.schedule_id=? "
        "AND p.carrier_message_uid=? AND p.carrier_content=? AND EXISTS ("
        "SELECT 1 FROM messages m JOIN secretary_session_bindings b ON b.session_id=m.session_id "
        "WHERE b.conversation_ref=p.conversation_ref AND m.message_uid=p.carrier_message_uid "
        "AND m.role='user' AND m.content=p.carrier_content) LIMIT 1",
        (conversation_ref, schedule_id, uid, content),
    ).fetchone() is not None


def schedule_finalize_conn(conn, schedule_id, claim_token, *, now, queued=False,
                           carrier_message_uid=None, carrier_content=None):
    """Settle a due lease after durable pending insert or a proven native instant row.

    queued=True is NOT delivery or completion: an unmaterialized one-shot remains
    active with next_run_at=None. Direct instant settlement requires the exact native
    carrier. C6 supplies it in ActiveReminderAdmission.commit's existing transaction.
    """
    if not claim_token:
        return None
    found = conn.execute("SELECT * FROM secretary_schedule_registry WHERE schedule_id=?", (schedule_id,)).fetchone()
    if found is None or found["claim_token"] != claim_token:
        return None
    row = schedule_current_claim_conn(conn, dict(found), now=now)
    if row is None:
        return None
    canonical = json.loads(row["canonical_schedule"])
    validate_canonical_schedule(canonical)
    timestamp = _now(now)
    next_run = (None if canonical["kind"] == "once" else
                schedule_advance_epoch(canonical, row["next_run_at"], now=timestamp))
    if queued:
        pending = conn.execute(
            "SELECT 1 FROM secretary_pending_reminders WHERE conversation_ref=? AND dedup_key=? "
            "AND schedule_generation=? AND status='pending' AND carrier_message_uid IS NULL",
            (row["conversation_ref"], occurrence_key(row), row["generation"]),
        ).fetchone()
        if pending is None:
            raise ScheduleError("state_conflict", "The occurrence has no durable pending receipt.",
                                "Queue and settle the current claim in one transaction.")
    else:
        if row["delivery_semantics"] != "user_reminder":
            raise ScheduleError("state_conflict", "A deferred Schedule cannot be settled as an instant invocation.",
                                "Use the existing pending Reminder lane for deferred delivery.")
        if not carrier_message_uid or not isinstance(carrier_content, str):
            raise ScheduleError("state_conflict", "An instant claim is not proof of delivery.",
                                "Supply the native persisted carrier when settling this claim.")
        _require_native_carrier_conn(conn, row["conversation_ref"], carrier_message_uid, carrier_content)
        rid = reminder_append_pending_conn(
            conn, row["conversation_ref"], row["reminder_text"], source_timestamp=row["next_run_at"],
            schedule_id=schedule_id, dedup_key=occurrence_key(row), delivery_semantics="user_reminder",
            entry_payload=occurrence_payload(row), schedule_generation=row["generation"],
            schedule_sequence=row["sequence"], origin_instant=True, now=timestamp,
        )
        conn.execute(
            "UPDATE secretary_pending_reminders SET status='delivered', delivered_at=?, "
            "carrier_message_uid=?, carrier_content=? WHERE reminder_id=?",
            (timestamp, carrier_message_uid, carrier_content, rid),
        )
    completed = canonical["kind"] == "once" and not queued
    conn.execute(
        "UPDATE secretary_schedule_registry SET state=?, next_run_at=?, last_fired_at=?, "
        "once_consumed_at=CASE WHEN ? THEN ? ELSE once_consumed_at END, "
        "last_delivery_at=CASE WHEN ? THEN last_delivery_at ELSE ? END, "
        "last_delivery_outcome=CASE WHEN ? THEN last_delivery_outcome ELSE 'admitted' END, "
        "claim_owner=NULL,claim_token=NULL,claim_expires_at=NULL,updated_at=? WHERE schedule_id=? AND claim_token=?",
        (SCHEDULE_STATE_DONE if completed else SCHEDULE_STATE_PENDING, next_run, timestamp,
         int(completed), timestamp, int(queued), timestamp, int(queued), timestamp, schedule_id, claim_token),
    )
    return schedule_definition_conn(conn, row["conversation_ref"], schedule_id)


def schedule_queue_pending_conn(conn, claim, *, now):
    """Current content + original instant flag + occurrence advance in one transaction."""
    current = schedule_current_claim_conn(conn, claim, now=now)
    if current is None:
        return None
    rid = reminder_append_pending_conn(
        conn, current["conversation_ref"], current["reminder_text"],
        source_timestamp=current["next_run_at"], schedule_id=current["schedule_id"],
        dedup_key=occurrence_key(current), entry_payload=occurrence_payload(current),
        schedule_generation=current["generation"], schedule_sequence=current["sequence"],
        origin_instant=current["delivery_semantics"] == "user_reminder", now=now,
    )
    if schedule_finalize_conn(conn, current["schedule_id"], current["claim_token"], now=now, queued=True) is None:
        raise ScheduleError("state_conflict", "The claim changed before pending settlement.",
                            "Let the normal due scanner retry the current definition.")
    return rid


def schedule_release_conn(conn, schedule_id, claim_token, *, now):
    """Failure releases only this token; old workers cannot change a replacement definition."""
    if not claim_token:
        return False
    timestamp = _now(now)
    return conn.execute(
        "UPDATE secretary_schedule_registry SET claim_owner=NULL,claim_token=NULL,claim_expires_at=NULL, "
        "last_delivery_at=?,last_delivery_outcome='failed',updated_at=? WHERE schedule_id=? AND claim_token=?",
        (timestamp, timestamp, schedule_id, claim_token),
    ).rowcount == 1


def reminder_revalidate_pending_conn(conn, conversation_ref, reminder_id):
    """Read the CURRENT occurrence before materializing, not the prepare-time payload.

    Already admitted carriers survive definition edits/deletion. Fresh rows require
    the current active generation. None means withdrawn/stale; read failures raise.
    """
    found = conn.execute(
        "SELECT * FROM secretary_pending_reminders WHERE conversation_ref=? AND reminder_id=? AND status='pending'",
        (conversation_ref, reminder_id),
    ).fetchone()
    if found is None:
        return None
    row = dict(found)
    if row["carrier_message_uid"] is None and row["schedule_id"] is not None:
        current = schedule_definition_conn(conn, conversation_ref, row["schedule_id"])
        if (current is None or not current["enabled"] or current["state"] != SCHEDULE_STATE_PENDING
                or row["schedule_generation"] != current["generation"]
                or row["schedule_sequence"] != current["sequence"]):
            return None
    row["entry_payload"] = json.loads(row["entry_payload"]) if row["entry_payload"] else None
    row["origin_instant"] = bool(row["origin_instant"])
    return row


def reminder_bind_carrier_conn(conn, conversation_ref, rows, *, carrier_message_uid, carrier_content, now):
    """Bind a whole revalidated batch to its native row in the SAME append transaction.

    C6 constructs the body from revalidate results inside that transaction, appends
    the native row, then calls this before commit/live publication. Any stale member
    rejects the whole append, rather than binding old text to a refreshed receipt.
    """
    current_rows = []
    keys = ("schedule_id", "schedule_generation", "schedule_sequence", "source_timestamp",
            "content", "entry_payload", "origin_instant", "carrier_message_uid")
    for previous in rows:
        current = reminder_revalidate_pending_conn(conn, conversation_ref, previous["reminder_id"])
        if current is None or any(current[key] != previous.get(key) for key in keys):
            raise ScheduleError("state_conflict", "A Reminder changed before native materialization.",
                                "Re-read the current pending batch before building its carrier.")
        if current["carrier_message_uid"] not in (None, carrier_message_uid):
            raise ScheduleError("state_conflict", "This occurrence already has a native carrier.",
                                "Reuse the admitted carrier instead of appending another.")
        current_rows.append(current)
    _require_native_carrier_conn(conn, conversation_ref, carrier_message_uid, carrier_content)
    timestamp = _now(now)
    for row in current_rows:
        conn.execute(
            "UPDATE secretary_pending_reminders SET carrier_message_uid=?,carrier_content=?, "
            "delivered_at=COALESCE(delivered_at,?) WHERE reminder_id=? AND status='pending'",
            (carrier_message_uid, carrier_content, timestamp, row["reminder_id"]),
        )
        current = schedule_definition_conn(conn, conversation_ref, row["schedule_id"])
        if current is None or current["generation"] != row["schedule_generation"]:
            continue  # A pre-existing admitted carrier never resurrects its definition.
        once = json.loads(current["canonical_schedule"])["kind"] == "once"
        conn.execute(
            "UPDATE secretary_schedule_registry SET last_delivery_at=?,last_delivery_outcome='admitted', "
            "once_consumed_at=CASE WHEN ? THEN COALESCE(once_consumed_at,?) ELSE once_consumed_at END, "
            "state=CASE WHEN ? THEN 'done' ELSE state END,updated_at=? WHERE schedule_id=? AND generation=?",
            (timestamp, int(once), timestamp, int(once), timestamp, current["schedule_id"], current["generation"]),
        )
    return [row["reminder_id"] for row in current_rows]


def reminder_pull_pending_conn(conn, conversation_ref):
    ids = conn.execute(
        "SELECT reminder_id FROM secretary_pending_reminders WHERE conversation_ref=? AND status='pending' "
        "ORDER BY created_at,reminder_id", (conversation_ref,),
    ).fetchall()
    result = []
    for found in ids:
        row = reminder_revalidate_pending_conn(conn, conversation_ref, found[0])
        if row is not None:
            row["text"] = build_system_reminder_text(row["content"], row["source_timestamp"])
            result.append(row)
    return result


def reminder_ack_conn(conn, reminder_id, *, now=None):
    """ACK only admitted receipts; caller proves actual request carriage and response.

    Do not change state/enabled/next_run/generation here. A late successful response
    cannot revive a paused, deleted or rescheduled definition.
    """
    row = conn.execute("SELECT * FROM secretary_pending_reminders WHERE reminder_id=?", (reminder_id,)).fetchone()
    if row is None or row["carrier_message_uid"] is None:
        return False
    if row["status"] == REMINDER_STATUS_DELIVERED:
        return True
    if row["status"] != REMINDER_STATUS_PENDING:
        return False
    timestamp = _now(now)
    conn.execute(
        "UPDATE secretary_pending_reminders SET status='delivered',acknowledged_at=? WHERE reminder_id=?",
        (timestamp, reminder_id),
    )
    conn.execute(
        "UPDATE secretary_schedule_registry SET last_delivery_at=?,last_delivery_outcome='delivered' "
        "WHERE conversation_ref=? AND schedule_id=? AND generation=?",
        (timestamp, row["conversation_ref"], row["schedule_id"], row["schedule_generation"]),
    )
    return True


def reminder_settle_retired_conn(conn, conversation_ref):
    """Preserve native compacted-carrier retirement; never settle a missing carrier."""
    return conn.execute(
        "UPDATE secretary_pending_reminders SET status='terminated' "
        "WHERE conversation_ref=? AND status='pending' AND carrier_message_uid IS NOT NULL "
        "AND EXISTS (SELECT 1 FROM messages m JOIN secretary_session_bindings b "
        "ON b.session_id=m.session_id WHERE b.conversation_ref=? "
        "AND m.message_uid=carrier_message_uid AND m.compacted=1) "
        "AND NOT EXISTS (SELECT 1 FROM messages m JOIN secretary_session_bindings b "
        "ON b.session_id=m.session_id WHERE b.conversation_ref=? "
        "AND m.message_uid=carrier_message_uid AND m.active=1)",
        (conversation_ref, conversation_ref, conversation_ref),
    ).rowcount


def reminder_pending_count_conn(conn, conversation_ref):
    return int(conn.execute(
        "SELECT COUNT(*) FROM secretary_pending_reminders WHERE conversation_ref=? AND status='pending'",
        (conversation_ref,),
    ).fetchone()[0])


def build_system_reminder_text(content, source_timestamp):
    from agent.message_metadata import build_system_reminder_wrapper

    return build_system_reminder_wrapper(content, timestamp=source_timestamp)


def build_user_reminder_text(content, source_timestamp):
    from agent.message_metadata import build_user_reminder_wrapper

    return build_user_reminder_wrapper(content, timestamp=source_timestamp)


class SecretaryScheduleMixin:
    """SessionDB bindings; there is no Notebook sync/reconcile method anymore."""

    def init_secretary_schedule_conn(self, conn):
        init_secretary_schedule_schema(conn)

    def schedule_due_scan_conn(self, conn, **kwargs):
        return schedule_due_scan_conn(conn, **kwargs)

    def schedule_claim_conn(self, conn, schedule_id, **kwargs):
        return schedule_claim_conn(conn, schedule_id, **kwargs)

    def schedule_finalize_conn(self, conn, schedule_id, claim_token, **kwargs):
        return schedule_finalize_conn(conn, schedule_id, claim_token, **kwargs)

    def schedule_release_conn(self, conn, schedule_id, claim_token, **kwargs):
        return schedule_release_conn(conn, schedule_id, claim_token, **kwargs)

    def schedule_current_claim_conn(self, conn, claim, **kwargs):
        return schedule_current_claim_conn(conn, claim, **kwargs)

    def schedule_queue_pending_conn(self, conn, claim, **kwargs):
        return schedule_queue_pending_conn(conn, claim, **kwargs)

    def reminder_revalidate_pending_conn(self, conn, conversation_ref, reminder_id):
        return reminder_revalidate_pending_conn(conn, conversation_ref, reminder_id)

    def reminder_bind_carrier_conn(self, conn, conversation_ref, rows, **kwargs):
        return reminder_bind_carrier_conn(conn, conversation_ref, rows, **kwargs)

    def reminder_append_pending_conn(self, conn, conversation_ref, content, **kwargs):
        return reminder_append_pending_conn(conn, conversation_ref, content, **kwargs)

    def reminder_pull_pending_conn(self, conn, conversation_ref):
        return reminder_pull_pending_conn(conn, conversation_ref)

    def reminder_ack_conn(self, conn, reminder_id, **kwargs):
        return reminder_ack_conn(conn, reminder_id, **kwargs)

    def reminder_pending_count_conn(self, conn, conversation_ref):
        return reminder_pending_count_conn(conn, conversation_ref)
