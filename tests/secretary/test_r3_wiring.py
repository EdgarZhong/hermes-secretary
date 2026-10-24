"""C9-S actual registration, native dispatch, Main restoration and persistence seams."""

import copy
import json
from types import SimpleNamespace

import pytest

from tests.secretary.test_noting_surface import _agent, _names, _requests, _turn, runtime as _runtime


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    yield from _runtime.__wrapped__(tmp_path, monkeypatch)


def call(name, args=None, ident="c1"):
    return SimpleNamespace(id=ident, type="function", function=SimpleNamespace(name=name, arguments=json.dumps(args or {})))


def test_real_catalog_registers_only_current_contract(runtime):
    import model_tools
    from tools.registry import registry
    from secretary.noting_tools import noting_tool_schemas
    from tools.secretary_dispatch import RETIRED_SECRETARY_TOOLS
    from toolsets import resolve_toolset
    for schema in noting_tool_schemas():
        schema = schema.get("function", schema)
        assert registry.get_schema(schema["name"]) == schema
    assert "scheduler" in resolve_toolset("scheduler")
    assert "conversation_history" in resolve_toolset("conversation_history")
    for name in RETIRED_SECRETARY_TOOLS:
        assert registry.get_schema(name) is None
        assert json.loads(registry.dispatch(name, {}))["error"]["code"] == "legacy_tool_removed"
        assert json.loads(model_tools.handle_function_call(name, {}))["error"]["code"] == "legacy_tool_removed"


@pytest.mark.parametrize("executor", ["execute_tool_calls_sequential", "execute_tool_calls_concurrent", "execute_tool_calls_segmented"])
def test_actual_batch_rejects_mixed_finish_before_any_tool_or_hook(runtime, monkeypatch, executor):
    from agent import tool_executor
    db, _ = runtime
    agent = _agent(db)
    agent._secretary_noting_child = True
    agent._secretary_noting_profile = "NOTING"
    effects = []
    monkeypatch.setattr("secretary.noting_tools.notebook_create", lambda *a: effects.append("mutation"))
    monkeypatch.setattr("secretary.noting_tools.finish_noting", lambda *a: effects.append("finish"))
    monkeypatch.setattr("agent.tool_executor._pre_tool_block", lambda *a: effects.append("hook"))
    calls = [call("notebook_create", {"action": "archive"}), call("finish_noting", {"reason": "done"}, "c2")]
    messages = [{"role": "assistant", "tool_calls": [{"id": c.id, "type": "function", "function": {"name": c.function.name, "arguments": c.function.arguments}} for c in calls]}]
    try:
        getattr(tool_executor, executor)(agent, SimpleNamespace(tool_calls=calls), messages, "batch")
        results = [m for m in messages if m.get("role") == "tool"]
        assert len(results) == 2 and effects == []
        assert all(json.loads(m["content"])["error"]["code"] == "invalid_argument" for m in results)
        assert results[0]["content"] == results[1]["content"]
    finally:
        agent.close()


@pytest.mark.parametrize("concurrent", [False, True])
def test_actual_main_dispatch_history_notebook_and_scheduler(runtime, concurrent):
    from agent.tool_executor import execute_tool_calls_concurrent, execute_tool_calls_sequential
    db, config = runtime
    config.write_text("noting:\n  enabled: false\nscheduler:\n  enabled: true\n")
    agent = _agent(db, selected=["session_search"])
    db.append_message(agent.session_id, "user", "canonical evidence", message_uid="evidence")
    messages = []
    tools = [call("conversation_history", {"mode": "read", "limit": 10}),
             call("scheduler", {"action": "list"}, "c2")]
    try:
        fn = execute_tool_calls_concurrent if concurrent else execute_tool_calls_sequential
        fn(agent, SimpleNamespace(tool_calls=tools), messages, "actual")
        results = [json.loads(m["content"]) for m in messages if m.get("role") == "tool"]
        assert len(results) == 2 and all(r["success"] for r in results)
        assert "canonical evidence" in json.dumps(results[0])
        from agent.tool_executor import _tool_search_scoped_names
        assert "session_search" in _tool_search_scoped_names(agent) | agent.valid_tool_names
        assert "notebook_show" not in _names(agent.tools)
        assert agent._secretary_scheduler_enabled is True
    finally:
        agent.close()


