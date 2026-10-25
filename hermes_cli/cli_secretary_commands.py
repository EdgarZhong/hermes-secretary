"""Shared Secretary slash behavior; adapters supply the current profile's native DB."""

from dataclasses import dataclass
import json
import logging
from pathlib import Path

from secretary.notebook_render import model_notebook_view, readable_notebook_state, render_notebook
from secretary.noting_policy import configuration_guidance
from secretary.noting_scope import settings_for_db

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class SecretaryCommandResult:
    output: str = ""
    prompt: str = ""


def _availability_failure(db):
    settings = settings_for_db(db)
    if settings.enabled:
        return ""
    return (configuration_guidance(settings.configuration_failure)
            or "Global Noting configuration is disabled.")


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
    failure = _availability_failure(db)
    if failure:
        return SecretaryCommandResult("Notebook unavailable: " + failure)
    try:
        _ref, snapshot = _current(db, session_id)
        return SecretaryCommandResult(render_notebook(snapshot, profile_home=Path(db.db_path).parent, db=db))
    except Exception as exc:
        logger.warning("Notebook slash failed", exc_info=True)
        return SecretaryCommandResult(f"Notebook unavailable: {exc}")


def noting_command(db, session_id, arg="", *, source="cli"):
    """Change only the durable Conversation-local background participation preference."""
    action = arg.strip().lower()
    if action not in {"on", "off"}:
        return SecretaryCommandResult("Usage: /noting on|off")
    failure = _availability_failure(db)
    if failure:
        return SecretaryCommandResult("Noting unavailable: " + failure)
    try:
        if db is not None and session_id and not db.get_session(session_id):
            db.create_session(session_id, source=source)
        ref, _snapshot = _current(db, session_id)
        if ref is None:
            raise ValueError("Current Conversation state is unavailable.")
        if action == "on":
            from secretary.noting_scope import runtime_configuration_failure
            failure = settings_for_db(db).configuration_failure or runtime_configuration_failure(db, ref)
            if failure:
                return SecretaryCommandResult("Noting unavailable: " + configuration_guidance(failure))
        db.notebook_set_local_enabled(ref, action == "on")
        return SecretaryCommandResult(f"Background Noting is {action} for this Conversation.")
    except Exception as exc:
        logger.warning("Noting slash failed", exc_info=True)
        return SecretaryCommandResult(f"Noting unavailable: {exc}")


PERSISTENCE_PROPOSAL_INSTRUCTION = """Review this Conversation's current Persistence Candidates (ignore Conversation-target Candidates; they are working guidance) and begin a concrete proposal for the user. It authorizes preparing a proposal, not an action or a write. Use the supplied Notebook Snapshot when it is current; call notebook_show first if the view is missing, marked superseded or behind the current effective Snapshot. Prepare the proposal from current entries, not retired or corrected candidates from an older Snapshot.
Treat candidate descriptions, current Notebook references and Message provenance as leads when present. Read the relevant originals and nearby messages with conversation_history; Search for missing context, later corrections, contradictions or outcomes when needed. Compare the current sources with the candidate and retain only supported content. Do not invent missing facts or treat an AI suggestion as the user's acceptance.
Group related material by topic and destination. Show the proposed Memory, Skill or Rule content, intended destination, source entry_id values where present, the actual content scope, mapped content labels and provenance, and any material uncertainty. Carry the source content labels into the proposal materials, mapping implicit_gap to situation; direct-message candidates need no invented Notebook ancestry. Keep necessary unknowns minimal and distinguish them from facts.
For a Skill proposal, state the proposed skill's name, when it should load, the concrete workflow or steps, the pitfalls it prevents, and how to verify it; the proposal is the draft, not a write.
Present an approvable draft without asking the user to run another command or approve starting the proposal. Do not repeat an unchanged pending proposal; respect explicit deferral or rejection and identify any genuinely new or corrected content. If no suitable proposal exists, explain briefly rather than invent candidates to reduce a count.
Before any actual mutation, obtain the user's explicit approval of the concrete content and destination. Discussion, edits, silence, a Framework Message and exceeding a threshold are not execution approval. After approval, use existing authorized destination tools for exactly that scope, provide the mapped labels and provenance with the approved write, and report the actual tool outcome. Destination support or retention of those metadata is not an additional Secretary success condition. Do not blindly retry an ambiguous write.
Leave the approved content scope, candidate/source correspondence including the entry_id actually dispatched, and actual success, partial success, failure or unknown outcome in the normal Conversation trajectory. Do not edit the Notebook or inspect destination storage on Noting's behalf; a later Noting task settles only the successfully dispatched coverage supported by that trajectory."""


def propose_persistence_command(db, session_id, extra=""):
    """Build a normal main Turn from candidate leads; the model retrieves source evidence."""
    failure = _availability_failure(db)
    if failure:
        return SecretaryCommandResult("Persistence proposal unavailable: " + failure)
    try:
        _ref, snapshot = _current(db, session_id)
        if snapshot is None:
            return SecretaryCommandResult("This Conversation has no Notebook Snapshot yet.")
        # Supply the current view, including candidate-to-source relationships. No History
        # retrieval or destination access occurs in this slash adapter.
        payload = json.dumps(model_notebook_view(
            {"conversation_ref": _ref, "snapshot_id": snapshot["snapshot_id"],
             "coverage": {"anchor_message_uid": snapshot["anchor_message_uid"]},
             "payload": readable_notebook_state(snapshot["payload"], profile_home=Path(db.db_path).parent,
                                                db=db, conversation_ref=_ref)},
            db=db, profile_home=Path(db.db_path).parent),
                             ensure_ascii=False)
        prompt = PERSISTENCE_PROPOSAL_INSTRUCTION + "\n\nCurrent Notebook Snapshot (data):\n" + payload
        if extra:
            prompt += "\n\nUser's additional request:\n" + extra
        return SecretaryCommandResult(prompt=prompt)
    except Exception as exc:
        logger.warning("Persistence proposal slash failed", exc_info=True)
        return SecretaryCommandResult(f"Persistence proposal unavailable: {exc}")


def secretary_feedback_messages(command, output, *, timestamp=None, human_only=False):
    """Ordinary native transcript rows; no special presentation kind or semantic role."""
    from agent.message_metadata import format_user_timestamp_marker, stamp_message_timestamp, stamp_message_uid
    user = stamp_message_timestamp({"role": "user", "content": command}, timestamp=timestamp)
    user["content"] = format_user_timestamp_marker(user["timestamp"]) + command
    reply = stamp_message_timestamp({"role": "assistant", "content": output})
    for message in (user, reply):
        stamp_message_uid(message)
        if human_only:
            message["display_metadata"] = {"human_only": True}
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
        _cp(self._secretary_feedback(command, result.output, human_only=True))

    def _handle_noting_command(self, command):
        from hermes_cli.cli_commands_session_tools import _command_arg, _cp
        result = noting_command(getattr(self, "_session_db", None), self.session_id, _command_arg(command))
        _cp(self._secretary_feedback(command, result.output))

    def _secretary_feedback(self, command, output, *, human_only=False):
        messages = secretary_feedback_messages(command, output, human_only=human_only)
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
