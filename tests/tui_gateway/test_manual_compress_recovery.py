"""Real native manual-compaction lifecycle remains readable through activate."""
from __future__ import annotations

from contextlib import contextmanager
import copy
import json
import socket
import threading
import traceback
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from hermes_state import SessionDB
from tests.tui_gateway.test_recovery_view import activate, begin_web, request, settled_web_output
from tui_gateway import event_replay, recovery_view, server

pytest_plugins = ["tests.tui_gateway.test_recovery_view"]


@pytest.fixture(autouse=True)
def bounded_info(monkeypatch, request):
    monkeypatch.setattr(server, "_session_info", lambda agent, session: {"running": bool(session.get("running"))})
    def no_network(*_args, **_kwargs):
        raise AssertionError("external traffic forbidden in maintenance recovery regression")
    monkeypatch.setattr(socket.socket, "connect", no_network)
    monkeypatch.setattr(socket.socket, "connect_ex", no_network)
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", MagicMock())
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *_args, **_kwargs: {})
    monkeypatch.setattr("agent.model_metadata._is_ollama_server", lambda *_args, **_kwargs: False)
    yield
    properties = {key: json.loads(value) for key, value in request.node.user_properties
                  if key in {"native_alias_receipt", "noting_off_matrix"}}
    if properties:
        destination = request.config.rootpath / ".hermes-dev/incremental-sync-20261027/integration/maintenance-output-retention/alias-final-payloads"
        destination.mkdir(parents=True, exist_ok=True)
        (destination / (request.node.name + ".json")).write_text(json.dumps(properties, indent=2, default=str))


@contextmanager
def manual(native):
    _db, session, _home = native
    with server._manual_compress_turn("runtime", session):
        yield session


def test_real_manual_context_without_inflight_is_busy_but_recoverable(native):
    db, session, _ = native
    req = request(db)
    assert "inflight_turn" not in session
    with manual(native):
        assert session["running"] and session["_manual_compress_active"]
        result = activate(req)
        assert result["complete"] and result["running"] and result["status"] == "working"
        assert result["state_snapshot"]["events"] == [] and result["turn_started_at"] is None
        assert "inflight" not in result
    result = activate(req)
    assert result["complete"] and not result["running"]


def test_completed_output_remains_accounted_during_and_after_manual(native):
    db, session, _ = native
    settled_web_output(db, session)
    req = request(db)
    with manual(native):
        active = activate(req)
        assert active["complete"] and active["running"] and active["state_snapshot"]["events"] == []
    ended = activate(req)
    assert ended["complete"] and not ended["running"] and ended["state_snapshot"]["events"] == []


@pytest.mark.parametrize("exception", [RuntimeError, KeyboardInterrupt])
def test_manual_failure_or_cancellation_clears_maintenance_without_stale_busy(native, exception):
    db, session, _ = native
    req = request(db)
    with pytest.raises(exception):
        with manual(native):
            assert activate(req)["complete"]
            raise exception("controlled end")
    result = activate(req)
    assert result["complete"] and not result["running"] and not session.get("_manual_compress_active")


@pytest.mark.parametrize("holder", ["external-channel-owner", "opaque-local-owner"])
def test_manual_busy_cannot_borrow_conflicting_turn_lease(native, holder):
    db, session, _ = native
    req = request(db)
    with manual(native):
        db.try_acquire_session_turn_lease("stored", holder)
        result = activate(req)
        assert not result["complete"] and result["reason"] == "view_changed"
        db.release_session_turn_lease("stored", holder)


@pytest.mark.parametrize("status", ["valid", "missing_source", "missing_lease"])
def test_actual_turn_and_automatic_compaction_still_require_native_proof(native, status):
    db, session, _ = native
    holder = begin_web(db, session)
    assert db.try_acquire_compression_lock("stored", "automatic-compression-owner")
    if status == "missing_source":
        session["inflight_turn"].pop("_terminal_source")
    elif status == "missing_lease":
        db.release_session_turn_lease("stored", holder)
    result = activate(request(db))
    if status == "valid":
        assert result["complete"] and result["running"]
    else:
        assert not result["complete"] and result["reason"] == "runtime_unavailable"
    db.release_compression_lock("stored", "automatic-compression-owner")


