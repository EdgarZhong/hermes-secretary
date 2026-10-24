"""R3 C1 contract scenarios. Source authored in CLOUD_CODE; execution is NOT_RUN.

Run locally through scripts/run_tests.sh after the planned C5/C8/C9 integration.
The real-DB cases reuse the native SessionDB harness; no model/provider is needed.
"""

import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from threading import RLock

import pytest

from hermes_state_secretary_notebook import NotebookError
from secretary.notebook_contract import LEGACY_STATUSES, REQUIRED_FIELDS, SECTIONS, TYPE_SECTIONS
from secretary.notebook_model import NotebookValidationError, NotebookWorkingState
from secretary.notebook_render import render_notebook, show_notebook
from secretary.notebook_store import NotebookStore
from tests.hermes_state._secretary_notebook_harness import add, make, open_notebook_db, ref_of

REF = "conv_owner"
SOURCE = {"conversation_ref": REF, "message_uid": "m1"}
EVIDENCE = "2020-01-01T12:00:00+00:00"
RANGE = {"start_time": "1970-01-01T00:01:39+00:00", "end_time": "1970-01-01T00:01:41+00:00"}
FINISH = {"type": "finish_noting", "reason": "Reconciled the indexed information."}
FIELDS = {
    "matter": {"description": "Plan the visit", "completion_condition": "Dates agreed"},
    "action": {"description": "Ask for dates", "owner": "user", "completion_condition": "Reply received"},
    "situation": {"description": "Dates are undecided", "subjects": ["family"], "time_context": "Date unknown"},
    "implicit_gap": {"description": "The host is unknown", "situation_ref": "missing",
                     "missing_information": "Who is hosting?", "impact": "Cannot confirm dates",
                     "resolution_condition": "The user identifies the host"},
    "question": {"description": "Which dates work?", "unresolved_points": "Availability"},
    "insight": {"description": "The date is the blocker", "certainty": "tentative", "qualification": "This visit"},
    "decision": {"description": "Wait before booking", "scope": "This visit",
                 "valid_when": "Dates are unknown", "ends_when": "Dates are agreed"},
    "candidate": {"description": "Retain the visit outcome", "targets": ["memory"],
                  "notebook_refs": [], "source_types": []},
}


class Clock:
    def __init__(self):
        self.calls = 0

    def __call__(self):
        self.calls += 1
        return datetime(2030, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=self.calls)


def pure(clock=None):
    return NotebookWorkingState(REF, validate_source_identity=lambda source: source == SOURCE,
                                validate_source_range=lambda interval: interval == RANGE, clock=clock)


def create(book, entry_type="matter", *, fields=None, uid="m1", sources=True, **kwargs):
    body = deepcopy(FIELDS[entry_type] if fields is None else fields)
    if entry_type == "implicit_gap" and body["situation_ref"] == "missing":
        body["situation_ref"] = create(book, "situation", uid=uid)["entry_id"]
    return book.create(entry_type, body, source_message_identities=(
        [{"conversation_ref": book.conversation_ref, "message_uid": uid}] if sources else []), **kwargs)["entry"]


@pytest.fixture
def db(tmp_path):
    database = open_notebook_db(tmp_path / "state.db")
    make(database, "s")
    add(database, "s", "Discuss the visit", "m1", timestamp=100)
    add(database, "s", "Decide the next step", "m2", timestamp=200)
    add(database, "s", "Review the outcome", "m3", timestamp=300)
    yield database
    database.close()


def store(db, anchor="m1", **kwargs):
    return NotebookStore(db, ref_of(db, "s"), anchor_message_uid=anchor, **kwargs)


def version_count(db):
    return db._read_one("SELECT COUNT(*) FROM secretary_notebook_item")[0]


@pytest.mark.parametrize("entry_type", list(TYPE_SECTIONS))
def test_types_have_stable_identity_immutable_versions_and_reopenable_done(entry_type):
    book = pure()
    entry = create(book, entry_type)
    assert set(book.show()) == set(SECTIONS)
    assert book.show()[TYPE_SECTIONS[entry_type]][-1] == entry
    original_id, original_version = entry["entry_id"], entry["version_id"]
    assert entry["done"] is False and "status" not in entry
    for done in (True, False):
        result = book.update(original_id, {"done": done})
        assert result["success"] and result["changed"]
        assert result["entry"]["done"] is done
        assert result["entry"]["entry_id"] == original_id
        assert result["entry"]["version_id"] != original_version
        original_version = result["entry"]["version_id"]
    assert "type" not in entry and "archived" not in entry


@pytest.mark.parametrize("entry_type,status", [(kind, status) for kind, statuses in LEGACY_STATUSES.items()
                                              for status in statuses])
