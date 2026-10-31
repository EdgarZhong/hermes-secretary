"""Exercise actual host refusal/cancel seams and native Idle threshold admission."""
from pathlib import Path
from types import SimpleNamespace
import threading
import time

import pytest

from secretary import adaptive_runtime as runtime, adaptive_store as store, noting_runtime as noting
from tests.secretary import test_adaptive_runtime


@pytest.fixture
def owned(tmp_path, monkeypatch):
    yield from test_adaptive_runtime.owned.__wrapped__(tmp_path, monkeypatch)


def test_web_input_is_explicit_and_internal_submit_does_not_impersonate(owned):
    parent, db, ref = owned
    assert runtime.origin(runtime.web_submit_input({"agent": parent}, "hi", {"client_submission_id": "s1"})) == "user"
    assert runtime.origin(runtime.web_submit_input({"agent": parent}, "framework", {}, internal_hosted_submit=True)) == "unknown"
    assert runtime.origin(runtime.web_submit_input({"agent": parent}, "bot", {}, turn_author={"is_bot": True})) == "unknown"
    assert len([e for e in store.history(db, ref, time.time()) if e["kind"] == "user_activity"]) == 1


def test_real_idle_refusal_and_cancel_rpc_are_correlated_to_same_operation(owned, monkeypatch):
    from agent.compression_read import CompressionObservation
    from agent.conversation_compression import CompressionCommitFence
    from tui_gateway import methods_submit_idle as submit
    from tui_gateway.methods_web_read import _compression_handler
    parent, db, ref = owned
    registration = SimpleNamespace(observation=CompressionObservation(), fence=CompressionCommitFence())
    parent._compression_commit_fence_lock = threading.RLock()
    parent._compression_commit_fence_stack = [registration]
    runtime.maintenance(parent, registration, trigger="noting_joint_idle")
    monkeypatch.setattr(submit, "_err", lambda rid, code, message, data: {"code": code, **data}, raising=False)
    with submit._idle_submit_scope("first-attempt"):
        result = submit._idle_submit_claim_error("rid", {"running": True, "agent": parent})
    assert result["accepted"] is False
    server = SimpleNamespace(_sess_nowait=lambda *args: ({"agent": parent}, None),
                             _session_uses_compute_host=lambda session: False,
                             _ok=lambda rid, value: value)
    result = _compression_handler(server, "cancel", {"operation_id": registration.observation.operation_id}, cancel=True)
    assert result["outcome"] == "cancelled"
    events = store.history(db, ref, time.time())
    blocked = [e for e in events if e["kind"] == "blocked_send"]
    cancelled = [e for e in events if e["kind"] == "cancel"]
    assert len(blocked) == 1 and len(cancelled) == 2
    assert blocked[0]["operation_id"] == cancelled[0]["operation_id"]
    assert blocked[0]["trigger"] == cancelled[0]["trigger"] == "idle"
    assert all(item["source"] == "user" for item in cancelled)
    assert {item["outcome"] for item in cancelled} == {"requested", "cancelled"}
    users = [e for e in events if e["kind"] == "user_activity"]
    assert len(users) == 1 and users[0]["ingress"] == "web_submit"
    runtime.cancelled(parent, registration.observation.operation_id, "cancelled")
    assert len([e for e in store.history(db, ref, time.time()) if e["kind"] == "user_activity"]) == 1


def test_due_native_idle_uses_adopted_threshold_once_and_not_reoptimizing(owned, monkeypatch):
    parent, db, ref = owned
    called = []
    def policy(*args):
        called.append(True)
        return {"mode": "business", "threshold_tokens": 6000, "delay_seconds": 10}
    monkeypatch.setattr("secretary.adaptive_policy.decide", policy)
    assert noting.note_main_turn_finished(parent, at=100)
    decision = noting._joint_trigger_decision(parent, db, ref, "idle", noting.ContextMeasurement(5000, 130000, 75000),
                                               None, 110, db.noting_idle_state(ref))
    assert decision.reason == "below_idle_threshold"
    assert len(called) == 1
    assert db.noting_idle_claim_event(ref, now=120, delay_seconds=500) == "idle_trigger_produced"


