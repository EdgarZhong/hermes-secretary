"""Actual main assembly/response and runtime tail paths for the V1.6 delivery contract."""
import json
import time
from types import SimpleNamespace

import pytest

from hermes_state_secretary_schedule import reminder_append_pending_conn, reminder_pending_count_conn
from secretary.framework_messages import flush_framework_messages, publish_framework_message
from tests.secretary.test_noting_surface import _agent, _requests, _turn, runtime as _surface_runtime


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    yield from _surface_runtime.__wrapped__(tmp_path, monkeypatch)


def seed(agent, entry_id="1", due=1700000000):
    entry = {"entry_id": entry_id, "entry_type": "user_commitment", "fields": {"what": "报告"},
             "schedule": {"expression": "tomorrow"}}
    return agent._session_db._execute_write(lambda conn: reminder_append_pending_conn(
        conn, agent._secretary_conversation_ref, "报告到期", source_timestamp=due,
        entry_payload=entry, dedup_key=entry_id))


def pending(agent):
    return agent._session_db._execute_write(lambda conn: reminder_pending_count_conn(
        conn, agent._secretary_conversation_ref))


def deferred_rows(agent):
    return [row for row in agent._session_db.get_messages(agent.session_id)
            if str(row["content"]).startswith("<deferred-reminder>")]


def test_real_turn_batches_two_occurrences_live_durable_and_success_ack(runtime):
    db, _config = runtime
    agent = _agent(db)
    try:
        seed(agent, "1")
        seed(agent, "2", 1700000001)
        seen = _requests(agent)
        _turn(agent, "继续")
        rows = deferred_rows(agent)
        assert len(rows) == 1 and pending(agent) == 0
        carrier = rows[0]["content"]
        assert "<timestamp>" not in carrier
        assert carrier.startswith("<deferred-reminder>\n以下提醒已到期。\n")
        entries = json.loads(carrier.splitlines()[2])
        assert [e["entry_id"] for e in entries] == ["1", "2"]
        assert all("schedule" not in e and "due_at" in e for e in entries)
        assert entries[0]["fields"] == {"what": "报告"}
        assert any(carrier in str(row["content"]) for row in seen[0]["messages"])
        assert any(row["message_uid"] == rows[0]["message_uid"] for row in agent._session_messages)
        _turn(agent, "下一轮")
        assert len(deferred_rows(agent)) == 1
    finally:
        agent.close()


def test_context_selection_drop_keeps_pending_then_rematerializes(runtime, monkeypatch):
    db, _config = runtime
    agent = _agent(db)
    try:
        seed(agent)
        seen = _requests(agent)
        with monkeypatch.context() as m:
            m.setattr("agent.conversation_loop._apply_context_engine_selection",
                          lambda _agent, api, *_a, **_k: [row for row in api
                              if "<deferred-reminder>" not in str(row.get("content"))])
            _turn(agent)
        assert pending(agent) == 1
        assert not any("<deferred-reminder>" in str(row.get("content")) for row in seen[0]["messages"])
        # Simulate a context path that dropped the row; durable history is retained.
        history = [row for row in agent._session_messages if "<deferred-reminder>" not in str(row.get("content"))]
        result = agent.run_conversation("重试", conversation_history=history, title_user_message="")
        assert result["completed"] and pending(agent) == 0
        assert len(deferred_rows(agent)) == 2
    finally:
        agent.close()


def test_failed_provider_reuses_same_durable_batch_and_restart(runtime, monkeypatch):
    db, _config = runtime
    agent = _agent(db)
    try:
        seed(agent)
        agent._api_max_retries = 0
        agent.client.chat.completions.create.side_effect = RuntimeError("provider down")
        result = agent.run_conversation("继续", title_user_message="")
        assert result["failed"] and pending(agent) == 1
        original = deferred_rows(agent)[0]
        sid = agent.session_id
        agent.close()
        agent = _agent(db, existing=False, session_id=sid)
        _requests(agent)
        result = agent.run_conversation("恢复", conversation_history=db.get_messages_as_conversation(sid), title_user_message="")
        assert result["completed"] and pending(agent) == 0
        assert [row["message_uid"] for row in deferred_rows(agent)] == [original["message_uid"]]
    finally:
        agent.close()


