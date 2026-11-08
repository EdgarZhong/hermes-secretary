"""Early recovery aborts distinguish framework copy from preserved model output."""

import copy
import json
import time

import pytest

from hermes_state import SessionDB
from tests.agent import test_tool_batch_system_abort as batch

runtime = batch.runtime


# Exact non-empty arguments supplied by the four recovery callers.
CALLER_COPY = (
    "Operation interrupted: retrying API call after error (retry 1/3).",
    "Operation interrupted: handling API error (RuntimeError: synthetic provider unavailable).",
    "Operation interrupted: waiting for the provider to recover (cycle 1/3).",
    "Operation interrupted during retry (response time 1.0s, attempt 1/3).",
)


def _prepared(runtime, shape):
    from agent.turn_context import _bind_turn_identity

    agent = runtime.agent
    _bind_turn_identity(agent, "backoff-abort", None, None, None, None)
    agent._current_turn_timestamp = time.time()
    agent._persist_user_message_idx = 0
    messages = [{"role": "user", "content": "Synthetic task."}]
    if shape in {"partial", "tool"}:
        messages.extend([
            {"role": "assistant", "content": "", "tool_calls": [
                {"id": "done-one", "type": "function", "function": {
                    "name": "conversation_history", "arguments": "{}"}}]},
            {"role": "tool", "tool_call_id": "done-one", "name": "conversation_history",
             "content": "Real previously committed result."},
        ])
    if shape == "partial":
        # Already delivered provider text must survive even if it quotes framework copy.
        partial = "The user asked me to quote: " + CALLER_COPY[0]
        messages.append({"role": "assistant", "content": partial})
        agent._current_streamed_assistant_text = partial
    assert agent._flush_messages_to_session_db(messages)
    return messages, copy.deepcopy(runtime.db.get_messages("stored"))


def _api(agent, messages):
    from agent.turn_context import build_api_messages

    api, _ = build_api_messages(agent, messages, current_turn_user_idx=0,
        ext_prefetch_cache=None, plugin_user_context=None, moa_config=None,
        active_system_prompt="Frozen synthetic root.")
    return api


def _abort(runtime, messages, banner, *, watchdog=True):
    from agent.conversation_loop import _close_durable_failed_turn
    from agent.turn_recovery import abort_turn_on_interrupt, interruptible_backoff_sleep

    agent = runtime.agent
    if watchdog:
        agent.interrupt("Controlled watchdog abort.", hard_cancel=True, tool_reason="turn liveness watchdog")
    else:
        agent.interrupt(hard_cancel=True)
    # Actual error-handling exits call abort directly; the other recovery sites use the sleep owner.
    if "handling API error" in banner:
        result = abort_turn_on_interrupt(agent, messages, [], 2,
            abort_message="Interrupt detected during error handling, aborting retries.", interrupt_text=banner)
    else:
        result = interruptible_backoff_sleep(agent, 1, None, messages=messages,
            conversation_history=[], api_call_count=2,
            abort_message="Interrupt detected during retry wait, aborting.", interrupt_text=banner,
            activity_label="synthetic recovery backoff")
    assert result is not None and agent._interrupt_requested is False
    _close_durable_failed_turn(agent, result)
    return result


@pytest.mark.parametrize("banner", CALLER_COPY)
@pytest.mark.parametrize("shape", ["tool", "partial", "user"])
def test_watchdog_backoff_copy_is_not_model_output(runtime, banner, shape):
    from agent.conversation_loop import _close_durable_failed_turn
    from tui_gateway import server

    messages, before = _prepared(runtime, shape)
    result = _abort(runtime, messages, banner)
    saved = runtime.db.get_messages("stored")
    notices = [row for row in saved if row.get("display_kind") == "failed_turn"]
    assert result["failed"] and result["interrupted"] and not result["completed"]
    assert result["failure_reason"] == "turn_liveness_timeout"
    assert result["system_abort_notice_persisted"] is True
    assert len(notices) == 1 and notices[0]["display_metadata"]["human_only"] is True
    assert [(row["message_uid"], row["content"]) for row in saved[:len(before)]] == [
        (row["message_uid"], row["content"]) for row in before]
    ordinary_new = [row for row in saved[len(before):] if row.get("role") == "assistant"
                    and not row.get("display_kind")]
    assert not ordinary_new
    assert result.get("final_response") != banner
    raw, status, _ = server._turn_outcome(result)
    assert status == "error" and raw != banner
    api_text = json.dumps(_api(runtime.agent, messages))
    assert notices[0]["content"] not in api_text
    if shape == "partial":
        assert before[-1]["content"] in api_text
        assert result["final_response"] == before[-1]["content"]
        assert result["partial"] is True and raw == before[-1]["content"]
    else:
        assert banner not in api_text
        assert result.get("final_response") in (None, "")
    if shape == "tool":
        assert saved[len(before)]["display_kind"] == "hidden"
        assert saved[len(before)]["content"] == ""
        assert "Real previously committed result." in api_text
    _close_durable_failed_turn(runtime.agent, result)
    assert len(runtime.db.get_messages("stored")) == len(saved)
    with SessionDB(runtime.db.db_path, read_only=True) as cold:
        cold_notices = [row for row in cold.get_messages("stored") if row.get("display_kind") == "failed_turn"]
        assert [row["message_uid"] for row in cold_notices] == [notices[0]["message_uid"]]
        cold_api = _api(runtime.agent, cold.get_messages_as_conversation("stored"))
        assert notices[0]["content"] not in json.dumps(cold_api)


def test_user_stop_backoff_keeps_native_cancel_semantics(runtime):
    from tui_gateway import server

    messages, before = _prepared(runtime, "tool")
    banner = CALLER_COPY[0]
    result = _abort(runtime, messages, banner, watchdog=False)
    assert result["interrupted"] and not result.get("failed") and not result.get("error")
    assert "failure_reason" not in result
    assert result["final_response"] == banner
    raw, status, _ = server._turn_outcome(result)
    assert raw == banner and status == "interrupted"
    saved = runtime.db.get_messages("stored")
    assert not [row for row in saved if row.get("display_kind") == "failed_turn"]
    assert saved[len(before)]["content"] == banner
    assert banner in json.dumps(_api(runtime.agent, messages))


def test_rejected_watchdog_observation_does_not_attribute_backoff_stop(runtime, monkeypatch):
    # Real lease generation check rejects the stale snapshot after a real commit touch.
    result = batch.run_batch(runtime, monkeypatch, stop="stale")
    assert ("stale_after_commit", False) in runtime.trace
    assert result["interrupted"] and not result["failed"]
    assert "failure_reason" not in result
    assert not [row for row in runtime.saved if row.get("display_kind") == "failed_turn"]
