"""Notebook v2 uses real SQLite items, Snapshot gates and source projection."""

from copy import deepcopy
from datetime import datetime, timezone
import json
import sqlite3

import pytest
from jsonschema import Draft7Validator

from hermes_time import format_timestamp
from secretary.notebook_contract import NotebookValidationError, REQUIRED_FIELDS
from secretary.notebook_evidence import evidence_time
from secretary.notebook_items import insert_item_conn
from secretary.notebook_render import readable_notebook_entry, readable_notebook_state, show_notebook
from secretary.notebook_store import NotebookStore
from secretary.noting_contract import NOTEBOOK_CREATE_SCHEMA, NOTEBOOK_UPDATE_SCHEMA, NOTEBOOK_ARCHIVE_SCHEMA
from tests.hermes_state._secretary_notebook_harness import add, make, open_notebook_db, ref_of

FINISH = {"type": "finish_noting", "reason": "Reviewed the current records"}
BODY = {"description": "Plan the visit", "completion_condition": "Dates agreed"}
SUGGESTION = {"content": "Ask the host about the family visit: dates remain undecided, and booking must wait.",
              "schedule": "When the host is likely to know; no definite date was given"}
MINIMAL = {
    "matter": BODY,
    "action": {"description": "Ask the host", "owner": "Main", "completion_condition": "Reply received"},
    "situation": {"description": "The host is deciding", "subjects": ["host"]},
    "implicit_gap": {"description": "Host identity unknown", "situation_ref": "target",
                     "missing_information": "Who is the host?", "impact": "Cannot ask them"},
    "question": {"description": "Which dates work?"},
    "insight": {"description": "Dates are the blocker", "certainty": "tentative"},
    "decision": {"description": "Wait before booking", "scope": "this visit"},
    "candidate": {"description": "Keep the visit outcome", "targets": ["memory"],
                  "notebook_refs": [], "source_types": []},
}
OPTIONAL = {"situation": "time_context", "implicit_gap": "resolution_condition",
            "question": "unresolved_points", "insight": "qualification", "decision": "valid_when"}


@pytest.fixture
def owner(tmp_path):
    db = open_notebook_db(tmp_path / "state.db")
    make(db, "main")
    add(db, "main", "The visit is planned", "u1", timestamp=100)
    add(db, "main", "We should wait", "a1", role="assistant", timestamp=200)
    add(db, "main", "No date is known", "u2", timestamp=300)
    add(db, "main", "Tool output", "t1", role="tool", timestamp=400)
    add(db, "main", "Waiting for the host", "a2", role="assistant", timestamp=500)
    add(db, "main", "Runtime fact", "s1", role="system", timestamp=600)
    ref = ref_of(db, "main")
    yield db, ref
    db.close()


def book(owner, **kwargs):
    db, ref = owner
    return NotebookStore(db, ref, anchor_message_uid="u1", **kwargs)


def create(store, kind="matter", **kwargs):
    fields = deepcopy(kwargs.pop("fields", MINIMAL[kind]))
    if kind == "implicit_gap":
        fields["situation_ref"] = create(store, "situation")["entry_id"]
    return store.create(kind, fields, source_message_uids=kwargs.pop("source_message_uids", ["u1"]), **kwargs)["entry"]


def count(db):
    return db._read_one("SELECT COUNT(*) FROM secretary_notebook_item")[0]


@pytest.mark.parametrize("kind", list(MINIMAL))
def test_minimal_types_and_single_suggestion_survive_snapshot_and_reopen(owner, kind):
    db, ref = owner
    store = book(owner)
    entry = create(store, kind, schedule_suggestion=SUGGESTION)
    store.commit(termination=FINISH)
    reopened = book(owner)
    assert reopened.get(entry["entry_id"]) == entry
    assert reopened.get(entry["entry_id"])["schedule_suggestion"] == SUGGESTION
    assert set(REQUIRED_FIELDS[kind]) <= entry["fields"].keys()
    assert db.notebook_current(ref)["payload"]["work"] == store.show()["work"]