def test_framework_idle_busy_fence_same_row_and_anchor_marker(runtime):
    db, _config = runtime
    agent = _agent(db)
    try:
        _requests(agent)
        _turn(agent, "事实")
        anchor = db.get_foreground_anchor(conversation_ref=agent._secretary_conversation_ref)
        assert publish_framework_message(agent, "Background: notebook updated at T", display_metadata={"noting_run_output": True})
        row = db.get_messages(agent.session_id)[-1]
        assert row["content"] == agent._session_messages[-1]["content"]
        assert row["message_uid"] == agent._session_messages[-1]["message_uid"]
        assert "<timestamp>" not in row["content"]
        assert db.get_foreground_anchor(conversation_ref=agent._secretary_conversation_ref) == anchor
        agent._secretary_main_turn_running = True
        count = len(db.get_messages(agent.session_id))
        assert publish_framework_message(agent, "派发")
        assert len(db.get_messages(agent.session_id)) == count
        assert flush_framework_messages(agent) == 0
        agent._secretary_main_turn_running = False
        fence = SimpleNamespace()
        agent._active_compression_commit_fence = fence
        assert flush_framework_messages(agent) == 0
        del agent._active_compression_commit_fence
        deadline = time.monotonic() + 2
        while len(db.get_messages(agent.session_id)) == count and time.monotonic() < deadline:
            time.sleep(.01)
        assert len(db.get_messages(agent.session_id)) == count + 1
        assert flush_framework_messages(agent) == 0
        assert db.get_foreground_anchor(conversation_ref=agent._secretary_conversation_ref) != anchor
    finally:
        agent.close()


@pytest.mark.parametrize("disabled", ["global", "local", "auxiliary"])
def test_delivery_disabled_paths_remain_native(runtime, disabled):
    db, config = runtime
    agent = _agent(db)
    try:
        seed(agent)
        if disabled == "global":
            config.write_text("noting:\n  enabled: false\n")
        elif disabled == "local":
            db.notebook_set_local_enabled(agent._secretary_conversation_ref, False)
        else:
            agent._secretary_reminder_injection_disabled = True
            agent.side_agent = True
        seen = _requests(agent)
        _turn(agent)
        assert pending(agent) == 1 and not deferred_rows(agent)
        if disabled == "auxiliary":
            assert not publish_framework_message(agent, "禁止写入")
        assert not any("<deferred-reminder>" in str(row.get("content")) for row in seen[0]["messages"])
    finally:
        agent.close()


def test_native_compaction_pass_refuses_batch_then_same_turn_retries(runtime, monkeypatch):
    from agent import conversation_loop

    db, _config = runtime
    agent = _agent(db)
    try:
        seed(agent)
        seen = _requests(agent)
        assemblies = []
        native_assembly = conversation_loop.assemble_api_request
        compressor = agent.context_compressor
        compressor.threshold_tokens = 180000
        compressor.context_length = 256000
        monkeypatch.setattr(conversation_loop, "_midturn_request_pressure_tokens", lambda *_a: 180001)
        monkeypatch.setattr(compressor, "should_defer_preflight_to_real_usage", lambda _t: False)
        monkeypatch.setattr(compressor, "get_active_compression_failure_cooldown", lambda: None)
        monkeypatch.setattr(compressor, "should_compress", lambda _t: not assemblies or len(assemblies) == 1)
        monkeypatch.setattr("secretary.noting_runtime.maybe_admit_force_from_pressure", lambda *_a, **_k: None)
        monkeypatch.setattr("agent.turn_preflight.ensure_compression_feasibility_checked", lambda *_a: None)

        from functools import wraps

        @wraps(native_assembly)
        def assembly(*args, **kwargs):
            result = native_assembly(*args, **kwargs)
            assemblies.append({"durable": len(deferred_rows(agent)), "pending": pending(agent)})
            agent.compression_enabled = True  # prologue stayed on its native non-compress path
            return result

        def compact(messages, system, **kwargs):
            assert pending(agent) == 1 and not deferred_rows(agent)
            return list(messages), system

        monkeypatch.setattr(conversation_loop, "assemble_api_request", assembly)
        monkeypatch.setattr(agent, "_compress_context", compact)
        db.append_message(agent.session_id, "assistant", "前一轮事实")
        result = agent.run_conversation("继续", conversation_history=db.get_messages_as_conversation(agent.session_id), title_user_message="")
        assert result["completed"]
        assert assemblies[0] == {"durable": 0, "pending": 1}
        assert assemblies[1]["durable"] == 0
        assert assemblies[-1]["durable"] == 1
        assert pending(agent) == 0 and len(seen) == 1
    finally:
        agent.close()


