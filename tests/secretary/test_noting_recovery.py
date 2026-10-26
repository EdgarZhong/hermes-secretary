"""Recovery over real native child/Notebook/commit persistence; only model I/O is controlled."""
import json
import time

import pytest

from secretary.noting_recovery import _WORKERS, recovery_state, start_recovery
from secretary.noting_recovery_sources import NotingRecoveryError, reconstruct_noting
from tests.secretary.test_r3_child import (
    database as database, enabled_runtime as enabled_runtime, native_parent as native_parent,
    create_args, ref, response, run_task, tool_response,
)


def failed_task(native_parent, database):
    parent, client = native_parent
    client.chat.completions.create.side_effect = [
        tool_response("notebook_create", create_args(database), "create"),
        tool_response("finish_noting", {"reason": "Retained responsibility"}), response("Done"),
    ]
    def fail(_child):
        raise RuntimeError("Interrupted before Snapshot publication")
    outcome = run_task(parent, state_provider=fail)
    assert outcome.status == "failed" and not outcome.committed
    return outcome


def wait_recovery(db, failed, request="r1"):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        state = recovery_state(db, ref(db), failed.child_session_id, request)
        if state["status"] not in {"queued", "running"}:
            worker = _WORKERS.get((str(db.db_path.resolve()), state["operation_id"]))
            if worker is not None:
                worker.join(timeout=3)
            return state
        time.sleep(.01)
    pytest.fail("Recovery worker did not terminate")


def factory(parent):
    def build(db, recovered):
        from tests.secretary.test_noting_child import make_agent
        agent = make_agent(parent.session_id, db)
        agent.client = parent.client
        return agent
    return build


def test_failed_immutable_work_and_original_prefix_are_reconstructed(native_parent, database):
    failed = failed_task(native_parent, database)
    initial = reconstruct_noting(database, ref(database), failed.child_session_id)
    assert [row["message_uid"] for row in initial.prefix] == ["m1", "m2"]
    assert initial.root == "Frozen parent root"
    assert initial.tools[0]["function"]["name"] == "terminal"
    assert initial.working_state["work"][0]["fields"]["description"] == "Plan the visit"
    assert initial.working_state["work"][0]["version_id"] == "1"
    assert database.notebook_current(ref(database)) is None
    # Later Main changes never replace a failed task's frozen input.
    database.append_message("parent", "user", "Later private evidence", message_uid="m3")
    database.update_system_prompt("parent", "Current root")
    database.update_session_tool_names("parent", {"tools": []})
    later = reconstruct_noting(database, ref(database), failed.child_session_id)
    assert later.prefix == initial.prefix
    assert later.root == initial.root and later.tools == initial.tools
    assert later.working_state == initial.working_state


