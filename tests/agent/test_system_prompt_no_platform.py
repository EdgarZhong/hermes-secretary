"""New Conversations must not open with platform guidance or a ``Platform:`` line.

The runtime's process surface names where the process runs (``tui``, ``desktop``,
``weixin`` ...), not the interface the Conversation actually lands on. Injecting
that hint into a new prompt made the model describe a surface it may not be on;
the platform resolver stays available for dynamic switch notes and delivery
surfaces, but the initial system prompt carries neither the hint nor the identity
line.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from agent.prompt_builder import PLATFORM_HINTS
from agent.surface_switch import stage_surface_switch_note
from agent.system_prompt import build_system_prompt, platform_hint


def _make_agent(platform, **overrides):
    base = dict(
        load_soul_identity=False,
        skip_context_files=True,
        valid_tool_names=[],
        _task_completion_guidance=False,
        _tool_use_enforcement=False,
        _environment_probe=False,
        _kanban_worker_guidance="",
        _memory_store=None,
        _memory_manager=None,
        _platform_hint_overrides={},
        model="test-model",
        provider="openrouter",
        platform=platform,
        pass_session_id=False,
        session_id="session-1",
        _emit_status=lambda *_args, **_kwargs: None,
        _emit_diagnostic_status=lambda *_args, **_kwargs: None,
    )
    base.update(overrides)
    return SimpleNamespace(**base)


def _prompt(agent):
    with (
        patch("agent.prompt_builder.load_soul_md", return_value=""),
        patch("agent.prompt_builder.build_environment_hints", return_value=""),
        patch("agent.prompt_builder.build_context_files_prompt", return_value=""),
    ):
        return build_system_prompt(agent)


@pytest.mark.parametrize("platform", ["tui", "desktop", "weixin"])
def test_new_prompt_has_no_platform_guidance_or_identity(platform, monkeypatch):
    monkeypatch.delenv("HERMES_DESKTOP", raising=False)
    monkeypatch.delenv("HERMES_DESKTOP_TERMINAL", raising=False)
    agent = _make_agent(platform)
    prompt = _prompt(agent)

    assert PLATFORM_HINTS[platform] not in prompt
    assert "\nPlatform: " not in prompt
    assert not prompt.startswith("Platform: ")

    # Runtime identity that is not a surface label still anchors the prompt.
    assert "Conversation started:" in prompt
    assert "Model: test-model" in prompt
    assert "Provider: openrouter" in prompt

    # The platform attribute and the resolver are untouched by this subtraction.
    assert agent.platform == platform
    assert platform_hint(agent) == PLATFORM_HINTS[platform]


def test_new_conversation_without_platform_line_stages_no_switch_note(monkeypatch):
    monkeypatch.delenv("HERMES_DESKTOP", raising=False)
    monkeypatch.delenv("HERMES_DESKTOP_TERMINAL", raising=False)
    agent = _make_agent("desktop")
    prompt = _prompt(agent)

    assert stage_surface_switch_note(agent, prompt, []) is False
    assert not getattr(agent, "_surface_switch_note", "")
    # A first user turn in a brand-new Conversation is still not a surface switch.
    assert stage_surface_switch_note(
        agent, prompt, [{"role": "user", "content": "hello"}]
    ) is False
    assert not getattr(agent, "_surface_switch_note", "")
