"""U20 uses real SQLite, native compression fences and the real Noting model/tool Loop.

Only provider output and summary output are controlled. Events bound their order;
qualification, cancellation, Snapshot commit, FM append and receipts remain real.
"""

import json
import threading
import time
from collections import OrderedDict
from pathlib import Path

import pytest

from agent.compression_read import cancel_compression, compression_state
from agent.context_compaction_request import trust_default_system_message
from secretary import noting_child, noting_runtime
from secretary.noting_notes import check_note_delivery
from secretary.noting_scope import bind_main_runtime, owning_db_scope
from tests.agent.test_context_compaction_request import _summary
from tests.secretary.test_noting_child import _tool_response, mock_response

pytest_plugins = ["tests.secretary.test_noting_child"]
FINISH = {"type": "finish_noting", "reason": "Reviewed the complete frozen context."}


@pytest.fixture
def runtime(parent, db, stub_client, monkeypatch):
    Path(db.db_path).with_name("config.yaml").write_text(
        "noting:\n  enabled: true\n  idle:\n    enabled: true\n    delay_seconds: 500\n    threshold_tokens: 1000\n")
    for n in range(3, 11):
        db.append_message(parent.session_id, "user" if n % 2 else "assistant", "Dialogue " * 300,
                          message_uid=f"m{n}", timestamp=1000 + n)
    parent._session_messages = db.get_messages_as_conversation(parent.session_id)
    parent.compression_enabled = True
    parent.compression_in_place = True
    parent._compression_feasibility_checked = True
    parent.context_compressor.context_length = 130_000
    parent.context_compressor.threshold_tokens = 75_000
    parent.context_compressor.last_prompt_tokens = 50_000
    parent.context_compressor.last_real_prompt_tokens = 50_000
    trust_default_system_message(parent)
    bind_main_runtime(parent)
    workers = []
    spawn = noting_child.spawn_noting_task

    def track(*args, **kwargs):
        worker = spawn(*args, **kwargs)
        workers.append(worker)
        return worker

    monkeypatch.setattr(noting_child, "spawn_noting_task", track)
    with owning_db_scope(db):
        yield parent, db, stub_client, workers
    for worker in workers:
        worker.join(10)
        assert not worker.is_alive()


def wait_for(predicate):
    deadline = time.monotonic() + 10
    while not predicate() and time.monotonic() < deadline:
        time.sleep(.01)
    assert predicate()


def admissions(db):
    with db._read_ctx() as conn:
        return [dict(row) for row in conn.execute("SELECT * FROM secretary_noting_task_admissions ORDER BY admitted_at")]


def notes(db, ref):
    with db._read_ctx() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT * FROM secretary_noting_note_receipts WHERE conversation_ref=?", (ref,))]


def compress_async(parent, **options):
    result, failures = [], []

    def run():
        try:
            result.append(parent._compress_context(parent._session_messages, None, approx_tokens=50_000, **options))
        except BaseException as exc:
            failures.append(exc)
    worker = threading.Thread(target=run)
    worker.start()
    return worker, result, failures


def finish_provider(client):
    client.chat.completions.create.side_effect = [
        _tool_response("finish_noting", {"reason": FINISH["reason"]}, "finish"), mock_response("Finished.")]


@pytest.mark.parametrize("trigger", ["manual", "auto", "idle"])
@pytest.mark.parametrize("noting_first", [True, False])
def test_native_and_noting_start_together_and_settle_independently(runtime, monkeypatch, trigger, noting_first):
    parent, db, client, children = runtime
    child_entered, summary_entered, child_release, summary_release = [threading.Event() for _ in range(4)]
    calls = []

    def provider(**kwargs):
        child_entered.set()
        assert child_release.wait(10)
        calls.append(1)
        return (_tool_response("finish_noting", {"reason": FINISH["reason"]}, "finish")
                if len(calls) == 1 else mock_response("Finished."))

    def summary(messages, **kwargs):
        summary_entered.set()
        assert summary_release.wait(10)
        return _summary(messages, **kwargs)

    client.chat.completions.create.side_effect = provider
    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    ref = parent._secretary_conversation_ref
    native = None
    try:
        if trigger == "idle":
            db.noting_idle_turn_finished(ref, 1000, due_at=1500)
            assert noting_runtime._run_idle_event(parent, db, ref, now=2000) == "idle_compaction_requested"
            native = parent._native_compaction_worker
        else:
            native, _result, failures = compress_async(parent, force=trigger == "manual")
        assert child_entered.wait(10) and summary_entered.wait(10)
        admitted = admissions(db)[-1]
        assert admitted["operation_id"] == compression_state(parent)["operation_id"]
        if noting_first:
            child_release.set()
            children[0].join(10)
            assert not children[0].is_alive() and native.is_alive()
            assert db.noting_child(admitted["admission_id"])["status"] == "completed"
            assert db.notebook_current(ref) is not None
            assert not notes(db, ref)
            summary_release.set()
        else:
            summary_release.set()
            native.join(10)
            assert not native.is_alive() and children[0].is_alive()
            assert db.notebook_current(ref) is None
            child_release.set()
        native.join(10)
        children[0].join(10)
        assert not native.is_alive() and not children[0].is_alive()
        wait_for(lambda: len(notes(db, ref)) == 1)
        check_note_delivery(parent)
        assert len(notes(db, ref)) == 1
        assert db.noting_child(admitted["admission_id"])["status"] == "completed"
        if trigger != "idle":
            assert failures == []
    finally:
        child_release.set()
        summary_release.set()
        if native is not None:
            native.join(10)


