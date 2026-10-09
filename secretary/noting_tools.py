"""Noting-only semantic tools; the main agent has no mutation capability."""

from __future__ import annotations

import copy
import json
import threading

from secretary.notebook_model import OPTIONAL_FIELDS, REQUIRED_FIELDS, STATUS_TRANSITIONS, TYPE_SECTIONS

_OPERATIONS = {
    "create": {"entry_type", "fields", "status", "source_message_identities"},
    "edit": {"entry_id", "fields", "source_message_identities"},
    "archive": {"entry_id"}, "restore": {"entry_id"},
    "status": {"entry_id", "status"},
    "schedule_create": {"entry_id", "expression"},
    "schedule_update": {"entry_id", "expression"},
    "schedule_cancel": {"entry_id"},
}
FINISH_NOTING_SCHEMA = {
    "name": "finish_noting",
    "description": "Mark an ordinary Noting task complete after necessary Notebook work.",
    "parameters": {
        "type": "object",
        "properties": {
            "reason": {
                "type": "string",
                "description": (
                    "Briefly explain why this Noting task is complete, including what was "
                    "updated or why no changes were needed."
                ),
            },
        },
        "required": ["reason"],
        "additionalProperties": False,
    },
}

NOTEBOOK_MUTATE_SCHEMA = {
    "name": "notebook_mutate",
    "description": (
        "Maintain the task-local Notebook through semantic operations. Returns the complete entry "
        "and four-section state. No raw JSON replacement, SQL, or Schedule runtime fields. "
        "create requires entry_type and all its required fields; edit only updates semantic fields. "
        "archive/restore/status/Schedule operations require entry_id. Required fields by type: "
        + "; ".join(f"{kind}: {', '.join(fields) or 'provenance plus optional draft fields'}"
                    for kind, fields in REQUIRED_FIELDS.items())
        + ". Persistence candidates require valid source_message_identities from session_history."
    ),
    "parameters": {
        "type": "object", "additionalProperties": False,
        "properties": {
            "operation": {"type": "string", "enum": list(_OPERATIONS)},
            "entry_type": {"type": "string", "enum": list(TYPE_SECTIONS)},
            "entry_id": {"type": "string"},
            "fields": {"type": "object", "additionalProperties": False,
                       "description": "Only fields for the selected entry_type; include its required fields on create.",
                       "properties": {key: {"anyOf": [{"type": "string"}, {"type": "array", "items": {"type": "string"}}]}
                                      for group in (REQUIRED_FIELDS, OPTIONAL_FIELDS)
                                      for fields in group.values() for key in fields}},
            "status": {"type": "string", "description": "Legal status graph by entry type: "
                       + json.dumps(STATUS_TRANSITIONS, ensure_ascii=False)},
            "expression": {
                "type": "string",
                "description": (
                    "Required for schedule_create and schedule_update. "
                    "Time expression forms: "
                    "(1) recurring interval — '30m', 'every 2h', 'every hour' "
                    "(repeats indefinitely until cancelled); "
                    "(2) explicit one-shot delay — 'in 30m', 'in 2h' "
                    "(fires ONCE; use this for reminders after a duration, not a bare duration); "
                    "(3) natural day/time — 'every monday 9am', 'weekdays at 9am', "
                    "'every day at 9am' (recurring weekly/daily); "
                    "(4) cron syntax — '0 9 * * *' (daily at 9am); "
                    "(5) absolute one-shot — ISO timestamp '2026-11-01T09:00:00'. "
                    "A bare duration like '30m' means recurring, while 'in 30m' means one-shot. "
                    "Times without an explicit timezone use the configured Hermes timezone. "
                    "This expression defines an in-Conversation Notebook reminder, "
                    "NOT an independent Hermes Cron job."
                ),
            },
            "source_message_identities": {"type": "array", "items": {
                "type": "object", "additionalProperties": False,
                "properties": {"conversation_ref": {"type": "string"}, "message_uid": {"type": "string"}},
                "required": ["conversation_ref", "message_uid"],
            }},
        }, "required": ["operation"],
    },
}


def initialize_notebook_work(child, *, trigger_type):
    from secretary.notebook_store import NotebookStore

    child._noting_notebook_store = NotebookStore(
        child._session_db, child._secretary_parent_conversation_ref,
        trigger_type=trigger_type, runtime_profile=child._secretary_noting_profile,
    )
    child._noting_notebook_lock = threading.RLock()
    # A no-op Noting task still owns a complete legal working state.  Forced or
    # explicit completion may commit it through the ordinary Snapshot gate.
    child._noting_notebook_state = child._noting_notebook_store.show()


