"""Frozen spec Targets through real construction and warm/cold Main request boundaries."""

import copy
import json
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from agent.prompt_builder import PLATFORM_HINTS, SECRETARY_LOCAL_CRON_DELIVERY_APPEND
from agent.secretary_prompt import SECRETARY_CRONJOB_DESCRIPTION, SECRETARY_CRON_SCHEDULE_NOTE
from agent.system_prompt import HISTORY_SEARCH_GUIDANCE, SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE, platform_hint
from tests.secretary.test_noting_surface import _agent, _requests, _turn
from tools.cronjob_tools import CRONJOB_SCHEMA
from tests.secretary.test_noting_child import mock_response

pytest_plugins = ("tests.secretary.test_noting_surface",)


@pytest.fixture(autouse=True)
def interactive_cron_lane(monkeypatch):
    """Use the native CLI availability flag; the cron tool must actually be loaded."""
    monkeypatch.setenv("HERMES_INTERACTIVE", "1")


def _section(heading, end):
    spec = (Path(__file__).resolve().parents[2] / "docs/02-noting-system-specification.md").read_text()
    return spec.split(heading, 1)[1].split(end, 1)[0]


def _cron_schema(request):
    for tool in request["tools"]:
        if tool["function"]["name"] == "cronjob_manage":
            return tool["function"]
    for row in reversed(request["messages"]):
        if row["role"] == "tool":
            payload = json.loads(row["content"])
            if "cronjob_manage" in payload.get("tools", {}):
                return payload["tools"]["cronjob_manage"]
    raise AssertionError("The real request did not expose or describe cronjob_manage")


def _describe_requests(agent):
    def response(index):
        if index % 2:
            call = SimpleNamespace(id=f"describe-{index}", type="function", function=SimpleNamespace(
                name="tool_describe", arguments=json.dumps({"names": ["cronjob_manage"]})))
            return mock_response(None, "tool_calls", [call])
        return mock_response("done")
    return _requests(agent, response)


def _root(request):
    return "\n".join(row["content"] for row in request["messages"] if row["role"] in {"system", "developer"})


def test_guidance_matches_frozen_spec_six_paragraph_target_verbatim():
    section = _section("#### 1.2 `SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE`", "### 2. Noting Task messages")
    frozen = section.split("```text\n", 1)[1].split("\n```", 1)[0].split("\n\n")
    opening, merged, memo = [line.removeprefix("> ") for line in section.splitlines() if line.startswith("> ")]
    expected = "\n\n".join([frozen[0], opening, frozen[2], frozen[3].replace("agent_task", "secretary_task"),
                              frozen[-1], merged, memo])
    assert SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE == expected
    assert len(expected.split("\n\n")) == 7  # heading plus six paragraphs
    assert "`agent_task`" not in expected


def test_cron_targets_match_spec_verbatim_and_native_registry_keeps_originals():
    desc = _section("#### 7.1 `cronjob_manage`", "#### 7.2")
    schedule = _section("#### 7.2 `cronjob_manage`", "#### 7.3")
    note = _section("#### 7.3 `_LOCAL_CRON_DELIVERY_NOTE`", "---")
    assert SECRETARY_CRONJOB_DESCRIPTION == next(line[2:] for line in desc.splitlines() if line.startswith("> "))
    assert SECRETARY_CRON_SCHEDULE_NOTE == next(line[2:] for line in schedule.splitlines() if line.startswith("> "))
    assert SECRETARY_LOCAL_CRON_DELIVERY_APPEND == next(line[2:] for line in note.splitlines() if line.startswith("> "))
    assert "use this for 'remind me in N minutes'" in CRONJOB_SCHEMA["parameters"]["properties"]["schedule"]["description"]
    assert SECRETARY_CRONJOB_DESCRIPTION != CRONJOB_SCHEMA["description"]


