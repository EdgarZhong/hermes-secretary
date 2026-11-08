"""Real native iteration handoffs continue the same bounded Noting task."""

from contextlib import contextmanager
from copy import deepcopy
import json

import pytest

from agent.turn_failure_copy import is_max_iteration_handoff
from secretary import noting_child
from secretary.noting_prompts import DEFAULT_NOTING_TASK_INSTRUCTION
from tests.secretary.test_fixed_noting_permissions import call, runtime as base_runtime


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with contextmanager(base_runtime.__wrapped__)(tmp_path, monkeypatch) as value:
        value[0].model = "controlled-noting-model"
        value[0].provider = "custom"
        value[0].reasoning_config = {"enabled": True, "effort": "high"}
        value[3]["sent"].clear()
        yield value


def capture_child(monkeypatch, configure=None):
    from run_agent import AIAgent

    children, turns = [], []
    construct, run = noting_child.build_noting_child, AIAgent.run_conversation

    def build(*args, **kwargs):
        child = construct(*args, **kwargs)
        if configure is not None:
            configure(child)
        children.append(child)
        return child

    def turn(agent, *args, **kwargs):
        result = run(agent, *args, **kwargs)
        if getattr(agent, "_secretary_noting_child", False):
            turns.append(deepcopy(result))
        return result

    monkeypatch.setattr(noting_child, "build_noting_child", build)
    monkeypatch.setattr(AIAgent, "run_conversation", turn)
    return children, turns


def task_controls(request):
    return [row["content"] for row in request["messages"]
            if row.get("role") == "user" and str(row.get("content", "")).startswith("<noting-task>")]


def run_task(parent):
    db, ref = parent._session_db, parent._secretary_conversation_ref
    anchor = parent._session_messages[-1]["message_uid"]
    admission = db.noting_admit(ref, anchor, kind="manual")
    return noting_child.run_noting_task(
        parent, admission_id=admission, conversation_ref=ref, anchor_message_uid=anchor,
        trigger_type="manual", runtime_profile="NOTING", task_instruction=DEFAULT_NOTING_TASK_INSTRUCTION,
    )


def test_native_budget_continues_updates_same_source_slot_then_finishes(runtime, monkeypatch, record_property):
    parent, db, _config, state = runtime
    monkeypatch.setattr(noting_child, "NOTING_MAX_ITERATIONS", 1)
    children, turns = capture_child(monkeypatch)
    uid = parent._session_messages[0]["message_uid"]
    fields = {"description": "Send the report", "completion_condition": "Report delivered"}

    def update(request):
        result = next(json.loads(row["content"]) for row in request["messages"]
                      if row.get("tool_call_id") == "create")
        return [call("notebook_update", {"entry_id": result["entry"]["entry_id"], "done": True,
                                       "source_message_uids": [uid]}, "update")]

    state["script"] = [
        [call("notebook_create", {"entry_type": "matter", "fields": fields, "source_message_uids": [uid]}, "create")],
        None, update, None, [call("finish_noting", {"reason": "Recorded the report and its completion."}, "finish")],
    ]
    before = deepcopy(parent._session_messages)
    outcome = run_task(parent)
    assert outcome.committed and outcome.turns == 3 and outcome.termination["type"] == "finish_noting", outcome
    assert len(children) == 1 and len(turns) == 3
    assert all(is_max_iteration_handoff(result) for result in turns[:2])
    assert turns[2]["turn_exit_reason"] == "noting_finished"
    child = children[0]
    assert child.model == parent.model and child.provider == parent.provider
    assert child.reasoning_config == parent.reasoning_config and child.api_mode == parent.api_mode
    assert child._cached_system_prompt == parent._cached_system_prompt
    assert child.tools == parent.tools
    first = state["sent"][0]
    prefix_size = next(index for index, row in enumerate(first["messages"])
                       if str(row.get("content", "")).startswith("<noting-task>"))
    for request in state["sent"]:
        assert request["messages"][:prefix_size] == first["messages"][:prefix_size]
        assert request["tools"] == first["tools"] and request["model"] == first["model"]
    controls = task_controls(state["sent"][-1])
    assert len(controls) == 3
    for control in controls[1:]:
        assert "previous native Turn reached its iteration limit" in control
        assert "Continue the same Noting task" in control and "final standalone tool action" in control
        assert "CURRENT NOTING CONTROL" in control and "not a new user request" in control
    entry = db.notebook_current(parent._secretary_conversation_ref)["payload"]["work"][0]
    assert entry["done"] and entry["provenance"] == [[uid]]
    working_entry = child._noting_notebook_store.snapshot_state()["work"][0]
    assert working_entry["provenance_tasks"] == [str(child._secretary_noting_admission_id)]
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_item")[0] == 2
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots")[0] == 1
    rows = db.get_messages_as_conversation(outcome.child_session_id)
    assert [row["tool_call_id"] for row in rows if row["role"] == "tool"] == ["create", "update", "finish"]
    assert parent._session_messages[:len(before)] == before
    record_property("controlled_requests", json.dumps(state["sent"], ensure_ascii=False))
    record_property("native_turn_exits", json.dumps([result["turn_exit_reason"] for result in turns]))


