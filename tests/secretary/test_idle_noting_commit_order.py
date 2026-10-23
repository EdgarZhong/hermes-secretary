"""Idle's real child/Commit Gate/native compaction/Framework order, without model traffic."""

import threading

import pytest

from agent.context_compaction_request import trust_default_system_message
from secretary import noting_child, noting_runtime
from secretary.framework_messages import flush_framework_messages, mark_framework_turn
from secretary.noting_scope import owning_db_scope
from tests.agent.test_context_compaction_request import _summary
from tests.secretary.test_noting_child import _tool_response, mock_response

pytest_plugins = ["tests.secretary.test_noting_child"]


@pytest.fixture
def idle_runtime(parent, db, stub_client, monkeypatch, tmp_path):
    (tmp_path / "config.yaml").write_text(
        "noting:\n  enabled: true\n  idle:\n    enabled: true\n    delay_seconds: 500\n    threshold_tokens: 1000\n"
    )
    for number in range(3, 11):
        db.append_message(parent.session_id, "user" if number % 2 else "assistant",
                          "Original dialogue " * 100, message_uid=f"m{number}", timestamp=1000.0 + number)
    parent._session_messages = db.get_messages_as_conversation(parent.session_id)
    parent.compression_enabled = True
    parent.compression_in_place = True
    parent._compression_feasibility_checked = True
    parent.context_compressor.context_length = 130000
    parent.context_compressor.threshold_tokens = 75000
    parent.context_compressor.last_prompt_tokens = 50000
    parent.context_compressor.last_real_prompt_tokens = 50000
    trust_default_system_message(parent)
    monkeypatch.setattr("secretary.noting_timers.arm_idle_timer", lambda *a: None)
    workers = []
    spawn = noting_child.spawn_noting_task

    def capture(*args, **kwargs):
        worker = spawn(*args, **kwargs)
        workers.append(worker)
        return worker

    monkeypatch.setattr(noting_child, "spawn_noting_task", capture)
    with owning_db_scope(db):
        yield parent, db, stub_client, workers
    for worker in workers:
        worker.join(10)
        assert not worker.is_alive()


def start_idle(parent, db):
    ref = parent._secretary_conversation_ref
    db.noting_idle_turn_finished(ref, 1000, due_at=1500)
    return noting_runtime._run_idle_event(parent, db, ref, now=2000)


def result_rows(parent):
    return [row for row in parent._session_messages
            if (row.get("display_metadata") or {}).get("noting_run_output")]


def finish_responses(client):
    client.chat.completions.create.side_effect = [
        _tool_response("finish_noting", {"reason": "Reviewed the frozen dialogue."}, "finish"),
        mock_response("Finished."),
    ]


@pytest.mark.parametrize("in_place", [True, False], ids=["in-place", "rotation"])
@pytest.mark.parametrize("clear_request", [False, True], ids=["retained-request", "detached-request"])
def test_normal_finish_commits_before_native_compression_and_publishes_after_it(
        idle_runtime, monkeypatch, in_place, clear_request):
    parent, db, client, workers = idle_runtime
    parent.compression_in_place = in_place
    finish_responses(client)
    entered, release = threading.Event(), threading.Event()
    ref, original_session = parent._secretary_conversation_ref, parent.session_id
    observed = []

    def summary(messages, **kwargs):
        current = db.notebook_current(ref)
        observed.append(current["snapshot_id"])
        assert db.notebook_snapshot_audit(current["snapshot_id"])["termination"]["type"] == "finish_noting"
        assert not result_rows(parent)
        entered.set()
        assert release.wait(10)
        return _summary(messages, **kwargs)

    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    try:
        assert start_idle(parent, db) == "admitted"
        assert entered.wait(10)
        assert db.notebook_current(ref)["snapshot_id"] == observed[0]
        assert workers[0].is_alive() and not result_rows(parent)
        if clear_request:
            parent._native_compaction_request = None
            assert workers[0].is_alive() and not result_rows(parent)
        release.set()
        workers[0].join(10)
        assert not workers[0].is_alive()
        rows = result_rows(parent)
        assert len(rows) == 1 and "Termination: finish_noting" in rows[0]["content"]
        durable = [row for row in db.get_messages(parent.session_id)
                   if (row.get("display_metadata") or {}).get("noting_run_output")]
        assert durable[-1]["message_uid"] == rows[0]["message_uid"]
        assert db.get_native_request_publication(original_session) is not None
        assert (parent.session_id == original_session) is in_place
    finally:
        release.set()