def test_async_native_recovery_commits_preserved_versions_to_current_tail(native_parent, database, monkeypatch):
    parent, client = native_parent
    failed = failed_task(native_parent, database)
    old = database.get_session(failed.child_session_id)
    old_messages = database.get_messages_as_conversation(failed.child_session_id)
    old_registry = database.noting_child(1)
    database.append_message("parent", "user", "After the failed task", message_uid="later")
    before = database.get_messages_as_conversation("parent")
    client.chat.completions.create.reset_mock()
    client.chat.completions.create.side_effect = [tool_response("notebook_show", {}, "show"),
                                               tool_response("finish_noting", {"reason": "Resumed saved work"}), response("Done")]
    made = []
    from secretary.noting_child import build_noting_child
    def capture(*args, **kwargs):
        child = build_noting_child(*args, **kwargs)
        made.append(child)
        return child
    monkeypatch.setattr("secretary.noting_child.build_noting_child", capture)
    ack = start_recovery(database, ref(database), failed.child_session_id, "r1", parent_factory=factory(parent))
    state = wait_recovery(database, failed)
    assert state["committed"], state
    assert state["status"] == "completed"
    assert state["operation_id"] == ack["operation_id"]
    snapshot = database.notebook_current(ref(database))
    assert snapshot["payload"]["work"][0]["version_id"] == "1"
    assert snapshot["payload"]["work"][0]["entry_id"] == "1"
    assert snapshot["anchor_message_uid"] == "m2"
    after = database.get_messages_as_conversation("parent")
    assert after[:len(before)] == before
    assert after[-1]["display_metadata"]["noting_snapshot_id"] == state["snapshot_id"]
    assert "later" not in {row.get("message_uid") for row in made[0]._session_messages or []}
    wires = [call.kwargs for call in client.chat.completions.create.call_args_list]
    assert all("callable_tool_schemas" not in str(wire["messages"]) for wire in wires)
    assert all("tools" not in row for wire in wires for row in wire["messages"])
    assert wires[0]["messages"][0]["content"] == "Frozen parent root"
    assert "After the failed task" not in str(wires)
    assert wires[0]["tools"][0]["function"]["name"] == "terminal"
    assert database.get_session(failed.child_session_id) == old
    assert database.get_messages_as_conversation(failed.child_session_id) == old_messages
    assert database.noting_child(1) == old_registry
    assert made[0].client is None and made[0]._owns_session_db is False
    assert database.get_session(state["child_session_id"])["end_reason"]
    repeat = start_recovery(database, ref(database), failed.child_session_id, "r1", parent_factory=factory(parent))
    assert repeat == state
    assert client.chat.completions.create.call_count == 2
    durable = database.get_messages_as_conversation(state["child_session_id"])
    assert durable[-1]["role"] == "tool"
    assert json.loads(durable[-1]["content"]) == {"success": True, "status": "end_requested"}


def _legacy_control_schemas(monkeypatch):
    """Model an existing pre-fixed-tools task, without changing the current builder."""
    from secretary import noting_tools
    from secretary.noting_tools import noting_tool_schemas
    original = noting_tools.noting_tool_control_message

    def legacy(*args, **kwargs):
        content = original(*args, **kwargs)
        prefix, data = content.split("<noting-task-data>\n", 1)
        encoded, suffix = data.split("\n</noting-task-data>", 1)
        payload = json.loads(encoded)
        payload["callable_tool_schemas"] = noting_tool_schemas()
        return prefix + "<noting-task-data>\n" + json.dumps(payload) + "\n</noting-task-data>" + suffix

    monkeypatch.setattr(noting_tools, "noting_tool_control_message", legacy)


def test_original_control_tools_allow_recovery_without_full_parent_pin(native_parent, database, monkeypatch):
    _legacy_control_schemas(monkeypatch)
    failed = failed_task(native_parent, database)
    database.update_session_tool_names(failed.child_session_id, None)
    recovered = reconstruct_noting(database, ref(database), failed.child_session_id)
    assert recovered.sources["tools"] == "original_control_callable_schemas_parent_array_unavailable"
    assert {tool["function"]["name"] for tool in recovered.tools} == {"conversation_history", "notebook_show", "notebook_create", "notebook_update", "notebook_archive", "finish_noting"}


def test_new_prelude_is_not_accepted_as_old_tools(native_parent, database, monkeypatch):
    _legacy_control_schemas(monkeypatch)
    failed = failed_task(native_parent, database)
    database.update_session_tool_names(failed.child_session_id, None)
    database.capture_secretary_prelude("parent", "new root", [])
    recovered = reconstruct_noting(database, ref(database), failed.child_session_id)
    assert recovered.sources["tools"] == "original_control_callable_schemas_parent_array_unavailable"
    assert len(recovered.tools) == 6


def test_foreign_conversation_cannot_borrow_failed_child(native_parent, database):
    failed = failed_task(native_parent, database)
    database.create_session("foreign", source="test")
    with pytest.raises(NotingRecoveryError, match="Conversation"):
        reconstruct_noting(database, database.resolve_conversation_ref("foreign"), failed.child_session_id)


