"""Live capability/policy updates append durable system rows, preserving every old byte."""

import copy
import json

import pytest

from tests.secretary.test_cross_platform_prefix import (
    _new_agent, _requests, _schema, _wire_gateway, _wire_json,
    catalogs as _catalog_fixture, runtime as _runtime_fixture,
)


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    yield from _runtime_fixture.__wrapped__(tmp_path, monkeypatch)


@pytest.fixture
def catalogs(monkeypatch):
    return _catalog_fixture.__wrapped__(monkeypatch)


def _updates(messages):
    return [row for row in messages if row.get("display_kind") == "runtime_context"]


def _snapshot(messages):
    return _updates(messages)[-1]["display_metadata"]["runtime_context"]


@pytest.fixture
def dynamic_catalog(catalogs, monkeypatch):
    import model_tools
    from tools import tool_search
    from tools.registry import registry
    active = {}
    calls = []

    def definitions(*, skip_tool_search_assembly=False, disabled_toolsets=None, **kwargs):
        raw = catalogs(skip_tool_search_assembly=True, disabled_toolsets=disabled_toolsets, **kwargs)
        raw.extend(copy.deepcopy(row) for name, row in active.items()
                   if registry.get_entry(name).toolset not in (disabled_toolsets or ()))
        return raw if skip_tool_search_assembly else tool_search.assemble_tool_defs(raw).tool_defs

    def register(name="mcp_runtime_probe_lookup", description="Look up the current runtime probe."):
        schema = _schema(name)
        schema["function"]["description"] = description
        schema["function"]["parameters"] = {"type": "object", "properties": {
            "value": {"type": "string"}}, "required": ["value"]}
        def handler(args, **kwargs):
            calls.append(args)
            return json.dumps({"ok": True, "value": args["value"]})
        registry.register(name=name, toolset="mcp-runtime-probe", schema=schema["function"], handler=handler)
        active[name] = schema
        return name

    monkeypatch.setattr(model_tools, "get_tool_definitions", definitions)
    monkeypatch.setattr("tools.mcp_tool_discovery.has_registered_mcp_tools", lambda: True)
    return register, calls, active


def _bridge(agent, name, args):
    import model_tools
    return json.loads(model_tools.handle_function_call(
        name, args, enabled_toolsets=agent.enabled_toolsets, disabled_toolsets=agent.disabled_toolsets))


def test_unchanged_explicit_platform_exclusion_preserves_real_cross_platform_requests(runtime, catalogs):
    from run_agent import AIAgent
    db, _ = runtime
    db.create_session("surface-main", source="desktop")
    prior = None
    for platform in ("desktop", "weixin", "tui", "desktop"):
        agent = AIAgent(api_key="test-key", base_url="https://openrouter.ai/api/v1", session_db=db,
                        session_id="surface-main", platform=platform, quiet_mode=True, skip_context_files=True,
                        skip_memory=True, enabled_toolsets=[platform], disabled_toolsets=["catalog"])
        agent.compression_enabled = False
        agent._skip_mcp_refresh = True
        agent._use_prompt_caching = False
        agent.save_trajectories = False
        try:
            seen = _requests(agent)
            result = agent.run_conversation(platform, conversation_history=db.get_messages_as_conversation(agent.session_id),
                                            title_user_message="")
            assert result["completed"]
            if prior:
                assert _wire_json(seen[-1]["tools"]) == _wire_json(prior["tools"])
                assert seen[-1]["messages"][0] == prior["messages"][0]
                assert seen[-1]["messages"][:len(prior["messages"])] == prior["messages"]
            prior = copy.deepcopy(seen[-1])
        finally:
            agent.close()


