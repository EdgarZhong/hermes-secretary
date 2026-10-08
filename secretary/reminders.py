"""Reminder service: durable pending System Reminders and route-proven active delivery.

Passive delivery (due commitment/task/watchpoint, Force notice, busy User Reminder fallback)
creates a durable pending System Reminder and never starts a Turn. Active delivery (due
``user_reminder``) proves Conversation ownership through the identity registry, builds the
§5.6 carrier and hands it to the host's existing ingress — whose own admission decides
idle (new Turn) versus busy (convert to pending, no queued second Turn).
"""

import time
from pathlib import Path

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


class ActiveReminderPersistenceError(RuntimeError):
    """An admitted active carrier could not join its native durable transcript transaction."""


class ActiveReminderAdmission:
    """Process-only witness from native admission, never reconstructed from JSON or text."""

    def __init__(self, db_path, receipt):
        self.db_path, self.receipt = db_path, receipt
        self.row_proof = None
        self.aborted = False
        self.committed = False

    def durable(self, db):
        if self.committed:
            return True
        if self.row_proof is None or str(Path(db.db_path).resolve()) != self.db_path:
            return False
        session_id, uid, content, stamp = self.row_proof
        with db._read_ctx() as conn:
            row = conn.execute("SELECT content, timestamp FROM messages WHERE session_id=? AND message_uid=?",
                               (session_id, uid)).fetchone()
            state = conn.execute("SELECT * FROM secretary_schedule_registry WHERE schedule_id=?",
                                 (self.receipt["before"]["schedule_id"],)).fetchone()
        after = self.receipt["after"]
        keys = ("conversation_ref", "canonical_schedule", "delivery_semantics", "state", "next_run_at",
                "last_fired_at", "claim_token", "updated_at")
        return (row is not None and row["content"] == content and row["timestamp"] == stamp
                and after is not None and state is not None and all(state[key] == after[key] for key in keys))

    def commit(self, db, conn, session_id, row):
        if self.aborted or str(Path(db.db_path).resolve()) != self.db_path:
            raise ActiveReminderPersistenceError("Active Reminder admission is no longer owned")
        resolved = _resolve_active_conn(db, conn, self.receipt["before"], time.time(), session_id=session_id)
        from agent.message_sanitization import _sanitize_surrogates
        expected = _sanitize_surrogates(self.receipt["resolved"]["text"])
        if (not resolved["route"] or _sanitize_surrogates(resolved.get("text", "")) != expected
                or row.get("role") != "user" or row.get("content") != expected
                or row.get("timestamp") != self.receipt["resolved"]["source_timestamp"]):
            raise ActiveReminderPersistenceError("Active Reminder claim or native carrier changed before persistence")
        stored = conn.execute("SELECT content, timestamp, message_uid FROM messages WHERE id=? AND session_id=?",
                              (row.get("_row_id"), session_id)).fetchone()
        if stored is None or stored["content"] != expected or stored["timestamp"] != row["timestamp"]:
            raise ActiveReminderPersistenceError("Active Reminder native user row is not canonical")
        after = schedule_finalize_conn(conn, resolved["claim"]["schedule_id"],
                                       resolved["claim"]["claim_token"], now=time.time())
        if after is None:
            raise ActiveReminderPersistenceError("Active Reminder settlement lost its claim")
        self.receipt["after"] = after
        self.row_proof = (session_id, stored["message_uid"], expected, stored["timestamp"])


def active_admission_witness(value):
    from agent.message_metadata import TrustedUserInput
    witness = getattr(value, "_secretary_active_admission", None) if isinstance(value, TrustedUserInput) else None
    return witness if isinstance(witness, ActiveReminderAdmission) else None


def active_delivery_batch_callback(db, batch_msgs, batch_rows):
    pairs = [(active_admission_witness(msg.get("content")), row) for msg, row in zip(batch_msgs, batch_rows)]
    pairs = [(witness, row) for witness, row in pairs if witness is not None and not witness.durable(db)]
    if not pairs:
        return None

    def before_commit(conn, session_id, _inserted_rows):
        for witness, row in pairs:
            witness.commit(db, conn, session_id, row)

    return before_commit


def require_active_delivery_persisted(agent, messages):
    """Plain turns retain native best-effort persistence; admitted active turns must be durable."""
    witness = active_turn_witness(agent, messages)
    if witness is None:
        return
    if not witness.durable(agent._session_db):
        witness.aborted = True
        release_claim(agent._session_db, witness.receipt["before"])
        raise ActiveReminderPersistenceError("Active Reminder was not persisted; its occurrence remains retryable")
    # A COMMIT may succeed even when the caller loses its return. Re-adopt only the
    # exact row proved by that transaction, so native later flushes cannot duplicate it.
    from agent.message_metadata import DB_ROW_SNAPSHOT
    from agent.transcript_repair import sync_flushed_message_markers, transcript_row_snapshot
    sid, uid, _content, _stamp = witness.row_proof
    stored = agent._session_db._read_one("SELECT * FROM messages WHERE session_id=? AND message_uid=?",
                                        (sid, uid))
    if stored is not None:
        row = {"_row_id": stored["id"], "message_uid": uid, "timestamp": stored["timestamp"],
               DB_ROW_SNAPSHOT: transcript_row_snapshot(stored)}
        sync_flushed_message_markers([messages[agent._persist_user_message_idx]], [row])


def active_turn_witness(agent, messages):
    index = getattr(agent, "_persist_user_message_idx", None)
    if isinstance(index, int) and 0 <= index < len(messages):
        return active_admission_witness(messages[index].get("content"))
    return None


