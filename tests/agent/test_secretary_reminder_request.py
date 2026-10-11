"""Durable deferred Reminder batches and response-tied ACK on actual runtime seams.

Pending occurrences live in state.db, enter the live transcript before the real
assemble_api_request builder, and are acknowledged by perform_api_call only after
an actual provider response. Failure/replay retain the original due_at content.
"""

from __future__ import annotations

import json
import logging
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from hermes_state import SessionDB
from hermes_state_secretary_schedule import (
    REMINDER_STATUS_PENDING, init_secretary_schedule_schema, reminder_append_pending_conn,
    reminder_pending_count_conn,
)
from agent.turn_request_assembly import assemble_api_request
from agent.turn_api_call import perform_api_call
from secretary.reminder_request import inject_pending_reminders


def mock_response(content="ok"):
    message = SimpleNamespace(content=content, tool_calls=None)
    return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="stop")],
                           model="test/model", usage=None)


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    from run_agent import AIAgent

    client = MagicMock()
    client.chat.completions.create.return_value = mock_response("done")
    monkeypatch.setattr("model_tools.get_tool_definitions", lambda **kwargs: [])
    monkeypatch.setattr("model_tools.check_toolset_requirements", lambda *a, **k: {})
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **kwargs: client)
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **k: {})
    monkeypatch.setattr("agent.title_generator.maybe_auto_title", lambda *a, **k: None)
    monkeypatch.setattr("run_agent._hermes_home", tmp_path / "hermes-home")
    (tmp_path / "hermes-home" / "logs").mkdir(parents=True, exist_ok=True)
    db = SessionDB(db_path=tmp_path / "state.db")
    db._execute_write(lambda conn: init_secretary_schedule_schema(conn.cursor()))
    db.create_session("S17", source="test")
    db.append_message("S17", "user", "hello", message_uid="m1", timestamp=1000.0)
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
    # Stamped by the prologue in a real turn (_reset_per_turn_agent_state); the assembly
    # seam reads it for replay canonicalization.
    import time as _time
    agent._current_turn_timestamp = _time.time()
    yield agent, db, client
    db.close()


def seed_reminder(db, ref, content="submit the report", source_timestamp=1234.0):
    return db._execute_write(lambda conn: reminder_append_pending_conn(
        conn, ref, content, source_timestamp=source_timestamp, schedule_id="sched_1"))


def run_assembly(agent, messages):
    return assemble_api_request(
        agent, messages=messages, current_turn_user_idx=len(messages) - 1,
        _ext_prefetch_cache="", _plugin_user_context="", moa_config=None,
        active_system_prompt=agent._cached_system_prompt, original_user_message="hello",
        pending_moa_prepared_request=None, request_logger=logging.getLogger("test.assembly"),
    )


def run_api_call(agent, messages):
    return perform_api_call(
        agent, api_kwargs={"model": "test/model", "messages": messages},
        _original_api_kwargs=None, _llm_middleware_trace=[], _moa_prepared_request=None,
        _retry=SimpleNamespace(), thinking_spinner=None, retry_count=0, api_call_count=1,
        api_request_id="req-1", effective_task_id="task", turn_id="turn", interrupted=False,
    )


def test_pending_reminder_is_durable_and_acked_on_success(runtime):
    agent, db, _client = runtime
    ref = agent._secretary_conversation_ref
    reminder_id = seed_reminder(db, ref)
    messages = db.get_messages_as_conversation("S17")

    assembled = run_assembly(agent, messages)
    carrier = messages[-1]["content"]
    assert carrier.startswith("<deferred-reminder>\n以下提醒已到期。\n")
    assert "<timestamp>" not in carrier
    assert any(carrier in str(m.get("content")) for m in assembled.api_messages)
    assert db.get_messages("S17")[-1]["content"] == carrier
    assert agent._secretary_inflight_reminders == [reminder_id]
    assert db._execute_write(lambda conn: reminder_pending_count_conn(conn, ref)) == 1

    verdict = run_api_call(agent, assembled.api_messages)
    assert verdict.action == "fallthrough"
    assert agent._secretary_inflight_reminders == []
    assert db._execute_write(lambda conn: reminder_pending_count_conn(conn, ref)) == 0
    count = len(db.get_messages("S17"))
    run_assembly(agent, messages)
    assert len(db.get_messages("S17")) == count
    assert not agent._secretary_inflight_reminders


