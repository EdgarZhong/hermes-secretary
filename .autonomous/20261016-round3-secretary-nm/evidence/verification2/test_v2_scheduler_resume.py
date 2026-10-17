"""Second Verification: resuming a future calendar occurrence must use native time semantics."""

from __future__ import annotations

from datetime import datetime, timezone
import json

import pytest

from tests.secretary.test_r3_scheduler import store


@pytest.mark.parametrize(
    "expression",
    [
        pytest.param("2030-04-06T10:00:00+00:00", id="one-shot-positive-control"),
        pytest.param("0 10 * * *", id="daily-calendar-future-occurrence"),
    ],
)
def test_resume_before_due_keeps_native_next_occurrence(store, monkeypatch, expression):
    import cron.jobs as native

    clock = [datetime(2030, 4, 6, 9, 0, tzinfo=timezone.utc)]
    monkeypatch.setattr(native, "_hermes_now", lambda: clock[0])
    created = store.create("Attend the daily 10:00 review", expression, "instant", now=clock[0].timestamp())
    assert created["success"] is True, created
    schedule_id = created["schedule"]["schedule_id"]
    assert created["schedule"]["next_due_at"] == "2030-04-06T10:00:00+00:00"

    clock[0] = datetime(2030, 4, 6, 9, 10, tzinfo=timezone.utc)
    paused = store.pause(schedule_id, now=clock[0].timestamp())
    assert paused["success"] is True and paused["schedule"]["state"] == "paused", paused

    clock[0] = datetime(2030, 4, 6, 9, 20, tzinfo=timezone.utc)
    # This is the native computation used by cron.jobs.resume_job when its stored
    # next occurrence is still future. No Scheduler helper supplies the oracle.
    native_next = native.compute_next_run(created["schedule"]["canonical_schedule"])
    assert native_next == "2030-04-06T10:00:00+00:00", native_next
    resumed = store.resume(schedule_id, now=clock[0].timestamp())
    assert resumed["success"] is True and resumed["schedule"]["state"] == "active", resumed
    listed = store.list(now=clock[0].timestamp())
    assert listed["success"] is True and listed["count"] == 1, listed
    evidence = {
        "expression": expression,
        "created_at": "2030-04-06T09:00:00+00:00",
        "paused_at": "2030-04-06T09:10:00+00:00",
        "resumed_at": clock[0].isoformat(),
        "created_next_due_at": created["schedule"]["next_due_at"],
        "native_next_occurrence": native_next,
        "resumed_next_due_at": resumed["schedule"]["next_due_at"],
        "durable_list_next_due_at": listed["schedules"][0]["next_due_at"],
        "resumed_notice": resumed.get("notice"),
        "resumed_schedule": resumed["schedule"],
    }
    print("SECOND_VERIFICATION_RESUME_EVIDENCE " + json.dumps(evidence, ensure_ascii=False))
    assert resumed["schedule"]["next_due_at"] == native_next, json.dumps(evidence, ensure_ascii=False)
    assert listed["schedules"][0]["next_due_at"] == native_next
