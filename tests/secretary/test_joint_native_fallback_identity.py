"""Real stall fallback preserves the existing operation across both fence-swap races."""

import threading
import time

import pytest

from agent import context_compaction_request as native
from agent.compression_read import cancel_compression, compression_state
from agent.context_compressor import take_pinned_summary_route
from agent.auxiliary_client import AuxiliaryExplicitCancellation
from secretary.noting_native_link import cancel_request_fence
from tests.agent.test_context_compaction_request import _summary
from tests.secretary.test_joint_native_failure_independence import provider_barrier, start_idle, join
from tests.secretary.test_joint_noting_u20 import admissions, compress_async, notes, wait_for

pytest_plugins = ["tests.secretary.test_noting_child", "tests.secretary.test_joint_noting_u20",
                  "tests.secretary.test_joint_native_failure_independence"]


def controlled_stall(parent, monkeypatch, *, fallback):
    monkeypatch.setattr("agent.conversation_compression.resolve_context_compression_timeouts", lambda: (.15, 3.0))
    chain = [{"provider": "custom", "model": "controlled-fallback", "base_url": "https://example.invalid/v1",
              "api_key": "test-key", "timeout": 1}] if fallback else []
    monkeypatch.setattr("agent.auxiliary_client._get_auxiliary_task_config", lambda *args, **kwargs: {"fallback_chain": chain})
    calls, fences = [], []
    entered = threading.Event()
    def summary(messages, **kwargs):
        route = take_pinned_summary_route()
        calls.append(route)
        fences.append(parent._native_compaction_request.fence if getattr(parent, "_native_compaction_request", None)
                      else parent._active_compression_commit_fence)
        if route is None:
            entered.set()
            cancelled = parent.context_compressor._compression_cancelled_check
            deadline = time.monotonic() + 10
            while not cancelled() and time.monotonic() < deadline:
                time.sleep(.001)
            raise AuxiliaryExplicitCancellation()
        return _summary(messages)
    monkeypatch.setattr(parent.context_compressor, "compress", summary)
    return entered, calls, fences


def test_host_stall_cancelled_fence_does_not_mean_explicit_user_cancel(isolated_runtime, monkeypatch):
    parent, db, client, children = isolated_runtime
    child_entered, child_release = provider_barrier(client)
    entered, calls, _fences = controlled_stall(parent, monkeypatch, fallback=False)
    native_worker, _result, errors = compress_async(parent, force=True)
    try:
        assert entered.wait(10) and child_entered.wait(10)
        join(native_worker)
        assert not errors and len(calls) == 1
        task = admissions(db)[-1]
        assert compression_state(parent)["state"] == "cancelled"
        assert task["state"] == "admitted"
        child_release.set()
        join(children[-1])
        assert db.noting_admission(task["admission_id"])["state"] == "committed"
        assert notes(db, task["conversation_ref"]) == []
    finally:
        child_release.set()
        join(native_worker)


def test_real_stall_fallback_keeps_one_registration_and_independent_child(isolated_runtime, monkeypatch):
    parent, db, client, children = isolated_runtime
    child_entered, child_release = provider_barrier(client)
    entered, calls, fences = controlled_stall(parent, monkeypatch, fallback=True)
    worker = start_idle(parent, db)
    try:
        assert entered.wait(10) and child_entered.wait(10)
        task = admissions(db)[-1]
        join(worker)
        assert len(calls) == 2 and calls[0] is None and calls[1] is not None
        assert fences[0] is not fences[1]
        assert fences[0]._secretary_joint_registration is fences[1]._secretary_joint_registration
        assert fences[1]._secretary_joint_registration.observation.operation_id == task["operation_id"]
        assert not fences[1]._secretary_joint_registration.observation.cancel_requested
        assert db.noting_admission(task["admission_id"])["state"] == "admitted"
        child_release.set()
        join(children[-1])
        assert db.noting_admission(task["admission_id"])["state"] == "committed"
        assert len(notes(db, task["conversation_ref"])) == 1
        assert len(admissions(db)) == 1
    finally:
        child_release.set()
        join(worker)


