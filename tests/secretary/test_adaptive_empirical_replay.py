"""Chronological replay mechanisms, with a separate actual-policy contract check."""
from copy import deepcopy
from dataclasses import dataclass, field
import json
from types import SimpleNamespace

import pytest

from secretary.adaptive_empirical_replay import Replay
from secretary.adaptive_empirical_replay_data import _jobs, coverage_at, normalized_components, past_events
from secretary.adaptive_empirical_replay_report import FixedMode, audit_case


def package():
    user = dict(event_id="user:0", kind="user_activity", source="user", verified=True, at=0)
    turn = dict(event_id="turn:old", kind="turn_end", source="user", verified=True, at=1,
                duration_seconds=1, context_tokens=10000, context_epoch="old", model_key="m")
    job = dict(id="old", start=0, end=1, source="user", duration=1, calls=1,
               growth_tokens=0, first_suffix_tokens=0, output_tokens=1,
               context_tokens=10000, epoch="old", first_input=10000)
    return dict(events=[user, turn], jobs=[job], maintenance_samples=[], cutoff=1000,
                config=dict(hot_interval_seconds=60, business_interval_seconds=300,
                            cache_ratio=.1, output_ratio=5, cache_ttl_seconds=120,
                            hot_cache_fraction=.95, heartbeat_fresh_tokens=10, heartbeat_output_tokens=1),
                snapshot=dict(model_key="m", context_tokens=10000, native_threshold_tokens=80000,
                              heartbeat_status="active", heartbeat_mode="business"))


def case(end=200):
    return dict(id="test", start=2, end=end, expectation_type="conditional_plateau", expected="mechanism")


@dataclass
class Profile:
    cost: float = 100
    duration: float = 10
    retained: float = .1
    recovery: float = 0
    diagnostics: dict = field(default_factory=dict)
    cancellation_scenarios: tuple = ()
    scenarios: tuple = ()


class ControlledMaintenance:
    """Only controls the simulator action input, not the production policy test."""
    def decide(self, snapshot, history, config):
        previous = any(r["kind"] == "maintenance_end" for r in history)
        return dict(mode="business", threshold_tokens=None if previous else 1,
                    delay_seconds=None if previous else 0, fallback=False, diagnostics={})

    def _settings(self, config):
        return config

    def build_features(self, snapshot, history, config):
        return {}

    def _maintenance(self, features, config):
        return Profile()


def test_divergent_context_is_not_overwritten_by_historical_endpoint():
    data = package()
    data["jobs"].append(dict(id="new", start=100, end=105, source="user", duration=5,
                             calls=1, growth_tokens=20, first_suffix_tokens=10, output_tokens=2,
                             context_tokens=50000, epoch="old", first_input=49980))
    result = Replay(data, case(), ControlledMaintenance()).run()
    assert result["counts"]["completed"] == 1
    assert result["final_context"] == 1030
    assert result["final_context"] != data["jobs"][-1]["context_tokens"]


def test_hb_is_generated_per_strategy_not_replayed_as_external_demand():
    data = package()
    hot = Replay(data, case(), FixedMode("hot")).run()
    business = Replay(data, case(), FixedMode("business")).run()
    assert hot["counts"]["heartbeat"] > business["counts"]["heartbeat"]
    assert hot["input_equivalent_cost"] > business["input_equivalent_cost"]


def test_arrival_invalidates_unaccepted_plan():
    class Delayed(ControlledMaintenance):
        def decide(self, snapshot, history, config):
            value = super().decide(snapshot, history, config)
            value["delay_seconds"] = 30
            return value
    data = package()
    data["events"].append(dict(event_id="return", kind="user_activity", source="user", verified=True, at=10))
    result = Replay(data, case(100), Delayed()).run()
    assert result["counts"]["maintenance"] == 0


def test_late_sample_and_future_exposure_not_available_early():
    data = package()
    data["events"].append(dict(event_id="coverage", kind="coverage", source="user", verified=True,
                                start_at=0, end_at=1000, at=1000))
    data["maintenance_samples"].append(dict(event_id="late", kind="maintenance_sample", at=5, available_at=100))
    history = past_events(data, 50)
    assert not any(r["event_id"] == "late" for r in history)
    assert coverage_at(data["events"], 50)[0]["end_at"] == 50
    assert max(r["at"] for r in history) <= 50


