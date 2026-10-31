"""Real transactional plan, bounded history, restart and concurrent claim contracts."""
from concurrent.futures import ThreadPoolExecutor
import threading
import time

from hermes_state import SessionDB
from secretary import adaptive_runtime as runtime, adaptive_store as store, noting_runtime as noting
from secretary.heartbeat_store import ConversationHeartbeatStore, due_conversations
from hermes_cli.heartbeat import HeartbeatState
import pytest
from tests.secretary import test_adaptive_runtime


@pytest.fixture
def owned(tmp_path, monkeypatch):
    yield from test_adaptive_runtime.owned.__wrapped__(tmp_path, monkeypatch)


def test_main_finish_atomically_adopts_three_outputs_and_user_queue_invalidates(owned, monkeypatch):
    parent, db, ref = owned
    seen = []
    def decide(snapshot, history, config):
        seen.append(snapshot)
        return {"mode": "hot", "threshold_tokens": 4000, "delay_seconds": 30}
    monkeypatch.setattr("secretary.adaptive_policy.decide", decide)
    assert noting.note_main_turn_finished(parent, at=100)
    with db._read_ctx() as conn:
        plan, hb = store.plan_conn(conn, ref), store.heartbeat_conn(conn, ref)
    assert plan["decision"]["threshold_tokens"] == 4000 and hb["mode"] == "hot"
    assert db.noting_idle_state(ref)["due_at"] == 130
    assert seen[0]["heartbeat_next_due"] is None and seen[0]["last_user_at"] is None
    runtime.user_arrived(db, "main", at=110, event_id="user-queue")
    assert db.noting_idle_state(ref)["trigger_produced_at"] == 110
    assert db.noting_idle_claim_event(ref, now=140, delay_seconds=500) == "idle_trigger_produced"


def test_bad_policy_and_explicit_fallback_preserve_native_delay(owned, monkeypatch):
    parent, db, ref = owned
    for result in ({"mode": "bad"}, {"mode": "business", "threshold_tokens": None, "delay_seconds": None, "fallback": True}):
        monkeypatch.setattr("secretary.adaptive_policy.decide", lambda *args: result)
        assert noting.note_main_turn_finished(parent, at=100)
        assert db.noting_idle_state(ref)["due_at"] == 600
    with db._read_ctx() as conn:
        assert store.plan_conn(conn, ref) is None


def test_policy_no_early_consumes_cycle_and_does_not_disable_force(owned, monkeypatch):
    parent, db, ref = owned
    monkeypatch.setattr("secretary.adaptive_policy.decide", lambda *args: {"mode": "business", "threshold_tokens": None, "delay_seconds": None})
    assert noting.note_main_turn_finished(parent, at=100)
    assert db.noting_idle_state(ref)["trigger_produced_at"] == 100
    assert noting._threshold_skip(noting.ContextMeasurement(70000, 130000, 75000)) is None


def test_plan_cas_rejects_intervening_main_period(owned):
    parent, db, ref = owned
    before = db.noting_idle_state(ref)
    db.noting_idle_turn_started(ref, 200)
    config = runtime.settings.for_db(db)
    assert not store.commit_plan(db, ref, at=100, expected_period=before, config=config,
                                 context_epoch="old", decision={"mode": "hot", "threshold_tokens": 1, "delay_seconds": 10})
    assert db.noting_idle_state(ref)["last_turn_started_at"] == 200


def test_bounded_history_filters_future_before_tail_and_restart(owned):
    parent, db, ref = owned
    def write(conn):
        for i in range(2053):
            store.event_conn(conn, ref, {"event_id": str(i), "at": i, "kind": "turn_end", "source": "unknown", "verified": False})
    db._execute_write(write)
    events = store.history(db, ref, 2000, limit=4)
    assert [item["at"] for item in events] == [1997, 1998, 1999, 2000]
    assert len(store.history(db, ref, 3000)) == 2048
    other = SessionDB(db.db_path)
    try:
        assert store.history(other, ref, 2000, limit=4) == events
    finally:
        other.close()


