"""Native Stop commit wait cannot cancel a later real Loop on the same Agent."""
import threading
from types import SimpleNamespace

from agent.conversation_compression import CompressionCommitFence
from tests.agent.test_run_agent import _mock_response
from tests.tui_gateway.test_pending_native_turn import live as live
from tests.tui_gateway.test_web_controlled_input import send, rpc, settle_all
from tools.interrupt import is_thread_interrupted
from tui_gateway import server


def test_native_target_rechecks_after_real_commit_wait_before_all_side_effects(live, monkeypatch):
    parent = live.agent
    old_ready, finish_old, new_ready, finish_new = [threading.Event() for _ in range(4)]
    live.releases.extend([finish_old, finish_new])
    calls = []

    def provider(kwargs):
        calls.append(kwargs)
        ready, finish = (old_ready, finish_old) if len(calls) == 1 else (new_ready, finish_new)
        ready.set()
        assert finish.wait(15)
        return _mock_response(content="finished", finish_reason="stop")

    monkeypatch.setattr(parent, "_interruptible_api_call", provider)
    send("old", "old native request")
    assert old_ready.wait(5)
    old_turn = parent._current_turn_id
    fence = CompressionCommitFence()
    assert fence.begin_commit()
    parent._active_compression_commit_fence = fence
    wait_started, wait_completed, finish_stop = [threading.Event() for _ in range(3)]
    live.releases.append(finish_stop)
    cancel = CompressionCommitFence.cancel_before_commit

    def wait(current, *args, **kwargs):
        if current is fence:
            wait_started.set()
        value = cancel(current, *args, **kwargs)
        if current is fence:
            wait_completed.set()
            assert finish_stop.wait(15)
        return value

    monkeypatch.setattr(CompressionCommitFence, "cancel_before_commit", wait)
    results = []
    stop = threading.Thread(target=lambda: results.append(parent.hard_interrupt(require_turn_id=old_turn)))
    stop.start()
    try:
        assert wait_started.wait(5)
        fence.finish_commit()
        assert wait_completed.wait(5)
        finish_old.set()
        settle_all(live)

        send("new", "later native request must survive the old Stop")
        assert new_ready.wait(5)
        assert parent._current_turn_id != old_turn
        aborts, children = [], []
        parent._active_request_abort = lambda reason: aborts.append(reason)
        child = SimpleNamespace(hard_interrupt=lambda *a, **k: children.append("stopped"))
        with parent._active_children_lock:
            parent._active_children.append(child)
        finish_stop.set()
        stop.join(5)
        assert not stop.is_alive() and results == [False]
        assert not aborts and not children
        assert not parent._hard_interrupt_requested.is_set()
        assert not is_thread_interrupted(parent._execution_thread_id)
        assert live.session["running"]
        stale = rpc("session.interrupt", input_policy="web_controlled", turn_id=old_turn)["result"]
        assert stale["status"] == "not_interrupted" and stale["target"]["turn_id"] == old_turn
        assert not aborts and not children and live.session["running"]
    finally:
        finish_old.set()
        finish_new.set()
        finish_stop.set()
        if fence.commit_in_flight:
            fence.finish_commit()
        parent._active_request_abort = None
        with parent._active_children_lock:
            parent._active_children.clear()
        stop.join(5)
        settle_all(live)



