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


def test_host_tick_observes_history_import_from_another_process(owned, monkeypatch):
    """An importer cannot notify the in-process Main owner directly."""
    import subprocess
    import sys

    from hermes_cli.heartbeat import HeartbeatState
    from secretary.heartbeat_store import ConversationHeartbeatStore

    parent, db, ref = owned
    heartbeat = ConversationHeartbeatStore(db, "main")
    heartbeat.save(HeartbeatState("", 10800, created_at=100))
    from secretary.adaptive_policy import decide as real_decide
    evaluations = []
    def observe_decide(snapshot, history, config):
        evaluations.append(snapshot)
        return real_decide(snapshot, history, config)
    monkeypatch.setattr('secretary.adaptive_policy.decide', observe_decide)
    worker = """
from pathlib import Path
import sys
from hermes_state import SessionDB
from secretary.adaptive_import import import_samples
from tests.secretary.test_adaptive_empirical_wiring import _sample
db = SessionDB(Path(sys.argv[1]))
try:
    receipt = import_samples(db, sys.argv[2], [_sample()], import_id='external-worker',
                             source_sha256='c' * 64, apply=True, now=200)
    assert receipt['applied']
finally:
    db.close()
"""
    assert db.try_acquire_session_turn_lease("main", "active-host-turn")
    try:
        subprocess.run([sys.executable, "-c", worker, str(db.db_path), ref], check=True, timeout=30)
        # V4's default hot is already visible. A live native lease still prevents
        # adoption/dispatch; the persistent refresh receipt proves the later tick.
        assert heartbeat.load()._adaptive_interval_seconds == 60
        assert heartbeat.load().interval_seconds == 10800 and heartbeat.claim(200) is None
        assert evaluations == []
        with db._read_ctx() as conn:
            pending = store.refresh_conn(conn, ref)
            assert pending['revision'] == 1 and pending['evaluated_revision'] == 0
            assert store.heartbeat_conn(conn, ref) is None
    finally:
        db.release_session_turn_lease("main", "active-host-turn")
    # This is the normal recovery tick. No new user submission or Main Turn
    # has ended in the owning process since the import.
    noting.maybe_run_idle_noting(parent, db, ref, now=201)
    state = heartbeat.load()
    assert state._adaptive_interval_seconds == 60
    assert state.created_at == 100 and state.last_fired_at == 0 and state.fire_count == 0
    assert db.noting_idle_state(ref) is None
    assert len(evaluations) == 1
    assert evaluations[0]['historical_cohorts'][0]['events'][0]['kind'] == 'maintenance_sample'
    with db._read_ctx() as conn:
        adopted = store.refresh_conn(conn, ref)
        assert adopted['revision'] == adopted['evaluated_revision'] == 1
        assert store.heartbeat_conn(conn, ref)['mode'] == 'hot'


def test_native_rewind_invalidates_old_context_plan(owned, monkeypatch):
    parent, db, ref = owned
    monkeypatch.setattr("secretary.adaptive_policy.decide", lambda *args: {"mode": "hot", "threshold_tokens": 4000, "delay_seconds": 10})
    assert noting.note_main_turn_finished(parent, at=100)
    target = db._read_one("SELECT id FROM messages WHERE message_uid='u1'")[0]
    db.rewind_to_message("main", target)
    assert runtime.idle_settings(parent, noting.settings_for_db(db)).idle_threshold_tokens == 1000