def test_infinite_business_to_hot_preserves_real_anchor_and_claim_refund(owned):
    parent, db, ref = owned
    hb = ConversationHeartbeatStore(db, "main")
    hb.save(HeartbeatState("", 600, created_at=1))
    config = runtime.settings.for_db(db)
    db._execute_write(lambda conn: store.adopt_mode_conn(conn, ref, "business", config))
    assert hb.load().status == "active" and hb.load()._adaptive_infinite
    assert hb.claim(1000) is None and due_conversations(db, now=1000) == []
    db._execute_write(lambda conn: store.adopt_mode_conn(conn, ref, "hot", config))
    assert hb.load().created_at == 1
    result = hb.claim(1000)
    assert result is not None
    state, claim = result
    db._execute_write(lambda conn: store.adopt_mode_conn(conn, ref, "business", config))
    assert hb.claim_is_current(claim)
    assert hb.refund(claim)
    assert hb.load().fire_count == 0 and hb.load().created_at == 1
    assert hb.claim(1001) is None


def test_concurrent_connections_claim_once_and_pause_wins(owned):
    parent, db, ref = owned
    hb = ConversationHeartbeatStore(db, "main")
    hb.save(HeartbeatState("", 600, created_at=1))
    config = runtime.settings.for_db(db)
    db._execute_write(lambda conn: store.adopt_mode_conn(conn, ref, "hot", config))
    other = SessionDB(db.db_path)
    barrier = threading.Barrier(2)
    def claim(handle):
        barrier.wait(3)
        return ConversationHeartbeatStore(handle, "main").claim(100)
    try:
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(claim, (db, other)))
        assert sum(item is not None for item in results) == 1
        claimed = next(item[1] for item in results if item is not None)
        hb.set_status("paused")
        assert not hb.refund(claimed) and not hb.claim_is_current(claimed)
        assert hb.claim(1000) is None
    finally:
        other.close()


def test_matching_due_idle_precedes_heartbeat_until_consumed(owned, monkeypatch):
    parent, db, ref = owned
    hb = ConversationHeartbeatStore(db, "main")
    hb.save(HeartbeatState("", 600, created_at=1))
    monkeypatch.setattr("secretary.adaptive_policy.decide", lambda *args: {"mode": "hot", "threshold_tokens": 4000, "delay_seconds": 0})
    assert noting.note_main_turn_finished(parent, at=100)
    assert hb.claim(100) is None
    assert db.noting_idle_claim_event(ref, now=100, delay_seconds=500) == "trigger"
    assert hb.claim(100) is not None


def test_missing_historical_anchor_uses_first_configuration_clock_and_survives_restart(owned):
    parent, db, ref = owned
    hb = ConversationHeartbeatStore(db, "main")
    hb.save(HeartbeatState("", 600, created_at=0))
    config = runtime.settings.for_db(db)
    config["_configured_at"] = 100
    db._execute_write(lambda conn: store.adopt_mode_conn(conn, ref, "business", config))
    db._execute_write(lambda conn: store.adopt_mode_conn(conn, ref, "hot", config))
    assert hb.claim(159) is None
    other = SessionDB(db.db_path)
    try:
        reopened = ConversationHeartbeatStore(other, "main")
        assert reopened.load().created_at == 100
        assert ref in due_conversations(other, now=160)
        assert reopened.claim(160) is not None
    finally:
        other.close()


def test_real_processes_share_one_heartbeat_claim(owned):
    import subprocess
    import sys
    parent, db, ref = owned
    hb = ConversationHeartbeatStore(db, "main")
    hb.save(HeartbeatState("", 600, created_at=1))
    config = runtime.settings.for_db(db)
    db._execute_write(lambda conn: store.adopt_mode_conn(conn, ref, "hot", config))
    script = """import sys
from pathlib import Path
from hermes_state import SessionDB
from secretary.heartbeat_store import ConversationHeartbeatStore
handle=SessionDB(Path(sys.argv[1]))
try:
    print(int(ConversationHeartbeatStore(handle,'main').claim(100) is not None))
finally:
    handle.close()
"""
    workers = [subprocess.Popen([sys.executable, "-c", script, str(db.db_path)], stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True) for _ in range(2)]
    results = [worker.communicate(timeout=20) for worker in workers]
    assert all(worker.returncode == 0 for worker in workers), results
    assert sorted(stdout.strip() for stdout, _stderr in results) == ["0", "1"]
    assert hb.load().fire_count == 1


