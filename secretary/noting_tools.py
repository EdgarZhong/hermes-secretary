"""Task-bound six-tool Noting surface; Snapshot publication belongs to the runner."""

from __future__ import annotations

import copy
import json
import sqlite3
import threading
from datetime import datetime, timezone

from hermes_time import format_timestamp
from secretary.notebook_contract import NotebookValidationError, local_source_error
from secretary.notebook_render import (
    evidence_coverage, model_notebook_data, model_notebook_view,
    readable_notebook_entry, readable_notebook_state,
)
from secretary.noting_contract import (
    FINISH_NOTING_SCHEMA,
    NOTEBOOK_CREATE_SCHEMA,
    NOTEBOOK_UPDATE_SCHEMA,
    NOTEBOOK_ARCHIVE_SCHEMA,
    NOTEBOOK_SHOW_SCHEMA,
)
from secretary.noting_prompts import CURRENT_NOTING_CONTROL


def _encoded(result):
    return json.dumps(model_notebook_data(result), ensure_ascii=False)


def _error(message, *, code="invalid_argument", field=None, next_action=None):
    return NotebookValidationError(
        message, code=code, field=field,
        next_action=next_action or "Correct the named input; the working Notebook has not changed.",
    ).as_result()


def _bound_store(child):
    if not getattr(child, "_secretary_noting_child", False):
        raise NotebookValidationError(
            "Notebook maintenance is authorized only in a bound Noting task.", code="scope_denied",
            next_action="Use the Main read-only Notebook capability; do not retry a mutation here.",
        )
    store = getattr(child, "_noting_notebook_store", None)
    if (store is None or getattr(child, "_noting_notebook_lock", None) is not store.lock
            or store.conversation_ref != getattr(child, "_secretary_parent_conversation_ref", None)):
        raise NotebookValidationError(
            "There is no valid bound Notebook working view.", code="state_conflict",
            next_action="Let the runtime establish a bound task; do not supply a task or scope selector.",
        )
    return store


def initialize_notebook_work(child, *, trigger_type, frozen_work=None):
    from secretary.notebook_store import NotebookStore

    child._noting_notebook_lock = threading.RLock()
    options = {} if frozen_work is None else {"base_snapshot_id": frozen_work["base_snapshot_id"]}
    if frozen_work is not None and "working_state" in frozen_work:
        options["working_state"] = frozen_work["working_state"]
    child._noting_notebook_store = NotebookStore(
        child._session_db, child._secretary_parent_conversation_ref,
        anchor_message_uid=child._secretary_noting_anchor_uid,
        trigger_type=trigger_type, runtime_profile=child._secretary_noting_profile,
        lock=child._noting_notebook_lock, **options,
    )
    child._noting_notebook_state = child._noting_notebook_store.snapshot_state()
    child._secretary_noting_finish_result = None


def _mutation_args(args, schema):
    if not isinstance(args, dict):
        raise NotebookValidationError("Tool arguments must be an object.", field="arguments")
    parameters = schema["parameters"]
    unknown = set(args) - parameters["properties"].keys()
    if unknown:
        field = sorted(unknown)[0]
        raise NotebookValidationError(
            f"{schema['name']} does not accept {field}.", field=field,
            next_action="Use the tool's documented parameters directly; do not wrap them in action or changes.",
        )
    for field in parameters.get("required", []):
        if field not in args:
            raise NotebookValidationError(f"{schema['name']} requires {field}.", field=field)
    for field, value in args.items():
        value_type = parameters["properties"][field].get("type")
        if value is None and isinstance(value_type, str) and value_type != "null":
            raise NotebookValidationError(
                f"{field} requires a {value_type} value; null is not accepted.", field=field,
                next_action=f"Supply the documented {value_type} value; omit {field} only if it is optional.",
            )
    return args


def _notebook_mutation(child, args, schema):
    """One typed operation under the lock that also accepts end_requested."""
    try:
        store = _bound_store(child)
        with store.lock:
            if getattr(child, "_secretary_noting_terminal_action_done", False):
                return _encoded(_error(
                    f"The current state is end_requested; {schema['name']} cannot be applied.",
                    code="state_conflict", next_action="Use notebook_show to inspect the fixed view, then stop.",
                ))
            from secretary.noting_runtime import noting_trigger_gate
            if not noting_trigger_gate(child._session_db, store.conversation_ref)[0]:
                return _encoded(_error(
                    "Noting is effectively disabled for the bound Conversation.", code="scope_denied",
                    next_action="Keep the existing view; do not retry through another tool.",
                ))
            args = _mutation_args(args, schema)
            if schema["name"] == "notebook_create":
                result = store.create(**args)
            elif schema["name"] == "notebook_update":
                result = store.update(args["entry_id"], {key: value for key, value in args.items() if key != "entry_id"})
            else:
                result = store.archive(**args)
            child._noting_notebook_state = store.snapshot_state()
            if "entry" in result:
                result["entry"] = readable_notebook_entry(
                    result["entry"], db=child._session_db, conversation_ref=store.conversation_ref,
                    state=child._noting_notebook_state)
            if "updated_entries" in result:
                result["updated_entries"] = [readable_notebook_entry(
                    entry, db=child._session_db, conversation_ref=store.conversation_ref,
                    state=child._noting_notebook_state) for entry in result["updated_entries"]]
            return _encoded(result)
    except NotebookValidationError as exc:
        local_source_error(exc)
        return _encoded(exc.as_result())
    except sqlite3.Error:
        return _encoded(_error(
            "The Notebook database is temporarily unavailable.", code="temporarily_unavailable",
            next_action="Keep the current work; retry only through the normal task lifecycle later.",
        ))


