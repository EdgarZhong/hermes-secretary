"""Authorized provenance arrays share one real Store/version/Snapshot path."""

from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
import json

import pytest
from jsonschema import Draft7Validator

from hermes_state_secretary_notebook import NotebookError
from secretary.notebook_contract import NotebookValidationError, same_source_claim, section_for_type
from secretary.notebook_evidence import evidence_time
from secretary.notebook_items import insert_item_conn
from secretary.notebook_render import readable_notebook_entry, readable_notebook_state, render_notebook, show_notebook
from secretary.notebook_store import NotebookStore
from secretary.noting_contract import NOTEBOOK_CREATE_SCHEMA, NOTEBOOK_UPDATE_SCHEMA
from tests.hermes_state._secretary_notebook_harness import make, ref_of
from tests.secretary.test_notebook_maintenance_v2 import (
    BODY, FINISH, MINIMAL, admitted_instant, book, count, create, evidence_db_facts, owner as owner,
)


def point(epoch):
    timestamp = datetime.fromtimestamp(epoch, timezone.utc).isoformat()
    return {"start_time": timestamp, "end_time": timestamp}


def interval(start, end):
    return {"start_time": point(start)["start_time"], "end_time": point(end)["end_time"]}


@pytest.mark.parametrize("kind", [kind for kind in MINIMAL if kind != "candidate"])
def test_seven_types_mix_uid_and_multiple_explicit_ranges_through_snapshot(owner, kind):
    db, ref = owner
    store = book(owner)
    ranges = [point(100), interval(100, 300), interval(200, 500), point(100)]
    entry = create(store, kind, source_message_uids=["u1", "u2"], source_time_ranges=ranges)
    assert entry["source_time_ranges"] == ranges and "source_time_range" not in entry
    assert evidence_time(entry, db=db, conversation_ref=ref) == [point(100), point(300), *ranges]
    versions = count(db)
    assert not store.update(entry["entry_id"], {"source_time_ranges": deepcopy(ranges)})["changed"]
    assert count(db) == versions
    store.commit(termination=FINISH)
    assert book(owner).get(entry["entry_id"]) == entry
    persisted = db._read_one("SELECT payload_json FROM secretary_notebook_item WHERE id=?", (entry["version_id"],))[0]
    assert '"source_time_ranges"' in persisted and '"source_time_range"' not in persisted


@pytest.mark.parametrize("value", [None, {}, "range", [None], ["range"], [{"start_time": "2026-01-01T00:00:00Z"}],
                                   [interval(300, 100)], [{**point(100), "start_time": "1970-01-01T00:01:40"}],
                                   [{**point(100), "extra": "no"}], [{**point(100), "end_time": 100}]])
@pytest.mark.parametrize("operation", ["create", "update"])
def test_malformed_ranges_refuse_whole_operation_without_versions(owner, value, operation):
    db, _ref = owner
    store = book(owner)
    entry = create(store)
    before, versions = store.snapshot_state(), count(db)
    with pytest.raises(NotebookValidationError) as error:
        if operation == "create":
            create(store, source_time_ranges=value)
        else:
            store.update(entry["entry_id"], {"done": True, "source_time_ranges": value})
    assert error.value.field.startswith("source_time_ranges")
    assert store.snapshot_state() == before and count(db) == versions


@pytest.mark.parametrize("uids,ranges", [(["missing"], [point(100)]), (["u1"], [interval(1000, 1100)]),
                                         (["u1"], [point(100), interval(1000, 1100)]), ([], [])])
def test_mixing_sources_does_not_let_valid_half_authorize_invalid_half(owner, uids, ranges):
    db, _ref = owner
    store = book(owner)
    before, versions = store.snapshot_state(), count(db)
    with pytest.raises(NotebookValidationError):
        create(store, source_message_uids=uids, source_time_ranges=ranges)
    assert store.snapshot_state() == before and count(db) == versions


