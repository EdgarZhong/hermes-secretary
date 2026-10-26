"""Business completion and Notebook publication cannot restart or pause Scheduler."""

from copy import deepcopy

import pytest

from hermes_state import SessionDB
from secretary.notebook_store import NotebookStore
from secretary.schedules import SchedulerStore


@pytest.fixture
def owner(tmp_path):
    db = SessionDB(tmp_path / "state.db"); db.create_session("s", source="cli")
    db.append_message("s", "user", "review report", message_uid="a")
    ref = db.resolve_conversation_ref("s")
    result = SchedulerStore(db, ref, session_id="s").create("review report", "2035-01-01T09:00:00+00:00", "instant")
    assert result["success"]
    yield db, ref, result["schedule"]["schedule_id"]
    db.close()


@pytest.mark.parametrize("operation", ["complete", "archive"])
def test_notebook_business_state_cannot_control_schedule(owner, operation):
    db, ref, sid = owner
    before = dict(db._read_one("SELECT * FROM secretary_schedule_registry WHERE schedule_id=?", (sid,)))
    store = NotebookStore(db, ref, anchor_message_uid="a")
    item = store.create("matter", {"description": "review report", "completion_condition": "accepted"},
                        source_message_identities=[{"conversation_ref": ref, "message_uid": "a"}])["entry"]
    if operation == "complete":
        store.update(item["entry_id"], {"source_message_uids": ["a"], "done": True, "fields": {"description": "Report review completed"}})
    else:
        store.archive(item["entry_id"], "Completed review")
    store.commit(termination={"type": "forced"})
    assert dict(db._read_one("SELECT * FROM secretary_schedule_registry WHERE schedule_id=?", (sid,))) == before


def test_notebook_commit_failure_does_not_modify_schedule(owner, monkeypatch):
    db, ref, sid = owner
    before = deepcopy(dict(db._read_one("SELECT * FROM secretary_schedule_registry WHERE schedule_id=?", (sid,))))
    store = NotebookStore(db, ref, anchor_message_uid="a")
    def fail(*args, **kwargs):
        raise RuntimeError("pointer failure")
    monkeypatch.setattr(db, "_notebook_reselect_pointer_conn", fail)
    with pytest.raises(RuntimeError, match="pointer failure"):
        store.commit(termination={"type": "forced"})
    assert db.notebook_current(ref) is None
    assert dict(db._read_one("SELECT * FROM secretary_schedule_registry WHERE schedule_id=?", (sid,))) == before