def test_new_mcp_is_live_through_search_describe_call_without_mutating_warm_or_cold_head(runtime, dynamic_catalog):
    register, calls, _active = dynamic_catalog
    db, _ = runtime
    warm = _new_agent(db, "desktop", existing=True)
    cold = None
    try:
        seen = _requests(warm)
        first = warm.run_conversation("first", title_user_message="")
        old = copy.deepcopy(seen[-1])
        name = register()
        warm._skip_mcp_refresh = False
        second = warm.run_conversation("discover", conversation_history=first["messages"], title_user_message="")
        assert second["completed"]
        assert seen[-1]["tools"] == old["tools"]
        assert seen[-1]["messages"][0] == old["messages"][0]
        assert seen[-1]["messages"][:len(old["messages"])] == old["messages"]
        assert name not in warm.valid_tool_names
        assert name in _snapshot(second["messages"])["catalog"]
        search = _bridge(warm, "tool_search", {"queries": ["runtime probe lookup"]})
        assert name in search["tools"]
        described = _bridge(warm, "tool_describe", {"names": [name]})
        assert described["tools"][name]["parameters"]["required"] == ["value"]
        assert _bridge(warm, "tool_call", {"name": name, "arguments": {"value": "local"}})["ok"]
        assert calls == [{"value": "local"}]
        count = len(_updates(second["messages"]))
        third = warm.run_conversation("unchanged", conversation_history=second["messages"], title_user_message="")
        assert len(_updates(third["messages"])) == count
        cold = _new_agent(db, "desktop")
        cold._skip_mcp_refresh = False
        cold_seen = _requests(cold)
        restored = cold.run_conversation("cold", conversation_history=db.get_messages_as_conversation(cold.session_id),
                                         title_user_message="")
        assert restored["completed"]
        assert len(_updates(restored["messages"])) == count
        assert cold_seen[-1]["tools"] == old["tools"]
        cold.disabled_toolsets = [*(cold.disabled_toolsets or ()), "mcp-runtime-probe"]
        denied = cold.run_conversation("scope narrowed", conversation_history=restored["messages"], title_user_message="")
        assert denied["completed"]
        assert name not in _snapshot(denied["messages"])["catalog"]
        assert "error" in _bridge(cold, "tool_call", {"name": name, "arguments": {"value": "forbidden"}})
        assert calls == [{"value": "local"}]
        assert cold_seen[-1]["tools"] == old["tools"]
    finally:
        warm.close()
        if cold:
            cold.close()


@pytest.mark.parametrize("boundary", ["clear", "reload"])
def test_bridge_disabled_new_direct_mcp_remains_unexposed_until_explicit_boundary(runtime, dynamic_catalog, monkeypatch, boundary):
    from tools import tool_search
    from tools.mcp_tool_agent import refresh_agent_mcp_tools
    from secretary.conversation_cache import clear_context_cache
    register, _calls, _active = dynamic_catalog
    config = tool_search.ToolSearchConfig.from_raw({"enabled": "off"})
    monkeypatch.setattr(tool_search, "load_config", lambda: config)
    monkeypatch.setattr(tool_search, "load_config_readonly", lambda: config)
    db, _ = runtime
    agent = _new_agent(db, "desktop", existing=True)
    try:
        seen = _requests(agent)
        first = agent.run_conversation("first", title_user_message="")
        old = copy.deepcopy(seen[-1]["tools"])
        name = register()
        agent._skip_mcp_refresh = False
        next_turn = agent.run_conversation("new registration", conversation_history=first["messages"], title_user_message="")
        assert next_turn["completed"]
        assert seen[-1]["tools"] == old
        assert name not in agent.valid_tool_names
        assert _snapshot(next_turn["messages"])["bridge"] is False
        assert "discovery is unavailable" in _snapshot(next_turn["messages"])["catalog"]
        if boundary == "clear":
            assert clear_context_cache(db, agent._secretary_conversation_ref)["status"] == "cleared"
        else:
            refresh_agent_mcp_tools(agent)
        adopted = agent.run_conversation("after explicit boundary", conversation_history=next_turn["messages"], title_user_message="")
        assert adopted["completed"]
        assert name in agent.valid_tool_names
        assert name in {row["function"]["name"] for row in seen[-1]["tools"]}
    finally:
        agent.close()