def test_ranges_replace_clear_omit_noop_and_never_renew_lifecycle_clock(owner):
    db, _ref = owner
    store = book(owner)
    entry = create(store, fields={**BODY, "last_progress_time": point(100)["start_time"]},
                   source_time_ranges=[point(100), point(300)])
    changed = store.update(entry["entry_id"], {"source_time_ranges": [point(200)]})["entry"]
    assert changed["entry_id"] == entry["entry_id"] and changed["version_id"] != entry["version_id"]
    assert changed["source_time_ranges"] == [point(200)]
    paused = store.update(entry["entry_id"], {"fields": {"blocker": "Paused while awaiting dates"}})["entry"]
    assert paused["source_time_ranges"] == [point(200)]
    assert paused["done"] is False and paused["fields"]["blocker"] == "Paused while awaiting dates"
    cleared = store.update(entry["entry_id"], {"source_time_ranges": []})["entry"]
    assert cleared["source_time_ranges"] == []
    before, versions = store.snapshot_state(), count(db)
    assert not store.update(entry["entry_id"], {"source_time_ranges": []})["changed"]
    assert store.snapshot_state() == before and count(db) == versions
    assert cleared["created_at"] == entry["created_at"]
    assert cleared["fields"]["last_progress_time"] == entry["fields"]["last_progress_time"]
    assert cleared["last_processed_at"] is None


def test_old_internal_single_range_is_compatible_but_not_current_wire_alias(owner):
    store = book(owner)
    entry = create(store, source_time_range=point(100))
    assert entry["source_time_ranges"] == [point(100)]
    assert store.update(entry["entry_id"], {"source_time_range": None})["entry"]["source_time_ranges"] == []
    for schema in (NOTEBOOK_CREATE_SCHEMA, NOTEBOOK_UPDATE_SCHEMA):
        props = schema["parameters"]["properties"]
        assert "source_time_range" not in props
        assert props["source_time_ranges"]["type"] == "array"
        data = {"entry_type": "matter", "fields": BODY} if schema is NOTEBOOK_CREATE_SCHEMA else {"entry_id": entry["entry_id"]}
        validator = Draft7Validator(schema["parameters"])
        validator.validate({**data, "source_message_uids": ["u1"], "source_time_ranges": [point(100), point(100)]})
        assert list(validator.iter_errors({**data, "source_time_range": point(100)}))
        assert list(validator.iter_errors({**data, "source_time_ranges": None}))


@pytest.mark.parametrize("uids,ranges", [(["u1"], []), ([], [point(100), interval(200, 300)]),
                                         (["u1", "u2"], [point(100), interval(200, 300)])])
def test_candidate_direct_forms_create_update_snapshot_and_readonly_time(owner, uids, ranges):
    db, ref = owner
    store = book(owner)
    entry = create(store, "candidate", source_message_uids=uids, source_time_ranges=ranges)
    expected = [point(100) if uid == "u1" else point(300) for uid in uids] + ranges
    assert evidence_time(entry, db=db, conversation_ref=ref) == expected
    before, versions = store.snapshot_state(), count(db)
    assert not store.update(entry["entry_id"], {"source_message_uids": uids, "source_time_ranges": ranges})["changed"]
    assert store.snapshot_state() == before and count(db) == versions
    next_uids, next_ranges = (uids, [*ranges, point(500)]) if ranges else (["u2"], [])
    revised = store.update(entry["entry_id"], {"source_message_uids": next_uids,
                                             "source_time_ranges": next_ranges})["entry"]
    assert revised["entry_id"] == entry["entry_id"] and revised["version_id"] != entry["version_id"]
    assert revised["created_at"] == entry["created_at"]
    next_times = [point(100) if uid == "u1" else point(300) for uid in next_uids] + next_ranges
    assert evidence_time(revised, db=db, conversation_ref=ref) == next_times
    store.commit(termination=FINISH)
    assert book(owner).get(entry["entry_id"]) == revised
    assert show_notebook(db.notebook_current(ref), db=db)["payload"]["candidates"][0]["evidence_time"] == [
        item["start_time"] if item["start_time"] == item["end_time"] else item for item in next_times]


