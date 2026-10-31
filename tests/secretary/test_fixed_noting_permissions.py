"""Fixed advertised tools and task-bound dispatch through real Loop/SDK/DB paths."""

import copy
import json
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from openai import OpenAI

from agent.cache_parity import apply_cache_parity_from_parent
from agent.tool_executor import execute_tool_calls_concurrent, execute_tool_calls_sequential
from secretary.noting_child import NOTING_ALLOWED_TOOL_NAMES, build_noting_child, noting_dispatch_block, run_noting_task
from secretary.noting_contract import FINISH_NOTING_SCHEMA, NOTEBOOK_CREATE_SCHEMA, NOTEBOOK_UPDATE_SCHEMA, NOTEBOOK_ARCHIVE_SCHEMA
from secretary.noting_tools import initialize_notebook_work
from tests.secretary import test_noting_surface as surface

MAINTENANCE = {"notebook_create", "notebook_update", "notebook_archive", "finish_noting"}
DENIED_CHILD = ["terminal", "scheduler", "tool_search", "tool_call", "delegate_task", "notebook_maintain_tool"]


def call(name, args=None, uid="call"):
    if name in {"notebook_create", "notebook_update"} and (args or {}).get("source_message_uids"):
        args = {"source_description": "The user stated the report responsibility.", **args}
    return {"id": uid, "type": "function", "function": {"name": name, "arguments": json.dumps(args or {})}}


def native_call(name, args=None, uid="call"):
    value = call(name, args, uid)
    value["function"] = SimpleNamespace(**value["function"])
    return SimpleNamespace(**value)


def assert_permission_error(payload, agent, name):
    result = json.loads(payload) if isinstance(payload, str) else payload
    assert set(result) == {"success", "error"}
    assert result["success"] is False
    assert set(result["error"]) == {"code", "message", "next_action"}
    assert result["error"]["code"] == "scope_denied"
    assert result["error"]["message"] == noting_dispatch_block(agent, name)
    assert isinstance(result["error"]["message"], str)
    assert isinstance(result["error"]["next_action"], str) and result["error"]["next_action"].strip()
    return result


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    with contextmanager(surface.runtime.__wrapped__)(tmp_path, monkeypatch) as (db, config):
        state = {"sent": [], "script": []}

        def transport(request):
            payload = json.loads(request.content)
            state["sent"].append(payload)
            batch = state["script"].pop(0) if state["script"] else None
            if callable(batch):
                batch = batch(payload)
            message = {"role": "assistant", "content": "done" if batch is None else None}
            if batch is not None:
                message["tool_calls"] = batch
            return httpx.Response(200, json={
                "id": "controlled", "object": "chat.completion", "model": "test-model",
                "choices": [{"index": 0, "message": message,
                             "finish_reason": "stop" if batch is None else "tool_calls"}],
            })

        def client(**kwargs):
            old = kwargs.pop("http_client", None)
            if old is not None:
                old.close()
            kwargs["max_retries"] = 0
            return OpenAI(**kwargs, http_client=httpx.Client(transport=httpx.MockTransport(transport)))

        monkeypatch.setattr("agent.process_bootstrap.OpenAI", client)
        monkeypatch.setattr("agent.turn_api_call._should_stream", lambda _agent: False)
        parent = surface._agent(db, selected=["todo"])
        parent._disable_streaming = True
        surface._turn(parent, "I will send the report.")
        yield parent, db, config, state
        parent.close()


def bound_child(parent):
    child = build_noting_child(parent, runtime_profile="NOTING", parent_conversation_ref=parent._secretary_conversation_ref)
    child._disable_streaming = True
    child._secretary_noting_anchor_uid = parent._session_messages[-1]["message_uid"]
    initialize_notebook_work(child, trigger_type="manual")
    return child


def tool_rows(payload):
    return [row for row in payload["messages"] if row["role"] == "tool"]


