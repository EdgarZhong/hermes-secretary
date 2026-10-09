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
    child._noting_notebook_state = None


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


def after_noting_response(child):
    """The first request keeps exact Parent tools; later suffix requests expose semantic work."""
    if not getattr(child, "_secretary_noting_child", False):
        return
    child._secretary_noting_request_count = getattr(child, "_secretary_noting_request_count", 0) + 1
    if child._secretary_noting_request_count != 1:
        return
    schemas = [NOTEBOOK_MUTATE_SCHEMA]
    if child._secretary_noting_profile == "NOTING_WITH_COMPACTION":
        from secretary.noting_compact import COMPACT_PARENT_SCHEMA
        schemas.append(COMPACT_PARENT_SCHEMA)
    tools = copy.deepcopy(child.tools)
    names = {tool["function"]["name"] for tool in tools}
    tools.extend({"type": "function", "function": copy.deepcopy(schema)}
                 for schema in schemas if schema["name"] not in names)
    child.tools = tools
    child.valid_tool_names = {tool["function"]["name"] for tool in tools}
    child._secretary_noting_suffix_diverged = True


def record_noting_request(child, tools):
    """Audit the actual first request source before Hermes cache-marker decoration."""
    if not getattr(child, "_secretary_noting_child", False) or getattr(child, "_secretary_noting_request_count", 0):
        return
    child._secretary_noting_first_request_tools = copy.deepcopy(tools)
    child._secretary_noting_first_request_tools_parity = tools == child._secretary_noting_parent_tools
