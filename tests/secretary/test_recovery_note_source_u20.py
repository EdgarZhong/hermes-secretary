"""C-R5: recovery source audit through native compression, real Noting Loop and RPC."""

import json
import threading
import time
from pathlib import Path

import httpx
import pytest
from openai import BadRequestError

from secretary.noting_notes import _path, check_note_delivery, select_note_conn
from secretary.noting_recovery import recovery_state, _WORKERS
from secretary.noting_recovery_sources import reconstruct_noting
from secretary.noting_scope import bind_main_runtime
from hermes_state import SessionDB
from tests.agent.test_context_compaction_request import _summary
from tests.secretary.test_joint_noting_u20 import admissions, compress_async, notes, wait_for
from tests.secretary.test_noting_child import _tool_response, mock_response, make_agent

pytest_plugins = ["tests.secretary.test_noting_child", "tests.secretary.test_joint_noting_u20"]


def reject():
    return BadRequestError("Controlled terminal SDK rejection", response=httpx.Response(
        400, request=httpx.Request("POST", "https://example.invalid/v1/chat/completions")),
        body={"error": {"type": "invalid_request_error", "message": "Controlled terminal SDK rejection"}})


def rpc_setup(parent, db, monkeypatch):
    from tui_gateway import server
    monkeypatch.setattr(server, "_get_db", lambda: db)
    monkeypatch.setattr(server, "_profile_home", lambda name: Path(db.db_path).parent if name == "target" else None)
    def build(sid, key, **kwargs):
        agent = make_agent(key, kwargs["session_db"])
        agent.side_agent = kwargs.get("side_agent", False)
        return agent
    monkeypatch.setattr(server, "_make_agent", build)
    return server


def rpc_recover(server, ref, child_id, request):
    return server.handle_request({"jsonrpc": "2.0", "id": request, "method": "secretary.noting_recover",
        "params": {"profile": "target", "conversation_ref": ref,
                   "failed_child_session_id": child_id, "request_id": request}})


def await_recovery(db, ref, child_id, request):
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        state = recovery_state(db, ref, child_id, request)
        if state["status"] not in {"queued", "running"}:
            worker = _WORKERS.get((str(db.db_path.resolve()), state["operation_id"]))
            if worker is not None:
                worker.join(3)
            return state
        time.sleep(.01)
    raise AssertionError("Actual recovery worker did not terminate")


def current_path(db, ref):
    with db._read_ctx() as conn:
        position, boundary, last = _path(db, conn, ref)
        full = db.get_full_foreground_conn(conn, ref)
        return {"positions": position, "boundary": boundary, "latest_boundary": last,
                "full": [{key: row.get(key) for key in ("message_uid", "id", "path_position", "is_compaction")}
                         for row in full if row.get("message_identity")]}