def test_worker_build_failure_releases_resources_keeps_failed_registration(native_parent, database):
    failed = failed_task(native_parent, database)
    original = database.noting_child(1)
    def broken(db, recovered):
        raise RuntimeError("Target Provider unavailable")
    start_recovery(database, ref(database), failed.child_session_id, "r1", parent_factory=broken)
    state = wait_recovery(database, failed)
    assert state["status"] == "failed" and "Target Provider" in state["error"]
    assert database.noting_child(1) == original
    assert not _WORKERS
    with database._read_ctx() as conn:
        assert conn.execute("SELECT count(*) FROM session_turn_leases").fetchone()[0] == 0


def test_orphan_tool_call_is_repaired_by_native_turn_not_faked(native_parent, database):
    parent, client = native_parent
    failed = failed_task(native_parent, database)
    database.append_message(failed.child_session_id, "assistant", "", tool_calls=[
        {"id": "not_executed", "type": "function", "function": {"name": "notebook_create", "arguments": json.dumps(create_args(database, "Never executed"))}}])
    client.chat.completions.create.reset_mock()
    client.chat.completions.create.side_effect = [tool_response("finish_noting", {"reason": "Existing view checked"}), response("Done")]
    start_recovery(database, ref(database), failed.child_session_id, "r1", parent_factory=factory(parent))
    state = wait_recovery(database, failed)
    assert state["committed"], state
    assert len(database.notebook_current(ref(database))["payload"]["work"]) == 1
    rows = database.get_messages_as_conversation(state["child_session_id"])
    assert not any(row.get("role") == "tool" and row.get("tool_call_id") == "not_executed" for row in rows)


def test_compaction_after_failure_restores_archived_parent_interval(native_parent, database):
    failed = failed_task(native_parent, database)
    database.archive_and_compact("parent", [{"role": "user", "content": "Newer compacted summary",
                                           "_compressed_summary": True, "message_uid": "boundary"}])
    database.append_message("parent", "user", "After compaction", message_uid="newer")
    recovered = reconstruct_noting(database, ref(database), failed.child_session_id)
    assert [row["message_uid"] for row in recovered.prefix] == ["m1", "m2"]
    assert recovered.working_state["work"][0]["entry_id"] == "1"


def test_rebound_registry_keeps_original_failed_child_recoverable(native_parent, database):
    failed = failed_task(native_parent, database)
    database.create_session("later-recovery", source="subagent", parent_session_id="parent",
                            model_config={"_delegate_from": "parent"})
    database.noting_child_register(1, child_session_id="later-recovery", profile=None)
    database.noting_child_finish(1, status="completed")
    recovered = reconstruct_noting(database, ref(database), failed.child_session_id)
    assert recovered.admission["admission_id"] == 1
    assert recovered.working_state["work"][0]["entry_id"] == "1"


def test_admitted_compaction_interval_excludes_earlier_full_history(native_parent, database):
    from secretary.noting_child import run_noting_task
    from secretary.noting_prompts import DEFAULT_NOTING_TASK_INSTRUCTION
    parent, client = native_parent
    database.archive_and_compact("parent", [{"role": "user", "content": "Older work summarized",
                                           "_compressed_summary": True, "message_uid": "boundary"}])
    database.append_message("parent", "user", "Active interval request", message_uid="m3")
    database.append_message("parent", "assistant", "Active interval answer", message_uid="m4")
    parent._session_messages = database.get_messages_as_conversation("parent", repair_alternation=True)
    admission = database.noting_admit(ref(database), "m4", kind="manual")
    client.chat.completions.create.side_effect = [tool_response("finish_noting", {"reason": "No changes"}), response("done")]
    def fail(_):
        raise RuntimeError("Publication failure")
    failed = run_noting_task(parent, admission_id=admission, conversation_ref=ref(database),
                             anchor_message_uid="m4", trigger_type="manual", runtime_profile="NOTING",
                             task_instruction=DEFAULT_NOTING_TASK_INSTRUCTION, state_provider=fail)
    database.archive_and_compact("parent", [{"role": "user", "content": "Later summary",
                                           "_compressed_summary": True, "message_uid": "later-boundary"}])
    recovered = reconstruct_noting(database, ref(database), failed.child_session_id)
    assert [row["message_uid"] for row in recovered.prefix] == ["boundary", "m3", "m4"]
    assert "Plan a visit" not in str(recovered.prefix)


