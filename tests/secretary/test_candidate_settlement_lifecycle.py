"""S02: legal settlement through persistent native Noting children and real SQLite.

Only the provider response boundary and capability switch are controlled. Scripts
demonstrate available operations, not that a real model chooses these operations.
"""

from copy import deepcopy
import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from hermes_state import SessionDB
from secretary.notebook_store import NotebookStore
from secretary.noting_child import DEFAULT_NOTING_TASK_INSTRUCTION, run_noting_task


def _reply(name=None, arguments=None, call_id=""):
    calls = None if name is None else [SimpleNamespace(
        id=call_id, type="function",
        function=SimpleNamespace(name=name, arguments=json.dumps(arguments)),
    )]
    return SimpleNamespace(
        choices=[SimpleNamespace(
            message=SimpleNamespace(content="Paused" if calls is None else None, tool_calls=calls),
            finish_reason="stop" if calls is None else "tool_calls",
        )], model="controlled/s02", usage=None,
    )


class _ProviderScript:
    """Read real tool responses before returning the next single native call."""

    def __init__(self, steps, *, after_exhausted=None):
        self.steps = iter(steps)
        self.after_exhausted = after_exhausted
        self.results = {}
        self.wires = []
        self.issued = []
        self.failures = []

    def __call__(self, **wire):
        self.wires.append(deepcopy(wire))
        for row in wire["messages"]:
            call_id = row.get("tool_call_id")
            if row.get("role") == "tool" and call_id in self.issued:
                self.results[call_id] = json.loads(row["content"])
        if self.issued:
            assert self.issued[-1] in self.results, "The dispatcher must return the previous call result"
        try:
            name, arguments = next(self.steps)
        except StopIteration:
            if self.after_exhausted:
                self.after_exhausted()
            return _reply()
        if callable(arguments):
            try:
                arguments = arguments(self)
            except Exception as exc:
                self.failures.append(repr(exc))
                raise
        call_id = f"s02-{len(self.issued)}"
        self.issued.append(call_id)
        return _reply(name, arguments, call_id)


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    db = SessionDB(tmp_path / "state.db")
    db.create_session("parent", source="test", session_key="peer")
    db.append_message("parent", "user", "Begin this conversation.", message_uid="stable-anchor", timestamp=90)
    for uid, content in [("origin-a", "I prefer quiet museums."),
                         ("origin-b", "Please follow up my unfinished booking."),
                         ("correction", "The booking must remain open until Friday.")]:
        db.append_message("parent", "user", content, message_uid=uid, timestamp=100)
    monkeypatch.setattr("secretary.noting_runtime.noting_trigger_gate", lambda *a, **k: (True, ""))
    client = MagicMock()
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **kwargs: client)
    monkeypatch.setattr("model_tools.get_tool_definitions", lambda **kwargs: [])
    monkeypatch.setattr("model_tools.check_toolset_requirements", lambda *a, **k: {})
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **k: {})
    monkeypatch.setattr("agent.title_generator.maybe_auto_title", lambda *a, **k: None)
    monkeypatch.setattr("run_agent._hermes_home", tmp_path / "isolated-home")
    (tmp_path / "isolated-home/logs").mkdir(parents=True)
    parents = []

    def make_parent(database):
        from run_agent import AIAgent

        parent = AIAgent(
            api_key="test-key", base_url="https://api.example.test/v1", quiet_mode=True,
            skip_context_files=True, skip_memory=True, session_db=database, session_id="parent",
            gateway_session_key="peer",
        )
        parent.tools = []
        parent.valid_tool_names = set()
        parent._cached_system_prompt = "Frozen parent root"
        parent._use_prompt_caching = False
        parent.compression_enabled = False
        parent.save_trajectories = False
        parent._persist_disabled = False
        parent._secretary_conversation_ref = database.resolve_conversation_ref("parent")
        parent._session_messages = database.get_messages_as_conversation("parent")
        parents.append(parent)
        return parent

    yield SimpleNamespace(db=db, client=client, make_parent=make_parent)
    for parent in parents:
        parent.close()
    db.close()


