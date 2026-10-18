"""Native writes, live snapshots and global runtime invalidation across reconnects."""
from __future__ import annotations

import contextlib
import copy
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from tui_gateway import event_replay, server
from tui_gateway.contracts.sessions import LiveSessionSnapshot, SessionActiveListResult
from tui_gateway.transport import bind_transport, reset_transport


class Peer:
    def __init__(self):
        self.frames = []
        self.received = threading.Event()

    def write(self, frame):
        self.frames.append(copy.deepcopy(frame))
        self.received.set()
        return True


def install(monkeypatch, tmp_path):
    peer = Peer()
    monkeypatch.setattr(server, "_sessions", {})
    monkeypatch.setattr(server, "_live_transports", {peer})
    monkeypatch.setattr(server, "_launch_home", lambda: str(tmp_path / "main"))
    monkeypatch.setattr(server, "_current_profile_name", lambda: "main")
    monkeypatch.setattr(server, "profile_name_for_home", lambda home: Path(home).name if home else "main")
    monkeypatch.setattr(server, "_profile_home", lambda profile: str(tmp_path / profile))
    monkeypatch.setattr(server, "_session_live_title", lambda session, key: key)
    monkeypatch.setattr(server, "_fallback_session_info", lambda session: {"model": "controlled"})
    event_replay.reset_replay_state()
    return peer


def runtime(home, sid="runtime", stored="same-stored-id"):
    session = {"_sid": sid, "agent": SimpleNamespace(model="controlled", session_id=stored),
               "session_key": stored, "history": [], "history_lock": threading.Lock(),
               "created_at": 1.0, "last_active": 1.0, "running": False,
               "profile_home": str(home), "transport": Peer()}
    server._sessions[sid] = session
    return session


def begin(session, text="Reminder carrier"):
    with session["history_lock"]:
        server._set_session_running(session, True)
        server._start_inflight_turn(session, text)
    server._emit("message.start", session["_sid"])


def live_snapshot(session):
    return server._live_session_payload(session["_sid"], session, omit_messages=True)


def emit_typed(session, kind, payload, scope):
    """Controlled child relay uses the real legacy/typed seam and parent seq translation."""
    sid = session["_sid"]
    legacy = server._event_frame(kind, sid, payload)
    legacy["params"]["seq"] = 17
    server.write_json(legacy)
    paired = {**scope, "native_type": kind, "native_payload": payload, "source_event_seq": 17}
    event_type = "message.output_delta"
    if kind.startswith("tool."):
        event_type = "tool.output"
        paired = {key: value for key, value in scope.items() if key != "message_uid"}
        paired.update(assistant_message_uid=scope["message_uid"], tool_call_uid="actual-tool-uid",
                      phase=kind.split(".")[1], native_payload=payload, source_event_seq=17)
    frame = server._event_frame(event_type, sid, paired)
    frame["params"]["seq"] = 18
    server.write_json(frame)


def long_turn(session):
    begin(session)
    sid = session["_sid"]
    scope = {"turn_id": "actual-turn", "stored_session_id": session["session_key"],
             "conversation_ref": "controlled-conversation", "message_uid": "actual-assistant"}
    frame = server._event_frame("message.output_state", sid, {**scope, "state": "open", "api_request_id": "request", "stream_writer_token": 1})
    frame["params"]["seq"] = 1
    server.write_json(frame)
    server._emit("thinking.delta", sid, {"text": "Checking commitments. "})
    emit_typed(session, "tool.start", {"tool_id": "running-tool", "name": "terminal", "args": {"command": "controlled"}}, scope)
    for _ in range(600):
        emit_typed(session, "reasoning.delta", {"text": "r"}, scope)
    return scope


