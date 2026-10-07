"""noting config: shipped defaults, structure validation, and the retired review switch.

A16 / 02 §5.1: the old ``auxiliary.background_review`` switch and its routing block are removed
from the shipped defaults and have no enabling path left; ``noting`` carries the 02 §4.1 block.
"""

import pytest

from agent.background_review import load_background_review_settings
from hermes_cli.config import DEFAULT_CONFIG, validate_config_structure
from hermes_constants import get_hermes_home
from secretary.noting_policy import resolve_noting_settings


def test_default_config_carries_the_spec_noting_block():
    block = DEFAULT_CONFIG["noting"]
    assert block["enabled"] is True
    assert block["idle_delay_seconds"] == 500
    assert block["auto_trigger_compaction_after_noting"] == {"enabled": False, "threshold_tokens": None}
    assert block["auto_compact_after_force_noting_idle"] is False


def test_retired_background_review_switch_is_removed_not_defaulted_off():
    assert "background_review" not in DEFAULT_CONFIG["auxiliary"]
    assert load_background_review_settings() == (False, {})


def test_noting_settings_follow_the_user_config_file():
    (get_hermes_home() / "config.yaml").write_text(
        "noting:\n  enabled: false\n  idle_delay_seconds: 42\n", encoding="utf-8")
    settings = resolve_noting_settings()
    assert settings.enabled is False
    assert settings.idle_delay_seconds == 42.0


def test_old_review_switch_in_a_user_config_has_no_effect():
    (get_hermes_home() / "config.yaml").write_text(
        "auxiliary:\n  background_review:\n    enabled: true\n", encoding="utf-8")
    assert load_background_review_settings() == (False, {})


@pytest.mark.parametrize("block", [
    {"noting": "on"},
    {"noting": {"idle_delay_seconds": -1}},
    {"noting": {"idle_delay_seconds": "soon"}},
    {"noting": {"auto_trigger_compaction_after_noting": "yes"}},
    {"noting": {"auto_trigger_compaction_after_noting": {"threshold_tokens": 0}}},
    {"noting": {"auto_trigger_compaction_after_noting": {"threshold_tokens": "lots"}}},
])
def test_config_structure_reports_malformed_noting(block):
    issues = validate_config_structure(block)
    assert [issue for issue in issues if "noting" in issue.message]


def test_config_structure_accepts_the_spec_block():
    assert validate_config_structure({"noting": DEFAULT_CONFIG["noting"]}) == []
    assert validate_config_structure({}) == []
