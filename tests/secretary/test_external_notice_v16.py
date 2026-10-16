"""C07 through real Main runtimes, trigger glue and native dispatch recording."""

import time
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from secretary import noting_runtime as rt
from secretary.framework_messages import flush_framework_messages, publish_framework_message
from secretary.noting_scope import owning_db_scope
from secretary.noting_timers import cancel_idle_timer
from tests.secretary.test_noting_surface import _agent, _requests, _turn, runtime as _surface_runtime
from tests.secretary.test_v16_delivery import _switch_framework_owner

NOTICE = ("Background: Noting is unavailable because this Conversation's latest model request used an external agent runtime. "
          "Notebook updates can resume after native execution resumes.")


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    for db, config in _surface_runtime.__wrapped__(tmp_path, monkeypatch):
        config.write_text("noting:\n  enabled: true\n  idle:\n    enabled: true\n    delay_seconds: 3600\n    threshold_tokens: 10000\n")
        yield db, config


def prepare(db):
    agent = _agent(db)
    db.append_message(agent.session_id, "user", "已有会话事实", message_uid="fact")
    db.append_message(agent.session_id, "assistant", "已有回复", message_uid="reply")
    agent._session_messages = db.get_messages_as_conversation(agent.session_id)
    agent.context_compressor.context_length = 130000
    agent.context_compressor.threshold_tokens = 75000
    agent.context_compressor.last_real_prompt_tokens = 10000
    return agent


def external_dispatch(agent, *, persist=True):
    # Script the existing final-dispatch notifier, not a model/provider route guess.
    with rt.main_model_request_scope(agent, {}):
        rt.record_main_model_dispatch(source="external")
    assert agent._secretary_last_main_execution == "external"
    if persist:
        assert rt.persist_main_execution_source(agent)


def notices(agent):
    return [r for r in agent._session_db.get_messages(agent.session_id) if NOTICE in str(r["content"])]


def assert_notice(agent, count=1):
    rows = notices(agent)
    assert len(rows) == count
    live = [r for r in agent._session_messages if NOTICE in str(r["content"])]
    assert [r["message_uid"] for r in rows] == [r["message_uid"] for r in live]
    for row in rows:
        assert row["content"] == "<framework-message>\n" + NOTICE + "\n</framework-message>"
        assert row["role"] == "user" and "noting_run_output" not in row["display_metadata"]
    assert agent._session_db.get_foreground_anchor(conversation_ref=agent._secretary_conversation_ref)["message_uid"] == rows[-1]["message_uid"]


def assert_no_work(db):
    for table in ("secretary_noting_admissions", "secretary_noting_children", "secretary_notebook_snapshots",
                  "secretary_pending_reminders"):
        assert db._read_one(f"SELECT COUNT(*) FROM {table}")[0] == 0


@pytest.mark.parametrize("trigger", ["force", "idle", "cold-catchup"])
def test_external_trigger_glue_dual_writes_notice_without_noting_work(runtime, monkeypatch, trigger):
    db, _config = runtime
    agent = prepare(db)
    try:
        external_dispatch(agent)
        monkeypatch.setattr(rt, "_freeze_and_log_attempt", lambda *_a: pytest.fail("D01 must reject before freeze"))
        if trigger == "force":
            outcome = rt.maybe_admit_force_from_pressure(agent, 64000)
        else:
            ref, sid = agent._secretary_conversation_ref, agent.session_id
            db.noting_idle_turn_finished(ref, time.time() - 1000, due_at=time.time() - 1)
            if trigger == "cold-catchup":
                agent.close()
                agent = _agent(db, existing=False, session_id=sid)
                agent._session_messages = db.get_messages_as_conversation(sid)
                # Cold runtime must have the native last-request usage, not fabricate a reading.
                agent.context_compressor.last_real_prompt_tokens = 10000
            outcome = rt.maybe_run_idle_noting(agent, db, ref)
        assert outcome == "skip:external_main_execution"
        assert_notice(agent)
        assert_no_work(db)
        assert db.notebook_local_enabled(agent._secretary_conversation_ref)
        assert db.notebook_current(agent._secretary_conversation_ref) is None
    finally:
        agent.close()


