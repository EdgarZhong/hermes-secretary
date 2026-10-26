"""Native UI submission, persistence, replay and activate after real Turn settlement."""
from __future__ import annotations

import copy
import json
import threading
from pathlib import Path
from types import SimpleNamespace

import httpx
import openai
import pytest

from secretary.heartbeat import render_heartbeat
from tests.agent.test_run_agent import _mock_response
from tests.tui_gateway.test_pending_native_turn import TOOL
from tests.tui_gateway.test_recovery_view import activate, request
from tests.tui_gateway.test_submit_idle import live as live, wait_all
from tui_gateway import event_replay, recovery_view, server

_NATIVE_EMIT = server._emit


@pytest.fixture
def runtime(live, monkeypatch):
    class Peer:
        def write(self, frame):
            live.frames.append(copy.deepcopy(frame))
            params = frame.get("params") or {}
            if params.get("type") == "steer.consumed" and (params.get("payload") or {}).get("message_uid") is None:
                handoff_seen.set()
            return True

        def close(self):
            pass

    assert Path(recovery_view.__file__).resolve() == Path(__file__).parents[2] / "tui_gateway/recovery_view.py"
    handoff_seen = threading.Event()
    live.handoff_seen = handoff_seen
    event_replay.reset_replay_state()
    live.session.update(transport=Peer(), show_reasoning=True)
    monkeypatch.setattr(server, "_emit", _NATIVE_EMIT)
    monkeypatch.setattr(server, "_fallback_session_info", lambda _session: {"model": "controlled"})
    monkeypatch.setattr(server, "profile_name_for_home", lambda _home: "default")
    monkeypatch.setattr(server, "_current_profile_name", lambda: "default")
    monkeypatch.setattr(server, "_launch_home", lambda: str(live.home))
    for name, callback in server._agent_cbs("runtime").items():
        monkeypatch.setattr(live.agent, name, callback, raising=False)
    return live