def test_legacy_status_matrix_reads_real_immutable_versions_without_rewriting(db, entry_type, status):
    from secretary.notebook_items import insert_item_conn

    book = store(db)
    original = create(book, entry_type)
    state = book.snapshot_state()
    section = TYPE_SECTIONS[entry_type]
    legacy = next(entry for entry in state[section] if entry["entry_id"] == original["entry_id"])
    legacy.pop("done")
    legacy["status"] = status
    stored = db._execute_write(lambda conn: insert_item_conn(conn, book.conversation_ref, legacy, original["version_id"]))
    state[section] = [stored if entry["entry_id"] == original["entry_id"] else entry for entry in state[section]]
    snapshot_id = db.notebook_commit_snapshot(book.conversation_ref, state, anchor_message_uid="m1", termination=FINISH)
    item_json = db._read_one("SELECT payload_json FROM secretary_notebook_item WHERE id=?", (stored["version_id"],))[0]
    snapshot_json = db._read_one("SELECT payload_json FROM secretary_notebook_snapshots WHERE snapshot_id=?", (snapshot_id,))[0]
    assert json.loads(item_json)["status"] == status and "done" not in json.loads(item_json)
    before_count = version_count(db)
    terminal = {"completed", "terminated", "expired", "resolved", "invalid", "answered", "withdrawn", "superseded", "revoked"}
    for _read in range(2):
        restored = store(db).get(original["entry_id"])
        assert restored["entry_id"] == original["entry_id"] and restored["version_id"] == stored["version_id"]
        assert restored["done"] is (status in terminal) and "status" not in restored
        assert original["fields"]["description"] in restored["fields"]["description"]
        assert status.replace("_", " ") in restored["fields"]["description"]
        assert restored["fields"]["description"].count("Earlier record marked") == 1
        if status == "pending":
            assert "does not establish whether work had started" in restored["fields"]["description"]
        if entry_type == "candidate":
            assert "does not establish authorization or an actual write" in restored["fields"]["description"]
    assert version_count(db) == before_count
    assert db._read_one("SELECT payload_json FROM secretary_notebook_item WHERE id=?", (stored["version_id"],))[0] == item_json
    assert db._read_one("SELECT payload_json FROM secretary_notebook_snapshots WHERE snapshot_id=?", (snapshot_id,))[0] == snapshot_json


@pytest.mark.parametrize("entry_type,field", [(kind, field) for kind, fields in REQUIRED_FIELDS.items()
                                             for field in fields])
def test_missing_required_field_is_atomic(entry_type, field):
    book = pure()
    body = deepcopy(FIELDS[entry_type])
    if entry_type == "implicit_gap":
        body["situation_ref"] = create(book, "situation")["entry_id"]
    body.pop(field)
    before = book.snapshot_state()
    with pytest.raises(NotebookValidationError) as error:
        book.create(entry_type, body, source_message_identities=[SOURCE])
    assert error.value.code == "invalid_argument"
    assert book.snapshot_state() == before


@pytest.mark.parametrize("entry_type", list(TYPE_SECTIONS))
def test_every_type_including_candidate_requires_original_provenance(entry_type):
    book = pure()
    body = deepcopy(FIELDS[entry_type])
    if entry_type == "implicit_gap":
        body["situation_ref"] = create(book, "situation")["entry_id"]
    before = book.snapshot_state()
    with pytest.raises(NotebookValidationError):
        book.create(entry_type, body)
    assert book.snapshot_state() == before


def test_noop_and_reads_never_renew_runtime_or_evidence_times():
    clock = Clock()
    book = pure(clock)
    body = {**FIELDS["matter"], "last_progress_time": EVIDENCE, "blocker": None}
    entry = create(book, fields=body)
    assert "blocker" not in entry["fields"]
    before = book.snapshot_state()
    for changes in ({"fields": {"description": body["description"]}}, {"fields": {"blocker": None}},
                    {"fields": {"domains": []}}, {"done": False}, {"relations": []}):
        assert book.update(entry["entry_id"], changes)["changed"] is False
    book.show()["work"][0]["fields"].clear()
    book.get(entry["entry_id"])["fields"].clear()
    assert book.snapshot_state() == before
    assert clock.calls == 1
    changed = book.update(entry["entry_id"], {"fields": {"description": "Dates are being checked"}})["entry"]
    assert changed["created_at"] == entry["created_at"]
    assert changed["fields"]["last_progress_time"] == EVIDENCE
    assert changed["last_processed_at"] is None
    processed = book.update(entry["entry_id"], {"fields": {"processing_note": "Retained the unfinished responsibility"}})["entry"]
    assert processed["last_processed_at"] == processed["updated_at"]
    assert book.update(entry["entry_id"], {"fields": {"processing_note": processed["fields"]["processing_note"]}})["changed"] is False
    assert clock.calls == 3