def result_entry(payload, call_id):
    return next(json.loads(row["content"])["entry"] for row in tool_rows(payload) if row["tool_call_id"] == call_id)


def test_schema_and_direct_catalog_are_fixed(runtime):
    from tools import tool_search
    from tools.secretary_dispatch import filter_tool_definitions, secretary_surface_scope
    parent, _db, _config, state = runtime
    expected = {schema["name"]: schema for schema in (
        NOTEBOOK_CREATE_SCHEMA, NOTEBOOK_UPDATE_SCHEMA, NOTEBOOK_ARCHIVE_SCHEMA, FINISH_NOTING_SCHEMA)}
    sent = {tool["function"]["name"]: tool["function"] for tool in state["sent"][-1]["tools"]}
    assert all(sent[name] == schema for name, schema in expected.items())
    with secretary_surface_scope(parent):
        raw = filter_tool_definitions(copy.deepcopy(parent.tools), parent)
        assembled = tool_search.assemble_tool_defs(raw, context_length=256000).tool_defs
        assert MAINTENANCE <= surface._names(assembled)
        assert not MAINTENANCE & tool_search.scoped_deferrable_names(raw)
        assert all(not tool_search.is_deferrable_tool_name(name, frozenset(MAINTENANCE)) for name in MAINTENANCE)


@pytest.mark.parametrize("name", sorted(MAINTENANCE))
def test_main_loop_refuses_advertised_maintenance_before_repair(runtime, monkeypatch, name):
    parent, db, _config, state = runtime
    repair = MagicMock(side_effect=AssertionError("permission denial must not invoke name repair"))
    monkeypatch.setattr(parent, "_repair_tool_call", repair)
    before = db.notebook_current(parent._secretary_conversation_ref)
    state["script"] = [[call(name, {"reason": "claim Noting", "_secretary_noting_child": True})],
                       [call("conversation_history", {"mode": "read", "limit": 1}, "legal")], None]
    surface._turn(parent, "continue normally")
    assert db.notebook_current(parent._secretary_conversation_ref) == before
    rows = tool_rows(state["sent"][-1])
    assert_permission_error(next(row["content"] for row in rows if row["tool_call_id"] == "call"), parent, name)
    assert json.loads(next(row["content"] for row in rows if row["tool_call_id"] == "legal"))["success"]
    repair.assert_not_called()
    assert MAINTENANCE <= surface._names(state["sent"][-1]["tools"])


def test_main_mixed_batch_preserves_native_valid_calls(runtime, monkeypatch):
    parent, _db, _config, state = runtime
    original = parent._repair_tool_call
    seen = []
    def repair(name):
        seen.append(name)
        return original(name)
    monkeypatch.setattr(parent, "_repair_tool_call", repair)
    state["script"] = [[call("notebook_create"), call("conversation_history", {"mode": "read", "limit": 1}, "history")], None]
    surface._turn(parent, "normal evidence read")
    rows = tool_rows(state["sent"][-1])
    assert any(row["tool_call_id"] == "history" and json.loads(row["content"])["success"] for row in rows)
    assert_permission_error(next(row["content"] for row in rows if row["tool_call_id"] == "call"), parent, "notebook_create")
    assert "notebook_create" not in seen


@pytest.mark.parametrize("executor", [execute_tool_calls_sequential, execute_tool_calls_concurrent])
@pytest.mark.parametrize("name", sorted(MAINTENANCE))
def test_main_batch_and_direct_invoke_cannot_execute(runtime, executor, name):
    parent, db, _config, _state = runtime
    before = db.notebook_current(parent._secretary_conversation_ref)
    messages = [{"role": "user", "content": "go"}]
    executor(parent, SimpleNamespace(tool_calls=[native_call(name, {"reason": "forged"})]), messages, "test")
    assert_permission_error(messages[-1]["content"], parent, name)
    for bypass in (False, True):
        result = parent._invoke_tool(name, {"reason": "forged"}, "test", pre_tool_block_checked=bypass)
        assert_permission_error(result, parent, name)
    assert db.notebook_current(parent._secretary_conversation_ref) == before


