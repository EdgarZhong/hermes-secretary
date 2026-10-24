"""Persistence proposals project one complete real Snapshot on normal send paths."""

from contextlib import contextmanager
import json
import queue
import threading

import pytest

from hermes_cli.cli_secretary_commands import PERSISTENCE_PROPOSAL_INSTRUCTION, propose_persistence_command
from hermes_time import format_timestamp
from secretary.notebook_render import readable_notebook_state, show_notebook
from secretary.notebook_store import NotebookStore
from tests.hermes_state._secretary_notebook_harness import add, make, open_notebook_db, ref_of


@pytest.fixture
def committed(tmp_path):
    (tmp_path / "config.yaml").write_text("noting:\n  enabled: true\n")
    db = open_notebook_db(tmp_path / "state.db")
    make(db, "main", source="cli")
    add(db, "main", "The visit is complete; keep its reusable lessons.", "user-source", timestamp=100)
    add(db, "main", "The next visit's dates are still unknown.", "assistant-source", role="assistant", timestamp=150)
    add(db, "main", "The reviewed history ends here.", "private-coverage-anchor", role="assistant", timestamp=200)
    ref = ref_of(db, "main")
    store = NotebookStore(db, ref, anchor_message_uid="private-coverage-anchor")
    matter = store.create("matter", {"description": "The visit is complete.", "completion_condition": "Visit concluded"},
                          done=True, source_message_uids=["user-source"],
                          source_time_ranges=[{"start_time": "1970-01-01T00:01:30Z", "end_time": "1970-01-01T00:01:50Z"}])["entry"]
    store.create("situation", {"description": "The host prefers concise plans.", "subjects": ["host"]},
                 source_message_uids=["user-source"])
    store.create("question", {"description": "When is the next visit?"}, source_message_uids=["assistant-source"])
    store.create("candidate", {"description": "Retain the completed visit's lessons.", "targets": ["memory"],
                               "notebook_refs": [matter["entry_id"]], "source_types": ["matter"]},
                 source_message_uids=[])
    store.commit(termination={"type": "finish_noting", "reason": "Retained the visit and its open follow-up"})
    add(db, "main", "A later message is outside the frozen coverage.", "after-snapshot", timestamp=300)
    snapshot = db.notebook_current(ref)
    expected = readable_notebook_state(snapshot["payload"], profile_home=tmp_path, db=db, conversation_ref=ref)
    try:
        yield db, ref, snapshot, expected
    finally:
        db.close()


def dump(db):
    with db._read_ctx() as conn:
        return list(conn.iterdump())


def proposal_data(prompt):
    assert prompt.startswith(PERSISTENCE_PROPOSAL_INSTRUCTION + "\n\nCurrent Notebook Snapshot (data):\n")
    return json.loads(prompt.split("Current Notebook Snapshot (data):\n", 1)[1]
                      .split("\n\nUser's additional request:\n", 1)[0])


def assert_projection(prompt, committed, *, unavailable=False):
    db, ref, snapshot, expected = committed
    projected = proposal_data(prompt)
    assert projected["conversation_ref"] == ref
    assert projected["payload"] == expected
    assert all(projected["payload"][section] for section in ("work", "situations", "discussion", "candidates"))
    matter = projected["payload"]["work"][0]
    assert matter["done"] is True and projected["payload"]["candidates"][0]["done"] is False
    assert matter["entry_id"] == snapshot["payload"]["work"][0]["entry_id"]
    assert matter["version_id"] == snapshot["payload"]["work"][0]["version_id"]
    assert matter["source_message_uids"] == ["user-source"]
    assert matter["source_time_ranges"] == [{"start_time": format_timestamp(90, profile_home=db.db_path.parent),
                                               "end_time": format_timestamp(110, profile_home=db.db_path.parent)}]
    assert matter["evidence_time"] == [format_timestamp(100, profile_home=db.db_path.parent), *matter["source_time_ranges"]]
    assert {"snapshot_id", "base_snapshot_id", "coverage"}.isdisjoint(projected)
    assert "anchor_message_uid" not in prompt and "private-coverage-anchor" not in prompt
    assert snapshot["snapshot_id"] not in prompt
    coverage = projected["evidence_coverage"]
    if unavailable:
        assert coverage["status"] == "unavailable"
        assert "from_time" not in coverage and "through_time" not in coverage
    else:
        assert coverage["status"] == "resolved" and coverage["history_message_count"] == 3
        assert coverage["from_time"] == format_timestamp(100, profile_home=db.db_path.parent)
        assert coverage["through_time"] == format_timestamp(200, profile_home=db.db_path.parent)
        assert coverage["through_role"] == "assistant"
        assert coverage["through_time"] != format_timestamp(snapshot["created_at"], profile_home=db.db_path.parent)
    return projected


