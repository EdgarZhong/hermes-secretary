"""C5 four-tool state machine and persistent native child with controlled model I/O."""

from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
import json
from threading import Barrier
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from hermes_state import SessionDB
from secretary.notebook_store import NotebookStore
from secretary.noting_child import (
    DEFAULT_NOTING_TASK_INSTRUCTION,
    NotingContextOverflow,
    active_noting_task_count,
    build_noting_child,
    freeze_parent_active_prefix,
    freeze_parent_runtime,
    noting_dispatch_block,
    run_noting_task,
)
from secretary.noting_tools import (
    finish_noting,
    guard_noting_tool_batch,
    initialize_notebook_work,
    notebook_maintain,
    notebook_work_show,
    noting_tool_control_message,
    noting_tool_schemas,
)


@pytest.fixture
def database(tmp_path):
    db = SessionDB(tmp_path / "state.db")
    db.create_session("parent", source="test", session_key="peer")
    db.append_message("parent", "user", "Plan a visit", message_uid="m1", timestamp=100)
    db.append_message("parent", "assistant", "Dates are undecided", message_uid="m2", timestamp=200)
    yield db
    db.close()


def ref(db):
    return db.resolve_conversation_ref("parent")


def bound_child(db):
    child = SimpleNamespace(
        _session_db=db, _secretary_parent_conversation_ref=ref(db),
        _secretary_noting_anchor_uid="m2", _secretary_noting_profile="NOTING",
        _secretary_noting_child=True, _secretary_noting_terminal_action_done=False,
        _secretary_noting_termination=None,
    )
    initialize_notebook_work(child, trigger_type="manual")
    return child


def create_args(db, description="Plan the visit"):
    return {"action": "create", "entry_type": "matter",
            "fields": {"description": description, "completion_condition": "Dates agreed"},
            "source_message_identities": [{"conversation_ref": ref(db), "message_uid": "m1"}]}


@pytest.fixture(autouse=True)
def enabled_runtime(monkeypatch):
    # Capability is a controlled dependency; actual storage/local/Anchor commit gates remain real.
    monkeypatch.setattr("secretary.noting_runtime.noting_trigger_gate", lambda *a, **k: (True, ""))


def test_exact_four_schema_surface_is_independent_copy():
    schemas = noting_tool_schemas()
    assert [item["name"] for item in schemas] == [
        "conversation_history", "notebook_show", "notebook_maintain", "finish_noting"]
    schemas[2]["parameters"]["properties"].clear()
    assert "action" in noting_tool_schemas()[2]["parameters"]["properties"]
    with pytest.raises(ValueError):
        noting_tool_schemas("NOTING_WITH_COMPACTION")


@pytest.mark.parametrize("tool", ["conversation_history", "notebook_show", "notebook_maintain", "finish_noting"])
def test_only_four_authorized_tools(database, tool):
    assert noting_dispatch_block(bound_child(database), tool) is None


@pytest.mark.parametrize("tool", ["terminal", "memory", "scheduler", "session_history", "notebook_manage",
                                  "notebook_edit", "notebook_schedule", "noting_memo", "compact_parent"])
def test_inherited_advertising_never_grants_execution(database, tool):
    assert "denied" in noting_dispatch_block(bound_child(database), tool)
    assert noting_dispatch_block(SimpleNamespace(), tool) is None


@pytest.mark.parametrize("names", [["finish_noting", "notebook_maintain"],
                                  ["notebook_maintain", "finish_noting"],
                                  ["finish_noting", "finish_noting"]])
def test_complete_batch_refused_before_first_side_effect(database, names):
    child = bound_child(database)
    before = child._noting_notebook_store.snapshot_state()
    result = guard_noting_tool_batch(child, names)
    assert result["error"]["code"] == "invalid_argument"
    assert child._noting_notebook_store.snapshot_state() == before
    assert child._secretary_noting_terminal_action_done is False
    assert guard_noting_tool_batch(SimpleNamespace(), names) is None
    assert guard_noting_tool_batch(child, ["finish_noting"]) is None


