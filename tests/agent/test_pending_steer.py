"""Native steer insertion races over the single opt-in occurrence owner."""
import threading

from agent.agent_runtime_helpers import _requeue_pending_steer, apply_pending_steer_to_tool_results
from agent.pending_steer import (PendingSteerBuffer, append_claimed_batch, enable_locked,
                                 finish_native_turn, note_native_turn_started)
from tests.agent.test_steer import _bare_agent


def setup_owner():
    agent = _bare_agent()
    note_native_turn_started(agent, "native-turn")
    with agent._pending_steer_lock:
        owner = enable_locked(agent)
    return agent, owner


def submit(agent, owner, operation, text):
    with agent._pending_steer_lock:
        return owner.submit(owner.turn_id, operation, text)


def test_legacy_dormant_then_mixed_occurrences_share_one_order():
    agent = _bare_agent()
    assert agent.steer("old") is True
    assert agent._pending_steer == "old"
    note_native_turn_started(agent, "native-turn")
    with agent._pending_steer_lock:
        owner = enable_locked(agent)
    first = submit(agent, owner, "one", "same")
    agent.steer("legacy")
    second = submit(agent, owner, "two", "same")
    assert first["pending_id"] != second["pending_id"]
    messages = [{"role": "tool", "content": "result"}]
    apply_pending_steer_to_tool_results(agent, messages, 1)
    assert messages[-1]["content"].find("old\nsame\nlegacy\nsame") >= 0
    assert {r["state"] for r in owner.snapshot()["receipts"]} == {"consumed"}
    assert agent._pending_steer is owner


def test_claim_is_still_withdrawable_until_true_append():
    agent, owner = setup_owner()
    one = submit(agent, owner, "one", "a\nb")
    two = submit(agent, owner, "two", "a\nb")
    batch = agent._drain_pending_steer()
    with agent._pending_steer_lock:
        assert owner.withdraw("native-turn", two["pending_id"])["text"] == "a\nb"
    messages = []
    assert append_claimed_batch(agent, messages, batch)
    assert "a\nb\na\nb" not in messages[0]["content"]
    assert owner.withdraw("native-turn", one["pending_id"])["state"] == "already_consumed"
    assert owner.withdraw("native-turn", two["pending_id"])["state"] == "already_withdrawn"
    assert messages[0]["message_uid"]


def test_consumed_projection_reports_actual_middle_insert_without_mutating_prefix():
    from agent.pending_steer import native_source_boundary
    from types import SimpleNamespace

    agent, owner = setup_owner()
    frames = []
    agent._pending_steer_notify = lambda event, payload: frames.append((event, payload))
    submit(agent, owner, "keep", "correction")
    batch = agent._drain_pending_steer()
    # A real source tool address, followed by an existing Assistant: insertion is not at tail.
    messages = [{"role": "user", "content": "current", "message_uid": "current", "_row_id": 1, "_db_persisted": True},
                {"role": "tool", "content": "result", "tool_call_id": "repeated", "_tool_call_uid": "occurrence",
                 "message_uid": "result", "_row_id": 2, "_db_persisted": True},
                {"role": "assistant", "content": "later", "message_uid": "later"}]
    original = [dict(row) for row in messages]
    agent._persist_user_message_idx = 0
    agent.context_compressor = SimpleNamespace(compression_count=0)
    agent._pending_steer_source_boundary = lambda prefix, start: native_source_boundary(agent, prefix, start, [], 0)
    assert append_claimed_batch(agent, messages, batch, index=2)
    payload = next(payload for event, payload in frames if event == "steer.consumed")
    assert messages[:2] == original[:2] and messages[3] == original[2]
    assert payload["message"]["message_uid"] == messages[2]["message_uid"]
    assert payload["after_message_uid"] == "result"
    assert payload["predecessor"]["tool_call_uid"] == "occurrence"
    assert [row["message_uid"] for row in payload["source_messages"]] == ["current", "result"]
    assert payload["source_boundary"]["insertion_at_tail"] is False
    assert payload["source_boundary"]["all_rows_committed"] is True