def test_fifth_native_budget_handoff_forces_exactly_one_snapshot(runtime, monkeypatch):
    parent, db, _config, state = runtime
    monkeypatch.setattr(noting_child, "NOTING_MAX_ITERATIONS", 1)
    children, turns = capture_child(monkeypatch)
    state["script"] = [part for index in range(5)
                       for part in ([call("notebook_show", {}, f"show-{index}")], None)]
    outcome = run_task(parent)
    assert outcome.committed and outcome.turns == 5 and outcome.termination == {"type": "forced"}, outcome
    assert len(children) == 1 and len(turns) == 5 and all(map(is_max_iteration_handoff, turns))
    assert len(state["sent"]) == 10 and not state["script"]
    assert "five-Turn" in outcome.termination_summary and "unfinished" in outcome.termination_summary
    assert db._read_one("SELECT COUNT(*) FROM secretary_notebook_snapshots")[0] == 1
    rows = db.get_messages_as_conversation(outcome.child_session_id)
    assert len([row for row in rows if row["role"] == "user" and row["content"].startswith("<noting-task>")]) == 5
    assert [row["tool_call_id"] for row in rows if row["role"] == "tool"] == [f"show-{index}" for index in range(5)]


@pytest.mark.parametrize("prior_budget_turns", [0, 4])
def test_finish_at_budget_boundary_does_not_continue(runtime, monkeypatch, prior_budget_turns):
    parent, _db, _config, state = runtime
    monkeypatch.setattr(noting_child, "NOTING_MAX_ITERATIONS", 1)
    state["script"] = [part for index in range(prior_budget_turns)
                       for part in ([call("notebook_show", {}, f"show-{index}")], None)]
    state["script"].append([call("finish_noting", {"reason": "Reviewed"}, "finish")])
    outcome = run_task(parent)
    assert outcome.committed and outcome.turns == prior_budget_turns + 1 and outcome.termination["type"] == "finish_noting"
    assert len(state["sent"]) == prior_budget_turns * 2 + 1


def test_budget_then_plain_text_uses_the_corresponding_continuation(runtime, monkeypatch):
    parent, _db, _config, state = runtime
    monkeypatch.setattr(noting_child, "NOTING_MAX_ITERATIONS", 1)
    state["script"] = [[call("notebook_show", {}, "show")], None, None,
                       [call("finish_noting", {"reason": "Reviewed"}, "finish")]]
    outcome = run_task(parent)
    assert outcome.committed and outcome.turns == 3 and outcome.termination["type"] == "finish_noting"
    controls = task_controls(state["sent"][-1])
    assert "reached its iteration limit" in controls[1]
    assert "reached its iteration limit" not in controls[2]
    assert "ended without a successful finish_noting request" in controls[2]


def test_main_native_budget_still_returns_one_handoff(runtime):
    parent, db, _config, state = runtime
    parent.max_iterations = parent.iteration_budget.max_total = 1
    state["script"] = [[call("notebook_show", {}, "show")], None]
    result = parent.run_conversation(user_message="Inspect the current Notebook", title_user_message="")
    assert is_max_iteration_handoff(result)
    assert len(state["sent"]) == 2 and not state["script"]
    assert db.notebook_current(parent._secretary_conversation_ref) is None


def test_budget_continuation_keeps_tool_execution_permissions(runtime, monkeypatch):
    parent, db, _config, state = runtime
    monkeypatch.setattr(noting_child, "NOTING_MAX_ITERATIONS", 1)
    state["script"] = [[call("notebook_show", {}, "show")], None,
                       [call("terminal", {"command": "echo forbidden"}, "denied")], None,
                       [call("finish_noting", {"reason": "Reviewed"}, "finish")]]
    outcome = run_task(parent)
    assert outcome.committed and outcome.turns == 3 and outcome.termination["type"] == "finish_noting"
    rows = db.get_messages_as_conversation(outcome.child_session_id)
    denied = next(json.loads(row["content"]) for row in rows if row.get("tool_call_id") == "denied")
    assert denied["success"] is False and denied["error"]["code"] == "scope_denied"
    assert db.notebook_current(parent._secretary_conversation_ref)["payload"]["work"] == []


@pytest.mark.parametrize("exit_kind", ["cancel", "persistence", "overflow"])
def test_native_terminal_boundaries_do_not_start_another_turn(runtime, monkeypatch, exit_kind):
    from run_agent import AIAgent

    parent, db, _config, state = runtime
    monkeypatch.setattr(noting_child, "NOTING_MAX_ITERATIONS", 1)
    configure = ((lambda child: setattr(child.context_compressor, "context_length", 1))
                 if exit_kind == "overflow" else None)
    children, _turns = capture_child(monkeypatch, configure)
    original = AIAgent._flush_messages_to_session_db

    def flush(agent, messages, *args, **kwargs):
        if exit_kind == "persistence" and getattr(agent, "_secretary_noting_child", False):
            return False
        return original(agent, messages, *args, **kwargs)

    def response(_request):
        if exit_kind == "cancel":
            children[0].interrupt("Controlled cancellation", hard_cancel=True)
        return [call("notebook_show", {}, "show")]

    monkeypatch.setattr(AIAgent, "_flush_messages_to_session_db", flush)
    state["script"] = [response, None]
    outcome = run_task(parent)
    assert outcome.turns == 1, outcome
    if exit_kind == "overflow":
        assert outcome.committed and outcome.termination == {"type": "context_overflow"}, outcome
    else:
        assert not outcome.committed and db.notebook_current(parent._secretary_conversation_ref) is None, outcome
    assert len(state["sent"]) <= 2
