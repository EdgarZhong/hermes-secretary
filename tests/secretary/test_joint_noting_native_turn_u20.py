"""Force observes actual SDK-backed native Turns while the real durable lease is held."""

import copy
import threading
from types import SimpleNamespace

import pytest

from secretary import noting_child
from tests.secretary.test_joint_noting_force_owner_u20 import force_notices
from tests.secretary.test_joint_noting_u20 import admissions
from tests.secretary.test_noting_child import _tool_response, mock_response

pytest_plugins = ["tests.secretary.test_noting_child", "tests.secretary.test_joint_noting_u20"]


def sdk_responder(**kwargs):
    messages = str(kwargs.get("messages"))
    if "<noting-task>" in messages:
        return _tool_response("finish_noting", {"reason": "The ended Turn was reviewed"}, "finish")
    first = "second native request" not in messages
    response = mock_response("First native answer" if first else "Second native answer")
    response.usage = SimpleNamespace(prompt_tokens=63_900 if first else 100,
                                     completion_tokens=200 if first else 10,
                                     total_tokens=64_100 if first else 110)
    return response


def test_force_is_frozen_and_noticed_before_native_lease_release_and_successor_admission(runtime, monkeypatch):
    from agent.turn_facade_lease import DurableTurnLease
    from secretary.noting_policy import measurement_from_agent
    parent, db, client, workers = runtime
    parent.client = client
    parent._disable_streaming = True
    parent.compression_enabled = False
    next_model_entered, next_model_release = threading.Event(), threading.Event()
    def provider(**kwargs):
        messages = str(kwargs.get("messages"))
        if "<noting-task>" not in messages and "second native request" in messages:
            next_model_entered.set()
            assert next_model_release.wait(10)
        return sdk_responder(**kwargs)
    client.chat.completions.create.side_effect = provider
    monkeypatch.setattr("secretary.noting_timers.arm_idle_timer", lambda *args: None)
    before_release, release, next_waiting = threading.Event(), threading.Event(), threading.Event()
    captures, measured, results, errors = [], [], [], []
    spawn = noting_child.spawn_noting_task
    def capture(owner, admission, **kwargs):
        if admission.kind == "force":
            captures.append((admission, copy.deepcopy(kwargs["parent_active_messages"])))
        return spawn(owner, admission, **kwargs)
    monkeypatch.setattr(noting_child, "spawn_noting_task", capture)
    def measure(owner, usage):
        measured.append((threading.current_thread().name, usage))
        return measurement_from_agent(owner, usage)
    monkeypatch.setattr("secretary.noting_policy.measurement_from_agent", measure)
    real_release = DurableTurnLease.release
    def held_release(lease):
        if lease.agent is parent and threading.current_thread().name == "first-native":
            before_release.set()
            assert release.wait(10)
        return real_release(lease)
    monkeypatch.setattr(DurableTurnLease, "release", held_release)
    acquire = db.acquire_session_turn_lease
    def observe_wait(*args, **kwargs):
        if threading.current_thread().name == "second-native":
            on_wait = kwargs.get("on_wait")
            def waiting(elapsed):
                next_waiting.set()
                if on_wait:
                    on_wait(elapsed)
            kwargs["on_wait"] = waiting
        return acquire(*args, **kwargs)
    monkeypatch.setattr(db, "acquire_session_turn_lease", observe_wait)
    def run(text):
        try:
            results.append(parent.run_conversation(text, conversation_history=list(parent._session_messages)))
        except BaseException as exc:
            errors.append(exc)
    first = threading.Thread(target=run, args=("first native request",), name="first-native")
    second = threading.Thread(target=run, args=("second native request",), name="second-native")
    first.start()
    try:
        assert before_release.wait(10)
        with db._read_ctx() as conn:
            held = conn.execute("SELECT holder FROM session_turn_leases WHERE conversation_id=?",
                                (db._session_turn_lease_key(parent.session_id),)).fetchone()
        assert held is not None
        first_started = db.noting_idle_state(parent._secretary_conversation_ref)["last_turn_started_at"]
        second.start()
        assert next_waiting.wait(10)
        assert db.noting_idle_state(parent._secretary_conversation_ref)["last_turn_started_at"] == first_started
        assert not parent._secretary_main_turn_running
        assert len(force_notices(parent)) == len(captures) == 1
        assert any(name == "first-native" and usage >= 64_100 for name, usage in measured)
        assert captures[0][1][-1]["content"] == "First native answer"
        assert "second native request" not in str(captures[0][1])
        assert captures[0][0].anchor_message_uid == captures[0][1][-1]["message_uid"]
        release.set()
        first.join(10)
        assert not first.is_alive() and next_model_entered.wait(10)
        assert parent._secretary_main_turn_running and second.is_alive()
        assert len(force_notices(parent)) == 1
    finally:
        release.set()
        next_model_release.set()
        first.join(15)
        if second.ident is not None:
            second.join(15)
    assert not first.is_alive() and not second.is_alive() and errors == []
    assert len(results) == 2 and all(result["completed"] for result in results)
    assert len(admissions(db)) == len(force_notices(parent)) == 1
    for worker in workers:
        worker.join(10)