def _seed(runtime, *, two=False, shared=False, ranged=False, corrected=False, outcome="success"):
    db = runtime.db
    ref = db.resolve_conversation_ref("parent")
    store = NotebookStore(db, ref, anchor_message_uid="stable-anchor" if ranged else "correction")
    source_args = ({"source_time_range": {"start_time": "1970-01-01T00:01:40+00:00",
                                         "end_time": "1970-01-01T00:01:40+00:00"}}
                   if ranged else {"source_message_uids": ["origin-a"]})
    first = store.create("matter", {"description": "I prefer quiet museums.",
                                   "completion_condition": "Preference recorded"}, **source_args)["entry"]
    sources = [first]
    if two:
        sources.append(store.create("action", {
            "description": "Follow up my unfinished booking.", "owner": "assistant",
            "completion_condition": "Booking confirmed",
        }, source_message_uids=["origin-b"])["entry"])
    candidate = store.create("candidate", {
        "description": "Record museum preference" + (" and booking" if two else ""),
        "targets": ["memory"], "notebook_refs": [entry["entry_id"] for entry in sources],
        "source_types": [entry["entry_type"] for entry in sources],
    }, status="awaiting_result")["entry"]
    other = None
    if shared:
        other = store.create("candidate", {
            "description": "Separate unapproved museum account", "targets": ["memory"],
            "notebook_refs": [first["entry_id"]], "source_types": ["matter"],
        })["entry"]
    if corrected:
        sources[0] = store.update(first["entry_id"], {
            "fields": {"description": "Museum preference saved; booking still needs follow-up until Friday.",
                       "completion_condition": "Booking confirmed Friday"},
            "source_message_uids": ["origin-a", "correction"],
        })["entry"]
    store.commit(termination={"type": "finish_noting", "reason": "Prior indexed evidence"})
    proposal = {"candidate": candidate["entry_id"], "destination": "synthetic-space",
                "sources": [{"entry_id": entry["entry_id"], "version_id": entry["version_id"]}
                            for entry in [first] + sources[1:]]}
    db.append_message("parent", "assistant", "Proposal " + json.dumps(proposal),
                      message_uid="proposal", timestamp=200)
    db.append_message("parent", "user", "Approve this museum preference only in synthetic-space.",
                      message_uid="approval", timestamp=201)
    actual = {"outcome": outcome, "covered": [first["entry_id"]] if outcome == "success" else [],
              "destination": "synthetic-space", "unconfirmed": [entry["entry_id"] for entry in sources[1:]]}
    db.append_message("parent", "assistant", tool_calls=[{
        "id": "synthetic-write", "type": "function", "function": {
            "name": "synthetic_destination_write", "arguments": json.dumps(proposal)},
    }], message_uid="destination-action", timestamp=202)
    db.append_message("parent", "tool", json.dumps(actual), tool_name="synthetic_destination_write",
                      tool_call_id="synthetic-write", message_uid="actual-result", timestamp=203)
    return SimpleNamespace(ref=ref, sources=sources, candidate=candidate, other=other)


def _run(runtime, script, *, db=None, anchor="actual-result"):
    database = db or runtime.db
    parent = runtime.make_parent(database)
    runtime.client.chat.completions.create.side_effect = script
    ref = database.resolve_conversation_ref("parent")
    admission = database.noting_admit(ref, anchor, kind="manual")
    assert admission is not None, "Each new task requires a newly admitted parent anchor"
    outcome = run_noting_task(
        parent, admission_id=admission, conversation_ref=ref, anchor_message_uid=anchor,
        trigger_type="manual", runtime_profile="NOTING", admission_timestamp=500,
        task_instruction=DEFAULT_NOTING_TASK_INSTRUCTION,
    )
    assert len(script.results) == len(script.issued)
    assert not script.failures, script.failures
    rows = database.get_messages_as_conversation(outcome.child_session_id)
    assert any(row.get("role") == "tool" for row in rows), "Native child must durably persist tool suffix"
    print("S02_TRACE " + json.dumps({
        "child_session_id": outcome.child_session_id, "committed": outcome.committed,
        "termination": outcome.termination, "results": script.results,
        "current_payload": database.notebook_current(ref)["payload"],
    }, ensure_ascii=False))
    parent.close()
    return outcome


