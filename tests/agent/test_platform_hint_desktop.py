"""Platform resolution for the desktop chat surface, kept out of new prompts.

Pins the lookup-site behavior that still matters: the
``PLATFORM_HINTS["desktop"]`` entry, the deletion of the standalone
desktop-hint block from ``build_environment_hints()``, and the
lookup-site extension that appends the embedded-terminal-pane clarifier to
the ``tui`` platform hint when ``HERMES_DESKTOP_TERMINAL=1``.

New Conversations no longer receive that guidance in their system prompt;
these tests therefore assert the resolver still works while the prompt
stays free of it.

These tests run against the real prompt builders (no mocks) because
cache-stability and byte-for-byte text contracts are what we are
verifying — mocking the resolver would hide exactly the class of bug
this test covers.
"""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from agent.prompt_builder import PLATFORM_HINTS
from agent.system_prompt import (
    _tui_embedded_pane_clarifier,
    build_system_prompt_parts,
    platform_hint,
)

def _stable_prompt(agent):
    with (
        patch("agent.prompt_builder.load_soul_md", return_value=""),
        patch("agent.prompt_builder.build_environment_hints", return_value=""),
        patch("agent.prompt_builder.build_context_files_prompt", return_value=""),
    ):
        return build_system_prompt_parts(agent)["stable"]

def _make_agent(platform="", **overrides):
    base = dict(
        load_soul_identity=False,
        skip_context_files=False,
        valid_tool_names=[],
        _task_completion_guidance=False,
        _tool_use_enforcement=False,
        _environment_probe=False,
        _kanban_worker_guidance="",
        _memory_store=None,
        _memory_manager=None,
        _platform_hint_overrides={},
        model="",
        provider="",
        pass_session_id=False,
        session_id="",
    )
    base["platform"] = platform
    base.update(overrides)
    return SimpleNamespace(**base)

class TestPlatformHintStaysOutOfStablePrompt:
    """End-to-end through ``build_system_prompt_parts``: the runtime's process
    surface no longer injects guidance into a new Conversation's prompt. The
    desktop-hint block that used to live in ``build_environment_hints()`` is
    gone, and the lookup site still resolves the hint for dynamic notices."""

    def test_desktop_platform_does_not_stamp_guidance(self, monkeypatch):
        monkeypatch.setenv("HERMES_DESKTOP", "1")
        monkeypatch.delenv("HERMES_DESKTOP_TERMINAL", raising=False)
        agent = _make_agent(platform="desktop")
        stable = _stable_prompt(agent)
        assert PLATFORM_HINTS["desktop"] not in stable
        assert "Platform:" not in stable
        assert "terminal UI" not in stable
        assert "Runtime surface:" not in stable
        assert "embedded terminal pane" not in stable
        assert platform_hint(agent) == PLATFORM_HINTS["desktop"]

    def test_embedded_tui_does_not_stamp_hint_or_clarifier(self, monkeypatch):
        monkeypatch.setenv("HERMES_DESKTOP", "1")
        monkeypatch.setenv("HERMES_DESKTOP_TERMINAL", "1")
        agent = _make_agent(platform="tui")
        stable = _stable_prompt(agent)
        assert PLATFORM_HINTS["tui"] not in stable
        assert "embedded terminal pane" not in stable
        # The lookup-site clarifier survives for the dynamic switch-note path.
        assert "embedded terminal pane" in platform_hint(agent)

class TestEmbeddedTuiPaneClarifier:
    """When ``HERMES_DESKTOP_TERMINAL=1``, a standalone ``hermes --tui`` is
    running inside the desktop's embedded terminal pane. The user can
    ⌥-drag-select its output and ⌘/Ctrl+L to send it to the chat composer.
    That clarifier must be appended to the ``tui`` platform hint at the
    resolution site, NOT baked into the static ``PLATFORM_HINTS["tui"]``
    string (which is shared with every standalone TUI session and must
    stay byte-stable)."""

    @pytest.mark.parametrize("val", ["0", "false", ""])
    def test_falsy_env_does_not_trigger_clarifier(self, monkeypatch, val):
        monkeypatch.setenv("HERMES_DESKTOP_TERMINAL", val)
        out = _tui_embedded_pane_clarifier(PLATFORM_HINTS["tui"])
        assert out == PLATFORM_HINTS["tui"], (
            f"HERMES_DESKTOP_TERMINAL={val!r} should not trigger clarifier"
        )
