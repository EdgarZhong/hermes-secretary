"""Native Noting invalidation stays independent of parent transcript recovery."""
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from hermes_state import SessionDB
from hermes_state_history_notifications import notification_path
from secretary.noting_child import register_active_noting_task, unregister_active_noting_task
from secretary.web_events import changed, subscribe, unsubscribe
from tui_gateway import server


@pytest.fixture
def watched(tmp_path, monkeypatch):
    home = tmp_path / "profile"
    home.mkdir()
    (home / "config.yaml").write_text("display: {}\n")
    (home / "cron").mkdir()
    monkeypatch.setattr(server, "_hermes_home", str(home))
    monkeypatch.setattr(server, "_cfg_cache", None)
    for name in ("_change_sigs", "_change_checked_at", "_change_broadcast_at", "_sessions_db_sig_cache",
                 "_sessions_db_scope_cache", "_sessions_probe_scope", "_sessions_broadcast_scope", "_secretary_wake_sigs"):
        monkeypatch.setattr(server, name, {})
    monkeypatch.setattr(server, "_bot_relay_outbox_seen", 0)
    monkeypatch.setattr(server, "_pairing_roots_cache", None)
    monkeypatch.setattr(server, "_served_profile_homes", set())
    events, hints, databases = [], [], []
    monkeypatch.setattr(server, "_broadcast_global_event", lambda event, payload=None: events.append((event, payload)))
    subscribe("noting-connection-regression", lambda owner, conversation, reason, **metadata:
              hints.append((str(owner), conversation, reason, metadata)), include_metadata=True)

    def database(root=home):
        root.mkdir(exist_ok=True, parents=True)
        db = SessionDB(root / "state.db")
        db.create_session("parent", source="test")
        databases.append(db)
        return db

    db = database()
    try:
        yield SimpleNamespace(home=home, db=db, events=events, hints=hints, database=database)
    finally:
        unsubscribe("noting-connection-regression")
        for item in databases:
            item.close()


def session_events(fixture):
    return [payload for name, payload in fixture.events if name == "sessions.changed"]


def scoped(home, *identities):
    with SessionDB(home / "state.db", read_only=True) as db:
        return {"scope_complete": True, "changed_sessions": [
            {"profile_home": str(home.resolve()), "session_id": identity,
             "conversation_ref": db.resolve_conversation_ref(identity)} for identity in sorted(identities)]}


@pytest.mark.parametrize("trigger", ["manual", "force"])
def test_task_lifecycle_is_local_and_cross_process_secretary_only(watched, trigger):
    f = watched
    ref = f.db.resolve_conversation_ref("parent")
    child = SimpleNamespace(_session_db=f.db, _secretary_parent_conversation_ref=ref, trigger_type=trigger)
    server._broadcast_watched_changes(now=0.0)
    before = server._session_db_content_sig(f.home / "state.db")
    try:
        register_active_noting_task("arbitrary-child-identity", child)
        server._broadcast_watched_changes(now=10.0)
        assert [(hint[1], hint[2]) for hint in f.hints] == [(ref, "task_started"), (None, "global_changed")]
        f.hints.clear()
        for tick, reason in enumerate(("task_started", "notebook_changed", "task_finished"), 2):
            changed(f.db, ref, reason)
            server._broadcast_watched_changes(now=tick * 10.0)
            assert f.hints[-1][1:3] == (None, "global_changed")
        unregister_active_noting_task("arbitrary-child-identity", child)
        server._broadcast_watched_changes(now=50.0)
        assert session_events(f) == []
        assert server._session_db_content_sig(f.home / "state.db") == before
        assert not notification_path(f.db.db_path).exists()
        assert all(metadata.get("completion_snapshot_id") is None for _, _, _, metadata in f.hints)
    finally:
        unregister_active_noting_task("arbitrary-child-identity", child)


def test_child_create_append_end_and_delete_keep_native_scoped_event(watched):
    f = watched
    server._broadcast_watched_changes(now=0.0)
    operations = [lambda: f.db.create_session("opaque-child", source="noting", parent_session_id="parent"),
                  lambda: f.db.append_message("opaque-child", "user", "task body", message_uid="child-input"),
                  lambda: f.db.end_session("opaque-child", "completed"), lambda: f.db.delete_session("opaque-child")]
    previous = None
    for tick, operation in enumerate(operations, 1):
        operation()
        server._broadcast_watched_changes(now=tick * 10.0)
        expected = previous if tick == 4 else scoped(f.home, "opaque-child")
        assert session_events(f)[-1] == expected
        previous = expected
    assert len(session_events(f)) == 4


