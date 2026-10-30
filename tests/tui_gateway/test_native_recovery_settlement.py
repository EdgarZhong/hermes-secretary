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


def start(runtime, monkeypatch, *, source="prompt.submit_idle", steer=False, outcome="complete", ordinal=0, partial=False,
          prompt_tokens=None):
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
        response = _mock_response(content="Finished", finish_reason="stop", reasoning_content="Native reasoning")
        if prompt_tokens is not None:
            response.usage = SimpleNamespace(prompt_tokens=prompt_tokens, completion_tokens=200,
                                             total_tokens=prompt_tokens + 200)
        return response

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


def force_wire(runtime, client, previous=None):
    """Actual REST/RPC/replay envelopes for downstream App recovery verification."""
    response = client.get("/api/sessions/stored/messages", params={"recovery_view": 1, "history_sync": 1})
    assert response.status_code == 200, response.text
    rest = response.json()
    req = {"version": 1, "sync_version": 1, "profile": "default", "stored_id": "stored", "windows": [
        {"selector": rest["selector"], "receipt": rest["coverage"], "cursor": rest["sync"]["cursor"]}]}
    reply = server._methods["session.activate"]("wire", {
        "session_id": "runtime", "omit_messages": True, "recovery_view": req})
    assert "error" not in reply, reply
    base = previous or rest
    snapshot_req = {**req, "windows": [{"selector": base["selector"], "receipt": base["coverage"]}]}
    snapshot = server._methods["session.activate"]("snapshot-wire", {
        "session_id": "runtime", "omit_messages": True, "recovery_view": snapshot_req})
    assert "error" not in snapshot, snapshot
    assert snapshot["result"]["recovery_view"]["complete"]
    if previous is not None:
        assert not snapshot["result"]["recovery_view"]["windows"][0]["matched"]
    detail_ids = [str(row["id"]) for row in rest["messages"] if row.get("deferred_details")]
    details = None
    if detail_ids:
        detail_response = client.get("/api/sessions/stored/messages", params={"detail_row_ids": ",".join(detail_ids)})
        assert detail_response.status_code == 200, detail_response.text
        details = detail_response.json()
    secretary = server.handle_request({"id": "secretary", "method": "secretary.state", "params": {
        "profile": "default", "stored_session_id": "stored"}})
    assert "error" not in secretary, secretary
    return copy.deepcopy({"rest": rest, "activate": reply["result"], "activate_snapshot": snapshot["result"],
                          "details": details, "secretary": secretary["result"],
                          "events": event_replay.events_since("runtime", 0)})