def test_real_warm_turn_switches_guidance_and_cron_together_without_mutating_registry(runtime):
    db, config = runtime
    native = copy.deepcopy(CRONJOB_SCHEMA)
    agent = _agent(db, selected=["cronjob"])
    seen = _describe_requests(agent)
    try:
        _turn(agent)
        first = seen[-1]
        assert _root(first).count(SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE) == 1
        assert _root(first).count(SECRETARY_LOCAL_CRON_DELIVERY_APPEND) == 1
        target_schema = copy.deepcopy(_cron_schema(first))
        manifest = next(tool["function"]["description"] for tool in first["tools"]
                        if tool["function"]["name"] == "tool_search")
        assert "- cronjob_manage: Manage scheduled cron jobs." in manifest
        assert target_schema["description"] == SECRETARY_CRONJOB_DESCRIPTION
        assert "use this for 'remind me in N minutes'" not in target_schema["parameters"]["properties"]["schedule"]["description"]
        assert target_schema["parameters"]["properties"]["schedule"]["description"].endswith(
            'Not for in-Conversation reminders — "remind me in N minutes" belongs to the Notebook Schedule, not cron.')
        root = _root(first)
        _turn(agent, "same configuration")
        assert _root(seen[-1]) == root
        assert _cron_schema(seen[-1]) == target_schema
        db.notebook_set_local_enabled(agent._secretary_conversation_ref, False)
        _turn(agent, "local off")
        assert _root(seen[-1]) == root
        assert _cron_schema(seen[-1]) == target_schema
        config.write_text("noting:\n  enabled: false\n")
        _turn(agent, "global off")
        assert SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE not in _root(seen[-1])
        assert SECRETARY_LOCAL_CRON_DELIVERY_APPEND not in _root(seen[-1])
        assert HISTORY_SEARCH_GUIDANCE in _root(seen[-1])
        off_schema = _cron_schema(seen[-1])
        assert off_schema["description"] == native["description"]
        assert off_schema["parameters"]["properties"]["schedule"] == native["parameters"]["properties"]["schedule"]
        config.write_text("noting:\n  enabled: true\n")
        _turn(agent, "global on again")
        assert _root(seen[-1]) == root
        assert _cron_schema(seen[-1]) == target_schema
        assert CRONJOB_SCHEMA == native
    finally:
        agent.close()


@pytest.mark.parametrize("source", ["cron", "dreaming", "skill_refinement", "subagent"])
def test_auxiliary_construction_preserves_native_cron_schema_and_platform_hint(runtime, source):
    db, _config = runtime
    db.create_session("auxiliary", source=source)
    agent = _agent(db, selected=["cronjob"], existing=False, session_id="auxiliary")
    try:
        seen = _describe_requests(agent)
        _turn(agent)
        schema = _cron_schema(seen[-1])
        assert schema["description"] == CRONJOB_SCHEMA["description"]
        assert schema["parameters"]["properties"]["schedule"] == CRONJOB_SCHEMA["parameters"]["properties"]["schedule"]
        assert platform_hint(agent) == PLATFORM_HINTS["cli"]
        prompt = agent._build_system_prompt()
        assert SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE not in prompt
        assert SECRETARY_LOCAL_CRON_DELIVERY_APPEND not in prompt
    finally:
        agent.close()


@pytest.mark.parametrize("enabled", [False, True])
def test_cold_main_reconstruction_uses_current_global_gate_once(runtime, enabled):
    db, config = runtime
    config.write_text(f"noting:\n  enabled: {str(not enabled).lower()}\n")
    initial = _agent(db, selected=["cronjob"], session_id="cold-main")
    _requests(initial)
    _turn(initial)
    initial.close()
    history = db.get_messages_as_conversation("cold-main")
    config.write_text(f"noting:\n  enabled: {str(enabled).lower()}\n")
    agent = _agent(db, selected=["cronjob"], session_id="cold-main", existing=False)
    agent._cached_system_prompt = None
    try:
        seen = _describe_requests(agent)
        result = agent.run_conversation(user_message="resumed", conversation_history=history, title_user_message="")
        assert result["completed"] is True
        root = _root(seen[-1])
        assert root.count(SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE) == int(enabled)
        assert root.count(SECRETARY_LOCAL_CRON_DELIVERY_APPEND) == int(enabled)
        assert _cron_schema(seen[-1])["description"] == (
            SECRETARY_CRONJOB_DESCRIPTION if enabled else CRONJOB_SCHEMA["description"])
    finally:
        agent.close()


