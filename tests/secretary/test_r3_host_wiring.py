"""C9-H production call sites: native compression, atomic intervals, response ACK and completed sync."""

from copy import deepcopy
from types import MethodType, SimpleNamespace
from unittest.mock import MagicMock
import threading
import time

import httpx
import pytest

from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
from hermes_state import SessionDB
from secretary.noting_scope import owning_db_scope
from tests.agent.test_context_compaction_request import _agent


def summary(uid=None):
    result = {"role": "user", "content": SUMMARY_PREFIX + "Native retained work\n" + _SUMMARY_END_MARKER,
              "_compressed_summary": True}
    if uid:
        result["message_uid"] = uid
    return result


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    monkeypatch.setattr(httpx.Client, "send", lambda *a, **k: pytest.fail("No external HTTP"))
    monkeypatch.setattr(httpx.AsyncClient, "send", lambda *a, **k: pytest.fail("No external HTTP"))
    config = tmp_path / "config.yaml"
    config.write_text("noting:\n  enabled: true\n")
    db = SessionDB(tmp_path / "state.db")
    db.create_session("native-request-probe", source="cli", system_prompt="Native probe root")
    for i in range(25):
        db.append_message("native-request-probe", "user", f"Question {i} " + "relevant original context " * 100)
        db.append_message("native-request-probe", "assistant", f"Answer {i} " + "relevant original answer " * 100)
    with owning_db_scope(db):
        parent = _agent(db, monkeypatch, tmp_path)
        parent.context_compressor.context_length = 130_000
        parent.context_compressor.threshold_tokens = 75_000
        parent.context_compressor.protect_first_n = 2
        parent.context_compressor.protect_last_n = 4
        parent.context_compressor.tail_token_budget = 5000
        parent._disable_streaming = True
        parent.compression_enabled = True
        from secretary.noting_scope import bind_main_runtime
        bind_main_runtime(parent)
        frozen = []
        def spawn(owner, admission, *, parent_active_messages=None, **kwargs):
            from secretary.noting_child import freeze_parent_active_prefix
            prefix = freeze_parent_active_prefix(owner, admission.anchor_message_uid, parent_active_messages)
            frozen.append((admission, prefix))
            return threading.Thread(target=lambda: None)
        monkeypatch.setattr("secretary.noting_child.spawn_noting_task", spawn)
        monkeypatch.setattr(parent.context_compressor, "_call_summary_llm", lambda *a, **k:
                            "## Progress\nThe earlier work and its conclusions remain relevant.\n"
                            "## Open\nContinue the latest request with its original conditions and evidence.")
        yield parent, db, config, frozen
        parent.close()
    db.close()


@pytest.mark.parametrize("in_place", [True, False])
@pytest.mark.parametrize("manual", [True, False])
def test_native_compression_prepares_once_and_records_real_boundary(runtime, in_place, manual):
    from agent.conversation_compression_manual import compress_now, parse_compress_args
    parent, db, config, frozen = runtime
    parent.compression_in_place = in_place
    if manual:
        result = compress_now(parent, parent._session_messages, parse_compress_args(""))
        assert result.status == "compressed"
    else:
        parent._compress_context(parent._session_messages, None, approx_tokens=76_000)
    assert len(frozen) == 1
    admission, prefix = frozen[0]
    assert admission.kind == ("manual" if manual else "auto_compaction")
    assert prefix[-1]["message_uid"] == admission.anchor_message_uid
    with db._read_ctx() as conn:
        state = conn.execute("SELECT interval_id FROM secretary_noting_compaction_state WHERE conversation_ref=?",
                             (admission.conversation_ref,)).fetchone()
        boundary = db._noting_latest_compaction_uid_conn(conn, admission.conversation_ref)
    assert boundary and state["interval_id"] == boundary
    assert boundary != admission.compression_interval_id