def _maintain(arguments):
    arguments = dict(arguments)
    action = arguments.pop("action", "create")
    if action == "update":
        arguments = {"entry_id": arguments["entry_id"], **arguments["changes"]}
    return "notebook_" + action, arguments


def _archive(entry, reason):
    return _maintain({"action": "archive", "entry_id": entry["entry_id"], "reason": reason})


def _convert(candidate, uids):
    return _maintain({"action": "update", "entry_id": candidate["entry_id"], "changes": {
        "fields": {"notebook_refs": [], "source_types": []},
        "source_message_uids": uids, "source_time_range": None,
    }})


def _finish(reason="Sources handled; reported remaining scope accurately"):
    return "finish_noting", {"reason": reason}


def _payload(runtime):
    return runtime.db.notebook_current(runtime.db.resolve_conversation_ref("parent"))["payload"]


def test_last_ref_conversion_keeps_evidence_then_archives_source_before_candidate(runtime):
    seeded = _seed(runtime)
    script = _ProviderScript([
        _archive(seeded.sources[0], "Premature archive must be refused"),
        _maintain({"action": "update", "entry_id": seeded.candidate["entry_id"],
                   "changes": {"fields": {"notebook_refs": [], "source_types": []}}}),
        _convert(seeded.candidate, ["origin-a"]),
        ("notebook_show", {}),
        _archive(seeded.sources[0], "Actual write covers exact unchanged source"),
        _archive(seeded.candidate, "Source settlement succeeded"), _finish(),
    ])
    outcome = _run(runtime, script)
    assert outcome.committed, outcome
    assert script.results["s02-0"]["error"]["code"] == "invalid_reference"
    assert script.results["s02-1"]["success"] is False
    converted = script.results["s02-2"]["entry"]
    assert converted["status"] == "awaiting_result"
    assert converted["fields"]["description"] == seeded.candidate["fields"]["description"]
    assert converted["source_message_uids"] == ["origin-a"]
    assert converted["source_time_range"] is None
    during = script.results["s02-3"]["payload"]
    assert len(during["work"]) == len(during["candidates"]) == 1
    assert during["candidates"][0]["fields"]["notebook_refs"] == []
    assert script.results["s02-4"]["archived"] and script.results["s02-5"]["archived"]
    with runtime.db._read_ctx() as conn:
        archived = conn.execute(
            "SELECT lineage_id FROM secretary_notebook_item WHERE archived=1 ORDER BY id"
        ).fetchall()
    assert [str(row["lineage_id"]) for row in archived] == [
        seeded.sources[0]["entry_id"], seeded.candidate["entry_id"]]
    assert not _payload(runtime)["work"] and not _payload(runtime)["candidates"]


def test_partial_multiple_sources_preserves_unwritten_responsibility_and_ref_form(runtime):
    seeded = _seed(runtime, two=True)
    remaining = seeded.sources[1]
    script = _ProviderScript([
        _maintain({"action": "update", "entry_id": seeded.candidate["entry_id"], "changes": {
            "fields": {"notebook_refs": [remaining["entry_id"]], "source_types": ["action"],
                       "description": "Booking is unconfirmed; do not repeat uncertain write"},
        }}),
        _archive(seeded.sources[0], "Only museum preference was confirmed saved"), _finish(),
    ])
    outcome = _run(runtime, script)
    assert outcome.committed, outcome
    payload = _payload(runtime)
    assert [entry["entry_id"] for entry in payload["work"]] == [remaining["entry_id"]]
    candidate = payload["candidates"][0]
    assert candidate["fields"]["notebook_refs"] == [remaining["entry_id"]]
    assert candidate["source_message_identities"] == []
    assert candidate["status"] == "awaiting_result"
    assert payload["work"][0]["status"] == "pending"


def test_shared_source_is_retained_before_settled_candidate_closes_without_conversion(runtime):
    seeded = _seed(runtime, shared=True)
    script = _ProviderScript([
        _maintain({"action": "update", "entry_id": seeded.sources[0]["entry_id"], "changes": {
            "fields": {"processing_note": "Retain full body for the other unapproved Candidate"},
        }}),
        _archive(seeded.candidate, "This approved write settled; shared source retained"), _finish(),
    ])
    outcome = _run(runtime, script)
    assert outcome.committed, outcome
    payload = _payload(runtime)
    assert payload["work"][0]["fields"]["description"] == seeded.sources[0]["fields"]["description"]
    assert payload["work"][0]["candidate_refs"] == [seeded.other["entry_id"]]
    assert [entry["entry_id"] for entry in payload["candidates"]] == [seeded.other["entry_id"]]
    assert script.results["s02-0"]["entry"]["fields"]["processing_note"].startswith("Retain")