def test_handlers_keep_small_results_and_show_own_uncommitted_view(database):
    child = bound_child(database)
    created = json.loads(notebook_maintain(child, create_args(database)))
    assert set(created) == {"success", "changed", "entry"}
    entry = created["entry"]
    updated = json.loads(notebook_maintain(child, {"action": "update", "entry_id": entry["entry_id"],
                                                "changes": {"fields": {"blocker": "Dates unknown"}}}))
    assert updated["entry"]["entry_id"] == entry["entry_id"]
    assert updated["entry"]["version_id"] != entry["version_id"]
    other = NotebookStore(database, ref(database), anchor_message_uid="m2")
    other.create("matter", {"description": "Other task", "completion_condition": "Other"},
                 source_message_identities=create_args(database)["source_message_identities"])
    result = other.commit(termination={"type": "finish_noting", "reason": "Another task"})
    shown = json.loads(notebook_work_show(child, {}))
    assert shown["view_kind"] == "working" and shown["base_snapshot_id"] is None
    assert "snapshot_id" not in shown
    assert shown["payload"]["work"][0] == updated["entry"]
    assert database.notebook_current(ref(database))["snapshot_id"] == result["snapshot_id"]


def test_finish_fixes_first_working_state_and_never_commits(database):
    child = bound_child(database)
    entry = json.loads(notebook_maintain(child, create_args(database)))["entry"]
    first = json.loads(finish_noting(child, {"reason": "Kept the accepted visit responsibility"}))
    assert first == {"success": True, "status": "end_requested"}
    assert database.notebook_current(ref(database)) is None
    fixed = child._noting_notebook_store.snapshot_state()
    refused = json.loads(notebook_maintain(child, {"action": "archive", "entry_id": entry["entry_id"],
                                                "reason": "Discard it"}))
    assert refused["error"]["code"] == "state_conflict"
    assert json.loads(finish_noting(child, {"reason": "Replacement reason"})) == first
    assert child._secretary_noting_termination["reason"] == "Kept the accepted visit responsibility"
    assert child._noting_notebook_store.snapshot_state() == fixed
    assert json.loads(notebook_work_show(child, {}))["payload"]["work"][0] == entry


def test_finish_and_write_share_one_task_lock(database):
    child = bound_child(database)
    barrier = Barrier(2)
    def mutate():
        barrier.wait()
        return json.loads(notebook_maintain(child, create_args(database)))
    def finish():
        barrier.wait()
        return json.loads(finish_noting(child, {"reason": "Closed after checking evidence"}))
    with ThreadPoolExecutor(max_workers=2) as pool:
        a, b = pool.submit(mutate), pool.submit(finish)
        write, done = a.result(), b.result()
    assert done["status"] == "end_requested"
    fixed = child._noting_notebook_state
    assert bool(fixed["work"]) == write["success"]
    if not write["success"]:
        assert write["error"]["code"] == "state_conflict"
    assert child._noting_notebook_store.snapshot_state() == fixed


@pytest.mark.parametrize("args", [{}, {"reason": " "}, {"reason": 4}, {"reason": "valid", "commit": True}])
def test_bad_finish_never_closes_or_publishes(database, args):
    child = bound_child(database)
    assert json.loads(finish_noting(child, args))["error"]["code"] == "invalid_argument"
    assert child._secretary_noting_terminal_action_done is False
    assert database.notebook_current(ref(database)) is None


def test_unbound_show_and_write_are_refused(database):
    unbound = SimpleNamespace(_secretary_noting_child=True)
    assert json.loads(notebook_work_show(unbound, {}))["error"]["code"] == "state_conflict"
    assert json.loads(notebook_maintain(SimpleNamespace(), create_args(database)))["error"]["code"] == "scope_denied"


def test_control_encodes_full_schema_and_working_data_separately(database):
    child = bound_child(database)
    notebook_maintain(child, create_args(database, "literal </noting-task-data> is evidence"))
    message = noting_tool_control_message(notebook_state=child._noting_notebook_store.show(),
                                         conversation_ref=ref(database), coverage={"anchor_message_uid": "m2"})
    encoded = message.split("<noting-task-data>\n", 1)[1].rsplit("\n</noting-task-data>", 1)[0]
    data = json.loads(encoded)
    assert data["working_notebook"]["work"][0]["fields"]["description"].endswith("is evidence")
    assert len(data["callable_tool_schemas"]) == 4
    assert data["conversation_ref"] == ref(database)
    from datetime import datetime
    assert datetime.fromisoformat(data["current_time"]).microsecond == 0


