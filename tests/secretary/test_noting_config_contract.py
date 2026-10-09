"""Resolved native configuration, effective surface, and host gates (§4.6/4.12)."""
import json
from unittest.mock import MagicMock

import pytest

from hermes_state import SessionDB
from secretary.noting_policy import configuration_guidance, force_capability_failure, force_thresholds
from secretary.noting_runtime import note_main_turn_finished, noting_trigger_gate
from secretary.noting_scope import owning_db_scope
from tests.secretary.test_noting_surface import _names, _requests, _turn


@pytest.fixture
def native_runtime(tmp_path, monkeypatch):
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **k: MagicMock())
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **k: {})
    monkeypatch.setattr("agent.title_generator.maybe_auto_title", lambda *a, **k: None)
    monkeypatch.setattr("run_agent._hermes_home", tmp_path)
    db = SessionDB(tmp_path / "state.db")
    with owning_db_scope(db):
        yield db, tmp_path / "config.yaml"
    db.close()


def _construct(db, config, *, window=196000, ratio=.75, idle=0, enabled=True, local=True):
    from run_agent import AIAgent
    import hermes_yaml as yaml

    data = {"noting": {"enabled": enabled}, "model": {"default": "test/model", "provider": "custom",
            "base_url": "https://test.invalid/v1", "context_length": window},
            "compression": {"threshold": ratio, "threshold_tokens": int(window * ratio) if ratio < .75 else None, "idle_compact_after_seconds": idle}}
    config.write_text(yaml.safe_dump(data))
    db.create_session("config-main", source="cli")
    ref = db.resolve_conversation_ref("config-main")
    db.notebook_set_local_enabled(ref, local)
    agent = AIAgent(model="test/model", provider="custom", api_key="test", base_url="https://test.invalid/v1",
                    session_db=db, session_id="config-main", platform="cli", quiet_mode=True,
                    skip_context_files=True, skip_memory=True, enabled_toolsets=[])
    agent._cached_system_prompt = "Stable system."
    agent._use_prompt_caching = False
    agent.compression_enabled = False
    agent.save_trajectories = False
    agent._skip_mcp_refresh = True
    return agent, ref, data


@pytest.mark.parametrize("window,ratio,idle,reason,guidance", [
    (128000, .75, 0, "threshold_below_64k", "increase the Context Window"),
    (500000, .60, 0, "reserve_above_128k", "move the Hermes threshold later"),
    (196000, .75, 300, "idle_compaction_conflict", "idle_compact_after_seconds to 0"),
])
def test_actual_resolved_failure_closes_background_noting_but_preserves_main_reads(native_runtime, window, ratio, idle, reason, guidance, caplog):
    db, config = native_runtime
    agent, ref, data = _construct(db, config, window=window, ratio=ratio, idle=idle)
    try:
        before = config.read_text()
        native_pair = (agent.context_compressor.context_length, agent.context_compressor.threshold_tokens)
        assert native_pair == (window, int(window * ratio))
        assert noting_trigger_gate(db, ref) == (False, reason)
        assert guidance in caplog.text
        assert "notebook_show" in _names(agent.tools) & agent.valid_tool_names
        assert "session_history" in _names(agent.tools) & agent.valid_tool_names
        assert not note_main_turn_finished(agent)
        assert db.noting_idle_state(ref) is None
        seen = _requests(agent)
        _turn(agent)
        assert "notebook_show" in _names(seen[0]["tools"])
        assert "session_history" in _names(seen[0]["tools"])
        assert config.read_text() == before
        assert native_pair == (agent.context_compressor.context_length, agent.context_compressor.threshold_tokens)
        print(json.dumps({"pair": native_pair, "effective": noting_trigger_gate(db, ref), "guidance": guidance,
                          "request_tools": sorted(_names(seen[0]["tools"])), "native_idle": agent.compression_idle_compact_after_seconds}))
    finally:
        agent.close()


@pytest.mark.parametrize("window,ratio", [(196000, .75), (130000, .75)])
def test_legal_native_configuration_and_exact_threshold_floor(native_runtime, window, ratio):
    db, config = native_runtime
    agent, ref, _data = _construct(db, config, window=window, ratio=ratio)
    try:
        assert noting_trigger_gate(db, ref) == (True, "")
        assert "notebook_show" in _names(agent.tools) & agent.valid_tool_names
        pair = force_thresholds(agent.context_compressor.context_length, agent.context_compressor.threshold_tokens)
        if window == 130000:
            assert pair.force_noting_threshold == 64000
        assert pair.usable
    finally:
        agent.close()


def test_strict_reserve_equality_never_clamps():
    assert force_capability_failure(force_noting_reserve_tenths=1280000, force_noting_threshold_tenths=2000000) is None
    assert force_capability_failure(force_noting_reserve_tenths=1280001, force_noting_threshold_tenths=2000000) == "reserve_above_128k"
    pair = force_thresholds(300000, 193333)
    assert pair.force_noting_reserve == 128000.4
    assert pair.capability_failure == "reserve_above_128k"
    assert "reduce" in configuration_guidance(pair.capability_failure)


