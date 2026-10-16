"""Real-SQLite behavior of Noting admission, the child registry and durable Idle timing.

07 §8.1 (same-Anchor dedupe and durable Force interval occupation), inherited Idle
timing across restart, and real successful native compaction boundaries.
"""

import threading

import pytest

from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
from tests.hermes_state._secretary_noting_harness import add, empty_state, make, open_noting_db, ref_of


@pytest.fixture
def db(tmp_path):
    db = open_noting_db(tmp_path / "state.db")
    yield db
    db.close()


def _count_expression(db, table):
    with db._read_ctx() as conn:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_schema_init_is_idempotent_inside_the_callers_transaction(db):
    from hermes_state_secretary_noting import init_secretary_noting_schema

    db._execute_write(lambda conn: (
        init_secretary_noting_schema(conn.cursor()), init_secretary_noting_schema(conn.cursor())))

    with db._read_ctx() as conn:
        names = {row[0] for row in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name LIKE 'secretary_noting_%'")}
    assert names == {
        "secretary_noting_admissions", "secretary_noting_children", "secretary_noting_idle_state",
        "secretary_noting_compaction_state",
    }


def test_admission_is_idempotent_per_anchor_and_kind_agnostic(db):
    make(db, "s")
    add(db, "s", "turn", "m1")
    ref = ref_of(db, "s")

    first = db.noting_admit(ref, "m1", kind="idle")
    assert isinstance(first, int)
    assert db.noting_admit(ref, "m1", kind="idle") is None
    # Same Anchor, other trigger: still one admission (02 §4.8 same-Anchor dedupe).
    assert db.noting_admit(ref, "m1", kind="force") is None
    second = db.noting_admit(ref, "m2", kind="force")
    assert isinstance(second, int) and second != first

    row = db.noting_admission(first)
    assert (row["conversation_ref"], row["anchor_message_uid"], row["kind"]) == (ref, "m1", "idle")


def test_admission_rejects_unknown_kind(db):
    make(db, "s")
    ref = ref_of(db, "s")
    with pytest.raises(ValueError):
        db.noting_admit(ref, "m1", kind="compact_parent")
    with pytest.raises(ValueError):
        db.noting_admit("", "m1", kind="idle")


def test_same_anchor_admits_once_under_concurrency(tmp_path):
    path = tmp_path / "state.db"
    setup = open_noting_db(path)
    make(setup, "s")
    add(setup, "s", "turn", "m1")
    ref = ref_of(setup, "s")
    setup.close()

    results = []
    results_lock = threading.Lock()
    barrier = threading.Barrier(2)

    def _admit():
        handle = open_noting_db(path)
        try:
            barrier.wait(timeout=10)
            admission_id = handle.noting_admit(ref, "m1", kind="force")
        finally:
            handle.close()
        with results_lock:
            results.append(admission_id)

    threads = [threading.Thread(target=_admit) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert sum(1 for value in results if isinstance(value, int)) == 1
    assert results.count(None) == 1
    admission_id = next(value for value in results if isinstance(value, int))

    check = open_noting_db(path)
    try:
        assert check.noting_admission(admission_id)["anchor_message_uid"] == "m1"
        assert _count_expression(check, "secretary_noting_admissions") == 1
    finally:
        check.close()


def test_different_anchors_admit_concurrently(tmp_path):
    path = tmp_path / "state.db"
    setup = open_noting_db(path)
    make(setup, "s")
    add(setup, "s", "turn", "m1")
    ref = ref_of(setup, "s")
    setup.close()

    results = {}
    barrier = threading.Barrier(2)

    def _admit(uid):
        handle = open_noting_db(path)
        try:
            barrier.wait(timeout=10)
            results[uid] = handle.noting_admit(ref, uid, kind="idle")
        finally:
            handle.close()

    threads = [threading.Thread(target=_admit, args=("m1",)),
               threading.Thread(target=_admit, args=("m2",))]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert all(isinstance(value, int) for value in results.values())
    assert results["m1"] != results["m2"]


def test_child_registry_binds_a_child_and_records_terminal_status(db):
    make(db, "s")
    ref = ref_of(db, "s")
    admission_id = db.noting_admit(ref, "m1", kind="idle")

    db.noting_child_register(admission_id, child_session_id="child-1", profile="default")
    child = db.noting_child(admission_id)
    assert (child["child_session_id"], child["profile"], child["status"]) == ("child-1", "default", "running")
    assert child["finished_at"] is None

    # Re-registration rebinds identity without erasing the lifecycle record.
    db.noting_child_register(admission_id, child_session_id="child-2", profile="default")
    assert db.noting_child(admission_id)["child_session_id"] == "child-2"

    assert db.noting_child_finish(admission_id, status="completed") is True
    finished = db.noting_child(admission_id)
    assert finished["status"] == "completed" and finished["finished_at"] is not None
    assert db.noting_child_finish(9999, status="completed") is False
    with pytest.raises(ValueError):
        db.noting_child_register(9999, child_session_id="x", profile=None)


def test_idle_timing_and_admission_survive_a_restart(tmp_path):
    path = tmp_path / "state.db"
    db = open_noting_db(path)
    make(db, "s")
    ref = ref_of(db, "s")
    db.noting_idle_turn_started(ref, 1000.0)
    db.noting_idle_turn_finished(ref, 1500.0)
    admission_id = db.noting_admit(ref, "m1", kind="idle")
    db.close()

    reopened = open_noting_db(path)
    try:
        state = reopened.noting_idle_state(ref)
        assert (state["last_turn_started_at"], state["last_turn_finished_at"]) == (1000.0, 1500.0)
        assert reopened.noting_admission(admission_id)["anchor_message_uid"] == "m1"
        assert reopened.noting_admit(ref, "m1", kind="idle") is None
        assert reopened.noting_idle_due_conversations(now=2000.0, delay_seconds=500) == [ref]
        assert reopened.noting_idle_due_conversations(now=1999.0, delay_seconds=500) == []
    finally:
        reopened.close()


def test_idle_due_requires_the_last_event_to_be_a_finish(db):
    make(db, "a")
    make(db, "b")
    ref_a, ref_b = ref_of(db, "a"), ref_of(db, "b")
    db.noting_idle_turn_finished(ref_a, 1000.0)
    db.noting_idle_turn_started(ref_a, 1200.0)  # a new main Turn began: not idle
    db.noting_idle_turn_finished(ref_b, 1000.0)
    db.noting_idle_turn_started(ref_b, 1200.0)
    db.noting_idle_turn_finished(ref_b, 1300.0)

    assert db.noting_idle_due_conversations(now=3000.0, delay_seconds=500) == [ref_b]
    assert db.noting_idle_state(ref_a)["last_turn_started_at"] == 1200.0


@pytest.mark.parametrize("kind", ["idle", "manual", "auto_compaction", "force"])
def test_all_current_joint_kinds_share_the_native_interval(db, kind):
    make(db, "s")
    add(db, "s", "original", "m1")
    admission = db.noting_admit(ref_of(db, "s"), "m1", kind=kind)
    assert db.noting_admission(admission)["compression_interval_id"] == "conversation_start"


def test_force_interval_uses_successful_native_boundary_and_not_snapshot_or_child_end(db):
    make(db, "s")
    add(db, "s", "archived", "a")
    ref = ref_of(db, "s")
    admission = db.noting_admit(ref, "a", kind="force")
    assert isinstance(admission, int)
    db.notebook_commit_snapshot(ref, empty_state(), anchor_message_uid="a", trigger_type="force",
                                runtime_profile="NOTING", termination={"type": "finish_noting", "reason": "Completed"})
    db.noting_child_register(admission, child_session_id="child", profile="test")
    assert db.noting_child_finish(admission, status="completed")
    add(db, "s", "new anchor in occupied interval", "next")
    for kind in ("force", "idle", "manual", "auto_compaction"):
        assert db.noting_admit(ref, "next", kind=kind) is None
    db.archive_and_compact("s", [{"role": "user", "content": SUMMARY_PREFIX + "summary\n" + _SUMMARY_END_MARKER,
                                  "_compressed_summary": True, "message_uid": "sum"}])
    add(db, "s", "after the boundary", "b")
    next_admission = db.noting_admit(ref, "b", kind="force")
    assert isinstance(next_admission, int)
    state = db._read_one("SELECT interval_id,boundary_message_uid FROM secretary_noting_compaction_state WHERE conversation_ref=?", (ref,))
    assert state["boundary_message_uid"] == "sum"
    assert db.noting_admission(next_admission)["compression_interval_id"] == state["interval_id"] != "conversation_start"
    assert db.noting_admission(admission)["compression_interval_id"] == "conversation_start"
