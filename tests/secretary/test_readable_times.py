"""C15 presentation boundaries preserve real stored instants and owning profiles."""

import json
from datetime import datetime, timedelta

import pytest

from agent.message_metadata import format_user_timestamp_marker
from hermes_cli.cli_secretary_commands import notebook_command
from hermes_state import SessionDB
from hermes_time import format_timestamp, reset_cache
from secretary.notebook_store import NotebookStore
from secretary.reminder_request import _batch_carrier
from tools.notebook_tool import notebook_show
from tools.session_history_tool import session_history


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
        store = NotebookStore(db, ref)
        store.create("user_commitment", {"what": "report", "intent": "deliver"})
        store.commit("source")
        snapshot = db.notebook_current(ref)
        db.notebook_set_local_enabled(ref, False)
        model = json.loads(notebook_show(db=db, conversation_ref=ref, effective_enabled=True))["notebook"]
        parsed = datetime.fromisoformat(model["last_update_time"])
        assert parsed.timestamp() == pytest.approx(snapshot["created_at"], rel=0, abs=1e-6)
        assert parsed.utcoffset() == timedelta(hours=offset)
        # The actual shared slash result is reused by CLI, Gateway and TUI adapters.
        monkeypatch.setattr("hermes_cli.cli_secretary_commands._available", lambda: True)
        human = notebook_command(db, "main").output
        assert f"Created at: {model['last_update_time']}" in human
        assert "source" not in human and snapshot["snapshot_id"] not in human
        result = json.loads(session_history({"mode": "search", "query": "original"}, db=db, conversation_ref=ref))
        row = result["messages"][0]
        assert set(row) == {"message_uid", "timestamp", "role", "content"}
        source = datetime.fromisoformat(row["timestamp"])
        assert source.timestamp() == stamp and source.utcoffset() == timedelta(hours=offset)
        precise = json.loads(session_history({"mode": "read", "start_time": row["timestamp"], "end_time": row["timestamp"]},
                                           db=db, conversation_ref=ref))
        assert precise["messages"] == result["messages"]
        assert db.notebook_current(ref) == snapshot
        assert db.get_messages("main")[0]["timestamp"] == stamp
        assert row["content"] == "original body 1791756123.25"
        carrier = _batch_carrier([{"source_timestamp": stamp, "content": "due"}], db=db)
        assert "<timestamp>" not in carrier
        due = json.loads(carrier.splitlines()[2])[0]["due_at"]
        assert due == row["timestamp"]
        assert format_timestamp(snapshot["created_at"], profile_home=home) == model["last_update_time"]
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
        assert values == ["2026-10-12T06:02:03.25+08:00", "2026-10-11T22:02:03.25+00:00"]
    assert format_user_timestamp_marker(stamp).count("<timestamp>") == 1
    assert "-10:00" in format_user_timestamp_marker(stamp)
    reset_cache()


def test_valid_iso_null_and_invalid_absolute_time():
    assert format_timestamp("2026-10-12T07:22:03.250000+08:00") == "2026-10-12T07:22:03.250000+08:00"
    assert format_timestamp("2026-10-11T23:22:03Z") == "2026-10-11T23:22:03Z"
    assert format_timestamp(None) is None
    with pytest.raises(ValueError):
        format_timestamp("2026-10-12T07:22:03")


def test_numeric_fraction_is_preserved_without_rounding():
    value = "1791800714.1486568"
    rendered = format_timestamp(value)
    assert ".1486568" in rendered
    assert datetime.fromisoformat(rendered).tzinfo is not None
    assert ".+" not in format_timestamp(100.0)
    for invalid in ("not-time", float("nan"), float("inf")):
        with pytest.raises(ValueError):
            format_timestamp(invalid)