def confirm_active_delivery_batch(batch_msgs):
    """Called only after native append_messages_batch has returned from COMMIT successfully."""
    for msg in batch_msgs:
        witness = active_admission_witness(msg.get("content"))
        if witness is not None and witness.row_proof is not None:
            witness.committed = True


def active_delivery_auto_continue(text, default):
    return default and active_admission_witness(text) is None


def persist_active_before_compaction(agent, user_message, messages, history, pending_cli_message):
    if active_turn_witness(agent, messages) is not None:
        from agent.turn_context import _persist_turn_start
        _persist_turn_start(agent, messages, history, pending_cli_message)


def active_delivery_failure_result(agent, exc, history):
    """Use the native partial-result contract without compression reset or a ghost user input."""
    from agent.agent_runtime_helpers import note_turn_persisted
    from agent.conversation_loop import _partial_turn_result
    retained = list(history or [])
    agent._session_messages = retained
    agent._pending_cli_user_message = None
    agent._persist_user_message_idx = None
    note_turn_persisted(agent)
    return _partial_turn_result(str(exc), retained, 0, failed=True, turn_exit_reason="secretary_delivery_uncommitted",
                                failure_reason="state_persistence", failure_retryable=True)


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


def _current_claim_conn(db, conn, claim, timestamp):
    """Recheck the exact occurrence and effective gate under the registry write lock."""
    row = conn.execute(
        "SELECT * FROM secretary_schedule_registry WHERE schedule_id = ? AND conversation_ref = ? "
        "AND claim_token = ? AND next_run_at = ? AND next_run_at <= ? "
        "AND state = 'pending' AND enabled = 1 AND claim_expires_at > ?",
        (claim.get("schedule_id"), claim.get("conversation_ref"), claim.get("claim_token"),
         claim.get("next_run_at"), timestamp, timestamp),
    ).fetchone()
    if row is None:
        return None
    current = dict(row)
    from secretary.schedules import default_enablement
    if (not default_enablement(db)(current["conversation_ref"])
            or not db.notebook_local_enabled_conn(conn, current["conversation_ref"])):
        schedule_release_conn(conn, current["schedule_id"], current["claim_token"], now=timestamp)
        return None
    return current


def _resolve_active_conn(db, conn, claim, timestamp, *, session_id=None, route_validator=None, content=None):
    current = _current_claim_conn(db, conn, claim, timestamp)
    if current is None or current["delivery_semantics"] != ACTIVE_DELIVERY:
        return {"route": None, "reason": "claim_ineligible"}
    route = db.resolve_conversation_route_conn(conn, current["conversation_ref"])
    if (not route or (session_id is not None and route["id"] != session_id)
            or (route_validator is not None and not route_validator(route))):
        return {"route": None, "reason": "route_unproven"}
    content = content or occurrence_content(current)
    source_timestamp = occurrence_timestamp(current)
    return {"route": route, "text": build_user_reminder_text(content, source_timestamp),
            "content": content, "source_timestamp": source_timestamp, "reason": "ok", "claim": current}


def admit_active_reminder(db, claim, *, session_id=None, route_validator=None, now=None):
    """Validate at native idle admission; settle only with the native durable user row.

    The caller already owns its native session slot. This transaction orders local-off,
    Snapshot reconciliation and lease reclaim against admission; no Turn runs in it.
    """
    def admit(conn):
        timestamp = time.time() if now is None else float(now)
        resolved = _resolve_active_conn(db, conn, claim, timestamp, session_id=session_id,
                                        route_validator=route_validator)
        if not resolved["route"]:
            return None
        receipt = {"resolved": resolved, "before": resolved["claim"], "after": None}
        witness = ActiveReminderAdmission(str(Path(db.db_path).resolve()), receipt)
        resolved["text"]._secretary_active_admission = witness
        return receipt

    return db._execute_write(admit)


def recover_active_reminder(db, receipt, *, passive=False, now=None):
    """Refused handoff releases only its token; durable user rows are never rolled back."""
    witness = active_admission_witness(receipt["resolved"]["text"])
    if witness is not None and witness.durable(db):
        return False
    return release_claim(db, receipt["before"], now=now)


def queue_pending_for_claim(db, claim, *, now=None, content=None):
    """Passive delivery: durable pending System Reminder plus accounting, in one transaction."""
    def _queue(conn):
        timestamp = time.time() if now is None else float(now)
        current = _current_claim_conn(db, conn, claim, timestamp)
        if current is None:
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


def resolve_active_reminder(db, claim, *, content=None, now=None):
    """Prepare a currently eligible active carrier; native admission must recheck it again."""
    return db._execute_write(lambda conn: _resolve_active_conn(
        db, conn, claim, time.time() if now is None else float(now), content=content))


def finalize_claim(db, claim, *, now=None):
    """Account a delivered occurrence; a claim already finalized (busy conversion) is a no-op."""
    def finalize(conn):
        timestamp = time.time() if now is None else float(now)
        current = _current_claim_conn(db, conn, claim, timestamp)
        return current is not None and schedule_finalize_conn(
            conn, current["schedule_id"], current["claim_token"], now=timestamp) is not None

    return db._execute_write(finalize)


def release_claim(db, claim, *, now=None):
    """Delivery failed (route unproven / ingress refused): keep the occurrence for a retry."""
    timestamp = time.time() if now is None else float(now)
    return db._execute_write(
        lambda conn: schedule_release_conn(conn, claim["schedule_id"], claim["claim_token"], now=timestamp)
    )
