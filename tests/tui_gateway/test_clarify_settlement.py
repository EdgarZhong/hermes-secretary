"""Native Clarify settlement visibility on the existing request/event channel."""
import json
import time
from pathlib import Path

import pytest

from tests.tui_gateway.test_protocol import capture as capture, server as server, _start_batch_clarify


def _cancels(frames):
    return [frame for frame in frames if frame.get("method") == "event"
            and frame["params"]["type"] == "request.cancel"]


class Peer:
    def __init__(self):
        self.frames = []

    def write(self, frame):
        self.frames.append(json.loads(json.dumps(frame)))
        return True

    def close(self):
        pass


def _wait(predicate):
    deadline = time.monotonic() + 3
    while not predicate():
        assert time.monotonic() < deadline
        time.sleep(0.001)


def test_final_lock_broadcasts_once_to_both_native_peers(capture):
    from tui_gateway import server_requests
    from tui_gateway.transport import FanoutTransport

    native, _ = capture
    primary, responder = Peer(), Peer()
    fanout = FanoutTransport(primary, responder)
    native._sessions["s1"] = {"transport": fanout, "session_key": "fixture-settlement"}
    thread, box, req = _start_batch_clarify(native, None, ["q0", "q1", "q2", "q3"])
    _wait(lambda: primary.frames and responder.frames)
    source_request = primary.frames[0]
    assert source_request == responder.frames[0] == req.frame()
    acks = []
    for index in range(4):
        ack = native.handle_request({"id": index, "method": "clarify.lock", "params": {
            "request_id": req.id, "question_id": f"q{index}", "answer": f"answer-{index}"}})
        acks.append(ack["result"])
        if index < 3:
            assert _cancels(primary.frames) == _cancels(responder.frames) == []
    thread.join(timeout=3)
    assert not thread.is_alive()
    assert box["answer"]["outcome"] == "submitted"
    assert server_requests.open_requests("s1") == []
    _wait(lambda: len(_cancels(primary.frames)) == len(_cancels(responder.frames)) == 1)
    assert _cancels(primary.frames) == _cancels(responder.frames)
    event = _cancels(primary.frames)[0]["params"]
    assert event["session_id"] == "s1" and event["seq"] > 0
    assert event["payload"] == {"id": req.id, "method": "clarify", "reason": "resolved"}
    assert native.handle_request({"id": 5, "method": "clarify.lock", "params": {
        "request_id": req.id, "question_id": "q3", "answer": "late"}})["result"] == {"status": "expired"}
    assert not server_requests.resolve_response({"id": req.id, "result": {}})
    assert len(_cancels(primary.frames)) == len(_cancels(responder.frames)) == 1
    # Export actual native request/ACK/envelopes for the Controller consumers.
    folder = Path(__file__).resolve().parents[2] / ".hermes-dev" / "fv-f06"
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "native-clients.json").write_text(json.dumps({"request": source_request, "acks": acks,
        "primary": primary.frames, "responder": responder.frames}, indent=2) + "\n")
    fanout.close()


@pytest.mark.parametrize("result,outcome", [({"answers": {"q1": "yes"}}, "submitted"), ({}, "cancelled")])
def test_direct_clarify_resolution_notifies_only_its_id(capture, result, outcome):
    from tui_gateway import server_requests
    native, buf = capture
    thread, box, req = _start_batch_clarify(native, buf, ["q0", "q1"])
    assert server_requests.lock_answer(req.id, "q0", "kept") == ["q1"]
    assert server_requests.resolve_response({"id": req.id, "result": result})
    thread.join(timeout=3)
    assert not thread.is_alive()
    assert box["answer"]["outcome"] == outcome
    assert box["answer"]["answers"]["q0"] == "kept"
    assert [event["params"]["payload"] for event in _cancels([json.loads(line) for line in buf.getvalue().splitlines()])] == [
        {"id": req.id, "method": "clarify", "reason": "resolved"}]
    assert not server_requests.resolve_response({"id": req.id, "result": result})


@pytest.mark.parametrize("path", ["lock", "response"])
def test_notification_failure_preserves_native_ack_and_wakeup(capture, monkeypatch, path):
    from tui_gateway import server_requests
    native, buf = capture
    thread, box, req = _start_batch_clarify(native, buf, ["q0"])
    calls = []

    def failed(event, sid, payload):
        calls.append((event, sid, payload))
        raise RuntimeError("observer transport failure")

    monkeypatch.setattr(server_requests, "_emit", failed)
    if path == "lock":
        assert native.handle_request({"id": 1, "method": "clarify.lock", "params": {
            "request_id": req.id, "question_id": "q0", "answer": "yes"}})["result"] == {"status": "ok", "remaining": []}
    else:
        assert server_requests.resolve_response({"id": req.id, "result": {"answers": {"q0": "yes"}}})
    thread.join(timeout=3)
    assert not thread.is_alive()
    assert box["answer"] == {"answers": {"q0": "yes"}, "outcome": "submitted"}
    assert len(calls) == 1 and calls[0][2]["id"] == req.id
    assert server_requests.open_requests("s1") == []
