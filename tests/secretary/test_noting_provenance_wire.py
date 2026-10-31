"""Current provenance contracts across real SDK, Main restore and frozen Noting paths."""

import copy
import json

import pytest

from secretary.noting_child import freeze_parent_runtime, run_noting_task
from secretary.noting_prompts import DEFAULT_NOTING_TASK_INSTRUCTION
from secretary.noting_surface import apply_main_read_surface
from secretary.noting_tools import noting_tool_schemas
from tests.secretary.test_fixed_noting_permissions import (
    call, result_entry, runtime as runtime,
)


def _canonical():
    return {schema["name"]: {"type": "function", "function": schema} for schema in noting_tool_schemas()}


def _legacy(tools):
    legacy = copy.deepcopy(tools)
    for tool in legacy:
        function = tool["function"]
        if function["name"] in _canonical():
            function["description"] = "Historical definition of " + function["name"]
        if function["name"] in {"notebook_create", "notebook_update"}:
            properties = function["parameters"]["properties"]
            properties.pop("done", None)
            properties["status"] = {"type": "string"}
            properties.pop("source_time_ranges", None)
            properties["source_time_range"] = {"type": "object"}
    return legacy


def _run(parent, **options):
    db, ref = parent._session_db, parent._secretary_conversation_ref
    anchor = parent._session_messages[-1]["message_uid"]
    admission = db.noting_admit(ref, anchor, kind="manual")
    return run_noting_task(parent, admission_id=admission, conversation_ref=ref,
                          anchor_message_uid=anchor, trigger_type="manual", runtime_profile="NOTING",
                          task_instruction=DEFAULT_NOTING_TASK_INSTRUCTION, **options)


def _assert_current(tools):
    by_name = {tool["function"]["name"]: tool for tool in tools}
    assert set(_canonical()) == {"conversation_history", "notebook_show", "notebook_create",
                                 "notebook_update", "notebook_archive", "finish_noting"}
    for name, canonical in _canonical().items():
        assert by_name[name] == canonical
    for name in ("notebook_create", "notebook_update"):
        properties = by_name[name]["function"]["parameters"]["properties"]
        assert properties["done"]["type"] == "boolean" and "status" not in properties
        assert "source_time_ranges" not in properties
        assert "source_message_uids" in properties and "source_time_range" not in properties


@pytest.mark.parametrize("kind", ["matter", "candidate"])
@pytest.mark.parametrize("done", [False, True], ids=["still-unsettled", "confirmed-cancelled"])
def test_sdk_task_uid_sources_survive_create_update_receipts_snapshot_and_framework(runtime, kind, done):
    parent, db, _config, state = runtime
    if done:
        from tests.secretary import test_noting_surface as surface
        surface._turn(parent, "The report was cancelled. Withdraw its retention proposal; no outside write occurred.")
    prefix, root = copy.deepcopy(parent._session_messages), parent._cached_system_prompt
    parent_wire = copy.deepcopy(state["sent"][-1])
    tools = copy.deepcopy(state["sent"][-1]["tools"])
    _assert_current(tools)
    uid = next(row["message_uid"] for row in reversed(prefix) if row["role"] == "user")
    timestamp = next(row["timestamp"] for row in db.get_messages(parent.session_id) if row["message_uid"] == uid)
    provenance = {"source_message_uids": [uid], "source_description": "The user stated the report responsibility or its cancellation."}
    fields = ({"description": "send report", "completion_condition": "Report sent"} if kind == "matter" else
              {"description": "Retain the report commitment", "targets": ["memory"], "notebook_refs": [], "source_types": []})
    changed_fields = {"blocker": "Awaiting review"} if kind == "matter" else {"description": "Report commitment still awaits review"}
    if done:
        changed_fields = {"description": "Report cancelled; its retention proposal was withdrawn without an outside write."}
    section = "work" if kind == "matter" else "candidates"
    state["sent"].clear()
    state["script"] = [
        [call("notebook_create", {"entry_type": kind, "fields": fields, **provenance}, "create")],
        lambda payload: [call("notebook_update", {"entry_id": result_entry(payload, "create")["entry_id"],
            "fields": changed_fields, "done": done, **provenance}, "update")],
        [call("notebook_show", {}, "show")],
        [call("finish_noting", {"reason": "Indexed the report with its sources."}, "finish")],
    ]
    outcome = _run(parent)
    assert outcome.committed and len(state["sent"]) == 4, outcome
    from tests.secretary.test_joint_noting_notes_u20 import compact
    from secretary.noting_notes import check_note_delivery
    compact(parent, db, "description-wire-boundary")
    assert check_note_delivery(parent)
    for wire in state["sent"]:
        assert wire["tools"] == tools
        assert wire["messages"][0] == {"role": "system", "content": root}
        assert all("tools" not in row for row in wire["messages"])
        assert "callable_tool_schemas" not in str(wire["messages"])
    expected_prefix = [*parent_wire["messages"], {"role": "assistant", "content": "done"}]
    assert all(wire["messages"][:len(expected_prefix)] == expected_prefix for wire in state["sent"])
    task = state["sent"][0]["messages"][len(expected_prefix)]["content"]
    assert "Select only the exact Message UIDs needed to support the recorded changes" in task
    assert "Every Candidate uses exactly one source form" in task
    assert "Later edits overwrite the supplied attribute values and this same evidence group, preserving earlier tasks’ provenance nodes" in task
    assert "When the available evidence does not establish an action's progress, leave it unknown; done=false does not mean the work has not started." in task
    rows = db.get_messages_as_conversation(outcome.child_session_id)
    results = {row["tool_call_id"]: json.loads(row["content"]) for row in rows if row["role"] == "tool"}
    assert all(result["success"] for result in results.values())
    for name in ("create", "update"):
        entry = results[name]["entry"]
        assert len(entry["evidence_time"]) == 1
        assert entry["provenance"] == [[uid]]
        assert entry["provenance_descriptions"] == [provenance["source_description"]]
        assert entry["done"] is (done if name == "update" else False) and "status" not in entry
    assert results["show"]["payload"][section][0]["evidence_time"] == results["update"]["entry"]["evidence_time"]
    entry = db.notebook_current(parent._secretary_conversation_ref)["payload"][section][0]
    assert entry["provenance"] == [[uid]]
    assert entry["done"] is done and "status" not in entry
    if done:
        assert entry["fields"]["description"] == changed_fields["description"]
        assert "[done=true]" in parent._session_messages[-1]["content"]
        assert changed_fields["description"] in parent._session_messages[-1]["content"]
    from hermes_time import format_timestamp
    assert format_timestamp(timestamp, profile_home=db.db_path.parent) in parent._session_messages[-1]["content"]