def test_gap_identification_clock_does_not_follow_rewrite_or_evidence_time():
    book = pure(Clock())
    gap = create(book, "implicit_gap")
    revised = book.update(gap["entry_id"], {"fields": {"description": "Host remains unknown",
                                                     "processing_note": "Retained because dates depend on the host"}})["entry"]
    assert revised["created_at"] == gap["created_at"]
    assert revised["updated_at"] != gap["updated_at"]
    assert "evidence_time" not in revised["fields"]


def test_fields_merge_arrays_replace_and_null_clears_optional_singletons():
    book = pure()
    entry = create(book, fields={**FIELDS["matter"], "domains": ["family", "travel"], "blocker": "No reply"})
    result = book.update(entry["entry_id"], {"fields": {"domains": ["travel"], "blocker": None}})["entry"]
    assert result["fields"] == {**FIELDS["matter"], "domains": ["travel"]}
    assert book.update(entry["entry_id"], {"fields": {"domains": []}})["entry"]["fields"]["domains"] == []
    before = book.snapshot_state()
    for changes in ({}, {"fields": {"description": None}}, {"fields": {"owner": None}},
                    {"fields": {"domains": None}}, {"entry_type": "action"}, {"version_id": "999"},
                    {"created_at": EVIDENCE}, {"candidate_refs": []}, {"relations": None}):
        with pytest.raises(NotebookValidationError):
            book.update(entry["entry_id"], changes)
        assert book.snapshot_state() == before


@pytest.mark.parametrize("patch", [
    {"fields": {"domains": ["travel", "travel"]}},
    {"fields": {"external_refs": ["task-1", "task-1"]}},
    {"fields": {"evidence_time": "2026-10-16T12:00:00"}},
    {"fields": {"description": ["not text"]}},
    {"fields": {"schedule": "in 1h"}},
    {"status": "done"},
    {"source_message_identities": [SOURCE, SOURCE]},
    {"source_time_range": {"start_time": EVIDENCE}},
    {"source_time_range": {"start_time": "2021-01-01T00:00:00Z", "end_time": EVIDENCE}},
])
def test_invalid_patch_never_changes_working_state(patch):
    book = pure()
    entry = create(book)
    before = book.snapshot_state()
    with pytest.raises(NotebookValidationError):
        book.update(entry["entry_id"], patch)
    assert book.snapshot_state() == before


def test_typed_operations_return_structured_error_guidance_without_side_effects():
    book = pure()
    entry = create(book)
    invalid_operations = [
        lambda: book.update(entry["entry_id"], {}),
        lambda: book.update(entry["entry_id"], {"entry_type": "question"}),
        lambda: book.create("unknown", FIELDS["matter"], source_message_identities=[SOURCE]),
        lambda: book.archive(entry["entry_id"], "   "),
    ]
    before = book.snapshot_state()
    for operation in invalid_operations:
        with pytest.raises(NotebookValidationError) as error:
            operation()
        result = error.value.as_result()
        assert result["success"] is False
        assert {"code", "message", "next_action"} <= result["error"].keys()
        assert book.snapshot_state() == before
    result = book.update(entry["entry_id"], {"fields": {"blocker": "Paused while awaiting dates"}})
    assert result["entry"]["done"] is False and result["changed"]
    assert result["entry"]["fields"]["blocker"] == "Paused while awaiting dates"


def test_candidates_keep_sources_in_place_map_labels_and_derive_reverse_refs():
    book = pure()
    matter = create(book)
    gap = create(book, "implicit_gap")
    candidate = create(book, "candidate", fields={**FIELDS["candidate"],
        "notebook_refs": [matter["entry_id"], gap["entry_id"]], "source_types": ["matter", "situation"]}, sources=False)
    assert book.get(matter["entry_id"])["candidate_refs"] == [candidate["entry_id"]]
    original_source_version = matter["version_id"]
    updated = book.update(matter["entry_id"], {"fields": {"description": "New information about the same visit"}})["entry"]
    assert updated["version_id"] != original_source_version
    assert book.get(candidate["entry_id"])["fields"]["notebook_refs"] == [matter["entry_id"], gap["entry_id"]]
    raw = book.snapshot_state()
    assert all("candidate_refs" not in row for rows in raw.values() for row in rows)
    before = book.snapshot_state()
    for fields in ({"notebook_refs": [matter["entry_id"], matter["entry_id"]]}, {"source_types": ["matter"]},
                   {"source_types": ["implicit_gap"]}, {"targets": ["memory", "memory"]},
                   {"notebook_refs": [candidate["entry_id"]]}):
        with pytest.raises(NotebookValidationError):
            book.update(candidate["entry_id"], {"fields": fields})
        assert book.snapshot_state() == before
    book.update(candidate["entry_id"], {"fields": {"notebook_refs": [], "source_types": []},
                                        "source_message_identities": [SOURCE]})
    assert book.get(matter["entry_id"])["candidate_refs"] == []


