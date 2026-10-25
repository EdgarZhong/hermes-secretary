"""Model Notebook values exclude audit envelopes; default API values stay compatible."""

import json
from types import SimpleNamespace

import pytest

from hermes_state import SessionDB
from hermes_time import format_timestamp
from secretary.notebook_render import show_notebook
from secretary.notebook_store import NotebookStore
from tools.notebook_tool import notebook_show


@pytest.fixture
def notebook(tmp_path):
    db = SessionDB(tmp_path / "state.db")
    db.create_session("main", source="cli")
    db.append_message("main", "user", "Confirmed visit", message_uid="source-uid", timestamp=100)
    ref = db.resolve_conversation_ref("main")
    store = NotebookStore(db, ref, anchor_message_uid="source-uid")
    entry = store.create("matter", {"description": "Confirmed visit", "completion_condition": "Visit complete"},
                         source_message_identities=[{"conversation_ref": ref, "message_uid": "source-uid"}])["entry"]
    store.commit(termination={"type": "finish_noting", "reason": "Indexed visit"})
    yield db, ref, entry
    db.close()


def test_default_api_retains_audit_fields_while_model_projection_preserves_actionable_ids(notebook):
    db, ref, entry = notebook
    snapshot = db.notebook_current(ref)
    public = json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=True))
    model = json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=True, model_visible=True))
    assert public == show_notebook(snapshot, profile_home=db.db_path.parent, db=db, conversation_ref=ref)
    assert public["snapshot_id"] == snapshot["snapshot_id"]
    assert public["coverage"] == {"anchor_message_uid": "source-uid"}
    assert not {"snapshot_id", "base_snapshot_id", "coverage"}.intersection(model)
    assert model["conversation_ref"] == ref
    assert public["payload"]["work"][0]["version_id"] == entry["version_id"]
    item = model["payload"]["work"][0]
    assert item["entry_id"] == entry["entry_id"]
    assert "version_id" not in item
    assert item == {key: value for key, value in public["payload"]["work"][0].items() if key != "version_id"}
    assert item["source_message_uids"] == ["source-uid"]
    assert item["evidence_time"] == [format_timestamp(100, profile_home=db.db_path.parent)]
    assert db.notebook_current(ref) == snapshot


def test_formal_inline_and_catalog_model_routes_exclude_audit_envelope(notebook, monkeypatch):
    from agent.inline_tool_executors import _notebook_show
    from tools.registry import registry

    db, ref, entry = notebook
    monkeypatch.setattr("secretary.noting_surface.notebook_dispatch_enabled", lambda _agent: True)
    agent = SimpleNamespace(_session_db=db, _secretary_conversation_ref=ref)
    inline = json.loads(_notebook_show(agent, {}, None))
    catalog = json.loads(registry.get_entry("notebook_show").handler(
        {}, db=db, conversation_ref=ref, effective_enabled=True))
    for result in (inline, catalog):
        assert not {"snapshot_id", "base_snapshot_id", "coverage"}.intersection(result)
        assert result["payload"]["work"][0]["entry_id"] == entry["entry_id"]
        assert "version_id" not in result["payload"]["work"][0]


def test_empty_model_show_preserves_success_and_default_api_nulls(tmp_path):
    db = SessionDB(tmp_path / "empty.db")
    try:
        db.create_session("main", source="cli")
        ref = db.resolve_conversation_ref("main")
        public = json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=True))
        model = json.loads(notebook_show({}, db=db, conversation_ref=ref, effective_enabled=True, model_visible=True))
        assert public["snapshot_id"] is None and public["coverage"] is None
        assert model["success"] and model["payload"] == public["payload"]
        assert not {"snapshot_id", "base_snapshot_id", "coverage"}.intersection(model)
    finally:
        db.close()
