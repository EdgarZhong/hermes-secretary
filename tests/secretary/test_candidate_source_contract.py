"""Candidate target-specific indexes have one provenance form through native tools."""

from copy import deepcopy

from jsonschema import validate
import pytest

from secretary.notebook_store import NotebookStore
from secretary.noting_tools import noting_tool_schemas
from tests.secretary.test_candidate_settlement_lifecycle import (
    _ProviderScript,
    _finish,
    _maintain,
    _run,
    runtime as runtime,
)


SUMMARIES = {
    "memory": "Remember the museum preference and its qualification",
    "rule": "Avoid crowded museums when choosing a visit",
    "skill": "Choose a quiet museum: compare crowd levels before booking",
    "conversation": "Apply the quiet-visit preference when discussing this trip",
}
RANGE = {"start_time": "1970-01-01T00:01:40+00:00", "end_time": "1970-01-01T00:01:40+00:00"}
RANGES = [RANGE, {"start_time": "1970-01-01T00:01:30+00:00", "end_time": "1970-01-01T00:01:40+00:00"}]


def _assert_same_source(current, original):
    assert current["entry_id"] == original["entry_id"]
    assert current["fields"] == original["fields"]
    assert "version_id" not in current and "version_id" not in original


def _prepare(runtime):
    runtime.db.append_message("parent", "user", "Review the existing evidence without writing outside.",
                              message_uid="actual-result", timestamp=300)


def _source():
    return _maintain({"entry_type": "matter", "fields": {
        "description": "I prefer quiet museums.",
        "completion_condition": "Visit preference understood",
    }, "source_message_uids": ["origin-a"]})


def _candidate(script, target, form):
    source = script.results["s02-0"]["entry"]
    args = {"entry_type": "candidate", "fields": {
        "description": SUMMARIES[target], "targets": [target],
        "notebook_refs": [source["entry_id"]] if form == "refs" else [],
        "source_types": ["matter"] if form == "refs" else [],
        "stage_evidence": "Existing evidence is indexed; no proposal, approval or outside write is established.",
    }}
    if form in {"messages", "mixed_direct"}:
        args["source_message_uids"] = ["origin-a"]
    if form in {"ranges", "mixed_direct"}:
        args["source_time_ranges"] = deepcopy(RANGES)
    return args


@pytest.mark.parametrize("target", SUMMARIES)
@pytest.mark.parametrize("form", ["refs", "messages"])
def test_native_candidate_accepts_source_form_for_each_target(runtime, target, form):
    _prepare(runtime)
    script = _ProviderScript([
        _source(), ("notebook_create", lambda script: _candidate(script, target, form)),
        ("notebook_show", {}), _finish("Indexed existing evidence; no proposal, approval or outside write"),
    ])
    outcome = _run(runtime, script)
    assert outcome.committed, outcome
    assert script.results["s02-1"]["success"], script.results["s02-1"]
    source = script.results["s02-0"]["entry"]
    candidate = script.results["s02-2"]["payload"]["candidates"][0]
    assert candidate["fields"]["description"] == SUMMARIES[target]
    assert candidate["done"] is False
    assert "no proposal, approval or outside write" in candidate["fields"]["stage_evidence"]
    _assert_same_source(script.results["s02-2"]["payload"]["work"][0], source)
    if form == "refs":
        assert candidate["fields"]["notebook_refs"] == [source["entry_id"]]
        assert candidate["provenance"] == []
    else:
        assert candidate["fields"]["notebook_refs"] == []
        assert candidate["provenance"] == [["origin-a"]]
    assert len(candidate["evidence_time"]) == 1
    persisted = runtime.db.notebook_current(runtime.db.resolve_conversation_ref("parent"))["payload"]
    assert persisted["candidates"][0]["fields"] == candidate["fields"]
    assert persisted["candidates"][0]["provenance"] == candidate["provenance"]


@pytest.mark.parametrize("target", SUMMARIES)
@pytest.mark.parametrize("bad", ["mixed", "refs_ranges", "refs_both", "missing_uid", "foreign_uid", "foreign_ref", "none"])
def test_native_candidate_rejects_invalid_provenance_without_changing_source(runtime, target, bad):
    _prepare(runtime)
    runtime.db.create_session("foreign", source="test", session_key="other")
    runtime.db.append_message("foreign", "user", "Foreign evidence", message_uid="foreign-only", timestamp=100)
    foreign_store = NotebookStore(runtime.db, runtime.db.resolve_conversation_ref("foreign"),
                                  anchor_message_uid="foreign-only")
    foreign = foreign_store.create("matter", {"description": "Foreign matter", "completion_condition": "Complete"},
                                   source_message_uids=["foreign-only"])["entry"]
    foreign_store.commit(termination={"type": "finish_noting", "reason": "Other Conversation"})

    def bad_candidate(script):
        args = _candidate(script, target, "refs" if bad in {"mixed", "refs_ranges", "refs_both", "foreign_ref"} else "messages")
        patches = {
            "mixed": {"source_message_uids": ["origin-a"]},
            "refs_ranges": {"source_time_ranges": [deepcopy(RANGE)]},
            "refs_both": {"source_message_uids": ["origin-a"], "source_time_ranges": [deepcopy(RANGE)]},
            "missing_uid": {"source_message_uids": ["not-on-current-path"]},
            "foreign_uid": {"source_message_uids": ["foreign-only"]},
            "none": {"source_message_uids": []},
            "foreign_ref": {"fields": {**args["fields"], "notebook_refs": [foreign["entry_id"]]}},
        }
        args.update(patches[bad])
        return args

    script = _ProviderScript([
        _source(), ("notebook_create", bad_candidate), ("notebook_show", {}),
        _finish("Refused invalid Candidate; preserved the existing source"),
    ])
    outcome = _run(runtime, script)
    assert outcome.committed, outcome
    refused = script.results["s02-1"]
    assert refused["success"] is False
    expected = ("source_unavailable" if bad in {"missing_uid", "foreign_uid"}
                else "invalid_reference" if bad == "foreign_ref" else "invalid_argument")
    assert refused["error"]["code"] == expected
    if bad in {"refs_ranges", "refs_both"}:
        assert refused["error"]["field"] == "source_time_ranges"
    payload = script.results["s02-2"]["payload"]
    assert not payload["candidates"]
    _assert_same_source(payload["work"][0], script.results["s02-0"]["entry"])


