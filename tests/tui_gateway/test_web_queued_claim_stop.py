"""Native queued claim must not resurrect an accepted input after Main Stop."""
import threading

import pytest

from tests.tui_gateway.test_pending_native_turn import live as live
from tests.tui_gateway.test_submit_idle import image_file, native_vision
from tests.tui_gateway.test_web_controlled_input import provider_gate, receipt, rpc, send, settle_all
from tui_gateway import server


def seed_rotation(live, monkeypatch):
    from agent.prompt_cache_scope import initialize_conversation_identity
    for index in range(30):
        live.db.append_message("stored", "user", f"old question {index} " + "old words " * 120)
        live.db.append_message("stored", "assistant", f"old answer {index} " + "old result " * 120)
    live.session["history"] = live.db.get_messages_as_conversation("stored", include_row_ids=True)
    live.agent._session_messages = live.session["history"]
    initialize_conversation_identity(live.agent)
    live.agent._compression_feasibility_checked = True
    live.agent.compression_in_place = False
    monkeypatch.setattr("model_tools.get_tool_definitions", lambda **kwargs: live.agent.tools)
    monkeypatch.setattr("model_tools.check_toolset_requirements", lambda *args, **kwargs: {})
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *args, **kwargs: {})
    monkeypatch.setattr(live.agent.context_compressor, "_call_summary_llm",
                        lambda *args: "## Progress\nOld fixture work retained.\n## Open\nAnswer the current request.")


@pytest.mark.parametrize("cause", ["controlled_stop", "legacy_stop", "stop_then_new_input", "rotation"])
def test_stop_between_queue_claim_and_generation_check_never_reexecutes(live, monkeypatch, cause):
    if cause == "rotation":
        seed_rotation(live, monkeypatch)
    native_vision(live, monkeypatch)
    gate = provider_gate(live, monkeypatch)
    send("first", "original")
    assert gate.entered.wait(5)
    assert send("queued", "must not survive Main Stop", image_paths=[str(image_file(live))])["result"]["receipt"]["state"] == "waiting"
    claimed, release = threading.Event(), threading.Event()
    live.releases.append(release)
    original = server._session_uses_compute_host

    def after_claim(session, *args, **kwargs):
        if (session is live.session and threading.current_thread() is not threading.main_thread()
                and not session.get("queued_prompt") and not claimed.is_set()
                and session.get("running")):
            claimed.set()
            assert release.wait(15)
        return original(session, *args, **kwargs)

    monkeypatch.setattr(server, "_session_uses_compute_host", after_claim)
    gate.release.set()
    assert claimed.wait(5)
    if cause == "rotation":
        old_key = live.agent.session_id
        with server._session_profile_runtime_scope(live.session):
            live.agent._compress_context(live.agent._session_messages, "Test fixed root",
                                         approx_tokens=100000, force=True, trigger="mid_turn")
        assert live.agent.session_id != old_key
        with live.session["history_lock"]:
            server._sync_session_key_after_compress("runtime", live.session,
                clear_pending_title=False, restart_slash_worker=False)
    else:
        stopped = rpc("session.interrupt", **({} if cause == "legacy_stop" else {"input_policy": "web_controlled"}))["result"]
        assert stopped["status"] == "interrupted"
        if cause == "stop_then_new_input":
            assert send("new", "new explicit input after Stop")["result"]["receipt"]["accepted"]
    release.set()
    settle_all(live)
    if cause == "rotation":
        value = receipt("queued")
        assert value["state"] == "waiting" and live.session.get("queued_prompt")
    # Exercise the same formal drain invoked by the notification poller.
    server._drain_queued_prompt("post-stop-probe", "runtime", live.session)
    settle_all(live)
    assert len(gate.calls) == (2 if cause in {"rotation", "stop_then_new_input"} else 1)
    assert receipt("queued")["state"] == ("consumed" if cause == "rotation" else "cancelled")
    if cause == "stop_then_new_input":
        assert receipt("new")["state"] == "consumed"
        assert not any(isinstance(row.get("content"), list) for row in gate.calls[-1]["messages"] if row.get("role") == "user")
    assert not live.session.get("queued_prompt") and not live.session.get("queued_prompts")
