"""F17: validated Anchor identity survives a model-visible frozen handoff."""

from copy import deepcopy
from threading import Event
from types import SimpleNamespace

import pytest

from hermes_cli.cli_secretary_commands import secretary_feedback_messages
from secretary.noting_child import NotingChildError, freeze_parent_active_prefix, spawn_noting_task
from secretary.noting_runtime import NotingAdmission, prepare_joint_noting
from tests.secretary.test_r3_child import database as database, native_parent as native_parent, response


@pytest.mark.parametrize("human_only_anchor", [True, False])
@pytest.mark.parametrize("switch_conversation", [False, True])
def test_formal_manual_spawn_preserves_verified_anchor_across_worker_handoff(
        native_parent, database, monkeypatch, human_only_anchor, switch_conversation):
    from agent.memory_provider import spawn_context_thread
    import secretary.noting_child as owner

    parent, client = native_parent
    original_ref = parent._secretary_conversation_ref
    parent_wires, child_wires, frozen, active, decisions = [], [], [], [], []
    entered, release = Event(), Event()
    original_freeze = owner.freeze_parent_active_prefix
    def capture_freeze(*args, **kwargs):
        value = original_freeze(*args, **kwargs)
        frozen.append(deepcopy(value))
        return value
    monkeypatch.setattr(owner, "freeze_parent_active_prefix", capture_freeze)
    def gate_worker(target, **kwargs):
        if not kwargs.get("name", "").startswith("noting-task-"):
            return spawn_context_thread(target, **kwargs)
        def gated():
            entered.set()
            assert release.wait(10), "test worker barrier timed out"
            target()
        return spawn_context_thread(gated, **kwargs)
    monkeypatch.setattr("agent.memory_provider.spawn_context_thread", gate_worker)
    parent._on_turn_user_persisted = lambda messages, _index: active.append(messages)
    def provider(**kwargs):
        if not parent_wires:
            parent_wires.append(deepcopy(kwargs))
            messages = active[-1]
            if human_only_anchor:
                feedback = secretary_feedback_messages("/notebook", "Human-only Notebook inspection", human_only=True)
                database.append_messages_batch("parent", feedback)
                messages.extend(feedback)
            decision = prepare_joint_noting(parent, trigger="manual", messages=messages)
            decisions.append(decision)
            assert decision.action == "admit", decision
            assert entered.wait(3), "real spawn must enter its background worker"
            return response("Main response completed.")
        child_wires.append(deepcopy(kwargs))
        return response("Continue the same legal working view.")
    client.chat.completions.create.side_effect = provider
    workers = []
    original_spawn = owner.spawn_noting_task
    def capture_worker(*args, **kwargs):
        worker = original_spawn(*args, **kwargs)
        workers.append(worker)
        return worker
    monkeypatch.setattr(owner, "spawn_noting_task", capture_worker)
    try:
        result = parent.run_conversation(user_message="Visible Main input remains complete.",
            conversation_history=parent._session_messages, title_user_message="")
        assert result["completed"], result
        assert len(workers) == len(frozen) == 1
        anchor = decisions[0].admission.anchor_message_uid
        if human_only_anchor:
            assert not any(msg.get("message_uid") == anchor for msg in frozen[0])
            assert any(msg.get("message_uid") == anchor for msg in result["messages"])
        # The frozen worker must not consult the newly changed Parent context or request clock.
        parent._session_messages = []
        if switch_conversation:
            parent._secretary_conversation_ref = "another-parent-conversation"
        parent._persist_user_message_idx = 0
        parent._current_turn_timestamp += 1200
        parent._cached_system_prompt = "Changed Parent root after synchronous freeze"
        parent.tools = []
        release.set()
        workers[0].join(10)
        assert not workers[0].is_alive()
        child = database.noting_child(decisions[0].admission.admission_id)
        assert child["status"] == ("abandoned" if switch_conversation else "completed"), child
        assert child["child_session_id"]
        assert len(frozen) == 2
        assert all(value.anchor_identity == (original_ref, anchor) for value in frozen)
        assert len(child_wires) == 5
        for wire in child_wires:
            expected = parent_wires[0]["messages"]
            assert wire["messages"][:len(expected)] == expected
            assert wire["messages"][len(expected)]["content"].startswith("<noting-task>")
            assert wire["tools"] == parent_wires[0]["tools"]
            assert "Human-only Notebook inspection" not in str(wire["messages"])
        snapshot = database.notebook_current(original_ref)
        if switch_conversation:
            assert snapshot is None, "the original owner gate must reject this task's commit"
        else:
            assert snapshot["anchor_message_uid"] == anchor
    finally:
        release.set()
        for worker in workers:
            worker.join(10)


@pytest.mark.parametrize("change", ["anchor", "conversation"])
def test_verified_frozen_handoff_cannot_be_rebound_to_another_existing_anchor(native_parent, change):
    parent, _client = native_parent
    frozen = freeze_parent_active_prefix(parent, "m2")
    with pytest.raises(NotingChildError, match="Anchor"):
        freeze_parent_active_prefix(parent, "m1" if change == "anchor" else "m2", frozen,
            conversation_ref=parent._secretary_conversation_ref if change == "anchor" else "other-conversation")


def test_no_model_visible_prefix_fails_before_starting_worker(native_parent, database):
    parent, client = native_parent
    feedback = secretary_feedback_messages("/notebook", "No Notebook exists yet.", human_only=True)
    database.append_messages_batch("parent", feedback)
    anchor = feedback[-1]["message_uid"]
    ref = parent._secretary_conversation_ref
    admission_id = database.noting_admit(ref, anchor, kind="manual")
    admission = NotingAdmission(admission_id, ref, anchor, "manual", None, "NOTING")
    worker = None
    try:
        with pytest.raises(NotingChildError, match="(?i)(visible|empty|unavailable)"):
            worker = spawn_noting_task(parent, admission, parent_active_messages=feedback)
    finally:
        if worker is not None:
            worker.join(10)
    assert not client.chat.completions.create.called
    assert database.noting_child(admission_id)["status"] == "failed"


def test_unbound_subclass_cannot_supply_verified_anchor_identity(native_parent):
    from agent.cache_parity import FrozenParentPrefix
    parent, _client = native_parent
    ref = parent._secretary_conversation_ref
    class UnverifiedPrefix(FrozenParentPrefix):
        @property
        def anchor_identity(self):
            return (ref, "missing-anchor")
    source = UnverifiedPrefix(parent._session_messages)
    with pytest.raises(NotingChildError, match="Anchor"):
        freeze_parent_active_prefix(parent, "missing-anchor", source, conversation_ref=ref)
    actual = freeze_parent_active_prefix(parent, "m2", source, conversation_ref=ref)
    assert actual.anchor_identity == (ref, "m2")
    with pytest.raises(AttributeError):
        actual.anchor_identity = (ref, "missing-anchor")


def test_legacy_anonymous_freeze_is_only_an_unbound_structural_copy():
    source = [{"role": "user", "message_uid": "old-call-anchor", "content": "Visible original"}]
    parent = SimpleNamespace(_session_messages=source)
    frozen = freeze_parent_active_prefix(parent, "old-call-anchor")
    assert frozen.anchor_identity is None
    assert frozen is not source and frozen[0] is not source[0]
    assert source == [{"role": "user", "message_uid": "old-call-anchor", "content": "Visible original"}]
    with pytest.raises(NotingChildError, match="Anchor"):
        freeze_parent_active_prefix(parent, "missing-anchor", frozen)
