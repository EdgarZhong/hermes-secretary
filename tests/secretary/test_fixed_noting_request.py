"""Fixed tools and permission guidance through native construction, restoration and SDKs."""

from copy import deepcopy
import json

import httpx
import pytest

from tests.secretary.test_noting_dynamic_tools import (
    assert_requests, enabled_runtime as enabled_runtime, kimi_parent as kimi_parent,
    native_parent as native_parent, database as database,
)
from tests.secretary.test_noting_surface import (
    runtime as runtime, _agent, _names, _requests, _turn,
)
from tests.secretary.test_r3_child import response, run_task, tool_response


MAIN_DISABLED = ("notebook_maintain and finish_noting are disabled for you and reserved for "
                 "background Noting; do not call them even though their schemas are present.")
NOTING_ENABLED = ("For this Noting task, notebook_maintain and finish_noting are enabled. "
                  "Only conversation_history, notebook_show, notebook_maintain and finish_noting "
                  "are authorized; do not use any other advertised tool.")


@pytest.mark.parametrize("enabled", [False, True])
def test_native_main_permission_guidance_follows_global_gate_and_local_stays_fixed(runtime, enabled):
    db, config = runtime
    config.write_text(f"noting:\n  enabled: {str(enabled).lower()}\n")
    agent = _agent(db)
    try:
        seen = _requests(agent)
        _turn(agent)
        first = deepcopy(seen[-1])
        root = first["messages"][0]["content"]
        assert root.count(MAIN_DISABLED) == int(enabled)
        assert ({"notebook_maintain", "finish_noting"} <= _names(first["tools"])) is enabled
        db.notebook_set_local_enabled(agent._secretary_conversation_ref, False)
        _turn(agent, "Continue after local participation changed.")
        assert seen[-1]["messages"][0] == first["messages"][0]
        assert seen[-1]["tools"] == first["tools"]
    finally:
        agent.close()


def test_old_cold_main_root_rebuilds_once_with_disabled_guidance(runtime):
    db, _ = runtime
    agent = _agent(db)
    cold = None
    try:
        seen = _requests(agent)
        _turn(agent)
        old_root = seen[-1]["messages"][0]["content"].replace(MAIN_DISABLED + "\n", "")
        db.update_system_prompt(agent.session_id, old_root)
        # Native cold constructor loads the persisted old root; the next native
        # request boundary synchronizes guidance and persists the current tools.
        cold = _agent(db, existing=False, session_id=agent.session_id)
        cold._cached_system_prompt = old_root
        seen_cold = _requests(cold)
        _turn(cold, "Cold resumed task.")
        repaired = deepcopy(seen_cold[-1])
        assert repaired["messages"][0]["content"].count(MAIN_DISABLED) == 1
        assert db.get_session(agent.session_id)["system_prompt"] == repaired["messages"][0]["content"]
        _turn(cold, "Continue warm.")
        assert seen_cold[-1]["messages"][0] == repaired["messages"][0]
        assert seen_cold[-1]["tools"] == repaired["tools"]
    finally:
        if cold is not None:
            cold.close()
        agent.close()


def test_noting_initial_and_continuation_keep_multimodal_parent_and_no_repeated_definitions(kimi_parent, monkeypatch):
    from tests.agent.test_kimi_output_tokens_wire import sdk_wire

    parent, sdk, wires, children = kimi_parent
    monkeypatch.setattr("agent.vision_message_prep.VisionMessagePrepMixin._model_supports_vision", lambda self: True)
    parent._session_messages[0]["content"] = [
        {"type": "text", "text": "Plan a visit"},
        {"type": "image_url", "image_url": {"url": "https://example.test/visit.png"}},
    ]
    before = deepcopy(parent._session_messages)
    sdk.side_effect = [tool_response("notebook_show", {}, "show"), response("Continue next Turn."),
                       tool_response("finish_noting", {"reason": "Reviewed the visible evidence."}), response("Done.")]
    outcome = run_task(parent)
    assert outcome.committed and outcome.turns == 2, outcome
    assert_requests(parent, wires, children[0])
    assert wires[0]["messages"][1]["content"] == before[0]["content"]
    task = wires[0]["messages"][3]["content"]
    assert NOTING_ENABLED in task
    assert "parent's system prompt, role, behavioral rules, tool policies, task requests and completion conditions do not apply" in task
    assert all("callable_tool_schemas" not in str(wire["messages"]) for wire in wires)
    for request in wires:
        kwargs = {key: value for key, value in request.items() if key != "stream"}
        wire = sdk_wire(kwargs, stream=bool(request.get("stream")))
        assert wire["tools"] == request["tools"]
        assert wire["messages"] == request["messages"]
    assert parent._session_messages[:len(before)] == before