def test_prior_epoch_endpoint_does_not_become_new_epoch_initial_state():
    data = package()
    data["jobs"].append(dict(id="new", start=3, end=8, source="user", duration=5,
                             calls=1, growth_tokens=20, first_suffix_tokens=0, output_tokens=1,
                             context_tokens=1000, epoch="new", first_input=980))
    result = Replay(data, case(20), FixedMode("business")).run()
    assert result["initial_context"] == 980
    assert result["final_context"] == 1000


def test_native_overflow_is_never_used_to_inflate_no_maintenance_cost():
    data = package()
    data["snapshot"]["native_threshold_tokens"] = 10005
    with pytest.raises(ValueError, match="Native capacity"):
        Replay(data, case(200), FixedMode("hot")).run()


def test_real_policy_is_called_with_only_visible_numeric_inputs():
    from secretary import adaptive_policy
    class Observed:
        def decide(self, snapshot, history, config):
            assert all(max(r["at"], r.get("available_at", r["at"])) <= snapshot["now"] for r in history)
            return adaptive_policy.decide(snapshot, history, config)
    result = Replay(package(), case(20), Observed()).run()
    assert len(result["decisions"]) == 1
    assert result["decisions"][0]["decision"]["fallback"]


def test_negative_prompt_jump_is_unknown_not_observed_zero_growth():
    rows = [dict(kind="request", event_id="a", at=1, turn_id="x", input_tokens=100, output_tokens=2),
            dict(kind="request", event_id="b", at=2, turn_id="x", input_tokens=90, output_tokens=2),
            dict(kind="turn_end", event_id="turn:x", at=3, source="user", duration_seconds=3,
                 context_tokens=90, context_epoch="e")]
    assert _jobs(rows)[0]["growth_tokens"] is None


def test_whole_segment_no_maintenance_is_a_counterexample_not_a_pass():
    data, expectation = package(), case(20)
    expectation["expectation_type"] = "whole_segment_opportunity"
    result = Replay(data, expectation, FixedMode("business")).run()
    report = audit_case(expectation, result, [])
    assert report["automated_status"] == "counterexample"
    assert "missed_whole_segment_maintenance_opportunity" in report["automatic_errors"]


def test_case_cut_between_turns_does_not_fabricate_a_new_main_end_decision():
    data = package()
    middle = dict(case(100), start=20)
    result = Replay(data, middle, ControlledMaintenance()).run()
    assert result["decisions"] == []
    assert result["counts"]["maintenance"] == 0


def test_explicit_real_cancel_releases_main_and_preserves_paid_cost():
    data = package()
    data["events"].append(dict(event_id="stop", kind="user_activity", source="user", verified=True,
                                at=5, activity="cancel"))
    result = Replay(data, case(20), ControlledMaintenance()).run()
    assert result["counts"]["failed"] == 1
    assert result["final_context"] == 10000
    assert result["input_equivalent_cost"] == 100
    assert any(a["kind"] == "actual_user_cancel" and a["at"] == 5 for a in result["actions"])


def test_real_arrival_counts_collision_before_main_admission_source_is_known():
    data = package()
    data["events"].append(dict(event_id="queued", kind="user_activity", source="user", verified=True, at=5))
    result = Replay(data, case(20), ControlledMaintenance()).run()
    assert result["counts"]["collisions"] == 1
    assert result["max_wait_seconds"] == 7


def test_actual_cancel_consumes_formal_historical_paid_receipt_branch():
    class WithPaidCancel(ControlledMaintenance):
        def _maintenance(self, features, config):
            return Profile(cancellation_scenarios=(Profile(cost=30, duration=3, diagnostics={"receipt": "paid-stop"}),))
    data = package()
    data["events"].append(dict(event_id="stop", kind="user_activity", source="user", verified=True,
                                at=5, activity="cancel"))
    result = Replay(data, case(20), WithPaidCancel()).run()
    stop = next(a for a in result["actions"] if a["kind"] == "actual_user_cancel")
    assert result["input_equivalent_cost"] == 30
    assert stop["cancellation_cost_source"] == {"receipt": "paid-stop"}
    assert result["final_context"] == 10000


