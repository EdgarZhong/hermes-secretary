"""Retained cache machinery structurally isolates snapshots from the live transcript.

A16/A22 retire the CLI/Gateway refine handlers. The underlying clone and internal
compatibility chokepoint still protect nested tool/content containers from sanitizers.
"""

from unittest.mock import MagicMock

import pytest


@pytest.fixture(autouse=True)
def _review_gate_open(monkeypatch):
    """A16 / 02 §5.1 retires the review product; these tests drive the RETAINED chokepoint with
    the retired gate opened explicitly. The closed product path is covered by
    tests/agent/test_background_review_retired.py."""
    from agent.background_review import _background_review_task_config

    monkeypatch.setattr(
        "agent.background_review.load_background_review_settings",
        lambda: (True, _background_review_task_config()))


def _agent_with_real_chokepoint():
    """MagicMock agent whose _spawn_background_review is the REAL method.

    Everything below the chokepoint (thread spawn) is captured at
    ``_spawn_background_review_now`` so no fork actually runs.
    """
    from run_agent import AIAgent

    agent = MagicMock()
    agent.valid_tool_names = {"memory"}
    agent._delegate_depth = 0
    agent._spawn_background_review = AIAgent._spawn_background_review.__get__(agent)
    return agent


def _nested_history():
    return [
        {"role": "user", "content": [{"type": "text", "text": "ask"}]},
        {
            "role": "assistant",
            "content": "ok",
            "tool_calls": [{
                "id": "call-1",
                "function": {"name": "read_file", "arguments": '{"path":"x"}'},
            }],
        },
    ]


def _assert_isolated(live, snapshot):
    assert snapshot == live  # same shape/bytes …
    for live_msg, snap_msg in zip(live, snapshot):
        assert snap_msg is not live_msg  # … but no shared containers
        for key in ("content", "tool_calls"):
            if isinstance(live_msg.get(key), (dict, list)):
                assert snap_msg[key] is not live_msg[key]
    # Mutating the snapshot the way the fork's sanitizers do must not leak.
    snapshot[0]["content"][0]["text"] = "mutated"
    snapshot[1]["tool_calls"][0]["function"]["arguments"] = "{}"
    assert live[0]["content"][0]["text"] == "ask"
    assert live[1]["tool_calls"][0]["function"]["arguments"] == '{"path":"x"}'


def test_snapshot_clone_does_not_alias_live_history():
    from agent.turn_finalizer import _clone_background_review_messages

    live = _nested_history()
    _assert_isolated(live, _clone_background_review_messages(live))


def test_retained_chokepoint_isolates_snapshot():
    agent = _agent_with_real_chokepoint()
    live = _nested_history()
    agent._spawn_background_review(live, explicit=True)
    agent._spawn_background_review_now.assert_called_once()
    snapshot = agent._spawn_background_review_now.call_args.kwargs["messages_snapshot"]
    _assert_isolated(live, snapshot)