def test_retired_settlement_ignores_unmaterialized_and_dropped_rows(runtime):
    from hermes_state_secretary_schedule import reminder_settle_retired_conn
    db, _config = runtime
    agent = _agent(db)
    try:
        first = seed(agent, "1")
        assert db._execute_write(lambda conn: reminder_settle_retired_conn(conn, agent._secretary_conversation_ref)) == 0
        assert pending(agent) == 1
        from secretary.reminder_request import inject_pending_reminders
        inject_pending_reminders(agent, agent._session_messages)
        uid = agent._session_messages[-1]["message_uid"]
        second = seed(agent, "2")
        def retire(conn):
            conn.execute("UPDATE messages SET active=0,compacted=1 WHERE message_uid=?", (uid,))
            return reminder_settle_retired_conn(conn, agent._secretary_conversation_ref)
        assert db._execute_write(retire) == 1
        assert db._read_one("SELECT status FROM secretary_pending_reminders WHERE reminder_id=?", (first,))[0] == "terminated"
        assert db._read_one("SELECT status FROM secretary_pending_reminders WHERE reminder_id=?", (second,))[0] == "pending"
    finally:
        agent.close()


def test_native_tail_flush_failure_does_not_materialize_or_ack(runtime, monkeypatch):
    from secretary.reminder_request import inject_pending_reminders
    db, _config = runtime
    agent = _agent(db)
    try:
        seed(agent)
        monkeypatch.setattr(agent, "_flush_messages_to_session_db", lambda *_a: False)
        assert inject_pending_reminders(agent, agent._session_messages)[0] == 0
        assert pending(agent) == 1
        assert not deferred_rows(agent)
        assert not agent._secretary_inflight_reminders
    finally:
        agent.close()


def _switch_framework_owner(agent, *, branch=False):
    """Exercise native reset/branch identity seams on a real runtime and database."""
    from agent.prompt_cache_scope import initialize_conversation_identity
    from hermes_cli.cli_commands_mixin import _sync_agent_to_session

    db = agent._session_db
    old_sid = agent.session_id
    sid = "delivery-branch" if branch else "delivery-new"
    db.create_session(sid, source="cli", parent_session_id=old_sid if branch else None,
                      model_config={"_branched_from": old_sid} if branch else None)
    if branch:
        db.append_messages_batch(sid, db.get_messages_as_conversation(old_sid))
        cli = SimpleNamespace(agent=agent, conversation_history=db.get_messages_as_conversation(sid))
        _sync_agent_to_session(cli, sid, parent_session_id=old_sid, reason="branched")
    else:
        db.end_session(old_sid, "new_session")
        agent.session_id = sid
        agent.reset_session_state()
        initialize_conversation_identity(agent)
    agent._session_messages = db.get_messages_as_conversation(sid)
    return sid


@pytest.mark.parametrize("branch", [False, True], ids=["new", "branch"])
def test_framework_busy_queue_cannot_cross_native_owner_switch(runtime, branch):
    db, _config = runtime
    agent = _agent(db)
    try:
        _requests(agent)
        _turn(agent, "原会话事实")
        old_sid, old_ref = agent.session_id, agent._secretary_conversation_ref
        agent._secretary_main_turn_running = True
        assert publish_framework_message(agent, "旧 owner 完成通知", expected_conversation_ref=old_ref)
        sid = _switch_framework_owner(agent, branch=branch)
        assert agent._secretary_conversation_ref != old_ref
        # Real main Turn ends through note_main_turn_finished and flushes the queue.
        result = agent.run_conversation("新路径", conversation_history=db.get_messages_as_conversation(sid),
                                        title_user_message="")
        assert result["completed"]
        assert not agent._secretary_framework_messages
        assert not any("旧 owner 完成通知" in str(row["content"])
                       for target in (old_sid, sid) for row in db.get_messages(target))
        assert not any("旧 owner 完成通知" in str(row["content"]) for row in agent._session_messages)
        assert not publish_framework_message(agent, "晚到的旧 owner 通知", expected_conversation_ref=old_ref)
        assert publish_framework_message(agent, "当前 owner 通知",
                                         expected_conversation_ref=agent._secretary_conversation_ref)
        assert "当前 owner 通知" in db.get_messages(sid)[-1]["content"]
    finally:
        agent.close()