def test_candidate_mode_switches_require_clearing_other_mode_and_failed_writes_are_atomic(owner):
    db, _ref = owner
    store = book(owner)
    source = create(store, source_time_ranges=[point(100)])
    indirect_fields = {"notebook_refs": [source["entry_id"]], "source_types": ["matter"]}
    entry = create(store, "candidate", source_message_uids=["u1"], source_time_ranges=[point(300)])
    before, versions = store.snapshot_state(), count(db)
    for changes in ({"fields": indirect_fields}, {"fields": {"source_types": ["matter"]}},
                    {"source_message_uids": [], "source_time_ranges": []}):
        with pytest.raises(NotebookValidationError):
            store.update(entry["entry_id"], changes)
        assert store.snapshot_state() == before and count(db) == versions
    for sources in ({"source_message_uids": [], "source_time_ranges": []},
                    {"source_message_uids": ["missing"], "source_time_ranges": [point(100)]},
                    {"source_message_uids": ["u1"], "source_time_ranges": [point(1000)]}):
        with pytest.raises(NotebookValidationError):
            create(store, "candidate", **sources)
        assert store.snapshot_state() == before and count(db) == versions
    indirect = store.update(entry["entry_id"], {"fields": indirect_fields, "source_message_uids": [],
                                               "source_time_ranges": []})["entry"]
    before, versions = store.snapshot_state(), count(db)
    for sources in ({"source_message_uids": ["u1"]}, {"source_time_ranges": [point(100)]},
                    {"source_message_uids": ["u1"], "source_time_ranges": [point(100)]}):
        with pytest.raises(NotebookValidationError):
            store.update(entry["entry_id"], sources)
        with pytest.raises(NotebookValidationError):
            create(store, "candidate", fields={**MINIMAL["candidate"], **indirect_fields},
                   **{"source_message_uids": [], **sources})
        assert store.snapshot_state() == before and count(db) == versions
    with pytest.raises(NotebookValidationError):
        store.update(entry["entry_id"], {"fields": {"notebook_refs": []}, "source_time_ranges": [point(100)]})
    assert store.snapshot_state() == before and count(db) == versions
    direct = store.update(entry["entry_id"], {"fields": {"notebook_refs": [], "source_types": []},
                                             "source_time_ranges": [point(100), point(300)]})["entry"]
    assert direct["entry_id"] == indirect["entry_id"] == entry["entry_id"]
    assert direct["fields"]["notebook_refs"] == direct["fields"]["source_types"] == []
    store.commit(termination=FINISH)
    assert book(owner).get(entry["entry_id"]) == direct


def test_refs_aggregate_independent_arrays_in_working_and_snapshot_fallback(owner):
    db, ref = owner
    store = book(owner)
    first = create(store, source_message_uids=["u1", "u2"], source_time_ranges=[interval(100, 300), point(100)])
    second = create(store, "question", source_message_uids=["a1", "a2", "t1"], source_time_ranges=[point(600)])
    candidate = store.create("candidate", {**MINIMAL["candidate"], "notebook_refs": [first["entry_id"], second["entry_id"]],
                                           "source_types": ["matter", "question"]})["entry"]
    expected = [point(100), point(300), interval(100, 300), point(100), point(500), point(600)]
    assert evidence_time(candidate, db=db, conversation_ref=ref, state=store.snapshot_state()) == expected
    before, versions = store.snapshot_state(), count(db)
    with pytest.raises(NotebookValidationError):
        store.archive(first["entry_id"], "Cannot remove a pending Candidate source")
    assert store.snapshot_state() == before and count(db) == versions
    store.commit(termination=FINISH)
    assert evidence_time(candidate, db=db, conversation_ref=ref) == expected
    reopened = book(owner)
    assert reopened.get(candidate["entry_id"])["source_time_ranges"] == []
    assert reopened.get(candidate["entry_id"])["source_message_identities"] == []