@pytest.mark.parametrize("swap_order", ["new_bound_before_publication", "old_captured_before_swap"])
def test_idle_cancel_on_either_side_of_real_fallback_swap_targets_same_operation(isolated_runtime, monkeypatch, swap_order):
    parent, db, client, children = isolated_runtime
    child_entered, child_release = provider_barrier(client)
    entered, _calls, fences = controlled_stall(parent, monkeypatch, fallback=True)
    at_swap, release_swap, cancel_captured, release_cancel = [threading.Event() for _ in range(4)]
    bind = native.NativeCompactionRequest.bind_fence
    bound = []
    def held_bind(request, fence):
        bound.append(fence)
        if len(bound) == 2 and swap_order == "old_captured_before_swap":
            at_swap.set()
            assert release_swap.wait(20)
        result = bind(request, fence)
        if len(bound) == 2 and swap_order == "new_bound_before_publication":
            at_swap.set()
            assert release_swap.wait(20)
        return result
    monkeypatch.setattr(native.NativeCompactionRequest, "bind_fence", held_bind)
    worker = start_idle(parent, db)
    canceller = None
    try:
        assert entered.wait(10) and child_entered.wait(10) and at_swap.wait(10)
        old, retry = bound
        registration = old._secretary_joint_registration
        task = admissions(db)[-1]
        assert registration.fence is old and retry._secretary_joint_registration is registration
        assert task["operation_id"] == registration.observation.operation_id
        if swap_order == "new_bound_before_publication":
            assert parent._native_compaction_request.fence is retry
            native.cancel_native_request(parent)
        else:
            original_cancel = old.cancel_before_commit
            def held_cancel(*args, **kwargs):
                if threading.current_thread() is canceller:
                    cancel_captured.set()
                    assert release_cancel.wait(20)
                return original_cancel(*args, **kwargs)
            monkeypatch.setattr(old, "cancel_before_commit", held_cancel)
            canceller = threading.Thread(target=lambda: native.cancel_native_request(parent))
            canceller.start()
            assert cancel_captured.wait(10)
            release_swap.set()
            wait_for(lambda: registration.fence is retry)
            release_cancel.set()
            join(canceller)
        release_swap.set()
        child_release.set()
        join(worker)
        join(children[-1])
        assert registration.observation.cancel_requested
        assert db.noting_admission(task["admission_id"])["state"] == "cancelled"
        assert db.notebook_current(task["conversation_ref"]) is None
        assert len(admissions(db)) == 1
    finally:
        release_swap.set()
        release_cancel.set()
        child_release.set()
        join(worker)
        if canceller is not None:
            join(canceller)


def test_retired_old_fence_cannot_cancel_new_live_operation(isolated_runtime, monkeypatch):
    parent, db, client, children = isolated_runtime
    entered, release = provider_barrier(client)
    seen = []
    def no_change(messages, **kwargs):
        seen.append(parent._active_compression_commit_fence)
        return messages
    monkeypatch.setattr(parent.context_compressor, "compress", no_change)
    first, _result, errors = compress_async(parent, force=True)
    try:
        join(first)
        assert not errors and entered.wait(10)
        old = seen[0]
        db.append_message(parent.session_id, "user", "Next legitimate source", message_uid="new-source")
        parent._session_messages = db.get_messages_as_conversation(parent.session_id)
        next_summary, release_summary = threading.Event(), threading.Event()
        def summary(messages, **kwargs):
            next_summary.set()
            assert release_summary.wait(20)
            return _summary(messages)
        monkeypatch.setattr(parent.context_compressor, "compress", summary)
        second, _, errors = compress_async(parent, force=True)
        try:
            assert next_summary.wait(10)
            task = admissions(db)[-1]
            assert task["state"] == "admitted" and task["operation_id"] != old._secretary_joint_registration.observation.operation_id
            assert cancel_request_fence(parent, old, state="cancelled")
            assert db.noting_admission(task["admission_id"])["state"] == "admitted"
            assert cancel_compression(parent, task["operation_id"])["outcome"] == "cancelled"
            assert db.noting_admission(task["admission_id"])["state"] == "cancelled"
        finally:
            release.set()
            release_summary.set()
            join(second)
    finally:
        release.set()
        join(first)
        for child in children:
            join(child)
