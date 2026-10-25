"""Real Noting owners survive deferred Framework publication and retire once."""

import json
import subprocess
import sys
import threading

import pytest

from secretary import noting_child
from secretary.framework_messages import flush_framework_messages, mark_framework_turn
from secretary.notebook_model import SECTIONS
from tests.secretary.test_idle_noting_commit_order import finish_responses, result_rows, start_idle

pytest_plugins = ["tests.secretary.test_idle_noting_commit_order", "tests.secretary.test_noting_recovery"]


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
def test_deferred_carrier_owns_task_until_publication_or_retirement(
        idle_runtime, monkeypatch, failure, disposition):
    parent, db, client, workers = idle_runtime
    children, closed, close_threads = capture_close(parent, monkeypatch)
    finish_responses(client)
    monkeypatch.setattr(parent, "request_context_compaction", lambda **kwargs: True)
    if failure:
        monkeypatch.setattr("run_agent.AIAgent.run_conversation", lambda *args, **kwargs: {
            "completed": False, "failed": True, "error": "provider unavailable", "turn_exit_reason": "api_error"})
    defer_at_commit(parent, monkeypatch)
    original_session, ref = parent.session_id, parent._secretary_conversation_ref
    try:
        assert start_idle(parent, db) == "admitted"
        workers[0].join(10)
        assert not workers[0].is_alive() and not closed.is_set()
        assert parent._secretary_framework_messages and not result_rows(parent)
        child = children[0]
        assert noting_child.active_noting_task(child.session_id, db=db) is child
        assert db.noting_child(1)["status"] == "running"
        assert remote_state(db, original_session)["task_state"] == "active"
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
        assert closed.wait(5)
        assert noting_child.active_noting_task(child.session_id, db=db) is None
        assert db.noting_child(1)["status"] == ("failed" if failure else "completed")
        assert db.get_session(child.session_id)["ended_at"] is not None
        assert remote_state(db, original_session)["task_state"] == "idle"
        assert flush_framework_messages(parent) == 0 and len(close_threads) == 1
        expected = disposition == "write" or failure and disposition == "superseded"
        assert len(result_rows(parent)) == int(expected)
    finally:
        parent._secretary_conversation_ref = ref
        mark_framework_turn(parent, running=False)


def test_synchronous_carrier_keeps_cleanup_on_original_worker(idle_runtime, monkeypatch):
    parent, db, client, workers = idle_runtime
    _children, closed, close_threads = capture_close(parent, monkeypatch)
    finish_responses(client)
    monkeypatch.setattr(parent, "request_context_compaction", lambda **kwargs: True)
    assert start_idle(parent, db) == "admitted"
    workers[0].join(10)
    assert not workers[0].is_alive() and closed.is_set()
    assert close_threads == [workers[0].ident]
    assert db.noting_child(1)["status"] == "completed"
    assert len(result_rows(parent)) == 1


def test_real_recovery_retains_task_owner_until_its_carrier_settles(native_parent, database, monkeypatch):
    from secretary.noting_recovery import start_recovery
    from secretary.noting_scope import bind_main_runtime
    from tests.secretary.test_noting_recovery import factory, failed_task, wait_recovery
    from tests.secretary.test_r3_child import ref, response, tool_response

    parent, client = native_parent
    failed = failed_task(native_parent, database)
    original_registration = database.noting_child(1)
    children, closed, _threads = capture_close(parent, monkeypatch)
    assert bind_main_runtime(parent)
    mark_framework_turn(parent, running=True)
    client.chat.completions.create.side_effect = [
        tool_response("finish_noting", {"reason": "Checked the recovered work"}), response("Done"),
    ]
    build = factory(parent)
    def recover_parent(db, recovered):
        cold = build(db, recovered)
        # The live Main rebinds after cold construction, as it does on native
        # Turn entry. Its busy queue remains the completion publication owner.
        assert bind_main_runtime(parent)
        return cold
    try:
        start_recovery(database, ref(database), failed.child_session_id, "r1", parent_factory=recover_parent)
        state = wait_recovery(database, failed)
        assert state["committed"] and len(children) == 1
        assert not closed.is_set() and parent._secretary_framework_messages
        assert remote_state(database, parent.session_id)["task_state"] == "active"
        mark_framework_turn(parent, running=False)
        assert closed.wait(5)
        assert remote_state(database, parent.session_id)["task_state"] == "idle"
        assert database.get_session(state["child_session_id"])["ended_at"] is not None
        assert database.noting_child(1) == original_registration
    finally:
        mark_framework_turn(parent, running=False)


@pytest.mark.parametrize("timer_available", [True, False], ids=["timer-fallback", "both-unavailable"])
def test_close_dispatch_failure_retains_owner_and_single_cleanup(idle_runtime, monkeypatch, timer_available):
    parent, db, client, workers = idle_runtime
    _children, closed, close_threads = capture_close(parent, monkeypatch)
    finish_responses(client)
    monkeypatch.setattr(parent, "request_context_compaction", lambda **kwargs: True)
    defer_at_commit(parent, monkeypatch)
    assert start_idle(parent, db) == "admitted"
    workers[0].join(10)
    assert not workers[0].is_alive() and not closed.is_set()
    carrier = parent._secretary_framework_messages[0]

    def unavailable(*args, **kwargs):
        raise RuntimeError("background workers unavailable")

    with monkeypatch.context() as broken:
        broken.setattr("agent.memory_provider.spawn_context_thread", unavailable)
        if not timer_available:
            broken.setattr("agent.periodic_scheduler.schedule", unavailable)
        mark_framework_turn(parent, running=False)
        if timer_available:
            assert closed.wait(5)
        else:
            assert not closed.is_set()
            assert db.noting_child(1)["status"] == "running"
    if not timer_available:
        # Failed dispatch retained the original claim; retrying settlement can
        # finish it after execution capacity returns, without a second close.
        carrier.on_settled()
        assert closed.wait(5)
    carrier.on_settled()
    assert len(close_threads) == 1 and db.noting_child(1)["status"] == "completed"