def test_wrong_type_dangling_self_and_duplicate_relations_are_rejected():
    book = pure()
    matter = create(book)
    before = book.snapshot_state()
    for relations in ([{"kind": "related_to", "entry_id": "missing"}],
                      [{"kind": "related_to", "entry_id": matter["entry_id"]}],
                      [{"kind": "invalid", "entry_id": matter["entry_id"]}]):
        with pytest.raises(NotebookValidationError):
            book.update(matter["entry_id"], {"relations": relations})
        assert book.snapshot_state() == before
    with pytest.raises(NotebookValidationError) as error:
        create(book, "implicit_gap", fields={**FIELDS["implicit_gap"], "situation_ref": matter["entry_id"]})
    assert error.value.code == "invalid_reference"
    other = create(book, "action")
    relation = {"kind": "part_of", "entry_id": matter["entry_id"]}
    with pytest.raises(NotebookValidationError):
        book.update(other["entry_id"], {"relations": [relation, relation]})


def test_archive_reports_all_referrers_and_preserves_internal_final_version():
    book = pure()
    situation = create(book, "situation")
    gap = create(book, "implicit_gap", fields={**FIELDS["implicit_gap"], "situation_ref": situation["entry_id"]})
    action = create(book, "action", relations=[{"kind": "based_on", "entry_id": situation["entry_id"]}])
    candidate = create(book, "candidate", fields={**FIELDS["candidate"], "notebook_refs": [situation["entry_id"]],
                                                "source_types": ["situation"]}, sources=False)
    before = book.snapshot_state()
    with pytest.raises(NotebookValidationError) as error:
        book.archive(situation["entry_id"], "Redundant background")
    assert error.value.code == "invalid_reference"
    assert {row["entry_id"] for row in error.value.details["referrers"]} == {
        gap["entry_id"], candidate["entry_id"]}
    assert book.snapshot_state() == before
    book.archive(gap["entry_id"], "No longer affects the retained situation")
    book.update(action["entry_id"], {"relations": []})
    book.update(candidate["entry_id"], {"fields": {"notebook_refs": [], "source_types": []},
                                        "source_message_identities": [SOURCE]})
    result = book.archive(situation["entry_id"], "Necessary evidence remains in the direct-message candidate")
    assert result == {"success": True, "changed": True, "entry_id": situation["entry_id"], "archived": True}
    assert book.show()["situations"] == []
    with pytest.raises(NotebookValidationError):
        book.get(situation["entry_id"])
    tombstone = book.snapshot_state()["situations"][0]
    assert tombstone["archived"] and tombstone["version_id"] != situation["version_id"]


def test_working_operations_serialize_and_freeze_is_idempotent():
    book = pure()
    with ThreadPoolExecutor(max_workers=4) as pool:
        entries = list(pool.map(lambda index: create(book, fields={**FIELDS["matter"], "description": str(index)}), range(16)))
    assert len({entry["entry_id"] for entry in entries}) == 16
    frozen = book.freeze()
    assert book.freeze() == frozen
    with pytest.raises(NotebookValidationError) as error:
        book.update(entries[0]["entry_id"], {"done": True})
    assert error.value.code == "state_conflict"
    assert book.snapshot_state() == frozen and len(book.show()["work"]) == 16


def test_committed_snapshot_roundtrip_exact_versions_and_noop_writes(db):
    book = store(db)
    first = create(book)
    receipt = book.commit(termination=FINISH)
    assert receipt["pointer_changed"] and receipt["effective_snapshot_id"] == receipt["snapshot_id"]
    assert book.commit(termination=FINISH) == receipt
    again = store(db, "m2")
    before_count = version_count(db)
    assert again.update(first["entry_id"], {"done": False})["changed"] is False
    assert version_count(db) == before_count
    changed = again.update(first["entry_id"], {"fields": {"blocker": "Paused while awaiting dates"}})["entry"]
    second = again.commit(termination={"type": "forced"})
    assert second["snapshot_id"] != receipt["snapshot_id"]
    assert db.notebook_snapshot_audit(receipt["snapshot_id"])["payload"]["work"][0]["version_id"] == first["version_id"]
    assert db.notebook_current(book.conversation_ref)["payload"]["work"][0]["version_id"] == changed["version_id"]
    row = db._read_one("SELECT payload_json FROM secretary_notebook_snapshots WHERE snapshot_id = ?", (second["snapshot_id"],))
    assert json.loads(row[0]) == [changed["version_id"]]
    for table, key, value in (("secretary_notebook_item", "id", changed["version_id"]),
                              ("secretary_notebook_snapshots", "snapshot_id", second["snapshot_id"])):
        with pytest.raises(sqlite3.IntegrityError):
            db._execute_write(lambda conn: conn.execute(f"UPDATE {table} SET payload_json = '[]' WHERE {key} = ?", (value,)))
        with pytest.raises(sqlite3.IntegrityError):
            db._execute_write(lambda conn: conn.execute(f"DELETE FROM {table} WHERE {key} = ?", (value,)))