def test_successful_archive_replay_does_not_revive_removed_entry(native_parent, database):
    parent, client = native_parent
    client.chat.completions.create.side_effect = [
        tool_response("notebook_create", create_args(database, "Transient"), "first"),
        tool_response("notebook_create", create_args(database, "Keep this"), "second"),
        tool_response("notebook_archive", { "entry_id": "1", "reason": "Not needed"}, "archive"),
        tool_response("finish_noting", {"reason": "Complete"}), response("Done"),
    ]
    def fail(_):
        raise RuntimeError("Publication failure")
    failed = run_task(parent, state_provider=fail)
    recovered = reconstruct_noting(database, ref(database), failed.child_session_id)
    active = [entry for entry in recovered.working_state["work"] if not entry["archived"]]
    assert [entry["entry_id"] for entry in active] == ["2"]
    assert active[0]["fields"]["description"] == "Keep this"
    assert [entry["entry_id"] for entry in recovered.working_state["work"] if entry["archived"]] == ["1"]


def test_concurrent_same_request_runs_only_one_native_child(native_parent, database):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    parent, client = native_parent
    failed = failed_task(native_parent, database)
    entered, release = Event(), Event()
    steps = iter([tool_response("finish_noting", {"reason": "Recovered"}), response("Done")])
    calls = []
    def sdk(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            entered.set()
            assert release.wait(5)
        return next(steps)
    client.chat.completions.create.side_effect = sdk
    first = start_recovery(database, ref(database), failed.child_session_id, "r1", parent_factory=factory(parent))
    assert entered.wait(5)
    try:
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(lambda _: start_recovery(database, ref(database), failed.child_session_id,
                                                              "r1", parent_factory=factory(parent)), range(4)))
        assert {result["operation_id"] for result in results} == {first["operation_id"]}
    finally:
        release.set()
    assert wait_recovery(database, failed)["committed"]
    assert len(calls) == 1


def test_missing_original_anchor_reports_which_source_is_missing(native_parent, database):
    failed = failed_task(native_parent, database)
    database.replace_messages("parent", [{"role": "user", "content": "Replacement discussion", "message_uid": "new"}])
    with pytest.raises(NotingRecoveryError, match="Anchor message: m2"):
        reconstruct_noting(database, ref(database), failed.child_session_id)


def test_cold_completion_uses_main_native_lease_without_blocking_model_recovery(native_parent, database, monkeypatch):
    from threading import Event
    from run_agent import AIAgent
    parent, client = native_parent
    failed = failed_task(native_parent, database)
    finished_model = Event()
    original_run = AIAgent.run_conversation
    def run(agent, *args, **kwargs):
        result = original_run(agent, *args, **kwargs)
        if getattr(agent, "_secretary_noting_child", False):
            assert result["completed"] and result["turn_exit_reason"] == "noting_finished"
            durable = database.get_messages_as_conversation(agent.session_id)
            assert durable[-1]["role"] == "tool"
            assert json.loads(durable[-1]["content"]) == {"success": True, "status": "end_requested"}
            finished_model.set()
        return result
    monkeypatch.setattr(AIAgent, "run_conversation", run)
    client.chat.completions.create.side_effect = [tool_response("finish_noting", {"reason": "Recovered"})]
    assert database.acquire_session_turn_lease("parent", "main-current", wait_seconds=0)
    try:
        start_recovery(database, ref(database), failed.child_session_id, "r1", parent_factory=factory(parent))
        assert finished_model.wait(5), "Recovery incorrectly waited for Main before running the child"
        database.append_messages_batch("parent", [{"role": "assistant", "content": "Current Main finished"}],
                                       turn_lease_holder="main-current")
        assert database.notebook_current(ref(database)) is None
    finally:
        database.release_session_turn_lease("parent", "main-current")
    state = wait_recovery(database, failed)
    assert state["committed"], state
    rows = database.get_messages_as_conversation("parent")
    assert rows[-2]["content"] == "Current Main finished"
    assert rows[-1]["display_metadata"]["noting_snapshot_id"] == state["snapshot_id"]