@pytest.mark.parametrize("name", DENIED_CHILD)
def test_child_loop_refuses_every_non_whitelisted_name_without_repair(runtime, monkeypatch, name):
    parent, _db, _config, state = runtime
    child = bound_child(parent)
    before = child._noting_notebook_store.show()
    monkeypatch.setattr(child, "_repair_tool_call", MagicMock(side_effect=AssertionError("no repair")))
    state["script"] = [[call(name, {"name": "notebook_create", "arguments": {}})],
                       [call("notebook_show", {}, "legal")], None]
    try:
        surface._turn(child, "maintain")
        rows = tool_rows(state["sent"][-1])
        assert_permission_error(next(row["content"] for row in rows if row["tool_call_id"] == "call"), child, name)
        assert json.loads(next(row["content"] for row in rows if row["tool_call_id"] == "legal"))["success"]
        assert child._noting_notebook_store.show() == before
        assert child.valid_tool_names == set(NOTING_ALLOWED_TOOL_NAMES)
        assert child.tools == parent.tools
    finally:
        child.close()


@pytest.mark.parametrize("executor", [execute_tool_calls_sequential, execute_tool_calls_concurrent])
@pytest.mark.parametrize("name", DENIED_CHILD)
def test_child_executor_and_direct_invoke_reject_wrappers(runtime, executor, name):
    parent, _db, _config, _state = runtime
    child = bound_child(parent)
    try:
        messages = [{"role": "user", "content": "go"}]
        args = {"name": "notebook_show", "arguments": {}}
        executor(child, SimpleNamespace(tool_calls=[native_call(name, args)]), messages, "test")
        assert_permission_error(messages[-1]["content"], child, name)
        assert_permission_error(child._invoke_tool(name, args, "test", pre_tool_block_checked=True), child, name)
        assert json.loads(child._invoke_tool("notebook_show", {}, "test"))["success"]
    finally:
        child.close()


def test_real_runner_uses_all_six_tools_finishes_and_keeps_parent_prefix(runtime):
    parent, db, _config, state = runtime
    prefix = copy.deepcopy(parent._session_messages)
    anchor = prefix[-1]["message_uid"]
    user_uid = next(row["message_uid"] for row in prefix if row["role"] == "user")
    parent_request = copy.deepcopy(state["sent"][-1])
    state["sent"].clear()
    state["script"] = [
        [call("conversation_history", {"mode": "read", "limit": 2}, "read")],
        [call("notebook_show", {}, "show")],
        [call("notebook_create", {"entry_type": "matter", "fields": {
            "description": "send report", "completion_condition": "Report sent"}, "source_message_uids": [user_uid]}, "create")],
        lambda payload: [call("notebook_update", {"entry_id": result_entry(payload, "create")["entry_id"], "fields": {"blocker": "Awaiting review"},
            "source_message_uids": [user_uid],
            "schedule_suggestion": {"content": "Follow up on the report after review; the report is still waiting for reviewer acceptance.",
                                    "schedule": "after the reviewer responds"}}, "update")],
        [call("notebook_create", {"entry_type": "matter", "fields": {
            "description": "transient duplicate", "completion_condition": "merged"},
            "source_message_uids": [user_uid]}, "temporary")],
        lambda payload: [call("notebook_archive", {"entry_id": result_entry(payload, "temporary")["entry_id"],
            "reason": "Duplicate scope is covered by the report entry."}, "archive")],
        [call("finish_noting", {"reason": "Indexed the report commitment."}, "finish")], None,
    ]
    admission = db.noting_admit(parent._secretary_conversation_ref, anchor, kind="manual")
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=parent._secretary_conversation_ref,
                             anchor_message_uid=anchor, trigger_type="manual", runtime_profile="NOTING",
                             task_instruction="Maintain the Notebook.")
    assert outcome.committed and outcome.termination["type"] == "finish_noting"
    assert db.notebook_current(parent._secretary_conversation_ref)["payload"]["work"][0]["fields"]["description"] == "send report"
    current = db.notebook_current(parent._secretary_conversation_ref)["payload"]["work"]
    assert len(current) == 1 and current[0]["fields"]["blocker"] == "Awaiting review"
    assert current[0]["schedule_suggestion"]["schedule"] == "after the reviewer responds"
    assert not db._read_all("SELECT * FROM secretary_schedule_registry")
    assert len(state["sent"]) == 7
    for payload in state["sent"]:
        assert payload["tools"] == parent_request["tools"]
        assert payload["messages"][:len(parent_request["messages"]) + 1] == [*parent_request["messages"], {"role": "assistant", "content": "done"}]
    all_rows = [row for row in db.get_messages_as_conversation(outcome.child_session_id) if row["role"] == "tool"]
    assert {row["tool_call_id"] for row in all_rows} == {"read", "show", "create", "update", "temporary", "archive", "finish"}
    assert all(json.loads(row["content"])["success"] for row in all_rows)
    assert json.loads(all_rows[-1]["content"]) == {"success": True, "status": "end_requested"}