def test_model_change_rejects_unconsumed_old_plan(owned, monkeypatch):
    parent, db, ref = owned
    monkeypatch.setattr("secretary.adaptive_policy.decide", lambda *args: {"mode": "hot", "threshold_tokens": 1000, "delay_seconds": 10})
    assert noting.note_main_turn_finished(parent, at=100)
    parent.model = "changed-provider-model"
    assert runtime.idle_settings(parent, noting.settings_for_db(db)).idle_threshold_tokens is None


def test_gate_off_remains_native_and_idle_off_can_still_adapt_mode(owned, monkeypatch):
    parent, db, ref = owned
    config = Path(db.db_path).parent / "config.yaml"
    current = config.read_text()
    config.write_text(current.replace("    enabled: true\n    delay_seconds", "    enabled: false\n    delay_seconds"))
    monkeypatch.setattr("secretary.adaptive_policy.decide", lambda *args: {"mode": "hot", "threshold_tokens": None, "delay_seconds": None})
    assert not noting.note_main_turn_finished(parent, at=100)
    assert db.noting_idle_state(ref) is None
    with db._read_ctx() as conn:
        assert store.heartbeat_conn(conn, ref)["mode"] == "hot"
    config.write_text("noting:\n  enabled: true\n  idle:\n    enabled: true\n    delay_seconds: 500\n    threshold_tokens: 1000\n")
    monkeypatch.setattr("secretary.adaptive_policy.decide", lambda *args: pytest.fail("disabled policy was called"))
    assert noting.note_main_turn_finished(parent, at=200)
    assert db.noting_idle_state(ref)["due_at"] == 700


def test_policy_receives_current_turn_and_next_actual_instant_due(owned, monkeypatch):
    from secretary.schedules import SchedulerStore
    parent, db, ref = owned
    now = time.time()
    scheduler = SchedulerStore(db, ref, session_id="main")
    result = scheduler.create("known future", "in 20 minutes", "instant", now=now)
    assert result["success"]
    seen = []
    def policy(snapshot, history, config):
        seen.append((snapshot, history))
        return {"mode": "business", "threshold_tokens": None, "delay_seconds": None, "fallback": True}
    monkeypatch.setattr("secretary.adaptive_policy.decide", policy)
    assert noting.note_main_turn_finished(parent, at=now)
    snapshot, history = seen[-1]
    assert snapshot["next_reminder_known"] is True and snapshot["next_reminder_at"] > now
    assert any(event["kind"] == "turn_end" and event["at"] == now and event["context_tokens"] == 5000 for event in history)


def test_native_rewind_invalidates_old_context_plan(owned, monkeypatch):
    parent, db, ref = owned
    monkeypatch.setattr("secretary.adaptive_policy.decide", lambda *args: {"mode": "hot", "threshold_tokens": 4000, "delay_seconds": 10})
    assert noting.note_main_turn_finished(parent, at=100)
    target = db._read_one("SELECT id FROM messages WHERE message_uid='u1'")[0]
    db.rewind_to_message("main", target)
    assert runtime.idle_settings(parent, noting.settings_for_db(db)).idle_threshold_tokens is None


def test_stale_model_context_observation_does_not_hold_heartbeat(owned, monkeypatch):
    from hermes_cli.heartbeat import HeartbeatState
    from secretary.heartbeat_store import ConversationHeartbeatStore
    parent, db, ref = owned
    hb = ConversationHeartbeatStore(db, "main")
    hb.save(HeartbeatState("", 600, created_at=1))
    monkeypatch.setattr("secretary.adaptive_policy.decide", lambda *args: {"mode": "hot", "threshold_tokens": 4000, "delay_seconds": 0})
    assert noting.note_main_turn_finished(parent, at=100)
    parent.model = "new-model"
    runtime.record_event(db, ref, "context_read", at=101, verified=True, source="framework",
                         context_tokens=5000, model_key=runtime.model_key(parent))
    assert hb.claim(101) is not None


def test_context_capacity_change_invalidates_old_plan_without_model_change(owned, monkeypatch):
    parent, db, ref = owned
    monkeypatch.setattr("secretary.adaptive_policy.decide", lambda *args: {"mode": "hot", "threshold_tokens": 4000, "delay_seconds": 10})
    assert noting.note_main_turn_finished(parent, at=100)
    parent.context_compressor.context_length = 140000
    assert runtime.idle_settings(parent, noting.settings_for_db(db)).idle_threshold_tokens is None
