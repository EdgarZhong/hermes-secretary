"""C7: real admission transactions/native boundary facts, with child/model boundary controlled."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading

import pytest

from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
from secretary import noting_runtime as rt
from secretary.noting_policy import ContextMeasurement
from tests.hermes_state._secretary_noting_harness import add, make, open_noting_db, ref_of
from tests.secretary.test_noting_runtime import _agent

PRESSURE = ContextMeasurement(64_000, 130_000, 75_000)


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    db = open_noting_db(tmp_path / "state.db")
    make(db, "s", source="cli")
    add(db, "s", "original source", "m1")
    parent = _agent(db, "s")
    parent._session_messages = db.get_messages_as_conversation("s")
    calls = []
    def spawn(owner, admission, *, parent_active_messages=None, **kwargs):
        from secretary.noting_child import freeze_parent_active_prefix
        prefix = freeze_parent_active_prefix(owner, admission.anchor_message_uid, parent_active_messages)
        calls.append((admission, prefix))
        return threading.Thread(target=lambda: None)
    monkeypatch.setattr("secretary.noting_child.spawn_noting_task", spawn)
    monkeypatch.setattr("secretary.noting_timers.arm_idle_timer", lambda *a: None)
    yield parent, db, calls
    db.close()


def append(parent, db, uid):
    row = add(db, "s", "source " + uid, uid)
    parent._session_messages = db.get_messages_as_conversation("s")
    return row


def compact(parent, db, uid):
    db.archive_and_compact("s", [{"role": "user", "content": SUMMARY_PREFIX + "summary\n" + _SUMMARY_END_MARKER,
                                 "_compressed_summary": True, "message_uid": uid}])
    parent._session_messages = db.get_messages_as_conversation("s")
    return rt.note_successful_compaction(parent, committed=True)


@pytest.mark.parametrize("trigger", ["force", "idle", "manual", "auto_compaction"])
def test_four_entries_share_force_interval_occupation(runtime, trigger):
    parent, db, calls = runtime
    ref = ref_of(db, "s")
    assert rt.prepare_joint_noting(parent, trigger="force", measurement=PRESSURE).action == "admit"
    append(parent, db, "m2")
    db.noting_idle_turn_finished(ref, 1000)
    decision = rt.prepare_joint_noting(parent, trigger=trigger, measurement=PRESSURE, now=2000)
    assert decision.reason == "force_interval_occupied"
    assert len(calls) == 1
    assert calls[0][0].compression_interval_id == "conversation_start"


@pytest.mark.parametrize("status", ["finished", "failed", "cancelled"])
def test_child_terminal_status_and_rewind_never_rearm_force(runtime, status):
    parent, db, calls = runtime
    row = append(parent, db, "m2")
    first = rt.prepare_joint_noting(parent, trigger="force", measurement=PRESSURE).admission
    db.noting_child_register(first.admission_id, child_session_id="child-1", profile=None)
    db.noting_child_finish(first.admission_id, status=status)
    db.rewind_to_message("s", row)
    append(parent, db, "m3")
    assert rt.prepare_joint_noting(parent, trigger="manual").reason == "force_interval_occupied"
    assert len(calls) == 1


def test_successful_native_boundary_only_opens_next_interval_without_waiting_child(runtime):
    parent, db, calls = runtime
    first = rt.prepare_joint_noting(parent, trigger="force", measurement=PRESSURE).admission
    db.noting_child_register(first.admission_id, child_session_id="still-running", profile=None)
    assert not rt.note_successful_compaction(parent, committed=False)
    append(parent, db, "m2")
    assert rt.prepare_joint_noting(parent, trigger="auto_compaction").reason == "force_interval_occupied"
    assert compact(parent, db, "boundary1")
    assert not rt.note_successful_compaction(parent, committed=True)
    append(parent, db, "m3")
    second = rt.prepare_joint_noting(parent, trigger="force", measurement=PRESSURE).admission
    assert second.compression_interval_id == "boundary1"
    assert db.noting_child(first.admission_id)["status"] == "running"
    assert len(calls) == 2


@pytest.mark.parametrize("source", ["native", None, "external"])
@pytest.mark.parametrize("trigger", ["manual", "auto_compaction"])
def test_native_callback_always_runs_and_external_never_freezes(runtime, monkeypatch, source, trigger):
    parent, db, calls = runtime
    if source:
        rt.note_actual_main_execution(parent, source)
    order = []
    if source == "external":
        monkeypatch.setattr(rt, "_freeze_and_log_attempt", lambda *a: pytest.fail("No external freeze"))
    result, native = rt.run_joint_cycle(parent, trigger=trigger,
                                        native_compact=lambda: (order.append("native"), "compacted")[1])
    assert native == "compacted" and order == ["native"]
    assert len(calls) == (0 if source == "external" else 1)
    assert result.action == ("skip" if source == "external" else "admit")


def test_noting_failure_and_off_switch_preserve_native_callback_and_exception(runtime, monkeypatch):
    parent, db, calls = runtime
    monkeypatch.setattr(rt, "_freeze_and_log_attempt", lambda *args: (_ for _ in ()).throw(OSError("freeze failed")))
    observed = []
    decision, result = rt.run_joint_cycle(parent, trigger="manual", native_compact=lambda: observed.append(1))
    assert decision.reason == "trigger_error" and observed == [1]
    (Path(db.db_path).parent / "config.yaml").write_text("noting:\n  enabled: false\n")
    def native_failure():
        observed.append(2)
        raise OSError("native error")
    with pytest.raises(OSError, match="native error"):
        rt.run_joint_cycle(parent, trigger="auto_compaction", native_compact=native_failure)
    assert observed == [1, 2] and not calls


def test_two_concurrent_force_admissions_share_one_transaction_predicate(runtime):
    parent, db, calls = runtime
    barrier = threading.Barrier(2)
    def admit():
        barrier.wait()
        return rt.try_admit_force(db, ref_of(db, "s"), PRESSURE)
    with ThreadPoolExecutor(max_workers=2) as pool:
        decisions = list(pool.map(lambda _: admit(), range(2)))
    assert sorted(d.action for d in decisions) == ["admit", "skip"]
    with db._read_ctx() as conn:
        assert conn.execute("SELECT COUNT(*) FROM secretary_noting_admissions WHERE kind='force'").fetchone()[0] == 1


def test_reopen_keeps_force_occupation_even_when_anchor_was_rewound(runtime):
    parent, db, calls = runtime
    rt.prepare_joint_noting(parent, trigger="force", measurement=PRESSURE)
    append(parent, db, "m2")
    reopened = open_noting_db(db.db_path)
    try:
        owner = _agent(reopened, "s")
        owner._session_messages = reopened.get_messages_as_conversation("s")
        assert rt.prepare_joint_noting(owner, trigger="manual").reason == "force_interval_occupied"
        assert reopened.noting_admission(1)["compression_interval_id"] == "conversation_start"
    finally:
        reopened.close()


def test_idle_disabled_never_reads_usage_and_new_turn_cancels_existing_period(runtime, monkeypatch):
    parent, db, calls = runtime
    ref = ref_of(db, "s")
    (Path(db.db_path).parent / "config.yaml").write_text("noting:\n  enabled: true\n")
    monkeypatch.setattr("agent.context_compaction_request.read_context_usage", lambda *args: pytest.fail("Idle is off"))
    assert not rt.note_main_turn_finished(parent)
    assert rt.prepare_joint_noting(parent, trigger="idle").reason == "idle_disabled"
    assert not calls
    db.noting_idle_turn_finished(ref, 1000, due_at=1500)
    rt.note_main_turn_started(parent, at=1400)
    assert db.noting_idle_state(ref)["due_at"] is None


def test_parent_prefix_is_frozen_before_native_mutation(runtime):
    parent, db, calls = runtime
    parent._session_messages[0]["content"] = [{"type": "text", "text": "original"},
                                             {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}]
    def native():
        assert len(calls) == 1
        parent._session_messages[0]["content"][0]["text"] = "changed by compaction"
        return "native"
    rt.run_joint_cycle(parent, trigger="manual", native_compact=native)
    assert calls[0][1][0]["content"][0]["text"] == "original"
    assert calls[0][1][0]["content"][1]["type"] == "image_url"


@pytest.mark.parametrize("api_mode", ["codex_responses", "chat_completions"])
@pytest.mark.parametrize("trigger", ["force", "idle"])
def test_external_execution_fact_overrides_transport_shape_before_freeze(runtime, monkeypatch, api_mode, trigger):
    parent, db, calls = runtime
    parent.api_mode = api_mode
    parent.provider = "custom"
    assert rt.note_actual_main_execution(parent, "external")
    assert rt.persist_main_execution_source(parent)
    db.noting_idle_turn_finished(ref_of(db, "s"), 1000)
    monkeypatch.setattr(rt, "_freeze_and_log_attempt", lambda *args: pytest.fail("No External freeze"))
    decision = rt.prepare_joint_noting(parent, trigger=trigger, measurement=PRESSURE, now=2000)
    assert decision.reason == "external_main_execution"
    assert not calls
    with db._read_ctx() as conn:
        assert conn.execute("SELECT COUNT(*) FROM secretary_noting_admissions").fetchone()[0] == 0


@pytest.mark.parametrize("failure", ["freeze", "spawn"])
def test_idle_noting_preparation_failure_never_requests_compaction(runtime, monkeypatch, failure):
    parent, db, calls = runtime
    parent.context_compressor.update_from_response({"prompt_tokens": 50000})
    db.noting_idle_turn_finished(ref_of(db, "s"), 1000)
    def fail(*args, **kwargs):
        raise OSError("controlled Noting failure")
    if failure == "freeze":
        monkeypatch.setattr(rt, "_freeze_and_log_attempt", fail)
    else:
        monkeypatch.setattr("secretary.noting_child.spawn_noting_task", fail)
    native = []
    parent.request_context_compaction = lambda **kwargs: native.append(kwargs)
    outcome = rt._run_idle_event(parent, db, ref_of(db, "s"), now=2000)
    assert outcome == "skip:trigger_error"
    assert native == []


def test_rewind_across_successful_boundary_does_not_reopen_its_force_interval(runtime):
    parent, db, calls = runtime
    assert compact(parent, db, "boundary1")
    append(parent, db, "m2")
    admission = rt.prepare_joint_noting(parent, trigger="force", measurement=PRESSURE).admission
    assert admission.compression_interval_id == "boundary1"
    boundary_row = next(row["id"] for row in db.get_messages("s") if row["message_uid"] == "boundary1")
    db.rewind_to_message("s", boundary_row)
    append(parent, db, "m3")
    assert not rt.note_successful_compaction(parent, committed=False)
    assert rt.prepare_joint_noting(parent, trigger="force", measurement=PRESSURE).reason == "force_interval_occupied"
    assert len(calls) == 1