def test_later_source_correction_is_not_covered_by_approval_of_older_version(runtime):
    seeded = _seed(runtime, corrected=True)
    script = _ProviderScript([
        _maintain({"action": "update", "entry_id": seeded.sources[0]["entry_id"], "changes": {
            "fields": {"description": "Booking still needs follow-up until Friday.",
                       "processing_note": "Retain later correction and unfinished responsibility"},
            "source_message_uids": ["correction"],
        }}),
        _archive(seeded.candidate, "Old museum scope saved; later booking responsibility retained"), _finish(),
    ])
    outcome = _run(runtime, script)
    assert outcome.committed, outcome
    retained = _payload(runtime)["work"][0]
    assert retained["fields"]["description"] == "Booking still needs follow-up until Friday."
    assert retained["status"] == "in_progress"
    assert [source["message_uid"] for source in retained["source_message_identities"]] == ["correction"]
    assert not _payload(runtime)["candidates"]


@pytest.mark.parametrize("outcome", ["partial", "unknown", "failed"])
def test_unconfirmed_destination_outcome_preserves_candidate_and_source(runtime, outcome):
    seeded = _seed(runtime, outcome=outcome)
    script = _ProviderScript([
        ("notebook_show", {}), _finish("Actual outcome remains " + outcome + "; nothing settled"),
    ])
    result = _run(runtime, script)
    assert result.committed, result
    assert _payload(runtime)["work"][0]["version_id"] == seeded.sources[0]["version_id"]
    assert _payload(runtime)["candidates"][0]["version_id"] == seeded.candidate["version_id"]


def test_missing_exact_message_rejects_conversion_without_losing_time_range_source(runtime):
    seeded = _seed(runtime, ranged=True)
    removed = runtime.db._read_one("SELECT id FROM messages WHERE message_uid='origin-a'")[0]
    runtime.db.rewind_to_message("parent", removed)
    runtime.db.notebook_reselect_pointer(seeded.ref)
    runtime.db.append_message("parent", "user", "The original has left this path; keep uncertainty.",
                              message_uid="actual-result", timestamp=204)
    script = _ProviderScript([
        ("conversation_history", {"mode": "read", "message_identity": {
            "conversation_ref": seeded.ref, "message_uid": "origin-a"}, "before": 0, "after": 0}),
        _convert(seeded.candidate, ["origin-a"]),
        _archive(seeded.sources[0], "Cannot archive while exact-source repair failed"),
        _finish("Exact source unavailable; keep source and Candidate pending"),
    ])
    outcome = _run(runtime, script)
    assert outcome.committed, outcome
    assert script.results["s02-0"]["error"]["code"] == "source_unavailable"
    assert script.results["s02-1"]["error"]["code"] == "source_unavailable"
    assert script.results["s02-2"]["error"]["code"] == "invalid_reference"
    assert _payload(runtime)["work"][0]["source_time_range"] == seeded.sources[0]["source_time_range"]
    assert _payload(runtime)["candidates"][0]["version_id"] == seeded.candidate["version_id"]


