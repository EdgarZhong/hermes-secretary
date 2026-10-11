"""Durable deferred batches, pre-assembly registration and actual-carriage ACK (02 §5.6)."""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Optional, Tuple

from agent.message_metadata import build_system_reminder_wrapper

logger = logging.getLogger(__name__)


def _conversation_db_and_ref(agent: Any) -> Tuple[Any, Optional[str]]:
    """The owning SessionDB and Conversation Ref; (None, None) when this agent has none."""
    db = getattr(agent, "_session_db", None)
    if db is None:
        return None, None
    ref = getattr(agent, "_secretary_conversation_ref", None)
    if not ref:
        try:
            from agent.prompt_cache_scope import initialize_conversation_identity

            ref = initialize_conversation_identity(agent)
        except Exception:
            logger.debug("reminder Conversation identity resolution failed", exc_info=True)
            ref = None
    return db, ref


def injection_eligible(agent: Any) -> bool:
    """Eligibility of this agent's requests for the main-Conversation reminder lane.

    Detached forks (persistence-isolated review/side forks), the Noting child, delegate
    children and any explicitly disabled lane never pull reminders: the lane targets the
    main Conversation's own provider-neutral request construction.
    """
    if getattr(agent, "_persist_disabled", False):
        return False
    if getattr(agent, "_secretary_noting_profile", None) or getattr(agent, "_secretary_noting_child", False):
        return False
    if getattr(agent, "side_agent", False):
        return False
    if getattr(agent, "_secretary_reminder_injection_disabled", False) is True:
        return False
    return True


def _effective_noting_enabled(db: Any, conversation_ref: str) -> bool:
    """Noting/Schedule gate for delivery: global Noting AND Conversation-local participation.

    Unavailable policy/local state fails closed; durable pending state remains for retry.
    """
    try:
        from secretary.noting_runtime import noting_trigger_gate
        enabled, _reason = noting_trigger_gate(db, conversation_ref)
        return enabled
    except Exception:
        logger.debug("Noting policy gate unavailable; reminder lane disabled", exc_info=True)
        return False


def _locked_db_hook(db: Any, name: str) -> Any:
    """T4's locked reminder method: the SessionDB sibling, else the module-level function.

    The Schedule mixin may not be part of ``SessionDB``'s MRO yet (central wiring is the
    main session's step); both shapes take the caller's connection and behave identically.
    """
    fn = getattr(db, name, None)
    if callable(fn):
        return fn
    try:
        from hermes_state_secretary_schedule import (
            reminder_ack_conn, reminder_pull_pending_conn,
        )

        return {"reminder_pull_pending_conn": reminder_pull_pending_conn,
                "reminder_ack_conn": reminder_ack_conn}.get(name)
    except Exception:
        logger.debug("Schedule reminder module unavailable", exc_info=True)
        return None


def pending_reminders(agent: Any) -> List[Dict[str, Any]]:
    """The Conversation's durable pending reminders via T4's locked pull method (best-effort)."""
    db, ref = _conversation_db_and_ref(agent)
    if db is None or not ref:
        return []
    pull = _locked_db_hook(db, "reminder_pull_pending_conn")
    if not callable(pull):
        return []
    try:
        rows = db._execute_write(lambda conn: pull(conn, ref))
    except Exception:
        if not getattr(agent, "_secretary_reminder_pull_warned", False):
            agent._secretary_reminder_pull_warned = True
            logger.warning("Pending System Reminder pull failed; requests continue without it", exc_info=True)
        else:
            logger.debug("Pending System Reminder pull failed again", exc_info=True)
        return []
    return [dict(row) for row in rows or () if isinstance(row, dict) or hasattr(row, "keys")]


def prepare_pending_reminders(agent: Any, messages: list) -> int:
    """Pull bookkeeping only; preview batch pressure before native compaction admission."""
    agent._secretary_inflight_reminders = []
    agent._secretary_inflight_carriers = []
    agent._secretary_inflight_batches = []
    agent._secretary_pending_batch = []
    if not injection_eligible(agent):
        return 0
    db, ref = _conversation_db_and_ref(agent)
    if db is None or not ref or not _effective_noting_enabled(db, ref):
        return 0
    rows = pending_reminders(agent)
    agent._secretary_pending_batch = rows
    covered = {rid for row in messages for rid in (row.get("display_metadata") or {}).get("reminder_ids", [])}
    text = _messages_text(messages)
    covered.update(row["reminder_id"] for row in rows if row.get("carrier_content") and row["carrier_content"] in text)
    fresh = [row for row in rows if row["reminder_id"] not in covered]
    return _carrier_tokens([_batch_carrier(fresh)]) if fresh else 0


