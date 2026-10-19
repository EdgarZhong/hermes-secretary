"""C4: profile config, native prompt modules and human command boundaries (07 §6.3/8)."""

from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from secretary.noting_policy import (
    NotingSettings, SchedulerSettings, effective_noting_enabled, force_thresholds,
    noting_settings_from_config, scheduler_settings_from_config,
)


@pytest.mark.parametrize("noting,scheduler", [(True, True), (True, False), (False, True), (False, False)])
def test_independent_config_matrix_and_local_participation(noting, scheduler):
    config = {"noting": {"enabled": noting}, "scheduler": {"enabled": scheduler}}
    settings = noting_settings_from_config(config)
    assert settings.enabled is noting
    assert scheduler_settings_from_config(config).enabled is scheduler
    assert effective_noting_enabled(settings, False) is False
    assert effective_noting_enabled(settings, True) is noting
    assert settings.idle_enabled is False


def test_new_defaults_and_idle_dual_configuration():
    from hermes_cli.config_defaults import DEFAULT_CONFIG
    assert noting_settings_from_config(DEFAULT_CONFIG) == NotingSettings()
    assert scheduler_settings_from_config(DEFAULT_CONFIG) == SchedulerSettings()
    settings = noting_settings_from_config({"noting": {"idle": {
        "enabled": True, "delay_seconds": 0, "threshold_tokens": 100_000}}})
    assert (settings.enabled, settings.idle_enabled, settings.idle_delay_seconds,
            settings.idle_threshold_tokens) == (True, True, 0, 100_000)
    disabled = noting_settings_from_config({"noting": {"enabled": False, "idle": {
        "enabled": True, "threshold_tokens": 100_000}}})
    assert disabled.idle_enabled is False


@pytest.mark.parametrize("block,repair", [
    (None, "noting must be a mapping"),
    ({"enabled": "garbage"}, "noting.enabled"),
    ({"idle": []}, "noting.idle"),
    ({"idle": {"enabled": True}}, "noting.idle.threshold_tokens"),
    ({"idle": {"threshold_tokens": True}}, "noting.idle.threshold_tokens"),
    ({"idle": {"delay_seconds": -1}}, "noting.idle.delay_seconds"),
    ({"idle": {"delay_seconds": float("nan")}}, "noting.idle.delay_seconds"),
    ({"idle": {"delay_seconds": float("inf")}}, "noting.idle.delay_seconds"),
    ({"persistence_proposal": {"entry_threshold": 0}}, "noting.persistence_proposal.entry_threshold"),
    ({"persistence_proposal": {"char_threshold": True}}, "noting.persistence_proposal.char_threshold"),
    ({"idle_delay_seconds": 5}, "noting.idle.delay_seconds"),
    ({"auto_trigger_compaction_after_noting": {}}, "noting.idle.threshold_tokens"),
    ({"auto_compact_after_force_noting_idle": False}, "noting.idle.threshold_tokens"),
])
def test_bad_noting_config_disables_only_noting_and_explains_repair(block, repair):
    from hermes_cli.config import validate_config_structure
    config = {"noting": block}
    settings = noting_settings_from_config(config)
    assert not settings.enabled
    assert repair in settings.configuration_failure
    assert scheduler_settings_from_config(config).enabled
    issues = validate_config_structure(config)
    assert any(repair in issue.hint for issue in issues)


@pytest.mark.parametrize("block", [None, [], {"enabled": "maybe"}, {"enabled": 1}])
def test_bad_scheduler_config_is_isolated(block):
    from hermes_cli.config import validate_config_structure
    config = {"scheduler": block}
    settings = scheduler_settings_from_config(config)
    assert not settings.enabled
    assert "scheduler" in settings.configuration_failure
    assert noting_settings_from_config(config).enabled
    assert any("Scheduler" in issue.message for issue in validate_config_structure(config))


def test_native_idle_conflict_applies_to_global_noting_even_with_noting_idle_off():
    config = {"compression": {"idle_compact_after_seconds": 30}}
    settings = noting_settings_from_config(config)
    assert not settings.enabled
    assert settings.configuration_failure == "idle_compaction_conflict"
    assert scheduler_settings_from_config(config).enabled
    config["noting"] = {"enabled": False}
    assert not noting_settings_from_config(config).configuration_failure
    assert config["compression"]["idle_compact_after_seconds"] == 30
    thresholds = force_thresholds(200_000, 160_000)
    assert thresholds.force_noting_threshold == 134_000
    assert thresholds.measured_usage_triggers(134_000)
    assert not thresholds.measured_usage_triggers(133_999)


def agent(*, main=True, noting=True, scheduler=True, session_search=True):
    names = {"conversation_history"} if main else set()
    if scheduler:
        names.add("scheduler")
    if noting:
        names.add("notebook_show")
    if session_search:
        names.add("session_search")
    return SimpleNamespace(
        valid_tool_names=names, _secretary_main_read_eligible=main,
        _secretary_notebook_read_enabled=noting, _secretary_scheduler_enabled=scheduler,
        _task_completion_guidance=False, _parallel_tool_call_guidance=False,
        _tool_use_enforcement=False, _execution_guidance=False, model="test-model",
        platform="cli", _secretary_noting_child=False,
    )


