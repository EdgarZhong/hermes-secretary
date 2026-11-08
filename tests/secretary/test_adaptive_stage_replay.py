"""V3 replay boundaries: actual knowledge, shared state and two completion clocks."""
from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from secretary.adaptive_empirical_replay import Replay
from secretary.adaptive_empirical_replay_data import known_reminders
from secretary.adaptive_empirical_replay_report import FixedMode, SimpleStage
from secretary.adaptive_empirical_replay_stage import scenario_contract
from tests.secretary.test_adaptive_empirical_replay import ControlledMaintenance, Profile, case, package


def test_future_reminder_demand_is_not_schedule_knowledge():
    data = package()
    data["jobs"].append(dict(data["jobs"][0], id="reminder", source="reminder", start=100, end=101))
    engine = Replay(data, case(), FixedMode("hot"))
    assert not engine._snapshot()["next_reminder_known"]
    assert engine._snapshot()["reminder_due_times"] == []


def test_schedule_registration_available_at_and_revisions_are_respected():
    data = dict(package(), reminder_schedule=[
        dict(schedule_id="schedule", due_at=100, available_at=10),
        dict(schedule_id="schedule", due_at=200, available_at=50),
        dict(schedule_id="schedule", due_at=None, enabled=False, available_at=80)])
    assert not known_reminders(data, 9)["known"]
    assert known_reminders(data, 10)["due_times"] == [100]
    assert known_reminders(data, 49)["due_times"] == [100]
    assert known_reminders(data, 50)["due_times"] == [200]
    assert known_reminders(data, 80)["due_times"] == []


def test_reminder_after_comparison_end_is_still_known_to_current_policy():
    data = dict(package(), reminder_schedule=[dict(schedule_id="later", due_at=500, available_at=0)])
    engine = Replay(data, case(100), FixedMode("hot"))
    assert engine._snapshot()["next_reminder_at"] == 500
    unknown = Replay(data, case(100), FixedMode("hot"), variant="unknown_reminders")
    assert not unknown._snapshot()["next_reminder_known"]


def test_long_noting_planning_clock_does_not_become_main_wait():
    class LongNoting(ControlledMaintenance):
        def _maintenance(self, features, config):
            value = Profile(duration=10)
            value.planning_duration = 100
            return value

    data = package()
    data["events"].append(dict(kind="user_activity", event_id="return", source="user", verified=True, at=20))
    data["jobs"].append(dict(data["jobs"][0], id="return", start=20, end=21))
    result = Replay(data, case(30), LongNoting()).run()
    start = next(row for row in result["actions"] if row["kind"] == "maintenance_start")
    complete = next(row for row in result["actions"] if row["kind"] == "maintenance_planning_end")
    main = next(row for row in result["actions"] if row.get("id") == "return")
    assert start["main_release_at"] == 12
    assert start["planning_complete_at"] == complete["at"] == 102
    assert main["at"] == 20
    assert result["total_wait_seconds"] == 0
    assert result["settled_at"] >= 102  # Do not discard work at the short comparison cutoff.
    assert sum(result["billing_buckets"].values()) == pytest.approx(result["input_equivalent_cost"])


def test_legacy_duration_is_explicitly_not_full_task_evidence():
    result = Replay(package(), case(30), ControlledMaintenance()).run()
    start = next(row for row in result["actions"] if row["kind"] == "maintenance_start")
    assert start["planning_duration_source"] == "legacy_main_block_proxy_unknown_complete_task"


def test_actual_cancel_cancels_planning_clock_and_does_not_drop_paid_cost():
    class LongNoting(ControlledMaintenance):
        def _maintenance(self, features, config):
            value = Profile(duration=10)
            value.planning_duration = 100
            return value
    data = package()
    data["events"].append(dict(kind="user_activity", event_id="stop", source="user", verified=True,
                               at=5, activity="cancel"))
    result = Replay(data, case(30), LongNoting()).run()
    assert not any(r["kind"] == "maintenance_planning_end" for r in result["actions"])
    assert result["input_equivalent_cost"] == 100
    assert result["final_context"] == 10000


def test_switch_hot_inherits_overdue_anchor_and_merges_to_one_immediate_hb():
    phase = dict(case(50), initial_state=dict(heartbeat_anchor=-100, mode="business"))
    result = Replay(package(), phase, FixedMode("hot")).run()
    hb = [r for r in result["actions"] if r["kind"] == "main_start" and r["source"] == "heartbeat"]
    assert result["initial_heartbeat_anchor"] == -100
    assert len(hb) == 1
    assert hb[0]["at"] == phase["start"]


def test_whole_turn_template_preserves_calls_duration_output_association():
    data = package()
    data["jobs"] += [dict(data["jobs"][0], id="small", source="heartbeat", calls=1, output_tokens=3, duration=1),
                     dict(data["jobs"][0], id="tail", source="heartbeat", calls=9, output_tokens=900, duration=90)]
    engine = Replay(data, case(), FixedMode("hot"))
    draw = engine._template("heartbeat")
    assert (draw["calls"], draw["output_tokens"], draw["duration"]) in ((1, 3, 1), (9, 900, 90))
    assert draw["source_job_id"] in ("small", "tail")


