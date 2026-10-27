"""Weixin's session-management boundary, using native command normalization."""

from dataclasses import replace

from gateway.platforms.event import MessageEvent
from hermes_cli.commands import resolve_command


SESSION_MANAGEMENT_COMMANDS = frozenset({"new", "clear", "resume", "sessions", "branch", "topic"})
SESSION_MANAGEMENT_REFUSAL = (
    "微信不支持会话管理 slash 命令，请回到 Web UI 管理会话；需要换绑时直接告诉 AI。"
)


def is_session_management_command(event: MessageEvent, quick_commands=None) -> bool:
    """Inspect aliases without rewriting the admitted event or invoking any command."""
    probe = replace(event)
    seen = set()
    quick_commands = quick_commands or {}
    while (command := probe.get_command()) and command not in seen:
        seen.add(command)
        definition = resolve_command(command)
        if definition is not None:
            return definition.name in SESSION_MANAGEMENT_COMMANDS
        alias = quick_commands.get(command)
        if not isinstance(alias, dict) or alias.get("type") != "alias":
            return False
        target = (alias.get("target") or "").strip()
        if not target:
            return False
        target = target if target.startswith("/") else f"/{target}"
        probe.text = f"{target} {probe.get_command_args().strip()}".strip()
    return False
