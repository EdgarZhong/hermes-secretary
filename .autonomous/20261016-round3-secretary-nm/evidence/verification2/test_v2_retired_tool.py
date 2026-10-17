"""Second Verification evidence: raw retired names through the real Noting loop.

Only the model client is stubbed. The native tool-name repair, child dispatcher,
Notebook mutation, admission, and snapshot commit are the fixed implementation.
"""

from __future__ import annotations

import copy
import json

import pytest

from secretary.noting_child import run_noting_task
from tests.secretary.test_noting_child import (  # existing real-runtime fixture helpers
    _tool_response,
    db,
    make_agent,
    mock_response,
    stub_client,
)
from tools.notebook_tool import NOTEBOOK_SHOW_SCHEMA


@pytest.fixture
def parent(db, stub_client):
    db.create_session("S17", source="test", session_key="peer")
    db.append_message("S17", "user", "please remind me about the report", message_uid="m1", timestamp=1000.0)
    db.append_message("S17", "assistant", "will do", message_uid="m2", timestamp=1001.0)
    agent = make_agent("S17", db, session_key="peer")
    agent._secretary_conversation_ref = db.resolve_conversation_ref("S17")
    agent._session_messages = db.get_messages_as_conversation("S17")
    agent.tools = [{"type": "function", "function": copy.deepcopy(NOTEBOOK_SHOW_SCHEMA)}]
    yield agent
    agent.close()


@pytest.mark.parametrize(
    ("raw_tool_name", "expected_write"),
    [
        pytest.param("notebook_maintain", True, id="current-name-positive-control"),
        pytest.param("notebook_manage", False, id="known-retired-negative-control"),
        pytest.param("notebook_mutate", False, id="required-retired-name-must-not-write"),
    ],
)
def test_raw_retired_name_cannot_write_through_native_noting_loop(
    parent, db, stub_client, raw_tool_name, expected_write
):
    ref = parent._secretary_conversation_ref
    maintain_args = {
        "action": "create",
        "entry_type": "matter",
        "fields": {
            "description": "SECOND_VERIFICATION_RAW_NAME_WRITE",
            "completion_condition": "Report sent",
        },
        "source_time_range": {
            "start_time": "1970-01-01T00:16:40+00:00",
            "end_time": "1970-01-01T00:16:41+00:00",
        },
    }
    stub_client.chat.completions.create.side_effect = [
        _tool_response("notebook_show", {}, "read"),
        _tool_response(raw_tool_name, maintain_args, "candidate-write"),
        _tool_response("finish_noting", {"reason": "Controlled name-dispatch verification finished."}, "finish"),
        mock_response("done"),
    ]
    admission_id = db.noting_admit(ref, "m2", kind="idle")
    assert admission_id is not None
    outcome = run_noting_task(
        parent,
        admission_id=admission_id,
        conversation_ref=ref,
        anchor_message_uid="m2",
        trigger_type="idle",
        runtime_profile="NOTING",
        task_instruction="Maintain the Notebook using the supplied tool calls, then finish.",
        parent_active_messages=parent._session_messages,
        admission_timestamp=2000.0,
    )
    assert outcome.committed is True, outcome
    assert outcome.status == "completed", outcome
    snapshot = db.notebook_current(ref)
    assert snapshot is not None
    rows = db.get_messages_as_conversation(outcome.child_session_id)
    tool_rows = [row for row in rows if row.get("role") == "tool"]
    written = any(
        entry.get("fields", {}).get("description") == "SECOND_VERIFICATION_RAW_NAME_WRITE"
        for entry in snapshot["payload"]["work"]
    )
    evidence = {
        "raw_model_tool_name": raw_tool_name,
        "raw_arguments": maintain_args,
        "model_calls": stub_client.chat.completions.create.call_count,
        "outcome": {"status": outcome.status, "committed": outcome.committed, "turns": outcome.turns},
        "tool_rows": tool_rows,
        "committed_work": snapshot["payload"]["work"],
        "expected_write": expected_write,
        "observed_write": written,
    }
    print("SECOND_VERIFICATION_EVIDENCE " + json.dumps(evidence, ensure_ascii=False, default=str))
    assert written is expected_write, json.dumps(evidence, ensure_ascii=False, default=str)
