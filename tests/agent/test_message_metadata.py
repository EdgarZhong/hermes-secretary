from agent.message_metadata import append_message, stamp_message_timestamp


def test_stamp_preserves_source_timestamp(monkeypatch):
    monkeypatch.setattr("agent.message_metadata.wall_time", lambda: 999.0)
    message = {"role": "user", "content": "hello", "timestamp": 123.0}

    result = stamp_message_timestamp(message)

    assert result is message
    assert message["timestamp"] == 123.0


def test_append_stamps_same_mapping_at_append_time(monkeypatch):
    monkeypatch.setattr("agent.message_metadata.wall_time", lambda: 456.0)
    messages = []
    message = {"role": "tool", "content": "ok"}

    result = append_message(messages, message)

    assert result is message
    assert messages == [message]
    assert message["timestamp"] == 456.0


def test_marker_fallback_uses_whole_second_format(monkeypatch):
    from datetime import datetime, timedelta, timezone
    from agent.message_metadata import format_user_timestamp_marker

    moment = datetime(2026, 10, 14, 12, 34, 56, 987654, tzinfo=timezone(timedelta(hours=8)))
    monkeypatch.setattr("hermes_time.now", lambda: moment)
    assert format_user_timestamp_marker(float("inf")) == "<timestamp>2026-10-14T12:34:56+08:00</timestamp>\n"
