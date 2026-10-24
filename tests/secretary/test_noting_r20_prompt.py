"""R20 default Task through Main, real SDK serialization, child Loop and SQLite.

SDK responses prescribe tool choices; this verifies delivery and execution, not
whether a natural model follows the new guidance.
"""

from copy import deepcopy
from datetime import datetime, timezone
import json

from secretary.notebook_store import NotebookStore
from secretary.noting_child import NOTING_ALLOWED_TOOL_NAMES, spawn_noting_task
from secretary.noting_prompts import (
    CURRENT_NOTING_CONTROL,
    DEFAULT_NOTING_TASK_INSTRUCTION,
    NOTING_CONTINUATION_INSTRUCTION,
)
from secretary.noting_runtime import NotingAdmission
from tests.secretary.test_fixed_noting_permissions import (
    call,
    result_entry,
    runtime as runtime,
)
from tests.secretary import test_noting_surface as surface


SOURCE_GUIDANCE = (
    "Keep sources supporting retained content and add sources for new or changed claims; "
    "do not replace all sources with only the newest message."
)
IN_PLACE_GUIDANCE = (
    "When new evidence only resolves or corrects the same situation, update it in place "
    "rather than archiving and recreating it."
)
R16_GUIDANCE = (
    "For the same piece of evidence, Message IDs or one element of source_time_ranges is usually "
    "sufficient; there is no need to repeat it in both forms. Different pieces of evidence may "
    "mix Message IDs and source_time_ranges. The Candidate source restrictions below still apply."
)
OLD_FACTS = (
    "Workshop Alpha has ended: 40 people attended in Room Cedar; its seating capacity was unknown. "
    "The temporary access-code issue is obsolete, with no remaining responsibility or retention value."
)
NEW_FACTS = (
    "The same Workshop Alpha venue is now confirmed to have 40 seats. "
    "A different event, Workshop Beta, will take place in Room Maple."
)
OLD_DESCRIPTION = "Workshop Alpha ended with 40 people in Room Cedar; capacity was unknown."
NEW_DESCRIPTION = "Workshop Alpha ended with 40 people in Room Cedar; its capacity is confirmed as 40 seats."


def latest_user(db, session_id):
    return next(row for row in reversed(db.get_messages(session_id)) if row["role"] == "user")


def assert_delivered_task(wires, parent_request):
    """Inspect actual serialized requests, including the next native Turn."""
    prefix = [*parent_request["messages"], {"role": "assistant", "content": "done"}]
    for wire in wires:
        assert wire["tools"] == parent_request["tools"]
        assert set(NOTING_ALLOWED_TOOL_NAMES) <= surface._names(wire["tools"])
        assert wire["messages"][:len(prefix)] == prefix
        assert all("tools" not in message for message in wire["messages"])
        tasks = [message["content"] for message in wire["messages"]
                 if message["role"] == "user" and DEFAULT_NOTING_TASK_INSTRUCTION in message.get("content", "")]
        assert len(tasks) == 1
        task = tasks[0]
        step2 = task.split("2. Update existing entries.", 1)[1].split("3. Create useful missing entries.", 1)[0]
        shared = task.split("TOOL USE\n", 1)[1].split(CURRENT_NOTING_CONTROL, 1)[0]
        assert "keep its stable entry_id. " + IN_PLACE_GUIDANCE in step2
        assert R16_GUIDANCE in step2 and SOURCE_GUIDANCE not in step2
        assert "Supply create/update attributes directly as tool parameters, without action or changes wrappers. " + SOURCE_GUIDANCE in shared
        assert task.count(SOURCE_GUIDANCE) == task.count(IN_PLACE_GUIDANCE) == 1
        assert CURRENT_NOTING_CONTROL in task
        assert "callable_tool_schemas" not in task and '"parameters"' not in task
    continuations = [message["content"] for message in wires[-1]["messages"]
                     if message["role"] == "user" and NOTING_CONTINUATION_INSTRUCTION in message.get("content", "")]
    assert len(continuations) == 1 and CURRENT_NOTING_CONTROL in continuations[0]