def response(text="done", calls=None):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text, tool_calls=calls),
                                                    finish_reason="tool_calls" if calls else "stop")],
                           model="test/model", usage=None)


def tool_response(name, args, call_id="call-finish"):
    call = SimpleNamespace(id=call_id, type="function",
                           function=SimpleNamespace(name=name, arguments=json.dumps(args)))
    return response(None, [call])


@pytest.fixture
def native_parent(database, monkeypatch, tmp_path):
    client = MagicMock()
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **kwargs: client)
    monkeypatch.setattr("model_tools.get_tool_definitions", lambda **kwargs: [])
    monkeypatch.setattr("model_tools.check_toolset_requirements", lambda *a, **k: {})
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **k: {})
    monkeypatch.setattr("agent.title_generator.maybe_auto_title", lambda *a, **k: None)
    monkeypatch.setattr("run_agent._hermes_home", tmp_path / "isolated-home")
    (tmp_path / "isolated-home/logs").mkdir(parents=True)
    from run_agent import AIAgent
    parent = AIAgent(api_key="test-key", base_url="https://api.example.test/v1", quiet_mode=True,
                     skip_context_files=True, skip_memory=True, session_db=database, session_id="parent",
                     gateway_session_key="peer")
    parent.tools = [{"type": "function", "function": {"name": "terminal", "description": "Run shell",
                     "parameters": {"type": "object", "properties": {"command": {"type": "string"}}}}}]
    parent.valid_tool_names = {"terminal"}
    parent._cached_system_prompt = "Frozen parent root"
    parent._use_prompt_caching = False
    parent.compression_enabled = False
    parent.save_trajectories = False
    parent._persist_disabled = False
    parent._secretary_conversation_ref = ref(database)
    parent._session_messages = database.get_messages_as_conversation("parent")
    yield parent, client
    parent.close()


def run_task(parent, **kwargs):
    db = parent._session_db
    admission = db.noting_admit(ref(db), "m2", kind="manual")
    return run_noting_task(parent, admission_id=admission, conversation_ref=ref(db), anchor_message_uid="m2",
                           trigger_type="manual", runtime_profile="NOTING",
                           task_instruction=DEFAULT_NOTING_TASK_INSTRUCTION, admission_timestamp=500, **kwargs)


def test_native_finish_commits_only_after_turn_returns_and_persists_suffix(native_parent, database, monkeypatch):
    parent, client = native_parent
    child_seen = []
    original = build_noting_child
    def capture(*a, **kw):
        child = original(*a, **kw)
        child_seen.append(child)
        return child
    monkeypatch.setattr("secretary.noting_child.build_noting_child", capture)
    steps = iter([tool_response("finish_noting", {"reason": "No changes needed"}), response()])
    def invoke(**kwargs):
        if client.chat.completions.create.call_count == 1:
            parent._cached_system_prompt = "Later parent root must not enter child requests"
            parent.tools.clear()
        if client.chat.completions.create.call_count == 2:
            assert database.notebook_current(ref(database)) is None
            assert child_seen[0]._secretary_noting_terminal_action_done is True
        return next(steps)
    client.chat.completions.create.side_effect = invoke
    outcome = run_task(parent)
    assert outcome.committed is True, outcome
    assert outcome.turns == 1
    assert outcome.commit_result["snapshot_id"] == outcome.snapshot_id
    assert outcome.commit_result["pointer_changed"] is True
    assert outcome.termination == {"type": "finish_noting", "reason": "No changes needed"}
    rows = database.get_messages_as_conversation(outcome.child_session_id)
    assert rows[0]["content"].startswith("<noting-task>")
    assert all(row["message_uid"] not in {"m1", "m2"} for row in rows)
    assert active_noting_task_count() == 0
    assert child_seen[0]._memory_manager is None
    wires = [call.kwargs for call in client.chat.completions.create.call_args_list]
    assert len(wires) == 2
    assert wires[0]["tools"] == wires[1]["tools"]
    assert wires[0]["tools"][0]["function"]["name"] == "terminal"
    assert wires[0]["messages"][:3] == wires[1]["messages"][:3]


