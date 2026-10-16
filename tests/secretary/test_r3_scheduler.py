"""C3 behavior contracts. CLOUD_CODE: authored, NOT_RUN.

The SQLite fixture intentionally has no Notebook tables. Store/host tests additionally
use the real SessionDB and therefore require C1/C4/C9 integration before local execution.
Run locally through scripts/run_tests.sh, not by a separate cloud test invocation.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import sqlite3
from threading import Barrier
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import pytest

from hermes_state_secretary_schedule import (
    ScheduleError,
    init_secretary_schedule_schema,
    reminder_ack_conn,
    reminder_bind_carrier_conn,
    reminder_revalidate_pending_conn,
    schedule_carrier_durable_conn,
    schedule_claim_conn,
    schedule_current_claim_conn,
    schedule_definition_conn,
    schedule_finalize_conn,
    schedule_queue_pending_conn,
    schedule_release_conn,
)
from secretary.scheduler_table import (
    NO_INSTANT_NOTICE,
    UNKNOWN_INSTANT_NOTICE,
    apply_schedule_action_conn,
    coverage_notice,
    instant_coverage_conn,
)
from secretary.scheduler_time import (
    epoch_to_utc_iso,
    parse_schedule_expression,
    schedule_advance_epoch,
    schedule_initial_next_run,
)
from secretary.schedules import SchedulerStore, default_enablement, scan_and_claim_due

NOW = 1_800_000_000.0


@pytest.fixture
def conn(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_TIMEZONE", "UTC")
    db = sqlite3.connect(tmp_path / "scheduler.db")
    db.row_factory = sqlite3.Row
    db.executescript("""
        CREATE TABLE secretary_conversations(conversation_ref TEXT PRIMARY KEY,created_at REAL);
        INSERT INTO secretary_conversations VALUES ('a',0),('b',0);
        CREATE TABLE secretary_session_bindings(session_id TEXT PRIMARY KEY,conversation_ref TEXT);
        INSERT INTO secretary_session_bindings VALUES ('sa','a'),('sb','b');
        CREATE TABLE messages(id INTEGER PRIMARY KEY,session_id TEXT,message_uid TEXT,
                              role TEXT,content TEXT,active INTEGER DEFAULT 1,compacted INTEGER DEFAULT 0);
    """)
    init_secretary_schedule_schema(db)
    db.commit()
    yield db
    db.close()


def call(conn, action, *, ref="a", now=NOW, **args):
    with conn:
        return apply_schedule_action_conn(conn, ref, {"action": action, **args}, now=now)


def create(conn, *, ref="a", due=NOW - 1, mode="instant", expression=None, content="Review the result"):
    result = call(conn, "create", ref=ref, content=content,
                  schedule=expression or epoch_to_utc_iso(due), delivery_mode=mode)
    return result["schedule"]["schedule_id"]


def claim(conn, sid, *, now=NOW, lease=60):
    with conn:
        return schedule_claim_conn(conn, sid, owner="worker", now=now, lease_seconds=lease)


def queue(conn, sid, *, now=NOW):
    owned = claim(conn, sid, now=now)
    with conn:
        return schedule_queue_pending_conn(conn, owned, now=now)


def native_row(conn, *, uid="carrier", text="scheduled attention", sid="sa"):
    conn.execute("INSERT INTO messages(session_id,message_uid,role,content) VALUES (?,?,?,?)",
                 (sid, uid, "user", text))
    return uid, text


def bind(conn, rid, *, now=NOW, uid="carrier", text="scheduled attention"):
    with conn:
        current = reminder_revalidate_pending_conn(conn, "a", rid)
        native_row(conn, uid=uid, text=text)
        reminder_bind_carrier_conn(conn, "a", [current], carrier_message_uid=uid,
                                   carrier_content=text, now=now)


def test_native_duration_and_profile_timezone(monkeypatch):
    import cron.jobs as native

    zone = ZoneInfo("Asia/Tokyo")
    monkeypatch.setattr(native, "_hermes_now", lambda: datetime.fromtimestamp(NOW, zone))
    assert parse_schedule_expression("30m")["kind"] == "interval"
    assert parse_schedule_expression("every 2h")["minutes"] == 120
    once = parse_schedule_expression("in 30m")
    assert once["kind"] == "once"
    assert datetime.fromisoformat(once["run_at"]).timestamp() == NOW + 1800
    naive = parse_schedule_expression("2026-10-17T09:00:00")
    assert naive["run_at"].endswith("+09:00")
    assert schedule_initial_next_run(naive, now=NOW) < NOW


def test_native_next_run_uses_supplied_epoch_and_bounded_backlog(monkeypatch):
    import cron.jobs as native

    calls = []
    original = native.compute_next_run

    def tracked(schedule, last_run_at=None):
        calls.append(last_run_at)
        return original(schedule, last_run_at)

    monkeypatch.setattr(native, "compute_next_run", tracked)
    canonical = {"kind": "interval", "minutes": 30}
    assert schedule_initial_next_run(canonical, now=NOW) == NOW + 1800
    assert calls == [epoch_to_utc_iso(NOW)]
    calls.clear()
    result = schedule_advance_epoch(canonical, NOW - 100000, now=NOW, max_steps=2)
    assert result == NOW + 1800
    assert len(calls) == 3


def test_interval_keeps_elapsed_duration_across_dst(monkeypatch):
    import hermes_time

    monkeypatch.setenv("HERMES_TIMEZONE", "America/New_York")
    hermes_time.reset_cache()
    base = datetime(2026, 11, 1, 1, 30, tzinfo=ZoneInfo("America/New_York"), fold=0).timestamp()
    assert schedule_initial_next_run({"kind": "interval", "minutes": 60}, now=base) == base + 3600
    hermes_time.reset_cache()


def test_crud_without_notebook_and_public_fields(conn):
    sid = create(conn)
    assert "notebook_entry_id" not in schedule_definition_conn(conn, "a", sid)
    item = call(conn, "list")["schedules"][0]
    assert set(item) == {"schedule_id", "content", "expression", "canonical_schedule", "timezone",
                         "delivery_mode", "state", "next_due_at", "pending_count", "last_delivery"}
    assert item["last_delivery"] is None and item["state"] == "active"
    assert call(conn, "update", schedule_id=sid, name="review")["schedule"]["name"] == "review"
    assert "name" not in call(conn, "update", schedule_id=sid, name="")["schedule"]
    assert call(conn, "pause", schedule_id=sid)["schedule"]["state"] == "paused"
    assert call(conn, "pause", schedule_id=sid)["changed"] is False
    assert call(conn, "resume", schedule_id=sid)["schedule"]["state"] == "active"
    assert call(conn, "resume", schedule_id=sid)["changed"] is False
    assert call(conn, "delete", schedule_id=sid) == {
        "success": True, "changed": True, "schedule_id": sid, "deleted": True}
    assert call(conn, "list")["count"] == 0


def test_noop_does_not_reparse_reanchor_or_invalidate_claim(conn):
    sid = create(conn)
    before = claim(conn, sid)

    def forbidden(_expression):
        raise AssertionError("unchanged time expressions must not be reparsed")

    with conn:
        result = apply_schedule_action_conn(
            conn, "a", {"action": "update", "schedule_id": sid, "schedule": before["expression"]},
            now=NOW + 1, parser=forbidden,
        )
    assert result["changed"] is False
    assert schedule_definition_conn(conn, "a", sid) == before
    assert schedule_current_claim_conn(conn, before, now=NOW + 1) is not None


@pytest.mark.parametrize("args,field", [
    ({"action": "create", "content": "x", "schedule": "in 2h"}, "delivery_mode"),
    ({"action": "update", "schedule_id": "s"}, "action"),
    ({"action": "list", "content": "x"}, "content"),
    ({"action": "pause", "schedule_id": "s", "state": "active"}, "state"),
    ({"action": "create", "content": "", "schedule": "in 2h", "delivery_mode": "instant"}, "content"),
    ({"action": "list", "delivery_mode": "now"}, "delivery_mode"),
    ({"action": "update", "schedule_id": "s", "generation": 2}, "generation"),
    ({"action": "delete", "schedule_id": "s", "conversation_ref": "b"}, "conversation_ref"),
])
def test_invalid_arguments_are_atomic(conn, args, field):
    sid = create(conn)
    before = schedule_definition_conn(conn, "a", sid)
    with pytest.raises(ScheduleError) as error, conn:
        apply_schedule_action_conn(conn, "a", args, now=NOW)
    assert error.value.error["code"] == "invalid_argument"
    assert error.value.error["field"] == field
    assert schedule_definition_conn(conn, "a", sid) == before


def test_invalid_reschedule_rolls_back_content_and_pending(conn):
    sid = create(conn)
    rid = queue(conn, sid)
    before = reminder_revalidate_pending_conn(conn, "a", rid)
    with pytest.raises(ScheduleError), conn:
        apply_schedule_action_conn(conn, "a", {"action": "update", "schedule_id": sid,
                                   "content": "must not persist", "schedule": "not a time"}, now=NOW)
    assert reminder_revalidate_pending_conn(conn, "a", rid) == before


def test_owner_isolation_and_empty_new_table(conn):
    sid = create(conn)
    assert call(conn, "list", ref="b")["schedules"] == []
    with pytest.raises(ScheduleError) as error:
        call(conn, "delete", ref="b", schedule_id=sid)
    assert error.value.error["code"] == "schedule_not_found"
    assert call(conn, "list")["count"] == 1


def test_competing_connections_have_one_claim_winner(conn):
    sid = create(conn)
    path = conn.execute("PRAGMA database_list").fetchone()[2]
    barrier = Barrier(2)

    def worker(owner):
        other = sqlite3.connect(path, timeout=5)
        other.row_factory = sqlite3.Row
        try:
            barrier.wait(timeout=5)
            with other:
                other.execute("BEGIN IMMEDIATE")
                return schedule_claim_conn(other, sid, owner=owner, now=NOW, lease_seconds=10)
        finally:
            other.close()

    with ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(worker, ["one", "two"]))
    assert sum(result is not None for result in results) == 1
    first = next(result for result in results if result is not None)
    second = claim(conn, sid, now=NOW + 11)
    assert second["claim_token"] != first["claim_token"]
    with conn:
        assert schedule_queue_pending_conn(conn, first, now=NOW + 11) is None
        assert schedule_release_conn(conn, sid, first["claim_token"], now=NOW + 11) is False


@pytest.mark.parametrize("action,changes", [
    ("update", {"content": "replacement"}), ("pause", {}), ("delete", {}),
])
def test_control_committed_first_fences_old_worker(conn, action, changes):
    sid = create(conn)
    owned = claim(conn, sid)
    result = call(conn, action, schedule_id=sid, **changes)
    assert "delivery_in_flight" not in result
    with conn:
        assert schedule_queue_pending_conn(conn, owned, now=NOW) is None
        assert schedule_release_conn(conn, sid, owned["claim_token"], now=NOW) is False
    assert conn.execute("SELECT COUNT(*) FROM secretary_pending_reminders").fetchone()[0] == 0


def test_queued_once_is_not_completed_and_pause_resume_can_recover(conn):
    sid = create(conn)
    rid = queue(conn, sid)
    item = call(conn, "list")["schedules"][0]
    assert item["state"] == "active" and item["next_due_at"] is None
    assert item["pending_count"] == 1 and item["last_delivery"] is None
    assert reminder_ack_conn(conn, rid, now=NOW) is False
    call(conn, "pause", schedule_id=sid)
    assert reminder_revalidate_pending_conn(conn, "a", rid) is None
    call(conn, "resume", schedule_id=sid, now=NOW + 100)
    new_rid = queue(conn, sid, now=NOW + 100)
    assert new_rid != rid
    bind(conn, new_rid, now=NOW + 101)
    assert call(conn, "list")["schedules"][0]["state"] == "completed"
    with pytest.raises(ScheduleError) as error:
        call(conn, "resume", schedule_id=sid)
    assert error.value.error["code"] == "state_conflict"


def test_mode_and_content_update_refresh_unadmitted_occurrence(conn):
    sid = create(conn)
    rid = queue(conn, sid)
    before = reminder_revalidate_pending_conn(conn, "a", rid)
    call(conn, "update", schedule_id=sid, content="new content", delivery_mode="deferred", name="review")
    current = reminder_revalidate_pending_conn(conn, "a", rid)
    assert current["content"] == "new content"
    assert current["entry_payload"]["delivery_mode"] == "deferred"
    assert current["entry_payload"]["name"] == "review"
    assert current["origin_instant"] is True
    assert current["schedule_generation"] > before["schedule_generation"]
    assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 0


def test_stale_prepare_cannot_bind_a_refreshed_pending_row(conn):
    sid = create(conn)
    rid = queue(conn, sid)
    stale = reminder_revalidate_pending_conn(conn, "a", rid)
    call(conn, "update", schedule_id=sid, content="new content")
    with pytest.raises(ScheduleError), conn:
        native_row(conn, uid="old", text="old cached body")
        reminder_bind_carrier_conn(conn, "a", [stale], carrier_message_uid="old",
                                   carrier_content="old cached body", now=NOW)
    assert conn.execute("SELECT 1 FROM messages WHERE message_uid='old'").fetchone() is None
    assert reminder_revalidate_pending_conn(conn, "a", rid)["carrier_message_uid"] is None
    bind(conn, rid, text="new body")
    assert reminder_revalidate_pending_conn(conn, "a", rid)["carrier_content"] == "new body"


def test_reschedule_cancels_old_unadmitted_occurrence(conn):
    sid = create(conn)
    rid = queue(conn, sid)
    call(conn, "update", schedule_id=sid, schedule=epoch_to_utc_iso(NOW + 500))
    assert reminder_revalidate_pending_conn(conn, "a", rid) is None
    current = schedule_definition_conn(conn, "a", sid)
    assert current["next_run_at"] == NOW + 500
    assert current["sequence"] == 2
    assert claim(conn, sid) is None


def test_delete_preserves_carrier_and_late_ack_cannot_resurrect(conn):
    sid = create(conn)
    rid = queue(conn, sid)
    bind(conn, rid)
    result = call(conn, "delete", schedule_id=sid)
    assert result["delivery_in_flight"] is True
    assert reminder_revalidate_pending_conn(conn, "a", rid)["carrier_message_uid"] == "carrier"
    with conn:
        assert reminder_ack_conn(conn, rid, now=NOW + 1) is True
        assert reminder_ack_conn(conn, rid, now=NOW + 2) is True
    assert schedule_definition_conn(conn, "a", sid) is None
    assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 1


def test_paused_recurring_stays_paused_after_late_ack(conn):
    sid = create(conn, expression="1m", mode="deferred")
    rid = queue(conn, sid, now=NOW + 61)
    bind(conn, rid, now=NOW + 62)
    assert call(conn, "pause", schedule_id=sid, now=NOW + 63)["delivery_in_flight"] is True
    paused = schedule_definition_conn(conn, "a", sid)
    with conn:
        assert reminder_ack_conn(conn, rid, now=NOW + 64)
    assert schedule_definition_conn(conn, "a", sid) == paused
    assert claim(conn, sid, now=NOW + 1000) is None


def test_instant_requires_native_witness_and_then_cannot_replay(conn):
    sid = create(conn)
    owned = claim(conn, sid)
    with pytest.raises(ScheduleError), conn:
        schedule_finalize_conn(conn, sid, owned["claim_token"], now=NOW)
    with conn:
        uid, body = native_row(conn)
        after = schedule_finalize_conn(conn, sid, owned["claim_token"], now=NOW,
                                       carrier_message_uid=uid, carrier_content=body)
    assert after["state"] == "done"
    assert claim(conn, sid) is None
    assert call(conn, "delete", schedule_id=sid)["delivery_in_flight"] is True
    assert schedule_carrier_durable_conn(conn, "a", sid, uid, body) is True
    assert schedule_carrier_durable_conn(conn, "b", sid, uid, body) is False
    with conn:
        conn.execute("UPDATE messages SET active=0,compacted=1 WHERE message_uid=?", (uid,))
    assert schedule_carrier_durable_conn(conn, "a", sid, uid, body) is True


def test_pure_deferred_cannot_take_instant_settlement_path(conn):
    sid = create(conn, mode="deferred")
    owned = claim(conn, sid)
    with pytest.raises(ScheduleError), conn:
        uid, body = native_row(conn)
        schedule_finalize_conn(conn, sid, owned["claim_token"], now=NOW,
                               carrier_message_uid=uid, carrier_content=body)
    assert conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0] == 0
    assert schedule_definition_conn(conn, "a", sid)["state"] == "pending"


def test_failure_release_keeps_due_and_records_failure(conn):
    sid = create(conn)
    owned = claim(conn, sid)
    with conn:
        assert schedule_release_conn(conn, sid, owned["claim_token"], now=NOW)
    item = call(conn, "list")["schedules"][0]
    assert item["last_delivery"]["outcome"] == "failed"
    assert claim(conn, sid, now=NOW + 1) is not None


def test_pending_receipt_is_durable_across_reopen(conn):
    sid = create(conn)
    rid = queue(conn, sid)
    path = conn.execute("PRAGMA database_list").fetchone()[2]
    reopened = sqlite3.connect(path)
    reopened.row_factory = sqlite3.Row
    try:
        assert reminder_revalidate_pending_conn(reopened, "a", rid)["schedule_id"] == sid
        assert schedule_claim_conn(reopened, sid, owner="restart", now=NOW + 1000, lease_seconds=60) is None
    finally:
        reopened.close()


def test_coverage_is_inclusive_readonly_and_counts_other_overdue_instant(conn):
    sid = create(conn, due=NOW + 86400)
    before = schedule_definition_conn(conn, "a", sid)
    assert instant_coverage_conn(conn, "a", now=NOW) is True
    assert schedule_definition_conn(conn, "a", sid) == before
    call(conn, "update", schedule_id=sid, schedule=epoch_to_utc_iso(NOW + 86401))
    assert instant_coverage_conn(conn, "a", now=NOW) is False
    other = create(conn, due=NOW - 1000)
    assert instant_coverage_conn(conn, "a", now=NOW) is True
    assert instant_coverage_conn(conn, "a", now=NOW, exclude_occurrences=[(other, NOW - 1000)]) is False


def test_coverage_excludes_current_once_but_counts_next_recurring(conn):
    once = create(conn)
    assert instant_coverage_conn(conn, "a", now=NOW, exclude_occurrences=[(once, NOW - 1)]) is False
    recurring = create(conn, expression="30m")
    state = schedule_definition_conn(conn, "a", recurring)
    assert instant_coverage_conn(conn, "a", now=NOW + 1800,
                                 exclude_occurrences=[(once, NOW - 1), (recurring, state["next_run_at"])]) is True
    assert schedule_definition_conn(conn, "a", recurring) == state


def test_pending_paused_completed_and_pure_deferred_do_not_cover(conn):
    create(conn, mode="deferred")
    paused = create(conn)
    call(conn, "pause", schedule_id=paused)
    pending = create(conn)
    rid = queue(conn, pending)
    assert reminder_revalidate_pending_conn(conn, "a", rid)["origin_instant"] is True
    assert instant_coverage_conn(conn, "a", now=NOW) is False
    bind(conn, rid)
    assert instant_coverage_conn(conn, "a", now=NOW) is False


def test_uncomputable_coverage_is_unknown_not_absent(conn, monkeypatch):
    sid = create(conn, expression="30m")

    def broken(*_args, **_kwargs):
        raise RuntimeError("native next run unavailable")

    monkeypatch.setattr("secretary.scheduler_table.schedule_advance_epoch", broken)
    assert instant_coverage_conn(conn, "a", now=NOW + 1800,
                                 exclude_occurrences=[(sid, NOW + 1800)]) is None
    assert coverage_notice(None) == UNKNOWN_INSTANT_NOTICE
    assert coverage_notice(False) == NO_INSTANT_NOTICE
    assert coverage_notice(True) is None


@pytest.fixture
def store(tmp_path, monkeypatch):
    from hermes_state import SessionDB

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.setenv("HERMES_TIMEZONE", "UTC")
    db = SessionDB(tmp_path / "state.db")
    db.create_session("main", source="test", session_key="r3-c3")
    ref = db.resolve_conversation_ref("main", ("test", "r3-c3", 0))
    value = SchedulerStore(db, ref, session_id="main", is_enabled=lambda _ref: True)
    yield value
    db.close()


def test_tool_notice_uses_full_table_even_when_list_filters_hide_instant(store):
    store.create("instant", epoch_to_utc_iso(NOW + 100), "instant", now=NOW)
    store.create("deferred", epoch_to_utc_iso(NOW + 100), "deferred", now=NOW)
    result = store.list(delivery_mode="deferred", now=NOW)
    assert result["count"] == 1
    assert "notice" not in result
    failed = store.execute({"action": "update", "schedule_id": "missing"}, now=NOW)
    assert failed["success"] is False and "notice" not in failed


def test_failure_noop_and_delete_last_receive_gap_notice(store):
    assert store.list(now=NOW)["notice"] == NO_INSTANT_NOTICE
    failed = store.execute({"action": "pause"}, now=NOW)
    assert failed["error"]["code"] == "invalid_argument" and failed["notice"] == NO_INSTANT_NOTICE
    result = store.create("deferred", epoch_to_utc_iso(NOW + 100), "deferred", now=NOW)
    sid = result["schedule"]["schedule_id"]
    noop = store.update(sid, content="deferred", now=NOW)
    assert noop["changed"] is False and noop["notice"] == NO_INSTANT_NOTICE
    assert store.delete(sid, now=NOW)["notice"] == NO_INSTANT_NOTICE
    assert store.list(now=NOW)["count"] == 0


def test_unknown_coverage_returns_read_error_and_rolls_back_control(store, monkeypatch):
    def unavailable(*_args, **_kwargs):
        raise sqlite3.OperationalError("coverage read unavailable")

    with monkeypatch.context() as patch:
        patch.setattr("secretary.schedules.instant_coverage_conn", unavailable)
        result = store.create("attention", epoch_to_utc_iso(NOW + 100), "instant", now=NOW)
        assert result["success"] is False
        assert result["error"]["code"] == "temporarily_unavailable"
        assert result["error"]["field"] == "schedule_table"
        assert "notice" not in result
    assert store.list(now=NOW)["count"] == 0


def test_postcommit_lost_return_reports_unknown_not_retry_create(store, monkeypatch):
    real_write = store.db._execute_write

    def lose_return(fn):
        real_write(fn)
        raise OSError("commit return lost")

    monkeypatch.setattr(store.db, "_execute_write", lose_return)
    result = store.create("attention", epoch_to_utc_iso(NOW + 100), "instant", now=NOW)
    assert result["error"]["code"] == "outcome_unknown"
    assert store.list(now=NOW)["count"] == 1


@pytest.mark.parametrize("config,enabled", [
    ({}, True), ({"noting": {"enabled": False}}, True),
    ({"noting": "invalid-noting-only"}, True),
    ({"scheduler": {"enabled": False}, "noting": {"enabled": True}}, False),
    ({"scheduler": {"enabled": "false"}}, False),
    ({"scheduler": None}, False),
])
def test_independent_configuration_gate(tmp_path, monkeypatch, config, enabled):
    monkeypatch.setattr("hermes_cli.config.load_config_readonly", lambda: config)
    db = SimpleNamespace(db_path=tmp_path / "state.db")
    assert default_enablement(db)("any-main") is enabled


def test_configuration_loader_uses_each_owning_home(tmp_path, monkeypatch):
    from hermes_constants import get_hermes_home

    a, b = tmp_path / "a", tmp_path / "b"
    seen = []

    def config():
        home = get_hermes_home()
        seen.append(home)
        return {"scheduler": {"enabled": home == a}}

    monkeypatch.setattr("hermes_cli.config.load_config_readonly", config)
    assert default_enablement(SimpleNamespace(db_path=a / "state.db"))("same-ref") is True
    assert default_enablement(SimpleNamespace(db_path=b / "state.db"))("same-ref") is False
    assert seen == [a, b]


def test_disabled_scanner_preserves_definitions_and_reenable_can_claim(store, monkeypatch):
    sid = store.create("overdue", epoch_to_utc_iso(NOW - 1), "instant", now=NOW)["schedule"]["schedule_id"]
    monkeypatch.setattr("hermes_cli.config.load_config_readonly", lambda: {"scheduler": {"enabled": False}})
    assert scan_and_claim_due(store.db, owner="host", now=NOW) == []
    assert store.list(now=NOW)["count"] == 1
    monkeypatch.setattr("hermes_cli.config.load_config_readonly", lambda: {"noting": {"enabled": False}})
    claims = scan_and_claim_due(store.db, owner="host", now=NOW)
    assert [row["schedule_id"] for row in claims] == [sid]


def test_tool_rejects_auxiliary_agent_and_model_supplied_owner(store, monkeypatch):
    from tools.scheduler_tool import handle_scheduler

    monkeypatch.setattr("hermes_cli.config.load_config_readonly", lambda: {})
    agent = SimpleNamespace(_session_db=store.db, session_id="main", platform="cli",
                            _secretary_conversation_ref=store.conversation_ref)
    denied = handle_scheduler({"action": "list", "conversation_ref": "other"}, agent=agent)
    assert denied["error"]["code"] == "invalid_argument"
    agent._secretary_noting_child = True
    denied = handle_scheduler({"action": "list"}, agent=agent)
    assert denied["error"]["code"] == "scope_denied"
    assert "notice" not in denied


def test_schema_is_copied_and_has_no_model_writable_runtime_fields():
    from tools.scheduler_tool import get_scheduler_schema

    schema = get_scheduler_schema()
    assert schema["parameters"]["required"] == ["action"]
    assert set(schema["parameters"]["properties"]) == {
        "action", "schedule_id", "name", "content", "schedule", "delivery_mode", "state"}
    assert schema["parameters"]["additionalProperties"] is False
    schema["parameters"]["properties"].clear()
    assert get_scheduler_schema()["parameters"]["properties"]