def test_branch_recovery_keeps_branch_path_and_rebinds_inherited_source_identity(native_parent, database):
    from secretary.noting_child import run_noting_task
    from secretary.noting_prompts import DEFAULT_NOTING_TASK_INSTRUCTION
    from tests.secretary.test_noting_child import make_agent
    _parent, client = native_parent
    database.create_session("branch", source="test", parent_session_id="parent", model_config={"_branched_from": "parent"},
                            branch_point_message_uid="m1")
    branch_ref = database.resolve_conversation_ref("branch")
    database.append_message("branch", "user", "Branch request", message_uid="b1")
    database.append_message("branch", "assistant", "Branch answer", message_uid="b2")
    branch = make_agent("branch", database)
    branch.client = client
    branch._secretary_conversation_ref = branch_ref
    branch._cached_system_prompt = "Branch original root"
    with database._read_ctx() as conn:
        source = database._foreground_source_rows_conn(conn, branch_ref)
        prefix = database._rows_to_conversation(source, session_id="branch", include_ancestors=False, repair_alternation=False)
    branch._session_messages = prefix
    admission = database.noting_admit(branch_ref, "b2", kind="manual")
    args = {"entry_type": "matter", "fields": {"description": "Branch work", "completion_condition": "Done"},
            "source_message_uids": ["m1"]}
    client.chat.completions.create.side_effect = [tool_response("notebook_create", args),
                                               tool_response("finish_noting", {"reason": "Kept branch"}), response("done")]
    def fail(_):
        raise RuntimeError("Publication failure")
    try:
        failed = run_noting_task(branch, admission_id=admission, conversation_ref=branch_ref,
                                 anchor_message_uid="b2", trigger_type="manual", runtime_profile="NOTING",
                                 task_instruction=DEFAULT_NOTING_TASK_INSTRUCTION, state_provider=fail)
        database.append_message("parent", "user", "Other branch later evidence", message_uid="foreign-tail")
        recovered = reconstruct_noting(database, branch_ref, failed.child_session_id)
        assert [row["message_uid"] for row in recovered.prefix] == ["m1", "b1", "b2"]
        assert recovered.working_state["work"][0]["provenance"] == [["m1"]]
        assert "Other branch later evidence" not in str(recovered.prefix)
    finally:
        branch._end_session_on_close = False
        branch.release_clients()


def test_base_snapshot_matches_original_view_instead_of_latest_created_snapshot(native_parent, database):
    from secretary.notebook_store import NotebookStore
    first = NotebookStore(database, ref(database), anchor_message_uid="m2")
    first.create(**create_args(database, "Existing responsibility"))
    expected = first.commit(termination={"type": "finish_noting", "reason": "Existing"})
    older = NotebookStore(database, ref(database), anchor_message_uid="m1", base_snapshot_id=None)
    unrelated = older.commit(termination={"type": "finish_noting", "reason": "Late older coverage"})
    assert unrelated["pointer_changed"] is False
    failed = failed_task(native_parent, database)
    recovered = reconstruct_noting(database, ref(database), failed.child_session_id)
    assert recovered.base_snapshot_id == expected["snapshot_id"]
    assert [entry["entry_id"] for entry in recovered.working_state["work"]] == ["1", "2"]


def test_other_tools_json_entry_is_not_replayed_as_a_maintenance_receipt(native_parent, database):
    from secretary.notebook_store import NotebookStore
    failed = failed_task(native_parent, database)
    other = NotebookStore(database, ref(database), anchor_message_uid="m2")
    unrelated = other.create(**create_args(database, "Other task work"))
    database.append_message(failed.child_session_id, "tool", json.dumps(unrelated),
                            tool_name="conversation_history", tool_call_id="other-read")
    recovered = reconstruct_noting(database, ref(database), failed.child_session_id)
    assert [entry["entry_id"] for entry in recovered.working_state["work"]] == ["1"]