@pytest.mark.parametrize("old_range", [None, point(300)])
@pytest.mark.parametrize("kind", ["matter", "candidate"])
def test_old_single_range_exact_version_and_off_path_basis_survive_without_json_rewrite(owner, old_range, kind):
    db, ref = owner
    store = book(owner)
    section = section_for_type(kind)
    expected_ranges = [] if old_range is None else [old_range]
    original = create(store, kind, source_message_uids=["u2"], source_time_ranges=expected_ranges)
    old = store.snapshot_state()[section][0]
    old.pop("source_time_ranges")
    old["source_time_range"] = old_range
    old["fields"]["evidence_time"] = point(100)["start_time"]
    legacy = db._execute_write(lambda conn: insert_item_conn(conn, ref, old, original["version_id"]))
    state = store.snapshot_state()
    state[section] = [legacy]
    snapshot_id = db.notebook_commit_snapshot(ref, state, anchor_message_uid="u1", termination=FINISH)
    stored_item = db._read_one("SELECT payload_json FROM secretary_notebook_item WHERE id=?", (legacy["version_id"],))[0]
    stored_snapshot = db._read_one("SELECT payload_json FROM secretary_notebook_snapshots WHERE snapshot_id=?", (snapshot_id,))[0]
    assert '"source_time_range"' in stored_item and '"source_time_ranges"' not in stored_item
    removed = db._read_one("SELECT id FROM messages WHERE message_uid='u2'")[0]
    db.rewind_to_message("main", removed)
    db.notebook_reselect_pointer(ref)
    old["version_id"] = legacy["version_id"]
    assert same_source_claim(old, legacy)
    resumed = book(owner, working_state={**state, section: [old]})
    assert not resumed.update(original["entry_id"], {"source_time_ranges": expected_ranges})["changed"]
    edited = resumed.update(original["entry_id"], {"fields": {"processing_note": "Reviewed the same inherited evidence"}})["entry"]
    assert edited["source_time_ranges"] == expected_ranges
    assert edited["created_at"] == original["created_at"]
    resumed.commit(termination=FINISH)
    forged = resumed.snapshot_state()
    forged[section][0]["source_time_ranges"] = [point(100)]
    with pytest.raises(NotebookError, match="immutable version"):
        db.notebook_commit_snapshot(ref, forged, anchor_message_uid="u1", termination=FINISH)
    assert db._read_one("SELECT payload_json FROM secretary_notebook_item WHERE id=?", (legacy["version_id"],))[0] == stored_item
    assert db._read_one("SELECT payload_json FROM secretary_notebook_snapshots WHERE snapshot_id=?", (snapshot_id,))[0] == stored_snapshot
    fresh = book(owner)
    before, versions = fresh.snapshot_state(), count(db)
    with pytest.raises(NotebookValidationError):
        fresh.update(original["entry_id"], {"fields": {"description": "New claim borrowing retired sources"}})
    assert fresh.snapshot_state() == before and count(db) == versions


@pytest.mark.parametrize("kind", ["matter", "candidate"])
def test_mixed_array_sources_rebind_on_branch_and_do_not_authorize_foreign_uid(owner, kind):
    db, ref = owner
    initial = book(owner)
    entry = create(initial, kind, source_message_uids=["u1", "u2"], source_time_ranges=[point(100), point(300)])
    initial.commit(termination=FINISH)
    make(db, "branch", "main", "_branched_from")
    branch_ref = db.inherit_foreground_branch("main", "branch")
    branch = NotebookStore(db, branch_ref, anchor_message_uid="u1")
    inherited = branch.get(entry["entry_id"])
    assert inherited["source_time_ranges"] == entry["source_time_ranges"]
    assert all(source["conversation_ref"] == branch_ref for source in inherited["source_message_identities"])
    revised = branch.update(entry["entry_id"], {"fields": {"processing_note": "Reviewed inherited source array"}})["entry"]
    branch.commit(termination=FINISH)
    assert revised["entry_id"] == entry["entry_id"]
    assert db.notebook_current(ref)["payload"][section_for_type(kind)][0] == entry
    make(db, "other")
    db.append_message("other", "user", "Foreign", message_uid="foreign", timestamp=100)
    reopened = NotebookStore(db, branch_ref, anchor_message_uid="u1")
    before, versions = reopened.snapshot_state(), count(db)
    with pytest.raises(NotebookValidationError):
        reopened.update(entry["entry_id"], {"source_message_uids": ["foreign"], "source_time_ranges": [point(100)]})
    assert reopened.snapshot_state() == before and count(db) == versions


