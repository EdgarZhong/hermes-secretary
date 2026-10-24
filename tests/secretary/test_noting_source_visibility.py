"""V2-F01 regression: only History-readable evidence may ground fresh Notebook provenance.

This is the public-tool form of the review counterexample: real SessionDB, a registered
Noting child, the bound ``notebook_create`` handler, ``finish_noting`` and the production
Snapshot transaction.  Hidden and human-only rows are unreadable through History, so they
must not become committed sources; a visible row remains a legal source.
"""

import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from hermes_state import SessionDB
from secretary.noting_tools import finish_noting, initialize_notebook_work, notebook_create


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    monkeypatch.setattr("secretary.noting_runtime.noting_trigger_gate", lambda *a, **k: (True, ""))
    database = SessionDB(tmp_path / "state.db")
    database.create_session("parent", source="cli")
    database.append_message(
        "parent", "user", "Please collect the context for my visit.",
        message_uid="visible_user", timestamp=1800000000,
    )
    yield database
    database.close()


def bind_child(database):
    conversation_ref = database.resolve_conversation_ref("parent")
    database.create_session(
        "child", source="subagent", parent_session_id="parent",
        model_config={"_delegate_from": "parent"},
    )
    admission = database.noting_admit(conversation_ref, "visible_anchor", kind="idle")
    database.noting_child_register(admission, child_session_id="child", profile=None)
    child = SimpleNamespace(
        _session_db=database, _secretary_history_db=database,
        session_id="child", platform="subagent", side_agent=True,
        _parent_session_id="parent", _secretary_noting_child=True,
        _secretary_parent_conversation_ref=conversation_ref,
        _secretary_noting_anchor_uid="visible_anchor",
        _secretary_noting_profile="NOTING",
        _secretary_noting_terminal_action_done=False,
        _secretary_noting_termination=None,
    )
    initialize_notebook_work(child, trigger_type="idle")
    return child, conversation_ref


def maintain(child, conversation_ref, *, message_uid=None, instant=None):
    fields = {
        "description": "Retain the visit assertion.",
        "subjects": ["visit"], "time_context": "Current visit planning",
    }
    arguments = {"entry_type": "situation", "fields": fields}
    if message_uid is not None:
        arguments["source_message_uids"] = [message_uid]
    else:
        arguments["source_time_range"] = {"start_time": instant, "end_time": instant}
    return json.loads(notebook_create(child, arguments))


@pytest.mark.parametrize("visibility", ["human_only", "hidden"])
@pytest.mark.parametrize("provenance", ["uid", "range"])
def test_unreadable_history_cannot_ground_new_provenance(runtime, visibility, provenance):
    database = runtime
    attributes = ({"display_metadata": {"human_only": True}}
                  if visibility == "human_only" else {"display_kind": "hidden"})
    database.append_message(
        "parent", "assistant", "A display-only assertion about the visit.",
        message_uid="inaccessible", timestamp=1800000010, **attributes,
    )
    database.append_message(
        "parent", "assistant", "I will check the visit context.",
        message_uid="visible_anchor", timestamp=1800000020,
    )
    child, conversation_ref = bind_child(database)
    store = child._noting_notebook_store
    before = store.snapshot_state()
    instant = datetime.fromtimestamp(1800000010, timezone.utc).isoformat()

    result = (maintain(child, conversation_ref, message_uid="inaccessible")
              if provenance == "uid" else maintain(child, conversation_ref, instant=instant))

    assert result["success"] is False, result
    assert result["error"]["code"] == "source_unavailable", result
    assert store.snapshot_state() == before
    assert database.notebook_current(conversation_ref) is None


def test_visible_history_remains_a_legal_source(runtime):
    database = runtime
    database.append_message(
        "parent", "assistant", "I will check the visit context.",
        message_uid="visible_anchor", timestamp=1800000020,
    )
    child, conversation_ref = bind_child(database)
    store = child._noting_notebook_store

    result = maintain(child, conversation_ref, message_uid="visible_user")

    assert result["success"] is True, result
    finished = json.loads(finish_noting(child, {"reason": "Provenance visibility regression"}))
    assert finished["success"] is True, finished
    committed = store.commit(termination=child._secretary_noting_termination)
    assert committed["pointer_changed"]
    snapshot = database.notebook_current(conversation_ref)
    assert snapshot["snapshot_id"] == committed["snapshot_id"]
