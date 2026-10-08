"""Native early persistence is mandatory only for an accepted active Reminder."""
import json
import time
from datetime import datetime, timezone

import pytest

from secretary import reminders, schedules
from tests.secretary.reminder_runtime import arm_native_reminder, persist_native_carrier
from tests.secretary.test_noting_surface import _agent, _requests, runtime as _native_runtime


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    yield from _native_runtime.__wrapped__(tmp_path, monkeypatch)


def armed_agent(runtime):
    db, config = runtime
    config.write_text("model:\n  context_length: 196000\nnoting:\n  enabled: true\n")
    db.create_session("surface-main", source="cli")
    ref = db.resolve_conversation_ref("surface-main")
    row = arm_native_reminder(db, ref, {"kind": "once", "run_at": datetime.fromtimestamp(
        time.time() - 30, timezone.utc).isoformat()}, "durable delivery")
    agent = _agent(db, existing=False)
    claim = schedules.claim_due(db, row["schedule_id"], owner="native")
    receipt = reminders.admit_active_reminder(db, claim, session_id=agent.session_id)
    return db, ref, agent, claim, receipt


@pytest.mark.parametrize("change", ["local_off", "cancel", "expire", "reclaim", "changed"])
def test_native_transaction_rejects_claim_changes_after_admission(runtime, change):
    from tests.secretary.test_active_reminder_admission import invalidate
    db, ref, agent, claim, receipt = armed_agent(runtime)
    try:
        invalidate(db, ref, claim, "expired" if change == "expire" else change)
        seen = _requests(agent)
        result = agent.run_conversation(receipt["resolved"]["text"], title_user_message="")
        assert result["failed"] and result["failure_retryable"] and result["api_calls"] == 0
        assert not seen and not any(r["role"] == "user" for r in db.get_messages(agent.session_id))
        assert agent._pending_cli_user_message is None
        assert agent._persist_user_message_idx is None
        assert all(r["role"] != "user" for r in result["messages"])
        if change == "reclaim":
            assert db._read_one("SELECT claim_owner FROM secretary_schedule_registry")[0] == "new"
    finally:
        agent.close()
    assert not any(r["role"] == "user" for r in db.get_messages("surface-main"))


@pytest.mark.parametrize("active", [True, False])
def test_failed_native_write_stops_only_active_before_compaction_and_sdk(runtime, monkeypatch, active):
    db, _ref, agent, _claim, receipt = armed_agent(runtime)
    original = db.append_messages_batch
    def fail(*_args, **_kwargs):
        raise OSError("controlled disk failure")
    monkeypatch.setattr(db, "append_messages_batch", fail)
    seen = _requests(agent)
    if active:
        from agent.turn_context_compaction import run_turn_start_compaction
        monkeypatch.setattr("agent.turn_context_compaction.run_turn_start_compaction",
                            lambda *a, **k: pytest.fail("uncommitted active entered compaction"))
    try:
        result = agent.run_conversation(receipt["resolved"]["text"] if active else "ordinary", title_user_message="")
        assert len(seen) == (0 if active else 1)
        if active:
            assert result["failed"] and result["api_calls"] == 0
            assert result["turn_exit_reason"] == "secretary_delivery_uncommitted"
            assert not result.get("compression_exhausted") and result["messages"] == []
            monkeypatch.setattr(db, "append_messages_batch", original)
            agent._persist_session(agent._session_messages)
            assert not any(r["role"] == "user" for r in db.get_messages(agent.session_id))
            monkeypatch.setattr("agent.turn_context_compaction.run_turn_start_compaction", run_turn_start_compaction)
            next_result = agent.run_conversation("next ordinary input", conversation_history=result["messages"], title_user_message="")
            assert next_result["completed"] and len(seen) == 1
            users = [r for r in db.get_messages(agent.session_id) if r["role"] == "user"]
            assert len(users) == 1 and "durable delivery" not in users[0]["content"]
    finally:
        agent.close()


