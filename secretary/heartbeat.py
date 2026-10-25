"""Profile-owned Heartbeat presentation policy, independent of local Noting participation."""

from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

HEARTBEAT_INSTRUCTION = (
    "This is a self-check reminder, not a user message.\n"
    "Check what you can do: attend to the user's current state, remind the user of relevant matters, "
    "delegate agent tasks and verify their results, register schedules (do not rely on heartbeat), "
    "and follow up on anything else that needs attention.\n"
    "If any matter needs coordination with the user, proactively report it when the user returns.\n"
    "Finish by replying with HEARTBEAT_OVER."
)


def ui_heartbeat_enabled() -> bool:
    """Read only the global switch in the current owning-profile scope.

    Noting capability/configuration validation and Conversation-local /noting do not
    decide Heartbeat presentation or its execution surface.
    """
    from hermes_cli.config import load_config_readonly

    try:
        config = load_config_readonly()
        block = config.get("noting", {})
        return isinstance(block, dict) and block.get("enabled", True) is True
    except Exception:
        logger.warning("Heartbeat global Noting switch unreadable", exc_info=True)
        return False


def heartbeat_set_note(native_note: str) -> str:
    if not ui_heartbeat_enabled():
        return native_note
    return (
        "Saved for this Conversation. The UI backend runs due heartbeats while it is running, "
        "even after you switch conversations or close the page. Settings survive backend restarts. "
        "/heartbeat pause | resume | clear to manage."
    )


def render_heartbeat(prompt: str, timestamp: float) -> str:
    from agent.message_metadata import build_user_wrapper

    body = HEARTBEAT_INSTRUCTION
    if prompt:
        body += "\n\nAdditional prompt:\n" + prompt
    return build_user_wrapper("heartbeat", body, timestamp=timestamp)
