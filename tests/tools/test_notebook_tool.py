"""notebook_show: explicit Main read eligibility, independent of local background Noting."""

import json
from datetime import datetime

import pytest

import tools.notebook_tool  # noqa: F401 -- import registers the tool
from secretary.notebook_store import NotebookStore
from tools.notebook_tool import notebook_show
from tools.registry import registry
from tests.hermes_state._secretary_notebook_harness import add, make, open_notebook_db, ref_of


@pytest.fixture
def db(tmp_path):
    db = open_notebook_db(tmp_path / "state.db")
    yield db
    db.close()


def test_registry_registration_and_schema_shape():
    entry = registry.get_entry("notebook_show")
    assert entry is not None
    assert entry.toolset == "notebook"
    assert entry.schema["name"] == "notebook_show"
    assert entry.schema["parameters"]["properties"] == {}
    assert "notebook_show" in registry.get_tool_names_for_toolset("notebook")


def test_show_returns_only_complete_notebook_content_and_commit_time(db):
    make(db, "s")
    add(db, "s", "remind me", "m1")
    ref = ref_of(db, "s")
    store = NotebookStore(db, ref)
    entry = store.create("user_reminder", {"message": "submit the report"})
    store.commit("m1")
    db.notebook_set_local_enabled(ref, False)

    audit_before = db.notebook_current(ref)
    result = json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=True))
    assert set(result) == {"success", "notebook"}
    assert result["success"] is True
    notebook = result["notebook"]
    assert set(notebook) == {"last_update_time", "anchor_message_uid", "user", "assistant", "consultation", "persistence"}
    assert notebook["user"] == [entry]
    assert datetime.fromisoformat(notebook["last_update_time"]).timestamp() == pytest.approx(audit_before["created_at"], rel=0, abs=1e-6)
    assert notebook["anchor_message_uid"] == "m1"
    assert datetime.fromisoformat(notebook["last_update_time"]).tzinfo is not None
    assert db.notebook_current(ref) == audit_before
    assert audit_before["anchor_message_uid"] == "m1"
    assert audit_before["message_identity"] == {"conversation_ref": ref, "message_uid": "m1"}


def test_show_gate_no_snapshot_and_argument_validation(db):
    make(db, "s")
    add(db, "s", "note", "m1")
    ref = ref_of(db, "s")
    assert json.loads(notebook_show({}, db=db, conversation_ref=ref))["success"] is False
    assert json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=True)) == {
        "success": True, "notebook": None}

    db.notebook_set_local_enabled(ref, False)
    assert json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=True)) == {
        "success": True, "notebook": None}
    assert json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=False))["success"] is False

    db.notebook_set_local_enabled(ref, True)
    assert json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=False))["success"] is False
    assert json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=True))["notebook"] is None
    assert json.loads(notebook_show({}, db=db, conversation_ref=None, effective_enabled=True))["success"] is False
    assert json.loads(notebook_show({}, db=None, conversation_ref=ref, effective_enabled=True))["success"] is False
    assert json.loads(notebook_show({"conversation": "other"}, db=db, conversation_ref=ref, effective_enabled=True))["success"] is False