def test_child_loop_rejects_complete_finish_mixture_before_any_effect(runtime):
    parent, _db, _config, state = runtime
    child = bound_child(parent)
    user_uid = next(row["message_uid"] for row in parent._session_messages if row["role"] == "user")
    mutation = {"entry_type": "matter", "fields": {
        "description": "send report", "completion_condition": "Report sent"}, "source_message_uids": [user_uid]}
    state["script"] = [[call("notebook_create", mutation, "write"), call("finish_noting", {"reason": "mixed"}, "mixed")],
                       [call("notebook_show", {}, "show")], [call("finish_noting", {"reason": "done"}, "finish")], None]
    try:
        surface._turn(child, "maintain")
        rows = tool_rows(state["sent"][-1])
        refusals = [json.loads(row["content"]) for row in rows if row["tool_call_id"] in {"write", "mixed"}]
        assert len(refusals) == 2
        assert all(result["error"]["code"] == "invalid_argument" for result in refusals)
        assert child._noting_notebook_store.show()["work"] == []
        assert child._secretary_noting_termination == {"type": "finish_noting", "reason": "done"}
    finally:
        child.close()


@pytest.mark.parametrize("executor", [execute_tool_calls_sequential, execute_tool_calls_concurrent])
def test_finish_mixture_and_end_requested_do_not_mutate(runtime, executor):
    parent, _db, _config, _state = runtime
    child = bound_child(parent)
    try:
        before = child._noting_notebook_store.show()
        messages = [{"role": "user", "content": "go"}]
        executor(child, SimpleNamespace(tool_calls=[native_call("notebook_show", uid="show"), native_call("finish_noting", {"reason": "done"}, "finish")]), messages, "test")
        assert len([row for row in messages if row["role"] == "tool"]) == 2
        assert all(json.loads(row["content"])["error"]["code"] == "invalid_argument" for row in messages if row["role"] == "tool")
        assert not child._secretary_noting_terminal_action_done
        assert json.loads(child._invoke_tool("finish_noting", {"reason": "done"}, "test"))["status"] == "end_requested"
        refused = json.loads(child._invoke_tool("notebook_create", {}, "test"))
        assert refused["error"]["code"] == "state_conflict"
        assert child._noting_notebook_store.show() == before
        assert json.loads(child._invoke_tool("finish_noting", {"reason": "changed"}, "test"))["status"] == "end_requested"
        assert child._secretary_noting_termination["reason"] == "done"
    finally:
        child.close()


