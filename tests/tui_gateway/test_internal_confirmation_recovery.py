"""An internal native Turn retains its real Clarify request through reattachment."""
import json
import threading
from types import SimpleNamespace

from agent.message_metadata import build_user_wrapper
from tests.agent.test_run_agent import _mock_response
from tests.tui_gateway.test_inflight_output_recovery import Peer
from tests.tui_gateway.test_pending_native_turn import live as live
from tests.tui_gateway.test_web_controlled_input import rpc, settle_all
from tools.clarify_tool import CLARIFY_SCHEMA
from tui_gateway import server, server_requests
from tui_gateway.transport import bind_transport, reset_transport

_native_emit = server._emit


class ConfirmingPeer(Peer):
    def __init__(self):
        super().__init__()
        self.question = threading.Event()

    def write(self, frame):
        result = super().write(frame)
        if frame.get("method") == "clarify":
            self.question.set()
        return result


def answer(request_id, text):
    return server.handle_request({"jsonrpc": "2.0", "id": "answer", "method": "request.answer",
                                  "params": {"id": request_id, "result": {"answers": {"q0": text}}}})


def test_internal_turn_native_confirmation_recovers_and_retired_request_cannot_answer_new(live, monkeypatch):
    parent, session = live.agent, live.session
    first, resumed = ConfirmingPeer(), ConfirmingPeer()
    session["transport"] = first
    monkeypatch.setattr(server, "_emit", _native_emit)
    parent.clarify_callback = server._agent_cbs("runtime")["clarify_callback"]
    parent.tools = [{"type": "function", "function": CLARIFY_SCHEMA}]
    parent.valid_tool_names = {"clarify"}
    calls = []

    def provider(kwargs):
        calls.append(kwargs)
        if len(calls) % 2:
            tool = SimpleNamespace(id=f"clarify-{len(calls)}", type="function", function=SimpleNamespace(
                name="clarify", arguments=json.dumps({"questions": [{"question": "Continue internal work?", "choices": ["Continue", "Stop"]}]})))
            return _mock_response(content=None, finish_reason="tool_calls", tool_calls=[tool])
        return _mock_response(content="confirmed internal work", finish_reason="stop")

    monkeypatch.setattr(parent, "_interruptible_api_call", provider)
    try:
        assert server._notif_claim_turn(session)
        server._notif_submit("internal", "runtime", session, build_user_wrapper("heartbeat", "self check"), "internal confirmation probe")
        assert first.question.wait(5)
        old = server_requests.open_requests("runtime")[0]
        assert old["method"] == "clarify"
        server._detach_session_transport(session, first)
        first._closed = True
        token = bind_transport(resumed)
        try:
            activated = rpc("session.activate", omit_messages=True)["result"]
            assert activated["session_id"] == "runtime" and activated["running"]
            assert activated["open_requests"] == [old]
            assert server_requests.open_requests("other-runtime") == []
            assert answer(old["id"], "Continue")["result"]["status"] == "ok"
        finally:
            reset_transport(token)
        settle_all(live)
        assert parent is session["agent"] and len(calls) == 2
        assert server._notif_claim_turn(session)
        server._notif_submit("internal-next", "runtime", session, build_user_wrapper("heartbeat", "next self check"), "next internal confirmation")
        assert resumed.question.wait(5)
        current = server_requests.open_requests("runtime")[0]
        assert current["id"] != old["id"]
        assert answer(old["id"], "Stop")["result"]["status"] == "expired"
        assert server_requests.open_requests("runtime")[0]["id"] == current["id"]
        assert answer(current["id"], "Continue")["result"]["status"] == "ok"
        settle_all(live)
        assert len(calls) == 4 and not server_requests.open_requests("runtime")
    finally:
        server_requests.cancel("runtime", reason="test_cleanup")
        settle_all(live)
