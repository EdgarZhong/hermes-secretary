"""Native compression capture/commit plus formal Web control and queued-loop dispatch."""
import threading
from pathlib import Path

import pytest

from agent import auxiliary_client as aux
from agent.conversation_compression import CompressionCommitFence
from tests.agent.test_compression_partial_summary import chunk
from tests.agent.test_run_agent import _mock_response
from tests.agent.test_web_compaction_control import runtime as runtime
from tests.tui_gateway.test_inflight_output_recovery import Peer
from tui_gateway import server

_native_emit = server._emit


@pytest.fixture
def hosted(runtime, monkeypatch):
    agent, db = runtime
    home = Path(db.db_path).parent
    peer = Peer()
    session = {"agent": agent, "session_key": agent.session_id, "source": "tui", "profile_home": str(home),
               "history": list(agent._session_messages), "history_lock": threading.Lock(), "history_version": 0,
               "running": False, "attached_images": [], "image_counter": 0, "cols": 80, "slash_worker": None,
               "show_reasoning": False, "tool_progress_mode": "all", "inflight_turn": None,
               "transport": peer, "created_at": 1, "close_on_disconnect": False}
    monkeypatch.setattr(server, "_sessions", {"runtime": session})
    monkeypatch.setattr(server, "_hermes_home", home)
    monkeypatch.setattr(server, "_emit", _native_emit)
    monkeypatch.setattr(server, "_session_cwd", lambda value: str(home))
    for name in ("_wire_callbacks", "_sync_agent_model_with_config", "_register_session_cwd", "_tts_stream_begin",
                 "_tts_stream_end", "_publish_session_control_snapshot", "_emit_settled_session_info",
                 "_post_turn_housekeeping", "_after_complete_turn"):
        monkeypatch.setattr(server, name, lambda *a, **k: None, raising=False)
    monkeypatch.setattr(server, "_get_usage", lambda value: {})
    monkeypatch.setattr(agent, "_cleanup_task_resources", lambda *a, **k: None)
    server._web_bind_compression("runtime", session, agent)
    yield agent, db, session, peer
    session["_closing"] = True
    thread = session.get("_run_thread")
    if thread:
        thread.join(5)
        assert not thread.is_alive()


def rpc(method, **params):
    return server.handle_request({"jsonrpc": "2.0", "id": method, "method": method,
                                  "params": {"session_id": "runtime", **params}})


@pytest.mark.parametrize("winner", ["finish", "cancel", "withdraw"])
def test_native_partial_stream_waiting_send_and_exact_operation_query(hosted, monkeypatch, winner):
    agent, db, session, peer = hosted
    entered, release = threading.Event(), threading.Event()
    fence = CompressionCommitFence()
    summary = "## Progress\nOriginal work retained.\n## Open\nRetain the current request."

    def stream():
        yield chunk(summary[:30])
        entered.set()
        assert release.wait(15)
        yield chunk(summary[30:])
        yield chunk(reason="stop")

    monkeypatch.setattr(agent.context_compressor, "_call_summary_llm",
                        lambda *a: aux.extract_content_or_reasoning(aux._aggregate_chat_stream(stream())))
    output, errors = [], []

    def run():
        try:
            with server._session_profile_runtime_scope(session):
                output.append(agent._compress_context(agent._session_messages, "Native probe root",
                    approx_tokens=100000, force=True, trigger="noting_joint_idle", commit_fence=fence))
        except Exception as exc:
            errors.append(exc)

    thread = threading.Thread(target=run)
    thread.start()
    try:
        assert entered.wait(10)
        state = rpc("session.compaction_state")["result"]
        operation = state["operation_id"]
        assert state["active"] and state["partial"]["text"] == summary[:30]
        assert rpc("session.compaction_state", operation_id="other")["result"]["state"] == "unknown"
        events = [frame["params"] for frame in peer.frames if frame.get("method") == "event"]
        delta = [event["payload"] for event in events if event["type"] == "session.compaction_delta"]
        assert delta == [{"operation_id": operation, "revision": state["partial"]["revision"],
                          "start_offset": 0, "text": summary[:30]}]
        assert not any(event["type"] in {"reasoning.delta", "message.delta"} for event in events)
        accepted = rpc("prompt.submit", input_policy="web_controlled", operation_id="waiting",
                       text="run after this maintenance")["result"]["receipt"]
        assert accepted["accepted"] and accepted["state"] == "waiting" and accepted["destination"] == "maintenance"
        assert not fence.is_cancelled
        assert rpc("session.input_state")["result"]["phase"] == "maintenance"
        if winner == "cancel":
            assert rpc("session.compaction_cancel", operation_id=operation)["result"]["outcome"] == "cancelled"
        elif winner == "withdraw":
            withdrawn = rpc("prompt.operation_withdraw", operation_id="waiting")["result"]
            assert withdrawn["outcome"] == "withdrawn" and withdrawn["receipt"]["state"] == "withdrawn"
            assert rpc("session.compaction_state", operation_id=operation)["result"]["active"]
            assert not fence.is_cancelled and not rpc("session.input_state")["result"]["waiting"]
        release.set()
        thread.join(15)

        assert not thread.is_alive() and not errors and output
        terminal = rpc("session.compaction_state", operation_id=operation)["result"]
        assert terminal["state"] == ("cancelled" if winner == "cancel" else "completed")
        assert not terminal["active"] and terminal["operation_id"] == operation
        assert rpc("prompt.operation_status", operation_id="waiting")["result"]["receipt"]["state"] == ("withdrawn" if winner == "withdraw" else "waiting")
        calls = []
        monkeypatch.setattr(agent, "_interruptible_api_call", lambda kwargs: (calls.append(kwargs) or _mock_response(content="finished", finish_reason="stop")))
        agent.context_compressor.threshold_tokens = 1000000
        server._sync_session_key_after_compress("runtime", session, clear_pending_title=False, restart_slash_worker=False)
        assert server._drain_queued_prompt("test", "runtime", session) is (winner != "withdraw")
        for _ in range(3):
            if worker := session.get("_run_thread"):
                worker.join(5)
                assert not worker.is_alive()
        assert len(calls) == (0 if winner == "withdraw" else 1)
        assert rpc("prompt.operation_status", operation_id="waiting")["result"]["receipt"]["state"] == ("withdrawn" if winner == "withdraw" else "consumed")
    finally:
        release.set()
        thread.join(15)



