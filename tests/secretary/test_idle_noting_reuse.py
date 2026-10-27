"""Real admission/child/Snapshot witnesses for Idle reuse; native model I/O is controlled."""

import json
import threading
import time

import pytest

from agent.context_compaction_request import cancel_native_request
from secretary import noting_child, noting_runtime
from secretary.noting_policy import ContextMeasurement
from tests.agent.test_context_compaction_request import _summary
from tests.secretary.test_idle_noting_commit_order import finish_responses, result_rows, start_idle
from tests.secretary.test_noting_child import _tool_response, mock_response

pytest_plugins = ["tests.secretary.test_idle_noting_commit_order"]
PRESSURE = ContextMeasurement(64000, 130000, 75000)


def force(parent, trigger="force"):
    decision = noting_runtime.prepare_joint_noting(parent, trigger=trigger,
                                                   measurement=PRESSURE if trigger == "force" else None)
    assert decision.action == "admit"
    return decision.admission


def delayed_finish(client, ready, release):
    responses = iter([
        _tool_response("finish_noting", {"reason": "Checked the current work."}, "finish"),
        mock_response("Finished."),
    ])
    def respond(**kwargs):
        ready.set()
        assert release.wait(10)
        return next(responses)
    client.chat.completions.create.side_effect = respond


@pytest.mark.parametrize("trigger", ["force", "manual"])
@pytest.mark.parametrize("writer_reads", [False, True], ids=["read-pool", "writer-connection"])
def test_running_force_normal_commit_compacts_before_its_framework(idle_runtime, monkeypatch, trigger, writer_reads):
    parent, db, client, workers = idle_runtime
    if writer_reads:
        monkeypatch.setattr(db, "_checkout_read_conn", lambda: None)
    ready, release, compressing, finish_compress = (threading.Event() for _ in range(4))
    delayed_finish(client, ready, release)
    admission = force(parent, trigger)
    def summary(messages, **kwargs):
        with db._read_ctx() as conn:
            assert db.noting_normal_child_snapshot_conn(conn, admission.admission_id,
                                                        admission.conversation_ref, admission.compression_interval_id)
        assert not result_rows(parent)
        compressing.set()
        assert finish_compress.wait(10)
        return _summary(messages, **kwargs)
    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    try:
        assert ready.wait(10)
        assert start_idle(parent, db) == "waiting_existing_noting"
        assert len(workers) == 1 and not compressing.is_set()
        release.set()
        assert compressing.wait(10)
        assert not result_rows(parent) and workers[0].is_alive()
        finish_compress.set()
        workers[0].join(10)
        assert not workers[0].is_alive()
        assert len(result_rows(parent)) == 1
        assert "Termination: finish_noting" in result_rows(parent)[0]["content"]
        request = parent._native_compaction_request
        assert request.durable_commit_succeeded and request.current()
        with db._read_ctx() as conn:
            assert db.noting_compaction_interval_conn(conn, admission.conversation_ref) != admission.compression_interval_id
    finally:
        release.set()
        finish_compress.set()


@pytest.mark.parametrize("marker", ["valid", "absent", "wrong_admission", "invalid_anchor"])
def test_completed_force_reuses_exact_durable_commit_without_reissuing_framework(idle_runtime, monkeypatch, marker):
    parent, db, client, workers = idle_runtime
    finish_responses(client)
    admission = force(parent)
    workers[0].join(10)
    assert not workers[0].is_alive() and len(result_rows(parent)) == 1
    child_id = db.noting_child(admission.admission_id)["child_session_id"]
    current = db.notebook_current(admission.conversation_ref)
    witness = db.get_session_model_config_value(child_id, "_secretary_noting_commit")
    assert witness == {"admission_id": admission.admission_id, "snapshot_id": current["snapshot_id"]}
    if marker in {"absent", "wrong_admission"}:
        db.patch_session_model_config(child_id, {"_secretary_noting_commit": None if marker == "absent"
            else {**witness, "admission_id": admission.admission_id + 1}})
    original_uid = result_rows(parent)[0]["message_uid"]
    if marker == "invalid_anchor":
        row_id = next(row["id"] for row in db.get_messages(parent.session_id) if row["message_uid"] == "m9")
        db.rewind_to_message(parent.session_id, row_id)
        db.append_message(parent.session_id, "user", "New direction after rewind", message_uid="new-head")
        parent._session_messages = db.get_messages_as_conversation(parent.session_id)
    compressed = []
    def summary(messages, **kwargs):
        compressed.append(True)
        return _summary(messages, **kwargs)
    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    outcome = start_idle(parent, db)
    if marker == "valid":
        assert outcome == "existing_noting_compaction_requested"
        parent._native_compaction_worker.join(10)
        assert compressed == [True]
        assert db.notebook_current(admission.conversation_ref)["snapshot_id"] == current["snapshot_id"]
    else:
        assert outcome == "skip:existing_noting_not_successful" and not compressed
    with db._read_ctx() as conn:
        rows = conn.execute("SELECT message_uid,display_metadata FROM messages").fetchall()
    outputs = [row["message_uid"] for row in rows
               if json.loads(row["display_metadata"] or "{}").get("noting_run_output")]
    # Native compaction may physically carry the same canonical message UID.
    assert set(outputs) == {original_uid}
    assert len(workers) == 1