@pytest.mark.parametrize("commit_first", [False, True])
def test_cancel_and_commit_cas_preserves_only_complete_work_and_anchor_can_retry(runtime, monkeypatch, commit_first):
    parent, db, client, children = runtime
    summary_entered, summary_release, child_entered, child_release = [threading.Event() for _ in range(4)]
    count = []

    def provider(**kwargs):
        child_entered.set()
        assert child_release.wait(10)
        count.append(1)
        return (_tool_response("finish_noting", {"reason": FINISH["reason"]}, "finish")
                if len(count) == 1 else mock_response("Finished."))

    def summary(messages, **kwargs):
        summary_entered.set()
        assert summary_release.wait(10)
        return _summary(messages, **kwargs)

    client.chat.completions.create.side_effect = provider
    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    native, _result, failures = compress_async(parent, force=True)
    try:
        assert summary_entered.wait(10) and child_entered.wait(10)
        first = admissions(db)[-1]
        if commit_first:
            child_release.set()
            children[0].join(10)
            assert db.notebook_current(first["conversation_ref"]) is not None
        outcome = cancel_compression(parent, compression_state(parent)["operation_id"])
        assert outcome["outcome"] == "cancelled"
        assert db.noting_admission(first["admission_id"])["state"] == ("committed" if commit_first else "cancelled")
        child_release.set()
        summary_release.set()
        native.join(10)
        children[0].join(10)
        assert failures == []
        if not commit_first:
            assert db.notebook_current(first["conversation_ref"]) is None
            finish_provider(client)
            monkeypatch.setattr(parent.context_compressor, "compress", _summary)
            retry, _, failures = compress_async(parent, force=True)
            retry.join(10)
            children[-1].join(10)
            assert not retry.is_alive() and failures == []
            second = admissions(db)[-1]
            assert second["anchor_message_uid"] == first["anchor_message_uid"]
            assert second["admission_id"] != first["admission_id"]
            assert second["state"] == "committed"
    finally:
        child_release.set()
        summary_release.set()
        native.join(10)


def test_replacement_freezes_audit_and_new_child_uses_last_complete_snapshot(runtime, monkeypatch):
    parent, db, client, children = runtime
    old_entered, old_release = threading.Event(), threading.Event()
    first = []

    def provider(**kwargs):
        if not first:
            first.append(1)
            old_entered.set()
            assert old_release.wait(10)
            return _tool_response("finish_noting", {"reason": "late"}, "old-finish")
        return _tool_response("finish_noting", {"reason": FINISH["reason"]}, "new-finish")

    client.chat.completions.create.side_effect = provider
    monkeypatch.setattr(parent.context_compressor, "compress", _summary)
    native, result, failures = compress_async(parent, force=True)
    try:
        assert old_entered.wait(10)
        native.join(10)
        assert failures == []
        parent._session_messages = result[0][0]
        old = admissions(db)[-1]
        child_id = db.noting_child(old["admission_id"])["child_session_id"]
        child = noting_child.active_noting_task(child_id, db=db)
        from secretary.noting_tools import notebook_create
        created = json.loads(notebook_create(child, {"entry_type": "matter", "fields": {
            "description": "Uncommitted work", "completion_condition": "Review"}, "source_message_uids": ["m1"]}))
        assert created["success"]
        db.append_message(parent.session_id, "user", "New evidence", message_uid="new-source")
        parent._session_messages = db.get_messages_as_conversation(parent.session_id)
        newer = noting_runtime.prepare_joint_noting(parent, trigger="manual", messages=parent._session_messages,
                                                     operation_id="second-native-operation")
        assert newer.action == "admit"
        audit_id = db.noting_admission(old["admission_id"])["snapshot_id"]
        audit = db.notebook_snapshot_audit(audit_id)
        assert audit["termination"] == {"type": "superseded"}
        assert audit["payload"]["work"][0]["fields"]["description"] == "Uncommitted work"
        assert db.notebook_current(parent._secretary_conversation_ref) is None
        new_child = None
        wait_for(lambda: db.noting_child(newer.admission.admission_id) is not None)
        new_child = noting_child.active_noting_task(db.noting_child(newer.admission.admission_id)["child_session_id"], db=db)
        if new_child is not None:
            assert new_child._noting_notebook_store.base_snapshot_id is None
        assert not json.loads(notebook_create(child, {"entry_type": "matter", "fields": {
            "description": "Late edit", "completion_condition": "Review"}, "source_message_uids": ["m1"]}))["success"]
        from secretary.notebook_store import NotebookStore
        with pytest.raises(ValueError, match="superseded"):
            NotebookStore(db, old["conversation_ref"], anchor_message_uid="new-source", base_snapshot_id=audit_id)
        old_release.set()
        for worker in children:
            worker.join(10)
        assert db.noting_admission(old["admission_id"])["state"] == "superseded"
        assert db.notebook_current(old["conversation_ref"])["snapshot_id"] != audit_id
    finally:
        old_release.set()
        native.join(10)