@pytest.mark.parametrize("known", [False, True])
def test_previous_output_in_manual_phase_uses_original_idle_receipt_proof(native, known):
    db, session, _ = native
    settled_web_output(db, session)
    req = request(db)
    with manual(native):
        # A real late frame must still be proved independently of maintenance.
        from tui_gateway import inflight_output
        inflight_output.start(session)
        if known:
            assistant = db.get_messages("stored")[-1]
            server._emit("message.output_committed", "runtime", {
                "turn_id": "native-turn", "stored_session_id": "stored", "conversation_ref": "controlled",
                "source_message": {"row_id": assistant["id"], "message_uid": assistant["message_uid"], "role": "assistant",
                                   "has_content": True, "has_reasoning": False}})
        else:
            server._emit("reasoning.delta", "runtime", {"text": "unproven previous thinking"})
        result = activate(req)
        assert result["complete"] is known
        if known:
            assert result["state_snapshot"]["events"] == []
        else:
            assert result["reason"] == "runtime_unavailable"


@pytest.mark.parametrize("persisted", [False, True])
def test_retained_failed_turn_without_completion_still_refuses_even_with_metadata(native, persisted):
    db, session, _home = native
    holder = begin_web(db, session)
    from tui_gateway import turn_terminal
    if persisted:
        turn_terminal.persist("runtime", session, {"status": "error", "text": "old live answer", "error": "controlled"},
                              turn_terminal.token(session))
    with session["history_lock"]:
        server._fail_inflight_turn(session, "controlled")
        session["running"] = False
    db.release_session_turn_lease("stored", holder)
    with manual(native):
        result = activate(request(db))
        # The stream is still open and no native completion receipt was emitted.
        # Durable metadata alone cannot prove these retained output frames.
        assert not result["complete"] and result["reason"] == "runtime_unavailable"


def test_phase_switch_at_snapshot_uses_native_manual_exit_and_retries(native, monkeypatch):
    db, session, _ = native
    session["history_lock"] = threading.RLock()
    ctx = server._manual_compress_turn("runtime", session)
    ctx.__enter__()
    req = request(db)
    original, captures = recovery_view.snapshot, []
    def capture(*args, **kwargs):
        state = original(*args, **kwargs)
        captures.append(True)
        if len(captures) == 1:
            ctx.__exit__(None, None, None)
        return state
    monkeypatch.setattr(recovery_view, "snapshot", capture)
    result = activate(req)
    assert result["complete"] and not result["running"] and len(captures) == 2


def test_queued_prompt_native_drain_takes_over_after_manual_busy(native, monkeypatch):
    db, session, _home = native
    from tui_gateway import turn_terminal
    monkeypatch.setattr(server, "_session_uses_compute_host", lambda _session: False)
    monkeypatch.setattr(server, "_load_busy_input_mode", lambda: "interrupt")
    observed = []
    def start_queued(rid, sid, owner, text, **kwargs):
        observed.append(text)
        owner["agent"]._current_turn_id = "queued-turn"
        owner["agent"]._active_session_turn_lease_holder = "queued-owner"
        owner["agent"]._session_db = db
        assert db.try_acquire_session_turn_lease("stored", "queued-owner")
        with owner["history_lock"]:
            server._start_inflight_turn(owner, text)
        staged = owner["_submit_user_row"]
        turn_terminal.source_observer(sid, owner, owner["agent"], turn_terminal.token(owner), None)([staged], 0)
    monkeypatch.setattr(server, "_run_prompt_submit", start_queued)
    with manual(native):
        queued = server._handle_busy_submit("queued", "runtime", session, "queued question", session["transport"])
        assert queued["result"]["status"] == "queued"
        result = activate(request(db))
        assert result["complete"] and result["running"] and result["queued"]["user"] == "queued question"
    assert observed == ["queued question"] and not session.get("_manual_compress_active")
    result = activate(request(db))
    assert result["complete"] and result["running"] and result["inflight"]["user"] == "queued question"
    db.release_session_turn_lease("stored", "queued-owner")