def test_default_task_initial_and_continuation_keep_same_situation_and_sources(runtime, monkeypatch):
    parent, db, _config, state = runtime
    surface._turn(parent, OLD_FACTS)
    ref = parent._secretary_conversation_ref
    old_user = latest_user(db, parent.session_id)
    store = NotebookStore(db, ref, anchor_message_uid=parent._session_messages[-1]["message_uid"])
    situation = store.create("situation", {"description": OLD_DESCRIPTION, "subjects": ["Workshop Alpha"]},
                             done=True, source_message_uids=[old_user["message_uid"]])["entry"]
    obsolete = store.create("situation", {"description": "Obsolete temporary access-code issue.",
                            "subjects": ["temporary access code"]}, done=True,
                            source_message_uids=[old_user["message_uid"]])["entry"]
    old_commit = store.commit(termination={"type": "finish_noting", "reason": "Prior supported situation"})
    old_snapshot = dict(db._read_one("SELECT * FROM secretary_notebook_snapshots WHERE snapshot_id=?",
                                   (old_commit["snapshot_id"],)))

    surface._turn(parent, NEW_FACTS)
    new_user = latest_user(db, parent.session_id)
    instant = datetime.fromtimestamp(new_user["timestamp"], timezone.utc).isoformat()
    new_range = {"start_time": instant, "end_time": instant}
    parent_request = deepcopy(state["sent"][-1])
    anchor = parent._session_messages[-1]["message_uid"]
    state["sent"].clear()
    state["script"] = [
        [call("conversation_history", {"mode": "read", "limit": 3}, "read-evidence")],
        [call("notebook_show", {}, "show-existing")],
        [call("notebook_update", {"entry_id": situation["entry_id"],
               "fields": {"description": NEW_DESCRIPTION},
               "source_message_uids": [old_user["message_uid"]], "source_time_ranges": [new_range]}, "same-situation")],
        None,  # A text final is not Finish: keep the complete Task for the next Turn.
        [call("notebook_create", {"entry_type": "situation", "fields": {
            "description": "Workshop Beta will take place in Room Maple.", "subjects": ["Workshop Beta"]},
            "source_message_uids": [new_user["message_uid"]]}, "different-event")],
        [call("notebook_archive", {"entry_id": obsolete["entry_id"],
               "reason": "The temporary issue is obsolete and has no remaining value."}, "obsolete")],
        [call("finish_noting", {"reason": "Corrected Alpha in place, indexed Beta and removed the obsolete issue."}, "finish")],
    ]
    children = []
    from secretary import noting_child
    original = noting_child.build_noting_child

    def capture(*args, **kwargs):
        child = original(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(noting_child, "build_noting_child", capture)
    admission_id = db.noting_admit(ref, anchor, kind="manual")
    admission = NotingAdmission(admission_id, ref, anchor, "manual", None, "NOTING")
    worker = spawn_noting_task(parent, admission)  # Exercise the real default selection.
    worker.join(timeout=30)
    assert not worker.is_alive()
    registration = db.noting_child(admission_id)
    assert registration["status"] == "completed", registration
    assert len(children) == 1 and children[0].tools == parent.tools
    assert children[0].valid_tool_names == set(NOTING_ALLOWED_TOOL_NAMES)
    wires = state["sent"]
    assert len(wires) == 7
    assert_delivered_task(wires, parent_request)

    snapshot = db.notebook_current(ref)
    assert snapshot["snapshot_id"] != old_commit["snapshot_id"]
    entries = {entry["entry_id"]: entry for section in snapshot["payload"].values() for entry in section}
    assert len(entries) == 2 and obsolete["entry_id"] not in entries
    updated = entries[situation["entry_id"]]
    assert updated["version_id"] != situation["version_id"]
    assert updated["fields"]["description"] == NEW_DESCRIPTION
    assert updated["fields"]["subjects"] == situation["fields"]["subjects"]
    assert updated["done"] is True  # Update omitted done: preserve the known terminal state.
    assert updated["source_message_identities"] == [{"conversation_ref": ref, "message_uid": old_user["message_uid"]}]
    assert updated["source_time_ranges"] == [new_range]
    beta = result_entry(wires[-1], "different-event")
    assert beta["entry_id"] not in {situation["entry_id"], obsolete["entry_id"]}
    assert entries[beta["entry_id"]]["done"] is False
    assert beta["source_message_uids"] == [new_user["message_uid"]]
    assert dict(db._read_one("SELECT * FROM secretary_notebook_snapshots WHERE snapshot_id=?",
                            (old_commit["snapshot_id"],))) == old_snapshot
    rows = db.get_messages_as_conversation(children[0].session_id)
    results = {row["tool_call_id"]: json.loads(row["content"]) for row in rows if row["role"] == "tool"}
    assert len(results) == 6 and all(result["success"] for result in results.values())
    assert results["same-situation"]["entry"]["entry_id"] == situation["entry_id"]
    assert results["finish"] == {"success": True, "status": "end_requested"}
    assert not state["script"]