def test_real_idle_timer_external_rejection_publishes_once(runtime, monkeypatch):
    db, config = runtime
    config.write_text("noting:\n  enabled: true\n  idle:\n    enabled: true\n    delay_seconds: 0.05\n    threshold_tokens: 10000\n")
    agent = prepare(db)
    try:
        external_dispatch(agent)
        monkeypatch.setattr(rt, "_freeze_and_log_attempt", lambda *_a: pytest.fail("External must not freeze"))
        assert rt.note_main_turn_finished(agent)
        deadline = time.monotonic() + 2
        while not notices(agent) and time.monotonic() < deadline:
            time.sleep(.01)
        assert_notice(agent)
        assert rt.maybe_run_idle_noting(agent, db, agent._secretary_conversation_ref) == "skip:idle_trigger_produced"
        assert_no_work(db)
    finally:
        cancel_idle_timer(db, agent._secretary_conversation_ref)
        agent.close()


def test_repeated_force_and_idle_rejections_share_suppression_native_dispatch_resets(runtime):
    db, _config = runtime
    agent = prepare(db)
    try:
        external_dispatch(agent)
        for _ in range(3):
            assert rt.maybe_admit_force_from_pressure(agent, 64000) == "skip:external_main_execution"
        ref = agent._secretary_conversation_ref
        db.noting_idle_turn_finished(ref, time.time() - 1000, due_at=time.time() - 1)
        assert rt.maybe_run_idle_noting(agent, db, ref) == "skip:external_main_execution"
        assert_notice(agent)
        # No request is dispatched by this empty end hook; it must not reset suppression.
        rt.note_main_turn_finished(agent)
        rt.maybe_admit_force_from_pressure(agent, 64000)
        assert len(notices(agent)) == 1
        seen = _requests(agent)
        result = agent.run_conversation("真实 Native 请求", title_user_message="",
                                        conversation_history=db.get_messages_as_conversation(agent.session_id))
        assert result["completed"]
        assert seen and rt.main_execution_for_force(agent) == "native"
        assert ref not in agent._secretary_external_notice_refs
        external_dispatch(agent)
        assert rt.maybe_admit_force_from_pressure(agent, 64000) == "skip:external_main_execution"
        assert_notice(agent, 2)
        assert_no_work(db)
    finally:
        agent.close()


@pytest.mark.parametrize("mode", ["global-off", "local-off", "under-threshold", "capability", "unknown",
                                   "no-live-owner", "review", "child"])
def test_non_d01_conditions_produce_no_external_notice(runtime, monkeypatch, mode):
    db, config = runtime
    agent = prepare(db)
    dispatched = []
    monkeypatch.setattr("secretary.noting_child.spawn_noting_task", lambda *args, **kwargs: dispatched.append(args))
    try:
        if mode != "unknown":
            external_dispatch(agent)
        setup = {
            "global-off": lambda: config.write_text("noting:\n  enabled: false\n"),
            "local-off": lambda: db.notebook_set_local_enabled(agent._secretary_conversation_ref, False),
            "capability": lambda: setattr(agent.context_compressor, "context_length", 120000),
            "no-live-owner": lambda: setattr(agent, "_session_messages", None),
            "review": lambda: setattr(agent, "_persist_disabled", True),
            "child": lambda: setattr(agent, "_parent_session_id", "parent"),
        }
        setup.get(mode, lambda: None)()
        outcome = rt.maybe_admit_force_from_pressure(agent, 63999 if mode == "under-threshold" else 64000)
        assert not notices(agent)
        assert not getattr(agent, "_secretary_framework_messages", None)
        if mode == "unknown":
            assert outcome.startswith("admit") and len(dispatched) == 1
            assert not hasattr(agent, "_secretary_last_main_execution")
        else:
            assert not dispatched
        if mode in {"review", "child"}:
            assert not rt.note_actual_main_execution(agent, "native")
            assert agent._secretary_last_main_execution == "external"
    finally:
        agent.close()


@pytest.mark.parametrize("disabled", [None, "global", "local"])
def test_idle_unmet_or_disabled_conditions_have_no_notice(runtime, disabled):
    db, config = runtime
    agent = prepare(db)
    try:
        external_dispatch(agent)
        if disabled == "global":
            config.write_text("noting:\n  enabled: false\n")
        elif disabled == "local":
            db.notebook_set_local_enabled(agent._secretary_conversation_ref, False)
        else:
            db.noting_idle_turn_finished(agent._secretary_conversation_ref, time.time(), due_at=time.time() + 1000)
        assert rt.maybe_run_idle_noting(agent, db, agent._secretary_conversation_ref).startswith("skip:")
        assert not notices(agent)
        assert_no_work(db)
    finally:
        cancel_idle_timer(db, agent._secretary_conversation_ref)
        agent.close()


