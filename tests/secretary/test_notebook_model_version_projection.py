"""Model outputs hide item versions while storage and human audit retain them."""

from copy import deepcopy
import json
from types import SimpleNamespace

import pytest

from hermes_state import SessionDB
from secretary.notebook_contract import NotebookValidationError
from secretary.notebook_render import model_notebook_data, render_notebook, show_notebook
from secretary.noting_tools import (
    initialize_notebook_work, notebook_archive, notebook_create, notebook_update, notebook_work_show,
)


@pytest.fixture
def child(tmp_path, monkeypatch):
    db = SessionDB(tmp_path / "state.db")
    db.create_session("parent", source="test")
    db.append_message("parent", "user", "A visit and a related follow-up", message_uid="evidence", timestamp=100)
    monkeypatch.setattr("secretary.noting_runtime.noting_trigger_gate", lambda *a, **k: (True, ""))
    agent = SimpleNamespace(
        _session_db=db, _secretary_parent_conversation_ref=db.resolve_conversation_ref("parent"),
        _secretary_noting_anchor_uid="evidence", _secretary_noting_profile="NOTING",
        _secretary_noting_child=True, _secretary_noting_terminal_action_done=False,
    )
    initialize_notebook_work(agent, trigger_type="manual")
    yield agent
    db.close()


def create(child, description="Visit", **options):
    return json.loads(notebook_create(child, {
        "entry_type": "matter", "fields": {"description": description, "completion_condition": "Visit complete"},
        "source_message_uids": ["evidence"], **options,
    }))["entry"]


def test_create_update_archive_outputs_keep_stable_ids_and_internal_versions(child):
    target = create(child)
    store = child._noting_notebook_store
    original = store.get(target["entry_id"])
    assert "version_id" not in target and original["version_id"]
    updated = json.loads(notebook_update(child, {
        "entry_id": target["entry_id"], "fields": {"description": "Visit completed"}, "done": True,
    }))["entry"]
    current = store.get(target["entry_id"])
    assert updated["entry_id"] == target["entry_id"] and "version_id" not in updated
    assert current["version_id"] != original["version_id"] and updated["done"] is True
    related = create(child, "Follow-up", relations=[{"kind": "related_to", "entry_id": target["entry_id"]}])
    related_before = store.get(related["entry_id"])
    archived = json.loads(notebook_archive(child, {"entry_id": target["entry_id"], "reason": "Settled"}))
    assert archived["success"] and archived["entry_id"] == target["entry_id"]
    assert archived["relations_removed_from"] == [related["entry_id"]]
    affected = archived["updated_entries"][0]
    assert affected["entry_id"] == related["entry_id"] and affected["relations"] == []
    assert "version_id" not in affected
    assert store.get(related["entry_id"])["version_id"] != related_before["version_id"]
    internal = store.snapshot_state()
    assert next(entry for entry in internal["work"] if entry["entry_id"] == target["entry_id"])["archived"]
    receipt = store.commit(termination={"type": "finish_noting", "reason": "Checked versions"})
    snapshot = child._session_db.notebook_current(store.conversation_ref)
    audit = child._session_db.notebook_snapshot_audit(receipt["snapshot_id"])
    assert audit["payload"]["work"][0]["version_id"]
    assert show_notebook(snapshot, db=child._session_db)["payload"]["work"][0]["version_id"]
    assert "version_id:" in render_notebook(snapshot, db=child._session_db)
    assert "version_id:" not in render_notebook(snapshot, db=child._session_db, model_visible=True)
    shown = json.loads(notebook_work_show(child, {}))["payload"]["work"]
    assert [entry["entry_id"] for entry in shown] == [related["entry_id"]]
    assert all("version_id" not in entry for entry in shown)


def test_archive_refusal_hides_versions_in_actual_error_details(child):
    source = create(child)
    candidate = json.loads(notebook_create(child, {
        "entry_type": "candidate", "fields": {
            "description": "Useful lesson", "targets": ["memory"],
            "notebook_refs": [source["entry_id"]], "source_types": ["matter"],
        },
    }))["entry"]
    store = child._noting_notebook_store
    before = store.snapshot_state()
    result = json.loads(notebook_archive(child, {"entry_id": source["entry_id"], "reason": "Too early"}))
    assert result["error"]["code"] == "invalid_reference"
    assert result["error"]["details"]["referrers"] == [{
        "entry_id": candidate["entry_id"], "fields": ["fields.notebook_refs[0]"],
    }]
    assert store.snapshot_state() == before
    assert store.get(candidate["entry_id"])["version_id"]


def test_nested_error_entries_are_projected_without_rewriting_body_fields(child, monkeypatch):
    entry = create(child)
    details = {"affected_entries": [{
        "entry_id": entry["entry_id"], "version_id": "internal-version",
        "fields": {"description": "Literal version_id", "version_id": "user-content",
                   "nested": {"entry_id": "quoted", "version_id": "quoted-version"}},
    }]}
    before = deepcopy(details)
    def refuse(*args, **kwargs):
        raise NotebookValidationError("Inspect affected entries", details=details)
    monkeypatch.setattr(child._noting_notebook_store, "update", refuse)
    result = json.loads(notebook_update(child, {"entry_id": entry["entry_id"], "done": True}))
    projected = result["error"]["details"]["affected_entries"][0]
    assert projected["entry_id"] == entry["entry_id"] and "version_id" not in projected
    assert projected["fields"] == before["affected_entries"][0]["fields"]
    assert details == before
    assert model_notebook_data(result) == result
