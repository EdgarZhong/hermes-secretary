"""Pinned Secretary Web UI host identity without transport / gateway rewrites."""

from types import SimpleNamespace

from agent.conversation_loop import _stored_prompt_matches_runtime
from agent.surface_switch import stage_surface_switch_note
from agent.system_prompt import effective_platform_hint_key, platform_hint


def _agent(platform="tui", host_mode="secretary_web"):
    return SimpleNamespace(
        platform=platform,
        _secretary_host_mode=host_mode,
        _platform_hint_overrides={},
        _secretary_main_read_eligible=False,
        valid_tool_names=set(),
        session_id="test-session",
        model="test-model",
        provider="test-provider",
        pass_session_id=False,
    )


def _persisted_prompt(platform):
    return (
        "Agent identity\n\n"
        f"Model: test-model\n"
        "Provider: test-provider\n"
        f"Platform: {platform}"
    )


def test_secretary_ui_hint_is_independent_of_tui_transport():
    agent = _agent(platform="tui")
    assert effective_platform_hint_key(agent) == "secretary_web"
    hint = platform_hint(agent)
    assert "Hermes Secretary Web UI" in hint
    assert "You are in the Hermes terminal UI" not in hint
    assert agent.platform == "tui"  # toolsets and other transport consumers untouched


def test_existing_tui_prompt_is_rebuilt_once_for_secretary_ui():
    agent = _agent()
    assert not _stored_prompt_matches_runtime(agent, _persisted_prompt("tui"))
    assert _stored_prompt_matches_runtime(agent, _persisted_prompt("secretary_web"))


def test_native_prompt_rules_unchanged_without_host_mode():
    agent = _agent(host_mode=None)
    assert effective_platform_hint_key(agent) == "tui"
    assert "Hermes terminal UI" in platform_hint(agent)
    assert _stored_prompt_matches_runtime(agent, _persisted_prompt("tui"))
    assert not _stored_prompt_matches_runtime(agent, _persisted_prompt("secretary_web"))


def test_pinned_host_never_stages_transport_switch_note():
    agent = _agent()
    agent._surface_switch_note = "old pending dynamic switch note"
    history = [{"role": "user", "content": "Hello!"}]
    assert not stage_surface_switch_note(agent, _persisted_prompt("desktop"), history)
    assert agent._surface_switch_note == ""


def test_native_surface_switch_notice_remains_available():
    agent = _agent(host_mode=None)
    assert stage_surface_switch_note(agent, _persisted_prompt("desktop"), [])
    assert "different interface: tui" in agent._surface_switch_note
