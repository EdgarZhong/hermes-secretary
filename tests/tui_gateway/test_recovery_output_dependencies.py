"""Active native tool recovery retains its real owner, not persisted text."""
from __future__ import annotations

import json

import pytest

from agent.context_compressor import _DB_PERSISTED_MARKER
from agent.pending_steer import native_source_message
from tests.tui_gateway.test_recovery_view import activate, begin, native_output, request
from tui_gateway import server

pytest_plugins = ["tests.tui_gateway.test_recovery_view"]


def source_row(row):
    message = {**row, "_row_id": row["id"], _DB_PERSISTED_MARKER: True}
    message["_tool_call_uids"] = json.loads(row.get("tool_call_uids") or "{}")
    message["_tool_call_uid"] = row.get("tool_call_uid")
    return native_source_message(message)


def parent(db, *, calls=1):
    ids = ["provider-call", *[f"provider-{index}" for index in range(1, calls)]]
    db.append_messages_batch("stored", [{
        "role": "assistant", "content": "durable parent body", "message_uid": "output-uid",
        "tool_calls": [{"id": provider_id, "function": {"name": "terminal", "arguments": "{}"}}
                       for provider_id in ids],
        "_tool_call_uids": {provider_id: f"occurrence-{index}" for index, provider_id in enumerate(ids)},
    }])
    return source_row(db.get_messages("stored")[-1])


def committed(source, **changes):
    server._emit("message.output_committed", "runtime", {
        "turn_id": "native-turn", "stored_session_id": "stored", "conversation_ref": "controlled",
        "source_message": source, **changes,
    })


def output(session):
    native_output(session, tool_uid="occurrence-0")


def events(db):
    view = activate(request(db))
    assert view["complete"], view
    return view["state_snapshot"]["events"]


def test_active_durable_parent_retains_original_owner_and_call_identity(native):
    db, session, _home = native
    begin(db, session)
    source = parent(db)
    output(session)
    committed(source)
    original = session["_inflight_output"]["events"]
    recovered = events(db)
    assert any(event["type"] == "tool.output" for event in recovered)
    assert [event for event in recovered if event["type"] in {"message.output_state", "message.output_committed"}] == [
        event for event in original if event["type"] in {"message.output_state", "message.output_committed"}]
    assert not any(event["type"] in {"message.delta", "message.output_delta"} for event in recovered)
    assert [event["seq"] for event in recovered] == sorted(event["seq"] for event in recovered)


def test_closed_native_owner_is_retained_for_its_unfinished_tool(native):
    db, session, _home = native
    begin(db, session)
    parent(db)
    output(session)
    owner = next(event["payload"] for event in session["_inflight_output"]["events"]
                 if event["type"] == "message.output_state")
    server._emit("message.output_state", "runtime", {**owner, "state": "closed"})
    assert [event["payload"]["state"] for event in events(db)
            if event["type"] == "message.output_state"] == ["open", "closed"]


@pytest.mark.parametrize("field,value", [("conversation_ref", "foreign"), ("message_uid", "other-uid")])
def test_dependency_does_not_borrow_a_different_owner(native, field, value):
    db, session, _home = native
    begin(db, session)
    parent(db)
    output(session)
    owner = next(event for event in session["_inflight_output"]["events"] if event["type"] == "message.output_state")
    owner["payload"][field] = value
    # Unknown UIDs follow the existing live path; closure must not infer an owner
    # for the persisted parent from either a different UID or Conversation.
    recovered = events(db)
    assert not any(event["type"] == "message.output_state" and event["payload"].get("message_uid") == "output-uid"
                   and event["payload"].get("conversation_ref") == "controlled" for event in recovered)


@pytest.mark.parametrize("damage", ["row", "occurrence", "call_id", "scope"])
def test_dependency_does_not_retain_a_contradictory_commit(native, damage):
    db, session, _home = native
    begin(db, session)
    source = parent(db)
    output(session)
    changes = {}
    if damage == "row":
        source["row_id"] += 100
    elif damage == "occurrence":
        source["tool_calls"][0]["tool_call_uid"] = "foreign-occurrence"
    elif damage == "call_id":
        source["tool_calls"][0]["id"] = "foreign-provider-id"
    else:
        changes["conversation_ref"] = "foreign"
    committed(source, **changes)
    assert not any(event["type"] == "message.output_committed" for event in events(db))


def test_completed_tool_and_unrelated_durable_owner_retire(native):
    db, session, _home = native
    begin(db, session)
    source = parent(db)
    output(session)
    committed(source)
    db.append_messages_batch("stored", [{"role": "tool", "content": "done", "tool_call_id": "provider-call",
                                         "_tool_call_uid": "occurrence-0"}])
    recovered = events(db)
    assert not any(event["type"] in {"message.output_state", "message.output_committed", "tool.start", "tool.output"}
                   for event in recovered)


def test_mixed_call_list_retains_only_real_completed_sibling_identity(native):
    db, session, _home = native
    begin(db, session)
    source = parent(db, calls=2)
    output(session)
    committed(source)
    db.append_messages_batch("stored", [{"role": "tool", "content": "done", "tool_call_id": "provider-1",
                                         "_tool_call_uid": "occurrence-1"}])
    result = source_row(db.get_messages("stored")[-1])
    committed(result)
    recovered = events(db)
    assert [event["payload"]["source_message"] for event in recovered
            if event["type"] == "message.output_committed"] == [source, result]
    assert not any(event["type"] == "tool.complete" for event in recovered)


def test_rewound_parent_does_not_reappear_as_a_live_dependency(native):
    db, session, _home = native
    begin(db, session)
    source = parent(db)
    output(session)
    committed(source)
    db.rewind_to_message("stored", db.get_messages("stored")[0]["id"])
    view = activate(request(db))
    assert not view["complete"] and view["reason"] in {"runtime_unavailable", "view_changed"}


@pytest.mark.parametrize("damage", ["turn_id", "stored_session_id", "source_proof"])
def test_active_dependency_keeps_existing_turn_and_source_refusal(native, damage):
    db, session, _home = native
    begin(db, session)
    parent(db)
    output(session)
    original = session["_inflight_output"]["events"]
    if damage == "source_proof":
        original[:] = [event for event in original if event["type"] != "message.source_committed"]
    else:
        typed = next(event for event in original if event["type"] == "tool.output")
        typed["payload"][damage] = "foreign"
    view = activate(request(db))
    assert not view["complete"] and view["reason"] in {"runtime_unavailable", "view_changed"}


def test_dependency_cannot_repair_a_mismatched_legacy_pair(native):
    db, session, _home = native
    begin(db, session)
    parent(db)
    output(session)
    typed = next(event for event in session["_inflight_output"]["events"] if event["type"] == "tool.output")
    typed["payload"]["native_payload"] = {"tool_id": "different"}
    assert not any(event["type"] == "message.output_state" for event in events(db))