def test_idle_request_marker_prevents_a_second_spawn_in_native_pipeline(runtime):
    from secretary.noting_policy import ContextMeasurement
    from secretary.noting_runtime import prepare_joint_noting
    parent, db, config, frozen = runtime
    config.write_text("noting:\n  enabled: true\n  idle:\n    enabled: true\n    threshold_tokens: 1000\n")
    db.noting_idle_turn_finished(parent._secretary_conversation_ref, 1000)
    decision = prepare_joint_noting(parent, trigger="idle", measurement=ContextMeasurement(50000, 130000, 75000), now=2000)
    assert decision.action == "admit"
    parent._compress_context(parent._session_messages, None, approx_tokens=76000, trigger="noting_joint_idle")
    assert len(frozen) == 1


@pytest.mark.parametrize("enabled", [True, False])
def test_native_compression_runs_with_noting_off_or_spawn_failure(runtime, monkeypatch, enabled):
    parent, db, config, frozen = runtime
    if not enabled:
        config.write_text("noting:\n  enabled: false\n")
    else:
        def failed(*args, **kwargs):
            raise OSError("controlled child freeze failure")
        monkeypatch.setattr("secretary.noting_child.spawn_noting_task", failed)
    parent._compress_context(parent._session_messages, None, approx_tokens=76000, force=True)
    assert parent.context_compressor.compression_count == 1
    assert any(row.get("_compressed_summary") for row in db.get_messages(parent.session_id))
    assert not frozen
    if not enabled:
        with db._read_ctx() as conn:
            assert conn.execute("SELECT COUNT(*) FROM secretary_noting_compaction_state").fetchone()[0] == 0


def test_summary_failure_preserves_force_occupation_and_dispatch_notice(runtime, monkeypatch):
    from secretary.noting_runtime import maybe_admit_force_from_pressure
    parent, db, config, frozen = runtime
    assert maybe_admit_force_from_pressure(parent, 64000, messages=parent._session_messages).startswith("admit")
    before = deepcopy(parent._session_messages)
    def failed(*args, **kwargs):
        raise OSError("native summary unavailable")
    monkeypatch.setattr(parent.context_compressor, "compress", failed)
    with pytest.raises(OSError, match="native summary unavailable"):
        parent._compress_context(parent._session_messages, None, force=True)
    assert parent._session_messages == before
    assert any((row.get("display_metadata") or {}).get("noting_force_dispatch") for row in db.get_messages(parent.session_id))
    with db._read_ctx() as conn:
        assert db.noting_force_occupied_conn(conn, parent._secretary_conversation_ref, "conversation_start")
    assert len(frozen) == 1


@pytest.mark.parametrize("proved", [True, False])
def test_in_place_boundary_interval_is_committed_before_competing_admission(runtime, monkeypatch, proved):
    from secretary.noting_policy import ContextMeasurement
    from secretary.noting_runtime import try_admit_force
    parent, db, config, frozen = runtime
    ref = parent._secretary_conversation_ref
    peer = SessionDB(db.db_path)
    entered, release, peer_write = threading.Event(), threading.Event(), threading.Event()
    original = db.noting_record_compaction_conn
    def observe(conn, owner):
        entered.set()
        assert release.wait(5)
        return original(conn, owner)
    monkeypatch.setattr(db, "noting_record_compaction_conn", observe)
    original_write = peer._execute_write
    def wait_write(fn, **kwargs):
        peer_write.set()
        return original_write(fn, **kwargs)
    monkeypatch.setattr(peer, "_execute_write", wait_write)
    outcomes, errors = [], []
    def publish():
        try:
            rows = db.get_messages(parent.session_id)
            kwargs = {"covered_ids": [row["id"] for row in rows]} if proved else {}
            db.archive_and_compact(parent.session_id, [summary("atomic-boundary")], **kwargs)
        except Exception as error:
            errors.append(error)
    def force():
        outcomes.append(try_admit_force(peer, ref, ContextMeasurement(64000, 130000, 75000)))
    writer = threading.Thread(target=publish)
    contender = threading.Thread(target=force)
    try:
        writer.start()
        assert entered.wait(5)
        contender.start()
        assert peer_write.wait(5)
        release.set()
        writer.join(5)
        contender.join(5)
        assert not writer.is_alive() and not contender.is_alive() and not errors
        assert outcomes[0].action == "admit"
        assert outcomes[0].admission.compression_interval_id == "atomic-boundary"
    finally:
        release.set()
        writer.join(5)
        if contender.ident:
            contender.join(5)
        peer.close()