@pytest.mark.parametrize("kind,key", list(OPTIONAL.items()) + [("decision", "ends_when")])
def test_new_optional_type_fields_can_be_added_and_cleared(owner, kind, key):
    store = book(owner)
    entry = create(store, kind)
    added = store.update(entry["entry_id"], {"fields": {key: "Supported condition"}})["entry"]
    assert added["fields"][key] == "Supported condition"
    cleared = store.update(entry["entry_id"], {"fields": {key: None}})["entry"]
    assert key not in cleared["fields"]
    assert cleared["entry_id"] == entry["entry_id"]
    assert cleared["version_id"] != added["version_id"]


def test_suggestion_whole_replacement_noop_clear_and_unparsed_schedule(owner):
    db, _ref = owner
    store = book(owner)
    entry = create(store, schedule_suggestion=SUGGESTION)
    before = count(db)
    assert not store.update(entry["entry_id"], {"schedule_suggestion": deepcopy(SUGGESTION)})["changed"]
    assert count(db) == before
    replacement = {"content": "Follow up on the agreed visit with the host.", "schedule": "This is semantic advice, not CRON!"}
    changed = store.update(entry["entry_id"], {"schedule_suggestion": replacement})["entry"]
    assert changed["schedule_suggestion"] == replacement
    assert changed["entry_id"] == entry["entry_id"]
    assert changed["version_id"] != entry["version_id"]
    assert changed["created_at"] == entry["created_at"]
    cleared = store.update(entry["entry_id"], {"schedule_suggestion": None})["entry"]
    assert "schedule_suggestion" not in cleared
    assert not store.update(entry["entry_id"], {"schedule_suggestion": None})["changed"]
    store.commit(termination=FINISH)
    assert "schedule_suggestion" not in book(owner).get(entry["entry_id"])


@pytest.mark.parametrize("value", [[], [SUGGESTION], "later", {}, {"content": "body"},
                                   {"content": "body", "schedule": 123}, {**SUGGESTION, "timezone": "UTC"},
                                   {"content": "", "schedule": "later"}])
@pytest.mark.parametrize("operation", ["create", "update"])
def test_bad_suggestions_leave_no_partial_versions(owner, value, operation):
    db, _ref = owner
    store = book(owner)
    entry = create(store)
    before, versions = store.snapshot_state(), count(db)
    with pytest.raises(NotebookValidationError) as error:
        if operation == "create":
            create(store, schedule_suggestion=value)
        else:
            store.update(entry["entry_id"], {"status": "paused", "schedule_suggestion": value})
    assert error.value.field.startswith("schedule_suggestion")
    assert store.snapshot_state() == before and count(db) == versions


@pytest.mark.parametrize("key", ["evidence_time", "external_refs", "schedule_refs"])
def test_retired_and_readonly_fields_cannot_enter_new_input(owner, key):
    db, _ref = owner
    store = book(owner)
    entry = create(store)
    before, versions = store.snapshot_state(), count(db)
    for invoke in (lambda: create(store, fields={**BODY, key: "2030-01-01T00:00:00Z"}),
                   lambda: store.update(entry["entry_id"], {"fields": {key: None}}),
                   lambda: store.update(entry["entry_id"], {key: None})):
        with pytest.raises(NotebookValidationError):
            invoke()
        assert store.snapshot_state() == before and count(db) == versions