def test_ordinary_child_never_inherits_maintenance_permission(runtime):
    parent, _db, _config, _state = runtime
    child = bound_child(parent)
    try:
        child._secretary_noting_child = False
        child._secretary_noting_profile = None
        apply_cache_parity_from_parent(child, parent, fork_tag="delegate")
        assert not MAINTENANCE & child.valid_tool_names
        for name in MAINTENANCE:
            assert "disabled for this runtime" in child._invoke_tool(name, {"reason": "forged"}, "test")
    finally:
        child.close()


def test_global_and_local_switches_and_stale_restore_preserve_ownership(runtime):
    parent, db, config, state = runtime
    on_tools = copy.deepcopy(parent.tools)
    on_root = state["sent"][-1]["messages"][0]
    db.notebook_set_local_enabled(parent._secretary_conversation_ref, False)
    surface._turn(parent, "local off")
    assert parent.tools == on_tools and state["sent"][-1]["messages"][0] == on_root
    config.write_text("noting:\n  enabled: false\n", encoding="utf-8")
    surface._turn(parent, "global off")
    assert not MAINTENANCE & surface._names(parent.tools)
    assert "conversation_history" in surface._names(parent.tools)
    config.write_text("noting:\n  enabled: true\n", encoding="utf-8")
    # Force a stale pin lacking the two tools, using the native persistence owner.
    parent.tools = [tool for tool in on_tools if tool["function"]["name"] not in MAINTENANCE]
    from tools.mcp_tool_agent import persist_agent_tool_names
    persist_agent_tool_names(parent)
    history = db.get_messages_as_conversation(parent.session_id)
    cold = surface._agent(db, existing=False, selected=["todo"])
    cold._cached_system_prompt = None
    cold._disable_streaming = True
    try:
        result = cold.run_conversation(user_message="cold resumed", conversation_history=history, title_user_message="")
        assert result["completed"]
        assert MAINTENANCE <= surface._names(state["sent"][-1]["tools"])
        assert not MAINTENANCE & cold.valid_tool_names
        for name in MAINTENANCE:
            assert "disabled for this runtime" in cold._invoke_tool(name, {"reason": "forged"}, "test")
    finally:
        cold.close()


@pytest.mark.parametrize("identity", ["main", "noting"])
def test_registry_entry_uses_standard_refusal_before_dispatch(runtime, monkeypatch, identity):
    from tools.secretary_dispatch import scoped_registry_dispatch
    parent, db, _config, _state = runtime
    agent = parent if identity == "main" else bound_child(parent)
    recorder = MagicMock(return_value='{"success": true}')
    monkeypatch.setattr("model_tools.handle_function_call", recorder)
    names = sorted(MAINTENANCE) if identity == "main" else DENIED_CHILD
    before = db.notebook_current(parent._secretary_conversation_ref)
    try:
        for name in names:
            assert_permission_error(scoped_registry_dispatch(agent, name, {}, "test"), agent, name)
        recorder.assert_not_called()
        assert db.notebook_current(parent._secretary_conversation_ref) == before
        assert json.loads(scoped_registry_dispatch(agent, "conversation_history", {}, "test"))["success"]
        recorder.assert_called_once()
    finally:
        if agent is not parent:
            agent.close()


@pytest.mark.parametrize("executor", [execute_tool_calls_sequential, execute_tool_calls_concurrent])
@pytest.mark.parametrize("identity,name", [("main", "notebook_create"), ("noting", "tool_call"), ("noting", "tool_search")])
def test_permission_post_hook_diagnostic_remains_string(runtime, monkeypatch, executor, identity, name):
    parent, _db, _config, _state = runtime
    agent = parent if identity == "main" else bound_child(parent)
    observed = []
    monkeypatch.setattr("agent.tool_executor._ToolCallRef.emit_post",
                        lambda self, agent, result, **outcome: observed.append(outcome))
    try:
        messages = [{"role": "user", "content": "go"}]
        executor(agent, SimpleNamespace(tool_calls=[native_call(name, {"name": "notebook_show", "arguments": {}})]), messages, "test")
        assert_permission_error(messages[-1]["content"], agent, name)
        assert len(observed) == 1
        assert observed[0]["error_type"] == "noting_dispatch_blocked"
        assert observed[0]["error_message"] == noting_dispatch_block(agent, name)
        assert isinstance(observed[0]["error_message"], str)
    finally:
        if agent is not parent:
            agent.close()


