"""C-R6: real recovery owners participate in Note requalification and settlement."""

import json
import subprocess
import sys
import threading

import pytest

from secretary import noting_child, noting_recovery
from secretary.framework_messages import mark_framework_turn
from secretary.notebook_store import NotebookStore
from secretary.noting_notes import check_note_delivery, select_note_conn
from tests.secretary.test_joint_noting_u20 import notes, wait_for
from tests.secretary.test_noting_child import _tool_response
from tests.secretary.test_recovery_note_source_u20 import (
    actual_notes, await_recovery, failed_carried_task, next_native_boundary,
    reject, rpc_setup, rpc_recover,
)

pytest_plugins = ["tests.secretary.test_noting_child", "tests.secretary.test_joint_noting_u20"]


def queued_old_note(runtime, monkeypatch):
    parent, db, client, _children = runtime
    ref = parent._secretary_conversation_ref
    original, child_id = failed_carried_task(runtime, monkeypatch)
    old = NotebookStore(db, ref, anchor_message_uid="m1").commit(
        termination={"type": "finish_noting", "reason": "Valid earlier source, late result"})
    assert check_note_delivery(parent) and len(notes(db, ref)) == 1
    mark_framework_turn(parent, running=True)
    next_native_boundary(runtime, monkeypatch)
    assert len(notes(db, ref)) == 1 and parent._secretary_framework_messages
    client.chat.completions.create.reset_mock()
    return original, child_id, old, rpc_setup(parent, db, monkeypatch)


def native_lease(db, operation):
    return db._read_one("SELECT * FROM session_turn_leases WHERE conversation_id=?", ("recovery:" + operation,))


def hold_worker(monkeypatch):
    entered, release = threading.Event(), threading.Event()
    run = noting_recovery._run_recovery
    def held(*args, **kwargs):
        entered.set()
        assert release.wait(20)
        return run(*args, **kwargs)
    monkeypatch.setattr(noting_recovery, "_run_recovery", held)
    return entered, release


@pytest.mark.parametrize("succeed", [True, False])
def test_inflight_recovery_requalifies_queued_note_and_terminal_check_publishes_once(runtime, monkeypatch, succeed):
    parent, db, client, _children = runtime
    ref = parent._secretary_conversation_ref
    original, child_id, old, server = queued_old_note(runtime, monkeypatch)
    child_before = db.noting_child(original["admission_id"])
    entered, release = threading.Event(), threading.Event()
    def provider(**kwargs):
        entered.set()
        assert release.wait(20)
        if not succeed:
            raise reject()
        return _tool_response("finish_noting", {"reason": "Recovered latest source"}, "finish")
    client.chat.completions.create.side_effect = provider
    publish = noting_child._publish_committed_completion
    observed = []
    def during_commit(child, conversation, termination, outcome):
        config = json.loads(db.get_session(child.session_id)["model_config"])["_noting_recovery"]
        assert config["status"] == "running" and not config.get("committed")
        result = publish(child, conversation, termination, outcome)
        assert native_lease(db, child.session_id) is not None
        assert notes(db, ref)[-1]["snapshot_id"] == outcome.snapshot_id
        observed.append(outcome.snapshot_id)
        return result
    monkeypatch.setattr(noting_child, "_publish_committed_completion", during_commit)
    ack = rpc_recover(server, ref, child_id, "inflight")
    assert "error" not in ack, ack
    try:
        assert entered.wait(10)
        mark_framework_turn(parent, running=False)
        assert len(notes(db, ref)) == 1 and not parent._secretary_framework_messages
    finally:
        release.set()
    state = await_recovery(db, ref, child_id, "inflight")
    assert state["committed"] is succeed
    expected = state["snapshot_id"] if succeed else old["snapshot_id"]
    assert len(notes(db, ref)) == 2 and notes(db, ref)[-1]["snapshot_id"] == expected
    assert observed == ([expected] if succeed else [])
    assert len(actual_notes(parent, db)) == 2
    assert not check_note_delivery(parent)
    assert db.noting_admission(original["admission_id"]) == original
    assert db.noting_child(original["admission_id"]) == child_before
    assert native_lease(db, state["operation_id"]) is None