def test_framework_queue_survives_native_same_owner_compression_rotation(runtime):
    from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER

    db, _config = runtime
    agent = _agent(db)
    try:
        _requests(agent)
        _turn(agent, "压缩前事实")
        old_sid, ref = agent.session_id, agent._secretary_conversation_ref
        agent._secretary_main_turn_running = True
        assert publish_framework_message(agent, "压缩后完成通知", expected_conversation_ref=ref)
        holder = "delivery-owner-rotation"
        assert db.try_acquire_compression_lock(old_sid, holder)
        db.publish_compression_child(
            parent_session_id=old_sid, child_session_id="delivery-compacted", source="cli",
            system_prompt=agent._cached_system_prompt, compression_lock_holder=holder,
            messages=[{"role": "user", "content": SUMMARY_PREFIX + "handoff\n" + _SUMMARY_END_MARKER,
                       "_compressed_summary": True}],
        )
        db.release_compression_lock(old_sid, holder)
        _turn(agent, "压缩后继续")
        assert agent.session_id == "delivery-compacted" and agent._secretary_conversation_ref == ref
        durable = [row for row in db.get_messages(agent.session_id) if "压缩后完成通知" in str(row["content"])]
        live = [row for row in agent._session_messages if "压缩后完成通知" in str(row["content"])]
        assert len(durable) == len(live) == 1 and durable[0]["message_uid"] == live[0]["message_uid"]
        assert not any("压缩后完成通知" in str(row["content"]) for row in db.get_messages(old_sid))
        assert flush_framework_messages(agent) == 0
    finally:
        agent.close()


@pytest.mark.parametrize("disabled", ["global", "local"])
def test_framework_admitted_queue_flushes_after_switch_is_disabled(runtime, disabled):
    from secretary.noting_runtime import note_main_turn_finished

    db, config = runtime
    agent = _agent(db)
    try:
        _requests(agent)
        _turn(agent)
        agent._secretary_main_turn_running = True
        assert publish_framework_message(agent, "已提交后关闭")
        if disabled == "global":
            config.write_text("noting:\n  enabled: false\n")
        else:
            db.notebook_set_local_enabled(agent._secretary_conversation_ref, False)
        note_main_turn_finished(agent)
        assert "已提交后关闭" in db.get_messages(agent.session_id)[-1]["content"]
        assert db.get_messages(agent.session_id)[-1]["message_uid"] == agent._session_messages[-1]["message_uid"]
        assert not agent._secretary_framework_messages and flush_framework_messages(agent) == 0
    finally:
        agent.close()


@pytest.mark.parametrize("boundary", ["native_flush", "append_transaction", "stale_ref"])
def test_framework_owner_change_at_write_boundary_aborts_both_writes(runtime, monkeypatch, boundary):
    db, _config = runtime
    agent = _agent(db)
    try:
        _requests(agent)
        _turn(agent)
        old_sid, old_ref, old_live = agent.session_id, agent._secretary_conversation_ref, agent._session_messages
        if boundary == "native_flush":
            native = agent._flush_messages_to_session_db
            def switch_after_flush(messages):
                result = native(messages)
                _switch_framework_owner(agent)
                return result
            monkeypatch.setattr(agent, "_flush_messages_to_session_db", switch_after_flush)
        else:
            native = db.append_messages_batch
            def switch_before_transaction(session_id, messages, **kwargs):
                if any("竞态通知" in str(row.get("content")) for row in messages):
                    if boundary == "stale_ref":
                        # CLI changes session_id before resetting/rebinding ref; do not
                        # accept the old ref while the physical target is already new.
                        db.create_session("delivery-new", source="cli")
                        agent.session_id = "delivery-new"
                    else:
                        _switch_framework_owner(agent)
                return native(session_id, messages, **kwargs)
            monkeypatch.setattr(db, "append_messages_batch", switch_before_transaction)
        assert publish_framework_message(agent, "竞态通知", expected_conversation_ref=old_ref)
        assert not agent._secretary_framework_messages
        assert not any("竞态通知" in str(row["content"])
                       for sid in (old_sid, "delivery-new") for row in db.get_messages(sid))
        assert not any("竞态通知" in str(row["content"]) for row in old_live + agent._session_messages)
        assert flush_framework_messages(agent) == 0
    finally:
        agent.close()