def test_long_history_is_not_truncated_by_recent_dense_heartbeat_rows():
    data = package()
    data["events"] += [dict(event_id="hb:"+str(i), kind="request", source="heartbeat", at=1.1+i/10000) for i in range(2100)]
    engine = Replay(data, case(), FixedMode("hot"))
    assert any(row["event_id"] == "user:0" for row in engine._known_history())


def test_late_import_rechecks_at_knowledge_boundary_without_new_user():
    data = dict(package(), maintenance_samples=[dict(kind="maintenance_sample", event_id="late", at=0, available_at=10)],
                knowledge_events=[dict(kind="history_updated", event_id="import", at=10, available_at=10)])
    class Observe(FixedMode):
        def __init__(self):
            super().__init__("business")
            self.inputs = []
        def decide(self, snapshot, history, config):
            self.inputs.append((snapshot["now"], deepcopy(history)))
            return super().decide(snapshot, history, config)
    policy = Observe()
    Replay(data, case(30), policy).run()
    assert [t for t, _ in policy.inputs] == [2, 10]
    assert not any(r["event_id"] == "late" for r in policy.inputs[0][1])
    assert any(r["event_id"] == "late" for r in policy.inputs[1][1])


def test_simple_stage_uses_hot_protection_then_frozen_policy():
    class Baseline(FixedMode):
        def __init__(self):
            super().__init__("business")
            self.calls = 0
        def decide(self, *args):
            self.calls += 1
            return super().decide(*args)
    baseline = Baseline()
    simple = SimpleStage(baseline)
    data = package()
    assert simple.decide(dict(now=2), data["events"], data["config"])["mode"] == "hot"
    assert baseline.calls == 0
    assert simple.decide(dict(now=2000), data["events"], data["config"])["mode"] == "business"
    assert baseline.calls == 1


def test_sixteen_expectations_freeze_input_hashes_without_running_policy(tmp_path):
    legacy, afternoon = tmp_path/"legacy.json", tmp_path/"afternoon.json"
    legacy.write_text(json.dumps(package()))
    afternoon.write_text("{}")
    contract = scenario_contract(legacy, afternoon)
    assert len(contract["scenarios"]) == 16
    assert contract["candidate_runs"] == 0
    assert contract["comparison"]["policies"] == ["old-online", "V2", "simple-stage", "V3"]
    assert contract["comparison"]["windows"] == ["original", "6h", "24h", "common-cutoff"]


def test_simulated_heartbeat_receipts_do_not_reseed_the_workload_generator():
    data = package()
    data['jobs'].append(dict(data['jobs'][0], id='observed-hb', source='heartbeat',
                             calls=1, output_tokens=3, duration=1))
    engine = Replay(data, case(200), FixedMode('hot'))
    original = deepcopy(engine.template_pool['heartbeat'])
    engine.run()
    assert engine.template_pool['heartbeat'] == original


def test_formal_replay_policy_sees_only_the_nearest_known_instant():
    data = dict(package(), reminder_schedule=[dict(schedule_id=str(t), due_at=t, available_at=0)
                                             for t in (100, 200, 300)])
    engine = Replay(data, case(400), FixedMode('hot'))
    assert engine._snapshot()['reminder_due_times'] == [100]
    assert engine._snapshot()['next_reminder_at'] == 100


def test_case_uses_the_actual_known_reasoning_contract_without_seeing_future_switch():
    data = package()
    identity = dict(provider='test', model='same')
    data['config']['model_identity'] = identity
    before = dict(provider='test', model='same', context_length=20000, threshold_tokens=18000,
                  reasoning_config=dict(effort='high'))
    data['jobs'][0]['terminal_event'] = dict(model_identity=identity, model_contract=before,
        model_key='known-high', at=1, event_id='known-switch')
    engine = Replay(data, case(400), FixedMode('hot'))
    assert engine._snapshot()['model_key'] == 'known-high'
    assert engine.cfg['model_contract'] == before
    data['jobs'][0]['terminal_event']['available_at'] = 999
    hidden = Replay(data, case(400), FixedMode('hot'))
    assert hidden._snapshot().get('model_key') != 'known-high'


def test_external_model_switch_is_observed_before_next_policy_boundary_and_anchor_survives():
    data = package()
    identity = dict(provider='test', model='same')
    data['config']['model_identity'] = identity
    data['jobs'].append(dict(data['jobs'][0], id='switch', source='user', start=10, end=11,
        terminal_event=dict(event_id='switch-end', at=11, model_identity=identity,
            model_key='new-contract', model_contract=dict(provider='test', model='same',
            context_length=20000, threshold_tokens=18000))))
    engine = Replay(data, case(40), FixedMode('business'))
    initial_anchor = engine.anchor
    result = engine.run()
    assert engine.snapshot_base['model_key'] == 'new-contract'
    assert engine.anchor == initial_anchor
    assert any(r['kind'] == 'model_contract_change' for r in result['actions'])
    assert all(r.get('model_key') == 'new-contract' for r in engine.history if r.get('turn_id') == 'switch')
