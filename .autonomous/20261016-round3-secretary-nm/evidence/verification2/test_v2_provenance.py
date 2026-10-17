"""Verification 2 NH-F02: legal History visibility must govern fresh provenance.

This is a review-only counterexample against fixed product SHA b40fa1ff.
It uses real SessionDB, a registered child, the bound notebook_maintain handler,
finish_noting, immutable versions, and the production Snapshot transaction.
Only external Noting readiness is controlled; no model/provider is invoked.
It deliberately asserts the required rejection after recording any publication,
so unfixed product failures retain both History and committed-payload evidence.
"""

import json
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from hermes_state import SessionDB
from hermes_state_secretary_notebook import NotebookError
from secretary.noting_tools import (
    finish_noting,
    initialize_notebook_work,
    notebook_maintain,
)
from tools.session_history_tool import conversation_history


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    # The tested provenance and local/Anchor commit gates remain unpatched.
    monkeypatch.setattr(
        "secretary.noting_runtime.noting_trigger_gate", lambda *a, **k: (True, "")
    )
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


@pytest.mark.parametrize("visibility", ["human_only", "hidden"])
@pytest.mark.parametrize("provenance", ["uid", "range"])
def test_inaccessible_history_cannot_become_committed_fresh_provenance(
    runtime, visibility, provenance
):
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
    source = {"conversation_ref": conversation_ref, "message_uid": "inaccessible"}
    instant = datetime.fromtimestamp(1800000010, timezone.utc).isoformat()
    interval = {"start_time": instant, "end_time": instant}

    def history(**arguments):
        return json.loads(conversation_history(arguments, agent=child))

    visible = history(
        mode="read", message_identity={**source, "message_uid": "visible_user"},
        before=0, after=0,
    )
    assert visible["success"] and visible["count"] == 1, visible
    anchored = history(mode="read", message_identity=source, before=0, after=0)
    ranged = history(mode="read", **interval)
    assert not anchored["success"], anchored
    assert anchored["error"]["code"] == "source_unavailable", anchored
    assert ranged["success"] and ranged["count"] == 0, ranged

    store = child._noting_notebook_store
    before = store.snapshot_state()
    arguments = {
        "action": "create", "entry_type": "situation",
        "fields": {
            "description": "Retain the display-only assertion about the visit.",
            "subjects": ["visit"], "time_context": "Current visit planning",
        },
        **({"source_message_identities": [source]} if provenance == "uid"
           else {"source_time_range": interval}),
    }
    maintained = json.loads(notebook_maintain(child, arguments))
    observed = {
        "visibility": visibility, "provenance": provenance,
        "history_anchor": anchored, "history_range": ranged,
        "maintain": maintained,
    }
    if maintained.get("success"):
        observed["finish"] = json.loads(finish_noting(child, {"reason": "Review probe complete"}))
        try:
            observed["commit"] = store.commit(termination=child._secretary_noting_termination)
        except NotebookError as exc:
            observed["commit_error"] = str(exc)
        observed["current_snapshot"] = database.notebook_current(conversation_ref)
    else:
        assert store.snapshot_state() == before
        assert database.notebook_current(conversation_ref) is None

    evidence = json.dumps(observed, ensure_ascii=False, sort_keys=True)
    print("NH-F02 evidence: " + evidence)
    assert maintained.get("success") is False, evidence
    assert maintained["error"]["code"] == "source_unavailable", evidence
