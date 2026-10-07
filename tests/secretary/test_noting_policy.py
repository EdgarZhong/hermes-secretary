"""Pure trigger policy: the two-layer gate, Idle due, and the exact Force boundaries (02 §4.2–4.11).

A23 fixes K = 1,000 tokens, so 64K/66K/128K are exactly 64,000 / 66,000 / 128,000. The
capability comparisons are strict, 128K is never a clamp, and the 1.20 multiplier is applied in
integer tenths so no rounding lands on a stated boundary.
"""

from types import SimpleNamespace

import pytest

from secretary.noting_policy import (
    CAPABILITY_RESERVE_ABOVE_128K,
    CAPABILITY_THRESHOLD_BELOW_64K,
    TASK_PROFILE_NOTING,
    TASK_PROFILE_NOTING_WITH_COMPACTION,
    ContextMeasurement,
    NotingSettings,
    effective_noting_enabled,
    force_capability_failure,
    force_thresholds,
    idle_due,
    idle_task_profile,
    measurement_from_agent,
    noting_settings_from_config,
)


def _settings(enabled=True, delay=500.0, selection=False, selection_threshold=None, compact_after_force=False):
    return NotingSettings(enabled, delay, selection, selection_threshold, compact_after_force)


# ── Two-layer enable gate (02 §4.2) ────────────────────────────────────────


@pytest.mark.parametrize(
    "global_enabled,local_enabled,expected",
    [(True, True, True), (True, False, False), (False, True, False), (False, False, False)],
)
def test_effective_gate_is_global_and_local(global_enabled, local_enabled, expected):
    assert effective_noting_enabled(_settings(enabled=global_enabled), local_enabled) is expected


def test_settings_parse_spec_defaults_and_overrides():
    defaults = noting_settings_from_config({})
    assert (defaults.enabled, defaults.idle_delay_seconds) == (True, 500.0)
    assert defaults.auto_trigger_compaction_enabled is False
    assert defaults.auto_trigger_compaction_threshold_tokens is None
    assert defaults.auto_compact_after_force_noting_idle is False

    parsed = noting_settings_from_config({"noting": {
        "enabled": False, "idle_delay_seconds": 30,
        "auto_trigger_compaction_after_noting": {"enabled": True, "threshold_tokens": 120_000},
        "auto_compact_after_force_noting_idle": True,
    }})
    assert parsed == NotingSettings(False, 30.0, True, 120_000, True)

    malformed = noting_settings_from_config({"noting": {
        "enabled": "no", "idle_delay_seconds": "soon",
        "auto_trigger_compaction_after_noting": {"enabled": True, "threshold_tokens": -5},
    }})
    assert (malformed.enabled, malformed.idle_delay_seconds) == (False, 500.0)
    assert malformed.auto_trigger_compaction_threshold_tokens is None


# ── Idle due (02 §4.5) ────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "started,finished,now,delay,expected",
    [
        (1000.0, 1500.0, 1999.9, 500.0, False),   # just short of the delay
        (1000.0, 1500.0, 2000.0, 500.0, True),    # exactly the delay
        (1000.0, 1500.0, 2500.0, 500.0, True),
        (None, 1500.0, 2500.0, 500.0, True),      # a finish with no recorded start is still idle
        (1500.0, 1500.0, 3000.0, 500.0, False),   # a newer start invalidates the timer
        (1600.0, 1500.0, 3000.0, 500.0, False),
        (1000.0, None, 3000.0, 500.0, False),     # no finish yet
    ],
)
def test_idle_due_boundaries(started, finished, now, delay, expected):
    assert idle_due(started, finished, now=now, delay_seconds=delay) is expected


# ── Force thresholds (02 §4.6, A23) ───────────────────────────────────────


def test_threshold_floor_boundary_is_strict():
    at_64000 = force_thresholds(130_000, 75_000)   # reserve 66,000 -> threshold 64,000
    below_64000 = force_thresholds(129_999, 75_000)  # the 66K reserve floor: threshold 63,999

    assert (at_64000.force_noting_reserve, at_64000.force_noting_threshold) == (66_000.0, 64_000.0)
    assert at_64000.usable and at_64000.auto_compaction_reserve == 55_000
    assert below_64000.force_noting_threshold == 63_999.0
    assert below_64000.capability_failure == CAPABILITY_THRESHOLD_BELOW_64K