def start(runtime, monkeypatch, *, source="prompt.submit_idle", steer=False, outcome="complete", ordinal=0, partial=False):
    entered, release, second, finish = (threading.Event() for _ in range(4))
    runtime.releases.extend([release, finish])
    calls = []

    def provider(kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            if partial:
                runtime.agent._claim_stream_writer()
                runtime.agent.reasoning_callback("Partial native reasoning")
                runtime.agent.tool_gen_callback(TOOL)
            entered.set()
            assert release.wait(5)
            if steer:
                call = SimpleNamespace(id="call_probe", type="function",
                                       function=SimpleNamespace(name=TOOL, arguments="{}"))
                return _mock_response(content="Working on the request", finish_reason="tool_calls", tool_calls=[call])
        if steer:
            second.set()
            assert finish.wait(5)
        if outcome == "interrupted":
            raise InterruptedError("controlled stopped provider call")
        if outcome == "error":
            response = httpx.Response(401, request=httpx.Request("POST", "http://invalid.local/v1"))
            raise openai.AuthenticationError("controlled provider rejection", response=response, body=None)
        return _mock_response(content="Finished", finish_reason="stop", reasoning_content="Native reasoning")

    monkeypatch.setattr(runtime.agent, "_interruptible_api_call", provider)
    text = render_heartbeat("Check current matters", 1800000000 + ordinal) if source == "heartbeat" else f"User input {ordinal}"
    if source in {"heartbeat", "direct"}:
        with runtime.session["history_lock"]:
            server._set_session_running(runtime.session, True)
        assert server._run_prompt_submit(f"native-{ordinal}", "runtime", runtime.session, text)
    else:
        response = server.handle_request({"id": "native", "method": source,
                                          "params": {"session_id": "runtime", "text": text}})
        assert response.get("result", {}).get("status") == "streaming", response
    assert entered.wait(5)
    if steer:
        response = server.handle_request({"id": "steer", "method": "session.steer_pending", "params": {
            "session_id": "runtime", "turn_id": runtime.agent._current_turn_id,
            "operation_id": f"steer-{ordinal}", "text": "Additional user input"}})
        assert "result" in response, response
        release.set()
        assert second.wait(5)
    return SimpleNamespace(release=release, finish=finish, calls=calls)


def settle(runtime, gate):
    gate.release.set()
    gate.finish.set()
    wait_all(runtime)
    assert not runtime.session["running"]
    return activate(request(runtime.db))


@pytest.mark.parametrize("source", ["direct", "heartbeat", "prompt.submit", "prompt.submit_idle"])
@pytest.mark.parametrize("steer", [False, True])
def test_native_success_and_following_turn_recover_without_waiting_for_finish(runtime, monkeypatch, source, steer):
    for ordinal in range(2):
        gate = start(runtime, monkeypatch, source=source, steer=steer, ordinal=ordinal)
        active = activate(request(runtime.db))
        assert active["complete"] and active["running"]
        idle = settle(runtime, gate)
        assert idle["complete"] and not idle["running"], idle
        assert not idle["state_snapshot"]["events"]
        events = recovery_view.snapshot(runtime.session, "runtime", include_internal=True)["events"]
        assert any(event["type"] == "reasoning.available" for event in events)
        assert not any(event["type"] == "message.source_committed" for event in events)
        if steer:
            assert any(event["type"] == "tool.complete" for event in events)
            assert any(event["type"] == "steer.consumed" for event in events)
            receipt = next(event["payload"]["persisted_turn"] for event in events if event["type"] == "message.complete")
            assert receipt["complete"] is False  # preserve native single-user fast-path semantics


@pytest.mark.parametrize("damage", ["missing", "null_receipt", "null_sources", "empty_sources", "uid", "row", "role",
                                  "rows", "source", "prefix", "compression", "committed", "final"])
def test_consumed_steer_receipt_requires_its_exact_durable_suffix(runtime, monkeypatch, damage):
    gate = start(runtime, monkeypatch, steer=True)
    assert settle(runtime, gate)["complete"]
    events = runtime.session["_inflight_output"]["events"]
    payload = next(event["payload"] for event in events if event["type"] == "message.complete")
    receipt = payload["persisted_turn"]
    mutations = {
        "missing": lambda: payload.pop("persisted_turn"),
        "null_receipt": lambda: payload.update(persisted_turn=None),
        "null_sources": lambda: receipt.update(source_messages=None),
        "empty_sources": lambda: receipt.update(source_messages=[]),
        "uid": lambda: receipt["source_messages"][-1].update(message_uid="unknown"),
        "row": lambda: receipt["source_messages"][-1].update(row_id=999999),
        "role": lambda: receipt["source_messages"][-1].update(role="tool"),
        "rows": lambda: receipt.update(row_ids=receipt["row_ids"][:-1]),
        "source": lambda: receipt["source_boundary"].update(user_message_uid="unknown"),
        "prefix": lambda: receipt["source_boundary"].update(prefix_unchanged=False),
        "compression": lambda: receipt["source_boundary"].update(compression_unchanged=False),
        "committed": lambda: receipt["source_boundary"].update(all_rows_committed=False),
        "final": lambda: receipt.pop("final_assistant_row_id"),
    }
    mutations[damage]()
    result = activate(request(runtime.db))
    assert not result["complete"] and result["reason"] == "runtime_unavailable"


@pytest.mark.parametrize("event", ["message.delta", "reasoning.delta"])
def test_completed_receipt_does_not_authorize_unknown_later_output(runtime, monkeypatch, event):
    gate = start(runtime, monkeypatch, steer=True)
    assert settle(runtime, gate)["complete"]
    server._emit(event, "runtime", {"text": "unaccounted output"})
    result = activate(request(runtime.db))
    assert not result["complete"] and result["reason"] == "runtime_unavailable"


def test_completion_sources_are_probed_even_outside_the_latest_page(runtime, monkeypatch):
    gate = start(runtime, monkeypatch, source="direct")
    assert settle(runtime, gate)["complete"]
    runtime.db.append_messages_batch("stored", [{"role": "assistant", "content": f"External {i}"} for i in range(220)])
    result = activate(request(runtime.db))
    assert result["complete"] and not result["running"]
    assert not result["state_snapshot"]["events"]


@pytest.mark.parametrize("steer", [False, True])
def test_completed_reasoning_recovers_after_native_history_compaction(runtime, monkeypatch, steer):
    gate = start(runtime, monkeypatch, steer=steer)
    assert settle(runtime, gate)["complete"]
    runtime.db.archive_and_compact("stored", [{"role": "user", "content": "summary", "_compressed_summary": True}])
    state = recovery_view.snapshot(runtime.session, "runtime", include_internal=True)
    raw = recovery_view.read_view(runtime.db, "stored", "default", [], identities=recovery_view._references(state))
    assert any(row["visible"] and not row["active"] and row["compacted"] for row in raw["identities"])
    result = activate(request(runtime.db))
    assert result["complete"] and not result["running"], result
    assert not result["state_snapshot"]["events"]


def test_natural_steer_handoff_preserves_control_replay_and_recovers_followup(runtime, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    runtime.releases.append(release)
    gate = start(runtime, monkeypatch)
    original_turn = runtime.agent._current_turn_id
    response = server.handle_request({"id": "carry", "method": "session.steer_pending", "params": {
        "session_id": "runtime", "turn_id": original_turn, "operation_id": "carry", "text": "Next turn input"}})
    assert response["result"]["accepted"]

    def followup_provider(kwargs):
        entered.set()
        assert release.wait(5)
        return _mock_response(content="Followup finished", finish_reason="stop", reasoning_content="Followup reasoning")

    monkeypatch.setattr(runtime.agent, "_interruptible_api_call", followup_provider)
    gate.release.set()
    assert entered.wait(5) and runtime.handoff_seen.wait(5)
    assert runtime.agent._current_turn_id != original_turn
    carried = [event for event in event_replay.events_since("runtime", 0) if event["type"] == "steer.consumed"]
    assert len(carried) == 1
    assert carried[0]["payload"] == {"turn_id": original_turn,
        "pending_ids": [response["result"]["pending_id"]], "message_uid": None}
    active = activate(request(runtime.db))
    assert active["complete"] and active["running"], active
    assert not any(event["type"] == "steer.consumed" for event in active["state_snapshot"]["events"])
    release.set()
    wait_all(runtime)
    idle = activate(request(runtime.db))
    assert idle["complete"] and not idle["running"], idle
    assert not idle["state_snapshot"]["events"]
    assert any("Next turn input" in row["content"] for row in runtime.db.get_messages("stored") if row["role"] == "user")


@pytest.mark.parametrize("identity", ["uid", "message"])
def test_unproved_steer_message_stays_in_display_snapshot_and_is_refused(runtime, monkeypatch, identity):
    gate = start(runtime, monkeypatch)
    assert settle(runtime, gate)["complete"]
    payload = {"turn_id": runtime.agent._current_turn_id, "pending_ids": ["unknown"], "message_uid": None,
               "source_messages": None}
    if identity == "uid":
        payload["message_uid"] = "uncommitted-user"
    else:
        payload["message"] = {"role": "user", "content": "Uncommitted input", "message_uid": "unknown-user",
                              "display_kind": "steer", "display_content": "Uncommitted input"}
    server._emit("steer.consumed", "runtime", payload)
    result = activate(request(runtime.db))
    assert not result["complete"] and result["reason"] == "runtime_unavailable"


@pytest.mark.parametrize("outcome", ["error", "interrupted"])
@pytest.mark.parametrize("steer", [False, True])
def test_native_exceptional_finish_does_not_lend_old_output_to_the_next_turn(runtime, monkeypatch, outcome, steer):
    gate = start(runtime, monkeypatch, outcome=outcome, steer=steer)
    if outcome == "interrupted":
        server._interrupt_session_turn("runtime", runtime.session)
    result = settle(runtime, gate)
    completed = [event["payload"] for event in recovery_view.snapshot(runtime.session, "runtime")["events"]
                 if event["type"] == "message.complete"]
    assert completed[-1]["status"] == outcome
    assert result["complete"] and not result["running"], result
    next_gate = start(runtime, monkeypatch, ordinal=1)
    assert settle(runtime, next_gate)["complete"]


@pytest.mark.parametrize("source_method", ["prompt.submit", "prompt.submit_idle"])
@pytest.mark.parametrize("status", ["interrupted", "error"])
def test_native_constructing_then_stop_recovers_from_durable_terminal(runtime, monkeypatch, source_method, status):
    gate = start(runtime, monkeypatch, source=source_method, outcome=status, partial=True)
    active = activate(request(runtime.db))
    assert active["complete"] and active["running"]
    assert any(event["type"] == "reasoning.delta" for event in active["state_snapshot"]["events"])
    if status == "interrupted":
        server._interrupt_session_turn("runtime", runtime.session)
    idle = settle(runtime, gate)
    rows = runtime.db.get_messages("stored")
    source = next(row for row in rows if row["role"] == "user")
    terminal = source["display_metadata"]["turn_terminal"]
    assert terminal["status"] == status
    assert terminal["outputs"] == [{"kind": "reasoning", "text": "Partial native reasoning",
                                    "message_uid": terminal["outputs"][0]["message_uid"]}]
    events = recovery_view.snapshot(runtime.session, "runtime", include_internal=True)["events"]
    assert any(event["type"] == "tool.generating" for event in events)
    assert any(event["type"] == "message.user_committed" for event in events) is (source_method == "prompt.submit_idle")
    assert not any(event["type"] == "message.source_committed" for event in events)
    assert idle["complete"] and not idle["running"], idle
    assert not idle["state_snapshot"]["events"]
    next_gate = start(runtime, monkeypatch, ordinal=1)
    assert settle(runtime, next_gate)["complete"]


@pytest.mark.parametrize("status", ["interrupted", "error"])
def test_native_partial_terminal_still_recovers_after_compaction(runtime, monkeypatch, status):
    gate = start(runtime, monkeypatch, outcome=status, partial=True)
    if status == "interrupted":
        server._interrupt_session_turn("runtime", runtime.session)
    assert settle(runtime, gate)["complete"]
    runtime.db.archive_and_compact("stored", [{"role": "user", "content": "summary", "_compressed_summary": True}])
    result = activate(request(runtime.db))
    assert result["complete"] and not result["running"], result
    assert not result["state_snapshot"]["events"]


@pytest.mark.parametrize("damage", ["missing", "source", "status", "text", "uid", "incomplete", "row",
                                  "pair", "pair_uid", "turn", "stored", "unclosed", "untyped", "later", "unknown_error"])
def test_stopped_partial_requires_exact_native_terminal_and_output_owner(runtime, monkeypatch, damage):
    gate = start(runtime, monkeypatch, outcome="interrupted", partial=True)
    server._interrupt_session_turn("runtime", runtime.session)
    assert settle(runtime, gate)["complete"]
    source = next(row for row in runtime.db.get_messages("stored") if row["role"] == "user")
    metadata = source["display_metadata"]
    terminal = metadata["turn_terminal"]
    events = runtime.session["_inflight_output"]["events"]
    pair = next(event["payload"] for event in events if event["type"] == "tool.output")
    receipt = next(event["payload"]["persisted_turn"] for event in events if event["type"] == "message.complete")
    mutations = {
        "missing": lambda: metadata.pop("turn_terminal"),
        "source": lambda: terminal.update(source_message_uid="unknown"),
        "status": lambda: terminal.update(status="error"),
        "text": lambda: terminal["outputs"][0].update(text="different partial"),
        "uid": lambda: terminal["outputs"][0].update(message_uid="unknown"),
        "incomplete": lambda: terminal.update(outputs_complete=False),
        "row": lambda: receipt.update(user_row_id=999999),
        "pair": lambda: pair.update(native_payload={"name": "different"}),
        "pair_uid": lambda: pair.update(assistant_message_uid="unknown"),
        "turn": lambda: pair.update(turn_id="unknown"),
        "stored": lambda: pair.update(stored_session_id="unknown"),
        "unclosed": lambda: events.__setitem__(slice(None), [event for event in events if not (
            event["type"] == "message.output_state" and event["payload"]["state"] == "uncommitted")]),
        "untyped": lambda: events.__setitem__(slice(None), [event for event in events if event["type"] != "tool.output"]),
        "later": lambda: server._emit("reasoning.delta", "runtime", {"text": "unknown late output"}),
        "unknown_error": lambda: events.insert(-1, {"type": "error", "seq": events[-1]["seq"] - 1,
                                                   "payload": {"message": "unaccounted error"}}),
    }
    mutations[damage]()
    runtime.db._execute_write(lambda conn: conn.execute("UPDATE messages SET display_metadata=? WHERE id=?",
                                                       (json.dumps(metadata), source["id"])))
    result = activate(request(runtime.db))
    assert not result["complete"] and result["reason"] == "runtime_unavailable", result