def test_unknown_parts_omit_only_unknown_points_and_keep_explicit_ranges(owner):
    db, ref = owner
    store = book(owner)
    entry = create(store, source_message_uids=["u1", "u2"], source_time_ranges=[point(300)])
    db._execute_write(lambda conn: conn.execute("UPDATE messages SET timestamp='unknown' WHERE message_uid='u1'"))
    assert evidence_time(entry, db=db, conversation_ref=ref) == [point(300), point(300)]
    only_unknown = {**entry, "source_message_identities": [{"conversation_ref": ref, "message_uid": "u1"}], "source_time_ranges": []}
    assert evidence_time(only_unknown, db=db, conversation_ref=ref) == []
    assistant = {**entry, "source_message_identities": [{"conversation_ref": ref, "message_uid": uid} for uid in ("a1", "a2")], "source_time_ranges": []}
    db._execute_write(lambda conn: conn.execute("UPDATE messages SET timestamp='unknown' WHERE message_uid='a2'"))
    assert evidence_time(assistant, db=db, conversation_ref=ref) == []
    assert evidence_time(entry) == [point(300)]


def test_formally_admitted_instant_keeps_fourth_level_points_and_ranges(owner):
    db, ref = owner
    _table, _schedule_id, carrier = admitted_instant(owner)
    store = book(owner)
    with_assistant = create(store, source_message_uids=[carrier["message_uid"], "a2"], source_time_ranges=[point(100)])
    isolated = create(store, source_message_uids=[carrier["message_uid"]], source_time_ranges=[point(100)])
    before = evidence_db_facts(db)
    assert evidence_time(with_assistant, db=db, conversation_ref=ref) == [point(500), point(100)]
    assert evidence_time(isolated, db=db, conversation_ref=ref) == [point(carrier["timestamp"]), point(100)]
    assert evidence_db_facts(db) == before


def test_every_projection_uses_profile_timezone_and_does_not_mutate_sources(owner, monkeypatch):
    db, ref = owner
    monkeypatch.setenv("HERMES_TIMEZONE", "UTC")
    Path(db.db_path).with_name("config.yaml").write_text("timezone: Asia/Shanghai\n")
    store = book(owner, clock=lambda: datetime(2030, 1, 1, tzinfo=timezone.utc))
    ranges = [{"start_time": "1970-01-01T09:01:40+09:00", "end_time": "1970-01-01T00:05:00Z"}]
    entry = create(store, fields={**BODY, "last_progress_time": "1970-01-01T09:01:40+09:00"},
                   source_message_uids=["u1", "u2"], source_time_ranges=ranges)
    before = store.snapshot_state()
    expected = ["1970-01-01T08:01:40+08:00", "1970-01-01T08:05:00+08:00",
                {"start_time": "1970-01-01T08:01:40+08:00", "end_time": "1970-01-01T08:05:00+08:00"}]
    projected = readable_notebook_entry(entry, db=db, conversation_ref=ref)
    assert projected["evidence_time"] == expected
    assert projected["source_time_ranges"] == [expected[-1]]
    assert projected["created_at"] == "2030-01-01T08:00:00+08:00"
    assert projected["fields"]["last_progress_time"] == expected[0]
    assert readable_notebook_entry(projected) == projected
    assert readable_notebook_state(before, db=db, conversation_ref=ref)["work"][0] == projected
    store.commit(termination=FINISH)
    snapshot = db.notebook_current(ref)
    assert show_notebook(snapshot, db=db)["payload"]["work"][0] == projected
    rendered = render_notebook(snapshot, db=db)
    rendered_ranges = next(line.split("source_time_ranges: ", 1)[1] for line in rendered.splitlines()
                           if "source_time_ranges: " in line)
    assert json.loads(rendered_ranges) == [expected[-1]]
    assert 'evidence_time: ["1970-01-01T08:01:40+08:00", "1970-01-01T08:05:00+08:00"' in rendered
    assert "source_time_range:" not in rendered
    assert store.snapshot_state() == before