def test_turn_auto_compaction_hands_waiting_text_to_same_turn_before_next_api(hosted, monkeypatch):
    from copy import deepcopy
    from types import SimpleNamespace
    from agent.message_metadata import append_message
    agent, db, session, peer = hosted
    entered, release = threading.Event(), threading.Event()
    second, finish = threading.Event(), threading.Event()
    calls, turn_ids = [], []
    agent.valid_tool_names = {"probe"}
    agent.tools = [{"type": "function", "function": {"name": "probe", "description": "controlled data",
                    "parameters": {"type": "object", "properties": {}}}}]

    def provider(request):
        calls.append(deepcopy(request["messages"]))
        turn_ids.append(agent._current_turn_id)
        if len(calls) == 1:
            tool = SimpleNamespace(id="probe-1", type="function", function=SimpleNamespace(name="probe", arguments="{}"))
            return _mock_response(content=None, finish_reason="tool_calls", tool_calls=[tool])
        second.set()
        assert finish.wait(15)
        return _mock_response(content="continued main result", finish_reason="stop")

    def tool_result(assistant, messages, task_id, api_call_count):
        append_message(messages, {"role": "tool", "name": "probe", "tool_call_id": "probe-1",
                                 "content": "A predictable current report line. " * 11000})
        assert agent._flush_messages_to_session_db(messages)

    def summary(*args):
        entered.set()
        assert release.wait(15)
        return "## Progress\nOriginal work retained.\n## Open\nContinue the original request."

    monkeypatch.setattr(agent, "_interruptible_api_call", provider)
    monkeypatch.setattr(agent, "_execute_tool_calls", tool_result)
    monkeypatch.setattr(agent.context_compressor, "_call_summary_llm", summary)
    try:
        assert rpc("prompt.submit", input_policy="web_controlled", operation_id="first", text="inspect data")["result"]["receipt"]["accepted"]
        assert entered.wait(10)
        turn = agent._current_turn_id
        waiting = rpc("prompt.submit", input_policy="web_controlled", operation_id="during-auto", text="follow this instruction at the safe boundary")["result"]["receipt"]
        assert waiting["state"] == "waiting" and waiting["destination"] == "maintenance"
        release.set()
        assert second.wait(10)
        receipt = rpc("prompt.operation_status", operation_id="during-auto")["result"]["receipt"]
        assert receipt["state"] == "consumed" and receipt["turn_id"] == turn
        assert turn_ids == [turn, turn]
        assert any("follow this instruction at the safe boundary" in str(row.get("content")) for row in calls[1])
        assert session["running"] and not session.get("queued_prompt")
    finally:
        release.set()
        finish.set()
        for _ in range(3):
            if worker := session.get("_run_thread"):
                worker.join(5)
                assert not worker.is_alive()