@pytest.mark.parametrize("restored", [False, True], ids=["main-boundary", "same-code-pinned-restore"])
def test_main_refreshes_same_name_contracts_and_repins_without_rebuilding_root(runtime, monkeypatch, restored):
    from tools.mcp_tool_agent import tool_pin_version
    parent, db, _config, state = runtime
    current = copy.deepcopy(parent.tools)
    legacy = _legacy(current)
    old = copy.deepcopy(legacy)
    parent.tools = legacy
    root = parent._cached_system_prompt
    db.update_session_tool_names(parent.session_id, {"version": tool_pin_version(), "tools": legacy})
    db.update_system_prompt(parent.session_id, root)
    if restored:
        parent.tools = current
        parent._cached_system_prompt = None
    observed = []
    monkeypatch.setattr("hermes_cli.observability.shared_metrics_efficiency.record_cache_break",
                        lambda agent, cause: observed.append((agent, cause)))
    state["sent"].clear()
    result = parent.run_conversation("Continue the report.",
        conversation_history=copy.deepcopy(parent._session_messages), title_user_message="")
    assert result["completed"], result
    _assert_current(state["sent"][0]["tools"])
    assert parent.tools == current
    assert parent._cached_system_prompt == db.get_session(parent.session_id)["system_prompt"] == root
    assert json.loads(db.get_session(parent.session_id)["tool_names"])["tools"] == current
    assert observed == [(parent, "toolset_change")]
    assert legacy == old
    unchanged = [tool for tool in current if tool["function"]["name"] not in _canonical()]
    assert [tool for tool in parent.tools if tool["function"]["name"] not in _canonical()] == unchanged


def test_already_frozen_child_keeps_historical_tools_after_main_refresh(runtime):
    parent, db, _config, state = runtime
    current = copy.deepcopy(parent.tools)
    parent.tools = _legacy(current)
    historical = copy.deepcopy(parent.tools)
    frozen = freeze_parent_runtime(parent)
    assert apply_main_read_surface(parent)
    assert parent.tools == current
    state["sent"].clear()
    state["script"] = [[call("notebook_show", {}, "show")],
                       [call("finish_noting", {"reason": "Reviewed the frozen work."}, "finish")]]
    outcome = _run(parent, frozen_runtime=frozen)
    assert outcome.committed and len(state["sent"]) == 2, outcome
    assert all(wire["tools"] == historical for wire in state["sent"])
    assert parent.tools == current and frozen["parity"].tools == historical
    assert json.loads(db.get_session(outcome.child_session_id)["tool_names"])["tools"] == historical