def test_floor_tracks_all_changes_since_last_actual_broadcast(watched):
    f = watched
    server._broadcast_watched_changes(now=0.0)
    f.db.create_session("child", source="noting", parent_session_id="parent")
    server._broadcast_watched_changes(now=10.0)
    f.events.clear()
    f.db.append_message("child", "assistant", "working", message_uid="child-work")
    server._broadcast_watched_changes(now=10.6)
    f.db.append_message("parent", "assistant", "actual Main output", message_uid="parent-output")
    server._broadcast_watched_changes(now=11.2)
    f.db.create_session("second-child", source="test")
    server._broadcast_watched_changes(now=11.8)
    assert session_events(f) == []
    server._broadcast_watched_changes(now=12.4)
    assert session_events(f) == [scoped(f.home, "child", "parent", "second-child")]


def test_cross_process_secretary_token_keeps_profile_and_no_completion_hint(watched, monkeypatch):
    f = watched
    other_home = f.home / "profiles" / "other"
    other = f.database(other_home)
    monkeypatch.setattr(server, "_served_profile_homes", {other_home})
    server._broadcast_watched_changes(now=0.0)
    environment = {**os.environ, "PYTHONPATH": str(Path(__file__).resolve().parents[2])}
    subprocess.run([sys.executable, "-c", "from types import SimpleNamespace; import sys; "
                    "from hermes_state_history_notifications import notify_secretary_changed; "
                    "notify_secretary_changed(SimpleNamespace(db_path=sys.argv[1]))", str(other.db_path)],
                   cwd=f.home.parent, env=environment, check=True, capture_output=True, timeout=10)
    server._broadcast_watched_changes(now=10.0)
    assert f.hints == [(str(other_home.resolve()), None, "global_changed", {"completion_snapshot_id": None})]
    assert session_events(f) == []


def test_multiple_profiles_same_session_id_remain_distinct(watched, monkeypatch):
    f = watched
    other_home = f.home / "profiles" / "other"
    other = f.database(other_home)
    monkeypatch.setattr(server, "_served_profile_homes", {other_home})
    server._broadcast_watched_changes(now=0.0)
    f.db.append_message("parent", "user", "first owner", message_uid="first")
    other.append_message("parent", "user", "other owner", message_uid="other")
    server._broadcast_watched_changes(now=10.0)
    assert session_events(f) == [{"scope_complete": True, "changed_sessions": [
        *scoped(f.home, "parent")["changed_sessions"], *scoped(other_home, "parent")["changed_sessions"]]}]


def test_true_parent_cas_rewrite_keeps_broad_history_invalidation(watched):
    f = watched
    f.db.append_messages_batch("parent", [{"role": "assistant", "content": "old", "message_uid": "stable", "timestamp": 1000., "token_count": 42}])
    server._broadcast_watched_changes(now=0.0)
    messages = f.db.get_messages_as_conversation("parent", repair_alternation=True, include_row_ids=False)
    messages[0]["content"] = "rewritten at the same UID and row"
    from agent.context_compressor import _DB_PERSISTED_MARKER
    messages[0].pop(_DB_PERSISTED_MARKER, None)
    assert f.db.append_messages_batch("parent", messages) == 0
    server._broadcast_watched_changes(now=10.0)
    assert session_events(f) == [{}]
    assert f.db.get_messages_as_conversation("parent")[0]["content"] == messages[0]["content"]
    f.events.clear()
    assert f.db.append_messages_batch("parent", f.db.get_messages_as_conversation("parent", repair_alternation=True, include_row_ids=False)) == 0
    server._broadcast_watched_changes(now=20.0)
    assert session_events(f) == []


def test_failed_profile_read_prevents_complete_scope_claim(watched, monkeypatch):
    f = watched
    other_home = f.home / "profiles" / "other"
    other = f.database(other_home)
    monkeypatch.setattr(server, "_served_profile_homes", {other_home})
    server._broadcast_watched_changes(now=0.0)
    other.close()
    (other_home / "state.db").write_text("unreadable sqlite")
    f.db.append_message("parent", "assistant", "new Main body", message_uid="changed")
    server._broadcast_watched_changes(now=10.0)
    assert session_events(f) == [{}]


