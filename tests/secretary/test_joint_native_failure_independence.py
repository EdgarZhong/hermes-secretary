"""R2-V01: native technical outcomes cannot revoke an independent Noting result."""

import threading
from pathlib import Path

import pytest

from agent.compression_read import cancel_compression, compression_state
from agent.context_compaction_request import cancel_native_request
from secretary import noting_runtime
from secretary.noting_notes import check_note_delivery
from tests.agent.test_context_compaction_request import _summary
from tests.secretary.test_joint_noting_u20 import admissions, compress_async, notes
from tests.secretary.test_noting_child import _tool_response

pytest_plugins = ["tests.secretary.test_noting_child", "tests.secretary.test_joint_noting_u20"]


@pytest.fixture
def isolated_runtime(runtime, tmp_path, monkeypatch):
    parent, db, _client, _children = runtime
    outside = tmp_path / "terminal-outside-git"
    outside.mkdir()
    config = Path(db.db_path).with_name("config.yaml")
    config.write_text(config.read_text() + "terminal:\n  cwd: " + str(outside) + "\n")
    parent.session_cwd = str(outside)
    monkeypatch.chdir(outside)
    return runtime


def provider_barrier(client):
    entered, release = threading.Event(), threading.Event()
    def provider(**kwargs):
        entered.set()
        assert release.wait(20)
        return _tool_response("finish_noting", {"reason": "Completed frozen context independently"}, "finish")
    client.chat.completions.create.side_effect = provider
    return entered, release


def join(worker):
    worker.join(15)
    assert not worker.is_alive()


def start_idle(parent, db):
    db.noting_idle_turn_finished(parent._secretary_conversation_ref, 1000, due_at=1500)
    assert noting_runtime._run_idle_event(parent, db, parent._secretary_conversation_ref, now=2000) == "idle_compaction_requested"
    return parent._native_compaction_worker


@pytest.mark.parametrize("outcome", ["error", "no_change", "expired"])
@pytest.mark.parametrize("child_first", [False, True])
def test_native_nonpublication_leaves_noting_independent_before_and_after_commit(isolated_runtime, monkeypatch, outcome, child_first):
    parent, db, client, children = isolated_runtime
    child_entered, child_release = provider_barrier(client)
    summary_entered, summary_release = threading.Event(), threading.Event()
    def summary(messages, **kwargs):
        summary_entered.set()
        assert summary_release.wait(20)
        if outcome == "error":
            raise RuntimeError("controlled native summary failure")
        return messages if outcome == "no_change" else _summary(messages)
    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    errors = []
    native = start_idle(parent, db) if outcome == "expired" else None
    if native is None:
        native, _result, errors = compress_async(parent, force=True)
    try:
        assert child_entered.wait(10) and summary_entered.wait(10)
        task = admissions(db)[-1]
        if child_first:
            child_release.set()
            join(children[-1])
            assert db.noting_admission(task["admission_id"])["state"] == "committed"
        if outcome == "expired":
            parent._native_compaction_request.cancel("expired")
        summary_release.set()
        join(native)
        assert bool(errors) == (outcome == "error")
        assert compression_state(parent)["state"] == {"error": "cancelled", "no_change": "no_change", "expired": "cancelled"}[outcome]
        assert db.noting_admission(task["admission_id"])["state"] == ("committed" if child_first else "admitted")
        child_release.set()
        join(children[-1])
        assert db.noting_admission(task["admission_id"])["state"] == "committed"
        snapshot = db.notebook_current(task["conversation_ref"])
        assert snapshot is not None and notes(db, task["conversation_ref"]) == []
    finally:
        child_release.set()
        summary_release.set()
        join(native)


