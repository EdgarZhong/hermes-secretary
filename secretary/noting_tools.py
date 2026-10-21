"""Task-bound four-tool Noting surface; Snapshot publication belongs to the runner."""

from __future__ import annotations

import copy
import json
import sqlite3
import threading
from datetime import datetime, timezone

from hermes_time import format_timestamp
from secretary.notebook_contract import NotebookValidationError, local_source_error
from secretary.notebook_render import evidence_coverage, model_notebook_view, readable_notebook_entry, readable_notebook_state
from secretary.noting_contract import (
    FINISH_NOTING_SCHEMA,
    NOTEBOOK_MAINTAIN_SCHEMA,
    NOTEBOOK_SHOW_SCHEMA,
)
from secretary.noting_prompts import CURRENT_NOTING_CONTROL


def _encoded(result):
    return json.dumps(result, ensure_ascii=False)


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


def notebook_maintain(child, args):
    """One semantic operation, under the same lock that accepts end_requested."""
    try:
        store = _bound_store(child)
        with store.lock:
            if getattr(child, "_secretary_noting_terminal_action_done", False):
                return _encoded(_error(
                    "The current state is end_requested; notebook_maintain cannot be applied.",
                    code="state_conflict", next_action="Use notebook_show to inspect the fixed view, then stop.",
                ))
            from secretary.noting_runtime import noting_trigger_gate
            if not noting_trigger_gate(child._session_db, store.conversation_ref)[0]:
                return _encoded(_error(
                    "Noting is effectively disabled for the bound Conversation.", code="scope_denied",
                    next_action="Keep the existing view; do not retry through another tool.",
                ))
            result = store.maintain(args)
            child._noting_notebook_state = store.snapshot_state()
            if "entry" in result:
                result["entry"] = readable_notebook_entry(result["entry"])
            return _encoded(result)
    except NotebookValidationError as exc:
        legacy_sources = isinstance(args, dict) and (
            "source_message_identities" in args or (
                isinstance(args.get("changes"), dict) and "source_message_identities" in args["changes"]))
        if not legacy_sources:
            local_source_error(exc)
        return _encoded(exc.as_result())
    except sqlite3.Error:
        return _encoded(_error(
            "The Notebook database is temporarily unavailable.", code="temporarily_unavailable",
            next_action="Keep the current work; retry only through the normal task lifecycle later.",
        ))


def notebook_work_show(child, args):
    try:
        store = _bound_store(child)
        if not isinstance(args, dict) or args:
            return _encoded(_error("notebook_show accepts only an empty argument object.", field="arguments"))
        with store.lock:
            view = model_notebook_view(store.working_view(), db=child._session_db)
            view["payload"] = readable_notebook_state(view["payload"])
            return _encoded(view)
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
    """Suffix declarations only: never change the frozen provider tools array."""
    if profile != "NOTING":
        raise ValueError("Unknown Noting runtime profile")
    from tools.session_history_tool import CONVERSATION_HISTORY_SCHEMA

    return copy.deepcopy([CONVERSATION_HISTORY_SCHEMA, NOTEBOOK_SHOW_SCHEMA,
                          NOTEBOOK_MAINTAIN_SCHEMA, FINISH_NOTING_SCHEMA])


def noting_tool_control_message(profile="NOTING", *, notebook_state=None, conversation_ref=None,
                                coverage=None, base_snapshot_id=None, current_time=None, db=None):
    """Encode all variable input as data after the exact frozen control text."""
    from secretary.notebook_model import SECTIONS

    data = {
        "conversation_ref": conversation_ref,
        "evidence_coverage": evidence_coverage(conversation_ref, coverage, db=db),
        "current_time": format_timestamp(current_time or datetime.now(timezone.utc)),
        "task_parameters": {"aging_days": 7, "implicit_gap_hours": 72},
        "working_notebook": readable_notebook_state(
            notebook_state if notebook_state is not None else {key: [] for key in SECTIONS}),
        "callable_tool_schemas": noting_tool_schemas(profile),
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