@pytest.mark.parametrize("ending", ["five_turns", "iterations", "overflow_exception", "overflow_result", "api_error"])
def test_abnormal_endings_never_compact_and_keep_existing_commit_semantics(idle_runtime, monkeypatch, ending):
    parent, db, client, workers = idle_runtime
    compact_calls = []
    monkeypatch.setattr(parent, "request_context_compaction", lambda **kwargs: compact_calls.append(kwargs))
    if ending == "five_turns":
        client.chat.completions.create.return_value = mock_response("Still working.")
    else:
        def run(child, **kwargs):
            if ending == "iterations":
                return {"completed": False, "turn_exit_reason": "max_iterations_reached(50/50)",
                        "final_response": "Native budget exhausted."}
            if ending == "overflow_exception":
                raise noting_child.NotingContextOverflow("controlled overflow")
            if ending == "overflow_result":
                return {"completed": False, "failed": True, "failure_reason": "context_overflow"}
            return {"completed": False, "failed": True, "error": "provider unavailable", "turn_exit_reason": "api_error"}
        monkeypatch.setattr("run_agent.AIAgent.run_conversation", run)
    assert start_idle(parent, db) == "admitted"
    workers[0].join(10)
    assert not workers[0].is_alive() and compact_calls == []
    current = db.notebook_current(parent._secretary_conversation_ref)
    rows = result_rows(parent)
    assert len(rows) == 1
    if ending == "api_error":
        assert current is None
        assert "No new Snapshot was committed" in rows[0]["content"]
        assert "provider unavailable" in rows[0]["content"]
    else:
        assert current is not None
        assert "Notebook maintenance did not finish normally" in rows[0]["content"]
        assert "CURRENT NOTEBOOK SNAPSHOT" in rows[0]["content"]


@pytest.mark.parametrize("failure", ["native_error", "native_disabled", "gate_disabled", "owner_closed"])
def test_native_failure_or_owner_change_does_not_roll_back_legal_notebook(idle_runtime, monkeypatch, failure):
    parent, db, client, workers = idle_runtime
    finish_responses(client)
    native_calls = []
    if failure == "native_error":
        def fail(**kwargs):
            native_calls.append(kwargs)
            raise RuntimeError("native request unavailable")
        monkeypatch.setattr(parent, "request_context_compaction", fail)
    elif failure == "native_disabled":
        parent.compression_enabled = False
        monkeypatch.setattr(parent.context_compressor, "compress", lambda *a, **k: pytest.fail("native disabled"))
    else:
        original = noting_child._commit_when_complete
        def change(*args, **kwargs):
            if failure == "gate_disabled":
                db.notebook_set_local_enabled(parent._secretary_conversation_ref, False)
            else:
                parent.close()
            return original(*args, **kwargs)
        monkeypatch.setattr(noting_child, "_commit_when_complete", change)
        if failure == "gate_disabled":
            monkeypatch.setattr(parent, "request_context_compaction", lambda **kwargs: native_calls.append(kwargs))
        else:
            monkeypatch.setattr(parent.context_compressor, "compress", lambda *a, **k: pytest.fail("owner closed"))
    assert start_idle(parent, db) == "admitted"
    workers[0].join(10)
    assert not workers[0].is_alive()
    current = db.notebook_current(parent._secretary_conversation_ref)
    if failure == "gate_disabled":
        assert current is None and not native_calls
    else:
        assert current is not None
        if failure == "owner_closed":
            assert not native_calls
        else:
            assert len(result_rows(parent)) == 1


def test_parent_becomes_active_noting_waits_for_native_safe_point_then_framework_tail(idle_runtime, monkeypatch):
    from agent.context_compaction_request import consume_native_request, enter_native_turn, leave_native_turn

    parent, db, client, workers = idle_runtime
    finish_responses(client)
    ready, release = threading.Event(), threading.Event()
    build = noting_child.build_noting_child

    def delayed(*args, **kwargs):
        child = build(*args, **kwargs)
        run = child.run_conversation
        def turn(**turn_kwargs):
            ready.set()
            assert release.wait(10)
            return run(**turn_kwargs)
        child.run_conversation = turn
        return child

    monkeypatch.setattr(noting_child, "build_noting_child", delayed)
    monkeypatch.setattr(parent.context_compressor, "compress", _summary)
    assert start_idle(parent, db) == "admitted"
    assert ready.wait(10)
    token, _ = enter_native_turn(parent, None, parent._session_messages)
    mark_framework_turn(parent, running=True)
    # Observe the actual native request, without treating admission as completion.
    requested = threading.Event()
    request = parent.request_context_compaction
    def observe(**kwargs):
        requested.set()
        return request(**kwargs)
    monkeypatch.setattr(parent, "request_context_compaction", observe)
    release.set()
    try:
        assert requested.wait(10)
        from time import monotonic, sleep
        deadline = monotonic() + 4
        while getattr(parent, "_native_compaction_request", None) is None and monotonic() < deadline:
            sleep(.01)
        assert workers[0].is_alive() and not result_rows(parent)
        assert consume_native_request(parent, parent._session_messages, None) is not None
        workers[0].join(10)
        assert not workers[0].is_alive() and not result_rows(parent)
        assert parent._secretary_framework_messages
    finally:
        release.set()
        leave_native_turn(parent, token)
        mark_framework_turn(parent, running=False)
    assert len(result_rows(parent)) == 1 and flush_framework_messages(parent) == 0