def test_transaction_rollback_and_unknown_commit_require_native_row_proof(runtime, monkeypatch):
    db, _ref, agent, claim, receipt = armed_agent(runtime)
    witness = reminders.active_admission_witness(receipt["resolved"]["text"])
    original = db.append_messages_batch
    def rollback(*args, **kwargs):
        callback = kwargs["before_commit"]
        def reject(conn, sid, inserted):
            callback(conn, sid, inserted)
            raise OSError("after finalize, before COMMIT")
        return original(*args, **{**kwargs, "before_commit": reject})
    monkeypatch.setattr(db, "append_messages_batch", rollback)
    with pytest.raises(OSError):
        persist_native_carrier(db, agent.session_id, receipt["resolved"]["text"])
    assert not witness.durable(db)
    assert db._read_one("SELECT state FROM secretary_schedule_registry")[0] == "pending"
    assert not any(r["role"] == "user" for r in db.get_messages(agent.session_id))
    def unknown(*args, **kwargs):
        original(*args, **kwargs)
        raise OSError("COMMIT succeeded, return was lost")
    monkeypatch.setattr(db, "append_messages_batch", unknown)
    seen = _requests(agent)
    try:
        result = agent.run_conversation(receipt["resolved"]["text"], title_user_message="")
        assert result["completed"] and len(seen) == 1
        assert witness.committed is False and witness.durable(db)
        assert not reminders.recover_active_reminder(db, receipt)
        assert schedules.claim_due(db, claim["schedule_id"], owner="new") is None
    finally:
        monkeypatch.setattr(db, "append_messages_batch", original)
        agent.close()
    assert len([r for r in db.get_messages(agent.session_id) if r["role"] == "user"]) == 1


def test_plain_json_carrier_has_no_settlement_permission_and_chunks_cannot_split(runtime):
    db, _ref, agent, claim, receipt = armed_agent(runtime)
    text = json.loads(json.dumps(receipt["resolved"]["text"]))
    assert reminders.active_admission_witness(text) is None
    try:
        seen = _requests(agent)
        result = agent.run_conversation(text, title_user_message="")
        assert result["completed"] and len(seen) == 1
        assert db._read_one("SELECT claim_token FROM secretary_schedule_registry")[0] == claim["claim_token"]
        with pytest.raises(ValueError, match="chunk_rows"):
            db.append_messages_batch(agent.session_id, [{"role": "user", "content": "never"}],
                                     chunk_rows=1, before_commit=lambda *a: None)
        assert not any(r["content"] == "never" for r in db.get_messages(agent.session_id))
    finally:
        agent.close()


def test_old_carrier_cannot_write_under_reclaimed_native_turn_lease(runtime):
    from hermes_state import SessionDB
    from hermes_state_errors import SessionTurnLeaseLostError
    db, _ref, agent, claim, receipt = armed_agent(runtime)
    other = SessionDB(db.db_path)
    try:
        assert db.try_acquire_session_turn_lease(agent.session_id, "old", ttl_seconds=.1)
        db._execute_write(lambda c: c.execute("UPDATE session_turn_leases SET expires_at=?", (time.time() - 1,)))
        assert other.try_acquire_session_turn_lease(agent.session_id, "new", ttl_seconds=30)
        messages = [{"role": "user", "content": receipt["resolved"]["text"], "timestamp": claim["next_run_at"]}]
        rows = [dict(messages[0])]
        callback = reminders.active_delivery_batch_callback(db, messages, rows)
        with pytest.raises(SessionTurnLeaseLostError):
            db.append_messages_batch(agent.session_id, rows, turn_lease_holder="old", before_commit=callback)
        assert not any(r["role"] == "user" for r in db.get_messages(agent.session_id))
        assert db._read_one("SELECT claim_token FROM secretary_schedule_registry")[0] == claim["claim_token"]
    finally:
        other.release_session_turn_lease(agent.session_id, "new")
        other.close()
        agent.close()