def test_trigger_boundary_66k_is_inclusive_and_reserve_floor_holds():
    at_66000 = force_thresholds(132_000, 77_000)  # threshold exactly 66,000
    assert at_66000.force_noting_threshold == 66_000.0
    assert at_66000.measured_usage_triggers(65_999) is False
    assert at_66000.measured_usage_triggers(66_000) is True

    floored = force_thresholds(130_000, 76_000)   # 54,000 * 1.20 = 64,800 -> floor 66,000
    assert floored.force_noting_reserve == 66_000.0
    assert floored.force_noting_threshold == 64_000.0

    scaled = force_thresholds(300_000, 240_000)   # 60,000 * 1.20 = 72,000 (multiplier applies)
    assert scaled.force_noting_reserve == 72_000.0
    assert scaled.force_noting_threshold == 228_000.0


def test_reserve_ceiling_is_strict_and_never_clamps():
    below = force_thresholds(300_000, 193_334)   # 106,666 * 1.20 = 127,999.2
    above = force_thresholds(300_000, 193_333)   # 106,667 * 1.20 = 128,000.4

    assert (below.force_noting_reserve, below.capability_failure) == (127_999.2, None)
    assert above.force_noting_reserve == 128_000.4
    assert above.force_noting_reserve_tenths == 1_280_004  # not clamped to 128K
    assert above.capability_failure == CAPABILITY_RESERVE_ABOVE_128K


def test_exactly_two_capability_failures_with_exact_equality_passing():
    assert force_capability_failure(
        force_noting_reserve_tenths=1_280_000, force_noting_threshold_tenths=640_000) is None
    assert force_capability_failure(
        force_noting_reserve_tenths=1_280_000,
        force_noting_threshold_tenths=639_999) == CAPABILITY_THRESHOLD_BELOW_64K
    assert force_capability_failure(
        force_noting_reserve_tenths=1_280_001,
        force_noting_threshold_tenths=640_000) == CAPABILITY_RESERVE_ABOVE_128K
    assert force_capability_failure(
        force_noting_reserve_tenths=1_280_001,
        force_noting_threshold_tenths=639_999) == CAPABILITY_THRESHOLD_BELOW_64K


def test_threshold_stays_earlier_than_hermes_compaction_and_rejects_bad_inputs():
    thresholds = force_thresholds(200_000, 150_000)
    assert thresholds.invariant_holds
    assert thresholds.force_noting_threshold < thresholds.hermes_auto_compaction_threshold
    assert thresholds.measured_usage_triggers(0) is False
    assert thresholds.measured_usage_triggers("100") is False

    for window, hermes in ((None, 100), (100, None), (0, 100), (100, 0), (True, 100)):
        with pytest.raises(ValueError):
            force_thresholds(window, hermes)

    unusable = force_thresholds(129_999, 75_000)
    assert unusable.measured_usage_triggers(10_000_000) is False


# ── Idle runtime profile (02 §4.10) and the measurement pair ──────────────


def test_idle_task_profile_follows_the_selection_knob():
    measurement = ContextMeasurement(120_000, 200_000, 150_000)
    assert idle_task_profile(_settings(), measurement) == TASK_PROFILE_NOTING
    assert idle_task_profile(_settings(selection=True, selection_threshold=120_000), measurement) \
        == TASK_PROFILE_NOTING_WITH_COMPACTION
    assert idle_task_profile(_settings(selection=True, selection_threshold=120_001), measurement) \
        == TASK_PROFILE_NOTING
    assert idle_task_profile(_settings(selection=True, selection_threshold=100_000), None) \
        == TASK_PROFILE_NOTING
    assert idle_task_profile(_settings(selection=True), measurement) == TASK_PROFILE_NOTING


def test_measurement_from_agent_uses_resolved_compressor_values():
    agent = SimpleNamespace(context_compressor=SimpleNamespace(context_length=200_000, threshold_tokens=150_000))
    measurement = measurement_from_agent(agent, 123_456)
    assert measurement == ContextMeasurement(123_456, 200_000, 150_000)

    assert measurement_from_agent(agent, None) is None
    assert measurement_from_agent(agent, 0) is None
    assert measurement_from_agent(SimpleNamespace(), 100) is None
    assert measurement_from_agent(
        SimpleNamespace(context_compressor=SimpleNamespace(context_length=200_000, threshold_tokens=None)), 100) is None
