"""Exceptional Turn facts survive native runtime reclamation without fabricated messages."""
from __future__ import annotations

import contextlib
import copy
import json
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from hermes_state import SessionDB
from tests.tui_gateway import test_pending_native_turn as native_turn
from tui_gateway import server
from tui_gateway.turn_terminal import token

NATIVE_EMIT = server._emit
native_live = native_turn.live


@pytest.fixture(autouse=True)
def capture_cold_history_dto(monkeypatch, record_property, request):
    original = cold_history
    def capture(runtime):
        rows = original(runtime)
        from hermes_cli.web_routers import sessions
        import asyncio
        monkeypatch.setattr(sessions, "_with_db", lambda _profile, read, **_kwargs: read(runtime.db_slot[0]))
        monkeypatch.setattr(sessions, "_history_profile_home", lambda _profile: runtime.home)
        monkeypatch.setattr(sessions, "_serving_profile", lambda _profile: "controlled")
        rest = asyncio.run(sessions.get_session_messages("stored", profile="controlled", limit=None,
                           offset=0, order=None, include_compacted=True, inline_images=True))
        record_property("cold_history", json.dumps({"case": request.node.name, "rpc_messages": rows, "rest": rest}))
        assert [row["message_uid"] for row in rest["messages"]] == [row["message_uid"] for row in rows]
        return rows
    monkeypatch.setattr(sys.modules[__name__], "cold_history", capture)


class Peer:
    def __init__(self):
        self.frames = []

    def write(self, frame):
        self.frames.append(copy.deepcopy(frame))
        return True


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    home = tmp_path / "profiles" / "exam"
    home.mkdir(parents=True)
    db = SessionDB(home / "state.db")
    db.create_session("stored", source="desktop")
    current_db = [db]
    agent = SimpleNamespace(session_id="stored", model="controlled", _session_db=db, _session_messages=[])
    session = {"_sid": "runtime", "agent": agent, "session_key": "stored", "profile_home": str(home),
               "history": [], "history_lock": threading.RLock(), "running": False, "created_at": 1,
               "transport": Peer(), "cols": 80}
    monkeypatch.setattr(server, "_sessions", {"runtime": session})
    monkeypatch.setattr(server, "_session_db", lambda _session: contextlib.nullcontext(current_db[0]))
    monkeypatch.setattr(server, "_session_info", lambda *_args: {})
    monkeypatch.setattr(server, "_fallback_session_info", lambda *_args: {})
    monkeypatch.setattr(server, "_get_usage", lambda _agent: {})
    monkeypatch.setattr(server, "_retire_turn_marker", lambda *_args: None)
    yield SimpleNamespace(home=home, db=db, db_slot=current_db, session=session, agent=agent)
    current_db[0].close()


@pytest.fixture
def native_runtime(native_live, monkeypatch):
    monkeypatch.setattr(server, "_emit", NATIVE_EMIT)
    native_live.session.update(_sid="runtime", transport=Peer())
    current = [native_live.db]
    monkeypatch.setattr(server, "_session_db", lambda _session: contextlib.nullcontext(current[0]))
    value = SimpleNamespace(home=native_live.home, db=native_live.db, db_slot=current,
                            agent=native_live.agent, session=native_live.session, live=native_live)
    yield value
    if current[0] is not native_live.db:
        current[0].close()


def accept(runtime, text="accepted input"):
    session = runtime.session
    with session["history_lock"]:
        server._set_session_running(session, True)
        server._start_inflight_turn(session, text)
    server._persist_submit_user_row(session, text, None, accept_metadata={"original": "kept"})
    server._emit("message.start", "runtime")
    return token(session)


def terminal(runtime, status="error", *, messages=None, text="failed body", error="original failure"):
    result = {"final_response": text, "messages": messages or [], "completed": status == "complete",
              "failed": status == "error", "interrupted": status == "interrupted"}
    if status == "error":
        result["error"] = error
    st = server._TurnRun(runtime.agent, None, None, True, result=result, inflight_token=token(runtime.session))
    payload, _, _ = server._complete_turn_payload(runtime.session, st, None, 80)
    server._emit("message.complete", "runtime", payload)
    with runtime.session["history_lock"]:
        server._set_session_running(runtime.session, False)
    return payload


