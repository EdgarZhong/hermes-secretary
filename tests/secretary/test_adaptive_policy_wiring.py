"""Actual numeric policy through native Main-end, SQLite and Heartbeat ownership."""
from pathlib import Path
import json

import pytest

from hermes_cli.heartbeat import HeartbeatState
from secretary import adaptive_runtime as runtime, adaptive_store as store, noting_runtime as noting
from secretary.heartbeat_store import ConversationHeartbeatStore
from tests.secretary import test_adaptive_runtime
from tests.secretary.test_adaptive_policy import CONFIG, NOW, empirical_history


@pytest.fixture
def owned(tmp_path, monkeypatch):
    yield from test_adaptive_runtime.owned.__wrapped__(tmp_path, monkeypatch)


def test_unmocked_policy_reaches_atomic_native_plan_and_due_clock(owned, monkeypatch):
    parent, db, ref = owned
    path = Path(db.db_path).parent / 'config.yaml'
    config = test_adaptive_runtime.adaptive_config(ref, CONFIG)
    path.write_text(json.dumps(config), encoding='utf-8')  # JSON is a YAML subset.
    monkeypatch.setattr(runtime.time, 'time', lambda: NOW)
    from agent.context_compressor import ContextCompressor
    parent.context_compressor = ContextCompressor(model='test/runtime', config_context_length=512000,
                                                  threshold_percent=.9, threshold_tokens_cap=440000,
                                                  quiet_mode=True)
    parent.context_compressor.update_from_response({'prompt_tokens': 330000})
    hb = ConversationHeartbeatStore(db, 'main')
    hb.save(HeartbeatState('', 7200, created_at=NOW))
    rows = [dict(row, model_key=runtime.model_key(parent)) if row.get('model_key') else row
            for row in empirical_history()]
    db._execute_write(lambda conn: [store.event_conn(conn, ref, event) for event in rows])
    runtime.turn_started(parent, runtime.mark_input('background', 'heartbeat'), at=NOW - 60)
    assert noting.note_main_turn_finished(parent, at=NOW)
    with db._read_ctx() as conn:
        plan, mode = store.plan_conn(conn, ref), store.heartbeat_conn(conn, ref)
    assert plan['status'] == 'pending'
    assert plan['decision']['diagnostics']['verified_user_events'] >= 8
    assert 32768 <= plan['decision']['threshold_tokens'] <= 330000
    assert plan['decision']['due_at'] == db.noting_idle_state(ref)['due_at']
    measured, _ = runtime.snapshot(parent, db, ref, runtime.settings.for_db(db, ref, parent=parent), NOW)
    assert mode['mode'] == 'hot' and measured['heartbeat_interval_seconds'] == 1740
    assert hb.load().interval_seconds == 7200  # Public definition remains the user's value.
    assert hb.load().created_at == NOW  # Mode did not reset the independent clock.
    runtime.user_arrived(db, 'main', at=NOW + 1, event_id='actual-user', ingress='web_submit')
    assert runtime.idle_settings(parent, noting.settings_for_db(db)).idle_threshold_tokens is None


@pytest.mark.parametrize('incompatible', [False, True])
def test_unknown_dispatch_or_provider_semantics_cannot_become_exact_adaptive_usage(owned, incompatible):
    from types import SimpleNamespace
    from agent.usage_read import begin_main_turn_usage, observe_main_canonical_usage, observe_main_model_dispatch
    from agent.usage_pricing import CanonicalUsage
    import time
    parent, db, ref = owned
    parent.provider = 'minimax' if incompatible else 'openai'
    parent.api_mode = 'anthropic_messages' if incompatible else 'chat_completions'
    path = Path(db.db_path).parent / 'config.yaml'
    config = json.loads(path.read_text())
    models = config['noting']['adaptive_idle_token_saving']['models']
    models[parent.provider] = {'test/runtime': dict(models['openai']['test/runtime'])}
    path.write_text(json.dumps(config))
    begin_main_turn_usage(parent, 't', has_prior_history=False)
    response = SimpleNamespace(usage={'input_tokens': 100, 'output_tokens': 2,
                                     'cache_read_input_tokens': 90})
    if incompatible:
        with observe_main_model_dispatch(parent) as receipt:
            receipt[0] = response
    observe_main_canonical_usage(parent, response, CanonicalUsage(input_tokens=10, cache_read_tokens=90, output_tokens=2))
    request = next(e for e in store.history(db, ref, time.time()) if e['kind'] == 'request')
    assert request['input_tokens'] is None and request['cache_read_tokens'] is None
