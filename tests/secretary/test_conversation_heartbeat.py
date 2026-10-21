"""Stable Conversation owner and atomic Heartbeat mutation/claim/refund contracts."""

from concurrent.futures import ThreadPoolExecutor
import threading
import time

import pytest

from hermes_cli.heartbeat import HeartbeatManager, HeartbeatState, load_heartbeat, save_heartbeat, migrate_heartbeat_to_session
from hermes_state import SessionDB
from secretary.heartbeat_route import heartbeat_route


@pytest.fixture
def owned(tmp_path):
    homes = [tmp_path / "a", tmp_path / "b"]
    dbs = []
    for home in homes:
        home.mkdir()
        (home / "config.yaml").write_text("noting:\n  enabled: true\n")
        db = SessionDB(home / "state.db")
        for sid in ("first", "second"):
            db.create_session(sid, "tui")
        dbs.append(db)
    yield dbs
    for db in dbs:
        db.close()


def due(db, sid="first", prompt=""):
    save_heartbeat(sid, HeartbeatState(prompt, 60, created_at=1), db=db)
    return HeartbeatManager(sid, db=db)


def test_two_conversations_and_profiles_are_independent(owned):
    a, b = owned
    one, two, other = due(a, "first", "A"), due(a, "second", "B"), due(b, "first", "C")
    one.pause()
    assert not one.due_prompt(now=120)
    assert two.due_prompt(now=120) and other.due_prompt(now=120)
    one.resume()
    assert one.state.status == "active" and not one.state.is_due(now=time.time())
    one.set("replacement", 120)
    assert one.state.prompt == "replacement"
    assert two.state.prompt == "B" and other.state.prompt == "C"
    one.clear()
    assert load_heartbeat("first", db=a) is None
    assert load_heartbeat("second", db=a).prompt == "B"
    assert load_heartbeat("first", db=b).prompt == "C"
    assert not a.list_meta_prefix("heartbeat:")


def test_compression_sessions_share_definition_but_fork_does_not(owned):
    db = owned[0]
    due(db)
    db.publish_compression_child(
        parent_session_id="first", child_session_id="tip", source="tui", require_compression_lease=False,
        model="offline", model_config={}, system_prompt="frozen", messages=[{"role": "user", "content": "summary"}])
    assert db.resolve_conversation_ref("tip") == db.resolve_conversation_ref("first")
    assert load_heartbeat("tip", db=db) == load_heartbeat("first", db=db)
    from secretary.noting_scope import owning_db_scope
    with owning_db_scope(db):
        assert migrate_heartbeat_to_session("first", "tip")
    HeartbeatManager("tip", db=db).pause()
    assert HeartbeatManager("first", db=db).state.status == "paused"
    HeartbeatManager("first", db=db).set("new", 60)
    assert HeartbeatManager("tip", db=db).state.prompt == "new"
    db.create_session("fork", "tui", parent_session_id="tip", model_config={"_branched_from": "tip"})
    assert load_heartbeat("fork", db=db) is None
    assert heartbeat_route(db, db.resolve_conversation_ref("first"))["id"] == "tip"
    assert db._read_one("SELECT COUNT(*) FROM secretary_heartbeats")[0] == 1
    assert not HeartbeatManager("first", db=db).due_prompt(now=time.time() + 3600)
    assert HeartbeatManager("tip", db=db).due_prompt(now=time.time() + 3600)


def test_concurrent_managers_on_separate_connections_claim_once(owned):
    db = owned[0]
    due(db)
    other = SessionDB(db.db_path)
    barrier = threading.Barrier(2)
    def fire(handle):
        manager = HeartbeatManager("first", db=handle)
        barrier.wait(timeout=5)
        return manager.due_prompt(now=120)
    try:
        with ThreadPoolExecutor(2) as pool:
            results = list(pool.map(fire, (db, other)))
        assert sum(value is not None for value in results) == 1
        assert load_heartbeat("first", db=db).fire_count == 1
    finally:
        other.close()