def test_full_current_turn_survives_ring_eviction_with_running_tool(monkeypatch, tmp_path):
    install(monkeypatch, tmp_path)
    session = runtime(tmp_path / "exam")
    long_turn(session)
    assert event_replay.is_truncated("runtime", 0)
    payload = live_snapshot(session)
    LiveSessionSnapshot.model_validate(payload)
    state = payload["state_snapshot"]
    assert state["complete"] is True
    assert state["epoch"] == event_replay.replay_epoch()
    events = state["events"]
    assert [event["seq"] for event in events] == sorted({event["seq"] for event in events})
    assert all(event["session_id"] == "runtime" and event["seq"] <= state["seq"] for event in events)
    assert events[0]["type"] == "message.start"
    assert [event["payload"]["text"] for event in events if event["type"] == "reasoning.delta"] == ["r" * 600]
    assert [event["payload"]["text"] for event in events if event["type"] == "thinking.delta"] == ["Checking commitments. "]
    assert any(event["type"] == "tool.start" for event in events)
    assert not any(event["type"] == "tool.start" for event in event_replay.events_since("runtime", 0))
    assert not any(event["type"] == "tool.complete" for event in events)
    assert len(events) < 12  # text segments, not a second token-event journal
    for event in events:
        if event["type"] in {"message.output_delta", "tool.output"}:
            source = next(item for item in events if item["seq"] == event["payload"]["source_event_seq"])
            assert source["payload"] == event["payload"]["native_payload"]
    assert payload["running"] is True


def test_snapshot_then_live_replay_is_an_exact_cut(monkeypatch, tmp_path):
    install(monkeypatch, tmp_path)
    session = runtime(tmp_path / "exam")
    scope = long_turn(session)
    snapshot = live_snapshot(session)["state_snapshot"]
    emit_typed(session, "reasoning.delta", {"text": "after"}, scope)
    server._emit("tool.complete", "runtime", {"tool_id": "running-tool", "name": "terminal", "result": "done"})
    replay = server._methods["session.events.since"]("replay", {"session_id": "runtime", "last_seen": snapshot["seq"]})["result"]
    assert replay["truncated"] is False
    assert [event["type"] for event in replay["events"]] == ["reasoning.delta", "message.output_delta", "tool.complete"]
    assert replay["events"][1]["payload"]["source_event_seq"] == replay["events"][0]["seq"]
    assert all(event["seq"] > snapshot["seq"] for event in replay["events"])
    assert not any(event["type"] == "tool.complete" for event in snapshot["events"])  # detached graph


def test_snapshot_cannot_split_native_stamp_from_projection(monkeypatch, tmp_path):
    install(monkeypatch, tmp_path)
    session = runtime(tmp_path / "exam")
    begin(session)
    from tui_gateway import inflight_output
    original = inflight_output.record
    entered, proceed = threading.Event(), threading.Event()

    def pause_record(owner, params):
        entered.set()
        assert proceed.wait(5)
        original(owner, params)

    monkeypatch.setattr(inflight_output, "record", pause_record)
    writer = threading.Thread(target=lambda: server._emit("thinking.delta", "runtime", {"text": "atomic"}))
    writer.start()
    assert entered.wait(5)
    snapshots = []
    reader = threading.Thread(target=lambda: snapshots.append(live_snapshot(session)))
    reader.start()
    proceed.set()
    writer.join(5)
    reader.join(5)
    assert not writer.is_alive() and not reader.is_alive()
    state = snapshots[0]["state_snapshot"]
    assert state["events"][-1]["payload"]["text"] == "atomic"
    assert state["seq"] == state["events"][-1]["seq"]


@pytest.mark.parametrize("status", ["complete", "error", "interrupted"])
def test_settlement_retains_terminal_projection_but_next_claim_drops_it(monkeypatch, tmp_path, status):
    peer = install(monkeypatch, tmp_path)
    session = runtime(tmp_path / "exam")
    begin(session)
    server._emit("message.delta", "runtime", {"text": "partial"})
    with session["history_lock"]:
        if status == "error":
            server._fail_inflight_turn(session, "controlled failure")
        else:
            server._clear_inflight_turn(session)
    server._emit("message.complete", "runtime", {"text": "partial", "status": status})
    with session["history_lock"]:
        server._set_session_running(session, False)
    ended = live_snapshot(session)
    assert ended["running"] is False
    assert ended["state_snapshot"]["events"][-1]["payload"]["status"] == status
    assert [frame["params"]["payload"]["running"] for frame in peer.frames][-1] is False
    with session["history_lock"]:
        server._set_session_running(session, True)
    assert "state_snapshot" not in live_snapshot(session)
    with session["history_lock"]:
        server._start_inflight_turn(session, "new carrier")
    assert live_snapshot(session)["state_snapshot"]["events"] == []