def test_stale_model_context_observation_does_not_hold_heartbeat(owned, monkeypatch):
    from agent.usage_pricing import CanonicalUsage
    from agent.usage_read import (begin_main_turn_usage, observe_main_model_dispatch,
                                 observe_main_canonical_usage, finish_main_turn_usage)
    from hermes_cli.heartbeat import HeartbeatState
    from secretary.heartbeat_store import ConversationHeartbeatStore
    parent, db, ref = owned
    clock = [99.0]
    monkeypatch.setattr('secretary.heartbeat_store.time.time', lambda: clock[0])
    hb = ConversationHeartbeatStore(db, "main")
    hb.save(HeartbeatState("", 600, created_at=1))

    def actual_response(identity):
        assert db.try_acquire_session_turn_lease('main', identity, ttl_seconds=60)
        try:
            runtime.turn_started(parent, runtime.mark_input('normal work', 'user', identity))
            begin_main_turn_usage(parent, identity, has_prior_history=True)
            response = SimpleNamespace(usage=SimpleNamespace(prompt_tokens=100, completion_tokens=2,
                                        prompt_tokens_details=SimpleNamespace(cached_tokens=90)))
            with observe_main_model_dispatch(parent) as receipt:
                receipt[0] = response
            observe_main_canonical_usage(parent, response, CanonicalUsage(input_tokens=10, cache_read_tokens=90, output_tokens=2))
            finish_main_turn_usage(parent, identity, {})
        finally:
            db.release_session_turn_lease('main', identity)

    actual_response('old-model-use')
    monkeypatch.setattr("secretary.adaptive_policy.decide", lambda *args: {"mode": "hot", "threshold_tokens": 4000, "delay_seconds": 0})
    assert noting.note_main_turn_finished(parent, at=100)
    parent.model = "new-model"
    db._execute_write(lambda conn: conn.execute("UPDATE sessions SET model='new-model' WHERE id='main'"))
    clock[0] = 101
    assert runtime.record_event(db, ref, 'context_read', parent=parent, at=101, verified=True,
        source='framework', context_tokens=5000, model_key=runtime.model_key(parent),
        context_contract=runtime.context_contract(parent), context_epoch=runtime._epoch(db, ref),
        context_path=['main', 0], cache_contract=runtime.settings.heartbeat_for_db(db, ref, parent=parent)['cache_contract'])
    assert hb.load()._adaptive_mode == 'standby' and hb.claim(101) is None
    clock[0] = 601
    assert hb.claim(601) is None  # No fallback to the former native 600-second definition.
    clock[0] = 602
    actual_response('new-model-use')
    # A late old-model usage observation must not hold the new warm HB behind
    # the old early-Idle plan. Only real requests established the current cache.
    prior_request = next(e for e in store.history(db, ref, 602)
                         if e['kind'] == 'request' and e['cache_contract']['model'] == 'test/runtime')
    runtime.record_event(db, ref, 'context_read', at=602, verified=True, source='framework',
                         context_tokens=5000, model_key=prior_request['model_key'],
                         model_identity=prior_request['model_identity'], model_contract=prior_request['model_contract'],
                         cache_contract=prior_request['cache_contract'], context_contract=runtime.context_contract(parent),
                         context_epoch=prior_request['context_epoch'], context_path=prior_request['context_path'])
    with db._read_ctx() as conn:
        old_plan = store.plan_conn(conn, ref)
        assert old_plan['status'] == 'invalidated' and old_plan['finished_at'] == 100
    state, claim = hb.claim(602)
    assert state.created_at == 1 and state.last_fired_at == 602 and state.fire_count == 1
    assert hb.claim_is_current(claim, now=602)


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
        renewed = db.noting_idle_state(ref)
        assert renewed['last_turn_started_at'] == 700 and renewed['last_turn_finished_at'] == 800
        if change == 'missing_model':
            # V4 keeps this enabled target in heartbeat-only mode. Missing price
            # cannot create another early-maintenance cycle at the new Main end.
            assert renewed['due_at'] is None and renewed['trigger_produced_at'] == 800
            with db._read_ctx() as conn:
                plan = store.plan_conn(conn, ref)
                assert plan['status'] == 'disabled' and plan['finished_at'] == 800
                assert plan['decision']['threshold_tokens'] is None and plan['decision']['delay_seconds'] is None
                assert plan['decision']['diagnostics']['maintenance_deferred'] == 'missing_priced_model_configuration'
                assert conn.execute('SELECT 1 FROM secretary_heartbeats WHERE conversation_ref=?', (ref,)).fetchone() is None
        else:
            assert renewed['due_at'] == 800 + native_delay


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
def test_claimed_heartbeat_settles_at_formal_turn_boundary_after_configuration_removed(owned, monkeypatch, change):
    import json
    from secretary.heartbeat_store import ConversationHeartbeatStore, enabled_for_db
    from hermes_cli.heartbeat import HeartbeatState
    from secretary.noting_turn_boundary import observe_admitted_turn_started, observe_admitted_turn_finished
    parent, db, ref = owned
    clock = [100.0]
    monkeypatch.setattr('secretary.heartbeat_store.time.time', lambda: clock[0])
    hb = ConversationHeartbeatStore(db, 'main')
    hb.save(HeartbeatState('', 600, created_at=1))
    config = runtime.settings.for_db(db, ref, parent=parent)
    db._execute_write(lambda conn: store.adopt_mode_conn(conn, ref, 'hot', config))
    claimed_state, claim = hb.claim(100)
    assert hb.claim_is_current(claim, now=100)
    # The native lease was accepted under the old contract; only its observing
    # callback is delayed. This is not permission to submit a newly stale claim.
    assert db.try_acquire_session_turn_lease('main', 'accepted-before-setting-change', ttl_seconds=60)
    try:
        path = Path(db.db_path).parent / 'config.yaml'
        raw = json.loads(path.read_text())
        if change == 'model_removed':
            raw['noting']['adaptive_idle_token_saving']['models'] = {}
        else:
            raw['noting']['enabled'] = False
        path.write_text(json.dumps(raw))
        assert not hb.claim_is_current(claim, now=100)
        assert hb.load()._adaptive_interval_seconds == (60 if change == 'model_removed' else 600)
        with db._read_ctx() as conn:
            assert store.heartbeat_conn(conn, ref)['claim_revision'] == claim.revision
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
        assert not hb.refund(claim) and not hb.claim_is_current(claim, now=100)
        clock[0] = 101
        observe_admitted_turn_finished(parent, object())
    finally:
        db.release_session_turn_lease('main', 'accepted-before-setting-change')
    assert hb.load().last_fired_at == 100 and hb.load().fire_count == 1
    if change == 'model_removed':
        assert hb.load()._adaptive_interval_seconds == 60
        assert hb.claim(159) is None and hb.claim(160) is not None
    else:
        assert not enabled_for_db(db) and hb.load()._adaptive_interval_seconds == 600