def test_resume_old_key_during_real_rotation_reuses_live_native_parent(hosted, monkeypatch):
    from tui_gateway.transport import bind_transport, reset_transport
    agent, db, session, peer = hosted
    monkeypatch.setattr(server, "_profile_home", lambda profile: Path(db.db_path).parent)
    old_key, parent = agent.session_id, agent
    agent.compression_in_place = False
    summary_entered, resume_located = threading.Event(), threading.Event()
    publish, finish_resume = threading.Event(), threading.Event()
    errors, responses = [], []

    def summary(*args):
        summary_entered.set()
        assert publish.wait(15)
        return "## Progress\nOriginal work retained.\n## Open\nRetain the current request."

    monkeypatch.setattr(agent.context_compressor, "_call_summary_llm", summary)
    original = server._resume_follow_tip

    def follow(ctx):
        original(ctx)
        assert ctx.target == old_key
        resume_located.set()
        assert finish_resume.wait(15)

    monkeypatch.setattr(server, "_resume_follow_tip", follow)

    def compress():
        try:
            with server._session_profile_runtime_scope(session):
                agent._compress_context(agent._session_messages, "Native probe root", approx_tokens=100000, force=True, trigger="manual")
        except Exception as exc:
            errors.append(exc)

    def resume():
        token = bind_transport(peer)
        try:
            responses.append(rpc("session.resume", session_id=old_key, profile="owned", omit_messages=True, include_system_prompt=False))
        finally:
            reset_transport(token)

    compressor, reader = threading.Thread(target=compress), threading.Thread(target=resume)
    compressor.start()
    try:
        assert summary_entered.wait(10)
        reader.start()
        assert resume_located.wait(10)
        publish.set()
        compressor.join(10)
        assert not compressor.is_alive() and not errors
        assert agent.session_id != old_key and session["session_key"] == old_key
        assert db.get_compression_tip(old_key) == agent.session_id
        finish_resume.set()
        reader.join(10)
        assert not reader.is_alive()
        assert responses[0]["result"]["session_id"] == "runtime", responses
        assert responses[0]["result"]["session_key"] == agent.session_id
        assert server._sessions == {"runtime": session} and session["agent"] is parent
    finally:
        publish.set()
        finish_resume.set()
        compressor.join(10)
        if reader.ident:
            reader.join(10)


@pytest.mark.parametrize("winner", ["cancel", "commit"])
def test_opt_in_maintenance_stop_preserves_waiting_until_real_safe_boundary(hosted, monkeypatch, winner):
    agent, db, session, peer = hosted
    entered, release = threading.Event(), threading.Event()
    fence = CompressionCommitFence()
    agent.compression_in_place = True
    calls, errors = [], []
    monkeypatch.setattr(agent, "_interruptible_api_call", lambda kwargs: (calls.append(kwargs) or _mock_response(content="finished", finish_reason="stop")))
    if winner == "commit":
        begin = fence.begin_commit

        def commit(*args, **kwargs):
            result = begin(*args, **kwargs)
            if result:
                entered.set()
                assert release.wait(15)
            return result
        monkeypatch.setattr(fence, "begin_commit", commit)

    def summary(*args):
        if winner == "cancel":
            entered.set()
            assert release.wait(15)
        return "## Progress\nOriginal work retained.\n## Open\nRetain the current request."

    monkeypatch.setattr(agent.context_compressor, "_call_summary_llm", summary)

    def run():
        try:
            with server._session_profile_runtime_scope(session), server._manual_compress_turn("runtime", session):
                result, _ = agent._compress_context(agent._session_messages, "Native probe root",
                    approx_tokens=100000, force=True, trigger="manual", commit_fence=fence)
                session["history"] = result
                agent.context_compressor.threshold_tokens = 1000000
        except Exception as exc:
            errors.append(exc)

    worker = threading.Thread(target=run)
    worker.start()
    try:
        assert entered.wait(10)
        operation = rpc("session.compaction_state")["result"]["operation_id"]
        assert rpc("prompt.submit", input_policy="web_controlled", operation_id="keep-waiting", text="accepted input survives maintenance Stop")["result"]["receipt"]["state"] == "waiting"
        result = rpc("session.interrupt", input_policy="web_controlled", operation_id=operation)["result"]
        assert result["target"] == {"kind": "maintenance", "operation_id": operation, "turn_id": None}
        assert result["maintenance"]["outcome"] == ("cancelled" if winner == "cancel" else "too_late")
        assert not calls and session.get("queued_prompt") and not session.get("_turn_cancel_requested")
        release.set()
        worker.join(10)
        assert not worker.is_alive() and not errors
        for _ in range(3):
            if turn := session.get("_run_thread"):
                turn.join(5)
                assert not turn.is_alive()
        assert len(calls) == 1
        assert rpc("prompt.operation_status", operation_id="keep-waiting")["result"]["receipt"]["state"] == "consumed"
        terminal = rpc("session.compaction_state", operation_id=operation)["result"]
        assert terminal["state"] == ("cancelled" if winner == "cancel" else "completed")
    finally:
        release.set()
        worker.join(10)