def test_restart_restores_absolute_idle_deadline_without_replanning(owned, monkeypatch):
    from secretary.noting_timers import attach_idle_timer
    from tests.secretary.test_noting_runtime import _agent
    parent, db, ref = owned
    monkeypatch.setattr("secretary.adaptive_policy.decide", lambda *args: {"mode": "hot", "threshold_tokens": 4000, "delay_seconds": 3000})
    now = time.time()
    assert noting.note_main_turn_finished(parent, at=now)
    reopened = SessionDB(db.db_path)
    try:
        resumed = _agent(reopened, "main")
        armed = []
        monkeypatch.setattr("secretary.noting_timers.arm_idle_timer", lambda parent, handle, owner, due: armed.append(due))
        assert attach_idle_timer(resumed, reopened, ref, now=now + 1000) == "skip:timer_armed"
        assert armed == [now + 3000]
        assert runtime.idle_settings(resumed, noting.settings_for_db(reopened)).idle_threshold_tokens == 4000
    finally:
        reopened.close()


def test_first_native_claim_defers_mode_update_until_refund(owned):
    parent, db, ref = owned
    hb = ConversationHeartbeatStore(db, "main")
    hb.save(HeartbeatState("", 600, created_at=1))
    state, claim = hb.claim(1000)
    config = runtime.settings.for_db(db)
    db._execute_write(lambda conn: store.adopt_mode_conn(conn, ref, "business", config))
    assert hb.claim_is_current(claim) and hb.load()._adaptive_interval_seconds == 600
    assert hb.refund(claim)
    assert hb.load()._adaptive_infinite and hb.load().fire_count == 0


def test_conflicting_event_identity_becomes_unknown_instead_of_first_writer_truth(owned):
    parent, db, ref = owned
    first = {"event_id": "same", "at": 1, "kind": "request", "source": "user", "verified": True, "input_tokens": 10}
    second = {**first, "input_tokens": 100}
    assert db._execute_write(lambda conn: store.event_conn(conn, ref, first))
    assert not db._execute_write(lambda conn: store.event_conn(conn, ref, {**first, "at": 2}))
    assert store.history(db, ref, 10)[-1]["verified"]
    assert not db._execute_write(lambda conn: store.event_conn(conn, ref, second))
    event = store.history(db, ref, 10)[-1]
    assert event["verified"] is False and event["source"] == "unknown" and event["conflict"] is True


def test_explicit_heartbeat_replacement_clears_old_policy_period(owned):
    parent, db, ref = owned
    hb = ConversationHeartbeatStore(db, "main")
    hb.save(HeartbeatState("", 600, created_at=1))
    config = runtime.settings.for_db(db)
    db._execute_write(lambda conn: store.adopt_mode_conn(conn, ref, "hot", config))
    assert hb.load().interval_seconds == 600 and hb.load()._adaptive_interval_seconds == 60
    hb.save(HeartbeatState("new explicit", 900, created_at=100))
    assert hb.load().interval_seconds == 900 and hb.claim(200) is None
    with db._read_ctx() as conn:
        assert store.heartbeat_conn(conn, ref) is None


def test_global_noting_off_ignores_existing_adaptive_heartbeat_sidecar(owned):
    from pathlib import Path
    parent, db, ref = owned
    hb = ConversationHeartbeatStore(db, "main")
    hb.save(HeartbeatState("", 600, created_at=1))
    config = runtime.settings.for_db(db)
    db._execute_write(lambda conn: store.adopt_mode_conn(conn, ref, "hot", config))
    assert hb.load().interval_seconds == 600 and hb.load()._adaptive_interval_seconds == 60
    path = Path(db.db_path).parent / "config.yaml"
    path.write_text(path.read_text().replace("  enabled: true", "  enabled: false", 1))
    assert runtime.settings.for_db(db) is None
    assert hb.load().interval_seconds == 600 and hb.load()._adaptive_interval_seconds == 600
    assert ref not in due_conversations(db, now=100) and hb.claim(100) is None
