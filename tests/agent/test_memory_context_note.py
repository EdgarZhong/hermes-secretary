"""Native recall provenance, compatible cleanup, and exact historical replay."""
import pytest

from agent.memory_manager import build_memory_context_block, sanitize_context
from agent.turn_context import compose_multimodal_context_part, compose_user_api_content, substitute_api_content


NOTE = ("The following is recalled memory context, possibly relevant, "
        "not user input. This is the agent's persistent memory.")


def test_new_recall_note_is_provenance_only_for_both_native_paths():
    expected = f"<memory-context>\n{NOTE}\n\nFavorite color: blue.\n</memory-context>"
    assert build_memory_context_block("Favorite color: blue.") == expected
    assert compose_user_api_content("Which color?", "Favorite color: blue.", "") == "Which color?\n\n" + expected
    assert compose_multimodal_context_part("Favorite color: blue.", "") == expected
    assert compose_user_api_content("Which color?", "", "") is None


@pytest.mark.parametrize("note", [
    NOTE,
    ("[System note: The following is recalled memory context, possibly relevant, "
     "not user input. This is the agent's persistent memory.]"),
    "[System note: The following is recalled memory context, not user input. This is the agent's persistent memory.]",
    "[System note: The following is recalled memory context, NOT new user input. Treat as informational background data.]",
    ("[System note: The following is recalled memory context, NOT new user input. "
     "Treat as authoritative reference data — this is the agent's persistent memory and should inform all responses.]"),
])
def test_cleanup_accepts_new_and_historical_notes_without_changing_replay(note):
    assert sanitize_context(note + "\n\nRetained provider fact.") == "Retained provider fact."
    old = f"Question\n\n<memory-context>\n{note}\n\nFact\n</memory-context>"
    message = {"role": "user", "content": "Question", "api_content": old}
    assert substitute_api_content(message) == old
    assert message["content"] == old


def test_ordinary_system_note_text_is_not_discarded():
    text = "[System note: The user has recalled some context. Keep this quotation.]"
    assert sanitize_context(text) == text