def test_main_unknown_mixture_keeps_native_error_shape(runtime):
    parent, _db, _config, state = runtime
    state["script"] = [[call("unavailable_unique_tool_xyz", uid="unknown"),
                        call("conversation_history", {"mode": "read", "limit": 1}, "legal")], None]
    surface._turn(parent, "read the evidence")
    rows = tool_rows(state["sent"][-1])
    assert "does not exist" in next(row["content"] for row in rows if row["tool_call_id"] == "unknown")
    assert json.loads(next(row["content"] for row in rows if row["tool_call_id"] == "legal"))["success"]


@pytest.mark.parametrize("block_type", ["scope", "plugin"])
def test_generic_scope_and_plugin_errors_keep_existing_shape(runtime, monkeypatch, block_type):
    from agent.tool_executor import _run_agent_tool_execution_middleware
    parent, _db, _config, _state = runtime
    blocked = "ordinary generic refusal"
    if block_type == "plugin":
        monkeypatch.setattr("agent.tool_executor._pre_tool_block", lambda agent, ref: (blocked, ref.args))
    executed = MagicMock()
    result = _run_agent_tool_execution_middleware(
        parent, function_name="conversation_history", function_args={}, effective_task_id="test",
        tool_call_id="generic", execute=executed, scope_block=blocked if block_type == "scope" else None,
    )
    assert json.loads(result.result) == {"error": blocked}
    executed.assert_not_called()


@pytest.mark.parametrize("executor", [execute_tool_calls_sequential, execute_tool_calls_concurrent])
@pytest.mark.parametrize("name", ["tool_search", "tool_call"])
def test_noting_wrapper_refusal_precedes_argument_parsing(runtime, executor, name):
    parent, _db, _config, _state = runtime
    child = bound_child(parent)
    tool = native_call(name)
    tool.function.arguments = "{malformed"
    before = child._noting_notebook_store.show()
    try:
        messages = [{"role": "user", "content": "go"}]
        executor(child, SimpleNamespace(tool_calls=[tool]), messages, "test")
        assert_permission_error(messages[-1]["content"], child, name)
        assert child._noting_notebook_store.show() == before
    finally:
        child.close()


@pytest.mark.parametrize("name", sorted(MAINTENANCE))
def test_raw_registry_cannot_authorize_main_from_arguments(runtime, name):
    from tools.registry import registry
    from tools.secretary_dispatch import secretary_surface_scope
    parent, db, _config, _state = runtime
    before = db.notebook_current(parent._secretary_conversation_ref)
    forged = {"_secretary_noting_child": True, "reason": "claim Noting"}
    assert_permission_error(registry.dispatch(name, forged, agent=parent), parent, name)
    with secretary_surface_scope(parent):
        assert_permission_error(registry.dispatch(name, forged), parent, name)
    assert db.notebook_current(parent._secretary_conversation_ref) == before


def test_raw_dispatch_scoped_noting_rejects_other_tools_and_old_alias(runtime):
    from tools.registry import registry
    from tools.secretary_dispatch import secretary_surface_scope
    import model_tools
    parent, _db, _config, _state = runtime
    child = bound_child(parent)
    try:
        with secretary_surface_scope(child):
            for name in ("terminal", "scheduler", "tool_call", "tool_search", "notebook_maintain"):
                assert_permission_error(registry.dispatch(name, {}), child, name)
                assert_permission_error(model_tools.handle_function_call(name, {}), child, name)
        assert json.loads(parent._invoke_tool("notebook_maintain", {}, "old"))["error"]["code"] == "legacy_tool_removed"
    finally:
        child.close()