def notebook_mutate(child, args):
    if not getattr(child, "_secretary_noting_child", False):
        return json.dumps({"success": False, "error": "Notebook mutation is Noting-only"})
    try:
        from secretary.noting_runtime import noting_trigger_gate
        enabled, _reason = noting_trigger_gate(child._session_db, child._secretary_parent_conversation_ref)
        if not enabled:
            raise ValueError("Noting is effectively disabled")
        operation = args.get("operation")
        allowed = _OPERATIONS.get(operation)
        if allowed is None or args.keys() - (allowed | {"operation"}):
            raise ValueError("Unknown operation or non-semantic arguments")
        kwargs = {key: value for key, value in args.items() if key != "operation"}
        method = "transition_status" if operation == "status" else operation
        store = child._noting_notebook_store
        with child._noting_notebook_lock:
            entry = getattr(store, method)(**kwargs)
            child._noting_notebook_state = store.show()
            result = {"success": True, "entry": entry, "state": child._noting_notebook_state}
            return json.dumps(result, ensure_ascii=False)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        return json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False)


def notebook_work_show(child, args):
    if args:
        return json.dumps({"success": False, "error": "notebook_show takes no arguments"})
    with child._noting_notebook_lock:
        state = child._noting_notebook_store.show()
        child._noting_notebook_state = state
        return json.dumps({"success": True, "notebook": state}, ensure_ascii=False)


def finish_noting(child, args):
    """Ordinary-profile terminal marker. Snapshot commit remains framework-owned."""
    if getattr(child, "_secretary_noting_profile", None) != "NOTING":
        return json.dumps({"success": False, "error": "finish_noting is ordinary-Noting only"})
    if not isinstance(args, dict) or set(args) != {"reason"}:
        return json.dumps({"success": False, "error": "finish_noting accepts only the required reason"})
    reason = args.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        return json.dumps({"success": False, "error": "finish_noting requires a nonempty reason"})
    child._secretary_noting_terminal_action_done = True
    child._secretary_noting_termination = {"type": "finish_noting", "reason": reason.strip()}
    return json.dumps({"success": True, "status": "finished"}, ensure_ascii=False)


def noting_tool_schemas(profile):
    """Current Noting-only callable schemas, carried as suffix text rather than top-level tools[]."""
    from tools.notebook_tool import NOTEBOOK_SHOW_SCHEMA
    from tools.session_history_tool import SESSION_HISTORY_SCHEMA

    schemas = [SESSION_HISTORY_SCHEMA, NOTEBOOK_SHOW_SCHEMA, NOTEBOOK_MUTATE_SCHEMA]
    if profile == "NOTING_WITH_COMPACTION":
        from secretary.noting_compact import COMPACT_PARENT_SCHEMA
        schemas.append(COMPACT_PARENT_SCHEMA)
    else:
        schemas.append(FINISH_NOTING_SCHEMA)
    return copy.deepcopy(schemas)


def noting_tool_control_message(profile):
    schemas = noting_tool_schemas(profile)
    names = [schema["name"] for schema in schemas]
    return (
        "<noting-tools>\n"
        "For this Noting task, the following list and complete schemas are authoritative and "
        "replace any earlier statements about which tools are available to Noting. The Parent's "
        "frozen top-level tools[] remains unchanged for cache parity; actual execution is still "
        "restricted by the Noting dispatch whitelist.\n"
        f"Available tools: {', '.join(names)}\n"
        "Schemas:\n"
        + json.dumps(schemas, ensure_ascii=False, sort_keys=True)
        + "\n</noting-tools>"
    )


def after_noting_response(child):
    """Count completed request/response cycles without ever mutating frozen top-level tools[]."""
    if getattr(child, "_secretary_noting_child", False):
        child._secretary_noting_request_count = getattr(child, "_secretary_noting_request_count", 0) + 1


def record_noting_request(child, tools):
    """Audit every actual Noting request before Hermes cache-marker decoration."""
    if not getattr(child, "_secretary_noting_child", False):
        return
    snapshot = copy.deepcopy(tools)
    history = getattr(child, "_secretary_noting_request_tools_history", None)
    if not isinstance(history, list):
        history = child._secretary_noting_request_tools_history = []
    history.append(snapshot)
    parity = tools == child._secretary_noting_parent_tools
    child._secretary_noting_all_request_tools_parity = (
        parity and getattr(child, "_secretary_noting_all_request_tools_parity", True)
    )
    if len(history) == 1:
        child._secretary_noting_first_request_tools = snapshot
        child._secretary_noting_first_request_tools_parity = parity