def test_automatic_refresh_registry_failure_cannot_fall_back_to_rewriting_the_head(runtime, dynamic_catalog, monkeypatch):
    from tools.mcp_tool_agent import refresh_agent_mcp_tools
    from tools.registry import registry
    register, _calls, _active = dynamic_catalog
    db, _ = runtime
    agent = _new_agent(db, "desktop", existing=True)
    try:
        _requests(agent)
        agent.run_conversation("first", title_user_message="")
        old = copy.deepcopy(agent.tools)
        register()
        monkeypatch.setattr(registry, "get_all_entries", lambda: (_ for _ in ()).throw(RuntimeError("registry unavailable")))
        assert refresh_agent_mcp_tools(agent, preserve_prefix=True) == set()
        assert agent.tools == old
    finally:
        agent.close()


def test_cold_restore_does_not_require_registry_enumeration_to_reuse_complete_pin(runtime, catalogs, monkeypatch):
    from tools.registry import registry
    db, _ = runtime
    warm = _new_agent(db, "desktop", existing=True)
    cold = None
    try:
        seen = _requests(warm)
        first = warm.run_conversation("first", title_user_message="")
        old = copy.deepcopy(seen[-1])
        cold = _new_agent(db, "weixin")
        monkeypatch.setattr(registry, "get_all_entries", lambda: (_ for _ in ()).throw(RuntimeError("registry unavailable")))
        cold_seen = _requests(cold)
        second = cold.run_conversation("cold alternate platform", conversation_history=first["messages"], title_user_message="")
        assert second["completed"]
        assert cold_seen[-1]["tools"] == old["tools"]
        assert cold_seen[-1]["messages"][0] == old["messages"][0]
    finally:
        warm.close()
        if cold:
            cold.close()


def test_snapshot_catalog_does_not_enumerate_unavailable_sources_outside_current_scope(runtime, catalogs, monkeypatch):
    monkeypatch.setattr("tools.tool_search_catalog.hidden_declared_sources",
                        lambda: pytest.fail("runtime catalog must not inspect globally declared servers"))
    db, _ = runtime
    agent = _new_agent(db, "desktop", existing=True)
    try:
        _requests(agent)
        result = agent.run_conversation("scope-only initial directory", title_user_message="")
        assert result["completed"]
        assert _snapshot(result["messages"])["catalog"]
    finally:
        agent.close()


def test_schema_change_adds_one_system_update_without_rewriting_tools_or_old_history(runtime, dynamic_catalog):
    register, _calls, active = dynamic_catalog
    db, _ = runtime
    name = register()
    agent = _new_agent(db, "desktop", existing=True)
    try:
        seen = _requests(agent)
        first = agent.run_conversation("first", title_user_message="")
        old = copy.deepcopy(seen[-1])
        active[name]["function"]["parameters"]["properties"]["value"]["description"] = "New meaning."
        second = agent.run_conversation("changed schema", conversation_history=first["messages"], title_user_message="")
        assert len(_updates(second["messages"])) == len(_updates(first["messages"])) + 1
        assert seen[-1]["tools"] == old["tools"]
        assert seen[-1]["messages"][:len(old["messages"])] == old["messages"]
        third = agent.run_conversation("unchanged again", conversation_history=second["messages"], title_user_message="")
        assert len(_updates(third["messages"])) == len(_updates(second["messages"]))
    finally:
        agent.close()


def test_snapshot_read_failure_does_not_publish_a_false_removal(runtime, dynamic_catalog, monkeypatch):
    import model_tools
    db, _ = runtime
    agent = _new_agent(db, "desktop", existing=True)
    try:
        _requests(agent)
        first = agent.run_conversation("first", title_user_message="")
        before = len(_updates(first["messages"]))
        monkeypatch.setattr(model_tools, "get_tool_definitions", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("offline")))
        second = agent.run_conversation("read unavailable", conversation_history=first["messages"], title_user_message="")
        assert second["completed"]
        assert len(_updates(second["messages"])) == before
    finally:
        agent.close()