@pytest.mark.parametrize("followup", [False, True])
@pytest.mark.parametrize("steer", [False, True])
def test_turn_end_force_keeps_main_settled_while_child_runs(runtime, monkeypatch, tmp_path, steer, followup):
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from hermes_cli.web_routers.sessions import manage_router
    from secretary import noting_child
    from secretary.noting_scope import bind_main_runtime
    from secretary.web_read import secretary_state
    from tests.agent.test_context_compaction_request import _summary
    from tests.secretary.test_noting_child import _tool_response

    config = runtime.home / "config.yaml"
    config.write_text(config.read_text().replace("noting:\n  enabled: false", "noting:\n  enabled: true")
                      + f"terminal:\n  cwd: {runtime.home}\n")
    bind_main_runtime(runtime.agent)
    monkeypatch.setattr("hermes_state.DEFAULT_DB_PATH", runtime.home / "state.db")
    app = FastAPI()
    app.include_router(manage_router)
    client = TestClient(app)
    entered, release = threading.Event(), threading.Event()
    workers = []
    spawn = noting_child.spawn_noting_task

    def track(*args, **kwargs):
        worker = spawn(*args, **kwargs)
        workers.append(worker)
        return worker

    def child_provider(kwargs):
        entered.set()
        assert release.wait(10)
        return _tool_response("finish_noting", {"reason": "Reviewed"}, "finish")

    build_child = noting_child.build_noting_child

    def controlled_child(*args, **kwargs):
        child = build_child(*args, **kwargs)
        child._disable_streaming = True
        child._interruptible_api_call = child_provider
        return child

    monkeypatch.setattr(noting_child, "spawn_noting_task", track)
    monkeypatch.setattr(noting_child, "build_noting_child", controlled_child)
    gate = start(runtime, monkeypatch, steer=steer, prompt_tokens=63_900)
    runtime.agent.context_compressor.context_length = 130_000
    runtime.agent.context_compressor.threshold_tokens = 75_000
    wire = {"steer": steer, "followup": followup, "pre": force_wire(runtime, client)}
    try:
        idle = settle(runtime, gate)
        assert entered.wait(5), "Force must start a real background child"
        rows = runtime.db.get_messages("stored")
        notices = [row for row in rows if (row.get("display_metadata") or {}).get("noting_force_dispatch")]
        assert len(notices) == 1
        assert secretary_state(runtime.db, "stored")["task_state"] == "active"
        assert idle["complete"] and not idle["running"], idle
        assert not idle["state_snapshot"]["events"]
        events = event_replay.events_since("runtime", 0)
        completion = next(event["payload"] for event in events if event["type"] == "message.complete")
        receipt = completion["persisted_turn"]
        assert receipt["source_messages"][-1]["role"] == "assistant"
        assert receipt["final_assistant_row_id"] < notices[0]["id"]
        assert notices[0]["id"] not in receipt["row_ids"]
        assert any(event["type"] == "status.update" and event["payload"].get("kind") == "framework" for event in events)
        assert any(row.get("message_uid") == notices[0]["message_uid"] for row in runtime.session["history"])
        wire["active"] = force_wire(runtime, client, previous=wire["pre"]["rest"])
        if followup:
            next_gate = start(runtime, monkeypatch, ordinal=1)
            assert any(notices[0]["content"] in row.get("content", "") for row in next_gate.calls[0]["messages"])
            assert secretary_state(runtime.db, "stored")["task_state"] == "active"
            assert settle(runtime, next_gate)["complete"]
            runtime.agent.compression_in_place = True
            runtime.agent._compression_feasibility_checked = True
            monkeypatch.setattr(runtime.agent.context_compressor, "compress", _summary)
            compact = server.handle_request({"id": "compact", "method": "session.compress", "params": {
                "session_id": "runtime"}})
            assert "error" not in compact, compact
            assert compact["result"]["status"] == "compressed" and compact["result"]["removed"] > 0, compact
            assert secretary_state(runtime.db, "stored")["task_state"] == "active"
            assert activate(request(runtime.db))["complete"]
    finally:
        release.set()
        for worker in workers:
            worker.join(10)
            assert not worker.is_alive()
    assert activate(request(runtime.db))["complete"]
    wire["finished"] = force_wire(runtime, client, previous=wire["pre"]["rest"])
    client.close()
    (tmp_path / "native-force-wire.json").write_text(json.dumps(wire, ensure_ascii=False, indent=2) + "\n")


@pytest.mark.parametrize("steer", [False, True])
def test_native_final_identity_closes_before_unrelated_framework_tail(runtime, monkeypatch, steer):
    from secretary.framework_messages import publish_framework_message
    from secretary.noting_scope import bind_main_runtime

    bind_main_runtime(runtime.agent)
    gate = start(runtime, monkeypatch, steer=steer)
    # Queue through the formal push publisher while Main runs. Its native end
    # observation flushes these unrelated producers after the final output.
    for text in ("An unrelated background operation finished", "A later notification arrived"):
        assert publish_framework_message(runtime.agent, text)
    assert settle(runtime, gate)["complete"]
    rows = runtime.db.get_messages("stored")
    assert all(row["display_kind"] == "process_complete" for row in rows[-2:])
    events = event_replay.events_since("runtime", 0)
    receipt = next(event["payload"]["persisted_turn"] for event in events if event["type"] == "message.complete")
    assert receipt["final_assistant_row_id"] == rows[-3]["id"]
    assert receipt["row_ids"][-1] == rows[-3]["id"]
    assert receipt["source_messages"][-1]["message_uid"] == rows[-3]["message_uid"]
    assert [row["message_uid"] for row in runtime.session["history"]][-2:] == [row["message_uid"] for row in rows[-2:]]


@pytest.mark.parametrize("damage", ["missing", "empty", "user", "duplicate", "uncommitted", "body"])
def test_completed_native_final_identity_requires_exact_committed_output(runtime, monkeypatch, damage):
    from agent.context_compaction_request import finish_native_turn

    def damage_result(*args, **kwargs):
        result = finish_native_turn(*args, **kwargs)
        messages = result["messages"]
        mutations = {
            "missing": lambda: result.update(final_message_uid="unknown-final"),
            "empty": lambda: result.update(final_message_uid=None),
            "user": lambda: result.update(final_message_uid=messages[0]["message_uid"]),
            "duplicate": lambda: messages.append(copy.deepcopy(messages[-1])),
            "uncommitted": lambda: messages[-1].pop("_row_id"),
            "body": lambda: messages[-1].update(content="A different durable body"),
        }
        mutations[damage]()
        return result

    monkeypatch.setattr("agent.context_compaction_request.finish_native_turn", damage_result)
    gate = start(runtime, monkeypatch)
    idle = settle(runtime, gate)
    assert not idle["complete"] and idle["reason"] == "runtime_unavailable", idle


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
