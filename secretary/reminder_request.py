"""Request-only System Reminder delivery and success-tied acknowledgement (02 §3.11, §6.8).

The durable source of truth is Secretary's pending-reminder state; a pending reminder is
never written into the main Conversation transcript. Each eligible main LLM request:

```text
durable messages -> normal repair/request construction -> provider-neutral api_messages
-> select pending reminders for this Conversation -> append standalone role=user carriers
-> request accounting -> provider adapter
```

Delivery is acknowledged only after a successful provider/model response; a failed
request leaves the reminder pending, and a crash between response and ACK may redeliver
(at-least-once-safe, never lossy). Carriers reuse the durable source-event timestamp, so
retry and redelivery never mint a new time.

T4 owns the durable side and locks these method names on the owning SessionDB:
``reminder_pull_pending_conn(conn, conversation_ref)`` and
``reminder_ack_conn(conn, reminder_id)``.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple

from agent.message_metadata import build_system_reminder_wrapper

logger = logging.getLogger(__name__)

# Row fields read defensively; T4's locked methods answer rows carrying at least these.
_ID_KEYS = ("reminder_id", "id")
_CONTENT_KEYS = ("content", "message", "payload", "text")
_TIMESTAMP_KEYS = ("source_timestamp", "timestamp", "due_at", "created_at")


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


def _row_field(row: Dict[str, Any], keys: Tuple[str, ...]) -> Any:
    for key in keys:
        value = row.get(key)
        if value is not None and value != "":
            return value
    return None


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


def inject_pending_reminders(agent: Any, api_messages: list) -> Tuple[int, int]:
    """Append one standalone role=user carrier per pending reminder to *api_messages*.

    Returns ``(reminder_count, approx_tokens)``. Request-only: nothing durable changes and
    the carriers never enter the Conversation transcript. The carried ids are staged on the
    agent so the successful-response seam can acknowledge exactly them.
    """
    agent._secretary_inflight_reminders = []
    if not injection_eligible(agent):
        return 0, 0
    db, ref = _conversation_db_and_ref(agent)
    if db is None or not ref or not _effective_noting_enabled(db, ref):
        return 0, 0
    rows = pending_reminders(agent)
    if not rows:
        return 0, 0
    carriers: List[str] = []
    ids: List[Any] = []
    for row in rows:
        body = _row_field(row, _CONTENT_KEYS)
        if body is None:
            continue
        carrier = build_system_reminder_wrapper(body, timestamp=_row_field(row, _TIMESTAMP_KEYS))
        api_messages.append({"role": "user", "content": carrier})
        carriers.append(carrier)
        reminder_id = _row_field(row, _ID_KEYS)
        if reminder_id is not None:
            ids.append(reminder_id)
    agent._secretary_inflight_reminders = ids
    if not carriers:
        return 0, 0
    return len(carriers), _carrier_tokens(carriers)


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