def notebook_create(child, args):
    return _notebook_mutation(child, args, NOTEBOOK_CREATE_SCHEMA)


def notebook_update(child, args):
    return _notebook_mutation(child, args, NOTEBOOK_UPDATE_SCHEMA)


def notebook_archive(child, args):
    return _notebook_mutation(child, args, NOTEBOOK_ARCHIVE_SCHEMA)


def notebook_work_show(child, args):
    try:
        store = _bound_store(child)
        if not isinstance(args, dict) or args:
            return _encoded(_error("notebook_show accepts only an empty argument object.", field="arguments"))
        with store.lock:
            view = store.working_view()
            view["payload"] = readable_notebook_state(
                view["payload"], db=child._session_db, conversation_ref=store.conversation_ref)
            return _encoded(model_notebook_view(view, db=child._session_db))
    except NotebookValidationError as exc:
        return _encoded(exc.as_result())


def finish_noting(child, args):
    """Fix the first complete working state; this is deliberately not a commit."""
    try:
        store = _bound_store(child)
        if not isinstance(args, dict) or set(args) != {"reason"}:
            return _encoded(_error("finish_noting accepts only the required reason.", field="reason"))
        reason = args["reason"]
        if not isinstance(reason, str) or not reason.strip():
            return _encoded(_error("finish_noting requires a nonempty reason.", field="reason"))
        with store.lock:
            previous = child._secretary_noting_finish_result
            if previous is not None:
                return _encoded(previous)
            if getattr(child, "_secretary_noting_terminal_action_done", False):
                return _encoded(_error(
                    "The runtime has already closed this task.", code="state_conflict",
                    next_action="Stop; do not replace the runtime's termination reason.",
                ))
            child._noting_notebook_state = store.freeze()
            child._secretary_noting_termination = {"type": "finish_noting", "reason": reason.strip()}
            child._secretary_noting_terminal_action_done = True
            child._secretary_noting_finish_result = {"success": True, "status": "end_requested"}
            return _encoded(child._secretary_noting_finish_result)
    except NotebookValidationError as exc:
        return _encoded(exc.as_result())


def guard_noting_tool_batch(agent, tool_names):
    """Preflight the COMPLETE native batch before executing any call.

    C9 calls once for both sequential and concurrent dispatch. ``tool_names`` is
    the native batch's ordered sequence of resolved function names. A refusal is
    the same model-facing error result for every call, with no call dispatched.
    No task state or Batch DSL is introduced here; non-Noting batches return None.
    """
    if not getattr(agent, "_secretary_noting_child", False):
        return None
    names = list(tool_names)
    if "finish_noting" in names and len(names) != 1:
        return _error(
            "finish_noting must be the only call in its tool batch.", field="tool_calls",
            next_action="Complete other work first, then call finish_noting alone as the final action.",
        )
    return None


def noting_tool_schemas(profile="NOTING"):
    """Return independent canonical definitions for the six authorized tools."""
    if profile != "NOTING":
        raise ValueError("Unknown Noting runtime profile")
    from tools.session_history_tool import CONVERSATION_HISTORY_SCHEMA

    return copy.deepcopy([CONVERSATION_HISTORY_SCHEMA, NOTEBOOK_SHOW_SCHEMA,
                          NOTEBOOK_CREATE_SCHEMA, NOTEBOOK_UPDATE_SCHEMA, NOTEBOOK_ARCHIVE_SCHEMA,
                          FINISH_NOTING_SCHEMA])


def noting_tool_control_message(profile="NOTING", *, notebook_state=None, conversation_ref=None,
                                coverage=None, base_snapshot_id=None, current_time=None, db=None):
    """Encode all variable input as data after the exact frozen control text."""
    from secretary.notebook_model import SECTIONS

    if profile != "NOTING":
        raise ValueError("Unknown Noting runtime profile")
    data = {
        "conversation_ref": conversation_ref,
        "evidence_coverage": evidence_coverage(conversation_ref, coverage, db=db),
        "current_time": format_timestamp(current_time or datetime.now(timezone.utc)),
        "task_parameters": {"aging_days": 7, "implicit_gap_hours": 72},
        "working_notebook": model_notebook_data(readable_notebook_state(
            notebook_state if notebook_state is not None else {key: [] for key in SECTIONS},
            db=db, conversation_ref=conversation_ref)),
    }
    return (CURRENT_NOTING_CONTROL + "\n\n<noting-task-data>\n"
            + json.dumps(data, ensure_ascii=False, sort_keys=True) + "\n</noting-task-data>")


def after_noting_response(child):
    """Count native response cycles without mutating the frozen top-level tools."""
    if getattr(child, "_secretary_noting_child", False):
        child._secretary_noting_request_count = getattr(child, "_secretary_noting_request_count", 0) + 1


def record_noting_request(child, tools):
    """Audit every actual request before Hermes cache-marker decoration."""
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