def response(content="", calls=None, **extra):
    return SimpleNamespace(choices=[SimpleNamespace(finish_reason="tool_calls" if calls else "stop",
                           message=SimpleNamespace(content=content, tool_calls=calls))], usage=None, **extra)


def call(name="scheduler", arguments="{}"):
    return SimpleNamespace(id="c1", type="function", function=SimpleNamespace(name=name, arguments=arguments))


@pytest.mark.parametrize("streaming", [True, False])
@pytest.mark.parametrize("answer,accepted", [
    ({}, False), (None, False), (response("   "), False),
    (response("actual response"), True), (response(calls=[call()]), True),
    (response(calls=[call(arguments="{")]), True),
    (response(calls=[call(arguments="{"), call()]), True),
    (response(calls=[call(name="", arguments="")]), False),
    (response("untrusted", status="failed"), False),
    (response("untrusted", error="provider failure"), False),
])
def test_formal_provider_call_ack_requires_actual_successful_nonempty_output(runtime, monkeypatch, streaming, answer, accepted):
    from agent.turn_api_call import perform_api_call
    parent, db, config, frozen = runtime
    monkeypatch.setattr("agent.turn_api_call._should_stream", lambda *args: streaming)
    monkeypatch.setattr(parent, "_interruptible_api_call", lambda *args, **kwargs: answer)
    monkeypatch.setattr(parent, "_interruptible_streaming_api_call", lambda *args, **kwargs: answer)
    ack = []
    monkeypatch.setattr("secretary.reminder_request.acknowledge_carried_reminders", lambda *args: ack.append(True))
    payload = {"model": "test/model", "messages": [{"role": "user", "content": "review the reminder"}]}
    result = perform_api_call(parent, api_kwargs=payload, _original_api_kwargs=payload, _llm_middleware_trace=[],
        _moa_prepared_request=None, _retry=SimpleNamespace(), thinking_spinner=None, retry_count=0,
        api_call_count=1, api_request_id="host-ack", effective_task_id="default", turn_id="host-turn", interrupted=False)
    assert result.action == "fallthrough"
    assert bool(ack) is accepted


def test_provider_transport_failure_never_acknowledges(runtime, monkeypatch):
    from agent.turn_api_call import perform_api_call
    parent, db, config, frozen = runtime
    def failed(*args, **kwargs):
        raise OSError("transport unavailable")
    monkeypatch.setattr(parent, "_interruptible_api_call", failed)
    ack = MagicMock()
    monkeypatch.setattr("secretary.reminder_request.acknowledge_carried_reminders", ack)
    payload = {"messages": []}
    with pytest.raises(OSError, match="transport unavailable"):
        perform_api_call(parent, api_kwargs=payload, _original_api_kwargs=payload, _llm_middleware_trace=[],
            _moa_prepared_request=None, _retry=SimpleNamespace(), thinking_spinner=None, retry_count=0,
            api_call_count=1, api_request_id="host-failure", effective_task_id="default", turn_id="host-turn", interrupted=False)
    ack.assert_not_called()


@pytest.mark.parametrize("failed,interrupted,budget_exhausted,accepted", [
    (False, False, False, True), (True, False, False, False),
    (False, True, False, False), (False, False, True, False),
])
def test_finalizer_passes_real_outcome_to_generic_sync(monkeypatch, failed, interrupted, budget_exhausted, accepted):
    from agent.turn_finalizer import finalize_turn
    from run_agent import AIAgent
    from tests.agent.test_turn_finalizer_final_response_persistence import FakeAgent
    monkeypatch.setattr("hermes_cli.plugins.invoke_hook", lambda *a, **k: [])
    current = FakeAgent()
    current._memory_manager = MagicMock()
    current._sync_external_memory_for_turn = MethodType(AIAgent._sync_external_memory_for_turn, current)
    messages = [{"role": "user", "content": "Review the detailed pending work"}]
    result = finalize_turn(current, final_response="A concrete response or a visible failure explanation.",
        api_call_count=current.max_iterations if budget_exhausted else 1, interrupted=interrupted, failed=failed,
        messages=messages, conversation_history=[], effective_task_id="task", turn_id="turn",
        user_message="Review the detailed pending work", original_user_message="Review the detailed pending work",
        _should_review_memory=False, _turn_exit_reason="budget_stop" if budget_exhausted else "text_response(stop)")
    assert result["completed"] is accepted
    assert current._memory_manager.sync_all.called is accepted
    assert current._memory_manager.queue_prefetch_all.called is accepted