def test_working_view_never_reload_new_parent_pointer_and_late_commit_is_success(db):
    initial = store(db)
    entry = create(initial)
    base = initial.commit(termination=FINISH)
    older, newer = store(db, "m2"), store(db, "m3")
    older.update(entry["entry_id"], {"fields": {"description": "Older task result"}})
    newer.update(entry["entry_id"], {"fields": {"description": "Newer task result"}})
    effective = newer.commit(termination=FINISH)
    working = older.working_view()
    assert working["view_kind"] == "working" and "snapshot_id" not in working
    assert working["base_snapshot_id"] == base["snapshot_id"]
    assert working["coverage"] == {"anchor_message_uid": "m2"}
    assert working["payload"]["work"][0]["fields"]["description"] == "Older task result"
    late = older.commit(termination=FINISH)
    assert late["pointer_changed"] is False
    assert late["effective_snapshot_id"] == effective["snapshot_id"]
    assert db.notebook_snapshot_audit(late["snapshot_id"]) is not None
    current = show_notebook(db.notebook_current(initial.conversation_ref))
    assert current["payload"]["work"][0]["fields"]["description"] == "Newer task result"
    assert "termination" not in current and "base_snapshot_id" not in current


@pytest.mark.parametrize("repetitions", [1, 2])
def test_compaction_carry_does_not_promote_old_anchor_past_new_human_anchor(db, repetitions):
    original = store(db, "m3")
    entry = create(original)
    previous = original.commit(termination=FINISH)
    db.append_message("s", "assistant", "Notebook read-only feedback", message_uid="human",
                      display_metadata={"human_only": True}, timestamp=400)
    current = store(db, "human")
    late = store(db, "m3")
    visible = [row for row in db.get_messages_as_conversation("s")
               if not (row.get("display_metadata") or {}).get("human_only")]
    for index in range(repetitions):
        db.archive_and_compact("s", [{"role": "assistant", "content": "Compaction summary",
                                      "message_uid": f"summary-{index}", "_compressed_summary": True},
                                     *deepcopy(visible)])
    rows = db.get_full_foreground("s")[1:]
    assert next(row["message_id"] for row in rows if row["message_uid"] == "m3") > next(
        row["message_id"] for row in rows if row["message_uid"] == "human")
    current.update(entry["entry_id"], {"fields": {"description": "Current accepted outcome"}})
    result = current.commit(termination=FINISH)
    assert result["pointer_changed"]
    assert result["effective_snapshot_id"] == result["snapshot_id"] != previous["snapshot_id"]
    late.update(entry["entry_id"], {"fields": {"description": "Older task outcome"}})
    late_result = late.commit(termination=FINISH)
    assert not late_result["pointer_changed"]
    assert db.notebook_snapshot_audit(late_result["snapshot_id"])
    shown = show_notebook(db.notebook_current(current.conversation_ref))
    assert shown["payload"]["work"][0]["fields"]["description"] == "Current accepted outcome"


def test_fork_inherits_logical_coverage_after_parent_compaction_carries_old_uid(db):
    original = store(db, "m3")
    entry = create(original)
    original.commit(termination=FINISH)
    db.append_message("s", "assistant", "Notebook read-only feedback", message_uid="human",
                      display_metadata={"human_only": True}, timestamp=400)
    current = store(db, "human")
    visible = [row for row in db.get_messages_as_conversation("s")
               if not (row.get("display_metadata") or {}).get("human_only")]
    db.archive_and_compact("s", [{"role": "assistant", "content": "Compaction summary",
                                  "message_uid": "summary", "_compressed_summary": True}, *visible])
    current.update(entry["entry_id"], {"fields": {"description": "Current accepted outcome"}})
    current.commit(termination=FINISH)
    make(db, "branch", "s", "_branched_from")
    branch_ref = db.inherit_foreground_branch("s", "branch")
    inherited = db.notebook_current(branch_ref)
    assert inherited["anchor_message_uid"] == "human"
    assert inherited["payload"]["work"][0]["fields"]["description"] == "Current accepted outcome"
    db.clear_messages("s")
    db.notebook_reselect_pointer(branch_ref)
    assert db.notebook_current(branch_ref)["anchor_message_uid"] == "human"
    new_row = add(db, "branch", "Branch has a new outcome", "branch-new", timestamp=500)
    branch = NotebookStore(db, branch_ref, anchor_message_uid="branch-new")
    branch.update(entry["entry_id"], {"fields": {"description": "New branch outcome"}})
    assert branch.commit(termination=FINISH)["pointer_changed"]
    make(db, "nested", "branch", "_branched_from")
    nested_ref = db.inherit_foreground_branch("branch", "nested")
    assert db.notebook_current(nested_ref)["anchor_message_uid"] == "branch-new"
    db.rewind_to_message("branch", new_row)
    db.notebook_reselect_pointer(branch_ref)
    assert db.notebook_current(branch_ref)["anchor_message_uid"] == "human"
    db.notebook_reselect_pointer(nested_ref)
    assert db.notebook_current(nested_ref)["anchor_message_uid"] == "branch-new"


