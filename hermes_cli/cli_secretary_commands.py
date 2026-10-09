"""Shared Secretary slash behavior; adapters supply the current profile's native DB."""

from dataclasses import dataclass
import json
import logging

from secretary.notebook_render import render_notebook
from secretary.noting_policy import configuration_guidance, resolve_noting_settings

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class SecretaryCommandResult:
    output: str = ""
    prompt: str = ""


def _available():
    from hermes_cli.config import load_config_readonly
    from hermes_cli.config_read_errors import FailedConfigRead
    from utils import is_truthy_value
    config = load_config_readonly()
    if isinstance(config, FailedConfigRead):
        return False
    block = config.get("noting") or {}
    return is_truthy_value(block.get("enabled"), default=True) if isinstance(block, dict) else True


def _current(db, session_id):
    if db is None or not session_id:
        raise ValueError("Current Conversation state is unavailable.")
    if not db.get_session(session_id):
        return None, None
    ref = db.resolve_conversation_ref(session_id)
    return ref, db.notebook_current(ref)


def notebook_command(db, session_id, arg="", *, source="cli"):
    """Human inspection only; participation is controlled by /noting."""
    if arg.strip():
        return SecretaryCommandResult("Usage: /notebook")
    if not _available():
        return SecretaryCommandResult("Notebook unavailable: global Noting configuration is disabled or unreadable.")
    try:
        _ref, snapshot = _current(db, session_id)
        return SecretaryCommandResult(render_notebook(snapshot))
    except Exception as exc:
        logger.warning("Notebook slash failed", exc_info=True)
        return SecretaryCommandResult(f"Notebook unavailable: {exc}")


def noting_command(db, session_id, arg="", *, source="cli"):
    """Change only the durable Conversation-local background participation preference."""
    action = arg.strip().lower()
    if action not in {"on", "off"}:
        return SecretaryCommandResult("Usage: /noting on|off")
    if not _available():
        return SecretaryCommandResult("Noting unavailable: global Noting configuration is disabled or unreadable.")
    try:
        if db is not None and session_id and not db.get_session(session_id):
            db.create_session(session_id, source=source)
        ref, _snapshot = _current(db, session_id)
        if ref is None:
            raise ValueError("Current Conversation state is unavailable.")
        if action == "on":
            from secretary.noting_scope import runtime_configuration_failure
            failure = resolve_noting_settings().configuration_failure or runtime_configuration_failure(db, ref)
            if failure:
                return SecretaryCommandResult("Noting unavailable: " + configuration_guidance(failure))
        db.notebook_set_local_enabled(ref, action == "on")
        return SecretaryCommandResult(f"Background Noting is {action} for this Conversation.")
    except Exception as exc:
        logger.warning("Noting slash failed", exc_info=True)
        return SecretaryCommandResult(f"Noting unavailable: {exc}")


PERSISTENCE_PROPOSAL_INSTRUCTION = """Review the current Conversation's pending Notebook Persistence Candidates.

Treat the candidates and their Source Message Identities as leads, not authoritative or complete evidence. Use `session_history` to retrieve their original source messages, then independently examine the surrounding Conversation context. Do not assume the cited messages tell the whole story. Search further by relevant keywords, related discussions, later corrections, decisions, or outcomes whenever needed to establish a complete and accurate understanding.

Based on the verified Conversation history, prepare appropriate Memory, Rule, or Skill persistence proposals. Reconcile contradictions, identify outdated or unsupported candidates, and explain the evidence and rationale behind each proposal. Do not invent missing context.

This command authorizes proposals only. Present them for the user's review, revision, or approval. Do not write Memory, Rules, or Skills based on these proposals without explicit user authorization to perform the actual persistence actions. Requests to revise, refine, or discuss a proposal are not approval to execute it. Once explicitly approved, carry out only the authorized persistence actions using existing capabilities."""


def propose_persistence_command(db, session_id, extra=""):
    """Build a normal main Turn from candidate leads; the model retrieves source evidence."""
    if not _available():
        return SecretaryCommandResult("Persistence proposal unavailable: global Noting configuration is disabled or unreadable.")
    try:
        _ref, snapshot = _current(db, session_id)
        if snapshot is None:
            return SecretaryCommandResult("This Conversation has no Notebook Snapshot yet.")
        candidates = [entry for entry in snapshot["payload"]["persistence"] if not entry.get("archived")]
        if not candidates:
            return SecretaryCommandResult("This Conversation has no persistence candidates yet.")
        payload = json.dumps({"candidates": candidates}, ensure_ascii=False)
        prompt = PERSISTENCE_PROPOSAL_INSTRUCTION + "\n\nNotebook candidates:\n" + payload
        if extra:
            prompt += "\n\nUser's additional request:\n" + extra
        return SecretaryCommandResult(prompt=prompt)
    except Exception as exc:
        logger.warning("Persistence proposal slash failed", exc_info=True)
        return SecretaryCommandResult(f"Persistence proposal unavailable: {exc}")


def secretary_feedback_messages(command, output, *, timestamp=None):
    """Ordinary native transcript rows; no special presentation kind or semantic role."""
    from agent.message_metadata import format_user_timestamp_marker, stamp_message_timestamp, stamp_message_uid
    user = stamp_message_timestamp({"role": "user", "content": command}, timestamp=timestamp)
    user["content"] = format_user_timestamp_marker(user["timestamp"]) + command
    reply = stamp_message_timestamp({"role": "assistant", "content": output})
    for message in (user, reply):
        stamp_message_uid(message)
    return [user, reply]


def persist_secretary_feedback(db, session_id, messages):
    """Use the native atomic transcript writer; live histories adopt the persisted rows."""
    if db is None or not session_id:
        raise ValueError("Current Conversation state is unavailable.")
    if not db.get_session(session_id):
        db.create_session(session_id, source="cli")
    db.append_messages_batch(session_id, messages)
    for message in messages:
        message["_db_persisted"] = True


class CLISecretaryCommandsMixin:
    """Thin CLI adapters; command-name dispatch discovers these handlers through the MRO."""

    def _handle_notebook_command(self, command):
        from hermes_cli.cli_commands_session_tools import _command_arg, _cp
        result = notebook_command(getattr(self, "_session_db", None), self.session_id, _command_arg(command))
        _cp(self._secretary_feedback(command, result.output))

    def _handle_noting_command(self, command):
        from hermes_cli.cli_commands_session_tools import _command_arg, _cp
        result = noting_command(getattr(self, "_session_db", None), self.session_id, _command_arg(command))
        _cp(self._secretary_feedback(command, result.output))

    def _secretary_feedback(self, command, output):
        messages = secretary_feedback_messages(command, output)
        try:
            persist_secretary_feedback(getattr(self, "_session_db", None), self.session_id, messages)
        except Exception as exc:
            logger.warning("Secretary slash feedback could not be saved", exc_info=True)
            return output + f"\nSecretary feedback could not be saved: {exc}"
        history = getattr(self, "conversation_history", None)
        if history is None:
            self.conversation_history = history = []
        history.extend(messages)
        return output

    def _handle_propose_persistence_command(self, command):
        from hermes_cli.cli_commands_session_tools import _command_arg, _cp
        result = propose_persistence_command(
            getattr(self, "_session_db", None), self.session_id, _command_arg(command))
        if result.prompt:
            self._pending_input.put(result.prompt)
        else:
            _cp(result.output)