def test_queued_fact_already_has_exact_native_owner_before_worker_runs(runtime, monkeypatch):
    parent, db, client, _children = runtime
    ref = parent._secretary_conversation_ref
    _original, child_id, _old, server = queued_old_note(runtime, monkeypatch)
    entered, release = hold_worker(monkeypatch)
    client.chat.completions.create.side_effect = [
        _tool_response("finish_noting", {"reason": "Queued recovery completed"}, "finish")]
    ack = rpc_recover(server, ref, child_id, "queued")
    assert "error" not in ack, ack
    try:
        assert entered.wait(10)
        operation = ack["result"]["operation_id"]
        audit = json.loads(db.get_session(operation)["model_config"])["_noting_recovery"]
        assert audit["status"] == "queued" and native_lease(db, operation)["holder"] == audit["lease_holder"]
        repeat = rpc_recover(server, ref, child_id, "queued")
        assert repeat["result"]["operation_id"] == operation
        assert not client.chat.completions.create.called
        # Actual append requalification must not acquire the recovery registry
        # lock while it owns the DB transaction.
        with noting_recovery._RECOVERY_LOCK:
            flusher = threading.Thread(target=lambda: mark_framework_turn(parent, running=False))
            flusher.start()
            flusher.join(5)
            assert not flusher.is_alive()
        assert len(notes(db, ref)) == 1
    finally:
        release.set()
    state = await_recovery(db, ref, child_id, "queued")
    assert state["committed"] and len(notes(db, ref)) == 2
    assert client.chat.completions.create.call_count == 1


@pytest.mark.parametrize("failure", ["worker_start", "parent_constructor", "db_constructor"])
def test_start_or_constructor_failure_releases_reservation_and_rechecks_old_candidate(runtime, monkeypatch, failure):
    parent, db, client, _children = runtime
    ref = parent._secretary_conversation_ref
    _original, child_id, old, server = queued_old_note(runtime, monkeypatch)
    def fail(*args, **kwargs):
        raise RuntimeError("Controlled recovery startup failure")
    if failure == "worker_start":
        class BrokenWorker:
            start = fail
        monkeypatch.setattr("agent.memory_provider.spawn_context_thread", lambda *args, **kwargs: BrokenWorker())
    if failure == "parent_constructor":
        monkeypatch.setattr(server, "_make_agent", fail)
    if failure == "db_constructor":
        monkeypatch.setattr("hermes_state.SessionDB", fail)
    from tui_gateway.methods_noting_recovery import _noting_recovery_parent
    operation = noting_recovery._operation_id(ref, child_id, failure)
    if failure == "parent_constructor":
        ack = noting_recovery.start_recovery(db, ref, child_id, failure, parent_factory=_noting_recovery_parent)
        assert ack["operation_id"] == operation
        state = await_recovery(db, ref, child_id, failure)
        assert state["status"] == "failed"
    else:
        with pytest.raises(RuntimeError, match="startup failure"):
            noting_recovery.start_recovery(db, ref, child_id, failure, parent_factory=_noting_recovery_parent)
        row = db.get_session(operation)
        assert row is None if failure == "db_constructor" else json.loads(row["model_config"])["_noting_recovery"]["status"] == "failed"
    assert native_lease(db, operation) is None
    assert (str(db.db_path.resolve()), operation) not in noting_recovery._WORKERS
    mark_framework_turn(parent, running=False)
    assert len(notes(db, ref)) == 2 and notes(db, ref)[-1]["snapshot_id"] == old["snapshot_id"]
    assert not client.chat.completions.create.called