def test_schema_accepts_flat_parameters_and_refuses_wrapper_and_readonly_input():
    for schema, payload in (
        (NOTEBOOK_CREATE_SCHEMA, {"entry_type": "question", "fields": MINIMAL["question"], "schedule_suggestion": SUGGESTION}),
        (NOTEBOOK_UPDATE_SCHEMA, {"entry_id": "1", "fields": {"unresolved_points": None}, "schedule_suggestion": None}),
        (NOTEBOOK_ARCHIVE_SCHEMA, {"entry_id": "1", "reason": "Settled"}),
    ):
        Draft7Validator(schema["parameters"]).validate(payload)
    create_properties = NOTEBOOK_CREATE_SCHEMA["parameters"]["properties"]
    update_properties = NOTEBOOK_UPDATE_SCHEMA["parameters"]["properties"]
    assert (create_properties.keys() & update_properties.keys()) == {
        "fields", "status", "relations", "schedule_suggestion", "source_message_uids", "source_time_range"}
    validator = Draft7Validator(NOTEBOOK_UPDATE_SCHEMA["parameters"])
    assert list(validator.iter_errors({"entry_id": "1"}))
    for patch in ({"changes": {"status": "paused"}}, {"action": "update"}, {"entry_type": "matter"},
                  {"evidence_time": "now"}, {"fields": {"evidence_time": "now"}},
                  {"fields": {"external_refs": []}}):
        assert list(validator.iter_errors({"entry_id": "1", **patch}))


def test_legacy_immutable_payload_hydrates_without_rewriting_or_losing_sources(owner):
    db, ref = owner
    initial = book(owner)
    entry = create(initial)
    raw = {**initial.snapshot_state()["work"][0]}
    raw["fields"] = {**raw["fields"], "external_refs": ["old-file"], "evidence_time": "2020-01-01T00:00:00Z",
                     "last_progress_time": "2021-01-01T00:00:00Z"}
    legacy = db._execute_write(lambda conn: insert_item_conn(conn, ref, raw, entry["version_id"]))
    payload = initial.snapshot_state()
    payload["work"] = [legacy]
    snapshot_id = db.notebook_commit_snapshot(ref, payload, anchor_message_uid="u1", termination=FINISH)
    raw_item = db._read_one("SELECT payload_json FROM secretary_notebook_item WHERE id=?", (legacy["version_id"],))[0]
    raw_snapshot = db._read_one("SELECT payload_json FROM secretary_notebook_snapshots WHERE snapshot_id=?", (snapshot_id,))[0]
    old_payload = {**payload, "work": [raw | {"entry_id": legacy["entry_id"], "version_id": legacy["version_id"]}]}
    db.notebook_commit_snapshot(ref, old_payload, anchor_message_uid="u1", termination=FINISH)
    forged = deepcopy(old_payload)
    forged["work"][0]["fields"]["description"] = "Forged historical claim"
    from hermes_state_secretary_notebook import NotebookError
    with pytest.raises(NotebookError, match="immutable version"):
        db.notebook_commit_snapshot(ref, forged, anchor_message_uid="u1", termination=FINISH)
    # Old persisted child controls/receipts may still carry retired fields.
    restored = book(owner, working_state={**payload, "work": [raw | {"entry_id": legacy["entry_id"],
                                                                    "version_id": legacy["version_id"]}]})
    current = restored.get(entry["entry_id"])
    assert "external_refs" not in current["fields"] and "evidence_time" not in current["fields"]
    assert current["source_message_identities"] == entry["source_message_identities"]
    assert not restored.update(entry["entry_id"], {"fields": {"description": BODY["description"]}})["changed"]
    new = restored.update(entry["entry_id"], {"schedule_suggestion": SUGGESTION})["entry"]
    assert new["fields"]["last_progress_time"] == "2021-01-01T00:00:00Z"
    restored.commit(termination=FINISH)
    assert db._read_one("SELECT payload_json FROM secretary_notebook_item WHERE id=?", (legacy["version_id"],))[0] == raw_item
    assert db._read_one("SELECT payload_json FROM secretary_notebook_snapshots WHERE snapshot_id=?", (snapshot_id,))[0] == raw_snapshot
    assert json.loads(raw_item)["fields"]["external_refs"] == ["old-file"]


@pytest.mark.parametrize("uids,start,end", [(["u1", "a2", "t1"], 100, 100),
                                          (["u1", "u2", "a2"], 100, 300),
                                          (["a1", "a2", "t1"], 500, 500),
                                          (["t1", "s1"], 400, 600)])