@pytest.mark.parametrize("target", SUMMARIES)
def test_callable_schema_advertises_each_existing_candidate_target(target):
    schema = next(tool for tool in noting_tool_schemas() if tool["name"] == "notebook_create")
    validate({"entry_type": "candidate", "fields": {
        "description": SUMMARIES[target], "targets": [target], "notebook_refs": [], "source_types": [],
    }, "source_message_uids": ["original"]}, schema["parameters"])


@pytest.mark.parametrize("target", ["rule", "skill", "conversation"])
@pytest.mark.parametrize("form", ["messages"])
def test_new_ref_targets_convert_atomically_without_claiming_a_write(runtime, target, form):
    _prepare(runtime)

    def convert(script):
        return {"entry_id": script.results["s02-1"]["entry"]["entry_id"],
            "fields": {"notebook_refs": [], "source_types": []},
            "source_message_uids": ["origin-a"],
        }

    script = _ProviderScript([
        _source(), ("notebook_create", lambda script: _candidate(script, target, "refs")),
        ("notebook_update", convert), ("notebook_show", {}),
        _finish("Changed only source representation; Candidate and source remain unapproved"),
    ])
    outcome = _run(runtime, script)
    assert outcome.committed, outcome
    converted = script.results["s02-2"]["entry"]
    assert converted["done"] is False
    assert "no proposal, approval or outside write" in converted["fields"]["stage_evidence"]
    assert converted["fields"]["description"] == SUMMARIES[target]
    assert converted["fields"]["notebook_refs"] == converted["fields"]["source_types"] == []
    assert converted["provenance"] == [["origin-a"]]
    _assert_same_source(script.results["s02-3"]["payload"]["work"][0], script.results["s02-0"]["entry"])


@pytest.mark.parametrize("form", ["messages"])
def test_direct_candidate_requires_complete_source_clear_before_switch_to_refs(runtime, form):
    _prepare(runtime)

    def to_refs(script, clear=False):
        source = script.results["s02-0"]["entry"]
        candidate = script.results["s02-1"]["entry"]
        arguments = {"entry_id": candidate["entry_id"], "fields": {
            "notebook_refs": [source["entry_id"]], "source_types": ["matter"]}}
        if clear:
            arguments.update(source_message_uids=[])
        return arguments

    script = _ProviderScript([
        _source(), ("notebook_create", lambda script: _candidate(script, "memory", form)),
        ("notebook_update", to_refs), ("notebook_show", {}),
        ("notebook_update", lambda script: to_refs(script, clear=True)), ("notebook_show", {}),
        _finish("Changed provenance mode after clearing direct sources; no outside write"),
    ])
    outcome = _run(runtime, script)
    assert outcome.committed, outcome
    created = script.results["s02-1"]["entry"]
    refused = script.results["s02-2"]
    assert not refused["success"] and refused["error"]["code"] == "invalid_argument"
    assert script.results["s02-3"]["payload"]["candidates"][0] == created
    converted = script.results["s02-4"]["entry"]
    source = script.results["s02-0"]["entry"]
    assert converted["entry_id"] == created["entry_id"]
    assert "version_id" not in converted and "version_id" not in created
    assert converted["fields"]["description"] == created["fields"]["description"]
    assert converted["done"] is created["done"] is False
    assert converted["fields"]["stage_evidence"] == created["fields"]["stage_evidence"]
    assert converted["fields"]["notebook_refs"] == [source["entry_id"]]
    assert converted["fields"]["source_types"] == ["matter"]
    assert converted["provenance"] == []
    shown = script.results["s02-5"]["payload"]
    assert shown["candidates"][0] == converted
    _assert_same_source(shown["work"][0], source)
    assert shown["work"][0]["candidate_refs"] == [created["entry_id"]]


@pytest.mark.parametrize("target", SUMMARIES)
@pytest.mark.parametrize("form", ["ranges", "mixed_direct"])
def test_retired_time_ranges_cannot_create_direct_candidate(runtime, target, form):
    _prepare(runtime)
    script = _ProviderScript([
        _source(), ("notebook_create", lambda script: _candidate(script, target, form)),
        ("notebook_show", {}), _finish("Retired source range input was refused"),
    ])
    outcome = _run(runtime, script)
    assert outcome.committed, outcome
    refused = script.results["s02-1"]
    assert not refused["success"] and refused["error"]["field"] == "source_time_ranges"
    assert not script.results["s02-2"]["payload"]["candidates"]
    _assert_same_source(script.results["s02-2"]["payload"]["work"][0], script.results["s02-0"]["entry"])