@pytest.mark.parametrize("loss", ["expired", "absent", "different_holder"])
def test_dead_queued_owner_cannot_block_or_later_start_and_release_another_owner(runtime, monkeypatch, loss):
    parent, db, client, _children = runtime
    ref = parent._secretary_conversation_ref
    _original, child_id, old, server = queued_old_note(runtime, monkeypatch)
    entered, release = hold_worker(monkeypatch)
    ack = rpc_recover(server, ref, child_id, loss)
    assert "error" not in ack, ack
    operation = ack["result"]["operation_id"]
    replacement = noting_recovery._recovery_holder("another-owner")
    try:
        assert entered.wait(10)
        holder = native_lease(db, operation)["holder"]
        if loss == "expired":
            db._execute_write(lambda conn: conn.execute(
                "UPDATE session_turn_leases SET expires_at=0 WHERE conversation_id=?", ("recovery:" + operation,)))
        else:
            db.release_session_turn_lease("recovery:" + operation, holder)
        if loss == "different_holder":
            assert db.acquire_session_turn_lease("recovery:" + operation, replacement, wait_seconds=0)
        state = noting_recovery.recovery_state(db, ref, child_id, loss)
        assert state["status"] == "interrupted"
        mark_framework_turn(parent, running=False)
        assert len(notes(db, ref)) == 2 and notes(db, ref)[-1]["snapshot_id"] == old["snapshot_id"]
    finally:
        release.set()
    wait_for(lambda: (str(db.db_path.resolve()), operation) not in noting_recovery._WORKERS)
    assert not client.chat.completions.create.called
    if loss == "different_holder":
        assert native_lease(db, operation)["holder"] == replacement
        db.release_session_turn_lease("recovery:" + operation, replacement)


def test_concurrent_same_request_uses_one_actual_recovery_loop(runtime, monkeypatch):
    parent, db, client, _children = runtime
    ref = parent._secretary_conversation_ref
    original, child_id, _old, server = queued_old_note(runtime, monkeypatch)
    entered, release, ready = threading.Event(), threading.Event(), threading.Barrier(3)
    def provider(**kwargs):
        entered.set()
        assert release.wait(20)
        return _tool_response("finish_noting", {"reason": "One idempotent execution"}, "finish")
    client.chat.completions.create.side_effect = provider
    results = []
    def request():
        ready.wait(10)
        results.append(rpc_recover(server, ref, child_id, "concurrent"))
    workers = [threading.Thread(target=request) for _ in range(2)]
    for worker in workers:
        worker.start()
    try:
        ready.wait(10)
        for worker in workers:
            worker.join(10)
            assert not worker.is_alive()
        assert entered.wait(10)
        assert len(results) == 2 and all("error" not in result for result in results), results
        assert len({result["result"]["operation_id"] for result in results}) == 1
        assert client.chat.completions.create.call_count == 1
        mark_framework_turn(parent, running=False)
        assert len(notes(db, ref)) == 1
    finally:
        release.set()
    state = await_recovery(db, ref, child_id, "concurrent")
    assert state["committed"] and len(notes(db, ref)) == 2
    assert db.noting_admission(original["admission_id"]) == original