def _notebook_item_rows(db):
    return [tuple(row) for row in db._read_all("SELECT * FROM secretary_notebook_item ORDER BY id")]


def _create_notebook_args(parent):
    user_uid = next(row["message_uid"] for row in parent._session_messages if row["role"] == "user")
    return {"entry_type": "matter", "fields": {
        "description": "Send the report after review", "completion_condition": "Report accepted"},
        "source_message_uids": [user_uid], "source_description": "The user stated the report responsibility."}


@pytest.mark.parametrize("path", ["invoke", "loop"])
@pytest.mark.parametrize("field", ["entry_type", "fields", "done", "relations", "source_message_uids"])
def test_create_explicit_nonnullable_null_has_no_working_or_item_writes(runtime, path, field):
    parent, db, _config, state = runtime
    child = bound_child(parent)
    args = {**_create_notebook_args(parent), field: None}
    before, items = child._noting_notebook_store.snapshot_state(), _notebook_item_rows(db)
    try:
        if path == "invoke":
            result = json.loads(child._invoke_tool("notebook_create", args, "null-create"))
        else:
            state["script"] = [[call("notebook_create", args, "null-create")], None]
            surface._turn(child, "Validate the report entry without changing invalid input.")
            result = next(json.loads(row["content"]) for row in tool_rows(state["sent"][-1])
                          if row["tool_call_id"] == "null-create")
        assert result["success"] is False
        assert result["error"]["code"] == "invalid_argument"
        assert result["error"]["field"] == field
        assert "null" in result["error"]["message"]
        assert result["error"]["next_action"]
        assert child._noting_notebook_store.snapshot_state() == before
        assert _notebook_item_rows(db) == items
    finally:
        child.close()


@pytest.mark.parametrize("field", ["entry_id", "fields", "done", "relations", "source_message_uids"])
def test_update_explicit_nonnullable_null_preserves_existing_entry(runtime, field):
    parent, db, _config, _state = runtime
    child = bound_child(parent)
    try:
        made = json.loads(child._invoke_tool("notebook_create", _create_notebook_args(parent), "create"))
        assert made["success"]
        entry_id = made["entry"]["entry_id"]
        before, items = child._noting_notebook_store.snapshot_state(), _notebook_item_rows(db)
        result = json.loads(child._invoke_tool("notebook_update", {"entry_id": entry_id, field: None}, "null-update"))
        assert result["success"] is False
        assert result["error"]["code"] == "invalid_argument" and result["error"]["field"] == field
        assert child._noting_notebook_store.snapshot_state() == before
        assert _notebook_item_rows(db) == items
    finally:
        child.close()


def test_omitted_defaults_empty_relations_and_approved_null_clears_remain_legal(runtime):
    parent, db, _config, _state = runtime
    child = bound_child(parent)
    try:
        args = _create_notebook_args(parent)
        created = json.loads(child._invoke_tool("notebook_create", args, "default-create"))
        assert created["success"]
        assert created["entry"]["done"] is False and created["entry"]["relations"] == []
        assert "status" not in created["entry"]
        empty_relations = json.loads(child._invoke_tool("notebook_create", {**args, "relations": [],
            "fields": {**args["fields"], "blocker": None},
            "schedule_suggestion": None}, "empty-relations"))
        assert empty_relations["success"] and empty_relations["entry"]["relations"] == []
        assert empty_relations["entry"].get("schedule_suggestion") is None
        entry_id = created["entry"]["entry_id"]
        changed = json.loads(child._invoke_tool("notebook_update", {"entry_id": entry_id,
            "fields": {"blocker": "Awaiting review"}, "relations": [],
            "source_message_uids": args["source_message_uids"],
            "source_description": "The user stated the report responsibility.",
            "schedule_suggestion": {"content": "Review the report once feedback arrives.",
                                    "schedule": "after reviewer feedback"}}, "populate"))
        assert changed["success"]
        cleared = json.loads(child._invoke_tool("notebook_update", {"entry_id": entry_id,
            "fields": {"blocker": None}, "relations": [],
            "source_message_uids": args["source_message_uids"], "schedule_suggestion": None,
            "source_description": "The user stated the report responsibility."}, "clear"))
        assert cleared["success"] and cleared["changed"]
        entry = cleared["entry"]
        assert "blocker" not in entry["fields"]
        assert entry["relations"] == [] and entry.get("schedule_suggestion") is None
        assert entry["provenance"] == [args["source_message_uids"]]
    finally:
        child.close()


