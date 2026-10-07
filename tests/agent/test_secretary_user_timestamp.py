"""Source-event timestamp contract: real-user marker, wrappers, replay stability (02 §5.6/§6.5).

Real turns on a real agent: the marker bytes the model sees, the bytes stored durably, and
the bytes replayed on the next request must agree — derived from the message's own stored
timestamp, never re-minted, and never introducing a new mid-conversation system role.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from hermes_state import SessionDB
from agent.message_metadata import (
    build_noting_task_wrapper, build_system_reminder_wrapper, build_user_reminder_wrapper,
    format_user_timestamp_marker, strip_user_timestamp_marker,
)


def mock_response(content="ok"):
    message = SimpleNamespace(content=content, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="stop")],
                           model="test/model", usage=None)


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    from run_agent import AIAgent

    client = MagicMock()
    requests: list = []

    def _create(**kwargs):
        requests.append(kwargs)
        return mock_response("noted")

    client.chat.completions.create.side_effect = _create
    monkeypatch.setattr("model_tools.get_tool_definitions", lambda **kwargs: [])
    monkeypatch.setattr("model_tools.check_toolset_requirements", lambda *a, **k: {})
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **kwargs: client)
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **k: {})
    monkeypatch.setattr("agent.title_generator.maybe_auto_title", lambda *a, **k: None)
    monkeypatch.setattr("run_agent._hermes_home", tmp_path / "hermes-home")
    (tmp_path / "hermes-home" / "logs").mkdir(parents=True, exist_ok=True)
    db = SessionDB(db_path=tmp_path / "state.db")
    db.create_session("S17", source="test")
    agent = AIAgent(
        api_key="test-key", base_url="https://openrouter.ai/api/v1", quiet_mode=True,
        skip_context_files=True, skip_memory=True, session_db=db, session_id="S17",
    )
    agent.client = client
    agent._cached_system_prompt = "You are helpful."
    agent._use_prompt_caching = False
    agent.compression_enabled = False
    agent.save_trajectories = False
    agent._secretary_conversation_ref = db.resolve_conversation_ref("S17")
    yield agent, db, client, requests
    db.close()


def _wire_user_contents(request_kwargs):
    return [m["content"] for m in request_kwargs["messages"] if m.get("role") == "user"]


def test_real_user_turn_marker_on_wire_and_in_durable_content(runtime):
    agent, db, _client, requests = runtime
    result = agent.run_conversation("hello world", persist_user_timestamp=1_700_000_000.0)
    assert result["completed"] is True
    marker = format_user_timestamp_marker(1_700_000_000.0)
    assert result["messages"][-2]["content"] == "hello world"  # live dict stays clean

    wire = _wire_user_contents(requests[0])
    assert wire == [marker + "hello world"]
    durable = db.get_messages_as_conversation("S17")
    assert durable[0]["content"] == marker + "hello world"
    assert durable[0]["timestamp"] == 1_700_000_000.0
    assert len([m for m in requests[0]["messages"] if m.get("role") == "system"]) == 1


def test_replay_regenerates_identical_marker_bytes(runtime):
    agent, db, _client, requests = runtime
    first = agent.run_conversation("first question", persist_user_timestamp=1_700_000_000.0)
    agent.run_conversation("second question", conversation_history=first["messages"],
                           persist_user_timestamp=1_700_000_060.0)

    first_turn_wire = _wire_user_contents(requests[0])[0]
    replayed = _wire_user_contents(requests[1])
    assert replayed[0] == first_turn_wire  # byte-stable prefix across turns
    assert replayed[1] == format_user_timestamp_marker(1_700_000_060.0) + "second question"
    durable = db.get_messages_as_conversation("S17")
    assert durable[0]["content"] == first_turn_wire


def test_multimodal_turn_carries_the_marker_as_first_text_part(runtime):
    agent, db, _client, requests = runtime
    content = [{"type": "text", "text": "look here"}, {"type": "text", "text": "and here"}]
    result = agent.run_conversation(content, persist_user_timestamp=1_700_000_000.0)
    assert result["completed"] is True
    marker_line = format_user_timestamp_marker(1_700_000_000.0).rstrip("\n")
    wire = _wire_user_contents(requests[0])[0]
    assert isinstance(wire, list) and wire[0] == {"type": "text", "text": marker_line}
    durable = db.get_messages_as_conversation("S17")
    assert durable[0]["content"].startswith(marker_line + "\n")


def test_marker_is_independent_of_the_noting_gate(runtime, monkeypatch):
    agent, db, _client, requests = runtime
    from secretary import noting_policy

    monkeypatch.setattr(noting_policy, "resolve_noting_settings",
                        lambda: noting_policy.disabled_noting_settings())
    agent.run_conversation("still stamped", persist_user_timestamp=1_700_000_000.0)
    assert db.get_messages_as_conversation("S17")[0]["content"].startswith(
        format_user_timestamp_marker(1_700_000_000.0))


def test_three_wrappers_are_role_user_carriers_with_the_timestamp_first_inside():
    stamp = format_user_timestamp_marker(1234.0).rstrip("\n")
    cases = (
        (build_noting_task_wrapper, "noting-task", "do the work"),
        (build_system_reminder_wrapper, "system-reminder", "due now"),
        (build_user_reminder_wrapper, "user-reminder", "stand up"),
    )
    for builder, tag, body in cases:
        carrier = builder(body, timestamp=1234.0)
        assert carrier.startswith(f"<{tag}>\n{stamp}\n")
        assert carrier.endswith(f"\n{body}\n</{tag}>")
    # The helper strips only a leading marker, for identity comparisons.
    assert strip_user_timestamp_marker(f"{stamp}\nhello") == "hello"
    assert strip_user_timestamp_marker("no marker") == "no marker"