@pytest.mark.parametrize("cold", [False, True])
def test_scheduler_independent_switch_updates_actual_root_schemas_and_cache(runtime, cold):
    from agent.system_prompt import HISTORY_SEARCH_GUIDANCE, SCHEDULER_GUIDANCE, SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE
    from gateway.run import GatewayRunner
    db, config = runtime
    agent = _agent(db, selected=["session_search"])
    try:
        seen = _requests(agent)
        _turn(agent)
        history = db.get_messages_as_conversation(agent.session_id)
        config.write_text("noting:\n  enabled: false\nscheduler:\n  enabled: false\n")
        if cold:
            agent.close()
            agent = _agent(db, existing=False, selected=["session_search"])
            agent._cached_system_prompt = None
            seen = _requests(agent)
            result = agent.run_conversation(user_message="restored", conversation_history=history, title_user_message="")
            assert result["completed"]
        else:
            _turn(agent, "next turn")
        root = seen[-1]["messages"][0]["content"]
        assert root.count(HISTORY_SEARCH_GUIDANCE) == 1
        assert SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE not in root and SCHEDULER_GUIDANCE not in root
        assert "conversation_history" in _names(seen[-1]["tools"])
        assert not {"notebook_show", "scheduler"}.intersection(_names(seen[-1]["tools"]))
        assert (agent._secretary_main_read_eligible, agent._secretary_notebook_read_enabled,
                agent._secretary_scheduler_enabled) == (True, False, False)
        off = GatewayRunner._extract_cache_busting_config({"scheduler": {"enabled": False}})
        invalid = GatewayRunner._extract_cache_busting_config({"scheduler": {"enabled": "false"}})
        assert off["scheduler.enabled"] is False and invalid["scheduler.enabled"] is False
    finally:
        agent.close()


@pytest.mark.parametrize("noting,scheduler", [(True, True), (True, False), (False, True), (False, False)])
def test_actual_root_preserves_full_soul_and_independent_prompt_modules(runtime, noting, scheduler):
    from agent.prompt_builder import SESSION_SEARCH_GUIDANCE
    from agent.system_prompt import (
        HISTORY_SEARCH_GUIDANCE, NOTEBOOK_GUIDANCE, SCHEDULER_GUIDANCE,
        SECRETARY_ROLE_GUIDANCE, SECRETARY_TIME_GUIDANCE,
    )
    db, config = runtime
    config.write_text(f"noting:\n  enabled: {str(noting).lower()}\nscheduler:\n  enabled: {str(scheduler).lower()}\n")
    soul = "# SOUL\nLong-term private adviser.\n\nAnswer naturally and keep authorization explicit."
    (config.parent / "SOUL.md").write_text(soul)
    agent = _agent(db, selected=["session_search"], load_soul_identity=True)
    agent._cached_system_prompt = None
    try:
        seen = _requests(agent)
        _turn(agent)
        root = seen[0]["messages"][0]["content"]
        assert soul in root
        assert root.count(HISTORY_SEARCH_GUIDANCE) == 1
        for block in (SECRETARY_ROLE_GUIDANCE, NOTEBOOK_GUIDANCE, SECRETARY_TIME_GUIDANCE):
            assert root.count(block) == int(noting)
        assert root.count(SCHEDULER_GUIDANCE) == int(scheduler)
        assert SESSION_SEARCH_GUIDANCE not in root
        if not noting and not scheduler:
            from agent.system_prompt import _guidance_parts
            agent._secretary_main_read_eligible = False
            agent.valid_tool_names.add("session_search")
            native = "\n".join(filter(None, _guidance_parts(agent)))
            assert SESSION_SEARCH_GUIDANCE in native
            assert not any(block in native for block in (
                SECRETARY_ROLE_GUIDANCE, SCHEDULER_GUIDANCE, HISTORY_SEARCH_GUIDANCE))
    finally:
        agent.close()