@pytest.mark.parametrize("interrupted,error,accepted", [(False, None, True), (True, None, False), (False, "provider failed", False)])
def test_existing_external_runtime_sync_uses_actual_completed_flags(monkeypatch, interrupted, error, accepted):
    from agent.codex_runtime import _finish_codex_turn
    from run_agent import AIAgent
    monkeypatch.setattr("agent.codex_runtime._record_codex_app_server_compaction", lambda *a: None)
    monkeypatch.setattr("agent.codex_runtime._record_codex_app_server_usage", lambda *a, **k: {})
    current = SimpleNamespace(_memory_manager=MagicMock(), _skill_nudge_interval=0, valid_tool_names=set(), session_id="external-turn")
    current._sync_external_memory_for_turn = MethodType(AIAgent._sync_external_memory_for_turn, current)
    turn = SimpleNamespace(tool_iterations=1, interrupted=interrupted, error=error, final_text="Visible result or error explanation")
    _finish_codex_turn(current, turn, [], original_user_message="Review pending work", should_review_memory=False)
    assert current._memory_manager.sync_all.called is accepted
    assert current._memory_manager.queue_prefetch_all.called is accepted


def test_native_disabled_skips_all_noting_preparation(runtime, monkeypatch):
    parent, db, config, frozen = runtime
    parent.compression_enabled = False
    original = deepcopy(parent._session_messages)
    monkeypatch.setattr(parent, "_interruptible_api_call", lambda *a, **k: response("Completed without automatic compression."))
    result = parent.run_conversation("Continue the pending review", conversation_history=original)
    assert result["completed"] and not frozen
    assert parent.context_compressor.compression_count == 0
    with db._read_ctx() as conn:
        assert conn.execute("SELECT COUNT(*) FROM secretary_noting_compaction_state").fetchone()[0] == 0


def test_native_db_failure_does_not_advance_interval(runtime, monkeypatch):
    from secretary.noting_runtime import maybe_admit_force_from_pressure
    parent, db, config, frozen = runtime
    assert maybe_admit_force_from_pressure(parent, 64000, messages=parent._session_messages).startswith("admit")
    def fail_native(*args, **kwargs):
        raise OSError("native publication failed")
    monkeypatch.setattr(db, "_archive_named_rows", fail_native)
    before = deepcopy(parent._session_messages)
    output, _ = parent._compress_context(parent._session_messages, None, force=True)
    assert output == before  # Native publication failures retain the original transcript.
    with db._read_ctx() as conn:
        row = conn.execute("SELECT interval_id FROM secretary_noting_compaction_state").fetchone()
        assert row["interval_id"] == "conversation_start"
    assert not any(row.get("_compressed_summary") for row in db.get_messages(parent.session_id))
    assert any((row.get("display_metadata") or {}).get("noting_force_dispatch") for row in db.get_messages(parent.session_id))


