"""Check the evaluator independently of whether adaptive wins a particular trace."""
import pytest
from secretary.adaptive_simulation import Scenario, Simulation

CONFIG = dict(hot_interval_seconds=1740, business_interval_seconds=None, cache_ratio=.1,
              output_ratio=5, cache_ttl_seconds=1860)


def test_same_external_work_and_exact_no_cache_invoice():
    scenario = Scenario('invoice', 10000, hours=1, initial_context=1000, users=[(0, 200), (60, 200)],
                        actual_ttl=0)
    result = Simulation(scenario, CONFIG, [], 'business-none').run()
    assert result['counts']['user'] == 2
    assert result['input_equivalent_cost'] == (1100 + 100 * 5) + (1300 + 100 * 5)
    assert result['counts']['heartbeat'] == 0


def test_heartbeat_is_endogenous_and_output_is_billed():
    scenario = Scenario('hb', 10000, hours=2, initial_context=1000, hb_output=1000)
    business = Simulation(scenario, CONFIG, [], 'business-none').run()
    hot = Simulation(scenario, CONFIG, [], 'hot-none').run()
    assert business['input_equivalent_cost'] == 0
    assert hot['counts']['heartbeat'] == 4
    assert hot['input_equivalent_cost'] > 4 * 1000 * CONFIG['output_ratio']


def test_cancelled_maintenance_does_not_shrink_or_discard_pending_user():
    scenario = Scenario('cancel', 10000, hours=1, initial_context=10000, users=[(100, 200)],
                        cancel_on_collision=True, maintenance_duration=600)
    result = Simulation(scenario, CONFIG, [], 'business-fixed', threshold=5000, delay=0).run()
    assert result['counts']['cancelled'] == 1
    assert result['counts']['user'] == 1
    assert result['input_equivalent_cost'] >= scenario.maintenance_cost


def test_busy_maintenance_coalesces_hb_and_eventually_services_identical_demand():
    scenario = Scenario('blocked', 10000, hours=1, initial_context=10000, users=[(100, 200), (200, 400)],
                        maintenance_duration=1200)
    result = Simulation(scenario, CONFIG, [], 'hot-fixed', threshold=5000, delay=0).run()
    assert result['counts']['user'] == 2
    assert result['counts']['collisions'] == 2
    assert result['max_wait_seconds'] == pytest.approx(1100)
    assert result['maintenance_wait_seconds']['idle'] == 2100
    assert result['maintenance_collisions'] == {'idle': 2, 'auto': 0}


def test_arrival_at_exact_maintenance_finish_is_not_a_collision():
    scenario = Scenario('boundary', 10000, hours=1, initial_context=10000,
                        users=[(600, 200)], maintenance_duration=600)
    result = Simulation(scenario, CONFIG, [], 'business-fixed', threshold=5000, delay=0).run()
    assert result['counts']['collisions'] == 0
    assert result['total_wait_seconds'] == 0


def test_guarded_fixed_baseline_shares_quiet_and_frequency_constraints():
    scenario = Scenario('guarded', 10000, hours=12, initial_context=100000,
                        users=[(i * 3600, 10000) for i in range(12)])
    result = Simulation(scenario, CONFIG, [], 'business-guarded', threshold=5000, delay=0).run()
    assert result['counts']['maintenance'] - result['counts']['native'] <= 2
    assert result['counts']['user'] == 12