def test_global_roster_tracks_profile_owner_and_runtime_reclaim(monkeypatch, tmp_path):
    peer = install(monkeypatch, tmp_path)
    first = runtime(tmp_path / "main", "first")
    second = runtime(tmp_path / "exam", "second")
    begin(second)
    result = server._methods["session.active_list"]("all", {})["result"]
    SessionActiveListResult.model_validate(result)
    assert [(row["profile_name"], row["stored_session_id"], row["running"]) for row in result["sessions"]] == [
        ("main", "same-stored-id", False), ("exam", "same-stored-id", True)]
    filtered = server._methods["session.active_list"]("filtered", {"profile": "exam"})["result"]
    assert [row["id"] for row in filtered["sessions"]] == ["first", "second"]  # existing profile param remains global
    hint = peer.frames[-1]["params"]
    assert hint["session_id"] == "" and hint["type"] == "sessions.changed"
    assert hint["payload"]["runtime_id"] == "second" and hint["payload"]["profile_name"] == "exam"
    assert hint["payload"]["turn_started_at"] > 0
    assert server._pop_session_by_id("second") is second
    assert peer.frames[-1]["params"]["payload"]["running"] is False
    assert [row["id"] for row in server._methods["session.active_list"]("after", {})["result"]["sessions"]] == ["first"]
    assert first["running"] is False


def test_legacy_missing_snapshot_and_child_activity_do_not_invent_parent_output(monkeypatch, tmp_path):
    install(monkeypatch, tmp_path)
    parent = runtime(tmp_path / "main", "parent")
    assert "state_snapshot" not in live_snapshot(parent)
    begin(parent)
    child = runtime(tmp_path / "main", "child", "child-stored")
    begin(child)
    server._emit("message.delta", "child", {"text": "child output"})
    server._emit("subagent.thinking", "parent", {"text": "child detail", "goal": "child", "task_count": 1, "task_index": 0})
    assert [event["type"] for event in live_snapshot(parent)["state_snapshot"]["events"]] == ["message.start"]
    assert live_snapshot(child)["state_snapshot"]["events"][-1]["payload"]["text"] == "child output"


def test_resume_rebind_snapshot_and_existing_viewer_fanout(monkeypatch, tmp_path):
    install(monkeypatch, tmp_path)
    session = runtime(tmp_path / "exam")
    begin(session)
    server._emit("thinking.delta", "runtime", {"text": "first thinking"})
    original, newcomer = session["transport"], Peer()
    monkeypatch.setattr(server, "_session_db", lambda session: contextlib.nullcontext(None))
    token = bind_transport(newcomer)
    try:
        response = server._methods["session.activate"]("activate", {"session_id": "runtime", "omit_messages": True})
    finally:
        reset_transport(token)
    assert response["result"]["state_snapshot"]["events"][-1]["payload"]["text"] == "first thinking"
    server._emit("tool.start", "runtime", {"tool_id": "tool", "name": "terminal"})
    assert newcomer.received.wait(5)
    assert original.frames[-1] == newcomer.frames[-1]


def test_activity_is_latest_state_and_consumed_steer_keeps_native_identity(monkeypatch, tmp_path):
    install(monkeypatch, tmp_path)
    session = runtime(tmp_path / "exam")
    begin(session)
    server._emit("thinking.delta", "runtime", {"text": "Waiting"})
    server._emit("thinking.delta", "runtime", {"text": ""})
    consumed = {"turn_id": "actual-turn", "pending_ids": ["occurrence"], "message_uid": "steer-row",
                "message": {"role": "user", "content": "correction", "display_kind": "steer",
                            "message_uid": "steer-row", "display_content": "correction"}}
    server._emit("steer.consumed", "runtime", consumed)
    events = live_snapshot(session)["state_snapshot"]["events"]
    assert [event["payload"]["text"] for event in events if event["type"] == "thinking.delta"] == [""]
    assert events[-1]["type"] == "steer.consumed" and events[-1]["payload"] == consumed