def test_rpc_target_change_before_native_stop_preserves_new_pending(live, monkeypatch):
    import secretary.adaptive_runtime as adaptive
    observations, observe = [], adaptive.composer_cancel

    def composer(*args, **kwargs):
        observations.append(live.agent._current_turn_id)
        return observe(*args, **kwargs)

    monkeypatch.setattr(adaptive, "composer_cancel", composer)
    first, release_first, second, release_second = [threading.Event() for _ in range(4)]
    live.releases.extend([release_first, release_second])
    calls = []

    def provider(kwargs):
        calls.append(kwargs)
        ready, release = (first, release_first) if len(calls) == 1 else (second, release_second)
        ready.set()
        assert release.wait(15)
        return _mock_response(content="finished", finish_reason="stop")

    monkeypatch.setattr(live.agent, "_interruptible_api_call", provider)
    send("first", "old turn")
    assert first.wait(5)
    old_turn = live.agent._current_turn_id
    captured, apply_stop = threading.Event(), threading.Event()
    live.releases.append(apply_stop)
    original = server._web_prepare_stop

    def prepare(*args):
        result = original(*args)
        captured.set()
        assert apply_stop.wait(15)
        return result

    monkeypatch.setattr(server, "_web_prepare_stop", prepare)
    results = []
    stop = threading.Thread(target=lambda: results.append(rpc("session.interrupt", input_policy="web_controlled", turn_id=old_turn)))
    stop.start()
    try:
        assert captured.wait(5)
        release_first.set()
        settle_all(live)
        send("second", "new turn")
        assert second.wait(5)
        pending = send("new-pending", "do not clear this newer input")["result"]["receipt"]
        assert pending["state"] == "pending"
        apply_stop.set()
        stop.join(5)
        assert not stop.is_alive() and results[0]["result"]["status"] == "not_interrupted"
        assert live.session["running"] and not live.agent._hard_interrupt_requested.is_set()
        assert rpc("prompt.operation_status", operation_id="new-pending")["result"]["receipt"]["state"] == "pending"
        assert not observations
    finally:
        apply_stop.set()
        release_first.set()
        release_second.set()
        stop.join(5)
        settle_all(live)


def test_late_session_cleanup_cannot_cancel_new_confirmation_or_retire_its_marker(live, monkeypatch):
    import json
    from tests.tui_gateway.test_internal_confirmation_recovery import ConfirmingPeer, answer
    from tools.clarify_tool import CLARIFY_SCHEMA
    from tui_gateway import server_requests
    parent, session = live.agent, live.session
    peer = ConfirmingPeer()
    session["transport"] = peer
    parent.clarify_callback = server._agent_cbs("runtime")["clarify_callback"]
    parent.tools = [{"type": "function", "function": CLARIFY_SCHEMA}]
    parent.valid_tool_names = {"clarify"}
    first, release_first, native_stopped, finish_stop = [threading.Event() for _ in range(4)]
    live.releases.extend([release_first, finish_stop])
    calls = []

    def provider(kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            first.set()
            assert release_first.wait(15)
        if len(calls) == 2:
            tool = SimpleNamespace(id="new-confirm", type="function", function=SimpleNamespace(name="clarify",
                arguments=json.dumps({"questions": [{"question": "New Turn confirmation?", "choices": ["Continue"]}]})))
            return _mock_response(content=None, finish_reason="tool_calls", tool_calls=[tool])
        return _mock_response(content="finished", finish_reason="stop")

    monkeypatch.setattr(parent, "_interruptible_api_call", provider)
    send("old", "original Turn")
    assert first.wait(5)
    old_turn, interrupt = parent._current_turn_id, parent.hard_interrupt

    def pause_after_native(*args, **kwargs):
        result = interrupt(*args, **kwargs)
        native_stopped.set()
        assert finish_stop.wait(15)
        return result

    monkeypatch.setattr(parent, "hard_interrupt", pause_after_native)
    results = []
    stop = threading.Thread(target=lambda: results.append(rpc("session.interrupt", input_policy="web_controlled", turn_id=old_turn)))
    stop.start()
    try:
        assert native_stopped.wait(5)
        release_first.set()
        settle_all(live)
        send("new", "a later Turn needs confirmation")
        assert peer.question.wait(5)
        current = server_requests.open_requests("runtime")[0]
        send("new-pending", "keep this input")
        marker = session.get("_active_turn_marker_key")
        assert marker and parent._current_turn_id != old_turn
        finish_stop.set()
        stop.join(5)
        assert not stop.is_alive() and results[0]["result"]["status"] == "interrupted"
        assert server_requests.open_requests("runtime")[0]["id"] == current["id"]
        assert session["_active_turn_marker_key"] == marker
        assert rpc("prompt.operation_status", operation_id="new-pending")["result"]["receipt"]["state"] == "pending"
        assert not parent._hard_interrupt_requested.is_set()
        assert answer(current["id"], "Continue")["result"]["status"] == "ok"
        settle_all(live)
    finally:
        release_first.set()
        finish_stop.set()
        server_requests.cancel("runtime", reason="test_cleanup")
        stop.join(5)
        settle_all(live)
