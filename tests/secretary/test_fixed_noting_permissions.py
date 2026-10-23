"""Fixed advertised tools and task-bound dispatch through real Loop/SDK/DB paths."""

import copy
import hashlib
import json
from contextlib import contextmanager
from types import SimpleNamespace
from unittest.mock import MagicMock

import httpx
import pytest
from openai import OpenAI

from agent.cache_parity import apply_cache_parity_from_parent
from agent.tool_executor import execute_tool_calls_concurrent, execute_tool_calls_sequential
from secretary.noting_child import NOTING_ALLOWED_TOOL_NAMES, build_noting_child, run_noting_task
from secretary.noting_contract import FINISH_NOTING_SCHEMA, NOTEBOOK_MAINTAIN_SCHEMA
from secretary.noting_tools import initialize_notebook_work
from tests.secretary import test_noting_surface as surface

MAINTENANCE = {"notebook_maintain", "finish_noting"}
DENIED_CHILD = ["terminal", "scheduler", "tool_search", "tool_call", "delegate_task", "notebook_maintain_tool"]


def call(name, args=None, uid="call"):
    return {"id": uid, "type": "function", "function": {"name": name, "arguments": json.dumps(args or {})}}


def native_call(name, args=None, uid="call"):
    value = call(name, args, uid)
    value["function"] = SimpleNamespace(**value["function"])
    return SimpleNamespace(**value)


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    with contextmanager(surface.runtime.__wrapped__)(tmp_path, monkeypatch) as (db, config):
        state = {"sent": [], "script": []}

        def transport(request):
            payload = json.loads(request.content)
            state["sent"].append(payload)
            batch = state["script"].pop(0) if state["script"] else None
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


def test_schema_and_direct_catalog_are_fixed(runtime):
    from tools import tool_search
    from tools.secretary_dispatch import filter_tool_definitions, secretary_surface_scope
    parent, _db, _config, state = runtime
    expected = {schema["name"]: schema for schema in (NOTEBOOK_MAINTAIN_SCHEMA, FINISH_NOTING_SCHEMA)}
    frozen_hashes = {"notebook_maintain": "4fbaab4cec9b50d7ed87888ba1a3cebaf6453b438d7a3ae06c2d7171b2b2ad3d",
                     "finish_noting": "59b73e172fd24a3c704f85b84adce58075d58fd8f965e9334544d288e20f0267"}
    for schema in expected.values():
        digest = hashlib.sha256(json.dumps(schema, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
        assert digest == frozen_hashes[schema["name"]]
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
    state["script"] = [[call(name, {"reason": "claim Noting", "_secretary_noting_child": True})], None]
    surface._turn(parent, "continue normally")
    assert db.notebook_current(parent._secretary_conversation_ref) == before
    result = json.loads(tool_rows(state["sent"][-1])[-1]["content"])
    assert result["error"]["code"] == "scope_denied"
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
    state["script"] = [[call("notebook_maintain"), call("conversation_history", {"mode": "read", "limit": 1}, "history")], None]
    surface._turn(parent, "normal evidence read")
    rows = tool_rows(state["sent"][-1])
    assert any(row["tool_call_id"] == "history" and json.loads(row["content"])["success"] for row in rows)
    assert "notebook_maintain" not in seen


@pytest.mark.parametrize("executor", [execute_tool_calls_sequential, execute_tool_calls_concurrent])
@pytest.mark.parametrize("name", sorted(MAINTENANCE))
def test_main_batch_and_direct_invoke_cannot_execute(runtime, executor, name):
    parent, db, _config, _state = runtime
    before = db.notebook_current(parent._secretary_conversation_ref)
    messages = [{"role": "user", "content": "go"}]
    executor(parent, SimpleNamespace(tool_calls=[native_call(name, {"reason": "forged"})]), messages, "test")
    assert "disabled for this runtime" in messages[-1]["content"]
    for bypass in (False, True):
        result = parent._invoke_tool(name, {"reason": "forged"}, "test", pre_tool_block_checked=bypass)
        assert "disabled for this runtime" in result
    assert db.notebook_current(parent._secretary_conversation_ref) == before


@pytest.mark.parametrize("name", DENIED_CHILD)
def test_child_loop_refuses_every_non_whitelisted_name_without_repair(runtime, monkeypatch, name):
    parent, _db, _config, state = runtime
    child = bound_child(parent)
    before = child._noting_notebook_store.show()
    monkeypatch.setattr(child, "_repair_tool_call", MagicMock(side_effect=AssertionError("no repair")))
    state["script"] = [[call(name, {"name": "notebook_maintain", "arguments": {}})], None]
    try:
        surface._turn(child, "maintain")
        assert "denied non-whitelisted tool" in tool_rows(state["sent"][-1])[-1]["content"]
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
        assert "denied non-whitelisted tool" in messages[-1]["content"]
        assert "denied non-whitelisted tool" in child._invoke_tool(name, args, "test", pre_tool_block_checked=True)
    finally:
        child.close()


def test_real_runner_uses_all_four_tools_finishes_and_keeps_parent_prefix(runtime):
    parent, db, _config, state = runtime
    prefix = copy.deepcopy(parent._session_messages)
    anchor = prefix[-1]["message_uid"]
    user_uid = next(row["message_uid"] for row in prefix if row["role"] == "user")
    parent_request = copy.deepcopy(state["sent"][-1])
    state["sent"].clear()
    state["script"] = [
        [call("conversation_history", {"mode": "read", "limit": 2}, "read")],
        [call("notebook_show", {}, "show")],
        [call("notebook_maintain", {"action": "create", "entry_type": "matter", "fields": {
            "description": "send report", "completion_condition": "Report sent"}, "source_message_uids": [user_uid]}, "maintain")],
        [call("finish_noting", {"reason": "Indexed the report commitment."}, "finish")], None,
    ]
    admission = db.noting_admit(parent._secretary_conversation_ref, anchor, kind="manual")
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=parent._secretary_conversation_ref,
                             anchor_message_uid=anchor, trigger_type="manual", runtime_profile="NOTING",
                             task_instruction="Maintain the Notebook.")
    assert outcome.committed and outcome.termination["type"] == "finish_noting"
    assert db.notebook_current(parent._secretary_conversation_ref)["payload"]["work"][0]["fields"]["description"] == "send report"
    assert len(state["sent"]) == 5
    for payload in state["sent"]:
        assert payload["tools"] == parent_request["tools"]
        assert payload["messages"][:len(parent_request["messages"]) + 1] == [*parent_request["messages"], {"role": "assistant", "content": "done"}]
    all_rows = tool_rows(state["sent"][-1])
    assert {row["tool_call_id"] for row in all_rows} == {"read", "show", "maintain", "finish"}
    assert all(json.loads(row["content"])["success"] for row in all_rows)
    assert json.loads(all_rows[-1]["content"]) == {"success": True, "status": "end_requested"}


def test_child_loop_rejects_complete_finish_mixture_before_any_effect(runtime):
    parent, _db, _config, state = runtime
    child = bound_child(parent)
    user_uid = next(row["message_uid"] for row in parent._session_messages if row["role"] == "user")
    mutation = {"action": "create", "entry_type": "matter", "fields": {
        "description": "send report", "completion_condition": "Report sent"}, "source_message_uids": [user_uid]}
    state["script"] = [[call("notebook_maintain", mutation, "write"), call("finish_noting", {"reason": "mixed"}, "mixed")],
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
        refused = json.loads(child._invoke_tool("notebook_maintain", {"action": "create"}, "test"))
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
