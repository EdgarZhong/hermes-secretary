"""Real native operation cancellation contends with the actual Snapshot write transaction."""

import threading

import pytest

from agent.compression_read import cancel_compression, compression_state
from secretary import noting_joint
from tests.agent.test_context_compaction_request import _summary
from tests.secretary.test_joint_noting_u20 import admissions, compress_async, finish_provider

pytest_plugins = ["tests.secretary.test_noting_child", "tests.secretary.test_joint_noting_u20"]


@pytest.mark.parametrize("commit_first", [True, False])
def test_native_cancel_and_snapshot_commit_contend_at_actual_write_transaction(runtime, monkeypatch, commit_first):
    parent, db, client, children = runtime
    summary_entered, summary_release, transaction_entered, transaction_release = [threading.Event() for _ in range(4)]
    commit_waiting, cancel_entered = threading.Event(), threading.Event()
    finish_provider(client)

    def summary(messages, **kwargs):
        summary_entered.set()
        assert summary_release.wait(10)
        return _summary(messages, **kwargs)

    record_commit = noting_joint.record_commit
    finish_child = db.noting_child_finish_conn

    def held_commit(*args):
        record_commit(*args)
        if commit_first:
            transaction_entered.set()
            assert transaction_release.wait(10)

    def held_cancel(conn, admission_id, *, status):
        result = finish_child(conn, admission_id, status=status)
        if status == "cancelled" and not commit_first:
            transaction_entered.set()
            assert transaction_release.wait(10)
        return result

    # For cancel-first, pause before the transaction is acquired. The real gate
    # still runs after cancellation wins; no helper or qualification is replaced.
    real_commit = __import__("secretary.noting_child", fromlist=["commit_noting_snapshot"]).commit_noting_snapshot

    def start_commit(*args, **kwargs):
        if not commit_first:
            commit_waiting.set()
            assert transaction_entered.wait(10)
            assert transaction_release.wait(10)
        return real_commit(*args, **kwargs)

    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    monkeypatch.setattr(noting_joint, "record_commit", held_commit)
    monkeypatch.setattr(db, "noting_child_finish_conn", held_cancel)
    monkeypatch.setattr("secretary.noting_child.commit_noting_snapshot", start_commit)
    native, _results, errors = compress_async(parent, force=True)
    cancel_result = []

    def cancel():
        cancel_entered.set()
        cancel_result.append(cancel_compression(parent, operation))

    canceller = threading.Thread(target=cancel)
    try:
        assert summary_entered.wait(10)
        operation = compression_state(parent)["operation_id"]
        if commit_first:
            assert transaction_entered.wait(10)
        else:
            assert commit_waiting.wait(10)
        canceller.start()
        assert cancel_entered.wait(10)
        if not commit_first:
            assert transaction_entered.wait(10)
        transaction_release.set()
        canceller.join(10)
        assert not canceller.is_alive()
        summary_release.set()
        native.join(10)
        for child in children:
            child.join(10)
        assert errors == [] and cancel_result[0]["outcome"] == "cancelled"
        admitted = admissions(db)[0]
        assert admitted["state"] == ("committed" if commit_first else "cancelled")
        assert (db.notebook_current(admitted["conversation_ref"]) is not None) == commit_first
        assert db.noting_child(admitted["admission_id"])["status"] == ("completed" if commit_first else "cancelled")
    finally:
        transaction_release.set()
        summary_release.set()
        native.join(10)
        if canceller.ident is not None:
            canceller.join(10)


@pytest.mark.parametrize("parent_state", ["closed", "capability_lost", "replaced"])
def test_frozen_task_commit_does_not_depend_on_live_parent_handle(runtime, monkeypatch, parent_state):
    from secretary import noting_runtime as rt
    from tests.secretary.test_noting_child import _tool_response, mock_response
    parent, db, client, children = runtime
    entered, release = threading.Event(), threading.Event()
    count = []
    def provider(**kwargs):
        entered.set()
        assert release.wait(10)
        count.append(1)
        return (_tool_response("finish_noting", {"reason": "Frozen work complete"}, "finish")
                if len(count) == 1 else mock_response("Done"))
    client.chat.completions.create.side_effect = provider
    decision = rt.prepare_joint_noting(parent, trigger="manual")
    assert decision.action == "admit" and entered.wait(10)
    try:
        if parent_state == "closed":
            parent._secretary_parent_closed = True
        elif parent_state == "capability_lost":
            parent.context_compressor = None
        else:
            from tests.secretary.test_noting_runtime import _agent
            replacement = _agent(db, parent.session_id)
            replacement.context_compressor = None
        release.set()
        children[0].join(10)
        assert not children[0].is_alive()
        assert db.noting_admission(decision.admission.admission_id)["state"] == "committed"
        assert db.notebook_current(decision.admission.conversation_ref) is not None
    finally:
        release.set()