def failed_carried_task(runtime, monkeypatch):
    parent, db, client, children = runtime
    ref = parent._secretary_conversation_ref
    config = Path(db.db_path).with_name("config.yaml")
    config.write_text("noting:\n  enabled: false\n")
    monkeypatch.setattr(parent.context_compressor, "compress", _summary)
    first, result, errors = compress_async(parent, force=True)
    first.join(10)
    assert not first.is_alive() and not errors and admissions(db) == []
    parent._session_messages = result[0][0]
    config.write_text("noting:\n  enabled: true\n  idle:\n    enabled: false\n")
    summary_entered, summary_release = threading.Event(), threading.Event()
    calls = []
    def failing_provider(**kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            return _tool_response("notebook_create", {"entry_type": "matter", "fields": {
                "description": "Valid work from the carried source", "completion_condition": "Reviewed"},
                "source_message_uids": [admissions(db)[-1]["anchor_message_uid"]]}, "create")
        raise reject()
    client.chat.completions.create.side_effect = failing_provider
    def failed_summary(messages, **kwargs):
        summary_entered.set()
        assert summary_release.wait(30)
        raise RuntimeError("Controlled native attempt failure after Noting terminal failure")
    monkeypatch.setattr(parent.context_compressor, "compress", failed_summary)
    second, _result, errors = compress_async(parent, force=True)
    try:
        assert summary_entered.wait(10)
        wait_for(lambda: len(children) == 1)
        children[0].join(25)
        assert not children[0].is_alive()
        original = admissions(db)[0]
        assert original["state"] == "failed"
        child_id = db.noting_child(original["admission_id"])["child_session_id"]
    finally:
        summary_release.set()
        second.join(10)
    assert errors and db.notebook_current(ref) is None and notes(db, ref) == []
    reconstructed = reconstruct_noting(db, ref, child_id)
    path_before = current_path(db, ref)
    assert original["compression_interval_id"] == db._noting_publication_interval(path_before["latest_boundary"])
    assert reconstructed.admission["compression_interval_id"] == original["compression_interval_id"]
    assert reconstructed.prefix[-1]["message_uid"] == original["anchor_message_uid"]
    assert reconstructed.working_state["work"][0]["fields"]["description"] == "Valid work from the carried source"
    return original, child_id


def recover_task(runtime, monkeypatch, child_id, request):
    parent, db, client, _children = runtime
    client.chat.completions.create.side_effect = [
        _tool_response("finish_noting", {"reason": "Explicitly recovered the failed legal task"}, "recover-finish"),
        mock_response("Finished.")]
    server = rpc_setup(parent, db, monkeypatch)
    ack = rpc_recover(server, parent._secretary_conversation_ref, child_id, request)
    assert "error" not in ack, ack
    return await_recovery(db, parent._secretary_conversation_ref, child_id, request)


def actual_notes(parent, db):
    return [row for row in db.get_messages(parent.session_id)
            if (row.get("display_metadata") or {}).get("noting_snapshot_id")]


def next_native_boundary(runtime, monkeypatch):
    parent, db, client, children = runtime
    # The next source task explicitly fails; the native writer remains real.
    client.chat.completions.create.side_effect = lambda **kwargs: (_ for _ in ()).throw(reject())
    monkeypatch.setattr(parent.context_compressor, "compress", _summary)
    native, result, errors = compress_async(parent, force=True)
    native.join(10)
    assert not native.is_alive() and not errors
    parent._session_messages = result[0][0]
    for child in children:
        child.join(10)
        assert not child.is_alive()


@pytest.mark.parametrize("legacy", [False, True])
def test_current_interval_recovery_is_excluded_then_next_native_boundary_delivers_once(runtime, monkeypatch, legacy):
    parent, db, _client, _children = runtime
    ref = parent._secretary_conversation_ref
    original, child_id = failed_carried_task(runtime, monkeypatch)
    child_before = db.noting_child(original["admission_id"])
    from secretary import noting_child
    publish = noting_child._publish_committed_completion
    publication_observed = []
    def before_session_audit(child, conversation, termination, outcome):
        config = json.loads(db.get_session(child.session_id)["model_config"])["_noting_recovery"]
        assert not config.get("committed") and not config.get("snapshot_id")
        with db._read_ctx() as conn:
            assert select_note_conn(db, conn, ref) is None
        publication_observed.append(outcome.snapshot_id)
        return publish(child, conversation, termination, outcome)
    monkeypatch.setattr(noting_child, "_publish_committed_completion", before_session_audit)
    state = recover_task(runtime, monkeypatch, child_id, "source-proof")
    assert publication_observed == [state["snapshot_id"]]
    assert state["committed"], state
    snapshot_id = state["snapshot_id"]
    audit = db.notebook_snapshot_audit(snapshot_id)
    assert audit["termination"]["noting_origin"] == {
        "admission_id": original["admission_id"], "compression_interval_id": original["compression_interval_id"],
        "recovery_session_id": state["child_session_id"]}
    assert db.notebook_current(ref)["snapshot_id"] == snapshot_id
    assert db.noting_admission(original["admission_id"]) == original
    assert db.noting_child(original["admission_id"]) == child_before
    assert notes(db, ref) == [] and actual_notes(parent, db) == []
    if legacy:
        # Prepare a pre-C-R5 writer shape by a real INSERT without the new
        # internal argument. Never UPDATE the immutable Snapshot being tested.
        result = db._execute_write(lambda conn: db.notebook_commit_snapshot_result_conn(
            conn, ref, audit["payload"], anchor_message_uid=audit["anchor_message_uid"],
            trigger_type=audit["trigger_type"], termination={"type": "finish_noting", "reason": "Legacy recovery"}))
        snapshot_id = result["snapshot_id"]
        witness = json.loads(db.get_session(state["child_session_id"])["model_config"])["_noting_recovery"]
        witness["snapshot_id"] = snapshot_id
        db.patch_session_model_config(state["child_session_id"], {"_noting_recovery": witness})
        assert db.notebook_current(ref)["snapshot_id"] == snapshot_id
        assert "noting_origin" not in db.notebook_snapshot_audit(snapshot_id)["termination"]
    for _ in range(2):
        assert not check_note_delivery(parent)
    with db._read_ctx() as conn:
        assert select_note_conn(db, conn, ref) is None
    assert notes(db, ref) == [] and actual_notes(parent, db) == []
    next_native_boundary(runtime, monkeypatch)
    assert len(notes(db, ref)) == 1 and notes(db, ref)[0]["snapshot_id"] == snapshot_id
    assert notes(db, ref)[0]["interval_id"] != original["compression_interval_id"]
    assert len(actual_notes(parent, db)) == 1
    for _ in range(2):
        assert not check_note_delivery(parent)
        bind_main_runtime(parent)
    reopened = SessionDB(db.db_path)
    try:
        with reopened._read_ctx() as conn:
            assert select_note_conn(reopened, conn, ref) is None
    finally:
        reopened.close()
    assert len(notes(db, ref)) == len(actual_notes(parent, db)) == 1
    assert "noting_origin" not in str(actual_notes(parent, db)[0]["content"])


def test_recovery_origin_is_in_insert_and_failure_rolls_back_without_stopping_native(runtime, monkeypatch):
    parent, db, _client, _children = runtime
    ref = parent._secretary_conversation_ref
    original, child_id = failed_carried_task(runtime, monkeypatch)
    before = [tuple(row) for row in db._read_all("SELECT * FROM secretary_notebook_snapshots")]
    reselect = SessionDB._notebook_reselect_pointer_conn
    observed = []
    def fail_recovery(self, conn, conversation):
        rows = conn.execute("SELECT termination_json FROM secretary_notebook_snapshots WHERE conversation_ref=?",
                            (conversation,)).fetchall()
        origins = [json.loads(row["termination_json"]).get("noting_origin") for row in rows]
        if any(origins):
            observed.extend(origins)
            raise RuntimeError("Controlled atomic recovery Snapshot failure")
        return reselect(self, conn, conversation)
    monkeypatch.setattr(SessionDB, "_notebook_reselect_pointer_conn", fail_recovery)
    state = recover_task(runtime, monkeypatch, child_id, "atomic-failure")
    assert not state["committed"] and state["snapshot_id"] is None
    assert observed == [{"admission_id": original["admission_id"],
                         "compression_interval_id": original["compression_interval_id"],
                         "recovery_session_id": state["child_session_id"]}]
    assert [tuple(row) for row in db._read_all("SELECT * FROM secretary_notebook_snapshots")] == before
    assert db.noting_admission(original["admission_id"]) == original
    assert db.notebook_current(ref) is None and notes(db, ref) == []
    next_native_boundary(runtime, monkeypatch)
    assert notes(db, ref) == []


def test_late_recovery_after_next_successful_native_boundary_delivers_once(runtime, monkeypatch):
    parent, db, _client, _children = runtime
    ref = parent._secretary_conversation_ref
    original, child_id = failed_carried_task(runtime, monkeypatch)
    next_native_boundary(runtime, monkeypatch)
    assert notes(db, ref) == []
    state = recover_task(runtime, monkeypatch, child_id, "late-recovery")
    assert state["committed"], state
    assert len(notes(db, ref)) == 1
    assert notes(db, ref)[0]["snapshot_id"] == state["snapshot_id"]
    assert notes(db, ref)[0]["interval_id"] != original["compression_interval_id"]
    assert len(actual_notes(parent, db)) == 1
    assert not check_note_delivery(parent)


@pytest.mark.parametrize("invalid", ["missing", "anchor", "conversation", "cancelled", "superseded"])
def test_recovery_origin_validation_preserves_failed_task_and_rejects_wrong_source(runtime, invalid):
    from secretary.noting_child import commit_noting_snapshot
    from tests.secretary.test_noting_child import empty_state
    parent, db, _client, _children = runtime
    ref = parent._secretary_conversation_ref
    original = db.noting_admit(ref, "m9", kind="manual")
    db.noting_child_finish(original, status="failed")
    origin = original
    if invalid == "missing":
        origin = 99999
    if invalid == "conversation":
        db.create_session("foreign", source="test")
        db.append_message("foreign", "user", "foreign source", message_uid="m9")
        origin = db.noting_admit(db.resolve_conversation_ref("foreign"), "m9", kind="manual")
    if invalid in {"cancelled", "superseded"}:
        origin = db.noting_admit(ref, "m9", kind="manual")
        db.noting_child_finish(origin, status=invalid)
    with pytest.raises(ValueError, match="original task"):
        commit_noting_snapshot(db, ref, empty_state(), anchor_message_uid="m10" if invalid == "anchor" else "m9",
                              trigger_type="manual", runtime_profile="NOTING",
                              termination={"type": "finish_noting", "reason": "Done"}, origin_admission_id=origin)
    assert db.noting_admission(original)["state"] == "failed"
    assert db.notebook_current(ref) is None


def test_conflicting_recovery_witness_cannot_borrow_another_task_source(runtime, monkeypatch, caplog):
    parent, db, _client, _children = runtime
    ref = parent._secretary_conversation_ref
    original, child_id = failed_carried_task(runtime, monkeypatch)
    state = recover_task(runtime, monkeypatch, child_id, "conflicting-witness")
    assert state["committed"], state
    other = db.noting_admit(ref, original["anchor_message_uid"], kind="manual")
    assert other is not None and other != original["admission_id"]
    db.noting_child_finish(other, status="failed")
    witness = json.loads(db.get_session(state["child_session_id"])["model_config"])["_noting_recovery"]
    witness["admission_id"] = other
    db.patch_session_model_config(state["child_session_id"], {"_noting_recovery": witness})
    with db._read_ctx() as conn, pytest.raises(ValueError, match="Conflicting Note source owners"):
        select_note_conn(db, conn, ref)
    assert not check_note_delivery(parent)
    assert "Conflicting Note source owners" in caplog.text
    assert notes(db, ref) == [] and actual_notes(parent, db) == []


def test_tool_termination_cannot_forge_internal_recovery_origin(runtime):
    from secretary.notebook_store import NotebookStore
    parent, db, _client, _children = runtime
    ref = parent._secretary_conversation_ref
    with pytest.raises(ValueError, match="exactly type and reason"):
        NotebookStore(db, ref, anchor_message_uid="m9").commit(termination={
            "type": "finish_noting", "reason": "Done", "noting_origin": {
                "admission_id": 123, "compression_interval_id": "conversation_start"}})
    assert db.notebook_current(ref) is None


def test_branch_copies_recovered_notebook_without_cross_conversation_source_owner(runtime, monkeypatch):
    parent, db, _client, _children = runtime
    ref = parent._secretary_conversation_ref
    _original, child_id = failed_carried_task(runtime, monkeypatch)
    state = recover_task(runtime, monkeypatch, child_id, "branch-source")
    assert state["committed"], state
    source = db.notebook_snapshot_audit(state["snapshot_id"])
    db.create_session("branch", source="test", parent_session_id=parent.session_id,
                      model_config={"_branched_from": parent.session_id})
    branch_ref = db.resolve_conversation_ref("branch")
    assert branch_ref != ref
    branch = db.notebook_current(branch_ref)
    assert branch is not None and branch["snapshot_id"] != source["snapshot_id"]
    clone = db.notebook_snapshot_audit(branch["snapshot_id"])
    assert clone["payload"] == source["payload"]
    assert clone["anchor_message_uid"] == source["anchor_message_uid"]
    assert clone["termination"] == {key: value for key, value in source["termination"].items()
                                     if key != "noting_origin"}
    assert db.notebook_snapshot_audit(source["snapshot_id"])["termination"] == source["termination"]
    db.append_message("branch", "user", "A real branch source", message_uid="branch-source")
    db.archive_and_compact("branch", _summary(db.get_messages_as_conversation("branch")))
    with db._read_ctx() as conn:
        selected = select_note_conn(db, conn, branch_ref)
    assert selected is not None and selected["snapshot_id"] == clone["snapshot_id"]
