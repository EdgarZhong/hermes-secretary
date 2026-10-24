"""V51: whole-second Notebook outputs preserve precise immutable source state."""

from copy import deepcopy
from datetime import datetime
import json
from threading import RLock
from types import SimpleNamespace

import pytest

from hermes_cli.cli_secretary_commands import notebook_command, propose_persistence_command
from secretary.framework_messages import publish_noting_completion
from secretary.notebook_store import NotebookStore
from secretary.noting_tools import notebook_create, notebook_update, notebook_work_show
from tests.secretary.test_r3_child import database as database, native_parent as native_parent, response
from tools.notebook_tool import notebook_show

EVIDENCE = "2026-10-17T12:34:56.654321+08:00"
EVIDENCE_DISPLAY = "2026-10-17T12:34:56+08:00"
CLOCK = datetime.fromisoformat("2026-10-17T14:15:16.987654+08:00")
CLOCK_DISPLAY = "2026-10-17T14:15:16+08:00"
SOURCE_RANGE = {"start_time": "2026-10-17T12:34:56.600000+08:00",
                "end_time": "2026-10-17T12:34:56.700000+08:00"}
DISPLAY_RANGE = {"start_time": EVIDENCE_DISPLAY, "end_time": EVIDENCE_DISPLAY}
DESCRIPTION = "Keep literal evidence text 2026-10-17T12:34:56.654321+08:00 unchanged."
FINISH = {"type": "finish_noting", "reason": "Checked the original evidence"}


@pytest.fixture
def time_book(database, monkeypatch):
    # Only capability discovery is controlled; Store/immutable versions/provenance are real.
    monkeypatch.setattr("secretary.noting_runtime.noting_trigger_gate", lambda *a, **k: (True, ""))
    from pathlib import Path
    Path(database.db_path).with_name("config.yaml").write_text(
        "timezone: UTC\nnoting:\n  enabled: true\n  persistence_proposal:\n    char_threshold: 1\n")
    database.append_message("parent", "user", "Original source evidence", message_uid="time-source",
                            timestamp=datetime.fromisoformat(EVIDENCE).timestamp())
    ref = database.resolve_conversation_ref("parent")
    store = NotebookStore(database, ref, anchor_message_uid="time-source", clock=lambda: CLOCK)
    child = SimpleNamespace(_session_db=database, _secretary_noting_child=True,
        _secretary_parent_conversation_ref=ref, _secretary_noting_anchor_uid="time-source",
        _secretary_noting_profile="NOTING", _noting_notebook_store=store, _noting_notebook_lock=store.lock)
    args = {"entry_type": "matter", "fields": {
        "description": DESCRIPTION, "completion_condition": "reviewed",
        "last_progress_time": EVIDENCE, "processing_note": "Retain the supported responsibility"},
        "source_message_uids": ["time-source"],
        "source_time_range": deepcopy(SOURCE_RANGE)}
    maintained = json.loads(notebook_create(child, args))
    assert maintained["success"], maintained
    question = deepcopy(args)
    question["entry_type"] = "question"
    question["fields"] = {"description": "What remains unresolved?", "unresolved_points": "Scope",
                          "last_discussion_time": EVIDENCE}
    assert json.loads(notebook_create(child, question))["success"]
    situation = deepcopy(args)
    situation["entry_type"] = "situation"
    situation["fields"] = {"description": "Expressed circumstances", "subjects": ["user"],
                           "time_context": DESCRIPTION}
    situation["source_time_range"] = None
    assert json.loads(notebook_create(child, situation))["success"]
    return child, store, maintained


def assert_projected_entry(entry):
    assert entry["source_message_uids"] == ["time-source"]
    assert "source_message_identities" not in entry
    assert "conversation_ref" not in entry
    assert entry["evidence_time"] == "2026-10-17T04:34:56+00:00"
    assert "evidence_time" not in entry["fields"]
    assert entry["created_at"] == CLOCK_DISPLAY
    assert entry["updated_at"] == CLOCK_DISPLAY
    if entry["entry_type"] == "matter":
        assert entry["last_processed_at"] == CLOCK_DISPLAY
        assert entry["fields"]["description"] == DESCRIPTION
        assert entry["fields"]["last_progress_time"] == EVIDENCE_DISPLAY
        assert entry["source_time_range"] == DISPLAY_RANGE
    elif entry["entry_type"] == "question":
        assert entry["last_processed_at"] is None
        assert entry["fields"]["last_discussion_time"] == EVIDENCE_DISPLAY
    else:
        assert entry["fields"]["time_context"] == DESCRIPTION
        assert "evidence_time" not in entry["fields"]
        assert entry["source_time_range"] is None


