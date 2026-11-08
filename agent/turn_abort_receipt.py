"""Durable human-only termination receipts at the existing failed-Turn close seam."""
from __future__ import annotations

import logging

from agent.context_compressor import _DB_PERSISTED_MARKER
from agent.interrupt_control import interrupt_issuer
from agent.message_metadata import append_message
from agent.turn_failure_copy import FAILED_TURN_DISPLAY_KIND, stamp_failure, system_abort_notice

logger = logging.getLogger(__name__)


def resolve_system_abort(agent, interrupted, exit_reason):
    """Retain a committed watchdog abort when an adjacent persistence failure exits first."""
    if system_abort_notice({"interrupted": interrupted, "turn_exit_reason": exit_reason}):
        return interrupted, exit_reason
    if getattr(agent, "_interrupt_requested", False) and interrupt_issuer(agent) == "turn_liveness_watchdog":
        return True, "interrupted_by_system(turn_liveness_watchdog)"
    return interrupted, exit_reason


def terminal_failure_text(result):
    return system_abort_notice(result) or result.get("final_response") or str(result.get("turn_exit_reason"))


def persistence_failed(agent, failed, exit_reason):
    return failed and (exit_reason == "session_persistence_failed" or getattr(agent, "_incremental_persistence_failed", False))


def retain_system_abort(agent, result):
    """Early retry/backoff exits capture the accepted issuer before clear_interrupt clears it."""
    interrupted, reason = resolve_system_abort(agent, result.get("interrupted"), result.get("turn_exit_reason"))
    candidate = {**result, "interrupted": interrupted, "turn_exit_reason": reason}
    if notice := system_abort_notice(candidate):
        result.update(interrupted=True, completed=False, failed=True, turn_exit_reason=reason, error=notice)
        stamp_failure(result, "turn_liveness_timeout", True)
    return result


def _receipt_metadata(agent, result, metadata_builder):
    try:
        return {**metadata_builder(agent, result), "human_only": True}
    except Exception:
        logger.warning("System-abort receipt diagnostic metadata unavailable", exc_info=True)
        return {"human_only": True}


def close_system_aborted_turn(agent, result, metadata_builder) -> bool:
    """Close an attributed stall even after a tool/partial/hidden assistant tail.

    Uses the admitted Turn's existing transcript/flush owner, UID, redaction and lease
    validation. The receipt is display-only, never a model final or a replay of any tool.
    Returns whether this result belongs to this closer (including a failed durable write).
    """
    notice = system_abort_notice(result)
    if notice is None:
        return False
    messages = result.get("messages")
    if not isinstance(messages, list) or not messages:
        return True
    tail = messages[-1]
    if tail.get("display_kind") == FAILED_TURN_DISPLAY_KIND and tail.get("content") == notice:
        boundary = tail
    else:
        boundary = {"role": "assistant", "content": notice, "display_kind": FAILED_TURN_DISPLAY_KIND,
                    "display_metadata": _receipt_metadata(agent, result, metadata_builder)}
        append_message(messages, boundary)
    if boundary.get(_DB_PERSISTED_MARKER):
        return True
    try:
        saved = agent._flush_messages_to_session_db(messages) is not False and bool(boundary.get(_DB_PERSISTED_MARKER))
    except Exception:
        logger.warning("System-abort receipt persistence failed", exc_info=True)
        saved = False
    result["system_abort_notice_persisted"] = saved
    if not saved:
        # Native message.complete retains this error even when SQLite cannot retain the receipt.
        # Do not claim cold recovery is guaranteed after a failed durable write.
        suffix = " The termination notice could not be saved."
        result["error"] = str(result.get("error") or notice).removesuffix(suffix) + suffix
        result["failed"] = True
    return True