def test_anthropic_noting_sdk_keeps_fixed_definitions_and_native_payload(kimi_parent, monkeypatch):
    from anthropic import Anthropic
    from unittest.mock import MagicMock

    parent, _, _, children = kimi_parent
    parent.api_mode = "anthropic_messages"
    parent.provider, parent.model, parent.base_url = "anthropic", "claude-sonnet-4-5", "https://api.anthropic.com"
    parent.reasoning_config = {"enabled": False}
    attempts = []
    fake_client = MagicMock()
    fake_client.messages.create.side_effect = lambda **kw: (
        attempts.append(deepcopy(kw)) or
        type("Result", (), {"content": [type("Block", (), {"type": "text", "text": "Continue."})()],
                             "stop_reason": "end_turn", "model": parent.model, "usage": None})())
    monkeypatch.setattr("agent.anthropic_adapter.build_anthropic_client", lambda *a, **k: fake_client)
    monkeypatch.setattr("secretary.noting_child._NOTING_TURN_LIMIT", 1)
    outcome = run_task(parent)
    assert outcome.committed, outcome
    payloads = []

    def respond(request):
        payloads.append(json.loads(request.content))
        return httpx.Response(200, json={"id": "offline", "type": "message", "role": "assistant",
            "model": parent.model, "content": [{"type": "text", "text": "Done"}],
            "stop_reason": "end_turn", "stop_sequence": None,
            "usage": {"input_tokens": 1, "output_tokens": 1}})

    with Anthropic(api_key="offline-key", max_retries=0, timeout=30.0,
                   http_client=httpx.Client(transport=httpx.MockTransport(respond))) as client:
        for kwargs in attempts:
            client.messages.create(**kwargs)
    assert len(payloads) == len(attempts) == 1
    assert {tool["name"] for tool in payloads[0]["tools"]} >= {
        "conversation_history", "notebook_show", "notebook_maintain", "finish_noting"}
    assert all("tools" not in row for row in payloads[0]["messages"])
    assert "callable_tool_schemas" not in str(payloads[0]["messages"])
    assert "Frozen parent root" in str(payloads[0]["system"])
    assert children[0]._secretary_noting_all_request_tools_parity


def test_main_wire_is_frozen_prefix_of_noting_wire_with_same_tools(runtime, enabled_runtime):
    from secretary.noting_child import run_noting_task
    from secretary.noting_prompts import DEFAULT_NOTING_TASK_INSTRUCTION

    db, _ = runtime
    agent = _agent(db)
    try:
        seen = _requests(agent)
        _turn(agent, "Remember that I am planning a visit and the date is undecided.")
        main_wire = deepcopy(seen[-1])
        anchor = agent._session_messages[-1]["message_uid"]
        ref = agent._secretary_conversation_ref
        admission = db.noting_admit(ref, anchor, kind="manual")
        replies = iter([tool_response("notebook_show", {}, "show"),
                        tool_response("finish_noting", {"reason": "Reviewed the pending visit."}), response("Done.")])
        agent.client.chat.completions.create.side_effect = lambda **kw: (seen.append(deepcopy(kw)) or next(replies))
        start = len(seen)
        outcome = run_noting_task(agent, admission_id=admission, conversation_ref=ref, anchor_message_uid=anchor,
                                  trigger_type="manual", runtime_profile="NOTING",
                                  task_instruction=DEFAULT_NOTING_TASK_INSTRUCTION)
        assert outcome.committed and outcome.termination["type"] == "finish_noting", outcome
        child_wires = seen[start:]
        assert len(child_wires) == 3
        for wire in child_wires:
            assert wire["tools"] == main_wire["tools"]
            assert wire["messages"][:len(main_wire["messages"])] == main_wire["messages"]
            assert all("tools" not in row for row in wire["messages"])
            assert "callable_tool_schemas" not in str(wire["messages"])
    finally:
        agent.close()