@pytest.mark.parametrize("in_place", [False, True])
def test_actual_manual_compress_commits_and_remains_recoverable(native, monkeypatch, in_place):
    from tests.tui_gateway.test_manual_compress_history_fence import _agent_with_history
    from hermes_state_recovery_view import project_view, read_view, selector
    fixture_db, session, home = native
    db, agent, parent, before = _agent_with_history(home, monkeypatch, in_place)
    session.update(agent=agent, session_key=parent, history=before, history_version=1, cwd=str(home))
    monkeypatch.setattr(server, "_get_usage", lambda agent: {})
    raw = project_view(read_view(fixture_db, parent, "default", [selector()]))
    req = {"version": 1, "profile": "default", "stored_id": parent, "windows": [
        {"selector": item["selector"], "receipt": item["coverage"]} for item in raw["windows"]]}
    try:
        with manual(native):
            assert activate(req)["complete"]
            removed, _ = server._compress_session_history(session, before_messages=before, history_version=1)
            assert removed > 0
            result = activate(req)
            assert result["complete"] and result["running"]
        assert activate(req)["complete"] and not session["running"]
        assert (agent.session_id == parent) is in_place
    finally:
        agent.close()
        db.close()


def test_manual_flag_cannot_lend_proof_to_a_real_inflight_without_source(native):
    db, session, _ = native
    with manual(native):
        with session["history_lock"]:
            server._start_inflight_turn(session, "unproved actual generation")
        result = activate(request(db))
        assert not result["complete"] and result["reason"] == "runtime_unavailable"


def test_manual_empty_snapshot_still_requires_continuous_native_epoch(native, monkeypatch):
    db, _session, _ = native
    original, epochs = recovery_view.project_view, []
    def change(*args, **kwargs):
        result = original(*args, **kwargs)
        epochs.append(True)
        monkeypatch.setattr(event_replay, "_REPLAY_EPOCH", f"new-epoch-{len(epochs)}")
        return result
    monkeypatch.setattr(recovery_view, "project_view", change)
    with manual(native):
        result = activate(request(db))
        assert not result["complete"] and result["reason"] == "replay_gap"