def test_actual_native_session_flush_refreshes_admitted_instant_before_commit(runtime):
    from agent.session_persistence import _db_flush_write
    from secretary import reminders, schedules
    from secretary.scheduler_time import epoch_to_utc_iso
    import time
    db, _ = runtime
    agent = _agent(db)
    store = schedules.SchedulerStore(db, agent._secretary_conversation_ref, session_id=agent.session_id)
    now = time.time()
    created = store.create("actual native refresh", epoch_to_utc_iso(now - 10), "instant", now=now)
    sid = created["schedule"]["schedule_id"]
    claim = schedules.claim_due(db, sid, owner="wiring", now=now)
    receipt = reminders.admit_active_reminder(db, claim, session_id=agent.session_id, now=now)
    live = [{"role": "user", "content": receipt["resolved"]["text"], "timestamp": receipt["resolved"]["source_timestamp"]}]
    rows = copy.copy(live[0])
    # The final instant notice changes between ingress resolution and real native insertion.
    store.create("future coverage", epoch_to_utc_iso(now + 100), "instant", now=now)
    try:
        _db_flush_write(agent, [rows], live, live)
        stored = db.get_messages(agent.session_id)
        assert len(stored) == 1
        assert stored[0]["content"] == live[0]["content"]
        assert "no instant reminder" not in stored[0]["content"].lower()
        assert reminders.active_admission_witness(live[0]["content"]).durable(db)
    finally:
        agent.close()


@pytest.mark.parametrize("aggregate", [False, True])
def test_noting_budget_feedback_is_authorized_and_honest(runtime, aggregate):
    from tools.budget_config import BudgetConfig
    from tools.tool_result_storage import enforce_turn_budget, maybe_persist_tool_result
    budget = BudgetConfig(default_result_size=100, turn_budget=100, preview_size=20)
    text = "original evidence " * 100
    if aggregate:
        rows = [{"role": "tool", "tool_call_id": "large", "content": text}]
        enforce_turn_budget(rows, config=budget, noting=True)
        restricted = rows[0]["content"]
    else:
        restricted = maybe_persist_tool_result(text, "conversation_history", "large", config=budget, noting=True)
    from tools.session_history_tool import NOTING_HISTORY_OVERSIZE_GUIDANCE
    assert NOTING_HISTORY_OVERSIZE_GUIDANCE in restricted
    assert "read_file" not in restricted and "execute_code" not in restricted and "terminal" not in restricted
    native = maybe_persist_tool_result(text, "conversation_history", "native", config=budget)
    assert "read_file" in native and "execute_code" in native


@pytest.mark.parametrize("concurrent", [False, True])
def test_bound_child_uses_all_four_tools_through_actual_dispatch(runtime, concurrent):
    from agent.tool_executor import execute_tool_calls_concurrent, execute_tool_calls_sequential
    from secretary.noting_child import build_noting_child
    from secretary.noting_tools import initialize_notebook_work
    db, _ = runtime
    parent = _agent(db)
    db.append_message(parent.session_id, "user", "Visit after dates agreed", message_uid="m1")
    child = build_noting_child(parent, runtime_profile="NOTING", parent_conversation_ref=parent._secretary_conversation_ref)
    child._secretary_noting_anchor_uid = "m1"
    admission = db.noting_admit(parent._secretary_conversation_ref, "m1", kind="manual")
    db.noting_child_register(admission, child_session_id=child.session_id, profile=None)
    initialize_notebook_work(child, trigger_type="manual")
    fn = execute_tool_calls_concurrent if concurrent else execute_tool_calls_sequential
    messages = []
    try:
        args = {"entry_type": "matter", "fields": {"description": "Plan visit", "completion_condition": "Dates agreed"},
                "source_message_uids": ["m1"]}
        for number, (name, args) in enumerate([
            ("conversation_history", {"mode": "read", "limit": 5}),
            ("notebook_create", args), ("notebook_show", {}), ("finish_noting", {"reason": "Indexed visit"}),
        ]):
            fn(child, SimpleNamespace(tool_calls=[call(name, args, f"child{number}")]), messages, "child")
            result = json.loads([m for m in messages if m.get("role") == "tool"][-1]["content"])
            assert result["success"], result
            if name == "notebook_show":
                assert result["view_kind"] == "working" and "Plan visit" in json.dumps(result)
            if name == "finish_noting":
                assert result["status"] == "end_requested" and "committed" not in result
        assert db.notebook_current(parent._secretary_conversation_ref) is None
    finally:
        child.close()
        parent.close()


