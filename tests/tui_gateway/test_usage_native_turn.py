"""Native prompt dispatch, real Main loop and SessionDB; provider boundary is controlled."""
import threading
import time
from types import SimpleNamespace

import pytest

from tests.agent.test_run_agent import _mock_response
from tests.tui_gateway.test_pending_native_turn import TOOL, rpc, settled
from tui_gateway import server

_NATIVE_USAGE = server._get_usage
pytest_plugins = ("tests.tui_gateway.test_pending_native_turn",)


def response(*, prompt=50, cache=20, output=5, tool=False, usage=True):
    calls = [SimpleNamespace(id="usage_probe", type="function",
                             function=SimpleNamespace(name=TOOL, arguments="{}"))] if tool else None
    return _mock_response(content=None if tool else "finished", finish_reason="tool_calls" if tool else "stop",
                          tool_calls=calls, usage={"prompt_tokens": prompt, "completion_tokens": output,
                                                  "prompt_tokens_details": {"cached_tokens": cache}} if usage else None)


def run(live, monkeypatch, replies, *, streaming=False):
    recorded = []
    def dispatch(kwargs, **kw):
        recorded.append(kwargs)
        item = replies[len(recorded) - 1]
        if isinstance(item, Exception):
            raise item
        return item
    live.agent._disable_streaming = not streaming
    if streaming:
        monkeypatch.setattr(live.agent, "_has_stream_consumers", lambda: True)
    monkeypatch.setattr(live.agent, "_interruptible_streaming_api_call" if streaming else "_interruptible_api_call", dispatch)
    assert rpc("prompt.submit", text="real user")["result"]["status"] == "streaming"
    wait_turn(live)
    return recorded


def wait_turn(live):
    # prompt.submit is deferred: its accepted receipt can arrive before _run_thread exists.
    deadline = time.monotonic() + 10
    while live.session.get("running"):
        assert time.monotonic() < deadline, "native Turn did not settle"
        threading.Event().wait(0.02)
    settled(live)


@pytest.mark.parametrize("streaming", [False, True])
def test_two_real_model_calls_one_completed_turn_and_legacy_usage(live, monkeypatch, streaming):
    monkeypatch.setattr(server, "_get_usage", _NATIVE_USAGE)
    run(live, monkeypatch, [response(tool=True), response(prompt=80, cache=30, output=9)], streaming=streaming)
    data = rpc("session.usage_detail")["result"]
    latest = data["latest_completed_turn"]
    assert latest["input_tokens"] == 80 and latest["cache_read_tokens"] == 50 and latest["output_tokens"] == 14
    assert latest["model_calls"] == 2 and latest["model_calls_source"] == "native_model_dispatch"
    assert latest["availability"] == "available" and latest["cache_hit_rate"] == pytest.approx(50 / 130)
    assert data["session_total"]["turns"] == 1
    assert data["session_total"]["input_tokens"] == live.agent.session_input_tokens == 80
    old = rpc("session.usage")["result"]
    assert old == _NATIVE_USAGE(live.agent)
    assert "latest_completed_turn" not in old and "turns" not in old
    assert len([row for row in live.db.get_messages("stored") if row["role"] == "user"]) == 1


def test_continuous_turns_keep_latest_until_real_completion(live, monkeypatch):
    run(live, monkeypatch, [response()])
    before = rpc("session.usage_detail")["result"]["latest_completed_turn"]
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    def dispatch(kwargs):
        entered.set()
        assert release.wait(5)
        return response(prompt=90, cache=40, output=8)
    monkeypatch.setattr(live.agent, "_interruptible_api_call", dispatch)
    assert rpc("prompt.submit", text="next")["result"]["status"] == "streaming"
    assert entered.wait(5)
    inflight = rpc("session.usage_detail")["result"]
    assert inflight["latest_completed_turn"] == before and inflight["session_total"]["turns"] == 1
    release.set()
    wait_turn(live)
    after = rpc("session.usage_detail")["result"]
    assert after["latest_completed_turn"]["turn_id"] != before["turn_id"]
    assert after["latest_completed_turn"]["input_tokens"] == 50
    assert after["session_total"]["input_tokens"] == 80 and after["session_total"]["turns"] == 2


