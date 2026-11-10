"""Real RPC, native Loop, SQLite and provider barriers for opt-in input custody."""
import threading

import pytest

from tests.tui_gateway.test_pending_native_turn import live as live, settled
from tests.agent.test_run_agent import _mock_response
from tui_gateway import server


def provider_gate(live, monkeypatch):
    from types import SimpleNamespace
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    calls = []

    def provider(kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            entered.set()
            assert release.wait(30)
        return _mock_response(content="finished", finish_reason="stop")
    monkeypatch.setattr(live.agent, "_interruptible_api_call", provider)
    return SimpleNamespace(entered=entered, release=release, calls=calls)


def settle_all(live):
    for _ in range(3):
        settled(live)


def rpc(method="prompt.submit", **params):
    return server.handle_request({"jsonrpc": "2.0", "id": method, "method": method,
                                  "params": {"session_id": "runtime", **params}})


def send(identity, text, **params):
    return rpc(input_policy="web_controlled", operation_id=identity, text=text, **params)


def receipt(identity):
    return rpc("prompt.operation_status", operation_id=identity)["result"]["receipt"]


def test_idle_and_active_inputs_use_one_native_owner_and_persist_receipts(live, monkeypatch):
    gate = provider_gate(live, monkeypatch)
    initial = send("first", "original")["result"]
    assert initial["status"] == "streaming" and initial["receipt"]["accepted"]
    assert gate.entered.wait(5)
    second = send("second", "same visible input")["result"]
    assert second["status"] == "steered"
    assert second["receipt"]["state"] == "pending"
    assert second["receipt"]["turn_id"] == live.agent._current_turn_id
    assert send("second", "same visible input")["result"]["receipt"] == second["receipt"]
    assert send("second", "conflicting text")["error"]["data"]["reason"] == "operation_conflict"
    assert len(gate.calls) == 1
    gate.release.set()
    settle_all(live)
    assert receipt("second")["state"] == "consumed"
    assert len(gate.calls) == 2
    assert live.session["running"] is False
    assert receipt("missing")["state"] == "unknown"


def test_startup_acceptance_transfers_once_when_native_identity_is_ready(live, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    original = server._run_after_agent_ready

    def ready(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(server, "_run_after_agent_ready", ready)
    gate = provider_gate(live, monkeypatch)
    assert send("first", "original")["result"]["status"] == "streaming"
    assert entered.wait(5)
    waiting = send("startup", "arrived before native ID")["result"]["receipt"]
    assert waiting["state"] == "waiting" and waiting["destination"] == "startup"
    assert rpc("session.input_state")["result"]["waiting"][0]["receipt"] == waiting
    release.set()
    assert gate.entered.wait(5)
    assert receipt("startup")["state"] in {"pending", "consumed"}
    gate.release.set()
    settle_all(live)
    assert receipt("startup")["state"] == "consumed"
    assert not live.session.get("queued_prompt")


def test_same_text_distinct_operations_and_stop_have_exact_receipts(live, monkeypatch):
    gate = provider_gate(live, monkeypatch)
    send("first", "original")
    assert gate.entered.wait(5)
    first = send("a", "original")["result"]["receipt"]
    second = send("b", "original")["result"]["receipt"]
    assert first["pending_id"] != second["pending_id"]
    assert rpc("session.interrupt")["result"]["status"] == "interrupted"
    assert receipt("a")["state"] == "cancelled"
    assert receipt("b")["state"] == "cancelled"
    gate.release.set()
    settled(live)
    assert len(gate.calls) == 1


@pytest.mark.parametrize("controlled", [False, True])
def test_startup_stop_does_not_wait_for_cold_build(live, monkeypatch, controlled):
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    original = server._run_after_agent_ready

    def ready(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(server, "_run_after_agent_ready", ready)
    send("first", "original")
    assert entered.wait(5)
    send("next", "queued during build")
    assert rpc("session.interrupt", **({"input_policy": "web_controlled"} if controlled else {}))["result"]["status"] == "interrupted"
    assert receipt("next")["state"] == "cancelled"
    assert live.session["_turn_cancel_requested"]
    release.set()
    settled(live)


def test_foreign_profile_cannot_query_or_submit_owned_input(live, monkeypatch):
    monkeypatch.setattr(server, "_profile_home", lambda name: live.home / "other")
    assert send("foreign", "never accepted", profile="foreign")["error"]["code"] == 4003
    assert rpc("prompt.operation_status", operation_id="foreign", profile="foreign")["error"]["code"] == 4003
    assert rpc("session.interrupt", input_policy="web_controlled", profile="foreign")["error"]["code"] == 4003


@pytest.mark.parametrize("failure", ["ensure_false", "write_raise", "write_none"])
def test_rejected_storage_never_leaves_an_executable_queue(live, monkeypatch, failure):
    gate = provider_gate(live, monkeypatch)
    send("first", "original")
    assert gate.entered.wait(5)
    if failure == "ensure_false":
        monkeypatch.setattr(server, "_ensure_session_db_row", lambda session: False)
    elif failure == "write_none":
        monkeypatch.setattr(server, "_write_submit_user_row", lambda *a, **k: None)
    else:
        def failed(*args, **kwargs):
            raise OSError("controlled storage failure")
        monkeypatch.setattr(server, "_write_submit_user_row", failed)
    rejected = send("rejected", "must never execute")
    assert rejected["error"]["data"]["accepted"] is False
    assert not live.session.get("queued_prompt")
    assert receipt("rejected")["accepted"] is False
    gate.release.set()
    settle_all(live)
    assert len(gate.calls) == 1


@pytest.mark.parametrize("failure", ["notification", "receipt_projection"])
def test_notification_failure_keeps_durable_acceptance_and_retry_is_readonly(live, monkeypatch, failure):
    gate = provider_gate(live, monkeypatch)
    send("first", "original")
    assert gate.entered.wait(5)
    previous = server._emit

    def emit(kind, *args, **kwargs):
        if kind == "session.input_changed":
            raise OSError("closed transport")
        return previous(kind, *args, **kwargs)

    monkeypatch.setattr(server, "_emit", emit)
    if failure == "receipt_projection":
        def fail_projection(*args, **kwargs):
            raise OSError("controlled receipt projection failure")
        monkeypatch.setattr(server, "_web_write_receipt", fail_projection)
    accepted = send("accepted", "retained despite notification failure")["result"]["receipt"]
    assert accepted["accepted"] and accepted["state"] == "pending"
    assert send("accepted", "retained despite notification failure")["result"]["receipt"] == accepted
    gate.release.set()
    settle_all(live)
    assert receipt("accepted")["state"] == "consumed"
    assert len(gate.calls) == 2


@pytest.mark.parametrize("failure", ["ensure_false", "write_raise", "write_none"])
def test_idle_unaccepted_storage_failure_has_no_native_dispatch(live, monkeypatch, failure):
    calls = []
    monkeypatch.setattr(live.agent, "_interruptible_api_call", lambda kwargs: calls.append(kwargs))
    if failure == "ensure_false":
        monkeypatch.setattr(server, "_ensure_session_db_row", lambda session: False)
    elif failure == "write_none":
        monkeypatch.setattr(server, "_write_submit_user_row", lambda *a, **k: None)
    else:
        def failed(*args, **kwargs):
            raise OSError("controlled idle storage failure")
        monkeypatch.setattr(server, "_write_submit_user_row", failed)
    result = send("rejected-idle", "no durable admission")
    assert result["error"]["data"]["accepted"] is False
    assert result["error"]["data"]["reason"] == "storage_unavailable"
    assert not live.session["running"] and not live.session.get("queued_prompt") and not calls
    assert receipt("rejected-idle")["accepted"] is False


def test_idle_durable_native_error_never_reverses_accepted_witness(live, monkeypatch):
    calls = []
    monkeypatch.setattr(live.agent, "_interruptible_api_call", lambda kwargs: calls.append(kwargs))

    def failed(*args, **kwargs):
        raise OSError("post-durable source observation unavailable")

    monkeypatch.setattr("tui_gateway.turn_terminal.submit_source", failed)
    result = send("durable", "recover the accepted original")
    assert "error" not in result
    assert result["result"]["receipt"]["accepted"] and result["result"]["receipt"]["state"] == "failed"
    assert not live.session["running"] and not calls
    status = rpc("prompt.operation_status", operation_id="durable")["result"]
    assert status["input"]["text"] == "recover the accepted original"
    assert send("durable", status["input"]["text"])["result"]["receipt"] == status["receipt"]
    assert not calls and not live.session.get("queued_prompt")


def test_restart_discovers_accepted_input_without_asserting_it_was_unexecuted(live, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    original = server._run_after_agent_ready

    def ready(*args, **kwargs):
        entered.set()
        assert release.wait(10)
        return original(*args, **kwargs)

    monkeypatch.setattr(server, "_run_after_agent_ready", ready)
    send("first", "original")
    assert entered.wait(5)
    send("waiting", "recover this exact raw text")
    from hermes_state import SessionDB
    reopened = SessionDB(live.db.db_path)
    try:
        fresh = {**live.session, "agent": None, "running": False, "queued_prompt": None}
        fresh.pop("queued_prompts", None)
        monkeypatch.setattr(server, "_sessions", {"runtime": fresh})
        monkeypatch.setattr("tui_gateway.event_replay.replay_epoch", lambda: "restarted-process")
        status = rpc("prompt.operation_status", operation_id="waiting")["result"]
        assert status["receipt"]["accepted"] and status["receipt"]["state"] == "unknown"
        assert status["receipt"]["reason"] == "runtime_restarted"
        assert status["input"] == {"text": "recover this exact raw text", "image_paths": []}
        unresolved = rpc("session.input_state")["result"]["unresolved"]
        assert any(item["receipt"]["operation_id"] == "waiting" and item["text"] == status["input"]["text"] for item in unresolved)
        assert reopened.get_messages("stored")
    finally:
        reopened.close()
        live.session["_closing"] = True
        release.set()
        settled(live)