@pytest.mark.parametrize("ending", ["forced", "context_overflow", "api_error"])
def test_waiting_idle_never_compacts_abnormal_existing_force(idle_runtime, monkeypatch, ending):
    parent, db, _client, workers = idle_runtime
    ready, release = threading.Event(), threading.Event()
    def run(child, **kwargs):
        ready.set()
        assert release.wait(10)
        if ending == "context_overflow":
            raise noting_child.NotingContextOverflow("controlled overflow")
        if ending == "forced":
            return {"completed": False, "turn_exit_reason": "max_iterations_reached(50/50)",
                    "final_response": "Work remains."}
        return {"completed": False, "failed": True, "turn_exit_reason": "api_error", "error": "provider unavailable"}
    monkeypatch.setattr("run_agent.AIAgent.run_conversation", run)
    requests = []
    monkeypatch.setattr(parent, "request_context_compaction", lambda **kwargs: requests.append(kwargs))
    admission = force(parent)
    try:
        assert ready.wait(10)
        assert start_idle(parent, db) == "waiting_existing_noting"
        release.set()
        workers[0].join(10)
        assert not workers[0].is_alive() and not requests
        assert len(result_rows(parent)) == 1
        assert (db.notebook_current(admission.conversation_ref) is None) is (ending == "api_error")
        # A later real Idle period must not treat a forced legal Snapshot as success.
        assert start_idle(parent, db) == "skip:existing_noting_not_successful"
        assert not requests
    finally:
        release.set()


def test_normal_committed_but_still_running_child_accepts_idle_before_publication(idle_runtime, monkeypatch):
    parent, db, client, workers = idle_runtime
    finish_responses(client)
    committed, release = threading.Event(), threading.Event()
    publish = noting_child._publish_after_idle_completion
    def delayed(handle, outcome, *args, **kwargs):
        assert outcome.committed
        committed.set()
        assert release.wait(10)
        return publish(handle, outcome, *args, **kwargs)
    monkeypatch.setattr(noting_child, "_publish_after_idle_completion", delayed)
    monkeypatch.setattr(parent.context_compressor, "compress", _summary)
    admission = force(parent)
    try:
        assert committed.wait(10)
        assert db.noting_child(admission.admission_id)["status"] == "running"
        assert not result_rows(parent)
        assert start_idle(parent, db) == "waiting_existing_noting"
        release.set()
        workers[0].join(10)
        assert not workers[0].is_alive() and len(result_rows(parent)) == 1
        assert db.get_native_request_publication(parent.session_id)
    finally:
        release.set()


