"""Usage-anchor model provenance: a cold-start restore must know which route priced the count."""

from agent.usage_anchor import (
    capture_usage_anchor,
    persisted_anchor_context,
    persisted_anchor_tokens,
)


def _messages():
    return [
        {"role": "system", "content": "You are Hermes."},
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"},
        {"role": "user", "content": "count this"},
    ]


class _DB:
    def __init__(self, anchor):
        self._anchor = anchor

    def get_session_model_config_value(self, session_id, key, default=None):
        return self._anchor if key == "_usage_anchor" else default


def test_capture_records_the_pricing_model():
    anchor = capture_usage_anchor(1234, 56, _messages(), model="DeepSeek-Flash")

    assert anchor["model"] == "deepseek-flash"
    context = persisted_anchor_context(_DB(anchor), "s1", _messages(), model="deepseek-flash")
    assert context == {"tokens": 1290, "model_matches": True}
    assert persisted_anchor_tokens(_DB(anchor), "s1", _messages()) == 1290


def test_anchor_without_model_stays_undecided():
    """Anchors persisted before model recording must never be judged stale."""
    anchor = capture_usage_anchor(1234, 56, _messages())

    assert "model" not in anchor
    context = persisted_anchor_context(_DB(anchor), "s1", _messages(), model="deepseek-flash")

    assert context["model_matches"] is None


def test_a_different_model_is_reported_as_stale():
    anchor = capture_usage_anchor(1234, 56, _messages(), model="deepseek-flash")

    context = persisted_anchor_context(_DB(anchor), "s1", _messages(), model="deepseek-v4-pro")

    assert context["model_matches"] is False


def test_a_rewritten_transcript_invalidates_the_anchor():
    anchor = capture_usage_anchor(1234, 56, _messages(), model="deepseek-flash")
    rewritten = _messages()[:-1] + [{"role": "user", "content": "edited"}]

    assert persisted_anchor_context(_DB(anchor), "s1", rewritten, model="deepseek-flash") is None
    assert persisted_anchor_tokens(_DB(anchor), "s1", rewritten) is None


def test_appended_messages_keep_the_anchor_and_add_the_delta():
    anchor = capture_usage_anchor(1234, 56, _messages(), model="deepseek-flash")
    grown = _messages() + [{"role": "user", "content": "and this too"}]

    context = persisted_anchor_context(_DB(anchor), "s1", grown, model="deepseek-flash")

    assert context["model_matches"] is True
    assert context["tokens"] > 1290
