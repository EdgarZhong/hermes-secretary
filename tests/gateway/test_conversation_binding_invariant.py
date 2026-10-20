"""An explicit Conversation binding is immutable outside its binding control owner."""
import asyncio
import json
import queue
import threading
from datetime import timedelta
from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest

from gateway.control_conversation_binding import ConversationBindingControl
from gateway.conversation_binding import BINDING_KEY, bind_conversation
from gateway.run import GatewayRunner
from gateway.run_shutdown import GatewayShutdownMixin
from gateway.run_turn import GatewayTurnMixin
from gateway.session import AsyncSessionStore, SessionStore
from hermes_state import AsyncSessionDB
from tests.gateway.test_conversation_binding import bound_store as bound_store
from tools import async_delegation as delegation


def runner_for(store, db):
    runner = object.__new__(GatewayRunner)
    runner.session_store = store
    runner._async_session_store = AsyncSessionStore(store)
    runner._session_db = AsyncSessionDB(db)
    runner._running_agents = {}
    runner._evict_cached_agent = Mock()
    runner._clear_conversation_scope = Mock()
    return runner


def control_call(runner, key, action, **params):
    return ConversationBindingControl(runner).execute({
        "profile": key.split(":")[1], "action": action, **params,
    })


def assert_binding(store, db, key, sid, ref):
    entry = store.lookup_by_session_key(key)
    assert entry.session_id == sid
    assert entry.metadata[BINDING_KEY]["conversation_ref"] == ref
    saved = json.loads(db.load_gateway_routing_entries(scope=store._routing_scope())[key])
    assert saved["session_id"] == sid
    assert saved["metadata"][BINDING_KEY]["conversation_ref"] == ref
    assert db.get_session(sid)["end_reason"] is None
    mirror = json.loads((store.sessions_dir / "sessions.json").read_text())
    assert mirror[key]["session_id"] == sid
    assert mirror[key]["metadata"][BINDING_KEY]["conversation_ref"] == ref


@pytest.mark.parametrize("late_end", [None, "idle_timeout", "agent_close"])
def test_real_dispatch_a_then_explicit_b_never_switches_or_injects(bound_store, monkeypatch, late_end):
    store, db, source, key = bound_store
    runner = runner_for(store, db)
    ref_a = db.resolve_conversation_ref("imported")
    db.create_session("chosen-b", "desktop")
    db.append_message("imported", "user", "A history")
    db.append_message("chosen-b", "user", "B history")
    ref_b = db.resolve_conversation_ref("chosen-b")
    assert control_call(runner, key, "bind", conversation_ref=ref_a)["ok"]
    release = threading.Event()
    started = threading.Event()
    completions = queue.Queue()
    import tools.process_registry as registry
    monkeypatch.setattr(registry.process_registry, "completion_queue", completions)
    delegation._reset_for_tests()

    def worker():
        started.set()
        assert release.wait(5)
        return {"summary": "A late result", "api_calls": 1}

    handle = delegation.dispatch_async_delegation(
        goal="A work", context=None, toolsets=None, role="general", model=None,
        session_key=key, parent_session_id="imported", runner=worker,
    )
    try:
        assert handle["status"] == "dispatched" and started.wait(3)
        assert control_call(runner, key, "bind", conversation_ref=ref_b)["ok"]
        if late_end:
            db.end_session("imported", late_end)
        before_a, before_b = db.get_messages("imported"), db.get_messages("chosen-b")
        release.set()
        event = completions.get(timeout=5)
        # The public delivery preflight refuses before adapter admission and settles only delivery.
        claim = asyncio.run(runner._preflight_completion_delivery(event))
        assert not claim.proceed
        assert asyncio.run(runner._resolve_async_delegation_session(
            store.lookup_by_session_key(key), "imported")) is None
        row = delegation.get_durable_delegation(handle["delegation_id"])
        assert row["state"] == "completed" and row["delivery_state"] == "dropped"
        assert "A late result" in json.dumps(row)
        assert db.get_messages("imported") == before_a
        assert db.get_messages("chosen-b") == before_b
        assert db.get_session("imported")["end_reason"] == late_end
        assert_binding(store, db, key, "chosen-b", ref_b)
        assert store.get_or_create_session(source).session_id == "chosen-b"
    finally:
        release.set()
        delegation._reset_for_tests()