def test_composite_carrier_user_projection_remains_newer_coverage_and_rewinds(db):
    from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER

    original = store(db, "m3")
    entry = create(original)
    previous = original.commit(termination=FINISH)
    row_id = db.append_message("s", "user", SUMMARY_PREFIX + "summary\n" + _SUMMARY_END_MARKER
                               + "\n\nThe genuine new user request", message_uid="composite",
                               _compressed_summary=True, timestamp=400)
    current = store(db, "composite")
    current.update(entry["entry_id"], {"fields": {"description": "Outcome from the genuine user request"}})
    result = current.commit(termination=FINISH)
    assert result["pointer_changed"]
    assert db.notebook_current(current.conversation_ref)["snapshot_id"] == result["snapshot_id"]
    db.rewind_to_message("s", row_id)
    db.notebook_reselect_pointer(current.conversation_ref)
    assert db.notebook_current(current.conversation_ref)["snapshot_id"] == previous["snapshot_id"]


def test_loading_uses_captured_snapshot_id_not_a_second_pointer_read(db, monkeypatch):
    initial = store(db)
    create(initial)
    receipt = initial.commit(termination=FINISH)
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Store must hydrate the captured base ID")
    monkeypatch.setattr(db, "notebook_snapshot_state_conn", forbidden)
    loaded = store(db, "m2")
    assert loaded.base_snapshot_id == receipt["snapshot_id"]
    assert len(loaded.show()["work"]) == 1


def test_empty_main_and_working_views_are_successful_not_published(db):
    book = store(db)
    assert book.working_view()["base_snapshot_id"] is None
    assert book.working_view()["payload"] == {section: [] for section in SECTIONS}
    main = show_notebook(None, conversation_ref=book.conversation_ref)
    assert main["success"] and main["snapshot_id"] is None and main["coverage"] is None
    assert db.notebook_current(book.conversation_ref) is None
    receipt = book.commit(termination={"type": "context_overflow"})
    assert receipt["pointer_changed"]
    assert db.notebook_snapshot_audit(receipt["snapshot_id"])["termination"] == {"type": "context_overflow"}
    assert "termination" not in show_notebook(db.notebook_current(book.conversation_ref))


def test_invalid_anchor_local_off_and_forged_version_fail_without_commit(db):
    book = store(db)
    entry = create(book)
    forged = book.snapshot_state()
    forged["work"][0]["fields"]["description"] = "Not this immutable row"
    with pytest.raises(NotebookError):
        db.notebook_commit_snapshot_result(book.conversation_ref, forged, anchor_message_uid="m1", termination=FINISH)
    db.notebook_set_local_enabled(book.conversation_ref, False)
    with pytest.raises(NotebookError):
        book.commit(termination=FINISH)
    db.notebook_set_local_enabled(book.conversation_ref, True)
    with pytest.raises(NotebookError):
        db.notebook_commit_snapshot_result(book.conversation_ref, book.snapshot_state(),
                                          anchor_message_uid="missing", termination=FINISH)
    assert db.notebook_current(book.conversation_ref) is None
    assert version_count(db) == 1
    assert book.get(entry["entry_id"])["version_id"] == entry["version_id"]


def test_insert_failure_rolls_back_without_publishing_working_state(db, monkeypatch):
    import secretary.notebook_items as items
    book = store(db)
    entry = create(book)
    before = book.snapshot_state()
    count = version_count(db)
    original_insert = items.insert_item_conn
    def fail_after_insert(*args, **kwargs):
        original_insert(*args, **kwargs)
        raise sqlite3.OperationalError("injected transaction rollback")
    monkeypatch.setattr(items, "insert_item_conn", fail_after_insert)
    with pytest.raises(sqlite3.OperationalError):
        book.update(entry["entry_id"], {"fields": {"blocker": "Paused while awaiting dates"}})
    assert version_count(db) == count and book.snapshot_state() == before


def test_commit_gate_revalidates_source_and_anchor_after_rewind(db):
    base = store(db)
    base.commit(termination=FINISH)
    current_id = db.notebook_current(base.conversation_ref)["snapshot_id"]
    source_row = db._read_one("SELECT id FROM messages WHERE session_id = ? AND message_uid = ?", ("s", "m2"))[0]
    source_lost = store(db, "m1")
    create(source_lost, uid="m2")
    anchor_lost = store(db, "m3")
    db.rewind_to_message("s", source_row)
    db.notebook_reselect_pointer(base.conversation_ref)
    for pending in (source_lost, anchor_lost):
        with pytest.raises(NotebookError):
            pending.commit(termination=FINISH)
    assert db.notebook_current(base.conversation_ref)["snapshot_id"] == current_id