def test_external_notice_busy_fence_queue_and_owner_switch(runtime):
    db, _config = runtime
    agent = prepare(db)
    try:
        external_dispatch(agent)
        agent._secretary_main_turn_running = True
        rt.maybe_admit_force_from_pressure(agent, 64000)
        rt.maybe_admit_force_from_pressure(agent, 64000)
        assert not notices(agent) and len(agent._secretary_framework_messages) == 1
        agent._secretary_main_turn_running = False
        agent._active_compression_commit_fence = SimpleNamespace()
        assert flush_framework_messages(agent) == 0
        del agent._active_compression_commit_fence
        deadline = time.monotonic() + 2
        while not notices(agent) and time.monotonic() < deadline:
            time.sleep(.01)
        assert_notice(agent)
        old_sid, old_ref = agent.session_id, agent._secretary_conversation_ref
        _switch_framework_owner(agent)
        external_dispatch(agent)
        assert agent._secretary_conversation_ref != old_ref
        rt.maybe_admit_force_from_pressure(agent, 64000)
        assert_notice(agent)
        assert len([r for r in db.get_messages(old_sid) if NOTICE in str(r["content"])]) == 1
    finally:
        agent.close()


def test_queued_external_notice_is_discarded_on_owner_change(runtime):
    db, _config = runtime
    agent = prepare(db)
    try:
        external_dispatch(agent)
        agent._secretary_main_turn_running = True
        rt.maybe_admit_force_from_pressure(agent, 64000)
        old_sid = agent.session_id
        _switch_framework_owner(agent)
        agent._secretary_main_turn_running = False
        assert flush_framework_messages(agent) == 0
        assert not agent._secretary_framework_messages
        assert not notices(agent) and not any(NOTICE in str(r["content"]) for r in db.get_messages(old_sid))
        external_dispatch(agent)
        rt.maybe_admit_force_from_pressure(agent, 64000)
        assert_notice(agent)
    finally:
        agent.close()


def test_concurrent_external_rejections_publish_at_most_once(runtime):
    db, _config = runtime
    agent = prepare(db)
    try:
        external_dispatch(agent)
        def attempt(_):
            with owning_db_scope(db):
                return rt.maybe_admit_force_from_pressure(agent, 64000)
        with ThreadPoolExecutor(max_workers=4) as pool:
            assert list(pool.map(attempt, range(8))) == ["skip:external_main_execution"] * 8
        assert_notice(agent)
        assert_no_work(db)
    finally:
        agent.close()


def test_local_middleware_reply_does_not_reset_external_suppression(runtime, monkeypatch):
    from tests.secretary.test_noting_child import mock_response

    db, _config = runtime
    agent = prepare(db)
    try:
        external_dispatch(agent)
        rt.maybe_admit_force_from_pressure(agent, 64000)
        ref = agent._secretary_conversation_ref
        seen = _requests(agent)
        monkeypatch.setattr("hermes_cli.middleware.run_llm_execution_middleware",
                            lambda *_a, **_k: mock_response("local reply"))
        result = agent.run_conversation("无实际请求", title_user_message="",
                                        conversation_history=db.get_messages_as_conversation(agent.session_id))
        assert result["completed"] and not seen
        assert rt.main_execution_for_force(agent) == "external" and ref in agent._secretary_external_notice_refs
        rt.maybe_admit_force_from_pressure(agent, 64000)
        assert len(notices(agent)) == 1
    finally:
        agent.close()


@pytest.mark.parametrize("auxiliary", ["review", "child"])
def test_auxiliary_dispatch_cannot_reset_parent_notice_suppression(runtime, auxiliary):
    db, _config = runtime
    agent = prepare(db)
    try:
        external_dispatch(agent)
        rt.maybe_admit_force_from_pressure(agent, 64000)
        refs = set(agent._secretary_external_notice_refs)
        if auxiliary == "review":
            agent._persist_disabled = True
        else:
            agent._parent_session_id = "parent"
        assert not rt.note_actual_main_execution(agent, "native")
        assert agent._secretary_external_notice_refs == refs
    finally:
        agent.close()


def test_external_rejection_owner_changes_before_publisher_cannot_cross(runtime, monkeypatch):
    db, _config = runtime
    agent = prepare(db)
    try:
        external_dispatch(agent)
        old_sid = agent.session_id
        native_decide = rt.try_admit_force
        def decide_then_switch(*args, **kwargs):
            decision = native_decide(*args, **kwargs)
            assert decision.reason == "external_main_execution"
            _switch_framework_owner(agent)
            return decision
        monkeypatch.setattr(rt, "try_admit_force", decide_then_switch)
        assert rt.maybe_admit_force_from_pressure(agent, 64000) == "skip:external_main_execution"
        assert not notices(agent) and not any(NOTICE in str(r["content"]) for r in db.get_messages(old_sid))
        assert not getattr(agent, "_secretary_external_notice_refs", None)
        assert_no_work(db)
    finally:
        agent.close()


