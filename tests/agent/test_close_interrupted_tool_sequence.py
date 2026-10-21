"""Regression tests for ``close_interrupted_tool_sequence`` (#48879 follow-up).

#48879 closed the tool-call sequence on interrupt inside ``finalize_turn``,
but the retry/backoff/error interrupt aborts in ``conversation_loop`` ``return``
early and never reach it — so they persisted a raw ``tool`` tail. The next user
message then lands as ``... tool → user``, the role-alternation violation that
makes strict providers (Gemini, Claude) hallucinate a continuation and ignore
prior context (what the user perceives as "lost context").

The fix routes every interrupt abort through this one shared helper. These tests
pin the helper's contract and prove the post-interrupt + next-user-message
transcript is alternation-safe.
"""

from agent.message_sanitization import close_interrupted_tool_sequence
from agent.turn_failure_copy import FAILED_TURN_DISPLAY_KIND


def _tool_tail():
    return [
        {"role": "user", "content": "edit the file"},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [{"id": "c1", "function": {"name": "patch", "arguments": "{}"}}],
        },
        {"role": "tool", "tool_call_id": "c1", "content": "ok edited"},
    ]


def _assert_no_tool_then_user(messages):
    for i in range(len(messages) - 1):
        if messages[i].get("role") == "tool":
            assert messages[i + 1].get("role") != "user", (
                f"role-alternation violation: tool → user at index {i}"
            )








def test_closing_makes_next_user_message_alternation_safe():
    """The whole point: appending a user turn after the close must not
    produce the ``tool → user`` shape strict providers choke on."""
    messages = _tool_tail()
    close_interrupted_tool_sequence(messages, None)
    assert isinstance(messages[-1]["timestamp"], float)
    follow_on = messages + [{"role": "user", "content": "they do! increase the timing"}]
    _assert_no_tool_then_user(follow_on)
    # A caller banner is the turn's only explanation: it stays visible, unhidden.
    bannered = _tool_tail()
    assert close_interrupted_tool_sequence(bannered, "Response truncated.") is True
    assert bannered[-1]["content"] == "Response truncated."
    assert "display_kind" not in bannered[-1]


def test_assistant_tail_is_left_untouched():
    messages = [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "partial reply"},
    ]
    before = [dict(m) for m in messages]
    assert close_interrupted_tool_sequence(messages, "interrupted") is False
    assert messages == before


def test_user_tail_is_left_untouched():
    messages = [{"role": "user", "content": "hi"}]
    assert close_interrupted_tool_sequence(messages, None) is False
    assert len(messages) == 1


def test_explicit_banner_kind_only_applies_to_the_appended_visible_row():
    messages = _tool_tail()
    before = [dict(message) for message in messages]
    text = "Operation interrupted: waiting for model response (1.8s elapsed)."

    assert close_interrupted_tool_sequence(messages, text, display_kind=FAILED_TURN_DISPLAY_KIND)
    assert messages[:-1] == before
    assert messages[-1]["content"] == text
    assert messages[-1]["display_kind"] == FAILED_TURN_DISPLAY_KIND
    assert not close_interrupted_tool_sequence(messages, text, display_kind=FAILED_TURN_DISPLAY_KIND)
    assert len(messages) == len(before) + 1


def test_explicit_banner_kind_does_not_make_the_empty_placeholder_visible():
    messages = _tool_tail()
    close_interrupted_tool_sequence(messages, None, display_kind=FAILED_TURN_DISPLAY_KIND)
    assert messages[-1]["content"] == ""
    assert messages[-1]["display_kind"] == "hidden"

