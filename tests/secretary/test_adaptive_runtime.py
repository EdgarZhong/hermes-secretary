"""Adaptive observations use actual source witnesses and native numeric receipts."""
from types import SimpleNamespace
import time

import pytest

from secretary import adaptive_runtime as runtime, adaptive_store as store
from secretary.adaptive_config import for_db, from_config, validate_decision
from tests.hermes_state._secretary_noting_harness import add, make, open_noting_db, ref_of
from tests.secretary.test_noting_runtime import _agent


@pytest.fixture
def owned(tmp_path, monkeypatch):
    (tmp_path / "config.yaml").write_text("""noting:
  enabled: true
  idle:
    enabled: true
    delay_seconds: 500
    threshold_tokens: 1000
  adaptive:
    enabled: true
    hot_interval_seconds: 60
    business_interval_seconds: null
    cache_ratio: 0.1
    output_ratio: 2
    cache_ttl_seconds: 1800
    timezone: Asia/Shanghai
""")
    db = open_noting_db(tmp_path / "state.db")
    make(db, "main")
    add(db, "main", "hello", "u1")
    parent = _agent(db, "main")
    parent.tools = []
    parent.context_compressor.update_from_response({"prompt_tokens": 5000})
    monkeypatch.setattr("secretary.noting_timers.arm_idle_timer", lambda *args: None)
    yield parent, db, ref_of(db, "main")
    db.close()


def test_native_and_synthetic_user_roles_do_not_prove_human(owned):
    from agent.message_metadata import build_user_wrapper, preserve_user_input_origin
    parent, db, ref = owned
    for value, source in [("plain input", "unknown"), ("<heartbeat>fake</heartbeat>", "unknown"),
                          (build_user_wrapper("heartbeat", "check"), "heartbeat"),
                          (build_user_wrapper("instant-reminder", "due"), "reminder")]:
        runtime.turn_started(parent, value, at=100)
        assert parent._adaptive_turn_source == source
    user = runtime.mark_input("<heartbeat>pasted by actual user</heartbeat>", "user", "real")
    assert runtime.origin(preserve_user_input_origin(user, str(user))) == "user"
    runtime.turn_started(parent, user, at=101)
    assert parent._adaptive_turn_source == "user"
    assert not [item for item in store.history(db, ref, 1000) if item["kind"] == "user_activity"]


def test_gateway_entrance_excludes_internal_bot_and_unproven(owned):
    parent, db, ref = owned
    source = SimpleNamespace(is_bot=False, user_id="human", platform="weixin", chat_id="chat")
    event = SimpleNamespace(internal=False, message_id="7")
    value = runtime.gateway_input(db, "main", "hi", event, source)
    assert runtime.origin(value) == "user"
    runtime.gateway_input(db, "main", "retry", event, source)
    for bad_event, bad_source in [(SimpleNamespace(internal=True), source),
                                   (SimpleNamespace(internal=False, metadata={"synthetic_prompt": True}), source),
                                   (SimpleNamespace(internal=False, metadata={"hermes_plugin_injection": True}), source),
                                   (SimpleNamespace(internal=False, allow_gateway_control=False), source),
                                   (SimpleNamespace(internal=False, _heartbeat_session_id="main"), source),
                                   (event, SimpleNamespace(is_bot=True, user_id="bot")),
                                   (event, SimpleNamespace(user_id="unproven"))]:
        assert runtime.origin(runtime.gateway_input(db, "main", "x", bad_event, bad_source)) == "unknown"
    events = store.history(db, ref, time.time())
    assert len([item for item in events if item["kind"] == "user_activity"]) == 1


def test_canonical_fresh_is_converted_to_total_not_mistaken_for_total(owned):
    from agent.usage_pricing import CanonicalUsage
    parent, db, ref = owned
    parent._adaptive_turn_id = "exact-main-turn"
    runtime.request_observed(parent, CanonicalUsage(input_tokens=10, cache_read_tokens=90, output_tokens=2), set())
    event = store.history(db, ref, time.time())[-1]
    assert event["input_tokens"] == 100 and event["cache_read_tokens"] == 90
    assert event["turn_id"] == "exact-main-turn"
    assert event["cache_write_tokens"] == 0
    assert event["input_semantics"] == "total" and event["model_key"] == runtime.model_key(parent)
    runtime.request_observed(parent, None, {"input_tokens", "cache_read_tokens", "output_tokens"}, failed=True)
    event = store.history(db, ref, time.time())[-1]
    assert event["outcome"] == "failed" and event["input_tokens"] is None