@pytest.mark.parametrize("surface", ["create", "working_show", "main_show", "slash", "web_read", "proposal", "framework"])
def test_real_store_times_are_projected_only_at_product_outputs(time_book, surface):
    child, store, maintained = time_book
    db, ref = child._session_db, store.conversation_ref
    raw = store.snapshot_state()
    assert raw["work"][0]["created_at"] == CLOCK.isoformat()
    assert raw["work"][0]["source_time_range"] == SOURCE_RANGE
    if surface == "create":
        assert_projected_entry(maintained["entry"])
    elif surface == "working_show":
        view = json.loads(notebook_work_show(child, {}))
        for entries in view["payload"].values():
            for entry in entries:
                assert_projected_entry(entry)
    else:
        result = store.commit(termination=FINISH)
        snapshot = db.notebook_current(ref)
        if surface == "main_show":
            view = json.loads(notebook_show(db=db, conversation_ref=ref, effective_enabled=True))
            for entries in view["payload"].values():
                for entry in entries:
                    assert_projected_entry(entry)
        elif surface == "proposal":
            command = propose_persistence_command(db, "parent")
            assert command.prompt, command.output
            view = json.loads(command.prompt.split("Current Notebook Snapshot (data):\n", 1)[1])
            for entries in view["payload"].values():
                for entry in entries:
                    assert_projected_entry(entry)
        else:
            if surface == "slash":
                output = notebook_command(db, "parent").output
            elif surface == "web_read":
                from secretary.web_read import notebook_read
                output = notebook_read(db, "parent")["output"]
            else:
                parent = SimpleNamespace(_session_db=db, session_id="parent", _secretary_conversation_ref=ref,
                    _session_messages=db.get_messages_as_conversation("parent"), _session_persist_lock=RLock(),
                    _secretary_main_turn_running=False, platform="cli", side_agent=False, _persist_disabled=False)
                assert publish_noting_completion(parent, result, termination=FINISH, summary="Checked evidence")
                row = db.get_messages("parent")[-1]
                assert row["display_metadata"]["noting_run_output"] is True
                assert row["content"] == parent._session_messages[-1]["content"]
                output = row["content"]
                assert "PERSISTENCE PROPOSAL REQUEST" in output
            assert 'source_message_uids: ["time-source"]' in output
            assert "source_message_identities" not in output
            assert "conversation_ref" not in output
            assert f'created_at: "{CLOCK_DISPLAY}"' in output
            assert f'last_processed_at: "{CLOCK_DISPLAY}"' in output
            assert 'evidence_time: "2026-10-17T04:34:56+00:00"\n' in output
            assert f"last_progress_time: {EVIDENCE_DISPLAY}\n" in output
            assert f"last_discussion_time: {EVIDENCE_DISPLAY}\n" in output
            rendered_range = next(line.split("source_time_range: ", 1)[1] for line in output.splitlines()
                                  if "source_time_range: {" in line)
            assert json.loads(rendered_range) == DISPLAY_RANGE
            assert DESCRIPTION in output
        assert db.notebook_current(ref) == snapshot
    assert store.snapshot_state() == raw
    assert store.show()["work"][0]["created_at"] == CLOCK.isoformat()


def test_reading_projected_values_never_changes_precise_versions_or_noop(time_book):
    from secretary.notebook_contract import public_state
    child, store, _maintained = time_book
    raw = store.snapshot_state()
    entry = raw["work"][0]
    db = child._session_db
    before = [tuple(row) for row in db._read_all("SELECT * FROM secretary_notebook_item ORDER BY id")]
    notebook_work_show(child, {})
    noop = json.loads(notebook_update(child, {"entry_id": entry["entry_id"], "fields": {"description": DESCRIPTION}}))
    assert noop["success"] and noop["changed"] is False
    assert noop["entry"]["version_id"] == entry["version_id"]
    assert store.snapshot_state() == raw
    assert public_state(raw)["work"][0]["source_time_range"] == SOURCE_RANGE
    assert [tuple(row) for row in db._read_all("SELECT * FROM secretary_notebook_item ORDER BY id")] == before
    invalid = json.loads(notebook_create(child, {"entry_type": "matter",
        "fields": {"description": "Unsupported", "completion_condition": "none"},
        "source_message_uids": ["missing"]}))
    assert invalid["success"] is False
    assert invalid["error"]["code"] == "source_unavailable"
    assert store.snapshot_state() == raw
    result = store.commit(termination=FINISH)
    restored = NotebookStore(db, store.conversation_ref, anchor_message_uid="time-source")
    assert restored.snapshot_state() == raw
    assert db.notebook_snapshot_audit(result["snapshot_id"])["payload"]["work"][0]["created_at"] == CLOCK.isoformat()


def test_native_child_initial_and_continuation_controls_share_time_projection(time_book, native_parent):
    from secretary.noting_child import DEFAULT_NOTING_TASK_INSTRUCTION, run_noting_task
    child, store, _maintained = time_book
    store.commit(termination=FINISH)
    parent, client = native_parent
    db, ref = child._session_db, store.conversation_ref
    raw = deepcopy(db.notebook_current(ref)["payload"])
    parent._session_messages = db.get_messages_as_conversation("parent")
    wires = []
    def provider(**kwargs):
        wires.append(deepcopy(kwargs))
        return response("Reviewing the same working state.")
    client.chat.completions.create.side_effect = provider
    admission = db.noting_admit(ref, "time-source", kind="manual")
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=ref,
        anchor_message_uid="time-source", trigger_type="manual", runtime_profile="NOTING",
        task_instruction=DEFAULT_NOTING_TASK_INSTRUCTION)
    assert outcome.committed and outcome.turns == len(wires) == 5, outcome
    for wire in wires:
        control = [msg["content"] for msg in wire["messages"]
                   if "<noting-task-data>" in str(msg.get("content"))][-1]
        data = json.loads(control.split("<noting-task-data>\n", 1)[1].split("\n</noting-task-data>", 1)[0])
        for entries in data["working_notebook"].values():
            for entry in entries:
                assert_projected_entry(entry)
    assert "previous native Turn" in wires[-1]["messages"][-1]["content"]
    assert db.notebook_current(ref)["payload"] == raw