def test_source_time_priority_and_model_projection_are_readonly(owner, uids, start, end):
    db, ref = owner
    store = book(owner)
    entry = create(store, source_message_uids=uids)
    before = store.snapshot_state()
    interval = evidence_time(entry, db=db, conversation_ref=ref)
    assert interval == {"start_time": datetime.fromtimestamp(start, timezone.utc).isoformat(),
                        "end_time": datetime.fromtimestamp(end, timezone.utc).isoformat()}
    projected = readable_notebook_entry(entry, db=db, conversation_ref=ref)
    expected = (format_timestamp(start) if start == end else
                {"start_time": format_timestamp(start), "end_time": format_timestamp(end)})
    assert projected["evidence_time"] == expected
    assert "evidence_time" not in projected["fields"]
    assert readable_notebook_entry(projected) == projected
    store.commit(termination=FINISH)
    shown = show_notebook(db.notebook_current(ref), db=db)["payload"]["work"][0]
    assert shown["evidence_time"] == expected
    assert store.snapshot_state() == before


def test_range_only_unknown_and_candidate_reference_time_keep_provenance_meaning(owner):
    db, ref = owner
    store = book(owner)
    interval = {"start_time": "1970-01-01T00:01:40+00:00", "end_time": "1970-01-01T00:05:00+00:00"}
    source = create(store, source_message_uids=[], source_time_range=interval)
    assert evidence_time(source, db=db, conversation_ref=ref) == interval
    uid_source = create(store, source_time_range=interval)
    assert evidence_time(uid_source, db=db)["start_time"] == interval["start_time"]
    assert evidence_time(uid_source, db=db)["end_time"] == interval["start_time"]
    candidate = store.create("candidate", {**MINIMAL["candidate"], "notebook_refs": [source["entry_id"]],
                                           "source_types": ["matter"]})["entry"]
    assert evidence_time(candidate, db=db, conversation_ref=ref, state=store.snapshot_state()) == interval
    store.commit(termination=FINISH)
    assert evidence_time(candidate, db=db, conversation_ref=ref) == interval
    assert readable_notebook_entry(candidate, db=db, conversation_ref=ref)["fields"]["notebook_refs"] == [source["entry_id"]]
    assert evidence_time(uid_source) is None
    # A missing time is unknown even though the entry has runtime created_at.
    db._execute_write(lambda conn: conn.execute("UPDATE messages SET timestamp='unknown' WHERE message_uid='u1'"))
    assert evidence_time(uid_source, db=db) is None
    assert "evidence_time" not in store.snapshot_state()["work"][0]


def test_archive_atomically_cleans_only_auxiliary_relations_with_new_versions(owner):
    db, _ref = owner
    store = book(owner)
    target, unrelated = create(store), create(store, "question")
    related = create(store, "action", relations=[{"kind": "depends_on", "entry_id": target["entry_id"]},
                                                {"kind": "related_to", "entry_id": unrelated["entry_id"]}])
    old = deepcopy(related)
    result = store.archive(target["entry_id"], "This scope was settled")
    assert result["relations_removed_from"] == [related["entry_id"]]
    current = store.get(related["entry_id"])
    assert current["relations"] == [{"kind": "related_to", "entry_id": unrelated["entry_id"]}]
    assert current["fields"] == old["fields"] and current["status"] == old["status"]
    assert current["source_message_identities"] == old["source_message_identities"]
    assert current["entry_id"] == old["entry_id"] and current["version_id"] != old["version_id"]
    assert current["last_processed_at"] == old["last_processed_at"]
    assert result["updated_entries"] == [current]
    assert count(db) == 5
    store.commit(termination=FINISH)
    assert book(owner).get(related["entry_id"])["relations"] == current["relations"]