@pytest.mark.parametrize("aggregate", [False, True])
def test_actual_dispatch_selects_noting_budget_feedback_from_runtime(runtime, monkeypatch, aggregate):
    from agent.tool_executor import execute_tool_calls_sequential
    from tools.budget_config import BudgetConfig
    db, _ = runtime
    agent = _agent(db)
    agent._secretary_noting_child = True
    agent._secretary_noting_profile = "NOTING"
    budget = BudgetConfig(default_result_size=10000 if aggregate else 100, turn_budget=100, preview_size=20)
    monkeypatch.setattr("agent.tool_executor._budget_for_agent", lambda _agent: budget)
    monkeypatch.setattr("tools.session_history_tool.conversation_history", lambda *a, **k: "evidence " * 300)
    messages = []
    try:
        execute_tool_calls_sequential(agent, SimpleNamespace(tool_calls=[call("conversation_history")]), messages, "budget")
        content = [m for m in messages if m.get("role") == "tool"][-1]["content"]
        from tools.session_history_tool import NOTING_HISTORY_OVERSIZE_GUIDANCE
        assert NOTING_HISTORY_OVERSIZE_GUIDANCE in content
        denied = json.loads(agent._invoke_tool("read_file", {"path": "synthetic-only"}, "denied-file"))
        assert "Noting runtime denied non-whitelisted tool: read_file" in denied["error"]["message"]
        assert "read_file" not in content and "execute_code" not in content
    finally:
        agent.close()


@pytest.mark.parametrize("name", ["session_history", "noting_memo", "notebook_mutate", "notebook_edit", "notebook_manage", "notebook_schedule", "compact_parent"])
@pytest.mark.parametrize("executor", ["execute_tool_calls_sequential", "execute_tool_calls_concurrent"])
def test_actual_restored_legacy_call_has_explicit_nonexecuting_result(runtime, name, executor):
    from agent import tool_executor
    db, _ = runtime
    agent = _agent(db)
    messages = []
    try:
        getattr(tool_executor, executor)(agent, SimpleNamespace(tool_calls=[call(name)]), messages, "legacy")
        result = json.loads(messages[-1]["content"])
        assert result["error"]["code"] == "legacy_tool_removed"
        assert json.loads(agent._invoke_tool(name, {}, "direct-legacy"))["error"]["code"] == "legacy_tool_removed"
        assert db.notebook_current(agent._secretary_conversation_ref) is None
    finally:
        agent.close()


def test_actual_catalog_does_not_restore_disabled_or_noting_only_capabilities(runtime):
    db, config = runtime
    config.write_text("noting:\n  enabled: false\nscheduler:\n  enabled: false\n")
    agent = _agent(db, selected=["notebook", "scheduler", "noting", "session_search"])
    try:
        result = json.loads(agent._invoke_tool("tool_describe", {
            "names": ["session_search", "scheduler", "notebook_show", "notebook_create", "finish_noting"]}, "catalog"))
        rendered = json.dumps(result)
        assert "session_search" in result.get("tools", {})
        assert not {"scheduler", "notebook_show", "notebook_create", "finish_noting"}.intersection(result.get("tools", {}))
        assert "legacy_tool_removed" not in rendered
        bridge = next(tool for tool in agent.tools if tool["function"]["name"] == "tool_search")
        for name in ("scheduler", "notebook_show", "notebook_create", "finish_noting"):
            assert f"- {name}:" not in bridge["function"]["description"]
    finally:
        agent.close()


@pytest.mark.parametrize("other", ["unknown_tool", "notebook_edit", "notebook_create"])
def test_real_turn_rejects_original_finish_batch_before_native_filtering(runtime, monkeypatch, other):
    from tests.secretary.test_noting_child import mock_response
    db, _ = runtime
    agent = _agent(db)
    agent._secretary_noting_child = True
    agent._secretary_noting_profile = "NOTING"
    agent.valid_tool_names |= {"finish_noting", "notebook_create"}
    agent._secretary_noting_parent_tools = copy.deepcopy(agent.tools)
    effects = []
    monkeypatch.setattr("secretary.noting_tools.finish_noting", lambda *a: effects.append("finish"))
    monkeypatch.setattr("secretary.noting_tools.notebook_create", lambda *a: effects.append("write"))
    def response(index):
        return mock_response(None, "tool_calls", [call("finish_noting", {"reason": "done"}), call(other, {}, "c2")]) if index == 1 else mock_response("stopped")
    seen = _requests(agent, response)
    try:
        _turn(agent)
        results = [row for row in seen[-1]["messages"] if row["role"] == "tool"]
        assert len(results) == 2 and effects == []
        assert all(json.loads(row["content"])["error"]["code"] == "invalid_argument" for row in results)
        assert results[0]["content"] == results[1]["content"]
    finally:
        agent.close()