def test_failed_broadcast_does_not_advance_scope_baseline(watched, monkeypatch):
    f = watched
    server._broadcast_watched_changes(now=0.0)
    f.db.create_session("child", source="noting")
    original = server._broadcast_global_event

    def unavailable(name, payload=None):
        if name == "sessions.changed":
            raise RuntimeError("transport unavailable")
        return original(name, payload)

    monkeypatch.setattr(server, "_broadcast_global_event", unavailable)
    server._broadcast_watched_changes(now=10.0)
    f.db.append_message("parent", "assistant", "changed after failed broadcast", message_uid="later")
    monkeypatch.setattr(server, "_broadcast_global_event", original)
    server._broadcast_watched_changes(now=11.0)
    assert session_events(f) == [scoped(f.home, "child", "parent")]


pytest_plugins = ["tests.secretary.test_noting_child", "tests.secretary.test_joint_noting_u20", "tests.secretary.test_noting_recovery"]


def install_parent_gateway(parent, db, monkeypatch):
    """Real activate handler and runtime snapshot; only the peer and owner lookup are controlled."""
    import threading
    from contextlib import contextmanager
    from tui_gateway import event_replay
    from tests.tui_gateway.test_recovery_view import Peer
    home = Path(db.db_path).parent
    config = home / "config.yaml"
    initial_config = config.read_text() if config.exists() else "noting:\n  enabled: true\n  idle:\n    enabled: false\n"
    config.write_text(initial_config + f"\nterminal:\n  cwd: {home}\n")
    monkeypatch.chdir(home)
    session = {"_sid": "runtime", "agent": parent, "session_key": parent.session_id,
               "profile_home": str(Path(db.db_path).parent), "history": list(parent._session_messages),
               "history_lock": threading.RLock(), "created_at": 1., "running": False, "transport": Peer()}
    monkeypatch.setattr(server, "_sessions", {"runtime": session})
    monkeypatch.setattr(server, "_fallback_session_info", lambda _session: {"model": "controlled"})
    monkeypatch.setattr(server, "_session_info", lambda agent, owner: {"running": bool(owner.get("running"))})
    monkeypatch.setattr(server, "profile_name_for_home", lambda home: "default")
    monkeypatch.setattr(server, "_launch_home", lambda: str(Path(db.db_path).parent))
    monkeypatch.setattr(server, "_current_profile_name", lambda: "default")

    @contextmanager
    def owning(_session):
        yield db

    monkeypatch.setattr(server, "_session_db", owning)
    event_replay.reset_replay_state()

    def view():
        from hermes_state_recovery_view import project_view, read_view, selector
        
        projected = project_view(read_view(db, parent.session_id, "default", [selector()]))
        request = {"version": 1, "profile": "default", "stored_id": parent.session_id,
                   "windows": [{"selector": item["selector"], "receipt": item["coverage"]}
                               for item in projected["windows"]], "details": []}
        response = server._methods["session.activate"]("probe", {"session_id": "runtime", "omit_messages": True,
                                                               "recovery_view": request})
        assert "error" not in response, response
        return response["result"]["recovery_view"]

    return session, view


def capture_parent_broadcasts(db, monkeypatch):
    monkeypatch.setattr(server, "_hermes_home", str(Path(db.db_path).parent))
    monkeypatch.setattr(server, "_served_profile_homes", set())
    for name in ("_change_sigs", "_change_checked_at", "_change_broadcast_at", "_sessions_db_sig_cache",
                 "_sessions_db_scope_cache", "_sessions_probe_scope", "_sessions_broadcast_scope", "_secretary_wake_sigs"):
        monkeypatch.setattr(server, name, {})
    broadcasts = []
    broadcast = server._broadcast_global_event

    def observe_broadcast(name, payload=None):
        broadcasts.append((name, payload))
        return broadcast(name, payload)

    monkeypatch.setattr(server, "_broadcast_global_event", observe_broadcast)
    server._broadcast_watched_changes(now=0.0)
    return broadcasts