def test_archive_insert_failure_rolls_back_all_versions_and_working_state(owner):
    db, _ref = owner
    store = book(owner)
    target = create(store)
    related = create(store, relations=[{"kind": "related_to", "entry_id": target["entry_id"]}])
    before, versions = store.snapshot_state(), count(db)
    db._execute_write(lambda conn: conn.execute(
        f"CREATE TRIGGER refuse_cleanup BEFORE INSERT ON secretary_notebook_item WHEN NEW.lineage_id={int(related['entry_id'])} "
        "BEGIN SELECT RAISE(ABORT, 'injected cleanup failure'); END"))
    with pytest.raises(sqlite3.IntegrityError, match="injected"):
        store.archive(target["entry_id"], "Settled")
    assert store.snapshot_state() == before and count(db) == versions


@pytest.mark.parametrize("protected", ["gap", "candidate"])
def test_protected_incoming_refs_block_archive_and_prevent_any_relation_cleanup(owner, protected):
    db, _ref = owner
    store = book(owner)
    situation = create(store, "situation")
    create(store, relations=[{"kind": "related_to", "entry_id": situation["entry_id"]}])
    if protected == "gap":
        fields = {**MINIMAL["implicit_gap"], "situation_ref": situation["entry_id"]}
        store.create("implicit_gap", fields, source_message_uids=["u1"])
    else:
        fields = {**MINIMAL["candidate"], "notebook_refs": [situation["entry_id"]], "source_types": ["situation"]}
        store.create("candidate", fields)
    before, versions = store.snapshot_state(), count(db)
    with pytest.raises(NotebookValidationError) as error:
        store.archive(situation["entry_id"], "Settled")
    assert error.value.code == "invalid_reference"
    assert all(not path.startswith("relations") for row in error.value.details["referrers"] for path in row["fields"])
    assert store.snapshot_state() == before and count(db) == versions


def test_archive_cleanup_preserves_committed_off_path_claim_without_licensing_new_content(owner):
    db, ref = owner
    store = book(owner)
    target = create(store, source_message_uids=["u2"])
    related = create(store, source_message_uids=["u2"], relations=[{"kind": "based_on", "entry_id": target["entry_id"]}])
    store.commit(termination=FINISH)
    removed = db._read_one("SELECT id FROM messages WHERE message_uid='u2'")[0]
    db.rewind_to_message("main", removed)
    db.notebook_reselect_pointer(ref)
    restored = book(owner)
    restored.archive(target["entry_id"], "Scope settled")
    cleaned = restored.get(related["entry_id"])
    assert cleaned["relations"] == []
    assert cleaned["source_message_identities"] == related["source_message_identities"]
    restored.update(related["entry_id"], {"fields": {"processing_note": "Same evidence retained"}})
    restored.commit(termination=FINISH)
    reopened = book(owner)
    before, versions = reopened.snapshot_state(), count(db)
    for patch in ({"fields": {"description": "An unrelated new claim"}}, {"schedule_suggestion": SUGGESTION}):
        with pytest.raises(NotebookValidationError):
            reopened.update(related["entry_id"], patch)
        assert reopened.snapshot_state() == before and count(db) == versions
    assert readable_notebook_state(before, db=db, conversation_ref=ref)["work"][0]["evidence_time"] is not None


def test_legacy_off_path_payload_keeps_version_gate_and_exact_provenance_basis(owner):
    db, ref = owner
    initial = book(owner)
    entry = create(initial, source_message_uids=["u2"])
    raw = initial.snapshot_state()["work"][0]
    raw["fields"].update({"external_refs": ["old-material"], "evidence_time": "2020-01-01T00:00:00Z"})
    legacy = db._execute_write(lambda conn: insert_item_conn(conn, ref, raw, entry["version_id"]))
    payload = initial.snapshot_state()
    payload["work"] = [legacy]
    db.notebook_commit_snapshot(ref, payload, anchor_message_uid="u1", termination=FINISH)
    removed = db._read_one("SELECT id FROM messages WHERE message_uid='u2'")[0]
    db.rewind_to_message("main", removed)
    db.notebook_reselect_pointer(ref)
    raw["version_id"] = legacy["version_id"]
    restored = book(owner, working_state={**payload, "work": [raw]})
    assert not restored.update(entry["entry_id"], {"fields": {"description": BODY["description"]}})["changed"]
    result = restored.update(entry["entry_id"], {"fields": {"processing_note": "Reviewed the unchanged old claim"}})
    assert result["entry"]["source_message_identities"] == legacy["source_message_identities"]
    restored.commit(termination=FINISH)
    resumed = book(owner)
    before, versions = resumed.snapshot_state(), count(db)
    with pytest.raises(NotebookValidationError):
        resumed.update(entry["entry_id"], {"fields": {"description": "Borrowed evidence for a new claim"}})
    assert resumed.snapshot_state() == before and count(db) == versions


