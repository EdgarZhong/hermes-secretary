"""Durable ConversationScheduleRegistry rows and pending System Reminder state.

Secretary-owned additions to the owning profile's ``state.db``: fast-changing Schedule
runtime state (claims, next run, delivery accounting) is separated from the immutable
Notebook Snapshot payloads, and routing information (platform / chat / user) is never
stored — it is resolved only at delivery time through the Conversation Ref.

Every function here takes the caller's connection so it can run inside an existing
``_execute_write`` transaction (Notebook mutation, busy conversion, request-time ACK).
"""

import json
import time
import uuid
from datetime import datetime, timezone

SCHEDULE_STATE_PENDING = "pending"
SCHEDULE_STATE_DONE = "done"
SCHEDULE_STATE_CANCELLED = "cancelled"
REMINDER_STATUS_PENDING = "pending"
REMINDER_STATUS_DELIVERED = "delivered"

SECRETARY_SCHEDULE_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS secretary_schedule_registry (
    schedule_id TEXT PRIMARY KEY,
    conversation_ref TEXT NOT NULL REFERENCES secretary_conversations(conversation_ref),
    notebook_entry_id TEXT NOT NULL,
    profile TEXT,
    canonical_schedule TEXT NOT NULL,
    delivery_semantics TEXT NOT NULL,
    reminder_text TEXT,
    state TEXT NOT NULL DEFAULT 'pending',
    enabled INTEGER NOT NULL DEFAULT 1,
    next_run_at REAL,
    last_fired_at REAL,
    claim_owner TEXT,
    claim_token TEXT,
    claim_attempts INTEGER NOT NULL DEFAULT 0,
    claim_expires_at REAL,
    updated_at REAL NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_secretary_sched_entry
    ON secretary_schedule_registry(conversation_ref, notebook_entry_id);
CREATE INDEX IF NOT EXISTS idx_secretary_sched_due
    ON secretary_schedule_registry(state, enabled, next_run_at);
CREATE TABLE IF NOT EXISTS secretary_pending_reminders (
    reminder_id TEXT PRIMARY KEY,
    conversation_ref TEXT NOT NULL,
    schedule_id TEXT,
    dedup_key TEXT NOT NULL DEFAULT '',
    delivery_semantics TEXT NOT NULL,
    source_timestamp REAL NOT NULL,
    content TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    created_at REAL NOT NULL,
    delivered_at REAL,
    acknowledged_at REAL
);
CREATE INDEX IF NOT EXISTS idx_secretary_reminder_pending
    ON secretary_pending_reminders(conversation_ref, status);
CREATE INDEX IF NOT EXISTS idx_secretary_reminder_dedup
    ON secretary_pending_reminders(conversation_ref, dedup_key, status);
"""


def init_secretary_schedule_schema(cursor):
    """Execute statement-by-statement, preserving the caller's transaction."""
    for statement in SECRETARY_SCHEDULE_SCHEMA_SQL.split(";"):
        if statement.strip():
            cursor.execute(statement)


def _now(now=None):
    return time.time() if now is None else float(now)


def iso_to_epoch(value):
    """Canonical schedule instants are timezone-aware ISO strings (cron parsing guarantees it)."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("A canonical schedule instant must include a timezone")
    return parsed.timestamp()


def epoch_to_utc_iso(timestamp):
    return datetime.fromtimestamp(float(timestamp), tz=timezone.utc).isoformat()


def render_source_timestamp(timestamp):
    """ISO 8601 with a UTC offset for the §5.6 reminder wrappers."""
    return datetime.fromtimestamp(float(timestamp)).astimezone().isoformat()


def _schedule_row(conn, schedule_id):
    row = conn.execute(
        "SELECT * FROM secretary_schedule_registry WHERE schedule_id = ?", (schedule_id,),
    ).fetchone()
    return dict(row) if row is not None else None


def _canonical_json(canonical_schedule):
    if not isinstance(canonical_schedule, dict):
        raise ValueError("Canonical schedule must be an object")
    return json.dumps(canonical_schedule, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def schedule_sync_conn(
    conn, conversation_ref, entry_id, *, active, canonical_schedule=None, delivery_semantics=None,
    reminder_text=None, cancelled=False, profile=None, now=None,
):
    """Register/update/disable one Notebook entry's Schedule runtime row in the caller's transaction.

    The intent itself lives in the Notebook; this only mirrors fast-changing runtime state.
    A disabled row keeps its identity, intent and next run — ``/notebook on`` re-enables it
    without recreating anything, and an overdue one-shot then fires at most once.
    """
    timestamp = _now(now)
    row = conn.execute(
        "SELECT * FROM secretary_schedule_registry WHERE conversation_ref = ? AND notebook_entry_id = ?",
        (conversation_ref, entry_id),
    ).fetchone()
    if row is None:
        if not active or canonical_schedule is None or delivery_semantics is None:
            return None
        schedule_id = "sched_" + uuid.uuid4().hex
        conn.execute(
            "INSERT INTO secretary_schedule_registry (schedule_id, conversation_ref, notebook_entry_id, profile, "
            "canonical_schedule, delivery_semantics, reminder_text, state, enabled, next_run_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (schedule_id, conversation_ref, entry_id, profile, _canonical_json(canonical_schedule),
             delivery_semantics, reminder_text, SCHEDULE_STATE_PENDING, 1,
             schedule_initial_next_run(canonical_schedule, now=timestamp), timestamp),
        )
        return _schedule_row(conn, schedule_id)
    row = dict(row)
    if cancelled or not active or canonical_schedule is None or delivery_semantics is None:
        state = SCHEDULE_STATE_CANCELLED if cancelled else row["state"]
        conn.execute(
            "UPDATE secretary_schedule_registry SET state = ?, enabled = 0, updated_at = ? WHERE schedule_id = ?",
            (state, timestamp, row["schedule_id"]),
        )
        return _schedule_row(conn, row["schedule_id"])
    payload = _canonical_json(canonical_schedule)
    changed = payload != row["canonical_schedule"] or row["delivery_semantics"] != delivery_semantics
    rearm = changed or row["state"] == SCHEDULE_STATE_CANCELLED
    if rearm:
        conn.execute(
            "UPDATE secretary_schedule_registry SET canonical_schedule = ?, delivery_semantics = ?, reminder_text = ?, "
            "state = ?, enabled = 1, next_run_at = ?, claim_owner = NULL, claim_token = NULL, claim_expires_at = NULL, "
            "updated_at = ? WHERE schedule_id = ?",
            (payload, delivery_semantics, reminder_text, SCHEDULE_STATE_PENDING,
             schedule_initial_next_run(canonical_schedule, now=timestamp), timestamp, row["schedule_id"]),
        )
    else:
        next_run_at = row["next_run_at"]
        if next_run_at is None and row["state"] == SCHEDULE_STATE_PENDING:
            next_run_at = schedule_initial_next_run(canonical_schedule, now=timestamp)
        conn.execute(
            "UPDATE secretary_schedule_registry SET delivery_semantics = ?, reminder_text = ?, enabled = 1, "
            "next_run_at = ?, updated_at = ? WHERE schedule_id = ?",
            (delivery_semantics, reminder_text, next_run_at, timestamp, row["schedule_id"]),
        )
    return _schedule_row(conn, row["schedule_id"])


def schedule_initial_next_run(canonical_schedule, *, now=None):
    """First fire instant for a freshly registered intent, as an epoch float.

    A one-shot keeps its stated instant (an overdue one fires once when it becomes eligible);
    recurring intents anchor on now via the shared Cron next-run utility.
    """
    kind = canonical_schedule.get("kind")
    if kind == "once":
        return iso_to_epoch(canonical_schedule.get("run_at"))
    from cron.jobs import compute_next_run

    nxt = compute_next_run(canonical_schedule, None)
    return iso_to_epoch(nxt) if nxt is not None else None


def schedule_advance_epoch(canonical_schedule, previous_next_run, *, now, max_steps=1000):
    """Next fire strictly after *now*, anchored on the previous occurrence (bounded backlog skip).

    Recurring schedules never replay an unbounded backlog: missed occurrences are advanced
    through (up to *max_steps*, preserving wall-clock phase) and then re-anchored on now.
    """
    from cron.jobs import compute_next_run

    anchor = epoch_to_utc_iso(previous_next_run) if previous_next_run else None
    for _ in range(max_steps):
        nxt = compute_next_run(canonical_schedule, anchor)
        if nxt is None:
            return None
        instant = iso_to_epoch(nxt)
        if instant > now:
            return instant
        anchor = nxt
    nxt = compute_next_run(canonical_schedule, None)
    return iso_to_epoch(nxt) if nxt is not None else None


def schedule_due_scan_conn(conn, *, now, limit=50, profile=None, conversation_ref=None):
    """Read-only view of currently claimable occurrences (claimability re-checked inside claim)."""
    sql = (
        "SELECT * FROM secretary_schedule_registry WHERE state = 'pending' AND enabled = 1 "
        "AND next_run_at IS NOT NULL AND next_run_at <= ? "
        "AND (claim_expires_at IS NULL OR claim_expires_at <= ?)"
    )
    params = [now, now]
    if profile is not None:
        sql += " AND (profile IS NULL OR profile = ?)"
        params.append(profile)
    if conversation_ref is not None:
        sql += " AND conversation_ref = ?"
        params.append(conversation_ref)
    sql += " ORDER BY next_run_at LIMIT ?"
    params.append(int(limit))
    return [dict(row) for row in conn.execute(sql, params).fetchall()]


def schedule_claim_conn(conn, schedule_id, *, owner, now, lease_seconds):
    """Atomically claim one due occurrence. Caller holds a write transaction; one winner only."""
    token = uuid.uuid4().hex
    cursor = conn.execute(
        "UPDATE secretary_schedule_registry SET claim_owner = ?, claim_token = ?, "
        "claim_attempts = claim_attempts + 1, claim_expires_at = ?, updated_at = ? "
        "WHERE schedule_id = ? AND state = 'pending' AND enabled = 1 "
        "AND next_run_at IS NOT NULL AND next_run_at <= ? "
        "AND (claim_token IS NULL OR claim_expires_at IS NULL OR claim_expires_at <= ?)",
        (owner, token, now + lease_seconds, now, schedule_id, now, now),
    )
    if cursor.rowcount != 1:
        return None
    return _schedule_row(conn, schedule_id)


def schedule_finalize_conn(conn, schedule_id, claim_token, *, now):
    """Account one successfully delivered occurrence: terminalize one-shots, advance recurring."""
    if not claim_token:
        return None
    row = _schedule_row(conn, schedule_id)
    if row is None or row["claim_token"] != claim_token:
        return None
    try:
        canonical = json.loads(row["canonical_schedule"])
        kind = canonical.get("kind") if isinstance(canonical, dict) else None
    except (TypeError, ValueError):
        kind = None
    if kind not in {"once", "interval", "cron"}:
        # Unusable runtime row: stop re-claiming it. The Notebook intent is untouched and a
        # changed intent re-arms the row on the next Notebook reconcile.
        conn.execute(
            "UPDATE secretary_schedule_registry SET state = ?, enabled = 0, last_fired_at = ?, "
            "claim_owner = NULL, claim_token = NULL, claim_expires_at = NULL, updated_at = ? WHERE schedule_id = ?",
            (SCHEDULE_STATE_CANCELLED, now, now, schedule_id),
        )
        return _schedule_row(conn, schedule_id)
    if kind == "once":
        state, next_run_at = SCHEDULE_STATE_DONE, None
    else:
        state = SCHEDULE_STATE_PENDING
        next_run_at = schedule_advance_epoch(
            canonical, row["next_run_at"], now=now, max_steps=1000,
        )
    conn.execute(
        "UPDATE secretary_schedule_registry SET state = ?, next_run_at = ?, last_fired_at = ?, "
        "claim_owner = NULL, claim_token = NULL, claim_expires_at = NULL, updated_at = ? WHERE schedule_id = ?",
        (state, next_run_at, now, now, schedule_id),
    )
    return _schedule_row(conn, schedule_id)


def schedule_release_conn(conn, schedule_id, claim_token, *, now):
    """Give back a claim whose delivery failed: the occurrence stays due and is retried."""
    if not claim_token:
        return False
    cursor = conn.execute(
        "UPDATE secretary_schedule_registry SET claim_owner = NULL, claim_token = NULL, claim_expires_at = NULL, "
        "updated_at = ? WHERE schedule_id = ? AND claim_token = ?",
        (now, schedule_id, claim_token),
    )
    return cursor.rowcount == 1


def reminder_append_pending_conn(
    conn, conversation_ref, content, *, source_timestamp, schedule_id=None, dedup_key=None,
    delivery_semantics="system_reminder", now=None,
):
    """Durably queue one pending System Reminder. Idempotent per (conversation, dedup key)."""
    timestamp = _now(now)
    key = dedup_key if dedup_key is not None else (schedule_id or "")
    if key:
        existing = conn.execute(
            "SELECT reminder_id FROM secretary_pending_reminders WHERE conversation_ref = ? "
            "AND dedup_key = ? AND status = 'pending' ORDER BY created_at LIMIT 1",
            (conversation_ref, key),
        ).fetchone()
        if existing is not None:
            return existing[0]
    reminder_id = "rem_" + uuid.uuid4().hex
    conn.execute(
        "INSERT INTO secretary_pending_reminders (reminder_id, conversation_ref, schedule_id, dedup_key, "
        "delivery_semantics, source_timestamp, content, status, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (reminder_id, conversation_ref, schedule_id, key, delivery_semantics,
         float(source_timestamp), content, REMINDER_STATUS_PENDING, timestamp),
    )
    return reminder_id


def reminder_pull_pending_conn(conn, conversation_ref):
    """Pending System Reminders for one Conversation, oldest first, as complete carriers."""
    rows = conn.execute(
        "SELECT * FROM secretary_pending_reminders WHERE conversation_ref = ? AND status = 'pending' "
        "ORDER BY created_at, reminder_id",
        (conversation_ref,),
    ).fetchall()
    return [
        {
            "reminder_id": row["reminder_id"],
            "text": build_system_reminder_text(row["content"], row["source_timestamp"]),
            "content": row["content"],
            "source_timestamp": float(row["source_timestamp"]),
            "delivery_semantics": row["delivery_semantics"],
            "schedule_id": row["schedule_id"],
        }
        for row in rows
    ]


def reminder_ack_conn(conn, reminder_id, *, now=None):
    """Acknowledge delivery after a successful model response; failures leave the row pending."""
    timestamp = _now(now)
    cursor = conn.execute(
        "UPDATE secretary_pending_reminders SET status = ?, delivered_at = COALESCE(delivered_at, ?), "
        "acknowledged_at = ? WHERE reminder_id = ? AND status = ?",
        (REMINDER_STATUS_DELIVERED, timestamp, timestamp, reminder_id, REMINDER_STATUS_PENDING),
    )
    if cursor.rowcount == 1:
        return True
    row = conn.execute(
        "SELECT status FROM secretary_pending_reminders WHERE reminder_id = ?", (reminder_id,),
    ).fetchone()
    return bool(row is not None and row[0] == REMINDER_STATUS_DELIVERED)


def reminder_pending_count_conn(conn, conversation_ref):
    row = conn.execute(
        "SELECT COUNT(*) FROM secretary_pending_reminders WHERE conversation_ref = ? AND status = ?",
        (conversation_ref, REMINDER_STATUS_PENDING),
    ).fetchone()
    return int(row[0])


def build_system_reminder_text(content, source_timestamp):
    """The §5.6 request-only carrier: complete wrapper, timestamp as the first line inside."""
    return (
        "<system-reminder>\n"
        f"<timestamp>{render_source_timestamp(source_timestamp)}</timestamp>\n"
        f"{content}\n"
        "</system-reminder>"
    )


def build_user_reminder_text(content, source_timestamp):
    """The §5.6 active carrier for an idle User Reminder admission."""
    return (
        "<user-reminder>\n"
        f"<timestamp>{render_source_timestamp(source_timestamp)}</timestamp>\n"
        f"{content}\n"
        "</user-reminder>"
    )


class SecretaryScheduleMixin:
    """SessionDB sibling: the same primitives bound to ``self`` for T2B/T3C call sites."""

    def init_secretary_schedule_conn(self, conn):
        init_secretary_schedule_schema(conn)

    def schedule_sync_conn(self, conn, conversation_ref, entry_id, **kwargs):
        return schedule_sync_conn(conn, conversation_ref, entry_id, **kwargs)

    def schedule_due_scan_conn(self, conn, **kwargs):
        return schedule_due_scan_conn(conn, **kwargs)

    def schedule_claim_conn(self, conn, schedule_id, **kwargs):
        return schedule_claim_conn(conn, schedule_id, **kwargs)

    def schedule_finalize_conn(self, conn, schedule_id, claim_token, **kwargs):
        return schedule_finalize_conn(conn, schedule_id, claim_token, **kwargs)

    def schedule_release_conn(self, conn, schedule_id, claim_token, **kwargs):
        return schedule_release_conn(conn, schedule_id, claim_token, **kwargs)

    def reminder_append_pending_conn(self, conn, conversation_ref, content, **kwargs):
        return reminder_append_pending_conn(conn, conversation_ref, content, **kwargs)

    def reminder_pull_pending_conn(self, conn, conversation_ref):
        return reminder_pull_pending_conn(conn, conversation_ref)

    def reminder_ack_conn(self, conn, reminder_id, **kwargs):
        return reminder_ack_conn(conn, reminder_id, **kwargs)

    def reminder_pending_count_conn(self, conn, conversation_ref):
        return reminder_pending_count_conn(conn, conversation_ref)