@pytest.mark.parametrize("boundary", ["close", "rebind", "interval", "local_off"])
def test_waiting_idle_drops_stale_owner_or_interval(idle_runtime, monkeypatch, boundary):
    parent, db, client, workers = idle_runtime
    ready, release = threading.Event(), threading.Event()
    delayed_finish(client, ready, release)
    force(parent)
    requests = []
    native = parent.request_context_compaction
    def observe(**kwargs):
        result = native(**kwargs)
        requests.append(result)
        return result
    monkeypatch.setattr(parent, "request_context_compaction", observe)
    monkeypatch.setattr(parent.context_compressor, "compress", _summary)
    try:
        assert ready.wait(10)
        assert start_idle(parent, db) == "waiting_existing_noting"
        if boundary == "close":
            cancel_native_request(parent, boundary=True)
        elif boundary == "rebind":
            db.create_session("replacement", source="test")
            parent.session_id = "replacement"
            parent._secretary_conversation_ref = db.resolve_conversation_ref("replacement")
            parent._session_messages = []
        elif boundary == "local_off":
            db.notebook_set_local_enabled(parent._secretary_conversation_ref, False)
        else:
            # A separate native compaction remains allowed while Noting runs.
            parent._compress_context(parent._session_messages, None, approx_tokens=50000, trigger="noting_joint_idle")
        release.set()
        workers[0].join(10)
        assert not workers[0].is_alive()
        assert all(not result.ok for result in requests)
        if boundary == "close":
            assert [result.status for result in requests] == ["owner_changed"]
        elif boundary == "rebind":
            assert not requests or [result.status for result in requests] == ["owner_changed"]
        else:
            assert not requests
    finally:
        release.set()


def test_association_failure_keeps_legal_snapshot_and_live_idle_completion(idle_runtime, monkeypatch):
    from hermes_state import SessionDB
    parent, db, client, workers = idle_runtime
    finish_responses(client)
    record = SessionDB.noting_record_child_snapshot_conn
    def fail(self, conn, *args):
        record(self, conn, *args)
        raise RuntimeError("association transaction failed")
    monkeypatch.setattr(SessionDB, "noting_record_child_snapshot_conn", fail)
    requests = []
    native = parent.request_context_compaction
    def observe(**kwargs):
        result = native(**kwargs)
        requests.append(result)
        return result
    monkeypatch.setattr(parent, "request_context_compaction", observe)
    monkeypatch.setattr(parent.context_compressor, "compress", _summary)
    ready, release = threading.Event(), threading.Event()
    delayed_finish(client, ready, release)
    admission = force(parent)
    assert ready.wait(10)
    assert start_idle(parent, db) == "waiting_existing_noting"
    release.set()
    workers[0].join(10)
    assert not workers[0].is_alive() and len(requests) == 1
    assert db.notebook_current(admission.conversation_ref) is not None
    child = db.noting_child(admission.admission_id)
    assert child["status"] == "completed"
    assert db.get_session_model_config_value(child["child_session_id"], "_secretary_noting_commit") is None
    assert len(result_rows(parent)) == 1 and "Termination: finish_noting" in result_rows(parent)[0]["content"]
    assert requests[0].ok and db.get_native_request_publication(parent.session_id)


@pytest.mark.parametrize("failed", [False, True])
def test_pending_construction_owns_idle_hook_until_success_or_failure(idle_runtime, monkeypatch, failed):
    parent, db, client, workers = idle_runtime
    finish_responses(client)
    constructing, release = threading.Event(), threading.Event()
    build = noting_child.build_noting_child
    def delayed(*args, **kwargs):
        constructing.set()
        assert release.wait(10)
        if failed:
            raise RuntimeError("child construction failed")
        return build(*args, **kwargs)
    monkeypatch.setattr(noting_child, "build_noting_child", delayed)
    monkeypatch.setattr(parent.context_compressor, "compress", _summary)
    admission = force(parent)
    try:
        assert constructing.wait(10)
        assert db.noting_child(admission.admission_id) is None
        assert start_idle(parent, db) == "waiting_existing_noting"
        release.set()
        workers[0].join(10)
        assert not workers[0].is_alive()
        with noting_child._ACTIVE_NOTING_LOCK:
            assert noting_child._completion_key(db, admission.admission_id) not in noting_child._NOTING_COMPLETIONS
        assert (db.notebook_current(admission.conversation_ref) is None) is failed
        if failed:
            assert db.noting_child(admission.admission_id)["status"] == "failed"
            assert getattr(parent, "_native_compaction_request", None) is None
        else:
            assert db.get_native_request_publication(parent.session_id)
    finally:
        release.set()