@pytest.mark.parametrize('changed', ['reasoning', 'model', 'route'])
def test_persisted_selection_retires_live_old_plan_and_cannot_be_readopted(owned, monkeypatch, changed):
    from secretary.adaptive_refresh import refresh
    from tests.secretary.test_adaptive_policy_wiring import _prepare_paid_history
    from tests.secretary.test_adaptive_policy import NOW
    parent, db, ref = owned
    parent.base_url = 'https://old-route.test.invalid/v1'
    db.patch_session_model_config('main', {'base_url': parent.base_url})
    hb = _prepare_paid_history(parent, db, ref, monkeypatch)
    runtime.turn_started(parent, runtime.mark_input('background', 'heartbeat'), at=NOW - 60)
    assert noting.note_main_turn_finished(parent, at=NOW)
    native = noting.settings_for_db(db, ref)
    with db._read_ctx() as conn:
        before = store.plan_conn(conn, ref)
    period = db.noting_idle_state(ref)
    assert before['status'] == 'pending' and before['decision']['threshold_tokens'] != native.idle_threshold_tokens
    if changed == 'reasoning':
        db.patch_session_model_config('main', {'reasoning_config': {'effort': 'high'}})
    elif changed == 'model':
        db._execute_write(lambda conn: conn.execute("UPDATE sessions SET model='new-unregistered-model' WHERE id='main'"))
    else:
        db.patch_session_model_config('main', {'base_url': 'https://new-route.test.invalid/v1'})
    assert hb.load()._adaptive_mode == 'standby'
    assert runtime.idle_settings(parent, native) == native
    with db._read_ctx() as conn:
        retired = store.plan_conn(conn, ref)
    restored = db.noting_idle_state(ref)
    assert retired['status'] == 'invalidated' and retired['generation'] == before['generation']
    assert restored['last_turn_finished_at'] == period['last_turn_finished_at'] == NOW
    assert restored['due_at'] == NOW + native.idle_delay_seconds
    assert restored['trigger_produced_at'] is None
    db._execute_write(lambda conn: store.request_refresh_conn(conn, ref, NOW + 1))
    assert not refresh(db, ref, parent=parent, now=NOW + 1)
    with db._read_ctx() as conn:
        assert store.plan_conn(conn, ref) == retired
    assert db.noting_idle_state(ref) == restored
    # The naturally finishing old runtime may report its actual work, but cannot
    # adopt a new early plan against the already changed persisted selection.
    assert noting.note_main_turn_finished(parent, at=NOW + 2)
    with db._read_ctx() as conn:
        assert store.plan_conn(conn, ref) == retired
    assert db.noting_idle_state(ref)['due_at'] == NOW + 2 + native.idle_delay_seconds
    assert hb.load().created_at == NOW and hb.load().last_fired_at == 0
    actual_end = [e for e in store.history(db, ref, NOW + 2) if e['kind'] == 'turn_end'][-1]
    assert actual_end['model_contract']['model'] == parent.model == 'test/runtime'
    assert actual_end['model_contract']['reasoning_config'] is None


