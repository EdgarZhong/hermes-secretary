"""Reminder service: durable pending System Reminders and route-proven active delivery.

Passive delivery (due commitment/task/watchpoint, Force notice, busy User Reminder fallback)
creates a durable pending System Reminder and never starts a Turn. Active delivery (due
``user_reminder``) proves Conversation ownership through the identity registry, builds the
§5.6 carrier and hands it to the host's existing ingress — whose own admission decides
idle (new Turn) versus busy (convert to pending, no queued second Turn).
"""

import time

from hermes_state_secretary_schedule import (
    build_system_reminder_text,
    build_user_reminder_text,
    reminder_ack_conn,
    reminder_append_pending_conn,
    reminder_pending_count_conn,
    reminder_pull_pending_conn,
    schedule_finalize_conn,
    schedule_release_conn,
)

ACTIVE_DELIVERY = "user_reminder"
PASSIVE_DELIVERY = "system_reminder"


def system_reminder_text(content, source_timestamp):
    return build_system_reminder_text(content, source_timestamp)


def user_reminder_text(content, source_timestamp):
    return build_user_reminder_text(content, source_timestamp)


def occurrence_timestamp(claim, *, now=None):
    """The source occurrence instant of one claimed row: the scheduled (due) fire time."""
    value = claim.get("next_run_at")
    return float(value) if value is not None else (time.time() if now is None else float(now))


def occurrence_content(claim):
    text = str(claim.get("reminder_text") or "").strip()
    if text:
        return text
    return f"Notebook {claim.get('notebook_entry_id', 'entry')} is due"


def queue_pending_for_claim(db, claim, *, now=None, content=None):
    """Passive delivery: durable pending System Reminder plus accounting, in one transaction."""
    timestamp = time.time() if now is None else float(now)

    def _queue(conn):
        # Reclaim, intent changes and pointer reconciliation may have invalidated the
        # caller's claim. Validate both its token and exact occurrence under the write lock.
        row = conn.execute(
            "SELECT * FROM secretary_schedule_registry WHERE schedule_id = ? AND conversation_ref = ? "
            "AND claim_token = ? AND next_run_at = ? "
            "AND state = 'pending' AND enabled = 1 AND claim_expires_at > ?",
            (claim["schedule_id"], claim["conversation_ref"], claim["claim_token"],
             claim["next_run_at"], timestamp),
        ).fetchone()
        if row is None:
            return None
        current = dict(row)
        if not db.notebook_local_enabled_conn(conn, current["conversation_ref"]):
            # The switch can change after scanning. Release only our proven token so the
            # same occurrence remains due when eligibility returns; never finalize it.
            schedule_release_conn(conn, current["schedule_id"], current["claim_token"], now=timestamp)
            return None
        reminder_id = reminder_append_pending_conn(
            conn, current["conversation_ref"], content or occurrence_content(current),
            source_timestamp=occurrence_timestamp(current), schedule_id=current["schedule_id"],
            dedup_key=f"{current['schedule_id']}:{current['next_run_at']}",
            now=timestamp,
        )
        if schedule_finalize_conn(conn, current["schedule_id"], current["claim_token"], now=timestamp) is None:
            raise RuntimeError("Schedule claim changed inside its pending transaction")
        return reminder_id

    return db._execute_write(_queue)


def convert_claim_to_pending(db, claim, *, now=None, content=None):
    """Busy User Reminder policy (§3.12): convert the occurrence to a pending System Reminder.

    The conversion is atomic with the schedule accounting, so a busy Conversation never grows
    a queued future Reminder Turn and the occurrence is not lost.
    """
    return queue_pending_for_claim(db, claim, now=now, content=content)


def pull_pending(db, conversation_ref):
    """Pending carriers for request-time injection (T3C); ACK only after a successful response."""
    with db._read_ctx() as conn:
        return reminder_pull_pending_conn(conn, conversation_ref)


def ack(db, reminder_id, *, now=None):
    """Acknowledge delivery of one pending System Reminder after a successful model response."""
    timestamp = time.time() if now is None else float(now)
    return db._execute_write(lambda conn: reminder_ack_conn(conn, reminder_id, now=timestamp))


def pending_count(db, conversation_ref):
    with db._read_ctx() as conn:
        return reminder_pending_count_conn(conn, conversation_ref)


def active_route(db, conversation_ref):
    """Proven current physical Session for active delivery, or None (fail closed)."""
    import sqlite3

    from hermes_state_secretary_identity import ConversationIdentityError

    try:
        return db.resolve_conversation_route(conversation_ref)
    except (ConversationIdentityError, sqlite3.Error):
        return None


def resolve_active_reminder(db, claim, *, content=None):
    """Ownership-proof + carrier for one due ``user_reminder`` occurrence.

    Returns ``{"route": ..., "text": ..., "source_timestamp": ...}`` only when the Conversation
    route is proven (current tip / generation / profile); otherwise ``{"route": None, "reason": ...}``
    so the caller can release the claim and retry later — never deliver into a successor Conversation.
    """
    route = active_route(db, claim["conversation_ref"])
    if not route:
        return {"route": None, "reason": "route_unproven"}
    source_timestamp = occurrence_timestamp(claim)
    return {
        "route": route,
        "text": build_user_reminder_text(content or occurrence_content(claim), source_timestamp),
        "content": content or occurrence_content(claim),
        "source_timestamp": source_timestamp,
        "reason": "ok",
    }


def finalize_claim(db, claim, *, now=None):
    """Account a delivered occurrence; a claim already finalized (busy conversion) is a no-op."""
    timestamp = time.time() if now is None else float(now)
    return db._execute_write(
        lambda conn: schedule_finalize_conn(conn, claim["schedule_id"], claim["claim_token"], now=timestamp)
        is not None
    )


def release_claim(db, claim, *, now=None):
    """Delivery failed (route unproven / ingress refused): keep the occurrence for a retry."""
    timestamp = time.time() if now is None else float(now)
    return db._execute_write(
        lambda conn: schedule_release_conn(conn, claim["schedule_id"], claim["claim_token"], now=timestamp)
    )