def test_insert_revalidates_every_range_after_a_rewind_race(owner, monkeypatch):
    db, _ref = owner
    store = book(owner)
    before, versions = store.snapshot_state(), count(db)
    removed = db._read_one("SELECT id FROM messages WHERE message_uid='u2'")[0]
    write = db._execute_write
    def rewind_before_insert(callback, *args, **kwargs):
        monkeypatch.setattr(db, "_execute_write", write)
        db.rewind_to_message("main", removed)
        return write(callback, *args, **kwargs)
    monkeypatch.setattr(db, "_execute_write", rewind_before_insert)
    with pytest.raises(NotebookValidationError) as error:
        create(store, source_message_uids=["u1"], source_time_ranges=[point(100), point(300)])
    assert error.value.code == "source_unavailable"
    assert store.snapshot_state() == before and count(db) == versions


def test_snapshot_gate_revalidates_uncommitted_ranges_without_borrowing_old_uid_permission(owner):
    db, ref = owner
    store = book(owner)
    create(store, source_message_uids=["u1"], source_time_ranges=[point(300)])
    removed = db._read_one("SELECT id FROM messages WHERE message_uid='u2'")[0]
    db.rewind_to_message("main", removed)
    before, versions = store.snapshot_state(), count(db)
    with pytest.raises(NotebookError):
        store.commit(termination=FINISH)
    assert store.snapshot_state() == before and count(db) == versions
    assert db.notebook_current(ref) is None
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots")[0] == 0


def test_multiple_ranges_can_be_entire_provenance_and_clear_needs_other_sources(owner):
    db, ref = owner
    store = book(owner)
    ranges = [point(100), interval(200, 300)]
    entry = create(store, source_message_uids=[], source_time_ranges=ranges)
    assert evidence_time(entry, db=db, conversation_ref=ref) == ranges
    before, versions = store.snapshot_state(), count(db)
    with pytest.raises(NotebookValidationError):
        store.update(entry["entry_id"], {"source_time_ranges": []})
    assert store.snapshot_state() == before and count(db) == versions
    converted = store.update(entry["entry_id"], {"source_message_uids": ["u1"], "source_time_ranges": []})["entry"]
    assert converted["source_time_ranges"] == []
    assert evidence_time(converted, db=db, conversation_ref=ref) == [point(100)]


def test_old_readable_time_shape_is_rederived_as_array_and_explicit_profile_reformats_points(owner):
    db, ref = owner
    entry = create(book(owner), source_time_ranges=[point(100)])
    current = readable_notebook_entry(entry, db=db, conversation_ref=ref)
    old_view = deepcopy(current)
    old_view["source_time_range"] = old_view.pop("source_time_ranges")[0]
    old_view["evidence_time"] = interval(100, 600)
    normalized = readable_notebook_entry(old_view)
    assert normalized["evidence_time"] == [point(100)["start_time"]]
    assert "source_time_range" not in normalized
    empty_old_view = {**old_view, "source_time_range": None, "evidence_time": None}
    assert readable_notebook_entry(empty_old_view)["evidence_time"] == []
    display_home = Path(db.db_path).parent / "alternate-display"
    display_home.mkdir()
    (display_home / "config.yaml").write_text("timezone: Asia/Shanghai\n")
    moved = readable_notebook_entry(current, profile_home=display_home)
    assert moved["evidence_time"] == ["1970-01-01T08:01:40+08:00", "1970-01-01T08:01:40+08:00"]
    assert moved["source_time_ranges"] == [{"start_time": "1970-01-01T08:01:40+08:00", "end_time": "1970-01-01T08:01:40+08:00"}]
