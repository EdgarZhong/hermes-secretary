"""Render a committed Noting result; never read a pointer or publish on its own."""

from hermes_cli.cli_secretary_commands import PERSISTENCE_PROPOSAL_INSTRUCTION
from secretary.notebook_render import render_notebook


SCHEDULE_SUGGESTION_INSTRUCTION = (
    "Schedule suggestions in this Notebook are semantic advice, not ready-to-submit Scheduler arguments. "
    "Noting has not created or updated Schedules from them. "
    "Consider creating or updating Schedules based on these suggestions."
)


class SupersededNotingResult(RuntimeError):
    """The queued Snapshot no longer owns the current pointer; drop this carrier."""


def completion_body(snapshot, *, termination, summary, settings, profile_home, db=None, conn=None):
    """Count the exact injected Notebook body, excluding the notification wrapper."""
    body = render_notebook(snapshot, profile_home=profile_home, db=db, conn=conn, model_visible=True)
    char_count = len(body)
    entry_count = sum(len(entries) for entries in snapshot["payload"].values())
    kind = termination["type"]
    if kind == "forced":
        summary += (" Notebook maintenance did not finish normally: the Noting execution budget ended; "
                    "some Noting responsibilities may remain unfinished.")
    elif kind == "context_overflow":
        summary += (" Notebook maintenance did not finish normally: the context window was exhausted; "
                    "some Noting responsibilities may remain unfinished.")
    result = (
        f"NOTING RESULT\nConversation: {snapshot['conversation_ref']}\n"
        f"Termination: {kind}\nSummary: {summary}\n"
        "Summary reports only the Noting task's work. For Conversation facts, uncertainty, "
        "user acceptance and decisions, use the CURRENT NOTEBOOK SNAPSHOT below; "
        "do not infer or strengthen them from Summary.\n\n"
        f"CURRENT NOTEBOOK SNAPSHOT\n{body}"
    )
    char_threshold = settings.persistence_proposal_char_threshold
    entry_threshold = settings.persistence_proposal_entry_threshold
    if char_count > char_threshold or entry_count > entry_threshold:
        result += (
            "\n\nPERSISTENCE PROPOSAL REQUEST\n"
            f"The committed Notebook contains {char_count} characters and {entry_count} current entries; "
            f"the proposal thresholds are {char_threshold} characters and {entry_threshold} entries. "
            "This is a request to prepare an approvable proposal, not permission to write or discard pending material."
            "\n\n" + PERSISTENCE_PROPOSAL_INSTRUCTION
        )
    if any(entry.get("schedule_suggestion") is not None
           for entries in snapshot["payload"].values() for entry in entries):
        result += "\n\n" + SCHEDULE_SUGGESTION_INSTRUCTION
    return result


def failure_body(conversation_ref, specific_reason):
    return (
        f"NOTING RESULT\nConversation: {conversation_ref}\n"
        f"No new Snapshot was committed by this task: {specific_reason}. "
        "Do not treat its attempted edits as committed; use the current effective Notebook selected by the normal pointer rules."
    )