def test_worker_native_construction_and_turn_keep_session_identity_task_local(native_parent, database, monkeypatch):
    import os
    from gateway.session_context import get_session_env, scoped_current_session_id
    parent, client = native_parent
    failed = failed_task(native_parent, database)
    monkeypatch.setenv("HERMES_SESSION_ID", "other-process-main-identity")
    identities = []
    steps = iter([tool_response("finish_noting", {"reason": "Recovered"}), response("Done")])
    def sdk(**kwargs):
        identities.append(get_session_env("HERMES_SESSION_ID"))
        return next(steps)
    client.chat.completions.create.side_effect = sdk
    with scoped_current_session_id("request-task-main"):
        ack = start_recovery(database, ref(database), failed.child_session_id, "r1", parent_factory=factory(parent))
        state = wait_recovery(database, failed)
        assert state["committed"], state
        assert identities == [ack["operation_id"]]
        assert get_session_env("HERMES_SESSION_ID") == "request-task-main"
    assert os.environ["HERMES_SESSION_ID"] == "other-process-main-identity"


@pytest.mark.parametrize("complete_pin", [False, True, "stale"],
                         ids=["legacy-tools-upgraded", "fixed-tools-unchanged", "same-name-contracts-refreshed"])
def test_recovery_constructs_fixed_tools_before_freeze_and_preserves_failed_records(
        native_parent, database, monkeypatch, complete_pin):
    from copy import deepcopy
    from secretary import noting_child
    from secretary.noting_tools import noting_tool_schemas

    parent, client = native_parent
    canonical = noting_tool_schemas()
    if complete_pin:
        parent.tools += [{"type": "function", "function": schema} for schema in canonical]
    expected = deepcopy(parent.tools)
    if not complete_pin:
        expected += [{"type": "function", "function": schema} for schema in canonical
                     if schema["name"] not in {tool["function"]["name"] for tool in expected}]
    if complete_pin == "stale":
        for tool in parent.tools[1:]:
            tool["function"]["description"] = "Historical definition of " + tool["function"]["name"]
            if tool["function"]["name"] in {"notebook_create", "notebook_update"}:
                properties = tool["function"]["parameters"]["properties"]
                properties.pop("done", None)
                properties["status"] = {"type": "string"}
                properties.pop("source_time_ranges", None)
                properties["source_time_range"] = {"type": "object"}
    failed = failed_task(native_parent, database)
    original_session = database.get_session(failed.child_session_id)
    original_rows = database.get_messages_as_conversation(failed.child_session_id)
    recovered = reconstruct_noting(database, ref(database), failed.child_session_id)
    assert recovered.sources["tools"] == "failed_child.tool_names"
    assert "callable_tool_schemas" not in str(original_rows)
    source_pin = deepcopy(recovered.tools)
    pairs, children = [], []
    native_freeze = noting_child.freeze_parent_runtime
    native_build = noting_child.build_noting_child

    def freeze(agent):
        frozen = native_freeze(agent)
        pairs.append((deepcopy(agent.tools), deepcopy(frozen["parity"].tools)))
        return frozen

    def build(*args, **kwargs):
        child = native_build(*args, **kwargs)
        children.append(child)
        return child

    monkeypatch.setattr(noting_child, "freeze_parent_runtime", freeze)
    monkeypatch.setattr(noting_child, "build_noting_child", build)
    client.chat.completions.create.reset_mock()
    client.chat.completions.create.side_effect = [tool_response("notebook_show", {}, "show"),
        tool_response("finish_noting", {"reason": "Reviewed recovered working state"}), response("Done")]
    ack = start_recovery(database, ref(database), failed.child_session_id, "r1", parent_factory=factory(parent))
    state = wait_recovery(database, failed)
    assert state["committed"], state
    assert children[0]._secretary_noting_parent_tools == expected
    assert all(left == right == expected for left, right in pairs)
    wires = [call.kwargs for call in client.chat.completions.create.call_args_list]
    assert all(wire["tools"] == expected for wire in wires)
    assert all("tools" not in row for wire in wires for row in wire["messages"])
    assert all("callable_tool_schemas" not in str(wire["messages"]) for wire in wires)
    if complete_pin is True:
        assert expected == source_pin
        assert state["sources"]["tools"] == "failed_child.tool_names"
        assert set(state["sources"]) == {"parent", "root", "tools", "notebook"}
    elif complete_pin == "stale":
        assert expected != source_pin
        assert "refreshed_canonical=" + ",".join(schema["name"] for schema in canonical) in state["sources"]["tools"]
        assert "historical_tools_prefix_not_byte_identical" in state["sources"]["tools"]
        assert json.loads(database.get_session(state["child_session_id"])["tool_names"])["tools"] == expected
    else:
        assert state["sources"]["tools"].startswith("failed_child.tool_names+fixed_noting_maintenance_definitions")
        assert "(conversation_history,notebook_show,notebook_create,notebook_update,notebook_archive,finish_noting)" in state["sources"]["tools"]
        assert "not_byte_identical" in state["sources"]["tools"]
        assert set(state["sources"]) == {"parent", "root", "tools", "notebook"}
    assert ack["sources"] == state["sources"]
    assert database.get_session(failed.child_session_id) == original_session
    assert database.get_messages_as_conversation(failed.child_session_id) == original_rows
    assert reconstruct_noting(database, ref(database), failed.child_session_id).tools == source_pin
    assert start_recovery(database, ref(database), failed.child_session_id, "r1", parent_factory=factory(parent)) == state
    assert len(wires) == 2
    durable = database.get_messages_as_conversation(state["child_session_id"])
    assert durable[-1]["role"] == "tool"
    assert json.loads(durable[-1]["content"]) == {"success": True, "status": "end_requested"}