@pytest.mark.parametrize("policy", ["Replacement during catalog outage.", ""])
def test_catalog_failure_keeps_directory_but_delivers_current_system_policy(runtime, catalogs, monkeypatch, policy):
    db, _ = runtime
    agent = _new_agent(db, "weixin", existing=True)
    try:
        seen = _requests(agent)
        _wire_gateway(agent, "weixin", policy="Original policy.")
        first = agent.run_conversation("first", title_user_message="")
        original_request = copy.deepcopy(seen[-1])
        original_snapshot = copy.deepcopy(_snapshot(first["messages"]))
        monkeypatch.setattr("agent.conversation_capabilities._live_catalog",
                            lambda agent: (_ for _ in ()).throw(RuntimeError("catalog offline")))
        _wire_gateway(agent, "weixin", policy=policy)
        second = agent.run_conversation("policy changed while catalog offline", conversation_history=first["messages"], title_user_message="")
        assert second["completed"]
        current = _snapshot(second["messages"])
        assert current["catalog"] == original_snapshot["catalog"]
        assert current["schemas"] == original_snapshot["schemas"]
        assert current["system_policy"] == policy
        assert seen[-1]["messages"][0] == original_request["messages"][0]
        assert seen[-1]["tools"] == original_request["tools"]
        assert seen[-1]["messages"][:len(original_request["messages"])] == original_request["messages"]
        update = seen[-1]["messages"][-1]
        assert update["role"] == "system"
        assert policy in update["content"] if policy else "no longer apply" in update["content"]
        count = len(_updates(second["messages"]))
        _wire_gateway(agent, "weixin", policy=policy)
        third = agent.run_conversation("same failed catalog and policy", conversation_history=second["messages"], title_user_message="")
        assert third["completed"]
        assert len(_updates(third["messages"])) == count
    finally:
        agent.close()


def test_initial_catalog_failure_exposes_policy_and_unknown_directory_then_successful_recovery(runtime, catalogs, monkeypatch):
    import agent.conversation_capabilities as capabilities
    db, _ = runtime
    agent = _new_agent(db, "weixin", existing=True)
    real_catalog = capabilities._live_catalog
    try:
        seen = _requests(agent)
        _wire_gateway(agent, "weixin", policy="Initial authoritative policy.")
        monkeypatch.setattr(capabilities, "_live_catalog", lambda agent: (_ for _ in ()).throw(RuntimeError("catalog offline")))
        first = agent.run_conversation("first with unavailable directory", title_user_message="")
        assert first["completed"]
        unknown = _snapshot(first["messages"])
        assert unknown["system_policy"] == "Initial authoritative policy."
        assert unknown["schemas"] is None
        assert "temporarily unknown" in unknown["catalog"]
        assert "No additional tools" not in unknown["catalog"]
        assert "Initial authoritative policy." in seen[-1]["messages"][-1]["content"]
        assert seen[-1]["messages"][-1]["role"] == "system"
        monkeypatch.setattr(capabilities, "_live_catalog", real_catalog)
        second = agent.run_conversation("directory recovered", conversation_history=first["messages"], title_user_message="")
        assert second["completed"]
        assert _snapshot(second["messages"])["schemas"] is not None
        assert _snapshot(second["messages"])["system_policy"] == unknown["system_policy"]
        assert len(_updates(second["messages"])) == len(_updates(first["messages"])) + 1
    finally:
        agent.close()


def test_main_catalog_classification_keeps_scope_and_omits_direct_and_forbidden_noting_tools(runtime, catalogs):
    from tools.secretary_dispatch import _SURFACE_AGENT, secretary_surface_scope
    db, _ = runtime
    agent = _new_agent(db, "desktop", existing=True)
    outer_owner = object()
    previous_owner = _SURFACE_AGENT.get()
    try:
        _requests(agent)
        with secretary_surface_scope(outer_owner):
            result = agent.run_conversation("Main capability catalog", title_user_message="")
            assert _SURFACE_AGENT.get() is outer_owner
        assert _SURFACE_AGENT.get() is previous_owner
        assert result["completed"]
        listing = _snapshot(result["messages"])["catalog"]
        assert "audit_tool_1" in listing
        forbidden = {"notebook_create", "notebook_update", "notebook_archive", "finish_noting"}
        assert forbidden <= {tool["function"]["name"] for tool in agent.tools}
        assert forbidden.isdisjoint(agent.valid_tool_names)
        direct = agent.valid_tool_names - {"tool_search", "tool_describe", "tool_call"}
        assert all(name not in listing for name in forbidden | direct)
    finally:
        agent.close()