def test_missing_usage_does_not_present_known_part_as_turn_total(live, monkeypatch):
    run(live, monkeypatch, [response(tool=True), response(usage=False)])
    data = rpc("session.usage_detail")["result"]
    latest = data["latest_completed_turn"]
    assert latest["availability"] == "partial" and latest["model_calls"] == 2
    assert latest["input_tokens"] is None and latest["cache_read_tokens"] is None and latest["output_tokens"] is None
    assert latest["cache_hit_rate"] is None and "missing_usage" in latest["reasons"]
    assert data["session_total"]["input_tokens"] is None
    assert live.agent.session_input_tokens == 30  # original accounting is preserved


def test_cold_history_does_not_infer_turn_count_from_user_or_steer_rows(live, monkeypatch):
    live.session["history"] = [{"role": "user", "content": "old user"},
                               {"role": "user", "content": "old steer", "display_kind": "steer"},
                               {"role": "assistant", "content": "old answer"}]
    assert rpc("session.usage_detail")["result"]["latest_completed_turn"] is None
    run(live, monkeypatch, [response()])
    data = rpc("session.usage_detail")["result"]
    assert data["session_total"]["availability"] == "unknown" and data["session_total"]["turns"] is None
    assert data["session_total"]["input_tokens"] is None
    assert data["latest_completed_turn"]["input_tokens"] == 30
    assert data["latest_completed_turn"]["model_calls"] == 1


def test_middleware_return_without_native_dispatch_is_unknown(live, monkeypatch):
    monkeypatch.setattr("hermes_cli.middleware.run_llm_execution_middleware", lambda *a, **kw: response())
    run(live, monkeypatch, [])
    latest = rpc("session.usage_detail")["result"]["latest_completed_turn"]
    assert latest["model_calls"] is None and latest["input_tokens"] is None
    assert "unobserved_dispatch" in latest["reasons"]


def test_actual_failed_retry_counts_dispatch_without_inventing_missing_tokens(live, monkeypatch):
    monkeypatch.setattr("agent.turn_api_error.compute_error_backoff", lambda *a, **kw: 0)
    run(live, monkeypatch, [TimeoutError("provider timed out"), response()])
    latest = rpc("session.usage_detail")["result"]["latest_completed_turn"]
    assert latest["model_calls"] == 2 and latest["input_tokens"] is None
    assert latest["availability"] == "partial" and "failed_dispatch" in latest["reasons"]
    assert live.agent.session_api_calls == 1


def test_retry_exhausted_real_early_return_still_ends_a_turn(live, monkeypatch):
    live.agent._api_max_retries = 1
    live.agent._auto_recovery_cycles = 0
    monkeypatch.setattr("agent.turn_api_error.compute_error_backoff", lambda *a, **kw: 0)
    run(live, monkeypatch, [ValueError("invalid request")])
    data = rpc("session.usage_detail")["result"]
    assert data["session_total"]["turns"] == 1
    assert data["latest_completed_turn"]["model_calls"] == 1
    assert data["latest_completed_turn"]["input_tokens"] is None


def test_native_fallback_refund_does_not_erase_actual_dispatch(live, monkeypatch):
    # Gateway refreshes the native fallback config at every real turn, so configure its source.
    (live.home / "config.yaml").write_text(
        "noting:\n  enabled: false\ncompression:\n  enabled: false\n"
        "model:\n  default: test/model\n  base_url: http://invalid.local/v1\n  context_length: 256000\n"
        "fallback_providers:\n  - provider: openai\n    model: fallback/model\n"
        "    base_url: http://invalid.local/v1\n    api_key: test-only\n")
    client = SimpleNamespace(base_url="http://invalid.local/v1", api_key="test-only")
    monkeypatch.setattr("agent.auxiliary_client.resolve_provider_client", lambda *a, **kw: (client, "fallback/model"))
    monkeypatch.setattr("agent.model_metadata.get_model_context_length", lambda *a, **kw: 256000)
    monkeypatch.setattr("agent.usage_pricing.fetch_endpoint_model_metadata", lambda *a, **kw: {})
    run(live, monkeypatch, [ValueError("invalid request"), response()])
    assert live.agent._provider_fallback_active is True and live.agent.model == "fallback/model"
    latest = rpc("session.usage_detail")["result"]["latest_completed_turn"]
    assert latest["model_calls"] == 2 and latest["input_tokens"] is None
    assert "failed_dispatch" in latest["reasons"]