def cold_history(runtime):
    server._pop_session_by_id("runtime")
    path = Path(runtime.db_slot[0].db_path)
    runtime.db_slot[0].close()
    runtime.db_slot[0] = SessionDB(path)
    runtime.session = {"_sid": "cold", "agent": None, "session_key": "stored", "profile_home": str(runtime.home),
                       "history": [], "history_lock": threading.RLock(), "running": False, "created_at": 2,
                       "transport": Peer()}
    server._sessions["cold"] = runtime.session
    response = server.handle_request({"id": "cold-history", "method": "session.history", "params": {"session_id": "cold"}})
    assert "error" not in response
    return response["result"]["messages"]


def outcome(rows):
    source = next(row for row in rows if row.get("role") == "user")
    return source["display_metadata"]["turn_terminal"]


def test_build_failure_reentry_then_reclaim_and_cold_history(runtime, monkeypatch):
    runtime.session["agent"] = None
    accepted = accept(runtime)
    original = runtime.db.get_messages("stored")[0]
    monkeypatch.setattr(server, "_wait_agent_for_prompt", lambda *_args: {"error": {"message": "build exploded"}})
    server._run_after_agent_ready("build", "runtime", runtime.session, "accepted input", None, None, None)
    server._emit_terminal_turn_error("runtime", runtime.session, "build exploded", expected_token=accepted)
    rows = runtime.db.get_messages("stored")
    assert len(rows) == 1 and rows[0]["message_uid"] == original["message_uid"]
    assert rows[0]["content"] == "accepted input" and rows[0]["api_content"] is None
    assert rows[0]["display_metadata"]["original"] == "kept"
    descriptor = rows[0]["display_metadata"]["turn_terminal"]
    assert descriptor["status"] == "error" and descriptor["error"] == "build exploded"
    assert descriptor["source_message_uid"] == original["message_uid"]
    restored = cold_history(runtime)
    assert len(restored) == 1 and restored[0]["role"] == "user"
    assert outcome(restored) == descriptor


@pytest.mark.parametrize("typed_failure", [False, True])
def test_interrupted_partial_output_and_real_tool_rows_restore_in_order(native_runtime, monkeypatch, typed_failure):
    from agent.output_identity import observe_outputs, accept_response
    from agent.turn_context import _bind_turn_identity
    from tui_gateway import output_identity

    runtime = native_runtime
    accept(runtime)
    source = runtime.db.get_messages_as_conversation("stored", include_row_ids=True)[0]
    agent = runtime.agent
    emit = lambda kind, payload: server._emit(kind, "runtime", payload)
    _bind_turn_identity(agent, "controlled-task", lambda text: emit("message.delta", {"text": text}), None, None, None)
    agent.reasoning_callback = lambda text: emit("reasoning.delta", {"text": text})
    agent._current_api_request_id = agent._current_turn_id + ":api:1"
    agent._persist_user_message_idx = 0
    if typed_failure:
        original = output_identity._frame
        def fail_typed(kind, *args):
            if kind in {"message.output_delta", "tool.output"}:
                raise RuntimeError("typed alias construction unavailable")
            return original(kind, *args)
        monkeypatch.setattr(output_identity, "_frame", fail_typed)
    messages = [source]
    with observe_outputs(agent, emit):
        writer = agent._claim_stream_writer()
        agent._fire_reasoning_delta("durable reasoning")
        raw = SimpleNamespace(content="", reasoning="durable reasoning", tool_calls=[SimpleNamespace(
            id=call, type="function", function=SimpleNamespace(name="terminal", arguments='{"command":"controlled"}'))
            for call in ("tool-1", "tool-2")])
        accept_response(agent, raw, writer)
        assistant = agent._build_assistant_message(raw, "tool_calls")
        messages.append(assistant)
        assert agent._flush_messages_to_session_db(messages, []) is True
        emit("tool.start", {"tool_id": "tool-1", "name": "terminal", "args": {"command": "controlled"}})
        messages.append({"role": "tool", "content": '{"output":"done"}', "tool_call_id": "tool-1", "name": "terminal"})
        assert agent._flush_messages_to_session_db(messages, []) is True
        emit("tool.complete", {"tool_id": "tool-1", "name": "terminal", "result": {"output": "done"}})
        emit("tool.start", {"tool_id": "tool-2", "name": "terminal", "args": {"command": "still running"}})
        agent._current_api_request_id = agent._current_turn_id + ":api:2"
        agent._claim_stream_writer()
        agent._fire_stream_delta("actual partial")
    from tui_gateway.inflight_output import snapshot
    assert all("_output_identity" not in event for event in snapshot(runtime.session, "runtime")["events"])
    terminal(runtime, "interrupted", messages=messages, text="actual partial")
    restored = cold_history(runtime)
    assert [row["role"] for row in restored] == ["user", "assistant", "tool"]
    assert restored[1]["reasoning"] == "durable reasoning"
    saved = outcome(restored)
    assert saved["status"] == "interrupted"
    assert [segment["kind"] for segment in saved["outputs"]] == ["tool", "message"]
    assert saved["outputs"][0]["state"] == "running"
    assert saved["outputs"][0]["assistant_message_uid"] == restored[1]["message_uid"]
    assert saved["outputs"][0]["tool_call_uid"] != restored[2]["tool_call_uid"]
    assert all(segment.get("message_uid") or segment.get("tool_call_uid") for segment in saved["outputs"])
    assert saved["outputs"][-1]["text"] == "actual partial"
    assert not any(row.get("text") == "actual partial" for row in restored)  # no invented assistant row