def test_recovery_preserves_archival_relation_cleanup_receipts_without_replaying_writes(native_parent, database):
    parent, client = native_parent
    client.chat.completions.create.side_effect = [
        tool_response("notebook_create", create_args(database, "Temporary scope"), "one"),
        tool_response("notebook_create", {**create_args(database, "Retained responsibility"),
            "relations": [{"kind": "related_to", "entry_id": "1"}]}, "two"),
        tool_response("notebook_archive", {"entry_id": "1", "reason": "Temporary scope is no longer needed"}, "archive"),
        tool_response("finish_noting", {"reason": "Preserved the separate responsibility"}), response(),
    ]
    def unavailable(_):
        raise RuntimeError("Controlled failure before publication")
    failed = run_task(parent, state_provider=unavailable)
    assert not failed.committed
    rows = database.get_messages_as_conversation(failed.child_session_id)
    receipt = next(json.loads(row["content"]) for row in rows if row.get("tool_call_id") == "archive")
    retained = receipt["updated_entries"][0]
    assert retained["entry_id"] == "2" and retained["relations"] == []
    assert "source_message_identities" not in retained
    before = [tuple(row) for row in database._read_all("SELECT * FROM secretary_notebook_item ORDER BY id")]
    recovered = reconstruct_noting(database, ref(database), failed.child_session_id)
    active = [entry for entry in recovered.working_state["work"] if not entry["archived"]]
    archived = [entry for entry in recovered.working_state["work"] if entry["archived"]]
    assert len(active) == len(archived) == 1
    assert active[0]["entry_id"] == retained["entry_id"] and active[0]["version_id"]
    assert archived[0]["entry_id"] == "1" and archived[0]["fields"]["processing_note"] == "Temporary scope is no longer needed"
    assert "version_id" not in retained
    assert active[0]["relations"] == []
    assert before == [tuple(row) for row in database._read_all("SELECT * FROM secretary_notebook_item ORDER BY id")]