def test_budget_exhaustion_summary_calls_are_explicitly_unknown(live, monkeypatch):
    live.agent.max_iterations = 1
    live.agent.iteration_budget.max_total = 1
    calls = run(live, monkeypatch, [response(tool=True), response()])
    assert len(calls) == 2
    latest = rpc("session.usage_detail")["result"]["latest_completed_turn"]
    assert latest["model_calls"] is None and latest["input_tokens"] is None
    assert "unobserved_iteration_summary" in latest["reasons"]


def test_preserved_verification_finalizer_does_not_mark_a_summary_dispatch(live):
    import logging
    from agent.turn_finalizer import _resolve_budget_fallback
    from agent.usage_read import begin_main_turn_usage, finish_main_turn_usage, main_usage_detail
    begin_main_turn_usage(live.agent, "preserved", has_prior_history=False)
    outcome = _resolve_budget_fallback(
        live.agent, final_response=None, api_call_count=live.agent.max_iterations,
        interrupted=False, failed=False, messages=[], _turn_exit_reason="budget_exhausted",
        _pending_verification_response="already verified", _pending_verification_response_previewed=False,
        logger=logging.getLogger(__name__))
    assert outcome[0] == "already verified" and outcome[2] is True
    finish_main_turn_usage(live.agent, "preserved", {})
    latest = main_usage_detail(live.agent)["latest_completed_turn"]
    assert latest["model_calls"] == 0 and latest["input_tokens"] == 0
    assert "unobserved_iteration_summary" not in latest["reasons"]


def test_real_uncaught_prologue_exception_is_unknown_and_read_only(live, monkeypatch):
    def fail(agent):
        raise RuntimeError("controlled prologue failure")
    monkeypatch.setattr("agent.turn_context._reset_per_turn_agent_state", fail)
    run(live, monkeypatch, [])
    before = live.db.get_messages("stored")
    history = list(live.session["history"])
    data = rpc("session.usage_detail")["result"]
    assert data["latest_turn_availability"] == "unknown" and data["session_total"]["turns"] == 1
    assert "turn_exception" in data["latest_completed_turn"]["reasons"]
    assert live.db.get_messages("stored") == before and live.session["history"] == history


def test_usage_reads_do_not_mutate_database_history_or_start_a_turn(live, monkeypatch):
    run(live, monkeypatch, [response()])
    with live.db._read_ctx() as connection:
        before = tuple(connection.iterdump())
    history = list(live.session["history"])
    counts = (live.agent.session_input_tokens, live.agent.session_api_calls)
    for _ in range(3):
        assert rpc("session.usage_detail")["result"]["session_total"]["turns"] == 1
    with live.db._read_ctx() as connection:
        assert tuple(connection.iterdump()) == before
    assert live.session["history"] == history and not live.session["running"]
    assert counts == (live.agent.session_input_tokens, live.agent.session_api_calls)


def test_owner_profile_and_hosted_projection(live, monkeypatch):
    monkeypatch.setattr(server, "_profile_home", lambda profile: live.home / "foreign")
    assert rpc("session.usage_detail", profile="wrong")["error"]["code"] == 4001
    live.session["_hosted_room_task"] = {"task_id": "hidden"}
    data = rpc("session.usage_detail")["result"]
    assert data["session_total"]["source"] == "unknown"
    assert data["session_total"]["reasons"] == ["hosted_owner_unavailable"]
    assert rpc("session.usage_detail", extra="reject")["error"]["code"] == 4000
    assert server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "session.usage_detail",
                                  "params": {"session_id": "foreign"}})["error"]["code"] == 4001
