"""Noting-only semantic tools; the main agent has no mutation capability."""

from __future__ import annotations

import copy
import json
import threading
from secretary.notebook_render import readable_notebook_entry, readable_notebook_state


_TOOL_OPERATIONS = {
    "notebook_manage": {
        "create": {"entry_type", "fields", "status", "source_message_identities", "source_time_range",
                   "expression", "delivery_mode"},
        "archive": {"entry_id"},
    },
    "notebook_edit": {
        "edit": {"entry_id", "fields", "source_message_identities", "source_time_range"},
        "status": {"entry_id", "status"},
    },
    "notebook_schedule": {
        "schedule_update": {"entry_id", "expression", "delivery_mode"},
        "schedule_cancel": {"entry_id"},
    },
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

NOTEBOOK_MANAGE_SCHEMA = {'name': 'notebook_manage',
 'description': "Notebook entry lifecycle. operation='create' opens a new entry and requires entry_type "
                'plus all required fields of that type (per-type field contract below); '
                "operation='archive' requires entry_id and removes the entry from the active Notebook. "
                'Returns the complete entry with its id plus the '
                'four-section state.',
 'parameters': {'type': 'object',
                'additionalProperties': False,
                'properties': {'operation': {'type': 'string', 'enum': ['create', 'archive']},
                               'entry_type': {'type': 'string',
                                              'enum': ['user_commitment',
                                                       'user_reminder',
                                                       'secretary_task',
                                                       'watchpoint',
                                                       'decision',
                                                       'open_question',
                                                       'formulating_insight',
                                                       'memory_candidate',
                                                       'rule_candidate',
                                                       'skill_candidate']},
                               'entry_id': {'type': 'string', 'description': 'Required for archive.'},
                               'fields': {'type': 'object',
                                          'additionalProperties': False,
                                          'description': 'create only. Only fields for the selected '
                                                         'entry_type. Required fields by type: '
                                                         'user_commitment: what, intent; user_reminder: '
                                                         'message; secretary_task: task (future work, not a completed-work log), purpose; '
                                                         'watchpoint: subject, what_to_watch, why, '
                                                         'until; decision: decision, rationale; '
                                                         'open_question: question, why_it_matters; '
                                                         'formulating_insight: insight, basis; '
                                                         'memory_candidate/rule_candidate/skill_candidate: '
                                                         'no required fields (provenance via '
                                                         'source_message_identities). Optional fields '
                                                         'by type: memory_candidate: draft, '
                                                         'why_persist; rule_candidate: draft_rule, '
                                                         'reason, scope; skill_candidate: capability, '
                                                         'workflow_draft, why_reusable; open_question: '
                                                         'needed_information; formulating_insight: '
                                                         'uncertainty, what_would_confirm, '
                                                         'what_would_refute.',
                                          'properties': {'basis': {'anyOf': [{'type': 'string'},
                                                                             {'type': 'array',
                                                                              'items': {'type': 'string'}}]},
                                                         'capability': {'anyOf': [{'type': 'string'},
                                                                                  {'type': 'array',
                                                                                   'items': {'type': 'string'}}]},
                                                         'decision': {'anyOf': [{'type': 'string'},
                                                                                {'type': 'array',
                                                                                 'items': {'type': 'string'}}]},
                                                         'draft': {'anyOf': [{'type': 'string'},
                                                                             {'type': 'array',
                                                                              'items': {'type': 'string'}}]},
                                                         'draft_rule': {'anyOf': [{'type': 'string'},
                                                                                  {'type': 'array',
                                                                                   'items': {'type': 'string'}}]},
                                                         'insight': {'anyOf': [{'type': 'string'},
                                                                               {'type': 'array',
                                                                                'items': {'type': 'string'}}]},
                                                         'intent': {'anyOf': [{'type': 'string'},
                                                                              {'type': 'array',
                                                                               'items': {'type': 'string'}}]},
                                                         'message': {'anyOf': [{'type': 'string'},
                                                                               {'type': 'array',
                                                                                'items': {'type': 'string'}}]},
                                                         'needed_information': {'anyOf': [{'type': 'string'},
                                                                                          {'type': 'array',
                                                                                           'items': {'type': 'string'}}]},
                                                         'purpose': {'anyOf': [{'type': 'string'},
                                                                               {'type': 'array',
                                                                                'items': {'type': 'string'}}]},
                                                         'question': {'anyOf': [{'type': 'string'},
                                                                                {'type': 'array',
                                                                                 'items': {'type': 'string'}}]},
                                                         'rationale': {'anyOf': [{'type': 'string'},
                                                                                 {'type': 'array',
                                                                                  'items': {'type': 'string'}}]},
                                                         'reason': {'anyOf': [{'type': 'string'},
                                                                              {'type': 'array',
                                                                               'items': {'type': 'string'}}]},
                                                         'scope': {'anyOf': [{'type': 'string'},
                                                                             {'type': 'array',
                                                                              'items': {'type': 'string'}}]},
                                                         'subject': {'anyOf': [{'type': 'string'},
                                                                               {'type': 'array',
                                                                                'items': {'type': 'string'}}]},
                                                         'task': {'anyOf': [{'type': 'string'},
                                                                            {'type': 'array',
                                                                             'items': {'type': 'string'}}]},
                                                         'uncertainty': {'anyOf': [{'type': 'string'},
                                                                                   {'type': 'array',
                                                                                    'items': {'type': 'string'}}]},
                                                         'until': {'anyOf': [{'type': 'string'},
                                                                             {'type': 'array',
                                                                              'items': {'type': 'string'}}]},
                                                         'what': {'anyOf': [{'type': 'string'},
                                                                            {'type': 'array',
                                                                             'items': {'type': 'string'}}]},
                                                         'what_to_watch': {'anyOf': [{'type': 'string'},
                                                                                     {'type': 'array',
                                                                                      'items': {'type': 'string'}}]},
                                                         'what_would_confirm': {'anyOf': [{'type': 'string'},
                                                                                          {'type': 'array',
                                                                                           'items': {'type': 'string'}}]},
                                                         'what_would_refute': {'anyOf': [{'type': 'string'},
                                                                                         {'type': 'array',
                                                                                          'items': {'type': 'string'}}]},
                                                         'why': {'anyOf': [{'type': 'string'},
                                                                           {'type': 'array',
                                                                            'items': {'type': 'string'}}]},
                                                         'why_it_matters': {'anyOf': [{'type': 'string'},
                                                                                      {'type': 'array',
                                                                                       'items': {'type': 'string'}}]},
                                                         'why_persist': {'anyOf': [{'type': 'string'},
                                                                                   {'type': 'array',
                                                                                    'items': {'type': 'string'}}]},
                                                         'why_reusable': {'anyOf': [{'type': 'string'},
                                                                                    {'type': 'array',
                                                                                     'items': {'type': 'string'}}]},
                                                         'workflow_draft': {'anyOf': [{'type': 'string'},
                                                                                      {'type': 'array',
                                                                                       'items': {'type': 'string'}}]}}},
                               'status': {'type': 'string',
                                          'description': 'create only, optional initial status; see '
                                                         'notebook_edit for the legal status '
                                                         'transitions of each entry_type.'},
                               'expression': {'type': 'string',
                                              'description': 'create only; REQUIRED for secretary_task, otherwise optional. Sets the new '
                                                             "entry's initial Schedule intent; only for "
                                                             'entry types that may carry a Schedule '
                                                             '(§3.8). For watchpoint, the required '
                                                             "field 'until' already defines its "
                                                             'one-shot Schedule — do not pass '
                                                             'expression. Same expression forms as '
                                                             'notebook_schedule.'},
                               'delivery_mode': {'type': 'string',
                                                 'enum': ['instant', 'deferred'],
                                                 'description': 'create only, REQUIRED for '
                                                                'every secretary_task: instant '
                                                                'fires at the due moment and may start '
                                                                'a Turn; deferred is delivered with the '
                                                                'next active request and never starts a '
                                                                'Turn. No default. Forbidden for all '
                                                                'other entry types.'},
                               'source_message_identities': {'type': 'array',
                                                             'items': {'type': 'object',
                                                                       'additionalProperties': False,
                                                                       'properties': {'conversation_ref': {'type': 'string'},
                                                                                      'message_uid': {'type': 'string'}},
                                                                       'required': ['conversation_ref',
                                                                                    'message_uid']},
                                                             'description': 'Candidate provenance: '
                                                                            'Message Identities from '
                                                                            'session_history results, '
                                                                            'or a source_time_range '
                                                                            '({start_time, end_time}) '
                                                                            'per §2.5; at least one '
                                                                            'valid form required for '
                                                                            'candidates.'},
                               'source_time_range': {'type': 'object',
                                                     'additionalProperties': False,
                                                     'properties': {'start_time': {'type': 'string'},
                                                                    'end_time': {'type': 'string'}},
                                                     'required': ['start_time', 'end_time']}},
                'required': ['operation']}}

NOTEBOOK_EDIT_SCHEMA = {'name': 'notebook_edit',
 'description': "Notebook entry content editing. operation='edit' updates semantic fields (requires "
                "entry_id + fields); operation='status' performs one legal status transition (requires "
                'entry_id + status, the TARGET status). Both insert a new version and return the '
                'complete entry with its NEW id (the id advances on every change) plus the four-section '
                'state.',
 'parameters': {'type': 'object',
                'additionalProperties': False,
                'properties': {'operation': {'type': 'string', 'enum': ['edit', 'status']},
                               'entry_id': {'type': 'string'},
                               'fields': {'type': 'object',
                                          'additionalProperties': False,
                                          'description': 'edit only. Only fields belonging to the '
                                                         "entry's type.",
                                          'properties': {'basis': {'anyOf': [{'type': 'string'},
                                                                             {'type': 'array',
                                                                              'items': {'type': 'string'}}]},
                                                         'capability': {'anyOf': [{'type': 'string'},
                                                                                  {'type': 'array',
                                                                                   'items': {'type': 'string'}}]},
                                                         'decision': {'anyOf': [{'type': 'string'},
                                                                                {'type': 'array',
                                                                                 'items': {'type': 'string'}}]},
                                                         'draft': {'anyOf': [{'type': 'string'},
                                                                             {'type': 'array',
                                                                              'items': {'type': 'string'}}]},
                                                         'draft_rule': {'anyOf': [{'type': 'string'},
                                                                                  {'type': 'array',
                                                                                   'items': {'type': 'string'}}]},
                                                         'insight': {'anyOf': [{'type': 'string'},
                                                                               {'type': 'array',
                                                                                'items': {'type': 'string'}}]},
                                                         'intent': {'anyOf': [{'type': 'string'},
                                                                              {'type': 'array',
                                                                               'items': {'type': 'string'}}]},
                                                         'message': {'anyOf': [{'type': 'string'},
                                                                               {'type': 'array',
                                                                                'items': {'type': 'string'}}]},
                                                         'needed_information': {'anyOf': [{'type': 'string'},
                                                                                          {'type': 'array',
                                                                                           'items': {'type': 'string'}}]},
                                                         'purpose': {'anyOf': [{'type': 'string'},
                                                                               {'type': 'array',
                                                                                'items': {'type': 'string'}}]},
                                                         'question': {'anyOf': [{'type': 'string'},
                                                                                {'type': 'array',
                                                                                 'items': {'type': 'string'}}]},
                                                         'rationale': {'anyOf': [{'type': 'string'},
                                                                                 {'type': 'array',
                                                                                  'items': {'type': 'string'}}]},
                                                         'reason': {'anyOf': [{'type': 'string'},
                                                                              {'type': 'array',
                                                                               'items': {'type': 'string'}}]},
                                                         'scope': {'anyOf': [{'type': 'string'},
                                                                             {'type': 'array',
                                                                              'items': {'type': 'string'}}]},
                                                         'subject': {'anyOf': [{'type': 'string'},
                                                                               {'type': 'array',
                                                                                'items': {'type': 'string'}}]},
                                                         'task': {'anyOf': [{'type': 'string'},
                                                                            {'type': 'array',
                                                                             'items': {'type': 'string'}}]},
                                                         'uncertainty': {'anyOf': [{'type': 'string'},
                                                                                   {'type': 'array',
                                                                                    'items': {'type': 'string'}}]},
                                                         'until': {'anyOf': [{'type': 'string'},
                                                                             {'type': 'array',
                                                                              'items': {'type': 'string'}}]},
                                                         'what': {'anyOf': [{'type': 'string'},
                                                                            {'type': 'array',
                                                                             'items': {'type': 'string'}}]},
                                                         'what_to_watch': {'anyOf': [{'type': 'string'},
                                                                                     {'type': 'array',
                                                                                      'items': {'type': 'string'}}]},
                                                         'what_would_confirm': {'anyOf': [{'type': 'string'},
                                                                                          {'type': 'array',
                                                                                           'items': {'type': 'string'}}]},
                                                         'what_would_refute': {'anyOf': [{'type': 'string'},
                                                                                         {'type': 'array',
                                                                                          'items': {'type': 'string'}}]},
                                                         'why': {'anyOf': [{'type': 'string'},
                                                                           {'type': 'array',
                                                                            'items': {'type': 'string'}}]},
                                                         'why_it_matters': {'anyOf': [{'type': 'string'},
                                                                                      {'type': 'array',
                                                                                       'items': {'type': 'string'}}]},
                                                         'why_persist': {'anyOf': [{'type': 'string'},
                                                                                   {'type': 'array',
                                                                                    'items': {'type': 'string'}}]},
                                                         'why_reusable': {'anyOf': [{'type': 'string'},
                                                                                    {'type': 'array',
                                                                                     'items': {'type': 'string'}}]},
                                                         'workflow_draft': {'anyOf': [{'type': 'string'},
                                                                                      {'type': 'array',
                                                                                       'items': {'type': 'string'}}]}}},
                               'status': {'type': 'string',
                                          'description': 'status only — pass the TARGET status; it must '
                                                         "be reachable from the entry's current status "
                                                         'in exactly one step. Legal transitions by '
                                                         'entry_type: user_commitment: '
                                                         'pending→in_progress|dropped, '
                                                         'in_progress→done|dropped; user_reminder: '
                                                         'active→delivered|cancelled; secretary_task: '
                                                         'pending→running|failed|dropped, '
                                                         'running→done|failed|dropped; watchpoint: '
                                                         'watching→resolved|dropped; decision: '
                                                         'active→superseded|revoked; open_question: '
                                                         'open→resolved|dropped; formulating_insight: '
                                                         'forming→validated|rejected|superseded; '
                                                         'memory_candidate, rule_candidate, '
                                                         'skill_candidate: NO status transitions — '
                                                         'never pass status for these.'},
                               'source_message_identities': {'type': 'array',
                                                             'items': {'type': 'object',
                                                                       'additionalProperties': False,
                                                                       'properties': {'conversation_ref': {'type': 'string'},
                                                                                      'message_uid': {'type': 'string'}},
                                                                       'required': ['conversation_ref',
                                                                                    'message_uid']}},
                               'source_time_range': {'type': 'object',
                                                     'additionalProperties': False,
                                                     'properties': {'start_time': {'type': 'string'},
                                                                    'end_time': {'type': 'string'}},
                                                     'required': ['start_time', 'end_time']}},
                'required': ['operation']}}

NOTEBOOK_SCHEDULE_SCHEMA = {'name': 'notebook_schedule',
 'description': 'Notebook Schedule-intent editing on existing entries that may carry a Schedule (§3.8). '
                'schedule_update requires entry_id + expression; schedule_cancel requires entry_id; '
                'forbidden for secretary_task — use notebook_manage archive. (A '
                "NEW entry's initial Schedule is set inside notebook_manage create — watchpoint.until "
                'or the expression argument — so this tool has no schedule_create.) Every change '
                'returns the complete entry with its NEW id plus the four-section state. A Notebook '
                'Schedule delivers in-Conversation reminders — it is NOT an independent Hermes Cron '
                'job.',
 'parameters': {'type': 'object',
                'additionalProperties': False,
                'properties': {'operation': {'type': 'string',
                                             'enum': ['schedule_update', 'schedule_cancel']},
                               'entry_id': {'type': 'string'},
                               'delivery_mode': {'type': 'string',
                                                 'enum': ['instant', 'deferred'],
                                                 'description': 'schedule_update only, and only for '
                                                                "secretary_task: changes the Schedule's "
                                                                'delivery mode. instant fires at the '
                                                                'due moment and may start a Turn; '
                                                                'deferred is delivered with the next '
                                                                'active request. Forbidden for all '
                                                                'other entry types.'},
                               'expression': {'type': 'string',
                                              'description': 'Required for schedule_update. Time '
                                                             'expression forms: (1) recurring interval '
                                                             "— '30m', 'every 2h', 'every hour' "
                                                             '(repeats indefinitely until cancelled); '
                                                             "(2) explicit one-shot delay — 'in 30m', "
                                                             "'in 2h' (fires ONCE; use this for "
                                                             'reminders after a duration, not a bare '
                                                             "duration); (3) natural day/time — 'every "
                                                             "monday 9am', 'weekdays at 9am', 'every "
                                                             "day at 9am' (recurring weekly/daily); (4) "
                                                             "cron syntax — '0 9 * * *' (daily at 9am); "
                                                             '(5) absolute one-shot — ISO timestamp '
                                                             "'2026-11-01T09:00:00'. A bare duration "
                                                             "like '30m' means recurring, while 'in "
                                                             "30m' means one-shot. Times without an "
                                                             'explicit timezone use the configured '
                                                             'Hermes timezone.'}},
                'required': ['operation']}}


def initialize_notebook_work(child, *, trigger_type):
    from secretary.notebook_store import NotebookStore

    child._noting_notebook_store = NotebookStore(
        child._session_db, child._secretary_parent_conversation_ref,
        trigger_type=trigger_type, runtime_profile=child._secretary_noting_profile,
    )
    child._noting_notebook_lock = threading.RLock()
    # A no-op Noting task still owns a complete legal working state.  Forced or
    # explicit completion may commit it through the ordinary Snapshot gate.
    child._noting_notebook_state = child._noting_notebook_store.snapshot_state()


def _notebook_operation(child, args, tool_name):
    if not getattr(child, "_secretary_noting_child", False):
        return json.dumps({"success": False, "error": f"{tool_name} is Noting-only"})
    try:
        from secretary.noting_runtime import noting_trigger_gate
        enabled, _reason = noting_trigger_gate(child._session_db, child._secretary_parent_conversation_ref)
        if not enabled:
            raise ValueError("Noting is effectively disabled")
        operation = args.get("operation")
        allowed = _TOOL_OPERATIONS[tool_name].get(operation)
        if allowed is None or args.keys() - (allowed | {"operation"}):
            raise ValueError(f"Unknown {tool_name} operation or non-semantic arguments")
        kwargs = {key: value for key, value in args.items() if key != "operation"}
        method = "transition_status" if operation == "status" else operation
        store = child._noting_notebook_store
        with child._noting_notebook_lock:
            entry = getattr(store, method)(**kwargs)
            child._noting_notebook_state = store.snapshot_state()
            result = {"success": True, "entry": readable_notebook_entry(entry),
                      "state": readable_notebook_state(store.show())}
            return json.dumps(result, ensure_ascii=False)
    except (AttributeError, KeyError, TypeError, ValueError) as exc:
        return json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False)