@pytest.mark.parametrize("in_place", [True, False], ids=["in_place", "rotation"])
def test_compaction_carries_policy_into_cold_ui_then_gateway_can_revoke_it(runtime, catalogs, monkeypatch, in_place):
    from agent.context_compressor import SUMMARY_PREFIX
    db, _ = runtime
    agent = _new_agent(db, "weixin", existing=True)
    cold_ui = cold_gateway = None
    try:
        _wire_gateway(agent, "weixin", policy="Keep the current private channel policy.")
        _requests(agent)
        first = agent.run_conversation("source " * 2000, title_user_message="")
        db.notebook_set_local_enabled(agent._secretary_conversation_ref, False)
        agent.compression_enabled, agent.compression_in_place = True, in_place
        agent._compression_feasibility_checked = True
        compressor = agent.context_compressor
        monkeypatch.setattr(compressor, "compress", lambda messages, **kwargs: [
            {"role": "user", "content": SUMMARY_PREFIX + "summary", "_compressed_summary": True},
            copy.deepcopy(messages[-1]),
        ])
        compressor._last_compress_aborted = False
        compressor._last_summary_error = None
        compressor.compression_count = 1
        agent._compress_context(first["messages"], None, approx_tokens=10000, trigger="manual")
        sid = agent.session_id
        cold_ui = _new_agent(db, "desktop", session_id=sid)
        _requests(cold_ui)
        ui = cold_ui.run_conversation("cold UI", conversation_history=db.get_messages_as_conversation(sid), title_user_message="")
        assert ui["completed"]
        assert _snapshot(ui["messages"])["system_policy"] == "Keep the current private channel policy."
        cold_gateway = _new_agent(db, "weixin", session_id=sid)
        _wire_gateway(cold_gateway, "weixin", policy="")
        gateway_requests = _requests(cold_gateway)
        revoked = cold_gateway.run_conversation("cold channel", conversation_history=db.get_messages_as_conversation(sid), title_user_message="")
        assert revoked["completed"]
        assert _snapshot(revoked["messages"])["system_policy"] == ""
        assert "no longer apply" in gateway_requests[-1]["messages"][-1]["content"]
    finally:
        agent.close()
        if cold_ui:
            cold_ui.close()
        if cold_gateway:
            cold_gateway.close()


def test_derived_snapshot_change_does_not_invalidate_another_warm_runtime_head(runtime, catalogs):
    db, _ = runtime
    first_agent = _new_agent(db, "weixin", existing=True)
    second_agent = None
    try:
        first_requests = _requests(first_agent)
        _wire_gateway(first_agent, "weixin", policy="Original policy.")
        first = first_agent.run_conversation("first", title_user_message="")
        original = copy.deepcopy(first_requests[-1])
        second_agent = _new_agent(db, "weixin")
        _wire_gateway(second_agent, "weixin", policy="Replacement policy.")
        _requests(second_agent)
        second = second_agent.run_conversation("other runtime", conversation_history=first["messages"], title_user_message="")
        assert second["completed"]
        first_agent._build_system_prompt = lambda *args, **kwargs: pytest.fail("tail-only change must not rebuild the root")
        third = first_agent.run_conversation("first runtime returns", conversation_history=db.get_messages_as_conversation(first_agent.session_id),
                                             title_user_message="")
        assert third["completed"]
        assert _snapshot(third["messages"])["system_policy"] == "Replacement policy."
        assert first_requests[-1]["tools"] == original["tools"]
        assert first_requests[-1]["messages"][0] == original["messages"][0]
    finally:
        first_agent.close()
        if second_agent:
            second_agent.close()


