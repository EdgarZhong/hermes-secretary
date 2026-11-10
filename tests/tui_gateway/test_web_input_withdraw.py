"""Formal input withdrawal against real queued custody and native Pending consume."""
import threading

import pytest

from tests.tui_gateway.test_pending_native_turn import live as live
from tests.tui_gateway.test_web_controlled_input import provider_gate, receipt, rpc, send, settle_all
from tui_gateway import server


def withdraw(identity):
    return rpc("prompt.operation_withdraw", operation_id=identity)


@pytest.mark.parametrize("boundary", ["queue", "pending"])
def test_startup_withdraw_follows_exact_operation_through_pending_transfer(live, monkeypatch, boundary):
    before, release = threading.Event(), threading.Event()
    live.releases.append(release)
    original = server._run_after_agent_ready

    def ready(*args, **kwargs):
        before.set()
        assert release.wait(15)
        return original(*args, **kwargs)

    monkeypatch.setattr(server, "_run_after_agent_ready", ready)
    gate = provider_gate(live, monkeypatch)
    send("first", "original")
    assert before.wait(5)
    assert send("removed", "identical")['result']['receipt']['state'] == "waiting"
    send("retained", "identical")
    if boundary == "pending":
        release.set()
        assert gate.entered.wait(5)
        assert receipt("removed")["state"] == "pending"
    result = withdraw("removed")["result"]
    assert result["outcome"] == "withdrawn" and result["receipt"]["state"] == "withdrawn"
    assert withdraw("removed")["result"] == result
    assert receipt("retained")["state"] in {"waiting", "pending"}
    release.set()
    assert gate.entered.wait(5)
    assert receipt("retained")["state"] in {"pending", "consumed"}, live.session.get("queued_prompt")
    gate.release.set()
    settle_all(live)
    assert receipt("retained")["state"] == "consumed"
    assert receipt("removed")["state"] == "withdrawn"
    consumed = [payload for kind, _, payload in live.frames if kind == "steer.consumed"]
    assert len(consumed) == 1 and consumed[0]["pending_ids"] == [receipt("retained")["pending_id"]]
    assert len(gate.calls) == 2


@pytest.mark.parametrize("winner", ["withdraw", "consume"])
def test_native_claimed_batch_and_withdraw_have_one_disposition(live, monkeypatch, winner):
    from agent import pending_steer
    from tests.tui_gateway.test_pending_native_turn import begin
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    original = pending_steer.append_claimed_batch

    def insert(*args, **kwargs):
        if winner == "consume":
            result = original(*args, **kwargs)
        entered.set()
        assert release.wait(15)
        return original(*args, **kwargs) if winner == "withdraw" else result

    monkeypatch.setattr(pending_steer, "append_claimed_batch", insert)
    gate = begin(live, monkeypatch, tools=True)
    send("race", "one exact correction")
    gate.release.set()
    assert entered.wait(5)
    result = withdraw("race")["result"]
    assert result["outcome"] == ("withdrawn" if winner == "withdraw" else "too_late")
    assert result["receipt"]["state"] == ("withdrawn" if winner == "withdraw" else "consumed")
    release.set()
    settle_all(live)
    steers = [row for row in live.db.get_messages("stored") if row.get("display_kind") == "steer"]
    assert len(steers) == (0 if winner == "withdraw" else 1)
    assert receipt("race")["state"] == result["receipt"]["state"]


def test_failed_queue_withdrawal_keeps_custody_and_unknown_operation_is_readonly(live, monkeypatch):
    from tests.tui_gateway.test_submit_idle import image_file, native_vision
    native_vision(live, monkeypatch)
    gate = provider_gate(live, monkeypatch)
    send("first", "original")
    assert gate.entered.wait(5)
    send("image", "queued attachment", image_paths=[str(image_file(live))])
    assert withdraw("absent")["result"]["outcome"] == "not_found"
    original = server._web_write_receipt

    def fail(*args, **kwargs):
        raise OSError("controlled withdrawal storage failure")

    monkeypatch.setattr(server, "_web_write_receipt", fail)
    assert withdraw("image")["error"]["code"] == 5071
    assert live.session["queued_prompt"]["_web_operation_id"] == "image"
    monkeypatch.setattr(server, "_web_write_receipt", original)
    # The write response may be lost; original receipt remains the only proof.
    original_emit = server._emit

    def emit(kind, *args, **kwargs):
        if kind == "session.input_changed":
            raise OSError("closed peer")
        return original_emit(kind, *args, **kwargs)

    monkeypatch.setattr(server, "_emit", emit)
    withdraw("image")
    assert receipt("image")["state"] == "withdrawn"
    gate.release.set()
    settle_all(live)
    assert len(gate.calls) == 1 and not live.session.get("queued_prompt")


def test_queue_already_claimed_by_next_turn_is_honestly_too_late(live, monkeypatch):
    from tests.tui_gateway.test_submit_idle import image_file, native_vision
    native_vision(live, monkeypatch)
    gate = provider_gate(live, monkeypatch)
    send("first", "original")
    assert gate.entered.wait(5)
    send("next", "normal followup", image_paths=[str(image_file(live))])
    claimed, release = threading.Event(), threading.Event()
    live.releases.append(release)
    original = server._run_prompt_submit

    def dispatch(*args, **kwargs):
        claimed.set()
        assert release.wait(15)
        return original(*args, **kwargs)

    monkeypatch.setattr(server, "_run_prompt_submit", dispatch)
    gate.release.set()
    assert claimed.wait(5)
    result = withdraw("next")["result"]
    assert result["outcome"] == "too_late" and result["receipt"]["state"] == "submitted"
    assert not live.session.get("queued_prompt")
    release.set()
    settle_all(live)
    assert receipt("next")["state"] == "consumed" and len(gate.calls) == 2
