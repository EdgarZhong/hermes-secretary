"""Trusted Finish hand-off from a durable tool round to native Turn finalization."""

import json

from agent.context_compressor import _DB_PERSISTED_MARKER
from agent.message_sanitization import coalesce_tool_call_id

NOTING_FINISHED = "noting_finished"


def finish_requested(agent):
    """Only the bound owner and the first successful handler receipt grant completion."""
    if getattr(agent, "_secretary_noting_child", False) is not True:
        return False
    from secretary.noting_tools import _bound_store
    from secretary.notebook_contract import NotebookValidationError
    try:
        store = _bound_store(agent)
    except NotebookValidationError:
        return False
    with store.lock:
        termination = getattr(agent, "_secretary_noting_termination", None)
        return (getattr(agent, "_secretary_noting_terminal_action_done", False) is True
                and getattr(agent, "_secretary_noting_finish_result", None)
                == {"success": True, "status": "end_requested"}
                and isinstance(termination, dict) and termination.get("type") == "finish_noting")


def _successful_receipt(row, call_id):
    if (row.get("role") != "tool" or row.get("tool_call_id") != call_id
            or row.get(_DB_PERSISTED_MARKER) is not True):
        return False
    try:
        # Native budget notices may follow the exact JSON tool result.
        result, _end = json.JSONDecoder().raw_decode(row.get("content", "").lstrip())
    except (ValueError, TypeError, AttributeError):
        return False
    return result == {"success": True, "status": "end_requested"}


def accepted_finish_round(agent, assistant_message, messages):
    """Only this durable standalone call/result pair can complete the native Turn."""
    calls = assistant_message.tool_calls
    if len(calls) != 1 or calls[0].function.name != "finish_noting" or not finish_requested(agent):
        return False
    call_id = coalesce_tool_call_id(calls[0])
    if not call_id:
        return False
    for index in range(len(messages) - 1, -1, -1):
        row = messages[index]
        if row.get("role") == "assistant" and row.get("tool_calls"):
            staged = row["tool_calls"]
            if (len(staged) != 1 or coalesce_tool_call_id(staged[0]) != call_id
                    or staged[0].get("function", {}).get("name") != "finish_noting"
                    or row.get(_DB_PERSISTED_MARKER) is not True):
                return False
            results = [item for item in messages[index + 1:] if item.get("role") == "tool"]
            return len(results) == 1 and _successful_receipt(results[0], call_id)
    return False


def controlled_finish(agent, exit_reason):
    return exit_reason == NOTING_FINISHED and finish_requested(agent)


def interrupt_reason(agent):
    from agent.interrupt_control import interrupt_issuer
    issuer = interrupt_issuer(agent)
    return f"interrupted_by_system({issuer})" if issuer else "interrupted_by_user"


def clear_finish_interrupt(agent, result):
    """Use the native interrupt publication lock at the existing finalizer clear edge."""
    def observe():
        if agent.is_interrupted:
            result.update(completed=False, interrupted=True, turn_exit_reason=interrupt_reason(agent))
            if agent._interrupt_message:
                result["interrupt_message"] = agent._interrupt_message
    agent.clear_interrupt(before_clear=observe)