def test_unadmitted_native_request_does_not_start_or_finish_secretary_main_period(runtime, monkeypatch):
    parent, db, client, _workers = runtime
    parent.client = client
    parent._disable_streaming = True
    client.chat.completions.create.side_effect = sdk_responder
    ref = parent._secretary_conversation_ref
    db.noting_idle_turn_finished(ref, 1000, due_at=1500)
    before = db.noting_idle_state(ref)
    assert db.acquire_session_turn_lease(parent.session_id, "external-owner", wait_seconds=0)
    monkeypatch.setattr("agent.turn_facade_lease.LEASE_WAIT_SECONDS", 0)
    try:
        result = parent.run_conversation("never admitted", conversation_history=list(parent._session_messages))
        assert result["failed"] and result["failure_reason"] == "session_busy"
        assert db.noting_idle_state(ref) == before
        assert admissions(db) == [] and force_notices(parent) == []
        client.chat.completions.create.assert_not_called()
    finally:
        db.release_session_turn_lease(parent.session_id, "external-owner")


@pytest.mark.parametrize("mode", ["global_off", "non_main"])
def test_native_turn_preserves_disabled_and_nonmain_paths(runtime, monkeypatch, mode):
    from pathlib import Path
    parent, db, client, _workers = runtime
    parent.client = client
    parent._disable_streaming = True
    parent.compression_enabled = False
    client.chat.completions.create.side_effect = sdk_responder
    monkeypatch.setattr("secretary.noting_timers.arm_idle_timer", lambda *args: None)
    if mode == "global_off":
        Path(db.db_path).with_name("config.yaml").write_text("noting:\n  enabled: false\n")
    else:
        parent.side_agent = True
    result = parent.run_conversation("first native request", conversation_history=list(parent._session_messages))
    assert result["completed"] and result["final_response"] == "First native answer"
    assert admissions(db) == [] and force_notices(parent) == []
    assert client.chat.completions.create.call_count == 1


def test_admitted_turn_relay_preparation_failure_balances_observation_and_releases_native_lease(runtime, monkeypatch):
    parent, db, client, _workers = runtime
    parent.client = client
    parent._disable_streaming = True
    monkeypatch.setattr("secretary.noting_timers.arm_idle_timer", lambda *args: None)
    def fail(*args, **kwargs):
        raise RuntimeError("Controlled relay preparation failure after native admission")
    monkeypatch.setattr("agent.relay_runtime.SESSION_COORDINATOR.begin_turn", fail)
    with pytest.raises(RuntimeError, match="relay preparation failure"):
        parent.run_conversation("accepted but failed", conversation_history=list(parent._session_messages))
    assert not parent._secretary_main_turn_running
    assert parent._relay_pending_turn_id is None
    assert parent._active_session_turn_lease_holder is None
    assert db._read_one("SELECT 1 FROM session_turn_leases WHERE conversation_id=?",
                        (db._session_turn_lease_key(parent.session_id),)) is None
    period = db.noting_idle_state(parent._secretary_conversation_ref)
    assert period["last_turn_finished_at"] >= period["last_turn_started_at"]
    client.chat.completions.create.assert_not_called()


def test_waiting_successor_does_not_delay_force_notice_beyond_next_native_model_request(runtime, monkeypatch):
    parent, db, client, workers = runtime
    parent.client = client
    parent._disable_streaming = True
    parent.compression_enabled = False
    monkeypatch.setattr("secretary.noting_timers.arm_idle_timer", lambda *args: None)
    first_model, release_first, next_waiting = threading.Event(), threading.Event(), threading.Event()
    next_model, release_next = threading.Event(), threading.Event()
    next_wire, errors = [], []
    def provider(**kwargs):
        messages = str(kwargs.get("messages"))
        if "<noting-task>" not in messages:
            if "second native request" in messages:
                next_wire.append(copy.deepcopy(kwargs["messages"]))
                next_model.set()
                assert release_next.wait(10)
            else:
                first_model.set()
                assert release_first.wait(10)
        return sdk_responder(**kwargs)
    client.chat.completions.create.side_effect = provider
    acquire = db.acquire_session_turn_lease
    def observe_wait(*args, **kwargs):
        if threading.current_thread().name == "queued-successor":
            on_wait = kwargs.get("on_wait")
            def waiting(elapsed):
                next_waiting.set()
                if on_wait:
                    on_wait(elapsed)
            kwargs["on_wait"] = waiting
        return acquire(*args, **kwargs)
    monkeypatch.setattr(db, "acquire_session_turn_lease", observe_wait)
    def run(text):
        try:
            parent.run_conversation(text, conversation_history=list(parent._session_messages))
        except BaseException as exc:
            errors.append(exc)
    first = threading.Thread(target=run, args=("first native request",), name="native-active")
    successor = threading.Thread(target=run, args=("second native request",), name="queued-successor")
    first.start()
    try:
        assert first_model.wait(10)
        successor.start()
        assert next_waiting.wait(10)
        release_first.set()
        first.join(10)
        assert not first.is_alive() and next_model.wait(10)
        assert parent._secretary_main_turn_running
        assert "a Notebook update task has been dispatched" in str(next_wire[0])
        assert len(force_notices(parent)) == 1
    finally:
        release_first.set()
        release_next.set()
        first.join(15)
        if successor.ident is not None:
            successor.join(15)
        for worker in workers:
            worker.join(10)
    assert errors == [] and not successor.is_alive()