def test_summary_error_result_waits_for_a_real_new_boundary_then_injects_once(isolated_runtime, monkeypatch):
    parent, db, client, children = isolated_runtime
    entered, release = provider_barrier(client)
    def fail(messages, **kwargs):
        assert entered.wait(10)
        raise RuntimeError("controlled native summary failure")
    monkeypatch.setattr(parent.context_compressor, "compress", fail)
    native, _result, errors = compress_async(parent, force=True)
    try:
        join(native)
        assert errors
        release.set()
        join(children[-1])
        task = admissions(db)[-1]
        snapshot = db.notebook_current(task["conversation_ref"])
        assert snapshot is not None and notes(db, task["conversation_ref"]) == []
        monkeypatch.setattr(parent.context_compressor, "compress", _summary)
        next_native, result, errors = compress_async(parent, force=True)
        join(next_native)
        assert not errors
        parent._session_messages = result[0][0]
        assert notes(db, task["conversation_ref"])[0]["snapshot_id"] == snapshot["snapshot_id"]
        assert not check_note_delivery(parent)
        assert len(notes(db, task["conversation_ref"])) == 1
    finally:
        release.set()
        join(native)


@pytest.mark.parametrize("cancel_entry", ["manual", "idle"])
@pytest.mark.parametrize("child_first", [False, True])
def test_idle_new_turn_cancel_is_explicit_and_retains_already_committed_snapshot(isolated_runtime, monkeypatch, child_first, cancel_entry):
    parent, db, client, children = isolated_runtime
    child_entered, child_release = provider_barrier(client)
    summary_entered, summary_release = threading.Event(), threading.Event()
    def summary(messages, **kwargs):
        summary_entered.set()
        assert summary_release.wait(20)
        return _summary(messages)
    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    native = start_idle(parent, db) if cancel_entry == "idle" else compress_async(parent, force=True)[0]
    try:
        assert summary_entered.wait(10) and child_entered.wait(10)
        task = admissions(db)[-1]
        if child_first:
            child_release.set()
            join(children[-1])
        if cancel_entry == "idle":
            cancel_native_request(parent)  # Real pre-Turn/owner boundary entry.
        else:
            assert cancel_compression(parent, task["operation_id"])["outcome"] == "cancelled"
        assert db.noting_admission(task["admission_id"])["state"] == ("committed" if child_first else "cancelled")
        child_release.set()
        summary_release.set()
        join(native)
        join(children[-1])
        assert (db.notebook_current(task["conversation_ref"]) is not None) == child_first
    finally:
        child_release.set()
        summary_release.set()
        join(native)


@pytest.mark.parametrize("cancel", ["manual", "idle", "expired"])
def test_cancel_during_prepare_before_admission_uses_same_explicit_operation_fact(isolated_runtime, monkeypatch, cancel):
    parent, db, client, children = isolated_runtime
    entered, release = threading.Event(), threading.Event()
    child_entered, child_release = provider_barrier(client)
    prepare = noting_runtime.prepare_joint_noting
    def delayed_prepare(*args, **kwargs):
        if kwargs.get("trigger") == "idle":
            return prepare(*args, **kwargs)
        entered.set()
        assert release.wait(20)
        return prepare(*args, **kwargs)
    monkeypatch.setattr(noting_runtime, "prepare_joint_noting", delayed_prepare)
    monkeypatch.setattr(parent.context_compressor, "compress", _summary)
    native = start_idle(parent, db) if cancel != "manual" else None
    errors = []
    if native is None:
        native, _result, errors = compress_async(parent, force=True)
    try:
        assert entered.wait(10) and admissions(db) == []
        operation = compression_state(parent)["operation_id"]
        if cancel == "manual":
            assert cancel_compression(parent, operation)["outcome"] == "cancelled"
        else:
            parent._native_compaction_request.cancel("expired" if cancel == "expired" else "cancelled")
        release.set()
        join(native)
        task = admissions(db)[-1]
        assert task["operation_id"] == operation
        assert task["state"] == ("admitted" if cancel == "expired" else "cancelled")
        child_release.set()
        join(children[-1])
        assert db.noting_admission(task["admission_id"])["state"] == ("committed" if cancel == "expired" else "cancelled")
        assert errors == []
    finally:
        release.set()
        child_release.set()
        join(native)