@pytest.mark.parametrize("omit_carrier", [False, True])
def test_real_loop_compresses_before_carrier_and_acks_only_final_wire_carriage(runtime, monkeypatch, omit_carrier):
    from secretary import reminder_request, reminders, schedules
    from secretary.scheduler_time import epoch_to_utc_iso
    parent, db, config, frozen = runtime
    config.write_text("scheduler:\n  enabled: true\nnoting:\n  enabled: false\n")
    now = time.time()
    store = schedules.SchedulerStore(db, parent._secretary_conversation_ref, session_id=parent.session_id)
    created = store.create("Review the actual retained evidence", epoch_to_utc_iso(now - 1), "deferred", now=now)
    assert created["success"]
    sid = created["schedule"]["schedule_id"]
    claimed = schedules.claim_due(db, sid, owner="host-loop", now=now)
    assert claimed is not None
    reminders.queue_pending_for_claim(db, claimed, now=now)
    events, actual_wire = [], []
    prepare, materialize = reminder_request.prepare_pending_reminders, reminder_request.materialize_pending_reminders
    native_summary = parent.context_compressor._call_summary_llm
    def record_prepare(*args, **kwargs):
        events.append("prepare")
        return prepare(*args, **kwargs)
    def record_materialize(*args, **kwargs):
        events.append("materialize")
        return materialize(*args, **kwargs)
    def record_summary(*args, **kwargs):
        events.append("summary")
        assert not any("SCHEDULED ATTENTION" in str(row.get("content")) for row in db.get_messages(parent.session_id))
        return native_summary(*args, **kwargs)
    monkeypatch.setattr(reminder_request, "prepare_pending_reminders", record_prepare)
    monkeypatch.setattr(reminder_request, "materialize_pending_reminders", record_materialize)
    monkeypatch.setattr(parent.context_compressor, "_call_summary_llm", record_summary)
    def dispatch(payload, **kwargs):
        actual_wire.append(deepcopy(payload["messages"]))
        return response("The pending evidence has been reviewed.")
    monkeypatch.setattr(parent, "_interruptible_api_call", dispatch)
    if omit_carrier:
        from hermes_cli import middleware
        native_middleware = middleware.run_llm_execution_middleware
        def remove_before_dispatch(api_kwargs, call_next, **kwargs):
            payload = deepcopy(api_kwargs)
            payload["messages"] = [row for row in payload["messages"] if "SCHEDULED ATTENTION" not in str(row.get("content"))]
            return native_middleware(payload, call_next, **kwargs)
        monkeypatch.setattr(middleware, "run_llm_execution_middleware", remove_before_dispatch)
    parent.context_compressor.update_from_response({"prompt_tokens": 90000})
    result = parent.run_conversation("Continue the retained work and review pending evidence", conversation_history=parent._session_messages)
    assert result["completed"], result
    assert parent.context_compressor.compression_count == 1 and not frozen
    assert events.index("prepare") < events.index("summary") < events.index("materialize")
    assert actual_wire and any("SCHEDULED ATTENTION" in str(row.get("content")) for row in actual_wire[0]) is not omit_carrier
    assert bool(reminders.pull_pending(db, parent._secretary_conversation_ref)) is omit_carrier


@pytest.mark.parametrize("successful", [True, False])
def test_actual_native_commit_alone_retires_force_notice_and_advances_interval(runtime, monkeypatch, successful):
    from secretary.noting_runtime import maybe_admit_force_from_pressure
    parent, db, config, frozen = runtime
    assert maybe_admit_force_from_pressure(parent, 64000, messages=parent._session_messages).startswith("admit")
    notice = next(row for row in db.get_messages(parent.session_id)
                  if (row.get("display_metadata") or {}).get("noting_force_dispatch"))
    if not successful:
        monkeypatch.setattr(parent.context_compressor, "compress", lambda messages, **kwargs: deepcopy(messages))
    output, _ = parent._compress_context(parent._session_messages, None, force=True)
    assert any(row.get("message_uid") == notice["message_uid"] for row in output) is not successful
    assert db._read_one("SELECT id FROM messages WHERE message_uid=?", (notice["message_uid"],)) is not None
    with db._read_ctx() as conn:
        interval = conn.execute("SELECT interval_id FROM secretary_noting_compaction_state").fetchone()[0]
    assert (interval != "conversation_start") is successful
    assert len(frozen) == 1


def test_external_fact_refuses_noting_before_actual_manual_native_compaction(runtime):
    from secretary.noting_runtime import note_actual_main_execution
    parent, db, config, frozen = runtime
    assert note_actual_main_execution(parent, "external")
    parent._compress_context(parent._session_messages, None, force=True)
    assert parent.context_compressor.compression_count == 1 and not frozen
    assert db._read_one("SELECT COUNT(*) AS n FROM secretary_noting_admissions")["n"] == 0
    assert parent._secretary_conversation_ref in parent._secretary_external_notice_refs
