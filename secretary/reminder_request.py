"""Durable deferred batches prepared inside native append, verified request-carriage ACK."""
from __future__ import annotations

from contextlib import nullcontext
import logging
import time
from typing import Any, Dict, List, Optional, Tuple

from agent.message_metadata import build_system_reminder_wrapper

logger = logging.getLogger(__name__)


class _NoPendingReminders(RuntimeError):
    """The prepared batch was withdrawn; roll back without publishing a live row."""


def _conversation_db_and_ref(agent: Any) -> Tuple[Any, Optional[str]]:
    db = getattr(agent, "_session_db", None)
    if db is None:
        return None, None
    ref = getattr(agent, "_secretary_conversation_ref", None)
    if not ref:
        try:
            with db._read_ctx() as conn:
                ref = db.resolve_conversation_ref_conn(conn, agent.session_id, read_only=True)
        except Exception:
            logger.debug("Reminder owner unavailable", exc_info=True)
    return db, ref


def injection_eligible(agent: Any) -> bool:
    if (getattr(agent, "_secretary_noting_profile", None)
            or getattr(agent, "_secretary_noting_child", False)
            or getattr(agent, "_secretary_reminder_injection_disabled", False)):
        return False
    from secretary.noting_runtime import is_main_conversation_agent
    return is_main_conversation_agent(agent)


def _scheduler_enabled(db):
    from secretary.noting_scope import scheduler_settings_for_db
    return scheduler_settings_for_db(db).enabled


def _owner_current_conn(agent, db, conn, ref, session_id):
    binding = db.resolve_conversation_ref_conn(conn, session_id, read_only=True)
    route = db.resolve_conversation_route_conn(conn, ref)
    return (binding == ref and route is not None and route["id"] == session_id
            and agent.session_id == session_id)


def pending_reminders(agent: Any) -> List[Dict[str, Any]]:
    from hermes_state_secretary_schedule import reminder_pull_pending_conn, reminder_settle_retired_conn
    db, ref = _conversation_db_and_ref(agent)
    if db is None or not ref:
        return []

    def pull(conn):
        if not _owner_current_conn(agent, db, conn, ref, agent.session_id):
            return []
        reminder_settle_retired_conn(conn, ref)
        return reminder_pull_pending_conn(conn, ref)

    try:
        return db._execute_write(pull)
    except Exception:
        logger.warning("Pending Reminder pull failed; receipts remain pending", exc_info=True)
        return []


def prepare_pending_reminders(agent: Any, messages: list) -> int:
    """Preview pressure only. Actual occurrence data is reread in native prepare_rows."""
    agent._secretary_inflight_reminders = []
    agent._secretary_inflight_carriers = []
    agent._secretary_inflight_batches = []
    agent._secretary_reminder_carriage_verified = False
    agent._secretary_reminder_provider_responded = False
    agent._secretary_pending_batch = []
    if not injection_eligible(agent):
        return 0
    db, ref = _conversation_db_and_ref(agent)
    if db is None or not ref:
        return 0
    rows = pending_reminders(agent)
    if not _scheduler_enabled(db):
        rows = [row for row in rows if row.get("carrier_message_uid")]
    agent._secretary_pending_batch = rows
    fresh = [row for row in rows if not row.get("carrier_message_uid")]
    return _carrier_tokens([_batch_carrier(fresh, db=db)]) if fresh else 0


def _batch_carrier(rows: list, *, db, conn=None, conversation_ref=None, now=None) -> str:
    from pathlib import Path
    from hermes_state_secretary_schedule import render_source_timestamp
    from secretary.reminders import instant_notice_conn, scheduled_attention_text

    blocks = []
    for row in rows:
        payload = row.get("entry_payload") or {}
        due = render_source_timestamp(row["source_timestamp"], profile_home=Path(db.db_path).parent)
        blocks.append(scheduled_attention_text(row.get("schedule_id") or "internal", due,
                      payload.get("delivery_mode", "deferred"), row["content"]))
    if conn is not None:
        notice = instant_notice_conn(conn, conversation_ref, rows, now=now)
        if notice:
            blocks.append(notice)
    return build_system_reminder_wrapper("\n\n".join(blocks))