def synthetic_user_carrier(db, carrier):
    """Persist the same trusted row kinds used by the native producers."""
    from types import SimpleNamespace
    from agent.message_metadata import build_framework_message_wrapper, build_system_reminder_wrapper
    from gateway.response_filters import display_kind_for_event
    from secretary.heartbeat import render_heartbeat

    if carrier == "heartbeat":
        content = render_heartbeat("Review the current work", 700)
        display_kind = display_kind_for_event(SimpleNamespace(internal=False, _heartbeat_session_id="main"))
        metadata = {}
    elif carrier == "reminder":
        content = build_system_reminder_wrapper("The agreed check is due")
        display_kind = "process_complete"
        metadata = {"origin": "reminder", "producer": "reminder", "reminder_ids": ["rem-test"]}
    else:
        content = build_framework_message_wrapper("Notebook maintenance completed")
        display_kind = "process_complete"
        metadata = {"origin": "notebook", "producer": "noting_result", "noting_run_output": True}
    db.append_message("main", "user", content, message_uid=carrier, timestamp=700,
                      display_kind=display_kind, display_metadata=metadata)


@pytest.mark.parametrize("carrier", ["heartbeat", "reminder", "framework"])
@pytest.mark.parametrize("other_sources,expected", [(["a2"], 500), (["u2", "a2"], 300), ([], 700)])
def test_synthetic_user_carriers_do_not_override_human_or_assistant_evidence(owner, carrier, other_sources, expected):
    db, ref = owner
    synthetic_user_carrier(db, carrier)
    store = book(owner)
    entry = create(store, source_message_uids=[carrier, *other_sources])
    before, versions = store.snapshot_state(), count(db)
    interval = evidence_time(entry, db=db, conversation_ref=ref)
    timestamp = datetime.fromtimestamp(expected, timezone.utc).isoformat()
    assert interval == {"start_time": timestamp, "end_time": timestamp}
    assert readable_notebook_entry(entry, db=db, conversation_ref=ref)["evidence_time"] == format_timestamp(expected)
    assert store.snapshot_state() == before and count(db) == versions


def test_pure_compaction_summary_is_not_authorized_as_new_notebook_provenance(owner):
    from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
    db, _ref = owner
    db.append_message("main", "user", SUMMARY_PREFIX + "summary\n" + _SUMMARY_END_MARKER,
                      message_uid="pure-summary", _compressed_summary=True, timestamp=700)
    store = book(owner)
    before, versions = store.snapshot_state(), count(db)
    with pytest.raises(NotebookValidationError) as error:
        create(store, source_message_uids=["pure-summary", "a2"])
    assert error.value.code == "source_unavailable"
    assert store.snapshot_state() == before and count(db) == versions


@pytest.mark.parametrize("typed_steer", [False, True])
def test_human_input_is_classified_by_native_metadata_not_heartbeat_words(owner, typed_steer):
    from agent.prompt_builder import STEER_DISPLAY_KIND
    db, ref = owner
    db.append_message("main", "user", "<heartbeat>quoted by the user, not a runtime event</heartbeat>",
                      message_uid="human-quoted", timestamp=800,
                      display_kind=STEER_DISPLAY_KIND if typed_steer else None)
    entry = create(book(owner), source_message_uids=["human-quoted", "a2"])
    timestamp = datetime.fromtimestamp(800, timezone.utc).isoformat()
    assert evidence_time(entry, db=db, conversation_ref=ref) == {"start_time": timestamp, "end_time": timestamp}


