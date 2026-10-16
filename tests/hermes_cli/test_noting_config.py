"""noting config: shipped defaults, structure validation, and the retired review switch.

A16 / 02 §5.1: the old ``auxiliary.background_review`` switch and its routing block are removed
from the shipped defaults and have no enabling path left; ``noting`` follows 07 §6.3, with independent Scheduler and fail-closed validation.
"""

import pytest

from agent.background_review import load_background_review_settings
from hermes_cli.config import DEFAULT_CONFIG, validate_config_structure
from hermes_constants import get_hermes_home
from secretary.noting_policy import noting_settings_from_config, resolve_noting_settings, scheduler_settings_from_config


def test_default_config_carries_the_spec_noting_block():
    block = DEFAULT_CONFIG["noting"]
    assert block["enabled"] is True
    assert block["idle"] == {"enabled": False, "delay_seconds": 500, "threshold_tokens": None}
    assert block["persistence_proposal"] == {"char_threshold": 12000, "entry_threshold": 60}
    assert DEFAULT_CONFIG["scheduler"] == {"enabled": True}
    for key in ("idle_delay_seconds", "auto_trigger_compaction_after_noting", "auto_compact_after_force_noting_idle"):
        assert key not in block


def test_retired_background_review_switch_is_removed_not_defaulted_off():
    assert "background_review" not in DEFAULT_CONFIG["auxiliary"]
    assert load_background_review_settings() == (False, {})


def test_noting_settings_follow_the_user_config_file():
    (get_hermes_home() / "config.yaml").write_text(
        "noting:\n  enabled: false\n  idle:\n    delay_seconds: 42\n", encoding="utf-8")
    settings = resolve_noting_settings()
    assert settings.enabled is False
    assert settings.idle_delay_seconds == 42.0
    assert not settings.configuration_failure and not settings.idle_enabled


def test_old_review_switch_in_a_user_config_has_no_effect():
    (get_hermes_home() / "config.yaml").write_text(
        "auxiliary:\n  background_review:\n    enabled: true\n", encoding="utf-8")
    assert load_background_review_settings() == (False, {})


@pytest.mark.parametrize("block", [
    {"noting": "on"},
    {"noting": {"idle": {"delay_seconds": -1}}},
    {"noting": {"idle": {"delay_seconds": "soon"}}},
    {"noting": {"idle": {"enabled": "yes"}}},
    {"noting": {"idle": {"enabled": True, "threshold_tokens": 0}}},
    {"noting": {"idle": {"enabled": True, "threshold_tokens": "lots"}}},
])
def test_config_structure_reports_malformed_noting(block):
    issues = validate_config_structure(block)
    assert [issue for issue in issues if "noting" in issue.message.lower()]
    settings = noting_settings_from_config(block)
    assert not settings.enabled and settings.configuration_failure
    assert scheduler_settings_from_config(block).enabled


def test_config_structure_accepts_the_spec_block():
    assert validate_config_structure({"noting": DEFAULT_CONFIG["noting"]}) == []
    assert validate_config_structure({}) == []


@pytest.mark.parametrize("key,replacement", [
    ("idle_delay_seconds", "noting.idle.delay_seconds"),
    ("auto_trigger_compaction_after_noting", "noting.idle.enabled"),
    ("auto_compact_after_force_noting_idle", "noting.idle.enabled"),
])
def test_retired_noting_keys_fail_closed_with_explicit_replacement(key, replacement):
    block = {"noting": {key: False}}
    issues = validate_config_structure(block)
    assert any(key in issue.hint and replacement in issue.hint for issue in issues)
    settings = noting_settings_from_config(block)
    assert not settings.enabled and not settings.idle_enabled
    assert "removed" in settings.configuration_failure
    assert scheduler_settings_from_config(block).enabled