def _existing_carriers_conn(db, conn, ref, rows, messages):
    """Reuse the exact durable carrier; a request failure never creates another row."""
    from agent.context_compressor import _DB_PERSISTED_MARKER
    from agent.message_metadata import DB_ROW_SNAPSHOT
    from agent.transcript_repair import transcript_row_snapshot

    needed = {row["carrier_message_uid"]: row["carrier_content"] for row in rows if row.get("carrier_message_uid")}
    text = _messages_text(messages)
    restore = []
    if not needed:
        return restore
    for source in db.get_history_foreground_conn(conn, ref):
        uid = source["message_uid"]
        if uid not in needed or needed[uid] in text:
            continue
        stored = conn.execute("SELECT * FROM messages WHERE id=? AND active=1", (source["id"],)).fetchone()
        if stored is None or stored["content"] != needed[uid]:
            continue
        row = db._decoded_repair_row(stored)
        row.update(_row_id=stored["id"], timestamp=stored["timestamp"])
        row[DB_ROW_SNAPSHOT] = transcript_row_snapshot(stored)
        row[_DB_PERSISTED_MARKER] = True
        restore.append(row)
        text += "\n" + needed[uid]
    return restore


def _materialize_batch(agent, db, ref, messages, wanted):
    from agent.context_compressor import _DB_PERSISTED_MARKER
    from hermes_state_secretary_schedule import (
        reminder_bind_carrier_conn, reminder_revalidate_pending_conn, reminder_settle_retired_conn,
    )
    # A private nonempty placeholder enters the existing native transaction. It is
    # replaced in-place by prepare_rows before native serialization/insertion.
    batch = [{}]
    admitted = {}
    session_id = agent.session_id

    def prepare(conn, sid, private_rows):
        if (getattr(agent, "_active_compression_commit_fence", None) is not None
                or not _owner_current_conn(agent, db, conn, ref, sid)):
            raise _NoPendingReminders()
        reminder_settle_retired_conn(conn, ref)
        current = [reminder_revalidate_pending_conn(conn, ref, rid) for rid in wanted]
        current = [row for row in current if row is not None]
        if not _scheduler_enabled(db):
            current = [row for row in current if row["carrier_message_uid"]]
        if not current:
            raise _NoPendingReminders()
        fresh = [row for row in current if not row["carrier_message_uid"]]
        admitted.update(current=current, fresh=fresh,
                        restore=_existing_carriers_conn(db, conn, ref, current, messages))
        if not fresh:
            private_rows[:] = []
            return
        carrier = _batch_carrier(fresh, db=db, conn=conn, conversation_ref=ref, now=time.time())
        private_rows[:] = [{"role": "user", "content": carrier, "display_kind": "process_complete",
                           "display_metadata": {"reminder_ids": [row["reminder_id"] for row in fresh],
                                                "display_text": "以下提醒已到期。",
                                                "origin": "reminder", "producer": "reminder"}}]

    def bind(conn, sid, _rows):
        if admitted["fresh"]:
            row = batch[0]
            reminder_bind_carrier_conn(conn, ref, admitted["fresh"], carrier_message_uid=row["message_uid"],
                                       carrier_content=str(row["content"]), now=time.time())
            for pending in admitted["fresh"]:
                pending["carrier_content"] = str(row["content"])
                pending["carrier_message_uid"] = row["message_uid"]

    db.append_messages_batch(session_id, batch,
        compression_lock_holder=getattr(agent, "_active_compression_lock_holder", None),
        turn_lease_holder=getattr(agent, "_active_session_turn_lease_holder", None),
        turn_lease_ttl_seconds=getattr(agent, "_active_session_turn_lease_ttl_seconds", 300.0),
        prepare_rows=prepare, before_commit=bind)
    # The caller still owns the native persist lock. No live mutations happened in
    # either callback, so failure/rollback cannot leak a carrier into the request.
    for row in [*admitted["restore"], *batch]:
        row[_DB_PERSISTED_MARKER] = True
        messages.append(row)
    return admitted["current"]


