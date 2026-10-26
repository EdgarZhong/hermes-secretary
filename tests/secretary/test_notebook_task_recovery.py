"""Native failed-child recovery preserves Task provenance ownership without model versions."""
from copy import deepcopy
import json

import pytest

from secretary.notebook_store import NotebookStore
from secretary.noting_recovery import start_recovery
from secretary.noting_recovery_sources import NotingRecoveryError, reconstruct_noting
from tests.secretary.test_noting_recovery import factory, wait_recovery
from tests.secretary.test_r3_child import (
    database as database, enabled_runtime as enabled_runtime, native_parent as native_parent,
    create_args, ref, response, run_task, tool_response,
)

FINISH = {"type": "finish_noting", "reason": "Seeded existing Notebook"}


def fail_before_commit(_child):
    raise RuntimeError("Controlled failure before publication")


def seed_and_fail(native_parent, database):
    parent, client = native_parent
    seed = NotebookStore(database, ref(database), anchor_message_uid="m1", task_id="seed-task")
    entry = seed.create(**create_args(database))["entry"]
    seed.commit(termination=FINISH)
    client.chat.completions.create.side_effect = [
        tool_response("notebook_update", {"entry_id": entry["entry_id"],
            "fields": {"description": "Dates are being checked"}, "source_message_uids": ["m2"]}, "edit"),
        tool_response("finish_noting", {"reason": "Checked current work"}), response("Done"),
    ]
    failed = run_task(parent, state_provider=fail_before_commit)
    assert not failed.committed and failed.status == "failed"
    return entry, failed


def test_nonempty_initial_and_successful_receipt_restore_task_owner_then_resume_same_slot(native_parent, database):
    parent, client = native_parent
    entry, failed = seed_and_fail(native_parent, database)
    recovered = reconstruct_noting(database, ref(database), failed.child_session_id)
    saved = recovered.working_state["work"][0]
    assert saved["provenance"] == [["m1"], ["m2"]]
    assert saved["provenance_tasks"] == ["seed-task", str(recovered.admission["admission_id"])]
    original = deepcopy(saved)
    client.chat.completions.create.reset_mock()
    client.chat.completions.create.side_effect = [
        tool_response("notebook_update", {"entry_id": entry["entry_id"], "done": True,
                                         "source_message_uids": ["m1", "m2"]}, "resume-edit"),
        tool_response("finish_noting", {"reason": "Recovered task finished"}), response("Done"),
    ]
    start_recovery(database, ref(database), failed.child_session_id, "resume", parent_factory=factory(parent))
    result = wait_recovery(database, failed, "resume")
    assert result["committed"], result
    state = database.notebook_snapshot_audit(result["snapshot_id"])["payload"]["work"][0]
    assert state["provenance"] == [["m1"], ["m1", "m2"]]
    assert state["provenance_tasks"] == original["provenance_tasks"]
    assert state["write_task_id"] == str(recovered.admission["admission_id"])
    next_task = NotebookStore(database, ref(database), anchor_message_uid="m2", task_id="next-admission")
    next_item = next_task.update(entry["entry_id"], {"done": False, "source_message_uids": ["m1"]})["entry"]
    assert next_item["provenance"] == [["m1"], ["m1", "m2"], ["m1"]]


def test_ambiguous_receipt_refuses_without_replaying_or_writing(native_parent, database):
    from secretary.notebook_items import insert_item_conn
    _entry, failed = seed_and_fail(native_parent, database)
    recovered = reconstruct_noting(database, ref(database), failed.child_session_id)
    item = recovered.working_state["work"][0]
    database._execute_write(lambda conn: insert_item_conn(conn, ref(database), item, item["version_id"]))
    before = [tuple(row) for row in database._read_all("SELECT * FROM secretary_notebook_item ORDER BY id")]
    with pytest.raises(NotingRecoveryError, match="ambiguous"):
        reconstruct_noting(database, ref(database), failed.child_session_id)
    assert [tuple(row) for row in database._read_all("SELECT * FROM secretary_notebook_item ORDER BY id")] == before


def test_receipt_cannot_borrow_another_task_owner(native_parent, database):
    _entry, failed = seed_and_fail(native_parent, database)
    child_rows = database.get_messages(failed.child_session_id)
    receipt = next(row for row in child_rows if row["role"] == "tool" and json.loads(row["content"]).get("entry"))
    body = json.loads(receipt["content"])
    body["entry"]["fields"]["description"] = "Receipt content that no owned version contains"
    database._execute_write(lambda conn: conn.execute("UPDATE messages SET content=? WHERE id=?", (json.dumps(body), receipt["id"])))
    before = [tuple(row) for row in database._read_all("SELECT * FROM secretary_notebook_item ORDER BY id")]
    with pytest.raises(NotingRecoveryError, match="Missing or ambiguous"):
        reconstruct_noting(database, ref(database), failed.child_session_id)
    assert [tuple(row) for row in database._read_all("SELECT * FROM secretary_notebook_item ORDER BY id")] == before


def test_native_recovery_after_current_task_candidate_switch_can_replace_same_slot(native_parent, database):
    parent, client = native_parent
    seed = NotebookStore(database, ref(database), anchor_message_uid="m1", task_id="seed")
    source = seed.create(**create_args(database))["entry"]
    seed.commit(termination=FINISH)
    seen = {}

    def provider(**wire):
        calls = client.chat.completions.create.call_count
        if calls == 1:
            return tool_response("notebook_create", {"entry_type": "candidate", "fields": {
                "description": "Retain visit outcome", "targets": ["memory"], "notebook_refs": [], "source_types": []},
                "source_message_uids": ["m1"]}, "direct-create")
        if calls == 2:
            receipt = next(json.loads(row["content"]) for row in wire["messages"] if row.get("tool_call_id") == "direct-create")
            seen["entry_id"] = receipt["entry"]["entry_id"]
            return tool_response("notebook_update", {"entry_id": seen["entry_id"],
                "fields": {"notebook_refs": [source["entry_id"]], "source_types": ["matter"]},
                "source_message_uids": []}, "to-refs")
        return tool_response("finish_noting", {"reason": "Current slot switched to source refs"})

    client.chat.completions.create.side_effect = provider
    failed = run_task(parent, state_provider=fail_before_commit)
    assert not failed.committed
    recovered = reconstruct_noting(database, ref(database), failed.child_session_id)
    candidate = recovered.working_state["candidates"][0]
    assert candidate["provenance"] == candidate["provenance_tasks"] == candidate["evidence_time"] == []
    owner = str(recovered.admission["admission_id"])
    assert candidate["write_task_id"] == owner
    client.chat.completions.create.reset_mock()
    client.chat.completions.create.side_effect = [
        tool_response("notebook_update", {"entry_id": seen["entry_id"], "fields": {"notebook_refs": [], "source_types": []},
                                         "source_message_uids": ["m2"]}, "back-direct"),
        tool_response("finish_noting", {"reason": "Replaced the same Task source slot"}),
    ]
    start_recovery(database, ref(database), failed.child_session_id, "switch", parent_factory=factory(parent))
    outcome = wait_recovery(database, failed, "switch")
    assert outcome["committed"], outcome
    committed = database.notebook_snapshot_audit(outcome["snapshot_id"])["payload"]["candidates"][0]
    assert committed["provenance"] == [["m2"]] and committed["provenance_tasks"] == [owner]
