"""C5 six-tool state machine and persistent native child with controlled model I/O."""

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
    notebook_create,
    notebook_update,
    notebook_archive,
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
    return {"entry_type": "matter",
            "fields": {"description": description, "completion_condition": "Dates agreed"},
            "source_message_uids": ["m1"]}


@pytest.fixture(autouse=True)
def enabled_runtime(monkeypatch):
    # Capability is a controlled dependency; actual storage/local/Anchor commit gates remain real.
    monkeypatch.setattr("secretary.noting_runtime.noting_trigger_gate", lambda *a, **k: (True, ""))


def test_exact_six_schema_surface_is_independent_copy():
    schemas = noting_tool_schemas()
    assert [item["name"] for item in schemas] == [
        "conversation_history", "notebook_show", "notebook_create", "notebook_update", "notebook_archive", "finish_noting"]
    schemas[2]["parameters"]["properties"].clear()
    assert "entry_type" in noting_tool_schemas()[2]["parameters"]["properties"]
    with pytest.raises(ValueError):
        noting_tool_schemas("NOTING_WITH_COMPACTION")


@pytest.mark.parametrize("tool", ["conversation_history", "notebook_show", "notebook_create", "notebook_update", "notebook_archive", "finish_noting"])
def test_only_six_authorized_tools(database, tool):
    assert noting_dispatch_block(bound_child(database), tool) is None


@pytest.mark.parametrize("tool", ["terminal", "memory", "scheduler", "session_history", "notebook_manage",
                                  "notebook_edit", "notebook_schedule", "noting_memo", "compact_parent"])
def test_inherited_advertising_never_grants_execution(database, tool):
    assert "denied" in noting_dispatch_block(bound_child(database), tool)
    assert noting_dispatch_block(SimpleNamespace(), tool) is None