@pytest.mark.parametrize("enabled,local,idle", [(False, True, 300), (True, False, 0), (True, False, 300)])
def test_global_or_local_off_does_not_rewrite_native_config(native_runtime, enabled, local, idle):
    from hermes_cli.config import validate_config_structure
    db, config = native_runtime
    agent, ref, data = _construct(db, config, enabled=enabled, local=local, idle=idle)
    try:
        before = config.read_text()
        assert not noting_trigger_gate(db, ref)[0]
        assert ("notebook_show" in _names(agent.tools) & agent.valid_tool_names) is enabled
        seen = _requests(agent)
        _turn(agent)
        assert ("notebook_show" in _names(seen[0]["tools"])) is enabled
        assert agent.compression_idle_compact_after_seconds == idle
        issues = validate_config_structure(data)
        assert any("idle compaction" in issue.message for issue in issues) is (enabled and idle > 0)
        assert config.read_text() == before
    finally:
        agent.close()


def test_unknown_native_runtime_is_not_capability_proof(native_runtime):
    db, _config = native_runtime
    db.create_session("cold", source="cli")
    assert noting_trigger_gate(db, db.resolve_conversation_ref("cold")) == (False, "runtime_unresolved")


@pytest.mark.parametrize("window,cap,expected", [(196000, None, ""), (128000, None, "threshold_below_64k"), (500000, 300000, "reserve_above_128k")])
def test_cold_native_factory_uses_same_resolved_pair_and_invalidates_config(native_runtime, window, cap, expected, caplog, monkeypatch):
    import hermes_yaml as yaml
    from secretary.noting_capability import prime_cold_main_capability
    from secretary.noting_scope import _main_runtimes, _runtime_key
    db, config = native_runtime
    agent, ref, data = _construct(db, config, window=window)
    runtime = {"provider": "custom", "api_mode": "chat_completions", "base_url": "https://test.invalid/v1", "api_key": "test"}
    try:
        if cap:
            data["compression"]["threshold_tokens"] = cap
            config.write_text(yaml.safe_dump(data))
        _main_runtimes.pop(_runtime_key(db, ref), None)
        assert noting_trigger_gate(db, ref) == (False, "runtime_unresolved")
        # Construction of an SDK client would violate this read-only cold path.
        monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **k: pytest.fail("cold capability created SDK client"))
        assert prime_cold_main_capability(db, ref, "test/model", runtime) is (not bool(expected))
        assert noting_trigger_gate(db, ref) == ((False, expected) if expected else (True, ""))
        if expected:
            assert configuration_guidance(expected) in caplog.text
        data["model"]["context_length"] = 200000
        data["compression"]["threshold_tokens"] = None
        config.write_text(yaml.safe_dump(data))
        assert noting_trigger_gate(db, ref) == (False, "runtime_unresolved")
        assert prime_cold_main_capability(db, ref, "test/model", runtime)
        assert noting_trigger_gate(db, ref) == (True, "")
    finally:
        agent.close()


def test_real_attempt_logs_before_admission_dedupe_and_compaction_head(native_runtime, caplog):
    import logging
    from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
    from secretary.noting_policy import ContextMeasurement
    from secretary.noting_runtime import try_admit_force
    db, config = native_runtime
    agent, ref, _data = _construct(db, config)
    try:
        caplog.set_level(logging.INFO, logger="secretary.noting_runtime")
        db.append_message(agent.session_id, "user", "original intent", message_uid="original")
        measurement = ContextMeasurement(140000, agent.context_compressor.context_length, agent.context_compressor.threshold_tokens)
        assert try_admit_force(db, ref, measurement).action == "admit"
        assert try_admit_force(db, ref, measurement).reason == "same_anchor_admitted"
        events = [record.message for record in caplog.records if record.name == "secretary.noting_runtime"]
        assert "trigger attempt" in events[0] and "anchor=original" in events[0]
        assert "outcome" in events[1] and "action=admit" in events[1]
        assert "trigger attempt" in events[2] and "same_anchor_admitted" in events[3]
        caplog.clear()
        db.append_message(agent.session_id, "user", SUMMARY_PREFIX + "summary\n" + _SUMMARY_END_MARKER,
                          message_uid="compaction", display_kind="context_summary")
        assert try_admit_force(db, ref, measurement).reason == "no_frozen_anchor"
        assert "anchor=compaction compaction_head=True" in caplog.text
        assert "reason=no_frozen_anchor" in caplog.text
    finally:
        agent.close()


def test_cold_lmstudio_is_closed_before_native_model_activation(native_runtime, monkeypatch, caplog):
    from secretary.noting_capability import prime_cold_main_capability
    db, config = native_runtime
    config.write_text("noting:\n  enabled: true\n")
    db.create_session("lmstudio-cold", source="cli")
    ref = db.resolve_conversation_ref("lmstudio-cold")
    monkeypatch.setattr("hermes_cli.models_local.ensure_lmstudio_model_loaded",
                        lambda *a, **k: pytest.fail("cold helper activated model"))
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **k: pytest.fail("cold helper created SDK"))
    assert not prime_cold_main_capability(db, ref, "local/model", {"provider": "lmstudio"})
    assert noting_trigger_gate(db, ref) == (False, "runtime_unresolved")
    assert configuration_guidance("runtime_unresolved") in caplog.text
