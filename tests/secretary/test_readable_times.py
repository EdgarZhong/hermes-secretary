"""Whole-second presentation preserves precise stored instants and owning profiles."""

import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from math import floor

import pytest

from agent.message_metadata import format_user_timestamp_marker
from hermes_cli.cli_secretary_commands import notebook_command
from hermes_state import SessionDB
from hermes_time import format_timestamp, reset_cache
from secretary.notebook_store import NotebookStore
from secretary.reminder_request import _batch_carrier
from tools.notebook_tool import notebook_show
from tools.session_history_tool import conversation_history
from types import SimpleNamespace


@pytest.mark.parametrize("zone,offset", [("Asia/Shanghai", 8), ("America/New_York", -4), ("UTC", 0)])
def test_real_db_human_and_model_projections_keep_same_instant(tmp_path, monkeypatch, zone, offset):
    monkeypatch.setenv("HERMES_TIMEZONE", "Pacific/Honolulu")
    home = tmp_path / zone.replace("/", "-")
    home.mkdir()
    (home / "config.yaml").write_text(f"timezone: {zone}\nnoting:\n  enabled: true\n")
    reset_cache()
    db = SessionDB(home / "state.db")
    try:
        db.create_session("main", source="cli")
        stamp = 1791756123.25
        db.append_message("main", "user", "original body 1791756123.25", message_uid="source", timestamp=stamp)
        ref = db.resolve_conversation_ref("main")
        store = NotebookStore(db, ref, anchor_message_uid="source")
        store.create("matter", {"description": "report", "completion_condition": "deliver"}, source_message_identities=[{"conversation_ref": ref, "message_uid": "source"}])
        store.commit(termination={"type": "forced"})
        snapshot = db.notebook_current(ref)
        db.notebook_set_local_enabled(ref, False)
        model = json.loads(notebook_show(db=db, conversation_ref=ref, effective_enabled=True))
        parsed = datetime.fromisoformat(model["created_at"])
        assert parsed.timestamp() == floor(snapshot["created_at"])
        assert parsed.utcoffset() == timedelta(hours=offset)
        # The actual shared slash result is reused by CLI, Gateway and TUI adapters.
        human = notebook_command(db, "main").output
        assert f"Created at: {model['created_at']}" in human
        assert "source" in human and snapshot["snapshot_id"] not in human
        agent = SimpleNamespace(_session_db=db, session_id="main", platform="cli", _secretary_conversation_ref=ref)
        result = json.loads(conversation_history({"mode": "search", "query": "original"}, agent=agent))
        row = result["messages"][0]
        assert set(row) == {"message_uid", "timestamp", "role", "kind", "source", "content",
                            "excerpt_kind"}
        source = datetime.fromisoformat(row["timestamp"])
        assert source.timestamp() == floor(stamp) and source.utcoffset() == timedelta(hours=offset)
        exact_boundary = datetime.fromtimestamp(stamp, timezone.utc).isoformat()
        precise = json.loads(conversation_history({"mode": "read", "start_time": exact_boundary, "end_time": exact_boundary},
                                           agent=agent))
        precise_row = precise["messages"][0]
        assert precise_row["content"] == row["content"]
        assert precise_row["message_uid"] == row["message_uid"]
        assert precise_row["kind"] == "human" and precise_row["source"] == "human"
        assert db.notebook_current(ref) == snapshot
        assert db.get_messages("main")[0]["timestamp"] == stamp
        assert row["content"] == "original body 1791756123.25"
        carrier = _batch_carrier([{"source_timestamp": stamp, "content": "due"}], db=db)
        assert "<timestamp>" not in carrier
        assert f"Due: {row['timestamp']}" in carrier
        assert format_timestamp(snapshot["created_at"], profile_home=home) == model["created_at"]
    finally:
        db.close()
        reset_cache()


def test_two_owners_do_not_use_launch_env_or_first_cached_timezone(tmp_path, monkeypatch):
    monkeypatch.setenv("HERMES_TIMEZONE", "Pacific/Honolulu")
    reset_cache()
    owners = []
    for name in ("Asia/Shanghai", "UTC"):
        home = tmp_path / name.replace("/", "-")
        home.mkdir()
        (home / "config.yaml").write_text(f"timezone: {name}\n")
        owners.append(home)
    stamp = 1791756123.25
    for _ in range(2):
        values = [format_timestamp(stamp, profile_home=home) for home in owners]
        assert values == ["2026-10-12T06:02:03+08:00", "2026-10-11T22:02:03+00:00"]
    assert format_user_timestamp_marker(stamp).count("<timestamp>") == 1
    assert "-10:00" in format_user_timestamp_marker(stamp)
    reset_cache()


def test_valid_iso_null_and_invalid_absolute_time():
    assert format_timestamp("2026-10-12T07:22:03.250000+08:00") == "2026-10-12T07:22:03+08:00"
    assert format_timestamp("2026-10-11T23:22:03Z") == "2026-10-11T23:22:03Z"
    assert format_timestamp("2026-10-11T23:22:03.999999Z") == "2026-10-11T23:22:03Z"
    assert format_timestamp(None) is None
    with pytest.raises(ValueError):
        format_timestamp("2026-10-12T07:22:03")


@pytest.mark.parametrize("value", ["1791800714.1486568", 1791800714.9999998, Decimal("-0.25")])
def test_numeric_fraction_is_hidden_without_rounding(value):
    rendered = format_timestamp(value)
    parsed = datetime.fromisoformat(rendered)
    assert parsed.timestamp() == floor(Decimal(str(value)))
    assert parsed.microsecond == 0 and parsed.tzinfo is not None


def test_datetime_fraction_is_hidden_without_mutating():
    moment = datetime(2026, 10, 14, 12, 34, 56, 999999, tzinfo=timezone(timedelta(hours=8)))
    assert format_timestamp(moment) == "2026-10-14T12:34:56+08:00"
    assert moment.microsecond == 999999


def test_invalid_numeric_absolute_times():
    for invalid in ("not-time", float("nan"), float("inf")):
        with pytest.raises(ValueError):
            format_timestamp(invalid)