def test_bridge_scope_is_concurrent_isolated_and_resets_after_failure(runtime):
    import model_tools
    from agent.secretary_prompt import cron_schema_scope
    db, _config = runtime
    parent = _agent(db, selected=["cronjob"])
    db.create_session("aux", source="cron")
    auxiliary = _agent(db, selected=["cronjob"], existing=False, session_id="aux")
    native_search = model_tools.handle_function_call(
        "tool_search", {"queries": ["cron"]}, enabled_toolsets=["cronjob"])
    results = {}
    barrier = threading.Barrier(2)
    def describe(owner, name):
        from secretary.noting_scope import owning_db_scope
        with owning_db_scope(db), cron_schema_scope(owner):
            barrier.wait(2)
            payload = json.loads(model_tools.handle_function_call(
                "tool_describe", {"names": ["cronjob_manage"]}, enabled_toolsets=["cronjob"]))
            searched = model_tools.handle_function_call(
                "tool_search", {"queries": ["cron"]}, enabled_toolsets=["cronjob"])
            results[name] = (payload["tools"]["cronjob_manage"]["description"], searched)
    workers = [threading.Thread(target=describe, args=(parent, "main")),
               threading.Thread(target=describe, args=(auxiliary, "aux"))]
    try:
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(3)
        assert results["main"][0] == SECRETARY_CRONJOB_DESCRIPTION
        assert json.loads(results["main"][1])["tools"]["cronjob_manage"]["description"] == SECRETARY_CRONJOB_DESCRIPTION
        assert results["aux"] == (CRONJOB_SCHEMA["description"], native_search)
        with pytest.raises(RuntimeError), cron_schema_scope(parent):
            raise RuntimeError("Interrupted bridge")
        native = json.loads(model_tools.handle_function_call(
            "tool_describe", {"names": ["cronjob_manage"]}, enabled_toolsets=["cronjob"]))
        assert native["tools"]["cronjob_manage"]["description"] == CRONJOB_SCHEMA["description"]
        assert model_tools.handle_function_call(
            "tool_search", {"queries": ["cron"]}, enabled_toolsets=["cronjob"]) == native_search
    finally:
        parent.close()
        auxiliary.close()


def test_eager_cron_schema_uses_same_target_without_changing_native_registry(runtime):
    db, config = runtime
    config.write_text("noting:\n  enabled: true\ntools:\n  tool_search:\n    enabled: off\n")
    agent = _agent(db, selected=["cronjob"])
    seen = _requests(agent)
    try:
        _turn(agent)
        schema = _cron_schema(seen[-1])
        assert schema["description"] == SECRETARY_CRONJOB_DESCRIPTION
        assert "use this for 'remind me in N minutes'" not in schema["parameters"]["properties"]["schedule"]["description"]
        assert CRONJOB_SCHEMA["description"] != SECRETARY_CRONJOB_DESCRIPTION
    finally:
        agent.close()


def test_real_bridge_search_and_describe_return_targets_in_one_tool_round(runtime):
    db, _config = runtime
    agent = _agent(db, selected=["cronjob"])
    def response(index):
        if index == 1:
            calls = [SimpleNamespace(id=name, type="function", function=SimpleNamespace(
                name=name, arguments=json.dumps(args))) for name, args in (
                    ("tool_search", {"queries": ["cron"]}),
                    ("tool_describe", {"names": ["cronjob_manage"]}))]
            return mock_response(None, "tool_calls", calls)
        return mock_response("done")
    seen = _requests(agent, response)
    try:
        _turn(agent)
        rows = [json.loads(row["content"]) for row in seen[-1]["messages"] if row["role"] == "tool"]
        searched = next(row for row in rows if "results" in row)
        described = next(row for row in rows if "results" not in row and "tools" in row)
        search_description = searched["tools"]["cronjob_manage"]["description"]
        assert search_description == SECRETARY_CRONJOB_DESCRIPTION
        assert described["tools"]["cronjob_manage"]["description"] == SECRETARY_CRONJOB_DESCRIPTION
        assert described["tools"]["cronjob_manage"]["parameters"]["properties"]["schedule"]["description"].endswith(
            'Not for in-Conversation reminders — "remind me in N minutes" belongs to the Notebook Schedule, not cron.')
    finally:
        agent.close()