def test_missing_target_metadata_cannot_default_to_this_historical_target():
    row = dict(kind="maintenance_sample", event_id="c", operation_id="c", component="compaction",
               at=10, start_at=0, verified=True, proof={"source": "native_receipt"})
    result = normalized_components({"samples": [row]}, {"turns": [], "compactions": []}, {})[0]
    assert result["proof"]["source_conversation_evidence"] == "foreign_or_unproven_component_pool"
    assert result["proof"]["source_session_hash"] is None


def test_unrecognized_same_target_prefix_cannot_gain_source_eligibility():
    engine = Replay(package(), case(20), FixedMode("business"), component_pool="same-target")
    assert not engine._in_pool(dict(kind="maintenance_sample", proof={"source_conversation_evidence": "same_target_unverified_guess"}))
    assert engine._in_pool(dict(kind="maintenance_sample", proof={"source_conversation_evidence": "same_target_parent_chain"}))


def test_stop_settles_actual_blocking_wait_and_releases_same_queued_work():
    data = package()
    data["events"].extend([
        dict(event_id="new", kind="user_activity", source="user", verified=True, at=4),
        dict(event_id="stop", kind="user_activity", source="user", verified=True, at=5, activity="cancel")])
    data["jobs"].append(dict(id="new", start=4, end=6, source="user", duration=2,
                             calls=1, growth_tokens=20, first_suffix_tokens=10, output_tokens=2,
                             context_tokens=50000, epoch="old", first_input=49980))
    result = Replay(data, case(20), ControlledMaintenance()).run()
    assert result["counts"]["collisions"] == 1
    assert result["total_wait_seconds"] == 1
    assert result["final_context"] == 10030
    arrival = next(a for a in result["actions"] if a["kind"] == "real_arrival_collision")
    assert arrival["settled"] and arrival["release_at"] == 5


def test_mechanical_failure_stress_retains_paid_cost_without_fake_reduction():
    class FailedComponent(ControlledMaintenance):
        def _maintenance(self, features, config):
            failed = Profile(cost=55, duration=8, retained=1, diagnostics={"scenario": {"outcome": "failed"}})
            return Profile(scenarios=(Profile(), failed))
    result = Replay(package(), case(20), FailedComponent(), variant="mechanical_failure").run()
    assert result["counts"]["failed"] == 1
    assert result["input_equivalent_cost"] == 55
    assert result["final_context"] == 10000


def test_current_model_component_pool_keeps_provider_and_option_identity():
    data = package()
    data["config"]["model_identity"] = dict(provider="one", model="option-900k")
    engine = Replay(data, case(20), FixedMode("business"), component_pool="gpt-only")
    assert not engine._in_pool(dict(kind="maintenance_sample", model_identity=dict(provider="two", model="option-900k")))
    assert not engine._in_pool(dict(kind="maintenance_sample", model_identity=dict(provider="one", model="option")))
    assert engine._in_pool(dict(kind="maintenance_sample", model_identity=dict(provider="one", model="option-900k")))


def test_experience_audit_uses_known_work_end_across_model_contracts():
    data = package()
    data["cutoff"] = 5000
    data["events"][1].update(at=1000, duration_seconds=1000, model_key="previous-contract")
    data["jobs"][0].update(end=1000, duration=1000)
    phase = dict(case(1100), start=1001)
    result = Replay(data, phase, ControlledMaintenance()).run()
    action = next(a for a in result["actions"] if a["kind"] == "maintenance_start")
    assert action["experience_timing_guard"]["last_known_user_work_end"] == 1000
    assert action["experience_timing_guard"]["actual_quiet_seconds"] == 1
    audit = audit_case(phase, result, [])
    assert "insufficient_quiet_after_known_user_work_end" in audit["automatic_errors"]


def test_unreconstructed_coverage_sensitivity_does_not_relabel_future_witness():
    data = package()
    data["events"].append(dict(event_id="coverage", kind="coverage", source="user", verified=True,
                                at=1000, start_at=0, end_at=1000))
    engine = Replay(data, case(100), FixedMode("business"), variant="raw_coverage_only")
    engine.now = 50
    assert not any(row["kind"] == "coverage" for row in engine._known_history())