def test_admitted_native_summary_failure_still_publishes_committed_notebook(idle_runtime, monkeypatch):
    parent, db, client, workers = idle_runtime
    finish_responses(client)
    summaries = []
    def fail_summary(*args, **kwargs):
        summaries.append(db.notebook_current(parent._secretary_conversation_ref)["snapshot_id"])
        raise RuntimeError("summary route unavailable")
    monkeypatch.setattr(parent.context_compressor, "compress", fail_summary)
    assert start_idle(parent, db) == "admitted"
    workers[0].join(10)
    assert not workers[0].is_alive() and summaries
    current = db.notebook_current(parent._secretary_conversation_ref)
    assert current["snapshot_id"] == summaries[0]
    assert len(result_rows(parent)) == 1
    assert "Termination: finish_noting" in result_rows(parent)[0]["content"]


def test_compaction_callback_exception_preserves_successful_snapshot_and_framework(idle_runtime, monkeypatch):
    parent, db, client, workers = idle_runtime
    finish_responses(client)
    def fail():
        raise RuntimeError("callback unavailable")
    monkeypatch.setattr("secretary.noting_compact.idle_compaction_after_commit", lambda *a, **k: fail)
    assert start_idle(parent, db) == "admitted"
    workers[0].join(10)
    assert not workers[0].is_alive()
    assert db.notebook_current(parent._secretary_conversation_ref) is not None
    assert len(result_rows(parent)) == 1
    assert "No new Snapshot" not in result_rows(parent)[0]["content"]


@pytest.mark.parametrize("finish_on_last_iteration", [False, True])
def test_native_iteration_boundary_compacts_only_for_successful_finish(
        idle_runtime, monkeypatch, finish_on_last_iteration):
    parent, db, client, workers = idle_runtime
    monkeypatch.setattr(noting_child, "NOTING_MAX_ITERATIONS", 1)
    client.chat.completions.create.side_effect = [
        _tool_response("finish_noting", {"reason": "Current work checked."}, "finish")
        if finish_on_last_iteration else _tool_response("notebook_show", {}, "show"),
        mock_response("Native budget boundary summary."),
    ]
    requests = []
    monkeypatch.setattr(parent, "request_context_compaction", lambda **kwargs: requests.append(kwargs))
    assert start_idle(parent, db) == "admitted"
    workers[0].join(10)
    assert not workers[0].is_alive()
    snapshot = db.notebook_current(parent._secretary_conversation_ref)
    kind = "finish_noting" if finish_on_last_iteration else "forced"
    assert db.notebook_snapshot_audit(snapshot["snapshot_id"])["termination"]["type"] == kind
    assert len(requests) == int(finish_on_last_iteration)
    assert len(result_rows(parent)) == 1
    assert ("Notebook maintenance did not finish normally" in result_rows(parent)[0]["content"]) is not finish_on_last_iteration


def test_existing_nonrequest_native_compaction_defers_framework_to_its_fence(idle_runtime, monkeypatch):
    from agent.conversation_compression import CompressionCommitFence

    parent, db, client, workers = idle_runtime
    finish_responses(client)
    entered, release, displayed = threading.Event(), threading.Event(), threading.Event()
    responses = iter([
        _tool_response("finish_noting", {"reason": "Reviewed the frozen dialogue."}, "finish"),
        mock_response("Finished."),
    ])
    def respond(**kwargs):
        assert entered.wait(10)
        return next(responses)
    client.chat.completions.create.side_effect = respond
    parent._print_fn = lambda text: displayed.set() if "NOTING RESULT" in text else None
    results = []
    def summary(messages, **kwargs):
        entered.set()
        assert release.wait(10)
        return _summary(messages, **kwargs)
    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    native = threading.Thread(target=lambda: results.append(parent._compress_context(
        parent._session_messages, None, approx_tokens=50000, trigger="noting_joint_idle",
        commit_fence=CompressionCommitFence(),
    )), daemon=True)
    # This is an independent native operation already in progress when Idle's
    # child finishes, rather than the request created by the Idle callback.
    assert start_idle(parent, db) == "admitted"
    native.start()
    try:
        assert entered.wait(10)
        workers[0].join(10)
        assert not workers[0].is_alive()
        assert getattr(parent, "_native_compaction_request", None) is None
        assert parent._secretary_framework_messages and not result_rows(parent)
        release.set()
        native.join(10)
        assert not native.is_alive() and results
        assert displayed.wait(5)
        assert len(result_rows(parent)) == 1
    finally:
        release.set()
        native.join(10)