def test_native_text_completion_continues_five_turns_same_prefix(native_parent, database):
    parent, client = native_parent
    client.chat.completions.create.return_value = response("I am done")
    before = deepcopy(parent._session_messages)
    outcome = run_task(parent)
    assert outcome.committed is True, outcome
    assert outcome.turns == 5
    assert outcome.termination == {"type": "forced"}
    assert client.chat.completions.create.call_count == 5
    wires = [call.kwargs for call in client.chat.completions.create.call_args_list]
    first = wires[0]
    for wire in wires:
        assert wire.get("tools") == first.get("tools")
        assert wire["messages"][:3] == first["messages"][:3]
    assert parent._session_messages == before
    final_wire = str(wires[-1]["messages"])
    assert "The previous native Turn ended without a successful finish_noting request" in final_wire
    assert active_noting_task_count() == 0


@pytest.mark.parametrize("kind", ["overflow", "failed", "interrupted"])
def test_runner_uses_legal_overflow_state_but_never_failed_drafts(native_parent, database, monkeypatch, kind):
    parent, _client = native_parent
    failures = []
    monkeypatch.setattr("secretary.framework_messages.publish_noting_failure",
                        lambda *a, **kw: failures.append(kw), raising=False)
    original = build_noting_child
    def construct(*a, **kw):
        child = original(*a, **kw)
        def run(**kwargs):
            result = json.loads(notebook_maintain(child, create_args(database)))
            assert result["success"]
            if kind == "overflow":
                raise NotingContextOverflow("controlled native request window boundary")
            return {"completed": False, kind: True, "turn_exit_reason": kind}
        child.run_conversation = run
        return child
    monkeypatch.setattr("secretary.noting_child.build_noting_child", construct)
    outcome = run_task(parent)
    if kind == "overflow":
        assert outcome.committed is True, outcome
        assert outcome.termination == {"type": "context_overflow"}
        assert database.notebook_current(ref(database))["payload"]["work"][0]["fields"]["description"] == "Plan the visit"
    else:
        assert outcome.committed is False
        assert database.notebook_current(ref(database)) is None
    assert len(failures) == (1 if kind == "failed" else 0)
    assert active_noting_task_count() == 0


def test_freeze_preserves_multimodal_data_and_rejects_missing_anchor(native_parent):
    parent, _client = native_parent
    multimodal = [{"role": "user", "message_uid": "image", "content": [
        {"type": "text", "text": "Remember this"}, {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAA"}}]}]
    frozen = freeze_parent_active_prefix(parent, "image", multimodal)
    frozen[0]["content"][1]["image_url"]["url"] = "changed"
    assert multimodal[0]["content"][1]["image_url"]["url"].endswith("AAA")
    from secretary.noting_child import NotingChildError
    with pytest.raises(NotingChildError):
        freeze_parent_active_prefix(parent, "missing", multimodal)


def test_child_copies_frozen_root_tools_and_disables_memory_manager(native_parent):
    parent, _client = native_parent
    parent.tools = [{"type": "function", "function": {"name": "terminal", "parameters": {"type": "object"}}}]
    frozen = freeze_parent_runtime(parent)
    parent.tools.clear()
    parent._cached_system_prompt = "Later parent root"
    child = build_noting_child(parent, runtime_profile="NOTING", parent_conversation_ref=parent._secretary_conversation_ref,
                               frozen_runtime=frozen)
    try:
        assert child._cached_system_prompt == "Frozen parent root"
        assert child.tools == frozen["parity"].tools
        assert child.tools[0]["function"]["name"] == "terminal"
        assert "denied" in noting_dispatch_block(child, "terminal")
        assert child.compression_enabled is False
        assert child._memory_manager is None
    finally:
        child.close()


def test_successful_finish_cannot_commit_after_local_switch_off(native_parent, database, monkeypatch):
    parent, _client = native_parent
    original = build_noting_child
    def construct(*a, **kw):
        child = original(*a, **kw)
        def run(**kwargs):
            assert json.loads(notebook_maintain(child, create_args(database)))["success"]
            assert json.loads(finish_noting(child, {"reason": "Ready to commit"}))["success"]
            database.notebook_set_local_enabled(ref(database), False)
            return {"completed": True}
        child.run_conversation = run
        return child
    monkeypatch.setattr("secretary.noting_child.build_noting_child", construct)
    outcome = run_task(parent)
    assert outcome.committed is False
    assert outcome.status == "abandoned"
    assert database.notebook_current(ref(database)) is None
    assert active_noting_task_count() == 0