def test_settle_during_history_read_is_delivered_after_snapshot_watermark(monkeypatch, tmp_path):
    install(monkeypatch, tmp_path)
    session = runtime(tmp_path / "exam")
    begin(session)
    server._emit("tool.start", "runtime", {"tool_id": "tool", "name": "terminal"})
    monkeypatch.setattr(server, "_session_db", lambda session: contextlib.nullcontext(None))

    def finish(owner, db, history):
        server._emit("tool.complete", "runtime", {"tool_id": "tool", "name": "terminal", "result": "done"})
        server._emit("message.complete", "runtime", {"text": "answer", "status": "complete"})
        with owner["history_lock"]:
            server._set_session_running(owner, False)
            server._clear_inflight_turn(owner)
        return history

    monkeypatch.setattr(server, "_live_visible_history", finish)
    binding = server._live_session_payload("runtime", session)
    assert binding["running"] is True and binding["status"] == "working"
    state = binding["state_snapshot"]
    assert state["events"][-1]["type"] == "tool.start"
    replay = server._methods["session.events.since"]("tail", {"session_id": "runtime", "last_seen": state["seq"]})["result"]
    assert [event["type"] for event in replay["events"]] == ["tool.complete", "message.complete"]
    assert session["running"] is False


def test_rewind_invalidates_removed_turn_projection(monkeypatch, tmp_path):
    install(monkeypatch, tmp_path)
    session = runtime(tmp_path / "exam")
    begin(session)
    server._emit("message.complete", "runtime", {"text": "removed answer", "status": "complete"})
    with session["history_lock"]:
        server._set_session_running(session, False)
        server._clear_inflight_turn(session)
        session["history"] = [{"role": "user", "content": "removed user"}, {"role": "assistant", "content": "removed answer"}]
        session["session_key"] = ""  # native unpersisted-session undo path
        server._rewind_active_session_history(session, 0)
    assert "state_snapshot" not in live_snapshot(session)
    assert session["history"] == []


def test_restarted_runtime_restores_persisted_sidecars_without_inventing_activity(monkeypatch, tmp_path):
    install(monkeypatch, tmp_path)
    from hermes_state import SessionDB
    path = tmp_path / "state.db"
    db = SessionDB(path)
    db.create_session("durable", source="desktop")
    db.append_message("durable", "user", "Reminder carrier")
    db.append_message("durable", "assistant", "", reasoning="Durable reasoning", tool_calls=[{
        "id": "call", "type": "function", "function": {"name": "terminal", "arguments": '{"command":"controlled"}'}}])
    db.append_message("durable", "tool", "done", tool_call_id="call", tool_name="terminal")
    db.append_message("durable", "assistant", "Durable answer")
    db.close()
    event_replay.reset_replay_state()
    server._sessions.clear()
    reopened = SessionDB(path)
    try:
        session = runtime(tmp_path / "exam", stored="durable")
        monkeypatch.setattr(server, "_session_db", lambda session: contextlib.nullcontext(reopened))
        payload = server._live_session_payload("runtime", session)
        assert payload["running"] is False and "state_snapshot" not in payload
        assert [row["role"] for row in payload["messages"]] == ["user", "assistant", "tool", "assistant"]
        assert payload["messages"][1]["reasoning"] == "Durable reasoning"
        assert payload["messages"][2]["name"] == "terminal"
        assert payload["messages"][2]["args"] == {"command": "controlled"}
        assert payload["messages"][-1]["text"] == "Durable answer"
        assert event_replay.latest_seq("runtime") == 0
    finally:
        reopened.close()


def test_projection_failure_never_blocks_native_output_or_claims_completeness(monkeypatch, tmp_path):
    install(monkeypatch, tmp_path)
    session = runtime(tmp_path / "exam")
    begin(session)
    from tui_gateway import inflight_output
    scope = {"turn_id": "actual-turn", "stored_session_id": session["session_key"],
             "conversation_ref": "controlled-conversation", "message_uid": "actual-assistant"}
    frame = server._event_frame("message.output_state", "runtime", {
        **scope, "state": "open", "api_request_id": "request", "stream_writer_token": 1})
    frame["params"]["seq"] = 1
    server.write_json(frame)

    def fail(events):
        raise RuntimeError("controlled additive projection failure")

    monkeypatch.setattr(inflight_output, "_fold_typed_delta", fail)
    emit_typed(session, "message.delta", {"text": "native answer"}, scope)
    delivered = session["transport"].frames
    assert [frame["params"]["type"] for frame in delivered][-2:] == ["message.delta", "message.output_delta"]
    assert "state_snapshot" not in live_snapshot(session)
    assert session["running"] is True