@pytest.mark.parametrize("legacy_name", ["session_history", "Session-History", "notebook_mutate", "Notebook-Mutate"])
def test_real_turn_does_not_fuzzy_execute_retired_history_name(runtime, monkeypatch, legacy_name):
    from tests.secretary.test_noting_child import mock_response
    db, _ = runtime
    agent = _agent(db)
    effects = []
    monkeypatch.setattr("tools.session_history_tool.conversation_history", lambda *a, **k: effects.append("history"))
    def response(index):
        return mock_response(None, "tool_calls", [call(legacy_name, {"mode": "read"})]) if index == 1 else mock_response("corrected")
    seen = _requests(agent, response)
    try:
        _turn(agent)
        assert effects == []
        result = next(row for row in seen[-1]["messages"] if row["role"] == "tool")
        assert json.loads(result["content"])["error"]["code"] == "legacy_tool_removed"
        assert agent._repair_tool_call(legacy_name) is None
    finally:
        agent.close()


def test_actual_native_session_flush_rejection_does_not_publish_live_or_consume(runtime, monkeypatch):
    import time
    from agent.session_persistence import _db_flush_write
    from secretary import reminders, schedules
    from secretary.scheduler_time import epoch_to_utc_iso
    db, _ = runtime
    agent = _agent(db)
    store = schedules.SchedulerStore(db, agent._secretary_conversation_ref, session_id=agent.session_id)
    now = time.time()
    sid = store.create("rollback carrier", epoch_to_utc_iso(now - 1), "instant", now=now)["schedule"]["schedule_id"]
    claim = schedules.claim_due(db, sid, owner="rollback", now=now)
    receipt = reminders.admit_active_reminder(db, claim, session_id=agent.session_id, now=now)
    original_text = receipt["resolved"]["text"]
    live = [{"role": "user", "content": original_text, "timestamp": receipt["resolved"]["source_timestamp"]}]
    store.create("new later coverage", epoch_to_utc_iso(now + 100), "instant", now=now)
    append = db.append_messages_batch
    def reject(*args, **kwargs):
        bind = kwargs["before_commit"]
        def before(conn, sid, rows):
            bind(conn, sid, rows)
            raise OSError("controlled native transaction rejection")
        return append(*args, **{**kwargs, "before_commit": before})
    monkeypatch.setattr(db, "append_messages_batch", reject)
    try:
        with pytest.raises(OSError, match="controlled native"):
            _db_flush_write(agent, [dict(live[0])], live, live)
        assert db.get_messages(agent.session_id) == []
        assert live[0]["content"] is original_text
        assert not reminders.active_admission_witness(original_text).committed
        assert db._read_one("SELECT state FROM secretary_schedule_registry WHERE schedule_id=?", (sid,))[0] == "pending"
    finally:
        agent.close()


def test_auxiliary_native_session_search_is_preserved(runtime, monkeypatch):
    from agent.tool_executor import _tool_search_scoped_names
    db, _ = runtime
    db.create_session("native-cron", source="cron")
    agent = _agent(db, session_id="native-cron", existing=False, selected=["session_search"])
    calls = []
    def native_search(**kwargs):
        calls.append(kwargs)
        return json.dumps({"success": True, "native": True})
    monkeypatch.setattr("tools.session_search_tool.session_search", native_search)
    try:
        assert "session_search" in _tool_search_scoped_names(agent) | agent.valid_tool_names
        assert not {"conversation_history", "notebook_show", "scheduler"}.intersection(_names(agent.tools))
        result = json.loads(agent._invoke_tool("session_search", {"query": "physical execution"}, "native"))
        assert result["native"] is True and len(calls) == 1
    finally:
        agent.close()


