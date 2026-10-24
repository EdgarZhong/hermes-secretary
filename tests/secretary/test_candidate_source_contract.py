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
    }}
    if form == "messages":
        args["source_message_uids"] = ["origin-a"]
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
    assert candidate["status"] == "proposed"
    assert script.results["s02-2"]["payload"]["work"][0]["version_id"] == source["version_id"]
    if form == "refs":
        assert candidate["fields"]["notebook_refs"] == [source["entry_id"]]
        assert candidate["source_message_uids"] == []
    else:
        assert candidate["fields"]["notebook_refs"] == []
        assert candidate["source_message_uids"] == ["origin-a"]
    persisted = runtime.db.notebook_current(runtime.db.resolve_conversation_ref("parent"))["payload"]
    assert persisted["candidates"][0]["fields"] == candidate["fields"]
    if form == "messages":
        assert persisted["candidates"][0]["source_message_identities"] == [
            {"conversation_ref": runtime.db.resolve_conversation_ref("parent"), "message_uid": "origin-a"}]


@pytest.mark.parametrize("target", SUMMARIES)
@pytest.mark.parametrize("bad", ["mixed", "range_only", "missing_uid", "foreign_uid", "foreign_ref"])
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
        args = _candidate(script, target, "refs" if bad in {"mixed", "foreign_ref"} else "messages")
        if bad == "mixed":
            args["source_message_uids"] = ["origin-a"]
        elif bad == "range_only":
            args.pop("source_message_uids")
            args["source_time_range"] = deepcopy(RANGE)
        elif bad in {"missing_uid", "foreign_uid"}:
            args["source_message_uids"] = ["not-on-current-path" if bad == "missing_uid" else "foreign-only"]
        else:
            args["fields"]["notebook_refs"] = [foreign["entry_id"]]
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
    payload = script.results["s02-2"]["payload"]
    assert not payload["candidates"]
    assert payload["work"][0]["version_id"] == script.results["s02-0"]["entry"]["version_id"]


@pytest.mark.parametrize("target", SUMMARIES)
def test_callable_schema_advertises_each_existing_candidate_target(target):
    schema = next(tool for tool in noting_tool_schemas() if tool["name"] == "notebook_create")
    validate({"entry_type": "candidate", "fields": {
        "description": SUMMARIES[target], "targets": [target], "notebook_refs": [], "source_types": [],
    }, "source_message_uids": ["original"]}, schema["parameters"])


@pytest.mark.parametrize("target", ["rule", "skill", "conversation"])
def test_new_ref_targets_convert_atomically_without_claiming_a_write(runtime, target):
    _prepare(runtime)

    def convert(script):
        return {"entry_id": script.results["s02-1"]["entry"]["entry_id"],
            "fields": {"notebook_refs": [], "source_types": []},
            "source_message_uids": ["origin-a"], "source_time_range": None,
        }

    script = _ProviderScript([
        _source(), ("notebook_create", lambda script: _candidate(script, target, "refs")),
        ("notebook_update", convert), ("notebook_show", {}),
        _finish("Changed only source representation; Candidate and source remain unapproved"),
    ])
    outcome = _run(runtime, script)
    assert outcome.committed, outcome
    converted = script.results["s02-2"]["entry"]
    assert converted["status"] == "proposed"
    assert converted["fields"]["description"] == SUMMARIES[target]
    assert converted["fields"]["notebook_refs"] == converted["fields"]["source_types"] == []
    assert converted["source_message_uids"] == ["origin-a"]
    assert converted["source_time_range"] is None
    assert script.results["s02-3"]["payload"]["work"][0]["version_id"] == script.results["s02-0"]["entry"]["version_id"]
