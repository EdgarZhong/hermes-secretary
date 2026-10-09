"""notebook_show: explicit Main read eligibility, independent of local background Noting."""

import json

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


def test_show_returns_complete_ai_facing_snapshot(db):
    make(db, "s")
    add(db, "s", "remind me", "m1")
    ref = ref_of(db, "s")
    store = NotebookStore(db, ref)
    entry = store.create("user_reminder", {"message": "submit the report"})
    store.commit("m1")
    db.notebook_set_local_enabled(ref, False)

    result = json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=True))
    assert result["success"] is True
    snapshot = result["snapshot"]
    assert snapshot["payload"]["user"] == [entry]
    assert snapshot["anchor_message_uid"] == "m1"
    assert snapshot["message_identity"] == {"conversation_ref": ref, "message_uid": "m1"}
    assert isinstance(snapshot["created_at"], float)


def test_show_gate_no_snapshot_and_argument_validation(db):
    make(db, "s")
    add(db, "s", "note", "m1")
    ref = ref_of(db, "s")
    assert json.loads(notebook_show({}, db=db, conversation_ref=ref))["success"] is False
    assert json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=True)) == {
        "success": True, "snapshot": None}

    db.notebook_set_local_enabled(ref, False)
    assert json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=True)) == {
        "success": True, "snapshot": None}
    assert json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=False))["success"] is False

    db.notebook_set_local_enabled(ref, True)
    assert json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=False))["success"] is False
    assert json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=True))["snapshot"] is None
    assert json.loads(notebook_show({}, db=db, conversation_ref=None, effective_enabled=True))["success"] is False
    assert json.loads(notebook_show({}, db=None, conversation_ref=ref, effective_enabled=True))["success"] is False
    assert json.loads(notebook_show({"conversation": "other"}, db=db, conversation_ref=ref, effective_enabled=True))["success"] is False