def test_framework_publisher_rechecks_committed_owner_after_waiting_for_lock(runtime):
    import threading
    from secretary.framework_messages import _lock

    db, _config = runtime
    agent = _agent(db)
    result = []
    ready = threading.Event()
    try:
        _requests(agent)
        _turn(agent)
        old_sid, committed_ref = agent.session_id, agent._secretary_conversation_ref
        def late_child_notice():
            ready.set()
            result.append(publish_framework_message(
                agent, "Child 提交的旧 owner 通知", expected_conversation_ref=committed_ref))
        with _lock(agent):
            thread = threading.Thread(target=late_child_notice)
            thread.start()
            assert ready.wait(2)
            new_sid = _switch_framework_owner(agent)
        thread.join(2)
        assert not thread.is_alive() and result == [False]
        assert not getattr(agent, "_secretary_framework_messages", None)
        assert not any("Child 提交的旧 owner 通知" in str(row["content"])
                       for sid in (old_sid, new_sid) for row in db.get_messages(sid))
    finally:
        agent.close()


@pytest.mark.parametrize("switch_owner", [False, True], ids=["same-owner", "new-owner"])
def test_force_producer_uses_admission_owner_when_runtime_switches(runtime, monkeypatch, switch_owner):
    from secretary import noting_runtime

    db, _config = runtime
    agent = _agent(db)
    admissions = []
    try:
        _requests(agent)
        _turn(agent, "Force 准入事实")
        old_sid, old_ref = agent.session_id, agent._secretary_conversation_ref
        agent.context_compressor.context_length = 130000
        agent.context_compressor.threshold_tokens = 75000
        native_admit = noting_runtime.try_admit_force
        def admit_then_switch(*args, **kwargs):
            decision = native_admit(*args, **kwargs)
            assert decision.action == "admit"
            if switch_owner:
                _switch_framework_owner(agent)
            return decision
        monkeypatch.setattr(noting_runtime, "try_admit_force", admit_then_switch)
        monkeypatch.setattr("secretary.noting_child.spawn_noting_task",
                            lambda parent, admission, **kwargs: admissions.append(admission))
        assert noting_runtime.maybe_admit_force_from_pressure(agent, 64000).startswith("admit")
        assert len(admissions) == 1 and admissions[0].conversation_ref == old_ref
        notices = [row for row in db.get_messages(old_sid)
                   if "临近上下文上限，notebook 更新任务已派发。" in str(row["content"])]
        if switch_owner:
            assert not notices
            assert not any("<framework-message>" in str(row["content"])
                           for row in db.get_messages(agent.session_id))
            assert not any("<framework-message>" in str(row["content"]) for row in agent._session_messages)
        else:
            assert len(notices) == 1 and notices[0]["message_uid"] == agent._session_messages[-1]["message_uid"]
        assert not getattr(agent, "_secretary_framework_messages", None)
    finally:
        agent.close()


def test_partial_request_ack_releases_only_the_batch_actually_carried(runtime):
    from secretary.reminder_request import inject_pending_reminders, verify_carried_reminders, acknowledge_carried_reminders
    db, _config = runtime
    agent = _agent(db)
    try:
        first = seed(agent, "1")
        inject_pending_reminders(agent, agent._session_messages)
        first_carrier = agent._session_messages[-1]["content"]
        second = seed(agent, "2")
        inject_pending_reminders(agent, agent._session_messages)
        assert verify_carried_reminders(agent, [{"role": "user", "content": first_carrier}])
        assert agent._secretary_inflight_reminders == [first]
        assert acknowledge_carried_reminders(agent) == 1
        assert db._read_one("SELECT status FROM secretary_pending_reminders WHERE reminder_id=?", (second,))[0] == "pending"
    finally:
        agent.close()
