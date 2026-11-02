"""Conversation-scoped native Idle uses existing lifecycle/claim owners, with profile defaults intact."""
import json
from pathlib import Path

import pytest

from hermes_state import SessionDB
from secretary import adaptive_runtime, adaptive_store, noting_runtime as runtime, noting_timers
from secretary.noting_scope import settings_for_db
from tests.secretary import test_adaptive_runtime
from tests.secretary.test_noting_runtime import _agent
from tests.hermes_state._secretary_noting_harness import make, add, ref_of


@pytest.fixture
def owned(tmp_path, monkeypatch):
    yield from test_adaptive_runtime.owned.__wrapped__(tmp_path, monkeypatch)


def configure(db, ref, *, adaptive=False):
    path = Path(db.db_path).parent / 'config.yaml'
    config = json.loads(path.read_text())
    config['noting']['idle'] = {'enabled': False, 'delay_seconds': 500, 'threshold_tokens': 98304,
        'conversations': {ref: {'enabled': True, 'delay_seconds': 7200, 'threshold_tokens': 700000}}}
    if not adaptive:
        config['noting'].pop('adaptive_idle_token_saving', None)
    path.write_text(json.dumps(config))
    return path, config


def test_target_end_arms_its_native_deadline_while_other_conversation_stays_disabled(owned, monkeypatch):
    parent, db, ref = owned
    configure(db, ref)
    make(db, 'other')
    add(db, 'other', 'other main', 'other-user')
    other = _agent(db, 'other')
    other_ref = ref_of(db, 'other')
    target = settings_for_db(db, ref)
    assert target.idle_enabled and target.idle_delay_seconds == 7200 and target.idle_threshold_tokens == 700000
    assert not settings_for_db(db).idle_enabled and not settings_for_db(db, other_ref).idle_enabled
    armed = []
    monkeypatch.setattr(noting_timers, 'arm_idle_timer', lambda owner, handle, reference, due: armed.append((reference, due)))
    assert runtime.note_main_turn_finished(parent, at=100)
    assert not runtime.note_main_turn_finished(other, at=100)
    assert armed == [(ref, 7300)]
    assert db.noting_idle_state(ref)['due_at'] == 7300 and db.noting_idle_state(other_ref) is None
    assert runtime.idle_candidates(db, now=7299) == []
    assert runtime.idle_candidates(db, now=7300) == [ref]


@pytest.mark.parametrize('gate', ['global', 'local'])
def test_target_override_does_not_bypass_noting_or_notebook_local_close(owned, monkeypatch, gate):
    parent, db, ref = owned
    path, config = configure(db, ref)
    assert runtime.note_main_turn_finished(parent, at=100)
    period = db.noting_idle_state(ref)
    if gate == 'global':
        config['noting']['enabled'] = False
        path.write_text(json.dumps(config))
    else:
        db.notebook_set_local_enabled(ref, False)
    decision = runtime._joint_trigger_decision(parent, db, ref, 'idle',
        runtime.ContextMeasurement(800000, 900000, 750000), None, 7300, period)
    assert decision.action == 'skip' and not decision.compaction_due
    assert db.noting_idle_state(ref) is None
    assert not noting_timers.refresh_maintenance(parent)


@pytest.mark.parametrize('override', [
    {'enabled': 'yes'}, {'delay_seconds': -1}, {'threshold_tokens': 0},
    {'enabled': True, 'threshold_tokens': None}, {'scheduler': {'enabled': True}},
])
def test_only_three_native_fields_are_allowed_and_validated_by_existing_parser(owned, override):
    _parent, db, ref = owned
    path, config = configure(db, ref)
    config['noting']['idle']['conversations'][ref].update(override)
    path.write_text(json.dumps(config))
    target = settings_for_db(db, ref)
    assert not target.enabled and not target.idle_enabled and target.configuration_failure
    assert settings_for_db(db, 'unconfigured-ref').enabled
    assert not settings_for_db(db, 'unconfigured-ref').idle_enabled


def test_missing_override_keeps_the_exact_existing_native_settings(owned):
    _parent, db, ref = owned
    path = Path(db.db_path).parent / 'config.yaml'
    before = path.read_text()
    assert settings_for_db(db, ref) == settings_for_db(db)
    configure(db, ref)
    unrelated = settings_for_db(db, 'other-ref')
    assert not unrelated.idle_enabled and unrelated.idle_delay_seconds == 500 and unrelated.idle_threshold_tokens == 98304
    # A partial target override inherits the unchanged native delay/threshold.
    config = json.loads(path.read_text())
    config['noting']['idle']['conversations'][ref] = {'enabled': True}
    path.write_text(json.dumps(config))
    partial = settings_for_db(db, ref)
    assert partial.idle_enabled and partial.idle_delay_seconds == 500 and partial.idle_threshold_tokens == 98304
    path.write_text(before)
    assert settings_for_db(db, ref) == settings_for_db(db)