@pytest.fixture
def failed_native_turn(native, monkeypatch, request):
    """Real stream/source/terminal callbacks, with only the summary dependency controlled."""
    from agent.output_identity import accept_response, observe_outputs
    from agent.turn_context import _bind_turn_identity
    from tests.tui_gateway.test_manual_compress_history_fence import _agent_with_history
    from tui_gateway import turn_terminal

    _fixture_db, session, home = native
    options = getattr(request, "param", {})
    config = {"terminal": {"cwd": str(home)}}
    if "noting_enabled" in options:
        config["noting"] = {"enabled": options["noting_enabled"]}
    (home / "config.yaml").write_text(json.dumps(config))
    db, agent, parent, before = _agent_with_history(home, monkeypatch)
    session.update(agent=agent, session_key=parent, history=before, history_version=1, cwd=str(home))
    monkeypatch.setattr(server, "_get_usage", lambda _agent: {})
    emit = lambda kind, payload: server._emit(kind, "runtime", payload)
    _bind_turn_identity(agent, "maintenance-retention", lambda text: emit("message.delta", {"text": text}),
                        None, None, None)
    holder = "native-output-retention-owner"
    assert db.try_acquire_session_turn_lease(parent, holder)
    agent._active_session_turn_lease_holder = holder
    try:
        with session["history_lock"]:
            server._set_session_running(session, True)
            server._start_inflight_turn(session, "accepted failing question")
        server._persist_submit_user_row(session, "accepted failing question", None)
        messages = db.get_messages_as_conversation(parent, include_row_ids=True)
        source = messages[-1]
        previous = messages[:-1]
        agent._persist_user_message_idx = len(messages) - 1
        turn_terminal.source_observer("runtime", session, agent, turn_terminal.token(session), None)(
            messages, agent._persist_user_message_idx)
        assert session["inflight_turn"]["_terminal_source"]["message_uid"] == source["message_uid"]
        with observe_outputs(agent, emit):
            agent._current_api_request_id = agent._current_turn_id + ":api:1"
            writer = agent._claim_stream_writer()
            agent._fire_stream_delta("native partial output")
            if options.get("terminal") == "complete" or options.get("persist_partial"):
                response = SimpleNamespace(content="native partial output", reasoning=None, tool_calls=None)
                accept_response(agent, response, writer)
                messages.append(agent._build_assistant_message(response, "stop"))
                assert agent._flush_messages_to_session_db(messages, []) is True
                if options.get("persist_partial"):
                    agent._current_api_request_id = agent._current_turn_id + ":api:2"
                    agent._claim_stream_writer()
                    agent._fire_stream_delta("unpersisted tail")
        completed = options.get("terminal") == "complete"
        terminal_text = "unpersisted tail" if options.get("persist_partial") else "native partial output"
        result = {"final_response": terminal_text, "messages": messages, "completed": completed,
                  "failed": not completed}
        if not completed:
            result.update(partial=True, error="controlled provider failure")
        state = server._TurnRun(agent, None, None, True, result=result, history=previous,
                                compression_count=agent.context_compressor.compression_count,
                                inflight_token=turn_terminal.token(session))
        payload, _, status = server._complete_turn_payload(session, state, None, 80)
        assert status == ("complete" if completed else "error")
        if options.get("committed_frames"):
            committed = {"stored_session_id": parent, "message": {
                "role": "user", "content": source["content"], "row_id": source["_row_id"],
                "message_uid": source["message_uid"], "timestamp": source["timestamp"]}}
            if options["committed_frames"] in {"bad_row", "bad_row_with_source"}:
                committed["message"]["row_id"] = 999999
            emit("message.user_committed", committed)
            if options["committed_frames"] in {"source", "bad_row_with_source"}:
                scope = session["_inflight_output"]["events"][0]["payload"]
                original_message = {**committed["message"], "row_id": source["_row_id"]}
                emit("message.source_committed", {**committed, "message": original_message, "turn_id": agent._current_turn_id,
                    "conversation_ref": scope["conversation_ref"], "source_messages": payload["persisted_turn"]["source_messages"],
                    "source_boundary": payload["persisted_turn"]["source_boundary"]})
        emit("message.complete", payload)
        with session["history_lock"]:
            server._set_session_running(session, False)
        db.release_session_turn_lease(parent, holder)
        session["history"] = db.get_messages_as_conversation(parent, include_row_ids=True)
        source_row = next(row for row in db.get_messages(parent) if row["message_uid"] == source["message_uid"])
        saved = (source_row.get("display_metadata") or {}).get("turn_terminal")
        if not completed:
            assert saved["status"] == "error" and saved.get("outputs_complete", True)
            assert saved["outputs"][-1]["text"] == terminal_text
            assert saved["outputs"][-1]["message_uid"]
        yield SimpleNamespace(db=db, session=session, parent=parent, source=source, saved=saved,
                              persist_partial=bool(options.get("persist_partial")))
    finally:
        from agent.agent_runtime_helpers import note_turn_persisted
        note_turn_persisted(agent)
        db.release_session_turn_lease(parent, holder)
        agent.close()
        db.close()


def failed_turn_request(failed):
    from hermes_state_recovery_view import project_view, read_view, selector
    view = project_view(read_view(failed.db, failed.parent, "default", [selector()]))
    return {"version": 1, "profile": "default", "stored_id": failed.parent, "windows": [
        {"selector": item["selector"], "receipt": item["coverage"]} for item in view["windows"]]}


