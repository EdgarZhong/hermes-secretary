"""F15: one-shot display times never reduce Scheduler definition precision."""

from datetime import datetime, timedelta
import json
from math import floor

import pytest

from hermes_state import SessionDB
from secretary.scheduler_time import parse_schedule_expression
from secretary.schedules import SchedulerStore

CLOCK = datetime.fromisoformat("2030-04-06T12:00:00.333333+05:30")
EXPLICIT = "2030-04-06T12:30:00.654321+05:30"


@pytest.mark.parametrize("expression", [EXPLICIT, "in 30m"])
@pytest.mark.parametrize("zone,offset", [("UTC", 0), ("Asia/Shanghai", 8)])
def test_create_list_update_project_once_times_without_rescheduling(tmp_path, monkeypatch, expression, zone, offset):
    # Only the native parser's current clock is controlled; parsing and recurrence code are real.
    monkeypatch.setattr("cron.jobs._hermes_now", lambda: CLOCK)
    (tmp_path / "config.yaml").write_text(f"timezone: {zone}\nscheduler:\n  enabled: true\nnoting:\n  enabled: false\n")
    db = SessionDB(tmp_path / "state.db")
    try:
        db.create_session("main", source="cli")
        ref = db.resolve_conversation_ref("main")
        parsed = []
        def native_parser(value):
            result = parse_schedule_expression(value)
            parsed.append(result)
            return result
        store = SchedulerStore(db, ref, session_id="main", parser=native_parser)
        created = store.create("Bring back the pending work", expression, "instant", now=CLOCK.timestamp())
        assert created["success"], created
        schedule = created["schedule"]
        sid = schedule["schedule_id"]
        def definition():
            return dict(db._read_one("SELECT * FROM secretary_schedule_registry WHERE schedule_id=?", (sid,)))
        raw = definition()
        canonical = json.loads(raw["canonical_schedule"])
        precise = datetime.fromisoformat(canonical["run_at"])
        assert precise.microsecond != 0 and len(parsed) == 1
        assert canonical == parsed[0]
        assert raw["expression"] == schedule["expression"] == expression
        assert raw["next_run_at"] == precise.timestamp()
        for item in [schedule, *store.list(now=CLOCK.timestamp())["schedules"]]:
            projected = datetime.fromisoformat(item["canonical_schedule"]["run_at"])
            next_due = datetime.fromisoformat(item["next_due_at"])
            assert projected.microsecond == next_due.microsecond == 0
            assert projected.tzinfo is not None and next_due.tzinfo is not None
            assert projected.timestamp() == next_due.timestamp() == floor(precise.timestamp())
            assert next_due.utcoffset() == timedelta(hours=offset)
            if expression == EXPLICIT:
                assert item["canonical_schedule"]["display"] == "once at 2030-04-06T12:30:00+05:30"
                assert canonical["display"] == "once at 2030-04-06 12:30"
            else:
                assert item["canonical_schedule"]["display"] == canonical["display"] == "once in 30m"
        assert definition() == raw, "list must not rewrite the canonical definition or advance next_due"
        changed = store.update(sid, name="Review pending work", now=CLOCK.timestamp() + 60)
        assert changed["success"] and changed["changed"]
        assert datetime.fromisoformat(changed["schedule"]["canonical_schedule"]["run_at"]).microsecond == 0
        assert changed["schedule"]["canonical_schedule"] == schedule["canonical_schedule"]
        after_update = definition()
        assert after_update["canonical_schedule"] == raw["canonical_schedule"]
        assert after_update["next_run_at"] == raw["next_run_at"]
        assert after_update["sequence"] == raw["sequence"]
        assert after_update["generation"] == raw["generation"] + 1
        noop = store.update(sid, schedule=expression, now=CLOCK.timestamp() + 120)
        assert noop["success"] and noop["changed"] is False
        assert noop["schedule"]["canonical_schedule"] == changed["schedule"]["canonical_schedule"]
        assert len(parsed) == 1, "a no-op must not reparse a relative expression into a new occurrence"
        assert definition() == after_update
        assert db._read_one("SELECT COUNT(*) FROM secretary_schedule_registry")[0] == 1
        assert db._read_one("SELECT COUNT(*) FROM secretary_pending_reminders")[0] == 0
        assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots")[0] == 0
    finally:
        db.close()