def test_orphan_running_child_without_live_handle_or_commit_cannot_compact(idle_runtime, monkeypatch):
    parent, db, _client, workers = idle_runtime
    ref = parent._secretary_conversation_ref
    admission = db.noting_admit(ref, "m10", kind="force")
    db.create_session("orphan-child", source="subagent", parent_session_id=parent.session_id)
    db.noting_child_register(admission, child_session_id="orphan-child", profile=None)
    requests = []
    monkeypatch.setattr(parent, "request_context_compaction", lambda **kwargs: requests.append(kwargs))
    assert start_idle(parent, db) == "skip:existing_noting_not_successful"
    assert not requests and not workers


def test_durable_success_can_be_reused_by_reopened_runtime_without_task_resume(idle_runtime, monkeypatch):
    from hermes_state import SessionDB
    from secretary.noting_scope import owning_db_scope
    from tests.secretary.test_noting_child import make_agent
    parent, db, client, workers = idle_runtime
    finish_responses(client)
    admission = force(parent)
    workers[0].join(10)
    reopened = SessionDB(db.db_path)
    owner = make_agent(parent.session_id, reopened)
    owner._secretary_conversation_ref = admission.conversation_ref
    owner._session_messages = reopened.get_messages_as_conversation(owner.session_id)
    owner.context_compressor.context_length = 130000
    owner.context_compressor.threshold_tokens = 75000
    owner.context_compressor.last_prompt_tokens = 50000
    requests = []
    from agent.context_compaction_request import NativeCompactionResult
    monkeypatch.setattr(owner, "request_context_compaction", lambda **kwargs: (
        requests.append(kwargs), NativeCompactionResult(True, "admitted"))[1])
    try:
        with owning_db_scope(reopened):
            assert start_idle(owner, reopened) == "existing_noting_compaction_requested"
        assert len(requests) == 1 and len(workers) == 1
        assert len(result_rows(owner)) == 1
    finally:
        reopened.close()


def test_true_child_snapshot_owner_conflict_still_refuses_commit(idle_runtime, monkeypatch):
    from hermes_state import SessionDB
    from hermes_state_secretary_noting import NotingChildSnapshotOwnershipError
    parent, db, client, workers = idle_runtime
    finish_responses(client)
    def mismatch(*args):
        raise NotingChildSnapshotOwnershipError("registered child no longer owns this admission")
    monkeypatch.setattr(SessionDB, "noting_record_child_snapshot_conn", mismatch)
    admission = force(parent)
    workers[0].join(10)
    assert not workers[0].is_alive()
    assert db.notebook_current(admission.conversation_ref) is None
    assert db.noting_child(admission.admission_id)["status"] == "abandoned"
    assert "No new Snapshot" in result_rows(parent)[0]["content"]


def test_idle_registration_racing_framework_publish_reuses_completed_task_without_replay(idle_runtime, monkeypatch):
    from secretary import framework_messages

    parent, db, client, workers = idle_runtime
    finish_responses(client)
    publishing, release, attaching = (threading.Event() for _ in range(3))
    publish = framework_messages.publish_noting_completion
    attach = noting_child.reuse_noting_for_idle
    results, errors = [], []
    def blocked(*args, **kwargs):
        publishing.set()
        assert release.wait(10)
        return publish(*args, **kwargs)
    def observe_attach(*args, **kwargs):
        attaching.set()
        return attach(*args, **kwargs)
    def run(call):
        try:
            results.append(call())
        except BaseException as exc:
            errors.append(exc)
    monkeypatch.setattr(framework_messages, "publish_noting_completion", blocked)
    monkeypatch.setattr(noting_child, "reuse_noting_for_idle", observe_attach)
    summaries = []
    def summary(messages, **kwargs):
        # Publication won the shared lock before this Idle registration; its
        # original Framework is already history, rather than a pending result.
        assert len(result_rows(parent)) == 1
        summaries.append(True)
        return _summary(messages, **kwargs)
    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    task_start = threading.Thread(target=lambda: run(lambda: force(parent)), daemon=True)
    idle_start = threading.Thread(target=lambda: run(lambda: start_idle(parent, db)), daemon=True)
    task_start.start()
    try:
        assert publishing.wait(10)
        idle_start.start()
        assert attaching.wait(10)
        assert idle_start.is_alive() and not result_rows(parent)
        release.set()
        task_start.join(10)
        idle_start.join(10)
        assert not task_start.is_alive() and not idle_start.is_alive() and not errors
        workers[0].join(10)
        parent._native_compaction_worker.join(10)
        assert "existing_noting_compaction_requested" in results and summaries == [True]
        with db._read_ctx() as conn:
            rows = conn.execute("SELECT message_uid,display_metadata FROM messages").fetchall()
        uids = {row["message_uid"] for row in rows
                if json.loads(row["display_metadata"] or "{}").get("noting_run_output")}
        assert len(uids) == 1 and len(workers) == 1
    finally:
        release.set()
        task_start.join(10)
        if idle_start.ident is not None:
            idle_start.join(10)