@pytest.mark.parametrize("local", [False, True])
@pytest.mark.parametrize("noting,scheduler", [(True, True), (False, True), (True, False), (False, False)])
def test_formal_tui_default_surface_keeps_main_tools_direct(runtime, monkeypatch, noting, scheduler, local):
    """Actual TUI assembly exposes Main tools directly and keeps native tools deferred."""
    import model_tools
    from tui_gateway import server
    from hermes_cli.cli_secretary_commands import noting_command
    from tools.secretary_dispatch import filter_tool_definitions
    from agent.tool_executor import _tool_search_scoped_names
    from secretary.scheduler_time import epoch_to_utc_iso
    import time

    db, config = runtime
    config.write_text(f"noting:\n  enabled: {str(noting).lower()}\nscheduler:\n  enabled: {str(scheduler).lower()}\n")
    monkeypatch.setattr(server, "_resolve_agent_model_runtime", lambda *a: ("test/model", {
        "provider": "custom", "api_key": "test-key", "base_url": "https://test.invalid/v1",
        "api_mode": "chat_completions"}))
    monkeypatch.setenv("HERMES_IGNORE_RULES", "1")
    db.create_session("f09-main", source="cli")
    # Exercise the actual TUI factory and its default toolset loader; do not use _agent.
    agent = server._make_agent("f09-ui", "f09-main", session_db=db, platform_override="cli")
    agent._disable_streaming = True
    agent.compression_enabled = False
    agent.save_trajectories = False
    agent._skip_mcp_refresh = True
    ref = agent._secretary_conversation_ref
    if not local:
        if noting:
            assert "is off" in noting_command(db, "f09-main", "off").output
        else:
            db.notebook_set_local_enabled(ref, False)
    try:
        raw = model_tools.get_tool_definitions(enabled_toolsets=agent.enabled_toolsets,
            disabled_toolsets=agent.disabled_toolsets, quiet_mode=True, skip_tool_search_assembly=True)
        # This reproduces the real default bundle: runtime additions are absent from the native raw list.
        assert not {"scheduler", "notebook_show"}.intersection(_names(raw))
        raw_before = copy.deepcopy(raw)
        composed = filter_tool_definitions(raw, agent)
        assert composed == filter_tool_definitions(composed, agent)
        assert _names(composed) == (_names(raw) | {"conversation_history"}
            | ({"scheduler"} if scheduler else set()) | ({"notebook_show", "notebook_create", "notebook_update", "notebook_archive", "finish_noting"} if noting else set()))
        assert len(composed) == len(_names(composed))
        for schema in composed:
            if schema["function"]["name"] in {"scheduler", "notebook_show"}:
                # The catalog owns its added Schema, never the owner/global cached dict.
                schema["function"]["description"] = "private catalog mutation probe"
        from secretary.noting_surface import _read_schema
        assert _read_schema("scheduler")["description"] != "private catalog mutation probe"
        assert _read_schema("notebook_show")["description"] != "private catalog mutation probe"
        # No current runtime scope means exactly native behavior, with no injected capabilities.
        assert filter_tool_definitions(raw) is raw and raw == raw_before
        assert {"tool_search", "tool_describe", "tool_call", "conversation_history"} <= _names(agent.tools)
        assert ("scheduler" in _names(agent.tools)) is scheduler
        assert ("notebook_show" in _names(agent.tools)) is noting

        calls = [call("tool_describe", {"names": ["scheduler", "notebook_show"]}, "describe"),
                 call("tool_search", {"queries": ["scheduler", "deferred", "notebook"]}, "search")]
        if scheduler:
            calls.append(call("scheduler", {
                "action": "create", "content": "Synthetic Main reminder", "schedule": epoch_to_utc_iso(time.time() + 600),
                "delivery_mode": "deferred"}, "create"))
        if noting:
            calls.append(call("notebook_show", {}, "show"))
        responses = [SimpleNamespace(model="test/model", usage=None, choices=[SimpleNamespace(
            finish_reason="tool_calls", message=SimpleNamespace(content="", tool_calls=[c],
                reasoning=None, reasoning_content=None))]) for c in calls]
        responses.append(SimpleNamespace(model="test/model", usage=None, choices=[SimpleNamespace(
            finish_reason="stop", message=SimpleNamespace(content="Completed the actual catalog and registration probe.",
                tool_calls=None, reasoning=None, reasoning_content=None))]))
        requests = _requests(agent, lambda n: responses[n - 1])
        result = agent.run_conversation("Use the available catalog to register a synthetic deferred reminder.", title_user_message="")
        assert result["completed"], result
        tool_rows = {row["tool_call_id"]: json.loads(row["content"]) for row in result["messages"] if row.get("role") == "tool"}
        described = tool_rows["describe"]
        main_names = {"scheduler", "notebook_show"}
        assert not main_names.intersection(described["tools"])
        expected_direct = ({"scheduler"} if scheduler else set()) | ({"notebook_show"} if noting else set())
        assert set(described.get("errors", {})) == expected_direct
        assert all("directly-listed" in error for error in described.get("errors", {}).values())
        assert set(described.get("not_found", [])) == main_names - expected_direct
        assert not main_names.intersection(tool_rows["search"]["tools"])
        assert not main_names.intersection(_tool_search_scoped_names(agent))
        assert {"todo_list", "process_manage", "session_search", "desktop_project"} <= _tool_search_scoped_names(agent)
        for name, enabled in [("scheduler", scheduler), ("notebook_show", noting)]:
            if enabled:
                declaration = next(t["function"] for t in requests[0]["tools"] if t["function"]["name"] == name)
                assert declaration["parameters"] == _read_schema(name)["parameters"]
        with db._read_ctx() as conn:
            rows = conn.execute("SELECT reminder_text,delivery_semantics FROM secretary_schedule_registry WHERE conversation_ref=?", (ref,)).fetchall()
        assert len(rows) == int(scheduler)
        if scheduler:
            assert rows[0]["reminder_text"] == "Synthetic Main reminder" and rows[0]["delivery_semantics"] == "system_reminder"
            assert tool_rows["create"]["success"] is True
        if noting:
            assert tool_rows["show"]["success"] is True and tool_rows["show"]["view_kind"] == "snapshot"
        assert len(requests) == len(responses)
        assert all(_names(request["tools"]) == _names(requests[0]["tools"]) for request in requests)
        assert db.notebook_local_enabled(ref) is local
        assert raw == raw_before
        if noting and scheduler:
            config.write_text("noting:\n  enabled: false\nscheduler:\n  enabled: false\n")
            _requests(agent)
            _turn(agent, "Continue after the owning feature configuration changed")
            disabled = json.loads(agent._invoke_tool("tool_describe", {
                "names": ["scheduler", "notebook_show"]}, "disabled-catalog"))
            assert not disabled["tools"] and set(disabled["not_found"]) == {"scheduler", "notebook_show"}
            assert not {"scheduler", "notebook_show"}.intersection(_tool_search_scoped_names(agent))
            blocked = json.loads(agent._invoke_tool("tool_call", {"calls": [{"name": "scheduler", "arguments": {
                "action": "create", "content": "must not register", "schedule": "in 1h", "delivery_mode": "deferred"}}]}, "disabled-call"))
            assert "not available" in str(blocked)
            assert db._read_one("SELECT COUNT(*) FROM secretary_schedule_registry WHERE conversation_ref=?", (ref,))[0] == 1
    finally:
        agent.close()