@pytest.mark.parametrize("busy", ["turn", "fence"])
def test_actual_native_fallback_removes_only_queued_external_notice(runtime, busy):
    db, _config = runtime
    agent = prepare(db)
    try:
        external_dispatch(agent)
        if busy == "turn":
            assert rt.note_main_turn_started(agent)
        else:
            agent._active_compression_commit_fence = SimpleNamespace()
        rt.maybe_admit_force_from_pressure(agent, 64000)
        finish = "Background: synthetic producer notification retained."
        force = "The context is nearing its limit, and a Notebook update task has been dispatched. Consider compacting soon. When you do, prioritize preserving the content after this message."
        assert publish_framework_message(agent, finish, display_metadata={"noting_run_output": True})
        assert publish_framework_message(agent, force)
        assert len(agent._secretary_framework_messages) == 3 and not notices(agent)
        # Use the concrete Native provider-dispatch seam that the Main loop calls.
        called = []
        with rt.main_model_request_scope(agent, {}):
            rt.dispatch_main_model_request(lambda **kwargs: called.append(kwargs), {"messages": []})
        assert called == [{}] and rt.main_execution_for_force(agent) == "native"
        assert len(agent._secretary_framework_messages) == 2
        if busy == "fence":
            del agent._active_compression_commit_fence
        rt.note_main_turn_finished(agent)
        flush_framework_messages(agent)
        assert not notices(agent)
        rows = db.get_messages(agent.session_id)[-2:]
        assert [r["content"] for r in rows] == ["<framework-message>\n" + body + "\n</framework-message>"
                                                for body in (finish, force)]
        assert [r["message_uid"] for r in rows] == [r["message_uid"] for r in agent._session_messages[-2:]]
        assert rows[0]["display_metadata"]["noting_run_output"] is True
        assert not agent._secretary_framework_messages
        external_dispatch(agent)
        rt.maybe_admit_force_from_pressure(agent, 64000)
        assert_notice(agent)
    finally:
        agent.close()


def test_native_after_rejection_before_publish_discards_stale_notice(runtime, monkeypatch):
    db, _config = runtime
    agent = prepare(db)
    try:
        external_dispatch(agent)
        native_decide = rt.try_admit_force
        def decide_then_native(*args, **kwargs):
            decision = native_decide(*args, **kwargs)
            assert decision.reason == "external_main_execution"
            with rt.main_model_request_scope(agent, {}):
                rt.dispatch_main_model_request(lambda **kwargs: None, {})
            return decision
        monkeypatch.setattr(rt, "try_admit_force", decide_then_native)
        assert rt.maybe_admit_force_from_pressure(agent, 64000) == "skip:external_main_execution"
        assert rt.main_execution_for_force(agent) == "native" and not notices(agent)
        assert not getattr(agent, "_secretary_external_notice_refs", None)
        assert_no_work(db)
    finally:
        agent.close()


def test_notice_suppression_survives_same_runtime_owner_round_trip(runtime):
    from hermes_cli.cli_commands_mixin import _sync_agent_to_session

    db, _config = runtime
    agent = prepare(db)
    try:
        external_dispatch(agent)
        rt.maybe_admit_force_from_pressure(agent, 64000)
        original_sid, original_ref = agent.session_id, agent._secretary_conversation_ref
        _switch_framework_owner(agent, branch=True)
        branch_sid, branch_ref = agent.session_id, agent._secretary_conversation_ref
        external_dispatch(agent)
        rt.maybe_admit_force_from_pressure(agent, 64000)
        assert agent._secretary_external_notice_refs == {original_ref, branch_ref}
        cli = SimpleNamespace(agent=agent, conversation_history=db.get_messages_as_conversation(original_sid))
        _sync_agent_to_session(cli, original_sid, parent_session_id=branch_sid, reason="resumed")
        agent._session_messages = cli.conversation_history
        external_dispatch(agent)
        rt.maybe_admit_force_from_pressure(agent, 64000)
        assert len(notices(agent)) == 1
        with rt.main_model_request_scope(agent, {}):
            rt.dispatch_main_model_request(lambda **kwargs: None, {})
        assert agent._secretary_external_notice_refs == {branch_ref}
        external_dispatch(agent)
        rt.maybe_admit_force_from_pressure(agent, 64000)
        assert_notice(agent, 2)
        assert branch_ref in agent._secretary_external_notice_refs
    finally:
        agent.close()