def test_actual_manual_noting_child_has_independent_scope_and_parent_stays_recoverable(runtime, monkeypatch):
    from secretary import noting_runtime
    import traceback
    import hermes_state_history_notifications as notifications
    from tests.secretary.test_joint_noting_u20 import finish_provider
    parent, db, client, workers = runtime
    finish_provider(client)
    _session, view = install_parent_gateway(parent, db, monkeypatch)
    broadcasts = capture_parent_broadcasts(db, monkeypatch)
    history_wakes = []
    history_proofs = []
    history_changed = notifications.notify_history_changed

    def observe_history(owner, session_id=None):
        identity = session_id
        registered = owner._read_one("SELECT child_session_id,status FROM secretary_noting_task_children WHERE child_session_id=?", (identity,))
        history_proofs.append({"session_id": identity, "registered": dict(registered) if registered else None})
        history_wakes.append([f"{Path(frame.filename).name}:{frame.name}:{frame.lineno}"
                              for frame in traceback.extract_stack(limit=10)])
        return history_changed(owner, session_id=session_id)

    monkeypatch.setattr(notifications, "notify_history_changed", observe_history)
    decision = noting_runtime.prepare_joint_noting(parent, trigger="manual")
    assert decision.action == "admit"
    for worker in workers:
        worker.join(10)
        assert not worker.is_alive()
    child_id = db.noting_child(decision.admission.admission_id)["child_session_id"]
    assert db.resolve_conversation_ref(child_id) != parent._secretary_conversation_ref
    server._broadcast_watched_changes(now=10.0)
    changes = [payload for name, payload in broadcasts if name == "sessions.changed"]
    diagnostic = "\n".join(" -> ".join(stack) for stack in history_wakes)
    assert history_proofs[0] == {"session_id": child_id, "registered": {"child_session_id": child_id, "status": "running"}}
    assert changes == [scoped(Path(db.db_path).parent, child_id)], f"changes={changes!r}\nproofs={history_proofs!r}\nhistory_wakes:\n{diagnostic}"
    assert view()["complete"]


def test_actual_force_dispatch_parent_fm_and_note_compact_recover(runtime, monkeypatch):
    from tui_gateway import turn_terminal
    from secretary import framework_messages
    from secretary.noting_notes import check_note_delivery
    from tests.secretary.test_joint_noting_native_turn_u20 import sdk_responder
    from tests.agent.test_context_compaction_request import _summary
    parent, db, client, workers = runtime
    parent.client = client
    parent._disable_streaming = True
    parent.compression_enabled = False
    client.chat.completions.create.side_effect = sdk_responder
    monkeypatch.setattr("secretary.noting_timers.arm_idle_timer", lambda *args: None)
    session, view = install_parent_gateway(parent, db, monkeypatch)
    broadcasts = capture_parent_broadcasts(db, monkeypatch)
    assert view()["complete"]
    session["running"] = True
    server._start_inflight_turn(session, "first native request")
    parent._on_turn_user_persisted = turn_terminal.source_observer(
        "runtime", session, parent, turn_terminal.token(session), None)
    server._emit("message.start", "runtime")
    dispatch_views = []
    publish = framework_messages.publish_framework_message

    def observe_dispatch(*args, **kwargs):
        result = publish(*args, **kwargs)
        if (kwargs.get("display_metadata") or {}).get("noting_force_dispatch"):
            dispatch_views.append(view())
        return result

    monkeypatch.setattr(framework_messages, "publish_framework_message", observe_dispatch)
    before_ids = {row["id"] for row in db.get_messages(parent.session_id)}
    result = parent.run_conversation("first native request", conversation_history=list(parent._session_messages))
    assert result["completed"]
    for worker in workers:
        worker.join(10)
        assert not worker.is_alive()
    rows = [row for row in db.get_messages(parent.session_id) if row["id"] not in before_ids]
    force = [row for row in rows if (row.get("display_metadata") or {}).get("noting_force_dispatch")]
    assert len(force) == len(dispatch_views) == 1
    assert dispatch_views[0]["complete"], dispatch_views[0]
    broadcasts.clear()
    server._broadcast_watched_changes(now=10.0)
    changes = [payload for name, payload in broadcasts if name == "sessions.changed"]
    assert len(changes) == 1
    # Native transcript reconciliation can also move the opaque history marker;
    # that broad invalidation is correct and must never become child-only.
    assert not changes[0].get("scope_complete") or {
        "profile_home": str(Path(db.db_path).parent.resolve()), "session_id": parent.session_id,
        "conversation_ref": parent._secretary_conversation_ref} in changes[0]["changed_sessions"]
    receipt = {"complete": True, "row_ids": [row["id"] for row in rows], "source_messages": [
        {"row_id": row["id"], "message_uid": row["message_uid"], "role": row["role"],
         "has_content": bool(row["content"]), "has_reasoning": bool(row.get("reasoning"))} for row in rows]}
    server._emit("message.complete", "runtime", {"text": result["final_response"], "persisted_turn": receipt})
    session["running"] = False
    server._clear_inflight_turn(session)
    session["history"] = list(parent._session_messages)
    assert view()["complete"]
    parent.compression_enabled = True
    compact_views = []

    def summarise(messages, **kwargs):
        compact_views.append(view())
        return _summary(messages, **kwargs)

    monkeypatch.setattr(parent.context_compressor, "compress", summarise)
    with server._manual_compress_turn("runtime", session):
        messages, _ = parent._compress_context(parent._session_messages, None, approx_tokens=50_000, force=True)
        parent._session_messages = messages
        session["history"] = list(messages)
    assert compact_views and all(item["complete"] for item in compact_views), compact_views
    check_note_delivery(parent)
    assert any((row.get("display_metadata") or {}).get("noting_run_output") for row in db.get_messages(parent.session_id))
    broadcasts.clear()
    server._broadcast_watched_changes(now=20.0)
    assert any(name == "sessions.changed" for name, _ in broadcasts)
    assert view()["complete"]