@pytest.mark.parametrize("field", ["root", "tools", "ephemeral_system_prompt", "prefill_messages"])
def test_true_input_change_still_reaches_an_existing_warm_runtime(runtime, catalogs, field):
    db, _ = runtime
    agent = _new_agent(db, "desktop", existing=True)
    try:
        seen = _requests(agent)
        first = agent.run_conversation("first", title_user_message="")
        row = db.get_session(agent.session_id)
        pin = json.loads(row["tool_names"])
        if field == "root":
            db.update_system_prompt(agent.session_id, row["system_prompt"] + "\nUpdated root instruction.")
        else:
            if field == "tools":
                pin["tools"][0]["function"]["description"] = "Updated direct tool instruction."
            elif field == "ephemeral_system_prompt":
                pin["request_prefix"][field] = "Updated ephemeral instruction."
            else:
                pin["request_prefix"][field] = [{"role": "user", "content": "Updated prefill."}]
            db.update_session_tool_names(agent.session_id, pin)
        second = agent.run_conversation("authoritative cache changed", conversation_history=first["messages"], title_user_message="")
        assert second["completed"]
        request = seen[-1]
        expected = {"root": "Updated root instruction.", "tools": "Updated direct tool instruction.",
                    "ephemeral_system_prompt": "Updated ephemeral instruction.", "prefill_messages": "Updated prefill."}
        assert expected[field] in json.dumps(request)
    finally:
        agent.close()


@pytest.mark.parametrize("policy", ["", "Replacement complete policy."])
def test_clear_adopts_current_gateway_policy_including_explicit_revocation(runtime, catalogs, policy):
    from secretary.conversation_cache import clear_context_cache
    db, _ = runtime
    agent = _new_agent(db, "weixin", existing=True)
    try:
        seen = _requests(agent)
        _wire_gateway(agent, "weixin", policy="Original full policy.")
        first = agent.run_conversation("first", title_user_message="")
        old = copy.deepcopy(seen[-1]["messages"][0])
        assert clear_context_cache(db, agent._secretary_conversation_ref)["status"] == "cleared"
        _wire_gateway(agent, "weixin", policy=policy)
        second = agent.run_conversation("after clear", conversation_history=first["messages"], title_user_message="")
        assert second["completed"]
        assert seen[-1]["messages"][0] != old
        assert "Original full policy." not in seen[-1]["messages"][0]["content"]
        assert _snapshot(second["messages"])["system_policy"] == policy
    finally:
        agent.close()


@pytest.mark.parametrize("mode", ["main", "global_off", "side_agent"])
def test_automatic_bot_chat_epoch_refresh_preserves_only_established_main_prefix(runtime, catalogs, monkeypatch, mode):
    db, config = runtime
    if mode == "global_off":
        config.write_text(config.read_text().replace("enabled: true", "enabled: false"), encoding="utf-8")
    warm = _new_agent(db, "desktop", existing=True)
    warm.side_agent = mode == "side_agent"
    cold = None
    refreshed = []
    try:
        seen = _requests(warm)
        first = warm.run_conversation("first", title_user_message="")
        old = copy.deepcopy(seen[-1])
        cold = _new_agent(db, "desktop")
        cold.side_agent = mode == "side_agent"
        monkeypatch.setattr("agent.conversation_loop._bot_chat_prompt_stale", lambda *args: True)
        monkeypatch.setattr("agent.conversation_loop._refresh_bot_chat_tools", lambda agent: refreshed.append(agent))
        cold_seen = _requests(cold)
        result = cold.run_conversation("capability epoch changed", conversation_history=first["messages"], title_user_message="")
        assert result["completed"]
        assert bool(refreshed) is (mode != "main")
        if mode == "main":
            assert cold_seen[-1]["tools"] == old["tools"]
            assert cold_seen[-1]["messages"][0] == old["messages"][0]
    finally:
        warm.close()
        if cold:
            cold.close()
