"""Native preflight/admission race and image custody through the same queued witness."""
import threading

from agent.message_metadata import build_user_wrapper
from tests.tui_gateway.test_pending_native_turn import live as live
from tests.tui_gateway.test_submit_idle import image_file, native_vision
from tests.tui_gateway.test_web_controlled_input import send, receipt, provider_gate, settle_all
from tui_gateway import server


def test_idle_preflight_loses_to_internal_claim_and_atomically_becomes_pending(live, monkeypatch):
    before, proceed = threading.Event(), threading.Event()
    live.releases.append(proceed)
    original = server._web_idle_input

    def preflight(*args):
        before.set()
        assert proceed.wait(15)
        return original(*args)

    monkeypatch.setattr(server, "_web_idle_input", preflight)
    gate = provider_gate(live, monkeypatch)
    responses = []
    caller = threading.Thread(target=lambda: responses.append(send("stale-idle", "explicit input must not be rejected")))
    caller.start()
    try:
        assert before.wait(5)
        # Match the actual resume lock order while the Send is still in preflight.
        with server._session_resume_lock:
            assert live.session["history_lock"].acquire(timeout=1)
            live.session["history_lock"].release()
        assert server._notif_claim_turn(live.session)
        server._notif_submit("internal", "runtime", live.session, build_user_wrapper("heartbeat", "internal run"), "internal probe")
        assert gate.entered.wait(5)
        proceed.set()
        caller.join(5)
        assert not caller.is_alive() and "error" not in responses[0]
        assert responses[0]["result"]["receipt"]["state"] == "pending"
        assert responses[0]["result"]["receipt"]["turn_id"] == live.agent._current_turn_id
        gate.release.set()
        settle_all(live)
        assert receipt("stale-idle")["state"] == "consumed" and len(gate.calls) == 2
    finally:
        proceed.set()
        gate.release.set()
        caller.join(5)
        settle_all(live)


def test_active_images_use_normal_followup_and_ack_retry_does_not_reopen_deleted_file(live, monkeypatch):
    native_vision(live, monkeypatch)
    gate = provider_gate(live, monkeypatch)
    path = image_file(live)
    assert send("first", "original")["result"]["status"] == "streaming"
    assert gate.entered.wait(5)
    image = send("image", "inspect this image", image_paths=[str(path)])["result"]["receipt"]
    assert image["state"] == "waiting" and image["destination"] == "followup" and image["pending_id"] is None
    assert live.session["queued_prompt"]["image_paths"] == [str(path)]
    gate.release.set()
    settle_all(live)
    assert len(gate.calls) == 2

    users = [row for row in gate.calls[1]["messages"] if row.get("role") == "user"]
    assert any(isinstance(row.get("content"), list) and any(part.get("type") == "image_url" for part in row["content"])
               for row in users)
    assert receipt("image")["state"] == "consumed"
    path.unlink()
    repeated = send("image", "inspect this image", image_paths=[str(path)])["result"]["receipt"]
    assert repeated["accepted"] and repeated["state"] == "consumed"
    assert len(gate.calls) == 2



def test_build_failure_gives_all_accepted_custody_terminal_receipts_without_dispatch(live, monkeypatch):
    ready = threading.Event()
    live.session["agent_ready"] = ready
    calls = []
    monkeypatch.setattr(live.agent, "_interruptible_api_call", lambda kwargs: calls.append(kwargs))
    assert send("first", "accepted before build result")["result"]["receipt"]["accepted"]
    assert send("waiting-build", "accepted while build pending")["result"]["receipt"]["state"] == "waiting"
    live.session["agent_error"] = "controlled external build failure"
    ready.set()
    settle_all(live)
    assert receipt("first")["state"] == "failed"
    assert receipt("waiting-build")["state"] == "failed"
    assert not live.session.get("queued_prompt") and not calls