def test_inherited_sources_are_bound_to_the_same_claim_not_unrelated_new_content(db):
    book = store(db)
    entry = create(book, uid="m2")
    book.commit(termination=FINISH)
    row = db._read_one("SELECT id FROM messages WHERE session_id = ? AND message_uid = ?", ("s", "m2"))[0]
    db.rewind_to_message("s", row)
    db.notebook_reselect_pointer(book.conversation_ref)
    inherited = store(db)
    assert inherited.get(entry["entry_id"])["version_id"] == entry["version_id"]
    processed = inherited.update(entry["entry_id"], {"fields": {"processing_note": "Retained the inherited indexed claim"}})
    assert processed["changed"]
    before = inherited.snapshot_state()
    for operation in (lambda: inherited.update(entry["entry_id"], {"fields": {"description": "Unrelated claim"}}),
                      lambda: create(inherited, uid="m2"),
                      lambda: inherited.update(entry["entry_id"], {"source_message_identities": [
                          {"conversation_ref": book.conversation_ref, "message_uid": "m3"}]})):
        with pytest.raises(NotebookValidationError) as error:
            operation()
        assert error.value.code == "source_unavailable" and inherited.snapshot_state() == before
    assert inherited.commit(termination=FINISH)["pointer_changed"]


def test_range_provenance_requires_current_known_evidence_not_just_valid_syntax(db):
    book = store(db)
    entry = book.create("situation", FIELDS["situation"], source_time_range=RANGE)["entry"]
    assert entry["source_message_identities"] == []
    before = book.snapshot_state()
    with pytest.raises(NotebookValidationError) as error:
        book.update(entry["entry_id"], {"source_time_range": {
            "start_time": "2000-01-01T00:00:00Z", "end_time": "2000-01-02T00:00:00Z"}})
    assert error.value.code == "source_unavailable" and book.snapshot_state() == before
    result = book.update(entry["entry_id"], {"source_time_range": None, "source_message_identities": [
        {"conversation_ref": book.conversation_ref, "message_uid": "m1"}]})
    assert result["entry"]["source_time_ranges"] == []
    with pytest.raises(NotebookValidationError):
        book.update(entry["entry_id"], {"source_message_identities": []})


def test_cross_conversation_and_cross_profile_sources_never_leak(db, tmp_path):
    book = store(db)
    make(db, "other")
    add(db, "other", "Not this Conversation", "foreign")
    other_ref = ref_of(db, "other")
    with pytest.raises(NotebookValidationError) as error:
        book.create("matter", FIELDS["matter"], source_message_identities=[
            {"conversation_ref": other_ref, "message_uid": "foreign"}])
    assert error.value.code == "scope_denied"
    independent = open_notebook_db(tmp_path / "independent.db")
    try:
        make(independent, "same-uid")
        add(independent, "same-uid", "Private", "foreign")
        with pytest.raises(NotebookValidationError) as error:
            create(book, uid="foreign")
        assert error.value.code == "source_unavailable"
    finally:
        independent.close()


def test_fork_shares_immutable_versions_but_not_updates_or_scheduler_state(db, monkeypatch):
    from secretary import schedules
    def forbidden(*_args, **_kwargs):
        raise AssertionError("Notebook must not reconcile or inherit Scheduler state")
    monkeypatch.setattr(schedules, "reconcile_payload", forbidden, raising=False)
    monkeypatch.setattr(schedules, "inherit_runtime_conn", forbidden, raising=False)
    parent = store(db)
    entry = create(parent)
    parent.commit(termination=FINISH)
    make(db, "branch", "s", "_branched_from")
    branch_ref = db.inherit_foreground_branch("s", "branch")
    child = NotebookStore(db, branch_ref, anchor_message_uid="m1")
    inherited = child.get(entry["entry_id"])
    assert inherited["version_id"] == entry["version_id"]
    assert inherited["source_message_identities"] == [{"conversation_ref": branch_ref, "message_uid": "m1"}]
    edited = child.update(entry["entry_id"], {"fields": {"blocker": "Paused while awaiting dates"}})["entry"]
    child.commit(termination=FINISH)
    assert edited["entry_id"] == entry["entry_id"] and edited["version_id"] != entry["version_id"]
    assert db.notebook_current(parent.conversation_ref)["payload"]["work"][0]["done"] is False
    assert "blocker" not in db.notebook_current(parent.conversation_ref)["payload"]["work"][0]["fields"]
    db.notebook_reselect_pointer(parent.conversation_ref)
    assert not any(name.startswith("noting_memo_") for name in dir(db))