def test_cross_process_prepublication_reservation_is_busy_and_same_id_retry_executes_once(runtime, monkeypatch, tmp_path):
    parent, db, client, _children = runtime
    ref = parent._secretary_conversation_ref
    _original, child_id, _old, server = queued_old_note(runtime, monkeypatch)
    operation = noting_recovery._operation_id(ref, child_id, "cross-process")
    ready = tmp_path / "lease-ready.json"
    script = """
import json,sys
from pathlib import Path
from hermes_state import SessionDB
from secretary.noting_recovery import _recovery_holder
conn=SessionDB(Path(sys.argv[1])); holder=_recovery_holder(sys.argv[2])
assert conn.acquire_session_turn_lease('recovery:'+sys.argv[2],holder,wait_seconds=0)
Path(sys.argv[3]).write_text(json.dumps({'holder':holder}))
sys.stdin.readline()
conn.release_session_turn_lease('recovery:'+sys.argv[2],holder);conn.close()
"""
    process = subprocess.Popen([sys.executable, "-c", script, str(db.db_path), operation, str(ready)],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        wait_for(ready.exists)
        ack = rpc_recover(server, ref, child_id, "cross-process")
        assert ack["error"]["code"] == 4002 and "being reserved" in ack["error"]["message"]
        assert db.get_session(operation) is None and not client.chat.completions.create.called
        assert native_lease(db, operation)["holder"] == json.loads(ready.read_text())["holder"]
    finally:
        stdout, stderr = process.communicate("\n", timeout=10)
        assert process.returncode == 0, (stdout, stderr)
    client.chat.completions.create.side_effect = [
        _tool_response("finish_noting", {"reason": "Same request after reservation released"}, "finish")]
    ack = rpc_recover(server, ref, child_id, "cross-process")
    assert "error" not in ack, ack
    mark_framework_turn(parent, running=False)
    state = await_recovery(db, ref, child_id, "cross-process")
    assert state["committed"] and client.chat.completions.create.call_count == 1


def test_one_recovery_commit_does_not_hide_another_newer_operation_on_same_source(runtime, monkeypatch):
    parent, db, client, _children = runtime
    ref = parent._secretary_conversation_ref
    _original, child_id, _old, server = queued_old_note(runtime, monkeypatch)
    operations = [noting_recovery._operation_id(ref, child_id, name) for name in ("first", "second")]
    entered = {key: threading.Event() for key in operations}
    releases = {key: threading.Event() for key in operations}
    def provider(**kwargs):
        key = threading.current_thread().name
        entered[key].set()
        assert releases[key].wait(20)
        if key == operations[1]:
            raise reject()
        return _tool_response("finish_noting", {"reason": "First operation committed"}, "finish")
    client.chat.completions.create.side_effect = provider
    try:
        for request, key in zip(("first", "second"), operations):
            ack = rpc_recover(server, ref, child_id, request)
            assert "error" not in ack and entered[key].wait(10), ack
        mark_framework_turn(parent, running=False)
        assert len(notes(db, ref)) == 1
        releases[operations[0]].set()
        first = await_recovery(db, ref, child_id, "first")
        assert first["committed"] and len(notes(db, ref)) == 1
    finally:
        for event in releases.values():
            event.set()
    second = await_recovery(db, ref, child_id, "second")
    assert not second["committed"]
    assert len(notes(db, ref)) == 2 and notes(db, ref)[-1]["snapshot_id"] == first["snapshot_id"]


def test_active_recovery_lease_loss_refuses_late_snapshot_commit(runtime, monkeypatch):
    parent, db, client, _children = runtime
    ref = parent._secretary_conversation_ref
    _original, child_id, old, server = queued_old_note(runtime, monkeypatch)
    entered, release = threading.Event(), threading.Event()
    def provider(**kwargs):
        entered.set()
        assert release.wait(20)
        return _tool_response("finish_noting", {"reason": "Late result from lost owner"}, "finish")
    client.chat.completions.create.side_effect = provider
    ack = rpc_recover(server, ref, child_id, "lost-active")
    assert "error" not in ack, ack
    operation = ack["result"]["operation_id"]
    try:
        assert entered.wait(10)
        lease = native_lease(db, operation)
        db.release_session_turn_lease("recovery:" + operation, lease["holder"])
        assert noting_recovery.recovery_state(db, ref, child_id, "lost-active")["status"] == "interrupted"
        mark_framework_turn(parent, running=False)
        assert len(notes(db, ref)) == 2 and notes(db, ref)[-1]["snapshot_id"] == old["snapshot_id"]
    finally:
        release.set()
    wait_for(lambda: (str(db.db_path.resolve()), operation) not in noting_recovery._WORKERS)
    state = noting_recovery.recovery_state(db, ref, child_id, "lost-active")
    assert state["status"] == "abandoned" and not state["committed"] and not state["snapshot_id"]
    assert db.notebook_current(ref)["snapshot_id"] == old["snapshot_id"]


def test_recovery_qualification_uses_exact_database_and_conversation(runtime, monkeypatch, tmp_path):
    import sqlite3
    from hermes_state import SessionDB
    parent, db, client, _children = runtime
    ref = parent._secretary_conversation_ref
    _original, child_id, old, server = queued_old_note(runtime, monkeypatch)
    entered, release = hold_worker(monkeypatch)
    client.chat.completions.create.side_effect = [
        _tool_response("finish_noting", {"reason": "Finish exact owner"}, "finish")]
    ack = rpc_recover(server, ref, child_id, "scope")
    assert "error" not in ack, ack
    try:
        assert entered.wait(10)
        db.create_session("foreign", source="test")
        db.append_message("foreign", "user", "Foreign source", message_uid="foreign-1")
        foreign = db.resolve_conversation_ref("foreign")
        snapshot = NotebookStore(db, foreign, anchor_message_uid="foreign-1").commit(
            termination={"type": "finish_noting", "reason": "Foreign Notebook"})
        db.archive_and_compact("foreign", [{"role": "user", "content": "Summary", "_compressed_summary": True,
                                           "message_uid": "foreign-boundary"}])
        with db._read_ctx() as conn:
            assert select_note_conn(db, conn, ref) is None
            assert select_note_conn(db, conn, foreign)["snapshot_id"] == snapshot["snapshot_id"]
        path = tmp_path / "separate-state.db"
        with sqlite3.connect(str(db.db_path)) as source, sqlite3.connect(str(path)) as target:
            source.backup(target)
        other = SessionDB(path)
        try:
            other._execute_write(lambda conn: conn.execute("DELETE FROM session_turn_leases"))
            with other._read_ctx() as conn:
                assert select_note_conn(other, conn, ref)["snapshot_id"] == old["snapshot_id"]
            assert native_lease(db, ack["result"]["operation_id"]) is not None
        finally:
            other.close()
    finally:
        release.set()
    assert await_recovery(db, ref, child_id, "scope")["committed"]


def test_process_restart_with_running_audit_and_dead_native_holder_does_not_block(runtime, monkeypatch):
    parent, db, client, _children = runtime
    ref = parent._secretary_conversation_ref
    original, child_id, old, _server = queued_old_note(runtime, monkeypatch)
    operation = noting_recovery._operation_id(ref, child_id, "orphan")
    audit = {"conversation_ref": ref, "failed_child_session_id": child_id, "admission_id": original["admission_id"],
             "request_id": "orphan", "status": "running", "created_at": original["admitted_at"] + 1}
    script = """
import json,sys
from pathlib import Path
from hermes_state import SessionDB
from secretary.noting_recovery import _recovery_holder
db=SessionDB(Path(sys.argv[1]));holder=_recovery_holder(sys.argv[2]);audit=json.loads(sys.argv[3])
audit['lease_holder']=holder
assert db.acquire_session_turn_lease('recovery:'+sys.argv[2],holder,wait_seconds=0)
db.create_session(sys.argv[2],source='subagent',parent_session_id=sys.argv[4],
                  model_config={'_delegate_from':sys.argv[4],'_noting_recovery':audit})
db.close()
"""
    completed = subprocess.run([sys.executable, "-c", script, str(db.db_path), operation, json.dumps(audit),
                                db.get_session(child_id)["parent_session_id"]], capture_output=True, text=True, timeout=10)
    assert completed.returncode == 0, completed.stderr
    assert native_lease(db, operation)["expires_at"] > original["admitted_at"]
    state = noting_recovery.recovery_state(db, ref, child_id, "orphan")
    assert state["status"] == "interrupted"
    repeat = noting_recovery.start_recovery(db, ref, child_id, "orphan", parent_factory=lambda *args: pytest.fail("No replay"))
    assert repeat["status"] == "interrupted" and not client.chat.completions.create.called
    mark_framework_turn(parent, running=False)
    assert len(notes(db, ref)) == 2 and notes(db, ref)[-1]["snapshot_id"] == old["snapshot_id"]