def test_restart_attach_restores_target_absolute_native_deadline_without_replanning(owned, monkeypatch):
    parent, db, ref = owned
    configure(db, ref)
    assert runtime.note_main_turn_finished(parent, at=100)
    period = db.noting_idle_state(ref)
    reopened = SessionDB(db.db_path)
    try:
        resumed = _agent(reopened, 'main')
        resumed.model, resumed.provider, resumed.api_mode = parent.model, parent.provider, parent.api_mode
        armed = []
        monkeypatch.setattr(noting_timers, 'arm_idle_timer', lambda *args: armed.append(args[-1]))
        assert noting_timers.attach_idle_timer(resumed, reopened, ref, now=1000) == 'skip:timer_armed'
        assert armed == [7300] and reopened.noting_idle_state(ref) == period
        assert noting_timers.refresh_maintenance(resumed)
    finally:
        reopened.close()


def test_removed_override_rejects_old_callback_and_retires_disabled_owner_period(owned):
    from secretary.noting_cache_owner import _retire_disabled_period
    parent, db, ref = owned
    path, config = configure(db, ref)
    assert runtime.note_main_turn_finished(parent, at=100)
    period = db.noting_idle_state(ref)
    config['noting']['idle'].pop('conversations')
    path.write_text(json.dumps(config))
    assert runtime._run_idle_event(parent, db, ref, now=7300, expected_period=period) == 'skip:idle_disabled'
    assert db.noting_idle_state(ref) is None
    # Cache reclamation consults the same target controls, never the unrelated Profile gate.
    db.noting_idle_turn_finished(ref, 200, due_at=7400)
    _retire_disabled_period(parent)
    assert db.noting_idle_state(ref) is None


def test_adaptive_snapshot_and_invalid_plan_restore_use_target_native_contract(owned, monkeypatch):
    parent, db, ref = owned
    path, config = configure(db, ref, adaptive=True)
    monkeypatch.setattr('secretary.adaptive_policy.decide', lambda *args: {
        'mode': 'hot', 'threshold_tokens': 4000, 'delay_seconds': 10})
    assert runtime.note_main_turn_finished(parent, at=100)
    active = adaptive_runtime.settings.for_db(db, ref, parent=parent)
    snapshot, _ = adaptive_runtime.snapshot(parent, db, ref, active, 100)
    assert snapshot['idle_enabled'] and snapshot['idle_config'] == [True, 7200, 700000]
    assert db.noting_idle_state(ref)['due_at'] == 110
    with db._read_ctx() as conn:
        assert adaptive_store.plan_conn(conn, ref)['decision']['idle_config'] == [True, 7200, 700000]
    config['noting']['adaptive_idle_token_saving']['conversations'][ref]['enabled'] = False
    path.write_text(json.dumps(config))
    decision = runtime._joint_trigger_decision(parent, db, ref, 'idle',
        runtime.ContextMeasurement(5000,130000,75000), None, 110, db.noting_idle_state(ref))
    assert decision.action == 'skip' and not decision.compaction_due
    assert db.noting_idle_state(ref)['due_at'] == 7300
    assert settings_for_db(db).idle_delay_seconds == 500 and not settings_for_db(db).idle_enabled


def test_target_due_event_reaches_existing_parent_request_once_with_target_threshold(owned):
    from types import SimpleNamespace
    parent, db, ref = owned
    path, config = configure(db, ref)
    config['noting']['idle']['conversations'][ref] = {
        'enabled': True, 'delay_seconds': 5, 'threshold_tokens': 1000}
    path.write_text(json.dumps(config))
    calls = []
    parent.request_context_compaction = lambda **kwargs: (
        calls.append(kwargs), SimpleNamespace(ok=True, status='admitted'))[1]
    assert runtime.note_main_turn_finished(parent, at=100)
    period = db.noting_idle_state(ref)
    assert period['due_at'] == 105
    assert runtime._run_idle_event(parent, db, ref, now=105, expected_period=period) == 'idle_compaction_requested'
    assert len(calls) == 1 and calls[0]['relevant_threshold_tokens'] == 1000
    assert calls[0]['expected_owner'][1:] == (db, ref)
    assert runtime._run_idle_event(parent, db, ref, now=106, expected_period=period) == 'skip:idle_trigger_produced'
    assert len(calls) == 1


def test_no_override_native_global_lifecycle_keeps_its_original_deadline(owned):
    parent, db, ref = owned
    path = Path(db.db_path).parent / 'config.yaml'
    config = json.loads(path.read_text())
    config['noting'].pop('adaptive_idle_token_saving')
    config['noting']['idle'] = {'enabled': True, 'delay_seconds': 1234, 'threshold_tokens': 1000}
    path.write_text(json.dumps(config))
    assert runtime.note_main_turn_finished(parent, at=100)
    assert db.noting_idle_state(ref)['due_at'] == 1334
    assert settings_for_db(db, ref) == settings_for_db(db)