@pytest.mark.parametrize("noting,scheduler", [(True, True), (True, False), (False, True), (False, False)])
def test_prompt_matrix_at_native_guidance_assembly(noting, scheduler):
    from agent.system_prompt import (
        HISTORY_SEARCH_GUIDANCE, SCHEDULER_GUIDANCE, SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE,
        SECRETARY_SESSION_SEARCH_GUIDANCE, _guidance_parts,
    )
    current = agent(noting=noting, scheduler=scheduler)
    parts = _guidance_parts(current)
    assert HISTORY_SEARCH_GUIDANCE in parts
    assert (SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE in parts) is noting
    assert (SCHEDULER_GUIDANCE in parts) is scheduler
    assert SECRETARY_SESSION_SEARCH_GUIDANCE in "\n".join(filter(None, parts))
    current._secretary_noting_local_enabled = False
    assert _guidance_parts(current) == parts


def test_noting_main_skips_finishing_the_job_guidance():
    """The universal block contradicts SOUL's orchestration rule on a Noting Main."""
    from agent.prompt_builder import TASK_COMPLETION_GUIDANCE
    from agent.system_prompt import _guidance_parts

    noting = agent(noting=True)
    noting._task_completion_guidance = True
    assert TASK_COMPLETION_GUIDANCE not in _guidance_parts(noting)

    plain = agent(noting=False)
    plain._task_completion_guidance = True
    assert TASK_COMPLETION_GUIDANCE in _guidance_parts(plain)


def test_native_search_guidance_unchanged_for_auxiliary_and_unavailable_search_absent():
    from agent.prompt_builder import SESSION_SEARCH_GUIDANCE
    from agent.system_prompt import SECRETARY_SESSION_SEARCH_GUIDANCE, _tool_guidance_block, _guidance_parts
    assert _tool_guidance_block(agent(main=False)) == SESSION_SEARCH_GUIDANCE
    main = agent(session_search=False)
    assert SECRETARY_SESSION_SEARCH_GUIDANCE not in "\n".join(filter(None, _guidance_parts(main)))


def test_scheduler_guidance_never_claims_a_missing_dispatch_tool():
    from agent.system_prompt import SCHEDULER_GUIDANCE, _guidance_parts
    current = agent()
    current.valid_tool_names.remove("scheduler")
    assert SCHEDULER_GUIDANCE not in _guidance_parts(current)


def test_cron_schema_copy_manifest_search_and_scope_preserve_native_global_schema():
    from agent.secretary_prompt import (
        SECRETARY_CRONJOB_DESCRIPTION, SECRETARY_CRON_SCHEDULE_NOTE,
        apply_cron_schema_guidance, apply_scoped_cron_search_guidance, cron_schema_scope,
    )
    from tools.cronjob_tools import CRONJOB_SCHEMA
    native = deepcopy(CRONJOB_SCHEMA)
    manifest = {"type": "function", "function": {"name": "tool_search", "description": "Tools:\n- cronjob_manage: native cron description"}}
    tools = [{"type": "function", "function": CRONJOB_SCHEMA}, manifest]
    result = apply_cron_schema_guidance(tools, enabled=True)
    assert result[0]["function"]["description"] == SECRETARY_CRONJOB_DESCRIPTION
    assert SECRETARY_CRON_SCHEDULE_NOTE in result[0]["function"]["parameters"]["properties"]["schedule"]["description"]
    assert CRONJOB_SCHEMA == native
    assert tools[1] == manifest
    assert "Manage independent scheduled Hermes Agent jobs" in result[1]["function"]["description"]
    assert apply_cron_schema_guidance(result, enabled=False)[0]["function"] == native
    search = json.dumps({"tools": {"cronjob_manage": {"description": "native"}}})
    for main, scheduler, child, expected in [(True, True, False, True), (True, False, False, False),
                                            (False, True, False, False), (True, True, True, False)]:
        current = agent(main=main, scheduler=scheduler)
        current._secretary_noting_child = child
        with cron_schema_scope(current):
            actual = json.loads(apply_scoped_cron_search_guidance(search))
        assert (actual["tools"]["cronjob_manage"]["description"] == SECRETARY_CRONJOB_DESCRIPTION) is expected
    assert apply_scoped_cron_search_guidance(search) == search


def test_profile_owned_settings_do_not_read_ambient_home(tmp_path, monkeypatch):
    from secretary.noting_scope import settings_for_db, scheduler_settings_for_db
    ambient = tmp_path / "ambient"
    owner = tmp_path / "owner"
    ambient.mkdir()
    owner.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(ambient))
    (ambient / "config.yaml").write_text("noting:\n  enabled: false\nscheduler:\n  enabled: true\n")
    (owner / "config.yaml").write_text("noting:\n  enabled: true\nscheduler:\n  enabled: false\n")
    db = SimpleNamespace(db_path=owner / "state.db")
    assert settings_for_db(db).enabled
    assert not scheduler_settings_for_db(db).enabled