def notebook_manage(child, args):
    return _notebook_operation(child, args, "notebook_manage")


def notebook_edit(child, args):
    return _notebook_operation(child, args, "notebook_edit")


def notebook_schedule(child, args):
    return _notebook_operation(child, args, "notebook_schedule")


def notebook_work_show(child, args):
    if args:
        return json.dumps({"success": False, "error": "notebook_show takes no arguments"})
    with child._noting_notebook_lock:
        state = child._noting_notebook_store.show()
        child._noting_notebook_state = child._noting_notebook_store.snapshot_state()
        return json.dumps({"success": True, "notebook": readable_notebook_state(state)}, ensure_ascii=False)


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

    schemas = [SESSION_HISTORY_SCHEMA, NOTEBOOK_SHOW_SCHEMA, NOTEBOOK_MANAGE_SCHEMA,
               NOTEBOOK_EDIT_SCHEMA, NOTEBOOK_SCHEDULE_SCHEMA]
    if profile == "NOTING_WITH_COMPACTION":
        from secretary.noting_compact import COMPACT_PARENT_SCHEMA
        schemas.append(COMPACT_PARENT_SCHEMA)
    else:
        schemas.append(FINISH_NOTING_SCHEMA)
    return copy.deepcopy(schemas)


def noting_tool_control_message(profile, *, notebook_state=None):
    from secretary.notebook_model import SECTIONS
    if notebook_state is not None:
        notebook_state = readable_notebook_state(notebook_state)
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
        + "\nCurrent Notebook:\n"
        + json.dumps(notebook_state if notebook_state is not None else {
            section: [] for section in ("user", "assistant", "consultation", "persistence")},
                     ensure_ascii=False, sort_keys=True)
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