def test_joint_cycle_idle_facade_cannot_run_native_callback_before_normal_commit(idle_runtime, monkeypatch):
    parent, db, client, workers = idle_runtime
    ready, release = threading.Event(), threading.Event()
    delayed_finish(client, ready, release)
    monkeypatch.setattr(parent.context_compressor, "compress", _summary)
    calls = []
    db.noting_idle_turn_finished(parent._secretary_conversation_ref, 1000, due_at=1500)
    try:
        decision, native = noting_runtime.run_joint_cycle(
            parent, trigger="idle", native_compact=lambda: calls.append(True), now=2000,
        )
        assert decision.action == "admit" and native is None and not calls
        assert ready.wait(10) and not result_rows(parent)
        release.set()
        workers[0].join(10)
        assert not workers[0].is_alive() and not calls
        assert len(result_rows(parent)) == 1 and db.get_native_request_publication(parent.session_id)
    finally:
        release.set()


def test_completed_task_retains_exact_parent_until_native_request_settles(idle_runtime, monkeypatch):
    from secretary.noting_timers import holds_maintenance, refresh_maintenance
    parent, db, client, workers = idle_runtime
    finish_responses(client)
    admission = force(parent)
    workers[0].join(10)
    assert not workers[0].is_alive()
    assert refresh_maintenance(parent)
    entered, release = threading.Event(), threading.Event()
    def summary(messages, **kwargs):
        entered.set()
        assert release.wait(10)
        return _summary(messages, **kwargs)
    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    try:
        assert start_idle(parent, db) == "existing_noting_compaction_requested"
        assert entered.wait(10)
        assert holds_maintenance(parent)
        assert noting_child.holds_parent_completion(parent)
        assert not parent._native_compaction_request.completed.is_set()
    finally:
        release.set()
    parent._native_compaction_worker.join(10)
    deadline = time.monotonic() + 10
    while holds_maintenance(parent) and time.monotonic() < deadline:
        time.sleep(.01)
    assert not holds_maintenance(parent)
    assert noting_child._completion_key(db, admission.admission_id) not in noting_child._NOTING_COMPLETIONS