def test_consumed_projection_does_not_mint_identity_for_unknown_predecessor():
    agent, owner = setup_owner()
    frames = []
    agent._pending_steer_notify = lambda event, payload: frames.append((event, payload))
    submit(agent, owner, "one", "correction")
    messages = [{"role": "tool", "content": "unknown result", "tool_call_id": "call"}]
    before = dict(messages[0])
    assert append_claimed_batch(agent, messages, agent._drain_pending_steer(), index=100)
    payload = next(payload for event, payload in frames if event == "steer.consumed")
    assert messages[0] == before
    assert payload["after_message_uid"] is None and payload["predecessor"]["message_uid"] is None
    assert "source_messages" not in payload and "source_boundary" not in payload
    assert payload["message"]["message_uid"] == messages[1]["message_uid"]


def test_consumed_projection_failure_cannot_veto_native_insertion():
    agent, owner = setup_owner()
    frames = []
    agent._pending_steer_notify = lambda event, payload: frames.append((event, payload))
    accepted = submit(agent, owner, "one", "correction")

    def unavailable(*_args):
        raise RuntimeError("observer unavailable")

    agent._pending_steer_source_boundary = unavailable
    messages = [{"role": "tool", "content": "result"}]
    assert append_claimed_batch(agent, messages, agent._drain_pending_steer())
    payload = next(payload for event, payload in frames if event == "steer.consumed")
    assert payload["message"]["message_uid"] == messages[-1]["message_uid"]
    assert "source_boundary" not in payload and "source_messages" not in payload
    assert owner.withdraw("native-turn", accepted["pending_id"])["state"] == "already_consumed"


def test_requeue_retains_original_ids_before_newer_enqueue():
    agent, owner = setup_owner()
    old = submit(agent, owner, "one", "old")
    batch = agent._drain_pending_steer()
    new = submit(agent, owner, "two", "new")
    _requeue_pending_steer(agent, batch)
    assert [r["pending_id"] for r in owner.snapshot()["pending"]] == [old["pending_id"], new["pending_id"]]
    assert str(agent._drain_pending_steer()) == "old\nnew"


def test_withdraw_and_real_insert_have_one_winner():
    agent, owner = setup_owner()
    receipt = submit(agent, owner, "one", "race")
    batch = agent._drain_pending_steer()
    barrier = threading.Barrier(3)
    result, messages = {}, []

    def insert():
        barrier.wait()
        result["inserted"] = append_claimed_batch(agent, messages, batch)

    def withdraw():
        barrier.wait()
        with agent._pending_steer_lock:
            result["withdraw"] = owner.withdraw("native-turn", receipt["pending_id"])

    workers = [threading.Thread(target=insert), threading.Thread(target=withdraw)]
    for worker in workers:
        worker.start()
    barrier.wait()
    for worker in workers:
        worker.join(3)
        assert not worker.is_alive()
    assert (bool(messages), result["withdraw"]["state"]) in {(True, "already_consumed"), (False, "withdrawn")}


def test_finalizer_closes_web_ack_but_retains_late_legacy_next_turn():
    agent, owner = setup_owner()
    first = submit(agent, owner, "one", "accepted")
    batch = finish_native_turn(agent)
    assert str(batch) == "accepted"
    assert submit(agent, owner, "late", "must reject")["accepted"] is False
    assert submit(agent, owner, "one", "accepted")["pending_id"] == first["pending_id"]
    assert agent.steer("legacy next") is True
    owner.handoff.update(state="dispatching", followup={"session_id": "r", "stored_session_id": "s", "turn_id": None})
    note_native_turn_started(agent, "next-turn")
    assert str(agent._drain_pending_steer()) == "legacy next"


