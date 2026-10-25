"""Cross-process Noting presence through real child, commit and native compaction."""

import json
import subprocess
import sys
import threading
import time
from datetime import datetime

import pytest

from hermes_state import SessionDB
from tests.secretary.test_idle_noting_commit_order import finish_responses, result_rows, start_idle

pytest_plugins = ["tests.secretary.test_idle_noting_commit_order"]

_READ_STATE = """
import json,sys
from pathlib import Path
from hermes_state import SessionDB
from secretary.web_read import secretary_state
with SessionDB(Path(sys.argv[1]), read_only=True) as db:
    with db._read_ctx() as conn:
        before = tuple(conn.iterdump())
    result = secretary_state(db, sys.argv[2])
    with db._read_ctx() as conn:
        assert tuple(conn.iterdump()) == before
    print(json.dumps(result))
"""


def remote_state(db, session_id):
    result = subprocess.run(
        [sys.executable, "-c", _READ_STATE, str(db.db_path), session_id],
        check=True, capture_output=True, text=True, timeout=15,
    )
    return json.loads(result.stdout)


@pytest.mark.parametrize("in_place", [True, False], ids=["in-place", "rotation"])
def test_other_process_observes_task_through_committed_notebook_and_native_summary(
        idle_runtime, monkeypatch, tmp_path, in_place):
    parent, db, client, workers = idle_runtime
    parent.compression_in_place = in_place
    finish_responses(client)
    ref, original_session = parent._secretary_conversation_ref, parent.session_id
    entered, release = threading.Event(), threading.Event()
    model_states = []
    responses = iter(client.chat.completions.create.side_effect)

    def respond(**kwargs):
        if not model_states:
            model_states.append(remote_state(db, original_session))
        return next(responses)

    def summarize(prompt, started):
        entered.set()
        assert release.wait(30)
        return "## Progress\nThe frozen dialogue was reviewed."

    client.chat.completions.create.side_effect = respond
    monkeypatch.setattr(parent.context_compressor, "_call_summary_llm", summarize)
    try:
        assert start_idle(parent, db) == "admitted"
        assert entered.wait(25)
        child = db._read_one("SELECT child_session_id,registered_at FROM secretary_noting_children "
                             "WHERE status='running'")
        assert child is not None and db.notebook_current(ref) is not None
        # The model Turn has ended; the whole Task still owns commit/summary/publication.
        assert db._read_one("SELECT 1 FROM session_turn_leases WHERE conversation_id=?",
                            (child["child_session_id"],)) is None
        state = remote_state(db, original_session)
        assert model_states[0]["task_state"] == state["task_state"] == "active"
        assert state["current_snapshot_id"] == db.notebook_current(ref)["snapshot_id"]
        assert state["tasks"][0]["task_id"] == child["child_session_id"]
        assert abs(datetime.fromisoformat(state["tasks"][0]["started_at"]).timestamp()
                   - child["registered_at"]) < 1
        assert workers[0].is_alive() and not result_rows(parent)
        # A second Profile with the same stored id has neither this Task nor its lease.
        with SessionDB(tmp_path / "other" / "state.db") as other:
            other.create_session(original_session, source="desktop")
            other.resolve_conversation_ref(original_session)
            assert remote_state(other, original_session)["task_state"] == "idle"
    finally:
        release.set()
        for worker in workers:
            worker.join(15)
    assert not workers[0].is_alive() and len(result_rows(parent)) == 1
    assert remote_state(db, original_session)["task_state"] == "idle"
    assert db._read_one("SELECT 1 FROM secretary_noting_task_leases WHERE child_session_id=?",
                        (child["child_session_id"],)) is None
    assert (parent.session_id == original_session) is in_place
    # The real native commit prices the summary; its later Framework increases
    # current cold Context without reviving the pre-compaction transcript.
    from agent.usage_anchor import persisted_context_estimate
    reading = db.get_session_model_config_value(parent.session_id, "_usage_context")
    assert reading["priced_tail"]["count"] == 1
    current_context = persisted_context_estimate(db, parent.session_id, model=parent.model, recover_legacy=True)
    assert current_context["tokens"] > reading["tokens"]


def test_presence_renews_and_expired_or_unproven_registration_stays_unknown(tmp_path):
    from types import SimpleNamespace
    from secretary.noting_child import register_active_noting_task, unregister_active_noting_task

    with SessionDB(tmp_path / "state.db") as db:
        db.create_session("main", source="desktop")
        db.append_message("main", "user", "Evidence", message_uid="m1")
        ref = db.resolve_conversation_ref("main")
        admission = db.noting_admit(ref, "m1", kind="idle")
        db.noting_child_register(admission, child_session_id="child", profile="default")
        assert remote_state(db, "main")["task_state"] == "unknown"
        child = SimpleNamespace(_session_db=db, _secretary_parent_conversation_ref=ref)
        register_active_noting_task("child", child)
        try:
            presence = child._secretary_task_presence
            register_active_noting_task("child", child)
            assert child._secretary_task_presence is presence
            assert remote_state(db, "main")["task_state"] == "active"
            db._execute_write(lambda conn: conn.execute(
                "UPDATE secretary_noting_task_leases SET expires_at=? WHERE child_session_id=?",
                (time.time() - 1, "child")))
            assert remote_state(db, "main")["task_state"] == "unknown"
            assert child._secretary_task_presence.refresh() is None
            assert remote_state(db, "main")["task_state"] == "active"
        finally:
            unregister_active_noting_task("child", child)
        # A crash/restart or failed terminal write cannot turn a stale running row into activity.
        assert remote_state(db, "main")["task_state"] == "unknown"
        db.noting_child_finish(admission, status="failed")
        assert remote_state(db, "main")["task_state"] == "idle"


