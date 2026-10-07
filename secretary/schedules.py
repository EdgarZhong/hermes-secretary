"""ConversationScheduleRegistry service: Notebook reconcile, due scan, atomic claim, advance.

Schedule is an adjunct of Noting/Notebook. Intent lives in the Notebook (immutable Snapshot
payload); this service keeps the separate runtime registry synchronized inside the Notebook
service's own transaction, then scans/claims due occurrences for the host that delivers them.
"""

import logging
import time

from hermes_state_secretary_schedule import (
    SCHEDULE_STATE_CANCELLED,
    SCHEDULE_STATE_PENDING,
    schedule_advance_epoch,
    schedule_claim_conn,
    schedule_due_scan_conn,
    schedule_finalize_conn,
    schedule_initial_next_run,
    schedule_release_conn,
    schedule_sync_conn,
)
from secretary.notebook_schedule import SCHEDULE_TYPES, schedule_delivery_semantics

logger = logging.getLogger(__name__)

DEFAULT_CLAIM_LEASE_SECONDS = 3600.0
DEFAULT_DUE_BATCH = 50


def entry_reminder_text(entry):
    """Delivery text for one schedule-carrying entry, projected from its semantic fields.

    The Notebook remains the intent source; this projection is refreshed by every reconcile.
    """
    fields = entry.get("fields") or {}
    entry_type = entry.get("type")
    if entry_type == "user_reminder":
        return str(fields.get("message") or "").strip()
    if entry_type == "user_commitment":
        return f"Commitment due: {fields.get('what', '')}".strip()
    if entry_type == "agent_task":
        return f"Task due: {fields.get('task', '')}".strip()
    if entry_type == "watchpoint":
        return f"Watchpoint due: {fields.get('subject', '')} — {fields.get('what_to_watch', '')}".strip()
    return ""


def reconcile_entry(conn, conversation_ref, entry, *, active=True, now=None, reminder_text=None):
    """Mirror one Notebook entry's Schedule into the runtime registry, inside the caller's write.

    Called by the Notebook service after a semantic mutation; a no-intent or now-inactive entry
    disables (never deletes) its runtime row, and a cancelled intent is terminal until replaced.
    """
    intent = entry.get("schedule")
    cancelled = bool(isinstance(intent, dict) and intent.get("cancelled"))
    canonical = intent.get("canonical_schedule") if isinstance(intent, dict) else None
    semantics = schedule_delivery_semantics(entry)
    if cancelled or canonical is None or semantics is None:
        return schedule_sync_conn(
            conn, conversation_ref, entry["entry_id"], active=False, cancelled=cancelled, now=now,
        )
    return schedule_sync_conn(
        conn, conversation_ref, entry["entry_id"], active=bool(active), canonical_schedule=canonical,
        delivery_semantics=semantics, reminder_text=reminder_text or entry_reminder_text(entry), now=now,
    )


def reconcile_conversation(conn, conversation_ref, entries, *, active=True, now=None, complete=True):
    """Reconcile every schedule-carrying entry; optionally disable rows whose entry vanished."""
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict) or not entry.get("entry_id"):
            continue
        if entry.get("type") not in SCHEDULE_TYPES:
            continue
        seen.add(entry["entry_id"])
        reconcile_entry(conn, conversation_ref, entry, active=active, now=now)
    if not complete:
        return
    rows = conn.execute(
        "SELECT notebook_entry_id FROM secretary_schedule_registry WHERE conversation_ref = ?", (conversation_ref,),
    ).fetchall()
    for (entry_id,) in rows:
        if entry_id not in seen:
            schedule_sync_conn(conn, conversation_ref, entry_id, active=False, now=now)


def reconcile_payload(conn, conversation_ref, payload, *, active=True, now=None, complete=True):
    """Reconcile a committed Notebook Snapshot payload (the four-section state) in place.

    This is the call the Notebook commit transaction makes, so registry state and the
    immutable Snapshot move together (02 §3.9).
    """
    entries = [entry for section in (payload or {}).values() if isinstance(section, list) for entry in section]
    return reconcile_conversation(
        conn, conversation_ref, entries, active=active, now=now, complete=complete,
    )