def test_failed_request_keeps_the_reminder_and_the_source_timestamp(runtime):
    agent, db, client = runtime
    ref = agent._secretary_conversation_ref
    seed_reminder(db, ref, content="ring the dentist", source_timestamp=2000.0)
    messages = db.get_messages_as_conversation("S17")

    assembled = run_assembly(agent, messages)
    client.chat.completions.create.side_effect = RuntimeError("provider down")
    with pytest.raises(Exception):
        run_api_call(agent, assembled.api_messages)
    assert db._execute_write(lambda conn: reminder_pending_count_conn(conn, ref)) == 1

    client.chat.completions.create.side_effect = None
    client.chat.completions.create.return_value = mock_response("done")
    retried = run_assembly(agent, messages)
    carrier = messages[-1]["content"]
    assert any(carrier in str(m.get("content")) for m in assembled.api_messages)
    assert any(carrier in str(m.get("content")) for m in retried.api_messages)
    assert len([row for row in db.get_messages("S17") if str(row["content"]).startswith("<deferred-reminder>")]) == 1

    run_api_call(agent, retried.api_messages)
    assert db._execute_write(lambda conn: reminder_pending_count_conn(conn, ref)) == 0


def test_noting_children_and_detached_forks_never_pull_reminders(runtime):
    agent, db, _client = runtime
    ref = agent._secretary_conversation_ref
    seed_reminder(db, ref)
    api_messages: list = [{"role": "user", "content": "hello"}]
    agent._secretary_noting_profile = "NOTING"
    assert inject_pending_reminders(agent, api_messages) == (0, 0)
    agent._secretary_noting_profile = None
    agent._persist_disabled = True
    assert inject_pending_reminders(agent, api_messages) == (0, 0)
    assert api_messages == [{"role": "user", "content": "hello"}]


def test_reminder_gate_follows_noting_settings(runtime, monkeypatch):
    agent, db, _client = runtime
    ref = agent._secretary_conversation_ref
    seed_reminder(db, ref)
    from secretary import noting_policy

    monkeypatch.setattr(noting_policy, "resolve_noting_settings",
                        lambda: noting_policy.disabled_noting_settings())
    api_messages: list = [{"role": "user", "content": "hello"}]
    assert inject_pending_reminders(agent, api_messages) == (0, 0)
    assert api_messages == [{"role": "user", "content": "hello"}]


def test_carrier_bytes_match_the_schedule_module_builder():
    """The §5.6 carrier format is one contract: the Schedule module's builder and the
    metadata helper must produce byte-identical wrappers."""
    from agent.message_metadata import build_system_reminder_wrapper
    from hermes_state_secretary_schedule import build_system_reminder_text

    assert build_system_reminder_text("due now", 1234.0) == build_system_reminder_wrapper(
        "due now", timestamp=1234.0
    )


def test_execution_middleware_without_provider_response_does_not_ack(runtime, monkeypatch):
    agent, db, _client = runtime
    ref = agent._secretary_conversation_ref
    seed_reminder(db, ref)
    messages = db.get_messages_as_conversation("S17")
    assembled = run_assembly(agent, messages)
    monkeypatch.setattr("hermes_cli.middleware.run_llm_execution_middleware",
                        lambda *_a, **_k: mock_response("cached local answer"))
    run_api_call(agent, assembled.api_messages)
    assert db._execute_write(lambda conn: reminder_pending_count_conn(conn, ref)) == 1