@pytest.mark.parametrize("name,args,field", [
    ("notebook_archive", {"entry_id": None, "reason": "No longer needed"}, "entry_id"),
    ("notebook_archive", {"entry_id": "unselected", "reason": None}, "reason"),
    ("finish_noting", {"reason": None}, "reason"),
    ("notebook_create", {"evidence_time": None}, "evidence_time"),
    ("conversation_history", {"mode": "read", "roles": None}, "roles"),
    ("notebook_show", {"entry_id": None}, "arguments"),
])
def test_existing_null_reason_readonly_and_read_selectors_do_not_mutate(runtime, name, args, field):
    parent, db, _config, _state = runtime
    child = bound_child(parent)
    before, items = child._noting_notebook_store.snapshot_state(), _notebook_item_rows(db)
    try:
        result = json.loads(child._invoke_tool(name, args, "null-existing"))
        assert result["success"] is False
        assert result["error"]["code"] == "invalid_argument" and result["error"]["field"] == field
        assert not child._secretary_noting_terminal_action_done
        assert child._noting_notebook_store.snapshot_state() == before
        assert _notebook_item_rows(db) == items
    finally:
        child.close()


@pytest.mark.parametrize("field", ["done", "relations"])
def test_empty_string_cannot_replace_a_rejected_null(runtime, field):
    parent, db, _config, _state = runtime
    child = bound_child(parent)
    before, items = child._noting_notebook_store.snapshot_state(), _notebook_item_rows(db)
    try:
        result = json.loads(child._invoke_tool("notebook_create", {
            **_create_notebook_args(parent), field: ""}, "empty-substitute"))
        assert result["success"] is False
        assert result["error"]["code"] == "invalid_argument" and result["error"]["field"] == field
        assert child._noting_notebook_store.snapshot_state() == before
        assert _notebook_item_rows(db) == items
    finally:
        child.close()


@pytest.mark.parametrize("path", ["invoke", "loop"])
@pytest.mark.parametrize("name", ["notebook_create", "notebook_update"])
def test_retired_status_is_not_a_current_model_write_alias(runtime, path, name):
    parent, db, _config, state = runtime
    child = bound_child(parent)
    try:
        made = json.loads(child._invoke_tool("notebook_create", _create_notebook_args(parent), "original"))
        assert made["success"] and made["entry"]["done"] is False
        args = (_create_notebook_args(parent) if name == "notebook_create" else {"entry_id": made["entry"]["entry_id"]})
        args["status"] = "completed"
        before, items = child._noting_notebook_store.snapshot_state(), _notebook_item_rows(db)
        if path == "invoke":
            result = json.loads(child._invoke_tool(name, args, "retired-status"))
        else:
            state["script"] = [[call(name, args, "retired-status")], None]
            surface._turn(child, "Use only the current Notebook input contract.")
            result = next(json.loads(row["content"]) for row in tool_rows(state["sent"][-1])
                          if row["tool_call_id"] == "retired-status")
        assert not result["success"] and result["error"]["code"] == "invalid_argument"
        assert result["error"]["field"] == "status"
        assert child._noting_notebook_store.snapshot_state() == before and _notebook_item_rows(db) == items
    finally:
        child.close()