@pytest.mark.parametrize('entry', ['finish', 'refresh'])
def test_persisted_selection_change_during_evaluation_is_fenced_at_commit(owned, monkeypatch, entry):
    from secretary.adaptive_refresh import refresh
    from secretary.adaptive_policy import decide as real_decide
    from tests.secretary.test_adaptive_policy_wiring import _prepare_paid_history
    from tests.secretary.test_adaptive_policy import NOW
    parent, db, ref = owned
    _prepare_paid_history(parent, db, ref, monkeypatch)
    runtime.turn_started(parent, runtime.mark_input('background', 'heartbeat'), at=NOW - 60)
    assert noting.note_main_turn_finished(parent, at=NOW)
    with db._read_ctx() as conn:
        prior, mode = store.plan_conn(conn, ref), store.heartbeat_conn(conn, ref)
        assert prior['status'] == 'pending'
    def change_after_decision(*args):
        decision = real_decide(*args)
        assert decision['threshold_tokens'] is not None
        db.patch_session_model_config('main', {'reasoning_config': {'effort': 'new-persisted-selection'}})
        return decision
    monkeypatch.setattr('secretary.adaptive_policy.decide', change_after_decision)
    if entry == 'finish':
        assert noting.note_main_turn_finished(parent, at=NOW + 1)
        assert db.noting_idle_state(ref)['due_at'] == NOW + 1 + noting.settings_for_db(db, ref).idle_delay_seconds
    else:
        db._execute_write(lambda conn: store.request_refresh_conn(conn, ref, NOW))
        assert not refresh(db, ref, parent=parent, now=NOW)
    with db._read_ctx() as conn:
        current = store.plan_conn(conn, ref)
        assert current['status'] == 'invalidated' and current['generation'] == prior['generation']
        assert current['finished_at'] == prior['finished_at'] == NOW
        assert store.heartbeat_conn(conn, ref) == mode


def test_plan_selection_uses_native_default_reasoning_and_explicit_empty_override(owned):
    import json
    from secretary.adaptive_model_config import selection_is_current
    parent, db, ref = owned
    path = Path(db.db_path).parent / 'config.yaml'
    raw = json.loads(path.read_text())
    raw['agent'] = {'reasoning_effort': 'high'}
    path.write_text(json.dumps(raw))
    parent.reasoning_config = {'enabled': True, 'effort': 'high'}
    with db._read_ctx() as conn:
        assert selection_is_current(db, ref, parent, conn=conn)
    db.patch_session_model_config('main', {'reasoning_config': {}})
    with db._read_ctx() as conn:
        assert not selection_is_current(db, ref, parent, conn=conn)
    parent.reasoning_config = {}
    with db._read_ctx() as conn:
        assert selection_is_current(db, ref, parent, conn=conn)
    # Native normalized endpoint identity does not invalidate an unchanged route.
    parent.base_url = 'https://same-route.test.invalid/v1/'
    db.patch_session_model_config('main', {'base_url': 'https://same-route.test.invalid/v1'})
    with db._read_ctx() as conn:
        assert selection_is_current(db, ref, parent, conn=conn)


@pytest.mark.parametrize('boundary', ['finish', 'refresh'])
def test_stale_live_selection_is_retired_at_boundary_without_prior_idle_read(owned, monkeypatch, boundary):
    from secretary.adaptive_refresh import refresh
    from tests.secretary.test_adaptive_policy_wiring import _prepare_paid_history
    from tests.secretary.test_adaptive_policy import NOW
    parent, db, ref = owned
    _prepare_paid_history(parent, db, ref, monkeypatch)
    runtime.turn_started(parent, runtime.mark_input('background', 'heartbeat'), at=NOW - 60)
    assert noting.note_main_turn_finished(parent, at=NOW)
    with db._read_ctx() as conn:
        assert store.plan_conn(conn, ref)['status'] == 'pending'
    db.patch_session_model_config('main', {'reasoning_config': {'effort': 'high'}})
    if boundary == 'finish':
        assert noting.note_main_turn_finished(parent, at=NOW + 1)
        native_anchor = NOW + 1
    else:
        assert not refresh(db, ref, parent=parent, now=NOW + 1)
        native_anchor = NOW
    with db._read_ctx() as conn:
        assert store.plan_conn(conn, ref)['status'] == 'invalidated'
    assert db.noting_idle_state(ref)['due_at'] == native_anchor + noting.settings_for_db(db, ref).idle_delay_seconds


def test_missing_route_metadata_does_not_hide_a_known_model_selection_change(owned):
    from secretary.adaptive_model_config import selection_is_current
    parent, db, ref = owned
    db.patch_session_model_config('main', {'provider': None, 'api_mode': None})
    with db._read_ctx() as conn:
        assert selection_is_current(db, ref, parent, conn=conn)
    db._execute_write(lambda conn: conn.execute("UPDATE sessions SET model='new-model' WHERE id='main'"))
    with db._read_ctx() as conn:
        assert not selection_is_current(db, ref, parent, conn=conn)
