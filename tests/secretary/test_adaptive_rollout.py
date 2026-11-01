"""Action feedback changes state; history is not a frozen counterfactual curve."""
from types import SimpleNamespace

from secretary.adaptive_rollout import collision_risk, forecast

CFG = dict(cache_ttl_seconds=100, hot_cache_fraction=1, cache_ratio=.1, output_ratio=5,
           heartbeat_extra_calls=0, heartbeat_fresh_tokens=10, heartbeat_output_tokens=2)
SNAPSHOT = dict(now=1000, context_tokens=1000)
PROFILE = SimpleNamespace(cost=500, duration=100, retained=.2, recovery=50)


def features(offsets):
    return dict(last_request_at=1000, heartbeat_calls=1, heartbeat_output_tokens=None,
                trajectory=dict(marks={}, paths=[dict(weight=1, events=[dict(offset=at, calls=1,
                     growth_tokens=200, output_tokens=100, duration_seconds=0) for at in offsets])]))


def test_multi_return_cost_bills_every_output_and_evolves_own_context():
    cost, terminal, reads = forecast(SNAPSHOT, features([50, 75]), CFG, [], None, None)
    assert cost == 1620  # (100 + 200 + 500) + (120 + 200 + 500)
    assert terminal == 1400
    assert reads == 0


def test_user_before_deadline_invalidates_maintenance_and_its_savings():
    data = features([5, 50])
    assert forecast(SNAPSHOT, data, CFG, [], 10, PROFILE) == forecast(SNAPSHOT, data, CFG, [], None, PROFILE)


def test_compaction_changes_future_context_and_does_not_keep_old_cache_alive():
    cost, terminal, reads = forecast(SNAPSHOT, features([150, 175]), CFG, [], 10, PROFILE)
    assert terminal == 600
    assert reads == 2
    assert cost == 2190  # maintenance 500 + cold 200 + 2*(growth200+output500) + recovery50 + warm40


def test_heartbeat_remains_due_during_work_then_coalesces_once():
    data = features([5])
    data['trajectory']['paths'][0]['events'][0]['duration_seconds'] = 80
    cost, terminal, _ = forecast(SNAPSHOT, data, CFG, [(50, 'heartbeat')], None, None)
    assert cost == 940  # User800 + retained due HB (120 + 10 + 2*5).
    assert terminal == 1212


def test_slower_more_expensive_maintenance_cannot_profit_by_dropping_a_due_heartbeat():
    cfg = {**CFG, 'cache_ttl_seconds': 1000}
    fast = SimpleNamespace(cost=500, duration=40, retained=.2, recovery=0)
    slow = SimpleNamespace(cost=520, duration=100, retained=.2, recovery=0)
    assert forecast(SNAPSHOT, features([]), cfg, [(50, 'heartbeat')], 10, fast)[0] == 720
    assert forecast(SNAPSHOT, features([]), cfg, [(50, 'heartbeat')], 10, slow)[0] == 740


def test_actual_heartbeat_claim_time_reanchors_following_period():
    data = features([5])
    data['trajectory']['paths'][0]['events'][0]['duration_seconds'] = 80
    cfg = {**CFG, 'horizon_seconds': 170}
    # Due50 -> actual85 -> next185 (outside horizon), not theoretical150.
    assert forecast(SNAPSHOT, data, cfg, [(50, 'heartbeat'), (150, 'heartbeat')], None, None,
                    heartbeat_interval=100)[0] == 940


def test_zero_call_user_activity_is_not_billed_as_a_model_read():
    data = features([5])
    data['trajectory']['paths'][0]['events'][0].update(calls=0, growth_tokens=0, output_tokens=0)
    assert forecast(SNAPSHOT, data, CFG, [], None, None) == (0, 1000, 0)


def test_collision_is_conditioned_on_plan_survival():
    data = features([40, 55])['trajectory']
    assert collision_risk(data, 20, 30) == (1, 10)
    assert collision_risk(data, 50, 30) == (1, 30)
