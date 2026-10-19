"""Channel provenance for the model: the timestamp marker cannot identify the channel.

Every genuine user message — Web UI and messaging gateway alike — begins with the same
``<timestamp>`` marker, so a weaker model needs an explicit delimiter around gateway
bodies. The wrapper is model-facing only; the durable transcript stays clean.
"""

from __future__ import annotations

from gateway.config import Platform
from gateway.platforms.event import MessageEvent
from gateway.inbound_provenance import wrap_inbound_origin
from gateway.run_turn import GatewayTurnMixin
from gateway.session import SessionSource


def _event(platform, text="hello", *, internal=False):
    return MessageEvent(
        text=text,
        source=SessionSource(platform=platform, chat_id="c", chat_type="dm", user_id="u"),
        internal=internal,
    )


def test_weixin_inbound_body_is_xml_wrapped():
    assert wrap_inbound_origin(_event(Platform.WEIXIN), "测试消息") == (
        '<gateway-message from="微信">\n测试消息\n</gateway-message>'
    )


def test_other_platforms_and_internal_events_are_never_wrapped():
    assert wrap_inbound_origin(_event(Platform.TELEGRAM), "hi") == "hi"
    assert wrap_inbound_origin(_event(Platform.WEIXIN, internal=True), "hi") == "hi"
    assert wrap_inbound_origin(_event(Platform.WEIXIN), "") == ""


def test_synthetic_prompt_events_are_never_wrapped():
    event = _event(Platform.WEIXIN, "goal continuation")
    event.metadata["synthetic_prompt"] = True
    assert wrap_inbound_origin(event, "goal continuation") == "goal continuation"


def test_goal_helper_marks_its_events_as_synthetic():
    from gateway.run_goals import GatewayGoalsMixin

    source = SessionSource(platform=Platform.WEIXIN, chat_id="c", chat_type="dm", user_id="u")
    event = GatewayGoalsMixin._synthetic_prompt_event(source, "keep going")
    assert event.metadata.get("synthetic_prompt") is True
    assert wrap_inbound_origin(event, event.text) == "keep going"


def test_gateway_turn_wraps_the_model_copy_and_keeps_the_transcript_clean(monkeypatch):
    monkeypatch.setattr("gateway.run._load_gateway_config", lambda: {})
    event = _event(Platform.WEIXIN)
    message_text, persist, _ts = GatewayTurnMixin._hmwa_apply_message_timestamp(None, event, event.text)
    assert message_text == '<gateway-message from="微信">\nhello\n</gateway-message>'
    # The durable/display copy must not carry the model-only wrapper.
    assert persist == "hello"


def test_other_platforms_keep_their_model_text(monkeypatch):
    monkeypatch.setattr("gateway.run._load_gateway_config", lambda: {})
    event = _event(Platform.TELEGRAM)
    message_text, persist, _ts = GatewayTurnMixin._hmwa_apply_message_timestamp(None, event, event.text)
    assert message_text == "hello"
    assert persist == "hello"