def test_two_real_successful_native_boundaries_each_receive_latest_snapshot_even_when_unchanged(runtime, monkeypatch):
    parent, db, client, children = runtime
    finish_provider(client)
    monkeypatch.setattr(parent.context_compressor, "compress", _summary)
    first, _, errors = compress_async(parent, force=True)
    first.join(10)
    for worker in children:
        worker.join(10)
    ref = parent._secretary_conversation_ref
    assert errors == []
    wait_for(lambda: len(notes(db, ref)) == 1)
    snapshot = db.notebook_current(ref)["snapshot_id"]
    initial = notes(db, ref)[0]
    second, _, errors = compress_async(parent, force=True)
    second.join(10)
    assert not second.is_alive() and errors == []
    assert db.notebook_current(ref)["snapshot_id"] == snapshot
    assert len(children) == 1  # Same frozen source needs no new Noting submission.
    second_receipts = notes(db, ref)
    assert len(second_receipts) == 2
    assert {row["snapshot_id"] for row in second_receipts} == {snapshot}
    assert len({row["interval_id"] for row in second_receipts}) == 2
    assert initial in second_receipts
    rows = [row for row in db.get_messages(parent.session_id)
            if (row.get("display_metadata") or {}).get("noting_snapshot_id") == snapshot]
    # Earlier FM may have been compacted; actual original rows and new FM both exist.
    all_rows = db._read_all("SELECT * FROM messages WHERE display_metadata LIKE ?", ('%' + snapshot + '%',))
    assert len(all_rows) >= 2 and rows
    for _ in range(3):
        check_note_delivery(parent)
    assert len(notes(db, ref)) == 2

    from hermes_state import SessionDB
    from tests.secretary.test_noting_runtime import _agent
    reopened = SessionDB(db.db_path)
    try:
        resumed = _agent(reopened, parent.session_id)
        for _ in range(3):
            bind_main_runtime(resumed)
            assert not check_note_delivery(resumed)
        assert len(notes(reopened, ref)) == 2
    finally:
        reopened.close()


def test_note_qualification_read_failure_after_native_publication_cannot_fail_compression(runtime, monkeypatch):
    from secretary.noting_notes import select_note_conn
    parent, db, client, children = runtime
    finish_provider(client)
    prepared = noting_runtime.prepare_joint_noting(parent, trigger="manual")
    assert prepared.action == "admit"
    children[0].join(10)
    ref = parent._secretary_conversation_ref
    snapshot = db.notebook_current(ref)["snapshot_id"]
    monkeypatch.setattr(parent.context_compressor, "compress", _summary)
    observed = []
    def broken_after_commit(database, conn, conversation_ref):
        boundary = conn.execute("SELECT interval_id FROM secretary_noting_compaction_state WHERE conversation_ref=?",
                                (conversation_ref,)).fetchone()
        if boundary is not None and boundary["interval_id"] != "conversation_start":
            observed.append(boundary["interval_id"])
            raise OSError("Controlled Note-only read failure after durable native publication")
        return select_note_conn(database, conn, conversation_ref)
    monkeypatch.setattr("secretary.noting_notes.select_note_conn", broken_after_commit)
    native, results, errors = compress_async(parent, force=True)
    native.join(10)
    assert not native.is_alive() and observed
    assert any(row.get("is_compaction") for row in db.get_full_foreground(conversation_ref=ref))
    assert errors == [] and len(results) == 1
    assert compression_state(parent)["state"] == "completed"
    assert notes(db, ref) == []
    assert db.notebook_current(ref)["snapshot_id"] == snapshot
    monkeypatch.setattr("secretary.noting_notes.select_note_conn", select_note_conn)
    parent._session_messages = results[0][0]  # The native caller adopts its successful result normally.
    assert check_note_delivery(parent)
    assert len(notes(db, ref)) == 1


def test_note_observation_guard_does_not_swallow_native_summary_failure(runtime, monkeypatch):
    parent, db, client, children = runtime
    finish_provider(client)
    def fail(*args, **kwargs):
        raise RuntimeError("Controlled original native summary failure")
    monkeypatch.setattr(parent.context_compressor, "compress", fail)
    native, results, errors = compress_async(parent, force=True)
    native.join(10)
    for worker in children:
        worker.join(10)
    assert not native.is_alive() and results == []
    assert len(errors) == 1 and "original native summary failure" in str(errors[0])
    # Native exception cleanup revokes its fence; the original exception still
    # propagates, rather than being converted into a successful result.
    assert compression_state(parent)["state"] == "cancelled"
    assert notes(db, parent._secretary_conversation_ref) == []