def test_native_persisted_failure_is_annotated_without_duplicate_reply(runtime):
    accepted = accept(runtime)
    native = [{"role": "assistant", "content": "native failed response"}]
    runtime.db.append_messages_batch("stored", native)
    terminal(runtime, messages=runtime.db.get_messages_as_conversation("stored", include_row_ids=True), text="native failed response")
    first = outcome(runtime.db.get_messages_as_conversation("stored", include_row_ids=True))
    server._emit_terminal_turn_error("runtime", runtime.session, "late duplicate callback", expected_token=accepted)
    restored = cold_history(runtime)
    assert [row["role"] for row in restored] == ["user", "assistant"]
    assert restored[-1]["text"] == "native failed response"
    assert outcome(restored) == first
    assert first["final_assistant_message_uid"] == native[0]["message_uid"]


def test_success_leaves_native_rows_and_metadata_unchanged(runtime):
    accept(runtime)
    before = copy.deepcopy(runtime.db.get_messages("stored"))
    native = [{"role": "assistant", "content": "normal response"}]
    runtime.db.append_messages_batch("stored", native)
    terminal(runtime, "complete", messages=native, text="normal response")
    after = runtime.db.get_messages("stored")
    assert after[0] == before[0] and len(after) == 2
    assert "turn_terminal" not in after[0]["display_metadata"]


@pytest.mark.parametrize("retired", ["next_turn", "closed", "rewound", "unaccepted"])
def test_retired_or_unaccepted_failure_cannot_create_or_pollute_history(runtime, retired):
    old = accept(runtime) if retired != "unaccepted" else None
    if retired == "next_turn":
        with runtime.session["history_lock"]:
            server._set_session_running(runtime.session, False)
            server._clear_inflight_turn(runtime.session)
        accept(runtime, "next input")
    elif retired == "closed":
        server._pop_session_by_id("runtime")
    elif retired == "rewound":
        runtime.db.rewind_user_turn("stored", 0)
    server._emit_terminal_turn_error("runtime", runtime.session, "retired failure", expected_token=old)
    assert all(not (row.get("display_metadata") or {}).get("turn_terminal") for row in runtime.db.get_messages("stored"))
    if retired == "next_turn":
        assert runtime.session["inflight_turn"]["user"] == "next input"
        assert not runtime.session["inflight_turn"].get("error")