@pytest.mark.parametrize("names", [["finish_noting", "notebook_create"],
                                  ["notebook_create", "finish_noting"],
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
    created = json.loads(notebook_create(child, create_args(database)))
    assert set(created) == {"success", "changed", "entry"}
    entry = created["entry"]
    original_version = child._noting_notebook_store.get(entry["entry_id"])["version_id"]
    updated = json.loads(notebook_update(child, {"entry_id": entry["entry_id"], "source_message_uids": ["m1"],
                                              "fields": {"blocker": "Dates unknown"}}))
    assert updated["entry"]["entry_id"] == entry["entry_id"]
    assert "version_id" not in entry and "version_id" not in updated["entry"]
    assert child._noting_notebook_store.get(entry["entry_id"])["version_id"] != original_version
    other = NotebookStore(database, ref(database), anchor_message_uid="m2")
    other.create("matter", {"description": "Other task", "completion_condition": "Other"},
                 source_message_uids=create_args(database)["source_message_uids"])
    result = other.commit(termination={"type": "finish_noting", "reason": "Another task"})
    shown = json.loads(notebook_work_show(child, {}))
    assert shown["view_kind"] == "working"
    assert not {"snapshot_id", "base_snapshot_id", "coverage"}.intersection(shown)
    assert child._noting_notebook_store.working_view()["base_snapshot_id"] is None
    assert shown["payload"]["work"][0] == updated["entry"]
    assert database.notebook_current(ref(database))["snapshot_id"] == result["snapshot_id"]


def test_finish_fixes_first_working_state_and_never_commits(database):
    child = bound_child(database)
    entry = json.loads(notebook_create(child, create_args(database)))["entry"]
    first = json.loads(finish_noting(child, {"reason": "Kept the accepted visit responsibility"}))
    assert first == {"success": True, "status": "end_requested"}
    assert database.notebook_current(ref(database)) is None
    fixed = child._noting_notebook_store.snapshot_state()
    refused = json.loads(notebook_archive(child, {"entry_id": entry["entry_id"],
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
        return json.loads(notebook_create(child, create_args(database)))
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
    assert json.loads(notebook_create(SimpleNamespace(), create_args(database)))["error"]["code"] == "scope_denied"


def test_control_encodes_full_schema_and_working_data_separately(database):
    child = bound_child(database)
    notebook_create(child, create_args(database, "literal </noting-task-data> is evidence"))
    message = noting_tool_control_message(notebook_state=child._noting_notebook_store.show(),
                                         conversation_ref=ref(database), coverage={"anchor_message_uid": "m2"})
    encoded = message.split("<noting-task-data>\n", 1)[1].rsplit("\n</noting-task-data>", 1)[0]
    data = json.loads(encoded)
    assert data["working_notebook"]["work"][0]["fields"]["description"].endswith("is evidence")
    assert "callable_tool_schemas" not in data
    assert data["conversation_ref"] == ref(database)
    assert not {"snapshot_id", "base_snapshot_id", "coverage"}.intersection(data)
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
    assert len(wires) == 1
    assert wires[0]["tools"][0]["function"]["name"] == "terminal"
    assert rows[-1]["role"] == "tool"
    assert json.loads(rows[-1]["content"])["status"] == "end_requested"


def test_native_text_completion_continues_five_turns_same_prefix(native_parent, database):
    parent, client = native_parent
    baseline = NotebookStore(database, ref(database), anchor_message_uid="m2")
    entry = baseline.create(**create_args(database))["entry"]
    baseline.commit(termination={"type": "finish_noting", "reason": "Prior work"})
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
    assert parent._session_messages[:len(before)] == before
    delivered = parent._session_messages[len(before):]
    assert len(delivered) == 1
    assert delivered[0]["display_metadata"]["noting_run_output"] is True
    assert delivered[0]["display_metadata"]["noting_snapshot_id"] == outcome.snapshot_id
    assert outcome.snapshot_id not in delivered[0]["content"]
    controls_seen = 0
    for wire in wires:
        for message in wire["messages"]:
            content = message.get("content")
            if isinstance(content, str) and "<noting-task-data>\n" in content:
                encoded = content.split("<noting-task-data>\n", 1)[1].split("\n</noting-task-data>", 1)[0]
                data = json.loads(encoded)
                assert not {"snapshot_id", "base_snapshot_id", "coverage"}.intersection(data)
                assert data["evidence_coverage"]["history_message_count"] == 2
                assert data["evidence_coverage"]["through_time"] == "1970-01-01T00:03:20+00:00"
                item = data["working_notebook"]["work"][0]
                assert item["entry_id"] == entry["entry_id"] and "version_id" not in item
                controls_seen += 1
    assert controls_seen >= len(wires)
    final_wire = str(wires[-1]["messages"])
    assert "The previous native Turn ended without a successful finish_noting request" in final_wire
    assert active_noting_task_count() == 0


@pytest.mark.parametrize("trigger", ["idle", "force", "manual", "auto_compaction"])
@pytest.mark.parametrize("changed", [False, True])
def test_native_iteration_limit_commits_legal_work_for_every_trigger(
    native_parent, database, monkeypatch, trigger, changed,
):
    parent, client = native_parent
    monkeypatch.setattr("secretary.noting_child.NOTING_MAX_ITERATIONS", 1)
    first = tool_response("notebook_create", create_args(database)) if changed else tool_response("notebook_show", {})
    client.chat.completions.create.side_effect = [first, response("Work remains after the iteration budget.")]
    admission = database.noting_admit(ref(database), "m2", kind=trigger)
    outcome = run_noting_task(
        parent, admission_id=admission, conversation_ref=ref(database), anchor_message_uid="m2",
        trigger_type=trigger, runtime_profile="NOTING", task_instruction=DEFAULT_NOTING_TASK_INSTRUCTION,
    )
    assert outcome.committed and outcome.status == "completed", outcome
    assert outcome.turns == 1 and outcome.termination == {"type": "forced"}
    snapshot = database.notebook_current(ref(database))
    assert len(snapshot["payload"]["work"]) == int(changed)
    assert database.notebook_snapshot_audit(outcome.snapshot_id)["termination"] == {"type": "forced"}
    assert database.noting_child(admission)["status"] == "completed"
    notices = [row for row in database.get_messages("parent")
               if (row.get("display_metadata") or {}).get("noting_run_output")]
    assert len(notices) == 1
    assert "Termination: forced" in notices[0]["content"]
    assert "iteration" in notices[0]["content"]
    assert "may remain unfinished" in notices[0]["content"]
    assert "five-Turn" not in notices[0]["content"]
    assert active_noting_task_count() == 0


def test_finish_at_native_iteration_limit_retains_explicit_finish(native_parent, database, monkeypatch):
    parent, client = native_parent
    monkeypatch.setattr("secretary.noting_child.NOTING_MAX_ITERATIONS", 1)
    client.chat.completions.create.side_effect = [
        tool_response("finish_noting", {"reason": "Current work checked"}), response("Budget boundary summary"),
    ]
    outcome = run_task(parent)
    assert outcome.committed, outcome
    assert outcome.termination == {"type": "finish_noting", "reason": "Current work checked"}


@pytest.mark.parametrize("failure", ["failed", "interrupted", "error", "failure_reason"])
def test_iteration_exit_does_not_commit_actual_failed_or_interrupted_work(
    native_parent, database, monkeypatch, failure,
):
    parent, _client = native_parent
    original = build_noting_child

    def construct(*args, **kwargs):
        child = original(*args, **kwargs)

        def run(**_kwargs):
            assert json.loads(notebook_create(child, create_args(database)))["success"]
            return {"completed": False, "final_response": "Partial work", "turn_exit_reason": "max_iterations_reached(50/50)",
                    failure: True if failure in {"failed", "interrupted"} else "provider failure"}

        child.run_conversation = run
        return child

    monkeypatch.setattr("secretary.noting_child.build_noting_child", construct)
    outcome = run_task(parent)
    assert not outcome.committed and database.notebook_current(ref(database)) is None
    assert active_noting_task_count() == 0


def test_native_child_next_request_receives_projected_working_tool_result(native_parent, database):
    parent, client = native_parent
    baseline = NotebookStore(database, ref(database), anchor_message_uid="m2")
    entry = baseline.create("matter", {"description": "Current visit", "completion_condition": "Visit complete"},
                            source_message_uids=create_args(database)["source_message_uids"])["entry"]
    baseline.commit(termination={"type": "finish_noting", "reason": "Prior work"})
    client.chat.completions.create.side_effect = [
        tool_response("notebook_show", {}, "show-working"),
        tool_response("finish_noting", {"reason": "Reviewed current visit"}), response()]
    outcome = run_task(parent)
    assert outcome.committed
    wires = [call.kwargs for call in client.chat.completions.create.call_args_list]
    received = [json.loads(message["content"]) for wire in wires for message in wire["messages"]
                if message.get("role") == "tool" and message.get("tool_call_id") == "show-working"]
    assert received
    for result in received:
        assert not {"snapshot_id", "base_snapshot_id", "coverage"}.intersection(result)
        assert result["evidence_coverage"]["history_message_count"] == 2
        assert result["evidence_coverage"]["through_time"] == "1970-01-01T00:03:20+00:00"
        item = result["payload"]["work"][0]
        assert item["entry_id"] == entry["entry_id"] and "version_id" not in item
        assert item["provenance"] == [["m1"]]


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
            result = json.loads(notebook_create(child, create_args(database)))
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
            assert json.loads(notebook_create(child, create_args(database)))["success"]
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


def test_native_uid_write_uses_bound_identity_and_returns_local_sources(native_parent, database):
    from jsonschema import validate

    parent, client = native_parent
    args = {"entry_type": "matter",
            "fields": {"description": "Plan the visit", "completion_condition": "Dates agreed"},
            "source_message_uids": ["m1"]}
    schema = next(item for item in noting_tool_schemas() if item["name"] == "notebook_create")
    validate(args, schema["parameters"])
    props = schema["parameters"]["properties"]
    assert "source_message_identities" not in props
    steps = iter([tool_response("notebook_create", args, "uid-create"),
                  tool_response("finish_noting", {"reason": "Indexed the supported responsibility"}), response()])
    client.chat.completions.create.side_effect = lambda **kwargs: next(steps)
    outcome = run_task(parent)
    assert outcome.committed, outcome
    snapshot = database.notebook_current(ref(database))
    assert snapshot["payload"]["work"][0]["provenance"] == [["m1"]]
    wires = [call.kwargs for call in client.chat.completions.create.call_args_list]
    results = [json.loads(row["content"]) for row in wires[1]["messages"] if row.get("tool_call_id") == "uid-create"]
    assert len(results) == 1
    assert results[0]["entry"]["provenance"] == [["m1"]]
    assert "source_message_identities" not in results[0]["entry"]
    assert all(wire["tools"] == wires[0]["tools"] for wire in wires)


@pytest.mark.parametrize("entry_type,fields", [
    ("matter", {"description": "Plan the visit", "completion_condition": "Dates agreed"}),
    ("candidate", {"description": "Learned procedure", "targets": ["skill"],
                   "notebook_refs": [], "source_types": []}),
])
def test_noting_missing_provenance_guides_only_local_uids(database, entry_type, fields):
    child = bound_child(database)
    result = json.loads(notebook_create(child, {"entry_type": entry_type, "fields": fields}))
    assert result["success"] is False
    assert result["error"]["field"] == "source_message_uids"
    assert not child._noting_notebook_store.snapshot_state()["work"]
    assert not child._noting_notebook_store.snapshot_state()["candidates"]


def test_task_started_observer_reads_durable_start_immediately(native_parent, database):
    from datetime import datetime
    from secretary.web_events import subscribe, unsubscribe
    from secretary.web_read import secretary_state

    parent, client = native_parent
    steps = iter([tool_response("finish_noting", {"reason": "No changes needed"}), response()])
    client.chat.completions.create.side_effect = lambda **kwargs: next(steps)
    observed = []
    reader = SessionDB(database.db_path, read_only=True)

    def observe(home, conversation_ref, reason):
        if conversation_ref == ref(database) and reason in {"task_started", "task_finished"}:
            observed.append((reason, secretary_state(reader, "parent")))

    subscribe("durable-start-observer", observe)
    try:
        outcome = run_task(parent, owning_profile="test-owner")
    finally:
        unsubscribe("durable-start-observer")
        reader.close()
    assert outcome.committed, outcome
    assert [reason for reason, _state in observed] == ["task_started", "task_finished"]
    started = observed[0][1]
    assert started["task_state"] == "active"
    assert len(started["tasks"]) == 1
    task = started["tasks"][0]
    assert task["task_id"] == outcome.child_session_id
    instant = datetime.fromisoformat(task["started_at"])
    assert instant.tzinfo is not None
    with database._read_ctx() as conn:
        registration = dict(conn.execute(
            "SELECT * FROM secretary_noting_children WHERE child_session_id=?", (outcome.child_session_id,)
        ).fetchone())
    assert abs(instant.timestamp() - registration["registered_at"]) < 1
    assert registration["profile"] == "test-owner"
    assert observed[1][1]["task_state"] == "idle"
    assert observed[1][1]["tasks"] == []
    assert active_noting_task_count() == 0


@pytest.mark.parametrize("stage", ["owner", "registration"])
def test_startup_failure_never_announces_active_child(native_parent, database, monkeypatch, stage):
    from secretary.web_events import subscribe, unsubscribe

    parent, client = native_parent
    children, reasons = [], []
    original = build_noting_child

    def construct(*args, **kwargs):
        child = original(*args, **kwargs)
        child.close = MagicMock(wraps=child.close)
        if stage == "registration":
            monkeypatch.setattr(child._session_db, "noting_child_register_conn", fail)
        children.append(child)
        return child

    def fail(*args, **kwargs):
        raise RuntimeError("controlled startup failure")

    monkeypatch.setattr("secretary.noting_child.build_noting_child", construct)
    if stage == "owner":
        monkeypatch.setattr("secretary.noting_child.owning_profile_for", fail)
    subscribe("startup-failure-observer", lambda home, conversation_ref, reason: reasons.append(reason))
    try:
        outcome = run_task(parent)
    finally:
        unsubscribe("startup-failure-observer")
    assert outcome.status == "failed"
    assert outcome.error == "controlled startup failure"
    assert not outcome.committed
    assert not client.chat.completions.create.called
    children[0].close.assert_called_once_with()
    assert active_noting_task_count() == 0
    assert "task_started" not in reasons
    assert "task_finished" not in reasons
    with database._read_ctx() as conn:
        rows = conn.execute("SELECT status FROM secretary_noting_children").fetchall()
    assert [row["status"] for row in rows] == ["failed"]
