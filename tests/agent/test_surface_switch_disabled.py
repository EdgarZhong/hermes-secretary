"""Regression tests for the temporary platform surface-switch note shutdown.

Web UI is currently misclassified as tui by the transport-derived platform.  Until
host mode is independent of the inbound channel, do not append interface-switch
instructions to the user turn (especially a multimodal user turn).
"""

from types import SimpleNamespace

import pytest

from agent.surface_switch import stage_surface_switch_note


@pytest.mark.parametrize(
    ("current_platform", "stored_platform"),
    [
        ("tui", "desktop"),
        ("desktop", "tui"),
        ("weixin", "tui"),
        ("tui", "tui"),
    ],
)
def test_surface_switch_staging_is_disabled(current_platform, stored_platform):
    agent = SimpleNamespace(
        platform=current_platform,
        session_id="session-1",
        provider="openrouter",
        api_mode="chat_completions",
        _surface_switch_note="stale pending note",
    )
    stored_prompt = f"System prompt\n\nPlatform: {stored_platform}"

    assert stage_surface_switch_note(agent, stored_prompt, []) is False
    assert agent._surface_switch_note == ""


def test_old_surface_note_in_history_does_not_stage_another():
    agent = SimpleNamespace(
        platform="tui",
        session_id="session-1",
        provider="openrouter",
        api_mode="chat_completions",
    )
    history = [{
        "role": "user",
        "content": "Original user text",
        "api_content": (
            "[System: This conversation is now being answered on a different "
            "interface: desktop — any earlier interface guidance in this "
            "conversation is superseded.]"
        ),
    }]

    assert stage_surface_switch_note(
        agent, "System prompt\n\nPlatform: desktop", history,
    ) is False
    assert agent._surface_switch_note == ""
