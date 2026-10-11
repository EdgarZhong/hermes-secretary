"""CLI transcript flush and session-end boundary helper."""
from contextlib import suppress


def _settle_native_compaction_boundary(cli) -> None:
    if cli.agent:
        from agent.context_compaction_request import settle_native_boundary_history
        history = settle_native_boundary_history(cli.agent, cli.conversation_history)
        if history is not cli.conversation_history:
            cli.conversation_history = history
            cli.session_id = cli.agent.session_id


def _end_current_session(cli, reason: str) -> None:
    """Flush un-persisted messages, then end the current session row with ``reason``.
    Best-effort on both steps (the switch proceeds even if the DB write fails)."""
    _settle_native_compaction_boundary(cli)
    if cli.agent:
        with suppress(Exception):
            cli.agent._flush_messages_to_session_db(
                cli.conversation_history, conversation_history=cli.conversation_history)
    with suppress(Exception):
        cli._session_db.end_session(cli.session_id, reason)