def test_main_direct_tools_do_not_leak_into_native_cached_surface(runtime):
    import model_tools
    from tools.secretary_dispatch import secretary_surface_scope
    from tools.tool_search import ToolSearchConfig, assemble_tool_defs

    db, _ = runtime
    agent = _agent(db)
    selected = ["scheduler", "notebook", "todo"]
    try:
        native = model_tools.get_tool_definitions(enabled_toolsets=selected, quiet_mode=True)
        assert not {"scheduler", "notebook_show"}.intersection(_names(native))
        with secretary_surface_scope(agent):
            direct = model_tools.get_tool_definitions(enabled_toolsets=selected, quiet_mode=True)
            assert {"scheduler", "notebook_show"} <= _names(direct)
            raw = model_tools.get_tool_definitions(enabled_toolsets=selected, quiet_mode=True,
                                                   skip_tool_search_assembly=True)
            explicit_defer = ToolSearchConfig.from_raw({"defer": ["scheduler", "notebook_show", "todo_list"]})
            assert {"scheduler", "notebook_show"} <= _names(assemble_tool_defs(raw, config=explicit_defer).tool_defs)
        assert model_tools.get_tool_definitions(enabled_toolsets=selected, quiet_mode=True) == native
        child = SimpleNamespace(_secretary_noting_child=True, _secretary_main_read_eligible=True,
                                _secretary_scheduler_enabled=True, _secretary_notebook_read_enabled=True)
        with secretary_surface_scope(child):
            assert model_tools.get_tool_definitions(enabled_toolsets=selected, quiet_mode=True) == native
    finally:
        agent.close()