def test_same_stored_id_foreign_profile_proof_is_rejected(runtime, tmp_path):
    accept(runtime)
    source = dict(runtime.session["inflight_turn"]["_terminal_source"])
    other = tmp_path / "profiles" / "other"
    other.mkdir()
    foreign = SessionDB(other / "state.db")
    foreign.create_session("stored", source="desktop")
    foreign.append_message("stored", "user", "foreign input")
    source["db_path"] = str(Path(foreign.db_path).resolve())
    runtime.session["inflight_turn"]["_terminal_source"] = source
    try:
        server._emit_terminal_turn_error("runtime", runtime.session, "wrong owner", expected_token=token(runtime.session))
        assert "turn_terminal" not in runtime.db.get_messages("stored")[0]["display_metadata"]
        assert not foreign.get_messages("stored")[0].get("display_metadata")
    finally:
        foreign.close()


def test_compacted_ancestor_source_uses_existing_visible_lineage(runtime):
    accept(runtime)
    history = runtime.db.get_messages_as_conversation("stored", include_row_ids=True)
    ancestor = copy.deepcopy(history)
    runtime.db.publish_compression_child(parent_session_id="stored", child_session_id="child", source="desktop",
                                         messages=history, require_compression_lease=False)
    runtime.agent.session_id = runtime.session["session_key"] = "child"
    from tui_gateway.turn_terminal import source_observer
    runtime.session["inflight_turn"].pop("_terminal_source")
    prior_calls = []
    source_observer("runtime", runtime.session, runtime.agent, token(runtime.session),
                    lambda *_args: prior_calls.append(True))(ancestor, 0)
    assert runtime.session["inflight_turn"]["_terminal_source"]["session_id"] == "stored"
    assert prior_calls == [True]
    server._emit_terminal_turn_error("runtime", runtime.session, "after rotation", expected_token=token(runtime.session))
    visible = runtime.db.get_messages_as_conversation("child", include_ancestors=True, include_row_ids=True)
    assert outcome(visible)["error"] == "after rotation"


def test_metadata_write_failure_preserves_original_error_and_is_retryable(runtime, monkeypatch):
    accepted = accept(runtime)
    original = runtime.db._execute_write
    monkeypatch.setattr(runtime.db, "_execute_write", lambda *_args, **_kwargs: (_ for _ in ()).throw(OSError("store failed")))
    server._emit_terminal_turn_error("runtime", runtime.session, "original error", expected_token=accepted)
    terminal_frame = runtime.session["transport"].frames[-1]["params"]["payload"]
    assert terminal_frame["error"] == "original error"
    assert runtime.session["inflight_turn"]["error"] == "original error"
    monkeypatch.setattr(runtime.db, "_execute_write", original)
    server._emit_terminal_turn_error("runtime", runtime.session, "original error", expected_token=accepted)
    assert outcome(cold_history(runtime))["error"] == "original error"


def test_formal_idle_submit_dispatcher_exception_survives_cold_history(native_runtime, monkeypatch, tmp_path):
    runtime = native_runtime
    monkeypatch.setattr(server, "_CRASH_LOG", tmp_path / "crash.log")
    entered = threading.Event()
    workers = []
    start = server._start_session_work
    def record_worker(*args, **kwargs):
        worker = start(*args, **kwargs)
        if worker is not None:
            workers.append(worker)
        return worker
    monkeypatch.setattr(server, "_start_session_work", record_worker)
    def crash(*_args, **_kwargs):
        entered.set()
        raise RuntimeError("dispatcher exploded before finalizer")
    monkeypatch.setattr(runtime.agent, "run_conversation", crash)
    response = server.handle_request({"id": "dispatcher", "method": "prompt.submit_idle",
                                      "params": {"session_id": "runtime", "text": "accepted dispatcher input"}})
    assert response["result"]["status"] == "streaming"
    assert entered.wait(5)
    native_turn.settled(runtime.live)
    for worker in workers:
        worker.join(5)
        assert not worker.is_alive()
    assert not runtime.session["running"]
    rows = cold_history(runtime)
    assert len(rows) == 1 and rows[0]["role"] == "user"
    assert rows[0]["message_uid"] == outcome(rows)["source_message_uid"]
    assert outcome(rows)["status"] == "error" and "dispatcher exploded" in outcome(rows)["error"]


