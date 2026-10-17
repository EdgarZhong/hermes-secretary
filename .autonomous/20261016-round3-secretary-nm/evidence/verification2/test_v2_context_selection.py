"""Independent RT prefix counterexample; run only through the canonical runner.

This file is review evidence, not a product change. It uses a public configurable
ContextEngine hook and the existing native parent fixture. All model I/O is local.
"""

from copy import deepcopy
import json

import pytest

from tests.agent.test_plugin_context_engine_init import _StubEngine
from tests.secretary.test_r3_child import (
    database as database,
    native_parent as native_parent,
    response,
    tool_response,
)


class ReviewSelectingEngine(_StubEngine):
    @property
    def name(self):
        return "review_selecting_engine"

    def __init__(self):
        self.requests = 0

    def select_context(self, request_messages, **kwargs):
        # This is the public request-only selection API: select new contextual
        # material on a later request, without changing durable history or tools.
        self.requests += 1
        selected = deepcopy(request_messages)
        if self.requests >= 2:
            first_user = next(row for row in selected if row.get("role") == "user")
            first_user["content"] = "Retrieved replacement for the earlier context."
        return selected


@pytest.fixture(autouse=True)
def configured_native_selector(monkeypatch):
    config = {
        "context": {"engine": "review_selecting_engine"},
        "compression": {"enabled": False},
        "noting": {"enabled": True, "idle": {"enabled": False}},
        "agent": {},
    }
    monkeypatch.setattr("hermes_cli.config.load_config", lambda *a, **kw: deepcopy(config))
    monkeypatch.setattr("hermes_cli.config.load_config_readonly", lambda *a, **kw: deepcopy(config))
    monkeypatch.setattr("plugins.context_engine.load_context_engine", lambda name: ReviewSelectingEngine())
    monkeypatch.setattr("agent.model_metadata.get_model_context_length", lambda *a, **kw: 204800)


def test_native_noting_second_request_preserves_frozen_parent_with_context_engine(native_parent, database):
    from secretary.noting_child import DEFAULT_NOTING_TASK_INSTRUCTION, active_noting_task_count, run_noting_task

    parent, client = native_parent
    main_wires = []
    client.chat.completions.create.side_effect = lambda **kw: main_wires.append(deepcopy(kw)) or response("Parent response.")
    main_result = parent.run_conversation(
        user_message="Keep this complete Parent prefix.",
        conversation_history=parent._session_messages,
        title_user_message="",
    )
    assert main_result["completed"]
    assert parent.context_compressor.name == "review_selecting_engine"
    assert parent.context_compressor.requests == 1, "Parent must use the same formal selection seam"
    parent._session_messages = main_result["messages"][:-1]
    anchor = parent._session_messages[-1]["message_uid"]
    original_history = deepcopy(parent._session_messages)
    ref = parent._secretary_conversation_ref
    admission_id = database.noting_admit(ref, anchor, kind="manual")

    child_wires = []
    replies = iter([
        tool_response("notebook_show", {}, "show-current-work"),
        tool_response("finish_noting", {"reason": "No changes are necessary."}, "finish-work"),
        response("Completed."),
    ])

    def provider(**kwargs):
        child_wires.append(deepcopy(kwargs))
        return next(replies)

    client.chat.completions.create.side_effect = provider
    outcome = run_noting_task(
        parent,
        admission_id=admission_id,
        conversation_ref=ref,
        anchor_message_uid=anchor,
        trigger_type="manual",
        runtime_profile="NOTING",
        task_instruction=DEFAULT_NOTING_TASK_INSTRUCTION,
        admission_timestamp=500,
    )
    expected = main_wires[0]["messages"]
    boundary = len(expected)
    print(json.dumps({
        "configured_engine": parent.context_compressor.name,
        "main_request_count": len(main_wires),
        "noting_request_count": len(child_wires),
        "committed": outcome.committed,
        "termination": outcome.termination,
        "prefix_equal_per_request": [wire["messages"][:boundary] == expected for wire in child_wires],
        "tools_equal_per_request": [wire["tools"] == main_wires[0]["tools"] for wire in child_wires],
        "active_children_after": active_noting_task_count(),
    }, ensure_ascii=False, sort_keys=True))
    assert outcome.committed, outcome
    assert len(child_wires) == 3
    assert active_noting_task_count() == 0
    assert parent._session_messages[:len(original_history)] == original_history
    assert child_wires[0]["messages"][:boundary] == expected
    assert child_wires[1]["messages"][:boundary] == expected, (
        "The second actual native Noting request changed its frozen Parent prefix through select_context."
    )
