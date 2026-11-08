"""Action feedback changes state; history is not a frozen counterfactual curve."""
import pytest

from secretary.adaptive_cost import Profile
from secretary.adaptive_rollout import collision_risk, forecast, simulate_path

CFG = dict(cache_ttl_seconds=100, hot_cache_fraction=1, cache_ratio=.1, output_ratio=5,
           heartbeat_extra_calls=0, heartbeat_fresh_tokens=10, heartbeat_output_tokens=2)
SNAPSHOT = dict(now=1000, context_tokens=1000)
PROFILE = Profile(cost=500, duration=100, retained=.2, recovery=50, provenance='declared_test')


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
    fast = Profile(cost=500, duration=40, retained=.2, recovery=0, provenance='declared_test')
    slow = Profile(cost=520, duration=100, retained=.2, recovery=0, provenance='declared_test')
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


def test_timing_only_proxy_prices_each_return_without_fabricating_work():
    data = features([50, 175])
    for event in data['trajectory']['paths'][0]['events']:
        event.update(calls=None, growth_tokens=None, output_tokens=None, duration_seconds=None)
    assert forecast(SNAPSHOT, data, CFG, [], None, None, timing_only=True) == (1100, 1000, 0)
    assert all(event['calls'] is None for event in data['trajectory']['paths'][0]['events'])
    data['trajectory']['paths'][0]['events'][0]['calls'] = 0
    assert forecast(SNAPSHOT, data, CFG, [], None, None, timing_only=True) == (1000, 1000, 0)


def test_common_finite_window_can_miss_payback_across_later_paid_reads():
    # Explicit conditional cost experiment, not a longer production forecast:
    # same external demand, one maintenance, and the same periodic read phases.
    snapshot = dict(now=1000, context_tokens=400000)
    profile = Profile(cost=3000000, duration=3600, retained=.25, recovery=50000, provenance='declared_test')
    cfg = {**CFG, 'horizon_seconds': 48 * 3600}
    data = features([])
    period = 10800
    def costs(hours):
        scenario = {**cfg, 'horizon_seconds': hours * 3600}
        background = [(at, 'heartbeat') for at in range(period, hours * 3600 + 1, period)]
        before = forecast(snapshot, data, scenario, background, None, profile, heartbeat_interval=period)[0]
        after = forecast(snapshot, data, scenario, background, 0, profile, heartbeat_interval=period)[0]
        return before, after
    short_before, short_after = costs(6)
    long_before, long_after = costs(48)
    assert short_after > short_before
    assert long_after < long_before
    # Both complete windows bill their own repeated output and exactly one rewrite.
    assert long_after > profile.cost


CANCEL_CFG = {**CFG, 'horizon_seconds': 2000, 'cache_ttl_seconds': 1800,
              'hot_cache_fraction': .95, 'cache_ratio': .05}


def arrival(at, *, growth=0, duration=0, cancel=False):
    return dict(offset=at, calls=0 if cancel else 1, growth_tokens=growth, output_tokens=0,
                duration_seconds=duration, activity='cancel' if cancel else None)


def cancellation_profile(receipt=150, *, outcome='completed'):
    paid = () if receipt is None else (Profile(receipt, 3, 1, 0, 'declared_cancel_receipt'),)
    return Profile(100, 1000, .1 if outcome == 'completed' else 1, 0, 'declared_component',
                   diagnostics={'scenario': {'outcome': outcome}}, cancellation_scenarios=paid)


def simulated(path, *, profile=None, background=(), data=None):
    context = dict(last_request_at=None, trajectory=dict(marks={})) if data is None else data
    return simulate_path(SNAPSHOT, context, CANCEL_CFG, background, path, 0,
                         profile or cancellation_profile(), None)


def test_stop_without_blocked_user_has_collision_but_zero_maintenance_wait():
    row = simulated([arrival(3, cancel=True), arrival(1200)])
    assert row['collision'] and row['wait'] == 0
    assert row['terminal'] == 1000 and row['cost'] == 1150 and row['reads'] == 0


@pytest.mark.parametrize('outcome,terminal', [('completed', 130), ('failed', 1030)])
def test_natural_release_keeps_earliest_user_wait_without_counting_later_main_busy(outcome, terminal):
    row = simulated([arrival(2, growth=10, duration=500), arrival(4, growth=20)],
                    profile=cancellation_profile(outcome=outcome))
    assert row['wait'] == 998 and row['collision']
    assert row['terminal'] == terminal


def test_multiple_queued_users_keep_original_arrival_after_stop_and_own_long_main():
    row = simulated([arrival(2, growth=10, duration=500), arrival(4, growth=20),
                     arrival(10, cancel=True), arrival(12, growth=30), arrival(1500)])
    assert row['wait'] == 8 and row['collision']
    assert row['terminal'] == 1060 and row['reads'] == 0
    assert row['cost'] == pytest.approx(1512.25)


@pytest.mark.parametrize('receipt', [250, 50, None])
def test_stop_wait_is_independent_of_high_low_or_missing_receipt_cost(receipt):
    row = simulated([arrival(2), arrival(3, cancel=True), arrival(1200)],
                    profile=cancellation_profile(receipt))
    paid = 100 if receipt is None else receipt
    assert row['wait'] == 1 and row['collision']
    assert row['cost'] == pytest.approx(paid + 1097.5)
    assert row['terminal'] == 1000 and row['reads'] == 0


@pytest.mark.parametrize('queued,expected_wait,expected_cost', [(False, 0, 100), (True, 998, 200)])
def test_stop_exactly_at_completion_does_not_cancel_a_finished_rewrite(queued, expected_wait, expected_cost):
    path = ([arrival(2)] if queued else []) + [arrival(1000, cancel=True)]
    row = simulated(path, profile=cancellation_profile(250))
    assert row['wait'] == expected_wait
    assert row['collision'] is queued
    assert row['terminal'] == 100 and row['cost'] == expected_cost


def test_no_return_or_stop_does_not_invent_wait():
    row = simulated([])
    assert row['wait'] == 0 and not row['collision']
    assert row['cost'] == 100 and row['terminal'] == 100


def test_stop_releases_background_due_behind_same_user_queue_without_changing_maintenance_wait():
    data = dict(last_request_at=None, trajectory=dict(marks={}),
                heartbeat_model=dict(calls=1, fresh=10, output=2, growth=12))
    row = simulated([arrival(1, duration=500), arrival(3, cancel=True)],
                    background=[(2, 'heartbeat')], data=data)
    assert row['wait'] == 2 and row['collision']
    assert row['cost'] == pytest.approx(1267.5) and row['terminal'] == 1012
    assert row['reads'] == 0