@pytest.mark.parametrize("trigger", ["idle", "force", "manual", "auto_compaction"])
@pytest.mark.parametrize("termination", [FINISH, {"type": "forced"}, {"type": "context_overflow"}])
def test_new_trigger_and_termination_values_are_separate_audit(db, trigger, termination):
    book = store(db, trigger_type=trigger)
    receipt = book.commit(termination=termination)
    audit = db.notebook_snapshot_audit(receipt["snapshot_id"])
    assert audit["trigger_type"] == trigger and audit["runtime_profile"] == "NOTING"
    assert audit["termination"] == termination
    assert "Termination" not in render_notebook(db.notebook_current(book.conversation_ref))


@pytest.mark.parametrize("termination", [None, {"type": "compact_parent"}, {"type": "finish_noting"},
                                        {"type": "finish_noting", "reason": " "}, {"type": "forced", "reason": "x"}])
def test_retired_or_invalid_termination_never_commits(db, termination):
    book = store(db)
    with pytest.raises(NotebookError):
        book.commit(termination=termination)
    assert db.notebook_current(book.conversation_ref) is None


def test_current_snapshot_predicate_is_conn_bound_and_rejects_stale_notifications(db):
    first = store(db)
    a = first.commit(termination=FINISH)
    second = store(db, "m2")
    b = second.commit(termination=FINISH)
    def inspect(conn):
        assert db.notebook_snapshot_if_current_conn(conn, first.conversation_ref, a["snapshot_id"]) is None
        current = db.notebook_snapshot_if_current_conn(conn, first.conversation_ref, b["snapshot_id"])
        assert current["snapshot_id"] == b["snapshot_id"]
    db._execute_write(inspect)


def test_archive_current_hidden_but_original_snapshot_and_final_audit_survive(db):
    book = store(db)
    entry = create(book)
    original = book.commit(termination=FINISH)
    next_task = store(db, "m2")
    next_task.archive(entry["entry_id"], "Transient process no longer needed")
    archived = next_task.commit(termination=FINISH)
    current = db.notebook_current(book.conversation_ref)
    assert current["payload"]["work"] == []
    assert show_notebook(current)["payload"]["work"] == []
    assert db.notebook_snapshot_audit(original["snapshot_id"])["payload"]["work"][0]["archived"] is False
    tombstone = db.notebook_snapshot_audit(archived["snapshot_id"])["payload"]["work"][0]
    assert tombstone["archived"] and tombstone["entry_id"] == entry["entry_id"]
    assert tombstone["version_id"] != entry["version_id"]


def test_soft_capacity_thresholds_do_not_reject_or_truncate_snapshot(db):
    book = store(db)
    long_text = "必要限定与来源不能被截断。" * 1300
    first = create(book, fields={**FIELDS["matter"], "description": long_text})
    for index in range(60):
        create(book, fields={**FIELDS["matter"], "description": f"Distinct indexed obligation {index}"})
    receipt = book.commit(termination=FINISH)
    current = db.notebook_current(book.conversation_ref)
    assert current["snapshot_id"] == receipt["snapshot_id"]
    assert len(current["payload"]["work"]) == 61
    assert current["payload"]["work"][0]["fields"]["description"] == long_text
    assert first["entry_id"] in render_notebook(current)


def test_explicit_base_captured_before_worker_never_reloads_new_parent_pointer(db):
    from secretary.noting_child import freeze_notebook_start

    first = store(db)
    original = create(first, uid="m1")
    first_result = first.commit(termination=FINISH)
    frozen = freeze_notebook_start(db, first.conversation_ref)
    newer = store(db, "m2")
    newer.update(original["entry_id"], {"fields": {"description": "Parent received later evidence"}})
    newer.commit(termination=FINISH)
    delayed = store(db, "m1", **frozen)
    assert delayed.base_snapshot_id == first_result["snapshot_id"]
    assert delayed.get(original["entry_id"])["fields"]["description"] == original["fields"]["description"]
    assert db.notebook_current(first.conversation_ref)["snapshot_id"] != delayed.base_snapshot_id


def test_explicit_empty_base_is_not_replaced_by_later_parent_snapshot(db):
    from secretary.noting_child import freeze_notebook_start

    ref = ref_of(db, "s")
    frozen = freeze_notebook_start(db, ref)
    assert frozen == {"base_snapshot_id": None}
    current = store(db)
    create(current, uid="m1")
    current.commit(termination=FINISH)
    delayed = store(db, **frozen)
    assert delayed.base_snapshot_id is None
    assert all(not entries for entries in delayed.show().values())


def test_explicit_base_refuses_other_owner_and_unavailable_snapshot(db):
    original = store(db)
    result = original.commit(termination=FINISH)
    make(db, "other-owner")
    add(db, "other-owner", "Independent", "other-message")
    with pytest.raises(NotebookValidationError) as error:
        NotebookStore(db, ref_of(db, "other-owner"), anchor_message_uid="other-message",
                      base_snapshot_id=result["snapshot_id"])
    assert error.value.code == "scope_denied"
    with pytest.raises(NotebookValidationError) as error:
        store(db, base_snapshot_id="missing-snapshot")
    assert error.value.code == "source_unavailable"