def test_idle_cancel_losing_to_native_commit_does_not_revoke_uncommitted_noting(isolated_runtime, monkeypatch):
    parent, db, client, children = isolated_runtime
    child_entered, child_release = provider_barrier(client)
    commit_entered, commit_release, cancel_started = [threading.Event() for _ in range(3)]
    append = db.archive_and_compact
    def held_append(*args, **kwargs):
        commit_entered.set()
        assert commit_release.wait(20)
        return append(*args, **kwargs)
    monkeypatch.setattr(db, "archive_and_compact", held_append)
    monkeypatch.setattr(parent.context_compressor, "compress", _summary)
    native = start_idle(parent, db)
    canceller = None
    try:
        assert commit_entered.wait(10) and child_entered.wait(10)
        task = admissions(db)[-1]
        def cancel():
            cancel_started.set()
            cancel_native_request(parent)
        canceller = threading.Thread(target=cancel)
        canceller.start()
        assert cancel_started.wait(10)
        commit_release.set()
        join(canceller)
        join(native)
        assert db.noting_admission(task["admission_id"])["state"] == "admitted"
        child_release.set()
        join(children[-1])
        assert db.noting_admission(task["admission_id"])["state"] == "committed"
        assert len(notes(db, task["conversation_ref"])) == 1
    finally:
        commit_release.set()
        child_release.set()
        join(native)
        if canceller is not None:
            join(canceller)


def test_idle_lease_refresh_failure_is_technical_expiry_not_user_cancel(isolated_runtime, monkeypatch):
    from agent import periodic_scheduler
    parent, db, client, children = isolated_runtime
    child_entered, child_release = provider_barrier(client)
    summary_entered, summary_release = threading.Event(), threading.Event()
    callbacks = []
    schedule = periodic_scheduler.schedule
    def capture(callback, *args, **kwargs):
        if callback.__module__ == "agent.context_compaction_request":
            callbacks.append(callback)
        return schedule(callback, *args, **kwargs)
    def summary(messages, **kwargs):
        summary_entered.set()
        assert summary_release.wait(20)
        return _summary(messages)
    monkeypatch.setattr(periodic_scheduler, "schedule", capture)
    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    worker = start_idle(parent, db)
    try:
        assert summary_entered.wait(10) and child_entered.wait(10) and len(callbacks) == 1
        task = admissions(db)[-1]
        db.release_session_turn_lease(parent.session_id, parent._active_session_turn_lease_holder)
        callbacks[0]()  # The registered production refresh callback actually loses its lease.
        assert parent._native_compaction_request.state == "expired"
        summary_release.set()
        join(worker)
        assert db.noting_admission(task["admission_id"])["state"] == "admitted"
        child_release.set()
        join(children[-1])
        assert db.noting_admission(task["admission_id"])["state"] == "committed"
    finally:
        summary_release.set()
        child_release.set()
        join(worker)


def test_cancelled_fence_before_native_prepare_does_not_dispatch_new_task(isolated_runtime):
    from agent.conversation_compression import CompressionCommitFence
    parent, db, client, _children = isolated_runtime
    fence = CompressionCommitFence()
    assert fence.cancel_before_commit()
    parent._compress_context(parent._session_messages, None, approx_tokens=50_000, force=True, commit_fence=fence)
    assert admissions(db) == [] and not client.chat.completions.create.called


def test_native_user_cancel_does_not_cancel_an_inflight_force(isolated_runtime, monkeypatch):
    from agent.usage_anchor import capture_usage_anchor
    parent, db, client, children = isolated_runtime
    child_entered, child_release = provider_barrier(client)
    summary_entered, summary_release = threading.Event(), threading.Event()
    def summary(messages, **kwargs):
        summary_entered.set()
        assert summary_release.wait(20)
        return _summary(messages)
    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    monkeypatch.setattr("secretary.noting_timers.arm_idle_timer", lambda *args: None)
    parent._usage_anchor = capture_usage_anchor(64_001, 0, parent._session_messages)
    noting_runtime.note_main_turn_started(parent)
    noting_runtime.note_main_turn_finished(parent)
    assert child_entered.wait(10)
    force = admissions(db)[-1]
    assert force["kind"] == "force"
    worker, _result, errors = compress_async(parent, force=True)
    try:
        assert summary_entered.wait(10)
        assert cancel_compression(parent, compression_state(parent)["operation_id"])["outcome"] == "cancelled"
        assert db.noting_admission(force["admission_id"])["state"] == "admitted"
        child_release.set()
        join(children[-1])
        assert db.noting_admission(force["admission_id"])["state"] == "committed"
        assert len(admissions(db)) == 1
    finally:
        summary_release.set()
        child_release.set()
        join(worker)
    assert errors == []
