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
    assert runtime.idle_settings(parent, noting.settings_for_db(db)).idle_threshold_tokens == 1000


def test_gate_off_remains_native_and_idle_off_can_still_adapt_mode(owned, monkeypatch):
    parent, db, ref = owned
    config = Path(db.db_path).parent / "config.yaml"
    import json
    current = json.loads(config.read_text())
    current["noting"]["idle"]["enabled"] = False
    config.write_text(json.dumps(current))
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
    assert runtime.idle_settings(parent, noting.settings_for_db(db)).idle_threshold_tokens == 1000


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
    # Unconfigured new model falls back to the native 600s definition, never the old hot plan.
    assert hb.claim(101) is None
    assert hb.claim(601) is not None


def test_context_capacity_change_invalidates_old_plan_without_model_change(owned, monkeypatch):
    parent, db, ref = owned
    monkeypatch.setattr("secretary.adaptive_policy.decide", lambda *args: {"mode": "hot", "threshold_tokens": 4000, "delay_seconds": 10})
    assert noting.note_main_turn_finished(parent, at=100)
    parent.context_compressor.context_length = 140000
    assert runtime.idle_settings(parent, noting.settings_for_db(db)).idle_threshold_tokens == 1000


@pytest.mark.parametrize('change', ['global', 'conversation', 'missing_model', 'window'])
def test_invalidated_early_plan_restores_native_clock_before_formal_claim(owned, monkeypatch, change):
    import json
    parent, db, ref = owned
    monkeypatch.setattr('secretary.adaptive_policy.decide', lambda *args: {
        'mode': 'hot', 'threshold_tokens': 4000, 'delay_seconds': 10})
    assert noting.note_main_turn_finished(parent, at=100)
    before = db.noting_idle_state(ref)
    assert before['due_at'] == 110
    path = Path(db.db_path).parent / 'config.yaml'
    config = json.loads(path.read_text())
    block = config['noting']['adaptive_idle_token_saving']
    native_delay = 700 if change == 'global' else 500
    native_due = 100 + native_delay
    config['noting']['idle']['delay_seconds'] = native_delay
    if change == 'global':
        block['enabled'] = False
    elif change == 'conversation':
        block['conversations'][ref]['enabled'] = False
    elif change == 'missing_model':
        block['models'] = {}
    else:
        parent.context_compressor.threshold_tokens_cap = 85000
        parent.context_compressor.context_length = 140000
    path.write_text(json.dumps(config))
    measured = noting.ContextMeasurement(5000, 140000 if change == 'window' else 130000,
                                          85000 if change == 'window' else 75000)
    decision = noting._joint_trigger_decision(parent, db, ref, 'idle', measured, None, 110, before)
    assert decision.action == 'skip' and not decision.compaction_due
    current = db.noting_idle_state(ref)
    assert current['last_turn_finished_at'] == 100 and current['due_at'] == native_due
    assert current['trigger_produced_at'] is None
    with db._read_ctx() as conn:
        assert store.plan_conn(conn, ref)['status'] == 'invalidated'
    # The original native claim cannot consume the former early deadline.
    assert db.noting_idle_claim_event(ref, now=native_due - 1, delay_seconds=native_delay) == 'not_idle'
    from secretary.noting_timers import attach_idle_timer
    armed = []
    monkeypatch.setattr('secretary.noting_timers.arm_idle_timer', lambda *args: armed.append(args[-1]))
    assert attach_idle_timer(parent, db, ref, now=111) == 'skip:timer_armed'
    assert armed == [native_due]
    due = noting._joint_trigger_decision(parent, db, ref, 'idle', measured, None, native_due, current)
    assert due.action == 'request' and due.compaction_due
    assert db.noting_idle_state(ref)['trigger_produced_at'] == native_due
    # A real new Main boundary creates its own native period, never reuses the old due.
    assert noting.note_main_turn_started(parent, at=700)
    if change != 'window':
        assert noting.note_main_turn_finished(parent, at=800)
        assert db.noting_idle_state(ref)['due_at'] == 800 + native_delay


def test_native_global_close_never_compacts_or_rearms_consumed_adaptive_cycle(owned, monkeypatch):
    import json
    parent, db, ref = owned
    monkeypatch.setattr('secretary.adaptive_policy.decide', lambda *args: {
        'mode': 'hot', 'threshold_tokens': 4000, 'delay_seconds': 10})
    assert noting.note_main_turn_finished(parent, at=100)
    before = db.noting_idle_state(ref)
    path = Path(db.db_path).parent / 'config.yaml'
    config = json.loads(path.read_text())
    config['noting']['enabled'] = False
    path.write_text(json.dumps(config))
    decision = noting._joint_trigger_decision(parent, db, ref, 'idle', noting.ContextMeasurement(5000,130000,75000),
                                               None, 110, before)
    assert decision.action == 'skip' and not decision.compaction_due
    decision = noting._joint_trigger_decision(parent, db, ref, 'idle', None, None, 600, None)
    assert decision.action == 'skip' and db.noting_idle_state(ref) is None