@pytest.mark.parametrize("change", ["pause", "clear", "replace", "resume"])
def test_old_claim_cannot_refund_or_execute_after_new_operation(owned, change):
    db = owned[0]
    worker = due(db)
    assert worker.due_prompt(now=120) and worker.fire_is_current()
    controller = HeartbeatManager("first", db=db)
    if change == "replace":
        controller.set("New definition", 120)
    else:
        getattr(controller, change)()
    before = load_heartbeat("first", db=db)
    assert not worker.fire_is_current() and not worker.abandon_fire()
    assert load_heartbeat("first", db=db) == before


def test_refund_is_exactly_once_and_does_not_override_later_claim(owned):
    db = owned[0]
    worker = due(db)
    assert worker.due_prompt(now=120)
    assert worker.abandon_fire() and not worker.abandon_fire()
    assert worker.state.fire_count == 0
    assert worker.due_prompt(now=120)
    later = HeartbeatManager("first", db=db)
    assert later.due_prompt(now=180)
    assert not worker.abandon_fire()
    assert later.state.fire_count == 2


def test_restart_keeps_active_but_does_not_resurrect_pause_or_clear(owned):
    db = owned[0]
    due(db, "first", "A").pause()
    due(db, "second", "B").clear()
    db.create_session("third", "tui")
    due(db, "third", "C")
    db.close()
    reopened = SessionDB(db.db_path)
    try:
        assert HeartbeatManager("first", db=reopened).state.status == "paused"
        assert not HeartbeatManager("first", db=reopened).due_prompt(now=120)
        assert load_heartbeat("second", db=reopened) is None
        assert HeartbeatManager("third", db=reopened).due_prompt(now=120)
    finally:
        reopened.close()


def test_native_definitions_are_preserved_without_automatic_migration(owned):
    db = owned[0]
    native = HeartbeatState("legacy", 60, created_at=1)
    db.set_meta("heartbeat:first", native.to_json())
    assert load_heartbeat("first", db=db) is None
    HeartbeatManager("first", db=db).set("", 120)
    assert db.get_meta("heartbeat:first") == native.to_json()
    (db.db_path.parent / "config.yaml").write_text("noting:\n  enabled: false\n")
    assert load_heartbeat("first", db=db).prompt == "legacy"
    assert HeartbeatManager("first", db=db).due_prompt(now=120).startswith("[Heartbeat")
    with pytest.raises(ValueError, match="empty"):
        HeartbeatManager("first", db=db).set("", 60)


def test_target_profile_timezone_is_used_when_caller_scope_is_another_home(owned):
    db = owned[1]
    path = db.db_path.parent / "config.yaml"
    path.write_text("noting:\n  enabled: true\ntimezone: Asia/Shanghai\n")
    prompt = due(db).due_prompt(now=120)
    assert "<timestamp>1970-01-01T08:02:00+08:00</timestamp>" in prompt


def test_branch_compression_with_inherited_marker_keeps_its_own_owner(owned):
    db = owned[0]
    due(db, prompt="parent")
    db.create_session("fork", "tui", parent_session_id="first", model_config={"_branched_from": "first"})
    assert load_heartbeat("fork", db=db) is None
    due(db, "fork", "fork only")
    db.publish_compression_child(
        parent_session_id="fork", child_session_id="fork-tip", source="tui", require_compression_lease=False,
        model="offline", model_config={"_branched_from": "first"}, system_prompt="frozen",
        messages=[{"role": "user", "content": "summary"}])
    assert load_heartbeat("fork-tip", db=db).prompt == "fork only"
    assert heartbeat_route(db, db.resolve_conversation_ref("fork"))["id"] == "fork-tip"
    assert load_heartbeat("first", db=db).prompt == "parent"


def test_unavailable_conversation_store_does_not_claim_a_native_definition(monkeypatch):
    monkeypatch.setattr("hermes_cli.heartbeat._get_session_db", lambda: None)
    monkeypatch.setattr("hermes_cli.heartbeat.ui_heartbeat_enabled", lambda: True)
    manager = HeartbeatManager("missing-store")
    with pytest.raises(ValueError, match="storage unavailable"):
        manager.set("Valid extra prompt", 60)
    assert manager.state is None