def test_real_native_finalizer_failure_is_not_persisted_twice(native_runtime):
    from agent.turn_finalizer import finalize_turn
    from agent.turn_context import _bind_turn_identity
    runtime = native_runtime
    accept(runtime)
    agent = runtime.agent
    _bind_turn_identity(agent, "controlled-finalizer", None, None, None, None)
    agent._persist_user_message_idx = 0
    agent._current_turn_timestamp = 1700000000.0
    messages = runtime.db.get_messages_as_conversation("stored", include_row_ids=True)
    result = finalize_turn(agent, final_response="Native recorded failure.", api_call_count=0,
        interrupted=False, failed=True, messages=messages, conversation_history=[],
        effective_task_id="controlled-finalizer", turn_id=agent._current_turn_id,
        user_message="accepted input", original_user_message="accepted input", _should_review_memory=False,
        _turn_exit_reason="all_retries_exhausted_no_response")
    assert result["failed"]
    before = runtime.db.get_messages("stored")
    assert [row["role"] for row in before] == ["user", "assistant"]
    st = server._TurnRun(agent, None, None, True, result=result, inflight_token=token(runtime.session))
    server._complete_turn_payload(runtime.session, st, None, 80)
    server._complete_turn_payload(runtime.session, st, None, 80)
    after = runtime.db.get_messages("stored")
    assert len(after) == len(before) and after[-1]["message_uid"] == before[-1]["message_uid"]
    from agent.turn_context import build_api_messages
    from tests.tui_gateway.test_output_identity import provider_wire
    api_messages, _ = build_api_messages(agent, result["messages"], current_turn_user_idx=0,
        ext_prefetch_cache=None, plugin_user_context=None, moa_config=None, active_system_prompt="Frozen native root.")
    body = provider_wire(agent._build_api_kwargs(api_messages, tools_for_api=[]))
    assert "turn_terminal" not in body and "source_message_uid" not in body and "finished_at" not in body
    saved = outcome(cold_history(runtime))
    assert saved["status"] == "error" and saved["final_assistant_message_uid"] == after[-1]["message_uid"]


def test_unidentified_legacy_output_does_not_guess_native_duplicates(runtime):
    accept(runtime)
    runtime.db.append_messages_batch("stored", [{"role": "assistant", "content": "already durable"}])
    server._emit("reasoning.delta", "runtime", {"text": "unidentified legacy"})
    server._emit_terminal_turn_error("runtime", runtime.session, "observer unavailable", expected_token=token(runtime.session))
    saved = outcome(cold_history(runtime))
    assert saved["outputs_complete"] is False and not saved.get("outputs")


def test_unidentified_uncommitted_output_is_retained_without_invented_uid(runtime):
    accept(runtime)
    server._emit("message.delta", "runtime", {"text": "uncommitted actual text"})
    server._emit_terminal_turn_error("runtime", runtime.session, "aborted", expected_token=token(runtime.session))
    assert outcome(cold_history(runtime))["outputs"] == [{"kind": "message", "text": "uncommitted actual text"}]


def test_foreign_active_native_turn_lease_rejects_terminal_write(runtime):
    accepted = accept(runtime)
    assert runtime.db.try_acquire_session_turn_lease("stored", "other-owner")
    try:
        server._emit_terminal_turn_error("runtime", runtime.session, "late owner", expected_token=accepted)
        assert "turn_terminal" not in runtime.db.get_messages("stored")[0]["display_metadata"]
    finally:
        runtime.db.release_session_turn_lease("stored", "other-owner")


@pytest.mark.parametrize("proof_key", ["row_id", "message_uid", "session_id"])
def test_source_proof_requires_real_row_uid_and_physical_owner(runtime, proof_key):
    accept(runtime)
    proof = runtime.session["inflight_turn"]["_terminal_source"]
    proof[proof_key] = 999 if proof_key == "row_id" else "not-the-accepted-source"
    server._emit_terminal_turn_error("runtime", runtime.session, "bad source", expected_token=token(runtime.session))
    assert "turn_terminal" not in runtime.db.get_messages("stored")[0]["display_metadata"]


def test_successful_terminal_metadata_disappears_with_native_rewind(runtime):
    accept(runtime)
    server._emit_terminal_turn_error("runtime", runtime.session, "before rewind", expected_token=token(runtime.session))
    assert outcome(runtime.db.get_messages_as_conversation("stored"))["status"] == "error"
    runtime.db.rewind_user_turn("stored", 0)
    assert cold_history(runtime) == []