@pytest.mark.parametrize("phase", ["parent_live", "parent_idle", "compression_parent", "compression_tip"])
def test_binding_change_during_lookup_wins_over_stale_entry(bound_store, phase):
    store, db, _source, key = bound_store
    entry = bind_conversation(store, key, "imported")
    if phase == "parent_idle":
        db.end_session("imported", "idle_timeout")
    if phase.startswith("compression"):
        db.end_session("imported", "compression")
        db.create_session("tip", "pi-import", parent_session_id="imported")
    stale = replace(entry, metadata=dict(entry.metadata))
    if phase == "compression_tip":
        stale.session_id = "tip"
    db.create_session("chosen-b", "desktop")
    ref_b = db.resolve_conversation_ref("chosen-b")
    runner = runner_for(store, db)

    async def race():
        entered, release = asyncio.Event(), asyncio.Event()

        async def lookup(sid):
            if phase.startswith("parent"):
                entered.set()
                await release.wait()
            return db.get_session(sid)

        async def compression_tip(sid):
            entered.set()
            await release.wait()
            return db.get_compression_tip(sid)

        runner._session_db = SimpleNamespace(get_session=lookup, get_compression_tip=compression_tip)
        pending = asyncio.create_task(runner._resolve_async_delegation_session(stale, "imported"))
        await asyncio.wait_for(entered.wait(), 3)
        assert control_call(runner, key, "bind", conversation_ref=ref_b)["ok"]
        release.set()
        assert await asyncio.wait_for(pending, 3) is None

    asyncio.run(race())
    assert_binding(store, db, key, "chosen-b", ref_b)


@pytest.mark.parametrize("path", ["switch", "advance"])
def test_bound_route_accepts_only_same_conversation_compression(bound_store, path):
    store, db, _source, key = bound_store
    entry = bind_conversation(store, key, "imported")
    entry.resume_pending = True
    entry.metadata["retained"] = "owner-state"
    ref = db.resolve_conversation_ref("imported")
    db.create_session("branch", "desktop", parent_session_id="imported",
                      model_config={"_branched_from": "imported"})
    assert db.resolve_conversation_ref("branch") != ref
    move = (lambda sid: store.switch_session(key, sid)) if path == "switch" else (
        lambda sid: store.advance_compression_session(key, "imported", sid))
    assert move("branch") is None
    assert_binding(store, db, key, "imported", ref)
    db.end_session("imported", "compression")
    db.create_session("tip", "pi-import", parent_session_id="imported")
    assert db.resolve_conversation_ref("tip") == ref
    continued = move("tip")
    assert continued is entry and continued.session_id == "tip"
    assert continued.resume_pending and continued.metadata["retained"] == "owner-state"
    assert continued.metadata[BINDING_KEY] == entry.metadata[BINDING_KEY]
    assert db.get_session("imported")["end_reason"] == "compression"
    assert_binding(store, db, key, "tip", ref)
    assert store.switch_session(key, "imported") is None  # Never reopen a compressed ancestor.
    assert asyncio.run(runner_for(store, db)._resolve_async_delegation_session(continued, "imported")) is continued


def test_reset_and_force_new_cannot_release_binding(bound_store):
    store, db, source, key = bound_store
    bind_conversation(store, key, "imported")
    ref = db.resolve_conversation_ref("imported")
    assert store.reset_session(key) is None
    with pytest.raises(ValueError, match="explicit unbind"):
        store.get_or_create_session(source, force_new=True)
    assert_binding(store, db, key, "imported", ref)