@pytest.mark.parametrize("ending", ["return", "error", "cancel", "compact_in_place", "compact_rotate"])
def test_settled_native_error_survives_manual_maintenance_and_next_turn(
    failed_native_turn, ending, record_property,
):
    from tui_gateway.inflight_output import snapshot

    failed = failed_native_turn
    session, db = failed.session, failed.db
    req = failed_turn_request(failed)
    retained = copy.deepcopy(snapshot(session, "runtime", include_internal=True)["events"])
    samples = {"before": activate(req)}
    assert samples["before"]["complete"] and not samples["before"]["running"]
    exception = {"error": RuntimeError, "cancel": KeyboardInterrupt}.get(ending)
    try:
        try:
            with server._manual_compress_turn("runtime", session):
                samples["active"] = activate(req)
                assert samples["active"]["complete"] and samples["active"]["running"]
                assert samples["active"]["state_snapshot"]["events"] == []
                if ending.startswith("compact_"):
                    session["agent"].compression_in_place = ending == "compact_in_place"
                    removed, _ = server._compress_session_history(session)
                    assert removed > 0
                    samples["committed"] = activate(req)
                    assert samples["committed"]["complete"] and samples["committed"]["running"]
                if exception:
                    raise exception("controlled manual exit")
        except (RuntimeError, KeyboardInterrupt) as exc:
            assert exception is not None and isinstance(exc, exception)
        samples["after"] = activate(req)
        assert samples["after"]["complete"] and not samples["after"]["running"]
        assert samples["after"]["status"] == "idle" and samples["after"]["state_snapshot"]["events"] == []
        assert not session.get("_manual_compress_active")
        assert snapshot(session, "runtime", include_internal=True)["events"] == retained
        source = next(row for row in db.get_messages(failed.parent, include_compacted=True)
                      if row["message_uid"] == failed.source["message_uid"])
        saved = source["display_metadata"]["turn_terminal"]
        assert saved == failed.saved
        with session["history_lock"]:
            server._set_session_running(session, True)
        assert snapshot(session, "runtime") is None
        with session["history_lock"]:
            server._start_inflight_turn(session, "genuine next question")
        assert snapshot(session, "runtime")["events"] == []
        samples["next_without_source"] = activate(req)
        assert not samples["next_without_source"]["complete"]
        assert samples["next_without_source"]["reason"] == "runtime_unavailable"
    finally:
        record_property("native_terminal", json.dumps({"source": failed.source, "terminal": failed.saved,
                                                       "retained_events": retained}))
        record_property("recovery_payloads", json.dumps({"ending": ending, "samples": samples}))


@pytest.mark.parametrize("invalid", ["missing_source", "wrong_db", "wrong_uid", "unknown_output"])
def test_retained_native_error_maintenance_does_not_weaken_proof(failed_native_turn, invalid):
    failed = failed_native_turn
    session = failed.session
    req = failed_turn_request(failed)
    if invalid == "missing_source":
        session["inflight_turn"].pop("_terminal_source")
    elif invalid == "wrong_db":
        session["inflight_turn"]["_terminal_source"]["db_path"] = "/different-owner/state.db"
    elif invalid == "wrong_uid":
        session["inflight_turn"]["_terminal_source"]["message_uid"] = "unproven-source"
    else:
        server._emit("reasoning.delta", "runtime", {"text": "unaccounted late output"})
    with server._manual_compress_turn("runtime", session):
        view = activate(req)
        assert not view["complete"] and view["reason"] == "runtime_unavailable"