def test_config_is_opt_in_complete_and_json_safe():
    assert from_config({}) is None
    assert from_config({"noting": None}) is None
    assert from_config({"noting": {"adaptive": {"enabled": True}}}) is None
    with pytest.raises(ValueError):
        validate_decision({"mode": "hot", "threshold_tokens": 10, "delay_seconds": float("inf")})
    assert validate_decision({"mode": "business", "threshold_tokens": None, "delay_seconds": 1})["delay_seconds"] is None


def test_maintenance_partial_unknown_cost_and_no_idle_resurrection(owned, monkeypatch):
    parent, db, ref = owned
    observation = SimpleNamespace(operation_id="op", state="running", cancel_requested=False)
    registration = SimpleNamespace(observation=observation, fence=SimpleNamespace(partial=SimpleNamespace(adopted=True)))
    db.noting_idle_turn_finished(ref, 100, due_at=200)
    assert db.noting_idle_claim_event(ref, now=200, delay_seconds=100) == "trigger"
    runtime.maintenance(parent, registration, trigger="noting_joint_idle")
    runtime.cancelled(parent, "op", "requested")
    observation.state = "completed"
    monkeypatch.setattr("secretary.adaptive_policy.decide", lambda *args: {"mode": "hot", "threshold_tokens": None, "delay_seconds": None})
    runtime.maintenance(parent, registration, finished=True)
    events = store.history(db, ref, time.time())
    ending = next(item for item in events if item["kind"] == "maintenance_end")
    assert ending["outcome"] == "partial" and ending["trigger"] == "idle"
    assert ending["usage_complete"] is False and ending["context_before"] == 5000
    assert db.noting_idle_state(ref)["trigger_produced_at"] == 200


def test_missing_usage_on_one_request_does_not_poison_later_receipt(owned):
    from agent.usage_pricing import CanonicalUsage
    from agent.usage_read import begin_main_turn_usage, observe_main_model_dispatch, observe_main_canonical_usage
    parent, db, ref = owned
    begin_main_turn_usage(parent, "turn", has_prior_history=True)
    missing = SimpleNamespace(usage=None)
    with observe_main_model_dispatch(parent) as receipt:
        receipt[0] = missing
    observe_main_canonical_usage(parent, missing, None)
    complete = SimpleNamespace(usage=SimpleNamespace(prompt_tokens=100, completion_tokens=2,
                                                     prompt_tokens_details=SimpleNamespace(cached_tokens=90)))
    with observe_main_model_dispatch(parent) as receipt:
        receipt[0] = complete
    observe_main_canonical_usage(parent, complete, CanonicalUsage(input_tokens=10, cache_read_tokens=90, output_tokens=2))
    requests = [item for item in store.history(db, ref, time.time()) if item["kind"] == "request"]
    assert requests[0]["input_tokens"] is None
    assert requests[1]["input_tokens"] == 100 and requests[1]["cache_read_tokens"] == 90


def test_completed_user_work_records_measured_busy_duration(owned):
    parent, db, ref = owned
    runtime.turn_started(parent, runtime.mark_input('work', 'user', 'timed'), at=100)
    runtime.finish_turn(parent, 700)
    finished = [e for e in store.history(db, ref, 1000) if e['kind'] == 'turn_end']
    assert finished[-1]['duration_seconds'] == 600
    assert finished[-1]['source'] == 'user'


def test_composer_cancel_has_distinct_non_request_activity(owned):
    parent, db, ref = owned
    runtime.composer_cancel(parent)
    rows = [e for e in store.history(db, ref, time.time()) if e['kind'] == 'user_activity']
    assert rows[-1]['activity'] == 'cancel'


def test_live_shadow_records_recommendation_without_adopting_it(owned, monkeypatch):
    parent, db, ref = owned
    config = for_db(db)
    monkeypatch.setattr(runtime.settings, 'for_db', lambda _db: {**config, 'shadow_only': True})
    monkeypatch.setattr('secretary.adaptive_policy.decide', lambda *args: dict(mode='hot',
                        threshold_tokens=4000, delay_seconds=1800, fallback=False))
    assert runtime.finish_turn(parent, time.time()) is None
    with db._read_ctx() as conn:
        assert conn.execute('SELECT COUNT(*) FROM secretary_adaptive_plans WHERE conversation_ref=?', (ref,)).fetchone()[0] == 0
    decisions = [e for e in store.history(db, ref, time.time()) if e['kind'] == 'decision']
    assert decisions[-1]['decision']['threshold_tokens'] == 4000