def test_exhaustion_reports_failure_without_reset_or_scope_loss(bound_store):
    store, db, source, key = bound_store
    entry = bind_conversation(store, key, "imported")
    runner = runner_for(store, db)
    response, kept = asyncio.run(GatewayTurnMixin._hmwa_compression_exhaustion_reset(
        runner, {"compression_exhausted": True}, "Provider failed.", entry, key, source))
    assert kept is entry and "preserved" in response and "Web UI" in response
    runner._evict_cached_agent.assert_not_called()
    runner._clear_conversation_scope.assert_not_called()
    assert_binding(store, db, key, "imported", db.resolve_conversation_ref("imported"))


def test_stuck_restart_blocks_auto_resume_but_keeps_binding_on_user_input(bound_store, tmp_path):
    store, db, source, key = bound_store
    bind_conversation(store, key, "imported")
    ref = db.resolve_conversation_ref("imported")
    store.mark_resume_pending(key)
    counters = tmp_path / "restart-counts.json"
    counters.write_text(json.dumps({key: 3}))
    driver = SimpleNamespace(
        session_store=store, _STUCK_LOOP_THRESHOLD=3, _stuck_loop_counts_path=lambda: counters,
        _read_json_counts=lambda path: json.loads(path.read_text()),
    )
    assert GatewayShutdownMixin._suspend_stuck_loop_sessions(driver) == 1
    restarted = SessionStore(store.sessions_dir, store.config)
    restarted._db = db
    observed = restarted.lookup_by_session_key(key)
    assert observed.suspended
    assert restarted.get_or_create_session(source, touch_activity=False).suspended
    resumed = restarted.get_or_create_session(source)
    assert not resumed.suspended
    assert_binding(restarted, db, key, "imported", ref)
    assert restarted.get_or_create_session(source).session_id == "imported"


@pytest.mark.parametrize("operation", ["bind", "unbind"])
def test_explicit_binding_write_failure_keeps_live_and_durable_binding(bound_store, monkeypatch, operation):
    store, db, _source, key = bound_store
    bind_conversation(store, key, "imported")
    ref = db.resolve_conversation_ref("imported")
    db.create_session("chosen-b", "desktop")
    runner = runner_for(store, db)
    with monkeypatch.context() as patch:
        patch.setattr(db, "save_gateway_routing_entry", Mock(side_effect=OSError("write failed")))
        patch.setattr(db, "replace_gateway_routing_entries", Mock(side_effect=OSError("write failed")))
        patch.setattr(store, "_save_sessions_json", Mock(side_effect=OSError("write failed")))
        with pytest.raises(OSError, match="write failed"):
            control_call(runner, key, operation, **({"conversation_ref": db.resolve_conversation_ref("chosen-b")}
                                                  if operation == "bind" else {}))
    assert_binding(store, db, key, "imported", ref)
    # The same explicit operation remains usable after storage recovers.
    assert control_call(runner, key, operation, **({"conversation_ref": db.resolve_conversation_ref("chosen-b")}
                                                if operation == "bind" else {}))["ok"]


def test_idle_pruning_keeps_the_persistent_binding(bound_store):
    store, db, source, key = bound_store
    entry = bind_conversation(store, key, "imported")
    entry.updated_at -= timedelta(days=31)
    assert store.prune_old_entries(30) == 0
    assert store.get_or_create_session(source).session_id == "imported"
    assert_binding(store, db, key, "imported", db.resolve_conversation_ref("imported"))