@pytest.mark.parametrize("failed_native_turn", [
    {"terminal": "error", "noting_enabled": False},
    {"terminal": "complete", "noting_enabled": False},
], indirect=True, ids=["error", "complete"])
@pytest.mark.parametrize("in_place", [True, False], ids=["in_place", "rotate"])
@pytest.mark.parametrize("summary_mode", ["native_anchor", "kept_source", "real_compressor"])
def test_noting_off_native_compaction_retention_matrix(
    failed_native_turn, monkeypatch, record_property, in_place, summary_mode,
):
    """No weakened expectation: collect every phase, then require full recovery."""
    from tui_gateway.inflight_output import snapshot

    failed = failed_native_turn
    session, db, source_uid = failed.session, failed.db, failed.source["message_uid"]
    session["agent"].compression_in_place = in_place
    compressor = session["agent"].context_compressor
    summary_before = copy.deepcopy(compressor.compress.return_value)
    summary_used = summary_before
    if summary_mode == "kept_source":
        kept = session["history"][-2:] if failed.saved is None else [summary_before[-1], session["history"][-1]]
        compressor.compress.return_value = [summary_before[0], *copy.deepcopy(kept)]
        summary_used = compressor.compress.return_value
    elif summary_mode == "real_compressor":
        from agent.context_compressor import ContextCompressor, SUMMARY_PREFIX
        native_compressor = ContextCompressor(model="test/model", quiet_mode=True, config_context_length=2048,
                                              protect_first_n=1, protect_last_n=2, tail_mode="legacy")
        native_compressor.compression_count = compressor.compression_count
        summary_used = {"external_summary": SUMMARY_PREFIX + " controlled native summary", "calls": []}
        def summarize(*args, **kwargs):
            summary_used["calls"].append(copy.deepcopy(args[1]))
            return summary_used["external_summary"]
        monkeypatch.setattr(native_compressor, "_summarize_window", summarize)
        session["agent"].context_compressor = native_compressor
    samples, reads, guards = {}, [], []
    phase = ["before"]
    original_read, original_envelope = recovery_view.read_view, recovery_view._envelope

    def read(*args, **kwargs):
        value = original_read(*args, **kwargs)
        reads.append({"phase": phase[0], "references": copy.deepcopy(kwargs.get("identities", [])),
                      "tip_id": value["tip_id"], "lineage": value["lineage"], "lease": value["lease"],
                      "identities": copy.deepcopy(value["identities"])})
        return value

    def envelope(*args, **kwargs):
        try:
            return original_envelope(*args, **kwargs)
        except recovery_view.RecoveryViewError as exc:
            guards.append({"phase": phase[0], "reason": exc.reason,
                           "traceback": [{"file": frame.filename, "line": frame.lineno, "function": frame.name}
                                         for frame in traceback.extract_tb(exc.__traceback__)]})
            raise

    monkeypatch.setattr(recovery_view, "read_view", read)
    monkeypatch.setattr(recovery_view, "_envelope", envelope)
    req = failed_turn_request(failed)

    def capture(label):
        phase[0] = label
        turn = session.get("inflight_turn")
        with db._read_ctx() as conn:
            rows = [dict(row) for row in conn.execute(
                "SELECT id,session_id,role,message_uid,active,compacted,display_metadata FROM messages "
                "WHERE message_uid=? ORDER BY id", (source_uid,))]
        for row in rows:
            row["display_metadata"] = json.loads(row["display_metadata"]) if row["display_metadata"] else None
        samples[label] = {"snapshot": snapshot(session, "runtime", include_internal=True),
                          "inflight": ({key: copy.deepcopy(value) for key, value in turn.items()
                                        if key != "_terminal_token"} if isinstance(turn, dict) else turn),
                          "running": session["running"], "manual_active": bool(session.get("_manual_compress_active")),
                          "source_rows": rows, "recovery": activate(req)}

    try:
        capture("before")
        with server._manual_compress_turn("runtime", session):
            capture("active")
            removed, _ = server._compress_session_history(session)
            assert removed > 0
            capture("committed")
        capture("after")
        assert samples["before"]["recovery"]["complete"]
        assert samples["active"]["recovery"]["complete"]
        assert samples["committed"]["recovery"]["complete"]
        assert samples["after"]["recovery"]["complete"]
        assert not samples["after"]["recovery"]["running"]
    finally:
        record_property("noting_off_matrix", json.dumps({"terminal": "error" if failed.saved else "complete",
            "in_place": in_place, "summary_mode": summary_mode, "source": failed.source,
            "summary_dependency_before": summary_before, "summary_dependency_used": summary_used,
            "samples": samples, "reads": reads, "guards": guards}, default=str))