def materialize_pending_reminders(agent: Any, messages: list) -> int:
    """Commit one batch, then publish live, before build_api_messages copies it."""
    rows = getattr(agent, "_secretary_pending_batch", [])
    if not rows or not injection_eligible(agent):
        return 0
    db, ref = _conversation_db_and_ref(agent)
    if db is None or not ref or getattr(agent, "_active_compression_commit_fence", None) is not None:
        return 0
    from secretary.noting_scope import owning_db_scope
    lock = getattr(agent, "_session_persist_lock", None)
    try:
        with owning_db_scope(db), nullcontext() if lock is None else lock:
            flush = getattr(agent, "_flush_messages_to_session_db", None)
            if callable(flush) and flush(messages) is False:
                raise RuntimeError("Native transcript tail flush failed")
            current = _materialize_batch(agent, db, ref, messages, [row["reminder_id"] for row in rows])
    except _NoPendingReminders:
        return 0
    except Exception:
        logger.warning("Deferred Reminder persistence failed; receipts remain pending", exc_info=True)
        return 0
    text = _messages_text(messages)
    batches = {}
    for row in current:
        carrier = row.get("carrier_content")
        if carrier and carrier in text:
            batches.setdefault(carrier, []).append(row["reminder_id"])
    agent._secretary_inflight_batches = list(batches.items())
    agent._secretary_inflight_carriers = list(batches)
    # No ACK authority until verify_carried_reminders observes the actual request.
    agent._secretary_inflight_reminders = []
    agent._secretary_reminder_carriage_verified = False
    return sum(len(ids) for ids in batches.values())


def _messages_text(messages):
    from agent.message_content import flatten_message_text
    return "\n".join(flatten_message_text(row.get("content")) for row in messages or [] if isinstance(row, dict))


def verify_carried_reminders(agent: Any, api_messages: list) -> bool:
    text = _messages_text(api_messages)
    batches = getattr(agent, "_secretary_inflight_batches", [])
    ids = [rid for carrier, row_ids in batches if carrier in text for rid in row_ids]
    agent._secretary_inflight_reminders = list(dict.fromkeys(ids))
    agent._secretary_reminder_carriage_verified = bool(ids)
    return bool(ids)


def inject_pending_reminders(agent: Any, messages: list) -> Tuple[int, int]:
    tokens = prepare_pending_reminders(agent, messages)
    return materialize_pending_reminders(agent, messages), tokens


def _carrier_tokens(carriers: List[str]) -> int:
    try:
        from agent.model_metadata import estimate_messages_tokens_rough
        return int(estimate_messages_tokens_rough([{"role": "user", "content": carrier} for carrier in carriers]))
    except Exception:
        logger.debug("carrier token estimate uses char heuristic", exc_info=True)
        return sum(len(carrier) for carrier in carriers) // 4


def acknowledge_carried_reminders(agent: Any) -> int:
    """Only the verified request's nonempty successful response can consume receipts."""
    if (not getattr(agent, "_secretary_reminder_carriage_verified", False)
            or not getattr(agent, "_secretary_reminder_provider_responded", False)):
        return 0
    ids = getattr(agent, "_secretary_inflight_reminders", [])
    agent._secretary_inflight_reminders = []
    agent._secretary_reminder_carriage_verified = False
    db, ref = _conversation_db_and_ref(agent)
    if db is None or not ref:
        return 0
    from hermes_state_secretary_schedule import reminder_ack_conn
    acknowledged = 0
    for rid in ids:
        def ack(conn):
            owner = conn.execute("SELECT conversation_ref FROM secretary_pending_reminders WHERE reminder_id=?", (rid,)).fetchone()
            return bool(owner and owner[0] == ref and reminder_ack_conn(conn, rid))
        try:
            acknowledged += int(db._execute_write(ack))
        except Exception:
            logger.warning("Reminder ACK failed; receipt remains retryable", exc_info=True)
    return acknowledged