def registered_child(db, identity):
    anchor = "anchor-" + identity
    db.append_message("parent", "assistant", "source evidence", message_uid=anchor)
    ref = db.resolve_conversation_ref("parent")
    admission = db.noting_admit(ref, anchor, kind="manual")
    db.create_session(identity, source="subagent", parent_session_id="parent", model_config={"_delegate_from": "parent"})
    db.noting_child_register(admission, child_session_id=identity, profile="default")
    return admission


def test_child_history_tokens_merge_all_proven_children_without_body_or_counter_changes(watched):
    from hermes_state_history_notifications import notify_history_changed, noting_history_notification_path
    f = watched
    registered_child(f.db, "first-opaque-child")
    registered_child(f.db, "second-opaque-child")
    server._broadcast_watched_changes(now=0.0)
    before = server._session_db_content_sig(f.home / "state.db")
    notify_history_changed(f.db, session_id="first-opaque-child")
    assert noting_history_notification_path(f.db.db_path).exists()
    assert not notification_path(f.db.db_path).exists()
    server._broadcast_watched_changes(now=10.0)
    assert session_events(f) == [scoped(f.home, "first-opaque-child", "second-opaque-child")]
    f.events.clear()
    notify_history_changed(f.db, session_id="second-opaque-child")
    server._broadcast_watched_changes(now=10.6)
    notify_history_changed(f.db, session_id="first-opaque-child")
    server._broadcast_watched_changes(now=11.2)
    assert session_events(f) == []
    server._broadcast_watched_changes(now=12.4)
    assert session_events(f) == [scoped(f.home, "first-opaque-child", "second-opaque-child")]
    assert server._session_db_content_sig(f.home / "state.db") == before


@pytest.mark.parametrize("loss", ["cap", "ref"])
def test_unprovable_child_history_scope_falls_back_global(watched, monkeypatch, loss):
    from hermes_state_history_notifications import notify_history_changed
    import hermes_state_noting_notifications as notifications
    f = watched
    registered_child(f.db, "first-child")
    registered_child(f.db, "second-child")
    server._broadcast_watched_changes(now=0.0)
    if loss == "cap":
        monkeypatch.setattr(notifications, "NOTING_HISTORY_SCOPE_LIMIT", 1)
    else:
        f.db._execute_write(lambda conn: conn.execute("DELETE FROM secretary_session_bindings WHERE session_id=?", ("first-child",)))
    notify_history_changed(f.db, session_id="first-child")
    server._broadcast_watched_changes(now=10.0)
    assert session_events(f) == [{}]


def test_main_lease_release_and_same_round_child_wake_keep_broad_history(watched):
    from hermes_state_history_notifications import notify_history_changed
    f = watched
    registered_child(f.db, "real-child")
    assert f.db.try_acquire_session_turn_lease("parent", "opaque-main-holder")
    server._broadcast_watched_changes(now=0.0)
    notify_history_changed(f.db, session_id="real-child")
    f.db.release_session_turn_lease("parent", "opaque-main-holder")
    server._broadcast_watched_changes(now=10.0)
    assert notification_path(f.db.db_path).exists()
    assert session_events(f) == [{}]