def admitted_instant(owner, *, sid="main", now=None, recurring=False):
    """Use actual Scheduler admission and native transaction to bind the receipt."""
    from pathlib import Path
    from secretary import reminders, schedules
    from secretary.scheduler_time import epoch_to_utc_iso
    from tests.secretary.reminder_runtime import bind_reminder_runtime, persist_native_carrier

    db, ref = owner
    if now is None:
        import time
        now = time.time()
    Path(db.db_path).with_name("config.yaml").write_text("scheduler:\n  enabled: true\nnoting:\n  enabled: true\n")
    bind_reminder_runtime(db, ref, sid)
    table = schedules.SchedulerStore(db, ref, session_id=sid)
    expression = "every 1m" if recurring else epoch_to_utc_iso(now - 10)
    made = table.create("Review the pending booking", expression, "instant", now=now - 120 if recurring else now)
    assert made["success"], made
    claim = schedules.claim_due(db, made["schedule"]["schedule_id"], owner="notebook-evidence-v2", now=now)
    assert claim
    receipt = reminders.admit_active_reminder(db, claim, session_id=sid, now=now)
    assert receipt
    persist_native_carrier(db, sid, receipt["resolved"]["text"])
    witness = reminders.active_admission_witness(receipt["resolved"]["text"])
    assert witness.durable(db)
    stored = db.get_messages(sid)[-1]
    assert stored["role"] == "user" and not stored.get("display_kind")
    proof = db._read_one("SELECT * FROM secretary_pending_reminders WHERE schedule_id=?",
                         (made["schedule"]["schedule_id"],))
    assert proof["origin_instant"] and proof["delivery_semantics"] == "user_reminder"
    assert proof["carrier_message_uid"] == stored["message_uid"] and proof["carrier_content"] == stored["content"]
    return table, made["schedule"]["schedule_id"], stored


def evidence_db_facts(db):
    return {name: [tuple(row) for row in db._read_all(f"SELECT * FROM {name} ORDER BY rowid")]
            for name in ("messages", "secretary_pending_reminders", "secretary_schedule_registry",
                         "secretary_notebook_item", "secretary_notebook_snapshots", "secretary_notebook_pointer")}


@pytest.mark.parametrize("other_sources,expected", [(["a2"], 500), (["u2", "a2"], 300), ([], None)])
def test_real_instant_admission_receipt_does_not_get_human_time_priority(owner, other_sources, expected):
    db, ref = owner
    _table, _schedule_id, stored = admitted_instant(owner)
    store = book(owner)
    entry = create(store, source_message_uids=[stored["message_uid"], *other_sources])
    before, working = evidence_db_facts(db), store.snapshot_state()
    timestamp = datetime.fromtimestamp(stored["timestamp"] if expected is None else expected, timezone.utc).isoformat()
    assert evidence_time(entry, db=db, conversation_ref=ref) == {"start_time": timestamp, "end_time": timestamp}
    assert evidence_db_facts(db) == before and store.snapshot_state() == working


@pytest.mark.parametrize("action", ["pause", "delete"])
def test_completed_instant_receipt_keeps_identity_after_schedule_changes(owner, action):
    db, ref = owner
    table, schedule_id, stored = admitted_instant(owner, recurring=True)
    result = getattr(table, action)(schedule_id)
    assert result["success"], result
    entry = create(book(owner), source_message_uids=[stored["message_uid"], "a2"])
    before = evidence_db_facts(db)
    timestamp = datetime.fromtimestamp(500, timezone.utc).isoformat()
    assert evidence_time(entry, db=db, conversation_ref=ref) == {"start_time": timestamp, "end_time": timestamp}
    assert evidence_db_facts(db) == before


