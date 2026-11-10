"""Closed-loop V4 state/expense tests; declared mechanisms, not historical claims."""
from secretary import adaptive_policy as policy
from secretary.adaptive_empirical_replay import Replay
from secretary.adaptive_model_config import digest
from tests.secretary.test_adaptive_empirical_replay import ControlledMaintenance, case, package


def cache_package():
    data = package()
    contract = dict(provider='test', model='first', api_mode='chat_completions',
                    context_length=100000, threshold_tokens=80000)
    data['config'].update(model_contract=contract, model_identity=dict(provider='test', model='first'))
    data['snapshot']['model_key'] = digest(contract)
    data['jobs'][0]['terminal_event'] = dict(data['events'][-1], model_contract=contract,
        model_identity=data['config']['model_identity'], model_key=digest(contract))
    data['events'][-1].update(model_key=digest(contract), model_contract=contract)
    data['events'].append(dict(event_id='actual-initial-request', kind='request', source='user', verified=True,
        outcome='observed', at=.5, model_key=digest(contract), model_contract=contract,
        context_epoch='old', input_tokens=10000, cache_read_tokens=9000, output_tokens=1))
    return data


def test_unused_model_switch_closes_heartbeat_until_normal_use_and_does_not_reanchor():
    data = cache_package()
    new = dict(data['config']['model_contract'], model='second')
    change = dict(kind='configuration_change', event_id='setting-change', at=20, available_at=20,
                  verified=True, model_contract=new, model_key=digest(new))
    data['knowledge_events'] = [change]
    data['jobs'].append(dict(data['jobs'][0], id='normal-new-model', start=100, end=101,
        terminal_event=dict(event_id='normal-new-model-end', at=101, model_contract=new,
                            model_identity=dict(provider='test', model='second'), model_key=digest(new))))
    engine = Replay(data, dict(case(180), initial_state=dict(mode='hot', heartbeat_anchor=0)), policy)
    result = engine.run()
    starts = [r for r in result['actions'] if r['kind'] == 'main_start']
    assert not any(r['source'] == 'heartbeat' and 20 <= r['at'] < 101 for r in starts)
    assert any(r['source'] == 'heartbeat' and r['at'] >= 101 for r in starts)
    assert result['initial_heartbeat_anchor'] == 0
    assert any(r['kind'] == 'heartbeat_mode_change' and r['after'] == 'standby' for r in result['actions'])
    assert result['counts']['user'] == 1 and result['counts']['maintenance'] == 0


def test_expired_cache_is_blocked_at_dispatch_even_without_a_new_main_decision():
    data = cache_package()
    engine = Replay(data, dict(case(300), start=200, initial_state=dict(mode='hot', heartbeat_anchor=0)), policy)
    result = engine.run()
    assert result['counts']['heartbeat'] == 0
    assert any(r['kind'] == 'heartbeat_standby' for r in result['actions'])


def test_reminder_runs_during_standby_and_restores_warm_heartbeat():
    data = cache_package()
    data['config']['cache_ttl_seconds'] = 10
    data['jobs'].append(dict(data['jobs'][0], id='due-reminder', source='reminder', start=100, end=101))
    result = Replay(data, dict(case(110), initial_state=dict(mode='hot', heartbeat_anchor=0)), policy).run()
    assert result['counts']['reminder'] == 1
    assert any(r['kind'] == 'main_start' and r['source'] == 'heartbeat' and r['at'] >= 101
               for r in result['actions'])


def test_compaction_first_recovery_read_is_charged_once_in_the_total():
    data = cache_package()
    class Maintain(ControlledMaintenance):
        assess_cache = staticmethod(policy.assess_cache)
        def decide(self, snapshot, history, config):
            result = super().decide(snapshot, history, config)
            result['mode'] = policy.assess_cache(snapshot, history, config)['mode']
            return result
    result = Replay(data, dict(case(150), initial_state=dict(mode='hot', heartbeat_anchor=0)), Maintain()).run()
    reads = [r for r in result['actions'] if r.get('recovery_operation_id')]
    assert len(reads) == 1 and reads[0]['recovery_first_read_cost'] > 1000
    assert reads[0]['requests'][0]['cache_state'] == 'cold'
    assert sum(result['billing_buckets'].values()) == result['input_equivalent_cost']


def test_declared_target_projection_keeps_request_and_turn_contracts_consistent():
    from copy import deepcopy
    from secretary.adaptive_empirical_replay_stage import project_declared_contract
    data = cache_package()
    old = deepcopy(data)
    request = data['events'][-1]
    request.update(turn_id='old', evidence_level='observed_Kimi_buckets_target_contract_proxy',
                   cache_write_tokens=0)
    request.pop('outcome')
    data['events'][1]['turn_id'] = 'old'
    data['config']['model_contract'] = dict(data['config']['model_contract'], model='projected-target')
    result = project_declared_contract(data)
    projected = [r for r in result['events'] if r.get('turn_id') == 'old']
    assert {r['model_key'] for r in projected} == {digest(data['config']['model_contract'])}
    assert result['events'][-1]['outcome'] == 'observed'
    assert result['events'][-1]['input_tokens'] == old['events'][-1]['input_tokens']
    assert result['events'][-1]['at'] == old['events'][-1]['at']
    assert data['events'][1]['model_key'] == old['events'][1]['model_key']
    assert 'outcome' not in data['events'][-1]


def test_declared_cache_environment_does_not_replace_policy_configuration():
    from secretary.adaptive_empirical_replay_report import FixedMode
    data = cache_package()
    data['environment_hot_cache_fraction'] = .999
    result = Replay(data, dict(case(100), initial_state=dict(mode='hot', heartbeat_anchor=0)), FixedMode('hot')).run()
    first = next(r for r in result['actions'] if r['kind'] == 'main_start')
    assert first['requests'][0]['cache_read_tokens'] == 10000 * .999
    assert data['config']['hot_cache_fraction'] == .95
