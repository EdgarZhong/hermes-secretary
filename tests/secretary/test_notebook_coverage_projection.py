"""Coverage is useful model data, independently of creation time and audit IDs."""

import json
from copy import deepcopy
from types import SimpleNamespace

import pytest

from hermes_state import SessionDB
from hermes_time import format_timestamp
from secretary.notebook_render import model_notebook_view, show_notebook
from secretary.notebook_store import NotebookStore
from secretary.noting_notifications import completion_body
from secretary.noting_tools import initialize_notebook_work, notebook_work_show
from tools.notebook_tool import notebook_show


@pytest.fixture
def history(tmp_path):
    db = SessionDB(tmp_path / "state.db")
    db.create_session("main", source="cli")
    for uid, role, timestamp in [("early-audit-anchor", "user", 100),
                                 ("late-audit-anchor", "assistant", 200)]:
        db.append_message("main", role, "Discuss the visit", message_uid=uid, timestamp=timestamp)
    ref = db.resolve_conversation_ref("main")
    snapshots = []
    for uid in ("early-audit-anchor", "late-audit-anchor"):
        book = NotebookStore(db, ref, anchor_message_uid=uid)
        receipt = book.commit(termination={"type": "finish_noting", "reason": "Checked"})
        snapshot = db.notebook_snapshot_audit(receipt["snapshot_id"])
        snapshot["created_at"] = 2000
        snapshots.append(snapshot)
    yield db, ref, snapshots
    db.close()


def options(db):
    return dict(termination={"type": "finish_noting"}, summary="Checked",
                settings=SimpleNamespace(persistence_proposal_char_threshold=100000,
                                         persistence_proposal_entry_threshold=1000),
                profile_home=db.db_path.parent, db=db)


def test_completion_distinguishes_t01_evidence_boundaries_with_equal_creation_time(history):
    db, _, snapshots = history
    bodies = [completion_body(snapshot, **options(db)) for snapshot in snapshots]
    assert bodies[0] != bodies[1]
    for body, count, timestamp in zip(bodies, (1, 2), (100, 200)):
        assert f'"history_message_count": {count}' in body
        assert format_timestamp(timestamp, profile_home=db.db_path.parent) in body
        assert "Created at: " + format_timestamp(2000, profile_home=db.db_path.parent) in body
        assert "audit-anchor" not in body


def test_main_show_distinguishes_t01_evidence_boundaries_and_keeps_default_api(history):
    db, ref, snapshots = history
    views = [model_notebook_view(show_notebook(snapshot), db=db) for snapshot in snapshots]
    assert views[0] != views[1]
    assert [view["evidence_coverage"]["history_message_count"] for view in views] == [1, 2]
    result = json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=True,
                                      model_visible=True))
    assert result["evidence_coverage"] == views[1]["evidence_coverage"]
    public = json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=True))
    assert public["coverage"] == {"anchor_message_uid": "late-audit-anchor"}
    assert "evidence_coverage" not in public


def test_working_show_and_initial_continuation_controls_share_frozen_boundary(history):
    from secretary.noting_child import _working_control

    db, ref, _ = history
    child = SimpleNamespace(_session_db=db, _secretary_parent_conversation_ref=ref,
                            _secretary_noting_anchor_uid="early-audit-anchor",
                            _secretary_noting_profile="NOTING", _secretary_noting_child=True)
    initialize_notebook_work(child, trigger_type="manual")
    db.append_message("main", "user", "New correction outside the frozen task", message_uid="new", timestamp=300)
    shown = json.loads(notebook_work_show(child, {}))
    for _ in range(2):
        control = _working_control(child)
        data = json.loads(control.split("<noting-task-data>\n", 1)[1].rsplit("\n</noting-task-data>", 1)[0])
        assert data["evidence_coverage"] == shown["evidence_coverage"]
        assert data["evidence_coverage"]["history_message_count"] == 1
        assert data["evidence_coverage"]["through_time"] == format_timestamp(100)
        assert "early-audit-anchor" not in control


@pytest.mark.parametrize("failure", ["no_database", "missing_anchor", "database_error"])
def test_unresolvable_coverage_never_uses_creation_time_or_aborts_payload(history, monkeypatch, failure):
    db, _, snapshots = history
    snapshot = deepcopy(snapshots[0])
    if failure == "missing_anchor":
        snapshot["anchor_message_uid"] = "missing"
    if failure == "database_error":
        monkeypatch.setattr(db, "_notebook_anchor_positions_conn", lambda *args: (_ for _ in ()).throw(RuntimeError("busy")))
    view = model_notebook_view(show_notebook(snapshot), db=None if failure == "no_database" else db)
    assert view["evidence_coverage"]["status"] == "unavailable"
    assert "through_time" not in view["evidence_coverage"]
    assert view["payload"] == snapshot["payload"]


def test_equal_timestamp_boundaries_still_differ_by_history_extent(history):
    db, _, snapshots = history
    db._execute_write(lambda conn: conn.execute("UPDATE messages SET timestamp=100 WHERE message_uid='late-audit-anchor'"))
    views = [model_notebook_view(show_notebook(snapshot), db=db) for snapshot in snapshots]
    assert views[0]["evidence_coverage"]["through_time"] == views[1]["evidence_coverage"]["through_time"]
    assert views[0]["evidence_coverage"]["history_message_count"] == 1
    assert views[1]["evidence_coverage"]["history_message_count"] == 2


def test_coverage_uses_the_bound_profile_timezone(history):
    db, _, snapshots = history
    db.db_path.with_name("config.yaml").write_text("timezone: Asia/Shanghai\n")
    view = model_notebook_view(show_notebook(snapshots[0]), db=db)
    assert view["evidence_coverage"]["through_time"] == "1970-01-01T08:01:40+08:00"


def test_carried_history_does_not_advance_older_notebook_coverage(history):
    db, _, snapshots = history
    before = [model_notebook_view(show_notebook(snapshot), db=db)["evidence_coverage"] for snapshot in snapshots]
    db.archive_and_compact("main", [{"role": "assistant", "content": "Compaction summary",
                                    "message_uid": "summary", "_compressed_summary": True},
                                   *db.get_messages_as_conversation("main")])
    db.append_message("main", "user", "Later correction", message_uid="correction", timestamp=3000)
    after = [model_notebook_view(show_notebook(snapshot), db=db)["evidence_coverage"] for snapshot in snapshots]
    assert after == before