def test_real_instant_source_keeps_original_receipt_owner_in_legal_branch(owner):
    db, _ref = owner
    _table, _schedule_id, stored = admitted_instant(owner)
    make(db, "branch", "main", "_branched_from")
    branch_ref = db.inherit_foreground_branch("main", "branch")
    branch = NotebookStore(db, branch_ref, anchor_message_uid=stored["message_uid"])
    entry = create(branch, source_message_uids=[stored["message_uid"], "a2"])
    before = evidence_db_facts(db)
    timestamp = datetime.fromtimestamp(500, timezone.utc).isoformat()
    assert evidence_time(entry, db=db, conversation_ref=branch_ref) == {"start_time": timestamp, "end_time": timestamp}
    assert evidence_db_facts(db) == before


@pytest.mark.parametrize("same_body", [False, True])
def test_foreign_same_uid_does_not_borrow_instant_receipt(owner, same_body):
    db, _ref = owner
    _table, _schedule_id, stored = admitted_instant(owner)
    make(db, "foreign")
    foreign_ref = ref_of(db, "foreign")
    db.append_message("foreign", "user", stored["content"] if same_body else "A different human statement",
                      message_uid=stored["message_uid"], timestamp=800)
    db.append_message("foreign", "assistant", "The foreign assistant reply", message_uid="foreign-assistant", timestamp=900)
    store = NotebookStore(db, foreign_ref, anchor_message_uid=stored["message_uid"])
    entry = create(store, source_message_uids=[stored["message_uid"], "foreign-assistant"])
    before = evidence_db_facts(db)
    timestamp = datetime.fromtimestamp(800, timezone.utc).isoformat()
    assert evidence_time(entry, db=db, conversation_ref=foreign_ref) == {"start_time": timestamp, "end_time": timestamp}
    assert evidence_db_facts(db) == before


@pytest.mark.parametrize("typed_steer", [False, True])
def test_human_exact_instant_wrapper_without_receipt_stays_human(owner, typed_steer):
    from agent.message_metadata import build_user_reminder_wrapper
    from agent.prompt_builder import STEER_DISPLAY_KIND
    db, ref = owner
    wrapper = build_user_reminder_wrapper("SCHEDULED ATTENTION\nReview the pending booking.", timestamp=700)
    db.append_message("main", "user", str(wrapper), message_uid="human-instant-wrapper", timestamp=700,
                      display_kind=STEER_DISPLAY_KIND if typed_steer else None)
    entry = create(book(owner), source_message_uids=["human-instant-wrapper", "a2"])
    timestamp = datetime.fromtimestamp(700, timezone.utc).isoformat()
    assert evidence_time(entry, db=db, conversation_ref=ref) == {"start_time": timestamp, "end_time": timestamp}


def test_instant_without_assistant_keeps_unknown_source_time_without_side_effects(owner):
    db, ref = owner
    _table, _schedule_id, stored = admitted_instant(owner)
    store = book(owner)
    entry = create(store, source_message_uids=[stored["message_uid"]])
    db._execute_write(lambda conn: conn.execute("UPDATE messages SET timestamp='unknown' WHERE id=?", (stored["id"],)))
    before, working = evidence_db_facts(db), store.snapshot_state()
    assert evidence_time(entry, db=db, conversation_ref=ref) is None
    assert evidence_db_facts(db) == before and store.snapshot_state() == working


def test_same_owner_uid_with_changed_body_cannot_borrow_old_instant_receipt(owner):
    db, ref = owner
    _table, _schedule_id, stored = admitted_instant(owner)
    assert db.secretary_set_user_content("main", stored["id"], "A new human statement at this source",
                                         expected_message_uid=stored["message_uid"]) == 1
    entry = create(book(owner), source_message_uids=[stored["message_uid"], "a2"])
    before = evidence_db_facts(db)
    timestamp = datetime.fromtimestamp(stored["timestamp"], timezone.utc).isoformat()
    assert evidence_time(entry, db=db, conversation_ref=ref) == {"start_time": timestamp, "end_time": timestamp}
    assert evidence_db_facts(db) == before