def test_capacity_retry_and_retired_epoch_cannot_reanimate():
    agent, owner = setup_owner()
    for index in range(256):
        assert submit(agent, owner, str(index), str(index))["accepted"]
    before = owner.snapshot()
    assert submit(agent, owner, "overflow", "new")["state"] == "capacity"
    assert submit(agent, owner, "0", "0")["accepted"]
    assert submit(agent, owner, "0", "other")["reason"] == "operation_conflict"
    assert before == owner.snapshot()
    owner.reject("closed", include_reserved=True)
    for index in range(9):
        note_native_turn_started(agent, f"later-{index}")
    assert "native-turn" not in owner.epochs
    result = owner.submit("native-turn", "0", "0")
    assert result["accepted"] is False and result["state"] == "unknown_turn"
    assert owner.current.entries == {}


def test_reservation_prevents_stale_claim_and_hard_stop_marks_other_receipts():
    agent, owner = setup_owner()
    receipt = submit(agent, owner, "one", "pending")
    batch = agent._drain_pending_steer()
    with agent._pending_steer_lock:
        operation, stop = owner.reserve("native-turn", "interrupt")
    assert stop and operation["selected_ids"] == [receipt["pending_id"]]
    assert not append_claimed_batch(agent, [], batch)
    agent.clear_interrupt(hard_cancel=True)
    assert owner.snapshot()["pending"][0]["state"] == "handoff_reserved"
    owner.reject("stopped", include_reserved=True)
    assert owner.snapshot()["receipts"][0]["state"] == "rejected"


def test_pre_api_claim_cannot_mutate_previous_turn_prefix():
    from agent.turn_iteration_prep import _inject_steer_after_newest_tool_result
    agent, owner = setup_owner()
    accepted = submit(agent, owner, "one", "new correction")
    messages = [{"role": "user", "content": "previous"}, {"role": "tool", "content": "old result"},
                {"role": "assistant", "content": "previous answer"}, {"role": "user", "content": "current"}]
    prefix = [dict(row) for row in messages]
    batch = agent._drain_pending_steer()
    _inject_steer_after_newest_tool_result(agent, messages, batch, 1, "current")
    assert messages == prefix
    assert owner.snapshot()["pending"][0]["pending_id"] == accepted["pending_id"]
    messages.extend([{"role": "assistant", "tool_calls": []}, {"role": "tool", "content": "current result"}])
    _inject_steer_after_newest_tool_result(agent, messages, agent._drain_pending_steer(), 3, "current")
    assert messages[:4] == prefix and len(messages) == 7
    assert owner.withdraw("native-turn", accepted["pending_id"])["state"] == "already_consumed"


def test_interrupt_capacity_and_retry_do_not_mutate_queue():
    agent, owner = setup_owner()
    for index in range(64):
        op, stop = owner.reserve("native-turn", str(index))
        assert op["state"] == "nothing_pending" and not stop
    accepted = submit(agent, owner, "one", "waiting")
    before = owner.snapshot()
    op, stop = owner.reserve("native-turn", "overflow")
    assert op["reason"] == "operation_capacity" and not stop
    retry, stop = owner.reserve("native-turn", "0")
    assert retry["state"] == "nothing_pending" and not stop
    assert owner.snapshot() == before and owner.current.entries[accepted["pending_id"]].state == "pending"


def test_plain_legacy_drain_requeue_cannot_overwrite_new_owner():
    agent = _bare_agent()
    agent.steer("drained before opt-in")
    legacy = agent._drain_pending_steer()
    note_native_turn_started(agent, "native-turn")
    with agent._pending_steer_lock:
        owner = enable_locked(agent)
    new = submit(agent, owner, "new", "newer")
    _requeue_pending_steer(agent, legacy)
    assert agent._pending_steer is owner
    assert owner.snapshot()["pending"][-1]["pending_id"] == new["pending_id"]
    assert str(agent._drain_pending_steer()) == "drained before opt-in\nnewer"