def default_enablement(db):
    """Effective Noting gate predicate (global config AND Conversation-local state, 02 §4.2).

    Consumes the Noting runtime's own gate (``noting_trigger_gate``), which already resolves
    global config AND the Notebook sibling's conversation-local participation. While those
    modules are absent the lane stays open (rows only exist when the Schedule lane is live);
    once installed, an evaluation error fails CLOSED for scanning — the occurrence stays due
    and fires after the gate is evaluable again, so nothing is lost.
    """

    def is_enabled(conversation_ref):
        try:
            from secretary.noting_runtime import noting_trigger_gate
        except ImportError:
            return True
        try:
            enabled, _reason = noting_trigger_gate(db, conversation_ref)
            return bool(enabled)
        except Exception:
            logger.warning("Noting gate evaluation failed for %s; skipping its Schedule scan",
                           conversation_ref, exc_info=True)
            return False

    return is_enabled


def due_rows(db, *, now=None, limit=DEFAULT_DUE_BATCH, profile=None, conversation_ref=None):
    timestamp = time.time() if now is None else float(now)
    with db._read_ctx() as conn:
        return schedule_due_scan_conn(
            conn, now=timestamp, limit=limit, profile=profile, conversation_ref=conversation_ref,
        )


def claim_due(db, schedule_id, *, owner, now=None, lease_seconds=DEFAULT_CLAIM_LEASE_SECONDS):
    timestamp = time.time() if now is None else float(now)
    return db._execute_write(lambda conn: schedule_claim_conn(
        conn, schedule_id, owner=owner, now=timestamp, lease_seconds=lease_seconds,
    ))


def scan_and_claim_due(
    db, *, owner, now=None, limit=DEFAULT_DUE_BATCH, profile=None, conversation_ref=None, is_enabled=None,
):
    """Claim up to *limit* due occurrences for one profile's store; at most one winner each.

    ``is_enabled`` is the effective Noting gate: an effectively-disabled Conversation is never
    scanned, and its registry rows (with their intent) stay stored for a later re-enable.
    """
    timestamp = time.time() if now is None else float(now)
    claims = []
    for row in due_rows(db, now=timestamp, limit=limit, profile=profile, conversation_ref=conversation_ref):
        if is_enabled is not None and not is_enabled(row["conversation_ref"]):
            continue
        claim = claim_due(db, row["schedule_id"], owner=owner, now=timestamp)
        if claim is not None:
            claims.append(claim)
    return claims


def finalize_delivery(db, schedule_id, claim_token, *, now=None):
    """Account one delivered occurrence (one-shot terminal, recurring advanced, no backlog)."""
    timestamp = time.time() if now is None else float(now)
    row = db._execute_write(lambda conn: schedule_finalize_conn(conn, schedule_id, claim_token, now=timestamp))
    if row is not None and row["state"] == SCHEDULE_STATE_CANCELLED:
        logger.error(
            "Schedule %s carried an unusable canonical schedule and was quarantined "
            "(disabled; the Notebook intent is untouched)", schedule_id,
        )
    elif row is not None and row["state"] == SCHEDULE_STATE_PENDING and row["next_run_at"] is None:
        logger.warning(
            "Recurring schedule %s could not compute a next run; it stays stored but is due again "
            "only after the schedule becomes computable (e.g. croniter available)", schedule_id,
        )
    return row


def release_claim(db, schedule_id, claim_token, *, now=None):
    """Delivery failed: keep the occurrence due so a later scan retries it."""
    timestamp = time.time() if now is None else float(now)
    return db._execute_write(lambda conn: schedule_release_conn(conn, schedule_id, claim_token, now=timestamp))


def stale_disable(db, schedule_id, *, now=None):
    """Quarantine an unusable runtime row without deleting the Notebook intent."""
    timestamp = time.time() if now is None else float(now)

    def _disable(conn):
        cursor = conn.execute(
            "UPDATE secretary_schedule_registry SET enabled = 0, state = ?, claim_owner = NULL, "
            "claim_token = NULL, claim_expires_at = NULL, updated_at = ? WHERE schedule_id = ?",
            (SCHEDULE_STATE_CANCELLED, timestamp, schedule_id),
        )
        return cursor.rowcount == 1

    return db._execute_write(_disable)


__all__ = [
    "DEFAULT_CLAIM_LEASE_SECONDS",
    "DEFAULT_DUE_BATCH",
    "claim_due",
    "default_enablement",
    "due_rows",
    "entry_reminder_text",
    "finalize_delivery",
    "reconcile_conversation",
    "reconcile_entry",
    "reconcile_payload",
    "release_claim",
    "scan_and_claim_due",
    "schedule_advance_epoch",
    "schedule_initial_next_run",
    "stale_disable",
]