def test_slash_off_has_no_memo_block_and_proposal_uses_current_complete_snapshot(tmp_path):
    from hermes_cli.cli_secretary_commands import (
        PERSISTENCE_PROPOSAL_INSTRUCTION, notebook_command, noting_command, propose_persistence_command,
    )
    from secretary.notebook_store import NotebookStore
    from tests.hermes_state._secretary_notebook_harness import add, make, open_notebook_db, ref_of
    (tmp_path / "config.yaml").write_text("noting:\n  enabled: true\n")
    db = open_notebook_db(tmp_path / "state.db")
    try:
        make(db, "s", source="cli")
        add(db, "s", "Discuss a meaningful question", "m1")
        ref = ref_of(db, "s")
        store = NotebookStore(db, ref, anchor_message_uid="m1")
        snapshot_id = store.commit(termination={"type": "finish_noting", "reason": "No changes needed."})["snapshot_id"]
        result = noting_command(db, "s", "off")
        assert result.output == "Background Noting is off for this Conversation."
        assert not db.notebook_local_enabled(ref)
        assert "Notebook" in notebook_command(db, "s").output
        result = propose_persistence_command(db, "s", "Only draft relevant items")
        assert result.prompt.startswith(PERSISTENCE_PROPOSAL_INSTRUCTION)
        assert snapshot_id in result.prompt
        assert "Only draft relevant items" in result.prompt
        assert db.notebook_current(ref)["snapshot_id"] == snapshot_id
        assert not db.notebook_local_enabled(ref)
    finally:
        db.close()


def test_slash_reports_specific_configuration_repair(tmp_path):
    from hermes_cli.cli_secretary_commands import notebook_command, noting_command, propose_persistence_command
    (tmp_path / "config.yaml").write_text("noting:\n  idle_delay_seconds: 50\n")
    db = SimpleNamespace(db_path=tmp_path / "state.db")
    for result in (notebook_command(db, "s"), noting_command(db, "s", "off"),
                   propose_persistence_command(db, "s")):
        assert "noting.idle.delay_seconds" in result.output
        assert not result.prompt


def test_unreadable_profile_fails_closed_without_guessing_defaults(tmp_path):
    from secretary.noting_scope import settings_for_db, scheduler_settings_for_db
    (tmp_path / "config.yaml").write_text("noting: [broken\n")
    db = SimpleNamespace(db_path=tmp_path / "state.db")
    assert not settings_for_db(db).enabled
    assert not scheduler_settings_for_db(db).enabled


def test_platform_cron_hint_is_scheduler_scoped():
    from agent.prompt_builder import SECRETARY_LOCAL_CRON_DELIVERY_APPEND
    from agent.system_prompt import platform_hint
    for main, scheduler in ((True, True), (True, False), (False, True), (False, False)):
        current = agent(main=main, noting=False, scheduler=scheduler)
        hint = platform_hint(current)
        assert (SECRETARY_LOCAL_CRON_DELIVERY_APPEND in hint) is (main and scheduler)


@pytest.mark.parametrize("value", [float("inf"), float("nan"), "invalid"])
def test_malformed_native_idle_config_does_not_raise(value):
    config = {"compression": {"idle_compact_after_seconds": value}}
    settings = noting_settings_from_config(config)
    assert not settings.enabled
    assert settings.configuration_failure == "idle_compaction_config_unreadable"
    assert scheduler_settings_from_config(config).enabled


def test_secretary_conversation_gates_skill_writes_instead_of_recording():
    from agent.prompt_builder import SECRETARY_SKILLS_GUIDANCE, SKILL_RECORD_GUIDANCE, SKILLS_GUIDANCE
    from agent.system_prompt import _tool_guidance_block

    current = agent()
    current.valid_tool_names.add("skill_manage")
    block = _tool_guidance_block(current)
    assert SECRETARY_SKILLS_GUIDANCE in block
    assert SKILL_RECORD_GUIDANCE not in block

    native = agent(main=False)
    native.valid_tool_names.add("skill_manage")
    native_block = _tool_guidance_block(native)
    assert SKILLS_GUIDANCE in native_block
    assert SKILL_RECORD_GUIDANCE in native_block


def test_skill_gate_requires_confirmed_secretary_conversation():
    from agent.prompt_builder import SECRETARY_SKILL_GATE, SKILL_RECORD_GUIDANCE
    from agent.system_prompt import _tool_guidance_block

    current = agent(main=False, noting=True)
    current.valid_tool_names.add("skill_manage")
    block = _tool_guidance_block(current)
    assert SECRETARY_SKILL_GATE not in block
    assert SKILL_RECORD_GUIDANCE in block