@pytest.mark.parametrize("coverage_failure", [False, True])
def test_proposal_complete_snapshot_and_real_coverage_are_readonly(committed, monkeypatch, coverage_failure):
    db, ref, snapshot, _expected = committed
    before = dump(db)
    if coverage_failure:
        def unavailable(*args, **kwargs):
            raise OSError("Coverage history temporarily unavailable")
        monkeypatch.setattr(db, "_notebook_anchor_positions_conn", unavailable)
    result = propose_persistence_command(db, "main", "Keep Exact CASE 和中文；proposal only")
    assert result.prompt and not result.output
    assert result.prompt.endswith("\n\nUser's additional request:\nKeep Exact CASE 和中文；proposal only")
    assert_projection(result.prompt, committed, unavailable=coverage_failure)
    assert db.notebook_current(ref) == snapshot and dump(db) == before
    external = show_notebook(snapshot, db=db)
    assert external["snapshot_id"] == snapshot["snapshot_id"]
    assert external["coverage"] == {"anchor_message_uid": "private-coverage-anchor"}
    assert "evidence_coverage" not in external


def test_cli_pending_input_receives_projected_complete_snapshot(committed, monkeypatch):
    from cli import HermesCLI
    db, ref, snapshot, _expected = committed
    cli = HermesCLI.__new__(HermesCLI)
    cli.session_id = "main"
    cli._session_db = db
    cli._pending_input = queue.Queue()
    cli._pending_resume_sessions = None
    cli.config = {}
    monkeypatch.setattr("hermes_cli.plugins.fire_pre_command_hook", lambda **kw: None)
    before = dump(db)
    assert cli.process_command("/propose-persistence Keep CLI CASE 中文")
    prompt = cli._pending_input.get_nowait()
    assert_projection(prompt, committed)
    assert prompt.endswith("Keep CLI CASE 中文") and cli._pending_input.empty()
    assert cli.session_id == "main" and db.notebook_current(ref) == snapshot
    assert dump(db) == before


def test_gateway_send_message_receives_projected_complete_snapshot(committed, monkeypatch):
    from tui_gateway import server
    db, ref, snapshot, _expected = committed
    sid = "proposal-projection-runtime"
    session = {"agent": None, "session_key": "main", "profile_home": str(db.db_path.parent),
               "history": [], "history_lock": threading.Lock(), "running": False, "source": "tui"}
    monkeypatch.setitem(server._sessions, sid, session)
    @contextmanager
    def session_db(_session):
        yield db
    monkeypatch.setattr(server, "_session_db", session_db)
    monkeypatch.setattr(server, "_session_uses_compute_host", lambda _session: False)
    before = dump(db)
    result = server._methods["slash.exec"]("projection-test", {"session_id": sid,
                                      "command": "/propose-persistence Keep Gateway CASE 中文"})["result"]
    assert result["type"] == "send"
    assert_projection(result["message"], committed)
    assert result["message"].endswith("Keep Gateway CASE 中文")
    assert session["history"] == [] and session["session_key"] == "main"
    assert db.notebook_current(ref) == snapshot and dump(db) == before