def _batch_carrier(rows: list) -> str:
    from hermes_state_secretary_schedule import render_source_timestamp
    entries = []
    for row in rows:
        # Occurrence captures the complete entry while its claim is settled. A
        # manually queued legacy/internal notice has no Notebook entry provenance.
        entry = dict(row.get("entry_payload") or {"content": row["content"]})
        entry.pop("schedule", None)
        entry["due_at"] = render_source_timestamp(row["source_timestamp"])
        entries.append(entry)
    return build_system_reminder_wrapper("以下提醒已到期。\n" + json.dumps(entries, ensure_ascii=False))


def materialize_pending_reminders(agent: Any, messages: list) -> int:
    """One durable batch enters the live sequence, before build_api_messages copies it."""
    rows = getattr(agent, "_secretary_pending_batch", [])
    if not rows:
        return 0
    if getattr(agent, "_active_compression_commit_fence", None) is not None:
        return 0
    wanted = {row["reminder_id"] for row in rows}
    covered = set()
    carriers = []
    batches = []
    for row in messages:
        ids = wanted.intersection((row.get("display_metadata") or {}).get("reminder_ids", []))
        if ids:
            covered.update(ids)
            carriers.append(str(row["content"]))
            batches.append((str(row["content"]), list(ids)))
    text = _messages_text(messages)
    for pending in rows:
        carrier = pending.get("carrier_content")
        if carrier and carrier in text and pending["reminder_id"] not in covered:
            covered.add(pending["reminder_id"])
            if carrier not in carriers:
                carriers.append(carrier)
            batches.append((carrier, [pending["reminder_id"]]))
    fresh = [row for row in rows if row["reminder_id"] not in covered]
    if fresh:
        from secretary.framework_messages import append_runtime_row
        carrier = _batch_carrier(fresh)
        ids = [row["reminder_id"] for row in fresh]
        row = {"role": "user", "content": carrier, "display_kind": "process_complete",
               "display_metadata": {"reminder_ids": ids, "display_text": "以下提醒已到期。"}}
        try:
            append_runtime_row(agent, messages, row)
        except Exception:
            logger.warning("Deferred Reminder batch persistence failed; remains pending", exc_info=True)
            return 0
        covered.update(ids)
        carriers.append(str(carrier))
        batches.append((str(carrier), ids))
    # Phase one: register before the builder or context selection can drop a row.
    agent._secretary_inflight_reminders = [row["reminder_id"] for row in rows if row["reminder_id"] in covered]
    agent._secretary_inflight_carriers = carriers
    agent._secretary_inflight_batches = batches
    return len(covered)


def _messages_text(messages):
    from agent.message_content import flatten_message_text
    return "\n".join(flatten_message_text(row.get("content")) for row in messages or [])


def verify_carried_reminders(agent: Any, api_messages: list) -> bool:
    """Phase two: ACK can only follow a response to a request carrying the full wrapper."""
    text = _messages_text(api_messages)
    batches = getattr(agent, "_secretary_inflight_batches", [])
    ids = [rid for carrier, row_ids in batches if carrier in text for rid in row_ids]
    agent._secretary_inflight_reminders = list(dict.fromkeys(ids))
    return bool(ids)


def inject_pending_reminders(agent: Any, messages: list) -> Tuple[int, int]:
    """Compatibility helper: materialize into LIVE messages, never a built API copy."""
    tokens = prepare_pending_reminders(agent, messages)
    return materialize_pending_reminders(agent, messages), tokens


def _carrier_tokens(carriers: List[str]) -> int:
    """Rough price of the injected carriers, for the usage-anchored pressure figure."""
    try:
        from agent.model_metadata import estimate_messages_tokens_rough

        return int(estimate_messages_tokens_rough(
            [{"role": "user", "content": carrier} for carrier in carriers]
        ))
    except Exception:
        logger.debug("carrier token estimate fell back to a char heuristic", exc_info=True)
        return sum(len(carrier) for carrier in carriers) // 4


def acknowledge_carried_reminders(agent: Any) -> int:
    """ACK the reminders carried by the request that just got a provider response.

    Called from the successful-response seam only. The staged ids are cleared first so a
    crash mid-ACK redelivers instead of losing the reminder (at-least-once).
    """
    ids = getattr(agent, "_secretary_inflight_reminders", None)
    if not ids:
        return 0
    agent._secretary_inflight_reminders = []
    db, _ref = _conversation_db_and_ref(agent)
    ack = _locked_db_hook(db, "reminder_ack_conn") if db is not None else None
    if not callable(ack):
        return 0
    acknowledged = 0
    for reminder_id in ids:
        try:
            db._execute_write(lambda conn, rid=reminder_id: ack(conn, rid))
            acknowledged += 1
        except Exception:
            logger.warning("System Reminder ACK failed for %s; delivery stays at-least-once", reminder_id,
                           exc_info=True)
    return acknowledged
