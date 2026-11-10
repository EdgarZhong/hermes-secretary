"""Exercise the actual Gateway recovery stage with distinct API and durable input."""
from types import SimpleNamespace

import pytest

from gateway.run_turn_runner import TurnRunner
from gateway.turn_context import TurnContext


def prepare(recovery, clean, message):
    entry = SimpleNamespace(resume_pending=True, resume_reason="restart_timeout", last_resume_marked_at=None)
    host = SimpleNamespace(session_store=SimpleNamespace(_entries={"key": entry} if recovery == "resume_pending" else {}),
                           _delivery_adapter_for=lambda source: None)
    history = [{"role": "tool", "content": "previous tool result"}] if recovery == "tool_tail" else []
    context = TurnContext(message=message, persist_user_message=clean, persist_user_timestamp=123,
                          session_key="key", history=history)
    result, timestamp = TurnRunner(host, context)._prepare_turn_message(history)
    return result, timestamp, context.message


@pytest.mark.parametrize("recovery", ["normal", "tool_tail", "resume_pending"])
@pytest.mark.parametrize("clean", ["user text", [{"type": "text", "text": "user text"}, {"type": "image_url", "image_url": {"url": "data:fixture"}}]])
def test_existing_clean_ingress_is_authoritative_after_recovery(recovery, clean):
    wrapped = '<gateway-message from="微信">\nuser text\n</gateway-message>'
    result, timestamp, model = prepare(recovery, clean, wrapped)
    assert result is clean
    assert timestamp == 123
    assert wrapped in model
    if recovery != "normal":
        assert "[System note:" in model


@pytest.mark.parametrize("recovery", ["tool_tail", "resume_pending"])
def test_no_override_keeps_native_recovery_fallback(recovery):
    result, _, model = prepare(recovery, None, "native input")
    assert result == "native input"
    assert "[System note:" in model


def test_empty_startup_resume_still_persists_its_native_note():
    result, _, model = prepare("resume_pending", None, "")
    assert result == model
    assert result.strip()