def test_forced_commit_after_conversion_is_recoverable_from_visible_state_and_history(runtime):
    seeded = _seed(runtime)
    first = _ProviderScript([_convert(seeded.candidate, ["origin-a"])])
    interrupted = _run(runtime, first)
    assert interrupted.committed and interrupted.termination == {"type": "forced"}
    candidate = _payload(runtime)["candidates"][0]
    assert candidate["fields"]["notebook_refs"] == []
    assert candidate["fields"]["description"] == seeded.candidate["fields"]["description"]
    assert _payload(runtime)["work"][0]["entry_id"] == seeded.sources[0]["entry_id"]

    # Open another connection and build a fresh child. The recovery callback may
    # use only that child's visible working data and actual History response.
    reopened = SessionDB(runtime.db.db_path)
    reopened.append_message("parent", "user", "Continue the pending settlement; no new write authorized.",
                            message_uid="resume-request", timestamp=204)
    recovered = {}

    def recover_from_visible(script):
        shown = script.results["s02-0"]["payload"]
        pending = shown["candidates"][0]
        assert pending["fields"]["notebook_refs"] == []
        uids = pending["source_message_uids"]
        history = script.results["s02-1"]["messages"]
        contents = "\n".join(str(row.get("content", "")) for row in history)
        assert "Approve this museum preference only" in contents
        assert '"outcome": "success"' in contents
        proposal = next(row["content"] for row in history if str(row.get("content", "")).startswith("Proposal "))
        source_refs = json.loads(proposal[len("Proposal "):])["sources"]
        original = script.results["s02-2"]["messages"][0]
        assert original["message_uid"] == uids[0]
        assert original["content"] == "I prefer quiet museums."
        source = next(entry for entry in shown["work"] if entry["source_message_uids"] == uids and
                      {"entry_id": entry["entry_id"], "version_id": entry["version_id"]} in source_refs)
        assert {"entry_id": source["entry_id"], "version_id": source["version_id"]} in source_refs
        assert pending["fields"]["description"] == "Record museum preference"
        recovered.update(source=source, candidate=pending)
        return {"action": "archive", "entry_id": source["entry_id"],
                "reason": "Original exact source/version still present; successful approved coverage confirmed"}

    second = _ProviderScript([
        ("notebook_show", {}),
        ("conversation_history", {"mode": "read", "message_identity": {
            "conversation_ref": reopened.resolve_conversation_ref("parent"), "message_uid": "actual-result"},
            "before": 4, "after": 0, "include_tool_content": True}),
        ("conversation_history", lambda script: {
            "mode": "read", "message_identity": {
                "conversation_ref": script.results["s02-0"]["conversation_ref"],
                "message_uid": script.results["s02-0"]["payload"]["candidates"][0]["source_message_uids"][0]},
            "before": 0, "after": 0}),
        ("notebook_archive", lambda script: {key: value for key, value in recover_from_visible(script).items() if key != "action"}),
        ("notebook_archive", lambda script: {
            "entry_id": recovered["candidate"]["entry_id"], "reason": "Recovered source successfully archived"}),
        _finish("Recovered from direct Message provenance and original proposal/approval/action"),
    ])
    try:
        finished = _run(runtime, second, db=reopened, anchor="resume-request")
        assert finished.committed, finished
        assert finished.child_session_id != interrupted.child_session_id
        assert not reopened.notebook_current(seeded.ref)["payload"]["work"]
        assert not reopened.notebook_current(seeded.ref)["payload"]["candidates"]
    finally:
        reopened.close()


def test_native_interruption_after_conversion_discards_draft_and_next_child_retries(runtime, monkeypatch):
    from secretary import noting_child

    seeded = _seed(runtime)
    original_builder = noting_child.build_noting_child
    children = []

    def capture(*args, **kwargs):
        child = original_builder(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(noting_child, "build_noting_child", capture)
    script = _ProviderScript([_convert(seeded.candidate, ["origin-a"])],
                             after_exhausted=lambda: children[-1].interrupt(hard_cancel=True))
    interrupted = _run(runtime, script)
    assert not interrupted.committed, interrupted
    assert script.results["s02-0"]["success"]
    assert _payload(runtime)["candidates"][0]["version_id"] == seeded.candidate["version_id"]
    assert _payload(runtime)["candidates"][0]["fields"]["notebook_refs"] == [seeded.sources[0]["entry_id"]]
    runtime.db.append_message("parent", "user", "Continue checking the existing successful write.",
                              message_uid="retry-anchor", timestamp=204)
    retry = _ProviderScript([
        _convert(seeded.candidate, ["origin-a"]),
        _archive(seeded.sources[0], "Confirmed unchanged source covered"),
        _archive(seeded.candidate, "Source was processed successfully"), _finish(),
    ])
    finished = _run(runtime, retry, anchor="retry-anchor")
    assert finished.committed, finished
    assert not _payload(runtime)["work"] and not _payload(runtime)["candidates"]