def test_already_accepted_idle_is_not_restored_or_replayed_on_close(owned, monkeypatch):
    import json
    parent, db, ref = owned
    monkeypatch.setattr('secretary.adaptive_policy.decide', lambda *args: {
        'mode': 'hot', 'threshold_tokens': 4000, 'delay_seconds': 10})
    assert noting.note_main_turn_finished(parent, at=100)
    assert db.noting_idle_claim_event(ref, now=110, delay_seconds=500) == 'trigger'
    accepted = db.noting_idle_state(ref)
    path = Path(db.db_path).parent / 'config.yaml'
    config = json.loads(path.read_text())
    config['noting']['adaptive_idle_token_saving']['enabled'] = False
    path.write_text(json.dumps(config))
    runtime.idle_settings(parent, noting.settings_for_db(db))
    assert db.noting_idle_state(ref) == accepted
    with db._read_ctx() as conn:
        assert store.plan_conn(conn, ref)['status'] == 'consumed'


def test_late_invalidated_plan_cannot_overwrite_new_period_or_current_valid_contract(owned, monkeypatch):
    parent, db, ref = owned
    monkeypatch.setattr('secretary.adaptive_policy.decide', lambda *args: {
        'mode': 'hot', 'threshold_tokens': 4000, 'delay_seconds': 10})
    assert noting.note_main_turn_finished(parent, at=100)
    period = db.noting_idle_state(ref)
    with db._read_ctx() as conn:
        plan = store.plan_conn(conn, ref)
    # Even if an earlier observation rejected this plan, the in-transaction recheck
    # must preserve it once the current runtime/config still matches its contract.
    assert not runtime._restore_native_idle(parent, db, ref, plan, period)
    assert db.noting_idle_state(ref) == period
    assert noting.note_main_turn_finished(parent, at=200)
    new_period = db.noting_idle_state(ref)
    assert not store.restore_native_idle(db, ref, expected_plan=plan, expected_period=period,
                                         recheck=lambda *args: 500)
    assert db.noting_idle_state(ref) == new_period
    with db._read_ctx() as conn:
        assert store.plan_conn(conn, ref)['status'] == 'pending'


@pytest.mark.parametrize('change', ['model_removed', 'noting_closed'])
def test_claimed_heartbeat_settles_at_formal_turn_boundary_after_configuration_removed(owned, change):
    import json
    from secretary.heartbeat_store import ConversationHeartbeatStore
    from hermes_cli.heartbeat import HeartbeatState
    from secretary.noting_turn_boundary import observe_admitted_turn_started
    parent, db, ref = owned
    hb = ConversationHeartbeatStore(db, 'main')
    hb.save(HeartbeatState('', 600, created_at=1))
    config = runtime.settings.for_db(db, ref, parent=parent)
    db._execute_write(lambda conn: store.adopt_mode_conn(conn, ref, 'hot', config))
    claimed_state, claim = hb.claim(100)
    path = Path(db.db_path).parent / 'config.yaml'
    raw = json.loads(path.read_text())
    if change == 'model_removed':
        raw['noting']['adaptive_idle_token_saving']['models'] = {}
    else:
        raw['noting']['enabled'] = False
    path.write_text(json.dumps(raw))
    assert hb.claim_is_current(claim) and hb.load()._adaptive_interval_seconds == 60
    from secretary.noting_scope import owning_db_scope
    with owning_db_scope(db):
        prompt = claimed_state.render_prompt(timestamp=100)
    assert runtime.origin(prompt) == 'heartbeat'
    if change == 'noting_closed':
        from hermes_cli.heartbeat import HEARTBEAT_PROMPT_TEMPLATE
        assert prompt == HEARTBEAT_PROMPT_TEMPLATE.format(interval='10m', prompt='')
    observe_admitted_turn_started(parent, object(), user_message=prompt)
    with db._read_ctx() as conn:
        assert store.heartbeat_conn(conn, ref)['claim_revision'] is None
    assert hb.load()._adaptive_interval_seconds == 600
    if change == 'model_removed':
        assert hb.claim(699) is None and hb.claim(700) is not None