def test_unbound_native_reset_switch_suspend_and_force_new_stay_native(bound_store):
    store, db, source, key = bound_store
    first = store.lookup_by_session_key(key).session_id
    reset = store.reset_session(key)
    assert reset.session_id != first and db.get_session(first)["end_reason"] == "session_reset"
    switched = store.switch_session(key, "imported")
    assert switched.session_id == "imported" and BINDING_KEY not in switched.metadata
    assert db.get_session(reset.session_id)["end_reason"] == "session_switch"
    store.suspend_session(key)
    resumed = store.get_or_create_session(source)
    assert resumed.session_id != "imported" and db.get_session("imported")["end_reason"] == "suspended"
    fresh = store.get_or_create_session(source, force_new=True)
    assert fresh.session_id != resumed.session_id and BINDING_KEY not in fresh.metadata


def test_deleting_a_bound_target_keeps_its_unavailable_binding(bound_store):
    store, db, source, key = bound_store
    bind_conversation(store, key, "imported")
    ref = db.resolve_conversation_ref("imported")
    assert store.remove_by_session_id("imported") == 0
    db.delete_session("imported")
    with pytest.raises(ValueError, match="Bound Conversation"):
        store.get_or_create_session(source)
    entry = store.lookup_by_session_key(key)
    assert entry.session_id == "imported" and entry.metadata[BINDING_KEY]["conversation_ref"] == ref


def test_unbind_create_failure_preserves_original_binding(bound_store, monkeypatch):
    store, db, _source, key = bound_store
    bind_conversation(store, key, "imported")
    ref = db.resolve_conversation_ref("imported")
    with monkeypatch.context() as patch:
        patch.setattr(db, "create_session", Mock(side_effect=OSError("cannot create")))
        with pytest.raises(OSError, match="cannot create"):
            control_call(runner_for(store, db), key, "unbind")
    assert_binding(store, db, key, "imported", ref)


def test_transient_binding_lookup_failure_keeps_completion_retryable(bound_store, monkeypatch):
    store, db, _source, key = bound_store
    bind_conversation(store, key, "imported")
    runner = runner_for(store, db)
    with monkeypatch.context() as patch:
        patch.setattr(db, "resolve_conversation_ref", Mock(side_effect=OSError("temporarily unavailable")))
        assert asyncio.run(runner._classify_completion_target("imported", key)) == "retry"
    assert_binding(store, db, key, "imported", db.resolve_conversation_ref("imported"))


@pytest.mark.parametrize("operation", ["bind", "unbind"])
def test_primary_failure_cannot_report_success_via_json_fallback(bound_store, monkeypatch, operation):
    store, db, _source, key = bound_store
    bind_conversation(store, key, "imported")
    ref = db.resolve_conversation_ref("imported")
    db.create_session("chosen-b", "desktop")
    rows_before = db._read_all("SELECT id FROM sessions ORDER BY id")
    with monkeypatch.context() as patch:
        patch.setattr(db, "save_gateway_routing_entry", Mock(side_effect=OSError("primary failed")))
        with pytest.raises(OSError, match="primary failed"):
            control_call(runner_for(store, db), key, operation,
                         **({"conversation_ref": db.resolve_conversation_ref("chosen-b")} if operation == "bind" else {}))
    assert_binding(store, db, key, "imported", ref)
    assert db._read_all("SELECT id FROM sessions ORDER BY id") == rows_before


def test_native_exhaustion_still_resets_and_clears_conversation_scope(bound_store):
    store, db, source, key = bound_store
    entry = store.lookup_by_session_key(key)
    original_id = entry.session_id
    runner = runner_for(store, db)
    runner._sync_telegram_topic_binding = Mock()
    response, fresh = asyncio.run(GatewayTurnMixin._hmwa_compression_exhaustion_reset(
        runner, {"compression_exhausted": True}, "Provider failed.", entry, key, source))
    assert fresh.session_id != original_id and BINDING_KEY not in fresh.metadata
    assert db.get_session(original_id)["end_reason"] == "session_reset"
    runner._evict_cached_agent.assert_called_once_with(key)
    runner._clear_conversation_scope.assert_called_once_with(key, reason="compression_exhausted_reset")
    assert response != "Provider failed."
