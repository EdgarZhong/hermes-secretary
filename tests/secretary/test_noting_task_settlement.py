"""U20 task terminal state is independent of deferred parent Framework publication."""

import json
import subprocess
import sys
import threading

import pytest

from secretary import noting_child
from secretary.framework_messages import flush_framework_messages, mark_framework_turn
from secretary.notebook_model import SECTIONS
from tests.secretary.test_idle_noting_commit_order import result_rows

pytest_plugins = ["tests.secretary.test_noting_child", "tests.secretary.test_joint_noting_u20"]


def remote_state(db, session_id):
    script = """import json,sys
from hermes_state import SessionDB
from secretary.web_read import secretary_state
with SessionDB(sys.argv[1], read_only=True) as db:
    print(json.dumps(secretary_state(db, sys.argv[2])))
"""
    result = subprocess.run([sys.executable, "-c", script, str(db.db_path), session_id],
                            check=True, capture_output=True, text=True, timeout=10)
    return json.loads(result.stdout)


def capture_close(parent, monkeypatch):
    children, close_threads = [], []
    closed = threading.Event()
    build = noting_child.build_noting_child

    def construct(*args, **kwargs):
        child = build(*args, **kwargs)
        children.append(child)
        original = child.close

        def close():
            assert not parent._secretary_framework_lock._is_owned()
            persist = getattr(parent, "_session_persist_lock", None)
            assert persist is None or not persist._is_owned()
            close_threads.append(threading.get_ident())
            original()
            closed.set()

        child.close = close
        return child

    monkeypatch.setattr(noting_child, "build_noting_child", construct)
    return children, closed, close_threads


def defer_at_commit(parent, monkeypatch):
    commit = noting_child._commit_when_complete

    def busy(*args, **kwargs):
        mark_framework_turn(parent, running=True)
        return commit(*args, **kwargs)

    monkeypatch.setattr(noting_child, "_commit_when_complete", busy)


@pytest.mark.parametrize("failure", [False, True], ids=["completed", "failed"])
@pytest.mark.parametrize("disposition", ["write", "owner_changed", "superseded", "append_failure", "runtime_invalid"])
def test_task_finishes_independently_of_deferred_carrier(runtime, monkeypatch, failure, disposition):
    from tests.agent.test_context_compaction_request import _summary
    from tests.secretary.test_joint_noting_u20 import admissions, compress_async, finish_provider, wait_for

    parent, db, client, workers = runtime
    children, closed, close_threads = capture_close(parent, monkeypatch)
    finish_provider(client)
    entered, release = threading.Event(), threading.Event()
    def summary(messages, **kwargs):
        entered.set()
        assert release.wait(10)
        return _summary(messages, **kwargs)
    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    if failure:
        monkeypatch.setattr("run_agent.AIAgent.run_conversation", lambda *args, **kwargs: {
            "completed": False, "failed": True, "error": "provider unavailable", "turn_exit_reason": "api_error"})
    defer_at_commit(parent, monkeypatch)
    original_session, ref = parent.session_id, parent._secretary_conversation_ref
    native, _result, errors = compress_async(parent, force=True)
    try:
        assert entered.wait(10)
        wait_for(lambda: len(workers) == 1)
        workers[0].join(10)
        assert not workers[0].is_alive() and closed.is_set()
        child, admitted = children[0], admissions(db)[0]
        assert noting_child.active_noting_task(child.session_id, db=db) is None
        assert db.noting_child(admitted["admission_id"])["status"] == ("failed" if failure else "completed")
        assert remote_state(db, original_session)["task_state"] == "idle"
        release.set()
        native.join(10)
        assert errors == [] and parent._secretary_framework_messages
        def fail(*args, **kwargs):
            raise RuntimeError("tail store unavailable")
        actions = {
            "write": lambda: None,
            "owner_changed": lambda: setattr(parent, "_secretary_conversation_ref", "different-owner"),
            "superseded": lambda: db.notebook_commit_snapshot(
                ref, {section: [] for section in SECTIONS}, anchor_message_uid="m10", termination={"type": "forced"}),
            "append_failure": lambda: monkeypatch.setattr("secretary.framework_messages.append_runtime_row", fail),
            "runtime_invalid": lambda: setattr(parent, "side_agent", True),
        }
        actions[disposition]()
        mark_framework_turn(parent, running=False)
        assert db.get_session(child.session_id)["ended_at"] is not None
        assert flush_framework_messages(parent) == 0 and len(close_threads) == 1
        expected = disposition == "write" or failure and disposition == "superseded"
        assert len(result_rows(parent)) == int(expected)
        assert db.noting_child(admitted["admission_id"])["status"] == ("failed" if failure else "completed")
    finally:
        release.set()
        native.join(10)
        parent._secretary_conversation_ref = ref
        mark_framework_turn(parent, running=False)


def test_cleanup_needs_no_background_dispatch_after_execution(runtime, monkeypatch):
    from tests.secretary.test_joint_noting_u20 import admissions, finish_provider
    from secretary.noting_runtime import prepare_joint_noting
    parent, db, client, workers = runtime
    _children, closed, close_threads = capture_close(parent, monkeypatch)
    finish_provider(client)
    defer_at_commit(parent, monkeypatch)
    decision = prepare_joint_noting(parent, trigger="manual")
    assert decision.action == "admit"
    workers[0].join(10)
    assert closed.is_set() and close_threads == [workers[0].ident]
    assert db.noting_child(admissions(db)[0]["admission_id"])["status"] == "completed"
    assert not getattr(parent, "_secretary_framework_messages", [])  # Current interval never receives its own Note.