@pytest.mark.parametrize("cleanup_first", [False, True], ids=["reuse-reserves-first", "cleanup-commits-first"])
def test_native_reuse_reservation_and_old_cleanup_commit_are_atomic(idle_runtime, monkeypatch, cleanup_first):
    from contextlib import contextmanager
    from secretary import framework_messages
    from secretary.noting_timers import holds_maintenance, refresh_maintenance
    parent, db, client, workers = idle_runtime
    finish_responses(client)
    refresh_maintenance(parent)
    cleanup_entered, release_cleanup, request_returned, release_request = (threading.Event() for _ in range(4))
    summary_entered, release_summary = threading.Event(), threading.Event()
    cleanup_ident, old_handles, results, errors = [], [], [], []
    real_lock, real_end = framework_messages._lock, noting_child._end_completion
    real_request = parent.request_context_compaction
    gate_used = threading.Event()

    @contextmanager
    def framework_gate(owner):
        if (cleanup_ident and threading.get_ident() == cleanup_ident[0] and not gate_used.is_set()):
            gate_used.set()
            cleanup_entered.set()
            assert release_cleanup.wait(10)
        with real_lock(owner):
            yield

    def cleanup(db, handle, *, task_cleanup=False):
        if task_cleanup and not cleanup_ident:
            cleanup_ident.append(threading.get_ident())
            old_handles.append(handle)
        return real_end(db, handle, task_cleanup=task_cleanup)

    def request(**kwargs):
        receipt = real_request(**kwargs)
        request_returned.set()
        assert release_request.wait(10)
        return receipt

    def summary(messages, **kwargs):
        summary_entered.set()
        assert release_summary.wait(10)
        return _summary(messages, **kwargs)

    def reuse():
        try:
            results.append(start_idle(parent, db))
        except BaseException as exc:
            errors.append(exc)

    monkeypatch.setattr(framework_messages, "_lock", framework_gate)
    monkeypatch.setattr(noting_child, "_end_completion", cleanup)
    monkeypatch.setattr(parent, "request_context_compaction", request)
    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    admission = force(parent)
    reuse_thread = threading.Thread(target=reuse)
    key = noting_child._completion_key(db, admission.admission_id)
    try:
        assert cleanup_entered.wait(10)
        old = old_handles[0]
        assert old.notified and not old.closed
        if cleanup_first:
            release_cleanup.set()
            workers[0].join(10)
            assert not workers[0].is_alive() and old.closed
            assert key not in noting_child._NOTING_COMPLETIONS
        reuse_thread.start()
        assert request_returned.wait(10) and summary_entered.wait(10)
        current = noting_child._NOTING_COMPLETIONS[key]
        assert current.native_pending and not current.closed
        assert (current is old) is not cleanup_first
        if not cleanup_first:
            release_cleanup.set()
            workers[0].join(10)
            assert not workers[0].is_alive()
            assert noting_child._NOTING_COMPLETIONS[key] is current and not old.closed
        assert holds_maintenance(parent)
        release_request.set()
        reuse_thread.join(10)
        assert not reuse_thread.is_alive() and not errors
        assert results == ["existing_noting_compaction_requested"]
        assert holds_maintenance(parent) and not current.closed
        release_summary.set()
        parent._native_compaction_worker.join(10)
        deadline = time.monotonic() + 10
        while noting_child.holds_parent_completion(parent) and time.monotonic() < deadline:
            time.sleep(.01)
        assert not noting_child.holds_parent_completion(parent)
        assert key not in noting_child._NOTING_COMPLETIONS
    finally:
        release_cleanup.set()
        release_request.set()
        release_summary.set()
        for worker in workers:
            worker.join(10)
        if reuse_thread.ident is not None:
            reuse_thread.join(10)
        if worker := getattr(parent, "_native_compaction_worker", None):
            worker.join(10)


def test_completed_reuse_never_attaches_another_round_native_request_slot(idle_runtime, monkeypatch):
    from agent.context_compaction_request import NativeCompactionRequest, _lock
    from secretary.noting_timers import refresh_maintenance
    parent, db, client, workers = idle_runtime
    finish_responses(client)
    admission = force(parent)
    workers[0].join(10)
    assert not workers[0].is_alive()
    refresh_maintenance(parent)
    entered, release = threading.Event(), threading.Event()
    own_requests, other_requests = [], []
    real_request = parent.request_context_compaction

    def summary(messages, **kwargs):
        entered.set()
        assert release.wait(10)
        return _summary(messages, **kwargs)

    def replace_after_receipt(**kwargs):
        receipt = real_request(**kwargs)
        assert entered.wait(10)
        with _lock(parent):
            own = parent._native_compaction_request
            other = NativeCompactionRequest(
                parent, own.deadline, own.usage, own.threshold, own.owner, own.db,
                own.conversation_ref, own.session_id, relevance_check=lambda: True)
            own_requests.append(own)
            other_requests.append(other)
            parent._native_compaction_request = other
        return receipt

    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    monkeypatch.setattr(parent, "request_context_compaction", replace_after_receipt)
    try:
        assert start_idle(parent, db) == "existing_noting_compaction_requested"
        assert own_requests and other_requests
        assert not other_requests[0].completed.is_set()
        # Both native identities match parent/epoch/Profile/Conversation; only the
        # callback's explicit relevance identity distinguishes the replacement.
        assert not noting_child.holds_parent_completion(parent)
        assert noting_child._completion_key(db, admission.admission_id) not in noting_child._NOTING_COMPLETIONS
    finally:
        release.set()
        parent._native_compaction_worker.join(10)
    assert own_requests[0].completed.is_set() and not other_requests[0].completed.is_set()