@pytest.mark.parametrize("failed_native_turn", [
    {"noting_enabled": False, "persist_partial": False, "committed_frames": True},
    {"noting_enabled": False, "persist_partial": True, "committed_frames": True},
    {"noting_enabled": False, "persist_partial": False, "committed_frames": "source"},
    {"noting_enabled": False, "persist_partial": True, "committed_frames": "source"},
], indirect=True, ids=["capsule", "persisted_partial", "capsule_source_frame", "partial_source_frame"])
@pytest.mark.parametrize("in_place", [True, False], ids=["in_place", "rotate"])
def test_settled_alias_recovers_all_native_receipt_references(failed_native_turn, in_place, record_property):
    from hermes_state_recovery_view import read_view, selector
    from tui_gateway.inflight_output import snapshot
    failed = failed_native_turn
    session = failed.session
    session["agent"].compression_in_place = in_place
    if failed.persist_partial:
        compressor = session["agent"].context_compressor
        compressor.compress.return_value = [compressor.compress.return_value[0], *copy.deepcopy(session["history"][-2:])]
    original = copy.deepcopy(snapshot(session, "runtime", include_internal=True))
    req = failed_turn_request(failed)
    samples = {"before": activate(req)}
    try:
        assert samples["before"]["complete"]
        with server._manual_compress_turn("runtime", session):
            samples["active"] = activate(req)
            assert samples["active"]["complete"]
            removed, _ = server._compress_session_history(session)
            assert removed > 0
            samples["committed"] = activate(req)
            assert samples["committed"]["complete"] and samples["committed"]["running"]
        result = activate(req)
        assert result["complete"] and not result["running"] and result["state_snapshot"]["events"] == []
        assert "_settled_reference_aliases" not in json.dumps(result)
        assert snapshot(session, "runtime", include_internal=True)["events"] == original["events"]
        raw = read_view(failed.db, failed.parent, "default", [selector()], identities=recovery_view._references(original))
        receipt = original["events"][-1]["payload"]["persisted_turn"]
        known = {row["message_uid"]: row for row in raw["identities"]}
        assert recovery_view._terminal_snapshot_accounted(original, raw, known)
        assert all(known[ref["message_uid"]].get("_settled_reference_aliases") for ref in receipt["source_messages"])
    finally:
        samples["after"] = activate(req)
        raw = read_view(failed.db, failed.parent, "default", [selector()], identities=recovery_view._references(original))
        record_property("native_alias_receipt", json.dumps({"before": original, "raw": raw, "samples": samples}, default=str))


@pytest.mark.parametrize("failed_native_turn", [
    {"noting_enabled": False, "persist_partial": False, "committed_frames": "bad_row"},
    {"noting_enabled": False, "persist_partial": True, "committed_frames": "bad_row"},
    {"noting_enabled": False, "persist_partial": True, "committed_frames": "bad_row_with_source"},
], indirect=True, ids=["capsule", "persisted_partial", "mixed_committed_frames"])
def test_settled_alias_cannot_lend_proof_to_wrong_committed_frame(failed_native_turn):
    failed = failed_native_turn
    req = failed_turn_request(failed)
    with server._manual_compress_turn("runtime", failed.session):
        removed, _ = server._compress_session_history(failed.session)
        assert removed > 0
        view = activate(req)
        assert not view["complete"] and view["reason"] == "runtime_unavailable"
    view = activate(req)
    assert not view["complete"] and view["reason"] == "runtime_unavailable"


@pytest.mark.parametrize("failed_native_turn", [{"noting_enabled": False}], indirect=True)
def test_settled_alias_invisible_old_fact_rewrite_between_d0_and_d1_is_rejected(failed_native_turn, monkeypatch):
    failed = failed_native_turn
    req = failed_turn_request(failed)
    original = recovery_view.snapshot
    def rewrite(*args, **kwargs):
        state = original(*args, **kwargs)
        failed.db._write_sql("UPDATE messages SET content='rewritten original' WHERE id=?", (failed.source["_row_id"],))
        return state
    with server._manual_compress_turn("runtime", failed.session):
        removed, _ = server._compress_session_history(failed.session)
        assert removed > 0 and activate(req)["complete"]
        monkeypatch.setattr(recovery_view, "snapshot", rewrite)
        view = activate(req)
        assert not view["complete"] and view["reason"] == "runtime_unavailable"