@pytest.mark.parametrize("identity", [None, "unregistered-session"])
def test_default_and_unproven_history_owner_preserve_original_global_marker(watched, identity):
    from hermes_state_history_notifications import notify_history_changed, noting_history_notification_path
    f = watched
    server._broadcast_watched_changes(now=0.0)
    notify_history_changed(f.db, session_id=identity)
    server._broadcast_watched_changes(now=10.0)
    assert session_events(f) == [{}]
    assert not noting_history_notification_path(f.db.db_path).exists()


def test_recovery_audit_must_match_actual_original_noting_registry(watched):
    from hermes_state_history_notifications import notify_history_changed, noting_history_notification_path
    f = watched
    admission = registered_child(f.db, "original-child")
    ref = f.db.resolve_conversation_ref("parent")
    f.db.create_session("real-recovery", source="subagent", parent_session_id="parent", model_config={
        "_delegate_from": "parent", "_noting_recovery": {"admission_id": admission, "failed_child_session_id": "original-child",
        "conversation_ref": ref, "status": "running"}})
    server._broadcast_watched_changes(now=0.0)
    notify_history_changed(f.db, session_id="real-recovery")
    server._broadcast_watched_changes(now=10.0)
    assert noting_history_notification_path(f.db.db_path).exists()
    assert session_events(f) == [scoped(f.home, "original-child", "real-recovery")]
    f.events.clear()
    f.db.create_session("unproven-recovery", source="subagent", model_config={"_noting_recovery": {
        "admission_id": admission, "failed_child_session_id": "not-a-known-child", "conversation_ref": ref, "status": "running"}})
    notify_history_changed(f.db, session_id="unproven-recovery")
    server._broadcast_watched_changes(now=20.0)
    assert session_events(f) == [{}]


@pytest.mark.parametrize("outcome", ["completed", "failed_build", "failed_start"])
def test_actual_recovery_reservation_release_names_real_notification_session(native_parent, database, monkeypatch, outcome):
    from tests.secretary.test_noting_recovery import failed_task, factory, wait_recovery, ref, tool_response, response
    from secretary.noting_recovery import start_recovery
    parent, client = native_parent
    failed = failed_task(native_parent, database)
    _session, _view = install_parent_gateway(parent, database, monkeypatch)
    broadcasts = capture_parent_broadcasts(database, monkeypatch)
    releases = []
    release = SessionDB.release_session_turn_lease

    def observed(owner, session_id, holder, *, notification_session_id=None):
        if Path(owner.db_path).resolve() == Path(database.db_path).resolve():
            releases.append((session_id, notification_session_id))
        return release(owner, session_id, holder, notification_session_id=notification_session_id)

    monkeypatch.setattr(SessionDB, "release_session_turn_lease", observed)
    builder = factory(parent)
    if outcome == "failed_build":
        def builder(_database, _recovered):
            raise RuntimeError("controlled recovery construction failure")
    if outcome == "failed_start":
        def no_start():
            raise RuntimeError("controlled recovery thread start failure")
        monkeypatch.setattr("agent.memory_provider.spawn_context_thread", lambda *args, **kwargs: SimpleNamespace(start=no_start))
        with pytest.raises(RuntimeError, match="thread start failure"):
            start_recovery(database, ref(database), failed.child_session_id, "ownership", parent_factory=builder)
        operation = database._read_one("SELECT id FROM sessions WHERE json_extract(model_config,'$._noting_recovery.request_id')='ownership'")[0]
    else:
        client.chat.completions.create.side_effect = [tool_response("finish_noting", {"reason": "Resumed saved work"}), response("Done")]
        ack = start_recovery(database, ref(database), failed.child_session_id, "ownership", parent_factory=builder)
        state = wait_recovery(database, failed, request="ownership")
        assert state["status"] == ("completed" if outcome == "completed" else "failed")
        operation = ack["operation_id"]
    assert ("recovery:" + operation, operation) in releases
    assert database._read_one("SELECT 1 FROM session_turn_leases WHERE conversation_id=?", ("recovery:" + operation,)) is None
    server._broadcast_watched_changes(now=10.0)
    changes = [payload for name, payload in broadcasts if name == "sessions.changed"]
    assert changes
    assert _view()["complete"]
    if not any(identity == parent.session_id for identity, _ in releases):
        assert all(payload.get("scope_complete") for payload in changes), changes
        assert all(all(row["session_id"] != parent.session_id for row in payload["changed_sessions"]) for payload in changes)