def test_recovery_presence_uses_existing_native_operation_owner_without_rebinding_failed_child(tmp_path):
    from types import SimpleNamespace
    from secretary.noting_child import register_active_noting_task, unregister_active_noting_task

    with SessionDB(tmp_path / "state.db") as db:
        db.create_session("main", source="desktop")
        db.append_message("main", "user", "Evidence", message_uid="m1")
        ref = db.resolve_conversation_ref("main")
        admission = db.noting_admit(ref, "m1", kind="idle")
        db.noting_child_register(admission, child_session_id="failed-child", profile="default")
        db.noting_child_finish(admission, status="failed")
        original = db.noting_child(admission)
        db.create_session("recovery-child", source="subagent", parent_session_id="main", model_config={
            "_noting_recovery": {"conversation_ref": ref, "status": "running", "created_at": time.time()},
        })
        child = SimpleNamespace(_session_db=db, _secretary_parent_conversation_ref=ref)
        register_active_noting_task("recovery-child", child)
        try:
            state = remote_state(db, "main")
            assert state["task_state"] == "active"
            assert [task["task_id"] for task in state["tasks"]] == ["recovery-child"]
            db.create_session("foreign", source="desktop")
            db.resolve_conversation_ref("foreign")
            child._secretary_parent_conversation_ref = db.resolve_conversation_ref("foreign")
            assert remote_state(db, "foreign")["task_state"] == "idle"
        finally:
            unregister_active_noting_task("recovery-child", child)
        assert remote_state(db, "main")["task_state"] == "unknown"
        db.end_session("recovery-child", "completed")
        assert remote_state(db, "main")["task_state"] == "idle"
        assert db.noting_child(admission) == original


@pytest.mark.parametrize("failure", ["unavailable", "summary_error"])
def test_observation_or_native_summary_failure_never_changes_committed_notebook(
        idle_runtime, monkeypatch, failure):
    parent, db, client, workers = idle_runtime
    finish_responses(client)
    if failure == "unavailable":
        def unavailable(_presence):
            raise OSError("Observation store unavailable")
        monkeypatch.setattr("secretary.noting_task_presence._TaskPresence.start", unavailable)

    def summarize(prompt, started):
        state = remote_state(db, parent.session_id)
        observed.append(state["task_state"])
        if failure == "summary_error":
            raise RuntimeError("Native summary unavailable")
        return "## Progress\nReviewed."

    observed = []
    monkeypatch.setattr(parent.context_compressor, "_call_summary_llm", summarize)
    assert start_idle(parent, db) == "admitted"
    workers[0].join(25)
    assert not workers[0].is_alive()
    assert observed == ["unknown" if failure == "unavailable" else "active"]
    assert db.notebook_current(parent._secretary_conversation_ref) is not None
    assert len(result_rows(parent)) == 1
    assert remote_state(db, parent.session_id)["task_state"] == "idle"
    assert db._read_one("SELECT 1 FROM session_turn_leases") is None
    assert db._read_one("SELECT 1 FROM secretary_noting_task_leases") is None


def test_presence_namespace_and_same_child_ids_in_different_databases_are_isolated(tmp_path):
    from types import SimpleNamespace
    from secretary.noting_child import active_noting_task, register_active_noting_task, unregister_active_noting_task

    with SessionDB(tmp_path / "a" / "state.db") as first, SessionDB(tmp_path / "b" / "state.db") as second:
        children = []
        for db in (first, second):
            db.create_session("main", source="desktop")
            db.append_message("main", "user", "Evidence", message_uid="m1")
            ref = db.resolve_conversation_ref("main")
            admission = db.noting_admit(ref, "m1", kind="idle")
            db.noting_child_register(admission, child_session_id="child", profile="default")
            child = SimpleNamespace(_session_db=db, _secretary_parent_conversation_ref=ref)
            register_active_noting_task("child", child)
            children.append(child)
        try:
            for db, child in zip((first, second), children):
                assert active_noting_task("child", db=db) is child
                assert remote_state(db, "main")["task_state"] == "active"
                for session_id in ("child", "noting-task:child"):
                    assert db.try_acquire_session_turn_lease(session_id, "ordinary-turn")
                    db.release_session_turn_lease(session_id, "ordinary-turn")
            unregister_active_noting_task("child", children[0])
            assert children[0]._secretary_task_presence.stopped.is_set()
            assert not children[1]._secretary_task_presence.stopped.is_set()
            assert remote_state(first, "main")["task_state"] == "unknown"
            assert remote_state(second, "main")["task_state"] == "active"
            assert first.try_acquire_session_turn_lease("noting-task:child", "unrelated-turn")
            assert remote_state(first, "main")["task_state"] == "unknown"
            first.release_session_turn_lease("noting-task:child", "unrelated-turn")
        finally:
            for child in children:
                unregister_active_noting_task("child", child)
        assert all(child._secretary_task_presence.stopped.is_set() for child in children)
        assert first._read_one("SELECT 1 FROM secretary_noting_task_leases") is None
        assert second._read_one("SELECT 1 FROM secretary_noting_task_leases") is None
