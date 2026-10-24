"""Frozen request boundaries and output-cap recovery through the native child loop."""

from copy import deepcopy
import json
from unittest.mock import MagicMock

import pytest

from tests.agent.test_plugin_context_engine_init import _StubEngine
from tests.secretary.test_r3_child import (
    database as database,
    native_parent as native_parent,
    response,
    run_task,
    tool_response,
)


class SelectingEngine(_StubEngine):
    @property
    def name(self):
        return "noting_protocol_selector"

    def __init__(self):
        self.selections = []

    def select_context(self, request_messages, **kwargs):
        self.selections.append(deepcopy((request_messages, kwargs["conversation_messages"])))
        selected = deepcopy(request_messages)
        first_user = next(row for row in selected if row["role"] == "user")
        first_user["content"] += "\nSelected request context."
        return selected


@pytest.fixture
def configured_selector(monkeypatch):
    config = {"context": {"engine": "noting_protocol_selector"}, "agent": {},
              "compression": {"enabled": False}, "noting": {"enabled": True}, "scheduler": {"enabled": False}}
    monkeypatch.setattr("hermes_cli.config.load_config", lambda *a, **kw: deepcopy(config))
    monkeypatch.setattr("hermes_cli.config.load_config_readonly", lambda *a, **kw: deepcopy(config))
    monkeypatch.setattr("plugins.context_engine.load_context_engine", lambda name: SelectingEngine())
    monkeypatch.setattr("agent.model_metadata.get_model_context_length", lambda *a, **kw: 204800)
    return config


def test_selector_only_receives_child_suffix_across_requests_and_turns(configured_selector, native_parent, monkeypatch):
    from secretary import noting_child

    parent, client = native_parent
    children = []
    original = noting_child.build_noting_child

    def capture(*args, **kwargs):
        child = original(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(noting_child, "build_noting_child", capture)
    client.chat.completions.create.side_effect = [
        tool_response("notebook_show", {}, "show"), response("Continue next Turn."),
        tool_response("finish_noting", {"reason": "Reviewed the unchanged work."}), response("Done."),
    ]
    before = deepcopy(parent._session_messages)
    outcome = run_task(parent)
    assert outcome.committed and outcome.turns == 2, outcome
    wires = [call.kwargs for call in client.chat.completions.create.call_args_list]
    assert len(wires) == 4
    prefix = wires[0]["messages"][:3]
    assert "Plan a visit" in str(prefix) and "Dates are undecided" in str(prefix)
    assert all(wire["messages"][:3] == prefix for wire in wires)
    assert all(wire["tools"] == wires[0]["tools"] for wire in wires)
    assert all("Selected request context." in str(wire["messages"][3:]) for wire in wires)
    selections = children[0].context_compressor.selections
    assert len(selections) == 4
    assert all("Plan a visit" not in str(parts) and "Dates are undecided" not in str(parts)
               for parts in selections)
    assert parent._session_messages[:len(before)] == before


def test_disabled_noting_keeps_native_context_selection(configured_selector, native_parent):
    parent, client = native_parent
    configured_selector["noting"]["enabled"] = False
    client.chat.completions.create.return_value = response("Native answer.")
    result = parent.run_conversation("Native request", conversation_history=parent._session_messages,
                                     title_user_message="")
    assert result["completed"]
    assert len(parent.context_compressor.selections) == 1
    selected_request, selected_history = parent.context_compressor.selections[0]
    assert selected_request[0]["role"] == "system"
    assert "Plan a visit" in str(selected_request) and "Plan a visit" in str(selected_history)
    wire = client.chat.completions.create.call_args.kwargs["messages"]
    assert "Selected request context." in str(wire)


@pytest.mark.parametrize("repeated", [False, True], ids=["cap-then-finish", "cap-budget-exhausted"])
def test_output_cap_retry_preserves_prefix_and_working_state(native_parent, database, monkeypatch, repeated):
    from secretary import noting_child

    parent, client = native_parent
    children = []
    original = noting_child.build_noting_child

    def capture(*args, **kwargs):
        child = original(*args, **kwargs)
        child._compress_context = MagicMock(side_effect=AssertionError("Noting must never auto-compact"))
        children.append(child)
        return child

    monkeypatch.setattr(noting_child, "build_noting_child", capture)
    error = Exception("max_tokens: 65536 > context_window: 204800 - input_tokens: 203800 = available_tokens: 1000")
    error.status_code = error.code = 400
    calls = 0
    wires = []

    def provider(**kwargs):
        nonlocal calls
        wires.append(deepcopy(kwargs))
        calls += 1
        if calls == 1:
            return tool_response("notebook_create", { "entry_type": "matter", "source_message_uids": ["m1"],
                "fields": {"description": "Keep the pending visit", "completion_condition": "Visit arranged"},
            }, "working-write")
        if calls == 2 or repeated:
            raise error
        if calls == 3:
            return tool_response("finish_noting", {"reason": "Kept the pending visit."})
        return response("Done.")

    before = deepcopy(parent._session_messages)
    client.chat.completions.create.side_effect = provider
    outcome = run_task(parent)
    assert outcome.committed, outcome
    assert outcome.termination["type"] == ("context_overflow" if repeated else "finish_noting")
    assert children[0]._compress_context.call_count == 0
    assert 3 <= len(wires) <= 6
    assert all(wire["messages"][:3] == wires[0]["messages"][:3] for wire in wires)
    assert all(wire["tools"] == wires[0]["tools"] for wire in wires)
    assert wires[2]["max_tokens"] <= 936
    assert all("Keep the pending visit" in str(wire["messages"]) for wire in wires[1:])
    current = database.notebook_current(parent._secretary_conversation_ref)
    assert current["payload"]["work"][0]["fields"]["description"] == "Keep the pending visit"
    assert parent._session_messages[:len(before)] == before
    assert noting_child.active_noting_task_count() == 0
    print(json.dumps({"requests": len(wires), "termination": outcome.termination,
                      "committed": outcome.committed, "compression_calls": children[0]._compress_context.call_count,
                      "working_state_preserved": True, "prefix_equal": True}, sort_keys=True))
