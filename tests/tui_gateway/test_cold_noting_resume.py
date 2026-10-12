"""Cold resume uses the production RPC, native Agent/DB/Idle/Child boundaries."""
import copy
import threading
import time
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from tests.agent.test_run_agent import _mock_response
from tests.tui_gateway.test_pending_native_turn import live as live, settled
from tui_gateway import server


def rpc(method, **params):
    return server.handle_request({"jsonrpc": "2.0", "id": method, "method": method, "params": params})


class HeldTimer:
    """Only external timer scheduling is held; registry/period/admission remain real."""
    def __init__(self, delay, target):
        self.target, self.daemon, self.name, self.cancelled = target, False, "", False
    def start(self):
        pass
    def cancel(self):
        self.cancelled = True
    def is_alive(self):
        return not self.cancelled


@pytest.fixture
def cold(live, monkeypatch):
    from secretary import noting_timers
    from secretary.noting_child import active_noting_task_count
    (live.home / "config.yaml").write_text("noting:\n  enabled: true\n  idle_delay_seconds: 0\n"
                                          "compression:\n  enabled: false\nmodel:\n  default: test/model\n"
                                          "  base_url: http://invalid.local/v1\n  context_length: 256000\n")
    with (live.home / "config.yaml").open("a") as config:
        config.write(f"terminal:\n  cwd: {live.home}\n")
    monkeypatch.setattr(noting_timers, "threading", SimpleNamespace(Timer=HeldTimer, RLock=threading.RLock))
    live.agent._cached_system_prompt = None
    monkeypatch.setattr(live.agent, "_interruptible_api_call", lambda kwargs: _mock_response(content="normal end", finish_reason="stop"))
    assert rpc("prompt.submit", session_id="runtime", text="cold restored working context")["result"]["status"] == "streaming"
    deadline = time.monotonic() + 10
    while live.session["running"] and time.monotonic() < deadline:
        time.sleep(.01)
    assert not live.session["running"], live.frames
    settled(live)
    ref = live.agent._secretary_conversation_ref
    period = live.db.noting_idle_state(ref)
    assert period and period["last_turn_finished_at"] and period["trigger_produced_at"] is None, live.frames
    assert live.db.get_session("stored")["system_prompt"]
    noting_timers.cancel_idle_timer(live.db, ref)
    warm = copy.deepcopy(live.agent._session_messages)
    warm_tools, warm_root = copy.deepcopy(live.agent.tools), live.agent._cached_system_prompt
    assert "result" in rpc("session.close", session_id="runtime")
    assert not server._sessions
    assert live.db.noting_idle_state(ref) == period
    built, polls, poll_workers, closes = [], [], [], {}
    client = MagicMock()
    from tests.secretary.test_noting_child import _tool_response, mock_response
    client.chat.completions.create.side_effect = [
        _tool_response("finish_noting", {"reason": "Restored context is current."}, "finish"), mock_response("done")]
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **kwargs: client)
    monkeypatch.setattr("model_tools.get_tool_definitions", lambda **kwargs: copy.deepcopy(warm_tools))
    monkeypatch.setattr("model_tools.check_toolset_requirements", lambda *a, **k: {})
    monkeypatch.setattr(server, "_get_db", lambda: live.db)
    monkeypatch.setattr(server, "_resolve_agent_model_runtime", lambda *a, **k: ("test/model", {
        "provider": "", "base_url": "http://invalid.local/v1", "api_key": "test-key", "api_mode": "chat_completions"}))
    original = server._make_agent
    def construct(*a, **k):
        agent = original(*a, **k)
        agent.compression_enabled = False
        agent._disable_streaming = True
        agent._use_prompt_caching = False
        agent.save_trajectories = False
        built.append(agent)
        closes[id(agent)] = 0
        close = agent.close
        def counted_close():
            closes[id(agent)] += 1
            close()
        agent.close = counted_close
        return agent
    monkeypatch.setattr(server, "_make_agent", construct)
    monkeypatch.setattr(server, "_wire_session_agent", lambda *a, **k: False)
    monkeypatch.setattr(server, "_schedule_mcp_late_refresh", lambda *a, **k: None)
    monkeypatch.setattr(server, "_notify_session_boundary", lambda *a, **k: None)
    monkeypatch.setattr(server, "_schedule_session_cap_enforcement", lambda: None)
    def poll(sid, session):
        from agent.memory_provider import spawn_context_thread
        polls.append((sid, session.get("profile_home"), bool(session["agent"]._session_messages)))
        worker = spawn_context_thread(lambda: server._maybe_fire_tui_noting_idle(sid, session), name="cold-idle-poll")
        poll_workers.append(worker)
        worker.start()
        return threading.Event()
    monkeypatch.setattr(server, "_start_notification_poller", poll)
    yield SimpleNamespace(live=live, ref=ref, built=built, polls=polls, client=client, warm=warm,
                          root=warm_root, tools=warm_tools, closes=closes, poll_workers=poll_workers)
    for worker in poll_workers:
        worker.join(10)
        assert not worker.is_alive()
    deadline = time.monotonic() + 10
    while active_noting_task_count() and time.monotonic() < deadline:
        time.sleep(.01)
    assert active_noting_task_count() == 0
    for agent in built:
        if not closes[id(agent)]:
            agent.close()
    noting_timers.cancel_idle_timer(live.db, ref)


@pytest.mark.parametrize("flags", [{"eager_build": True}, {}, {"defer_history": True},
                                   {"eager_build": True, "omit_messages": True}])
def test_cold_resume_needs_actual_parent_context_before_idle_catchup(cold, flags):
    result = rpc("session.resume", session_id="stored", source="tui", **flags)
    assert "result" in result, result
    assert result["result"].get("running") is False
    deadline = time.monotonic() + 5
    while cold.live.db.notebook_current(cold.ref) is None and time.monotonic() < deadline:
        time.sleep(.01)
    snapshot = cold.live.db.notebook_current(cold.ref)
    assert snapshot is not None, {"period": cold.live.db.noting_idle_state(cold.ref), "polls": cold.polls,
                                  "active": cold.built[0]._session_messages}
    assert snapshot["anchor_message_uid"] == cold.warm[-1]["message_uid"]
    parent = cold.built[0]
    assert parent._cached_system_prompt == cold.root and parent.tools == cold.tools
    assert cold.polls[0][2] is True and cold.client.chat.completions.create.call_count == 2
    requests = cold.client.chat.completions.create.call_args_list
    for call in requests:
        assert call.kwargs["messages"][0]["content"] == cold.root
        assert call.kwargs["tools"] == cold.tools
    wait_child_finished()
    before = copy.deepcopy(cold.live.db.get_messages("stored"))
    parent.close()
    assert cold.live.db.get_messages("stored") == before  # close never duplicates restored rows
    assert cold.closes[id(parent)] == 1


def spawn_resume(**params):
    results = []
    thread = threading.Thread(target=lambda: results.append(rpc("session.resume", session_id="stored", source="tui", **params)),
                              name="first-resume")
    thread.start()
    return thread, results


def join_resume(thread, results):
    thread.join(10)
    assert not thread.is_alive() and len(results) == 1
    return results[0]


def test_eager_constructor_loser_never_restores_root_or_starts_services(cold, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    original = server._make_agent
    def paused(*a, **k):
        agent = original(*a, **k)
        if threading.current_thread().name == "first-resume":
            entered.set()
            assert release.wait(5)
        return agent
    monkeypatch.setattr(server, "_make_agent", paused)
    from agent import conversation_loop
    restores = []
    original_restore = conversation_loop._restore_or_build_system_prompt
    def restore(agent, *a):
        restores.append(agent)
        return original_restore(agent, *a)
    monkeypatch.setattr(conversation_loop, "_restore_or_build_system_prompt", restore)
    thread, results = spawn_resume(eager_build=True)
    assert entered.wait(5)
    winner = rpc("session.resume", session_id="stored", eager_build=True, source="tui")
    release.set()
    loser = join_resume(thread, results)
    assert winner["result"]["session_id"] == loser["result"]["session_id"]
    assert len(restores) == 1 and len(cold.polls) == 1 and len(cold.built) == 2
    assert cold.closes[id(cold.built[0])] == 1


def test_rewrite_during_native_root_io_installs_latest_history_without_second_restore(cold, monkeypatch):
    from agent import conversation_loop
    entered, release = threading.Event(), threading.Event()
    calls = []
    original = conversation_loop._restore_or_build_system_prompt
    def paused(agent, *a):
        calls.append(agent)
        entered.set()
        assert release.wait(5)
        return original(agent, *a)
    monkeypatch.setattr(conversation_loop, "_restore_or_build_system_prompt", paused)
    thread, results = spawn_resume(eager_build=True)
    assert entered.wait(5)
    record = next(iter(server._sessions.values()))
    with record["history_lock"]:
        assert server._sessions_lock.acquire(timeout=1)
        server._sessions_lock.release()
        # This is the actual native rewrite owner and DB commit, not a replacement list.
        server._rewind_active_session_history(record, 0)
    release.set()
    assert "result" in join_resume(thread, results)
    assert record["agent"]._session_messages is record["history"] and record["history"] == []
    assert len(calls) == 1 and cold.live.db.notebook_current(cold.ref) is None


def test_close_during_root_io_discards_unpublished_agent_once(cold, monkeypatch):
    from agent import conversation_loop
    entered, release = threading.Event(), threading.Event()
    original = conversation_loop._restore_or_build_system_prompt
    def paused(*a):
        entered.set()
        assert release.wait(5)
        return original(*a)
    monkeypatch.setattr(conversation_loop, "_restore_or_build_system_prompt", paused)
    thread, results = spawn_resume(eager_build=True)
    assert entered.wait(5)
    sid = next(iter(server._sessions))
    assert "result" in rpc("session.close", session_id=sid)
    release.set()
    assert "error" in join_resume(thread, results)
    assert sid not in server._sessions and not cold.polls
    assert cold.closes[id(cold.built[0])] == 1
    assert cold.live.db.noting_idle_state(cold.ref)["trigger_produced_at"] is None


def test_true_root_prepare_raise_is_build_failure_not_idle_success(cold, monkeypatch):
    from agent import conversation_loop
    monkeypatch.setattr(conversation_loop, "_restore_or_build_system_prompt",
                        lambda *a: (_ for _ in ()).throw(RuntimeError("controlled root failure")))
    result = rpc("session.resume", session_id="stored", eager_build=True, source="tui")
    assert result["error"]["code"] == 5000 and "controlled root failure" in result["error"]["message"]
    assert not cold.polls and cold.closes[id(cold.built[0])] == 1
    assert cold.live.db.noting_idle_state(cold.ref)["trigger_produced_at"] is None
    assert cold.live.db.notebook_current(cold.ref) is None


def test_global_off_eager_is_native_without_root_preparation(cold, monkeypatch):
    from agent import conversation_loop
    config = cold.live.home / "config.yaml"
    config.write_text(config.read_text().replace("enabled: true", "enabled: false", 1))
    monkeypatch.setattr(conversation_loop, "_restore_or_build_system_prompt", lambda *a: pytest.fail("off must not restore"))
    result = rpc("session.resume", session_id="stored", eager_build=True, source="tui")
    assert "result" in result and cold.built[0]._cached_system_prompt is None
    assert cold.built[0]._session_messages == [] and cold.polls[0][2] is False
    assert cold.live.db.notebook_current(cold.ref) is None


def test_noneligible_eager_retains_native_context_even_with_global_on(cold, monkeypatch):
    from agent import conversation_loop
    cold.live.db.create_session("aux", source="subagent", parent_session_id="stored")
    cold.live.db.append_message("aux", "user", "auxiliary task")
    cold.live.db.append_message("aux", "assistant", "auxiliary response")
    monkeypatch.setattr(conversation_loop, "_restore_or_build_system_prompt", lambda *a: pytest.fail("aux must not restore"))
    assert "result" in rpc("session.resume", session_id="aux", eager_build=True, source="tui")
    assert cold.built[0]._session_messages == [] and cold.built[0]._cached_system_prompt is None
    assert cold.polls[0][2] is False


def wait_snapshot(cold):
    deadline = time.monotonic() + 5
    while cold.live.db.notebook_current(cold.ref) is None and time.monotonic() < deadline:
        time.sleep(.01)
    assert cold.live.db.notebook_current(cold.ref) is not None


def wait_child_finished():
    from secretary.noting_child import active_noting_task_count
    deadline = time.monotonic() + 5
    while active_noting_task_count() and time.monotonic() < deadline:
        time.sleep(.01)
    assert not active_noting_task_count()


@pytest.mark.parametrize("other_builder", [False, True])
def test_named_profile_prepared_handle_handoff_and_competing_builder(cold, monkeypatch, other_builder):
    import hermes_state_registry as registry
    from hermes_state_registry import live_shared_session_dbs
    baseline = [db for db in live_shared_session_dbs() if db.db_path == cold.live.db.db_path]
    refs = []
    acquire, release = registry.acquire, registry.release
    def acquired(*a, **k):
        db = acquire(*a, **k)
        import traceback
        refs.append(("acquire", id(db), traceback.format_stack(limit=4)[-2]))
        return db
    def released(db):
        import traceback
        refs.append(("release", id(db), traceback.format_stack(limit=4)[-2]))
        return release(db)
    monkeypatch.setattr(registry, "acquire", acquired)
    monkeypatch.setattr(registry, "release", released)
    monkeypatch.setattr(server, "_profile_home", lambda name: cold.live.home)
    original = server._start_agent_build
    adopted = []
    def start(sid, record, *, prepared_agent=None):
        if prepared_agent is not None and other_builder:
            # Another real native attachment request wins the existing build lock first.
            assert "result" in rpc("image.detach", session_id=sid, path="absent.png")
        result = original(sid, record, prepared_agent=prepared_agent)
        if prepared_agent is not None:
            adopted.append(result)
        return result
    monkeypatch.setattr(server, "_start_agent_build", start)
    result = rpc("session.resume", session_id="stored", eager_build=True, source="tui", profile="other")
    assert "result" in result, result
    wait_snapshot(cold)
    wait_child_finished()
    record = server._sessions[result["result"]["session_id"]]
    assert record["profile_home"] == str(cold.live.home) and cold.polls[0][1] == str(cold.live.home)
    assert adopted == [not other_builder]
    agent = record["agent"]
    assert agent._owns_session_db and agent._session_db.db_path == cold.live.db.db_path
    if other_builder:
        assert cold.closes[id(cold.built[0])] == 1 and agent is cold.built[1]
    before = copy.deepcopy(cold.live.db.get_messages("stored"))
    agent.close()
    assert cold.live.db.get_messages("stored") == before
    def returned_refs():
        return sum(item[0] == "acquire" for item in refs) == sum(item[0] == "release" for item in refs)
    deadline = time.monotonic() + 5
    while not returned_refs() and time.monotonic() < deadline:
        time.sleep(.01)
    assert returned_refs(), "\n".join(map(str, refs))
    assert [db for db in live_shared_session_dbs() if db.db_path == agent._session_db.db_path] == baseline
    assert cold.closes[id(agent)] == 1


def test_native_root_db_read_error_still_uses_native_fallback(cold, monkeypatch):
    from agent import conversation_loop
    original = conversation_loop._restore_or_build_system_prompt
    def read_fault(agent, *args):
        original_get = agent._session_db.get_session
        first = True
        def get(*a, **k):
            nonlocal first
            if first:
                first = False
                raise RuntimeError("controlled transient root-store read error")
            return original_get(*a, **k)
        with monkeypatch.context() as scope:
            scope.setattr(agent._session_db, "get_session", get)
            return original(agent, *args)
    monkeypatch.setattr(conversation_loop, "_restore_or_build_system_prompt", read_fault)
    assert "result" in rpc("session.resume", session_id="stored", eager_build=True, source="tui")
    wait_snapshot(cold)
    assert isinstance(cold.built[0]._cached_system_prompt, str)


def test_local_off_deadline_is_consumed_once_and_not_revived_by_on_or_cold(cold):
    cold.live.db.notebook_set_local_enabled(cold.ref, False)
    result = rpc("session.resume", session_id="stored", eager_build=True, source="tui")
    assert "result" in result and cold.polls[0][2]
    cold.poll_workers[-1].join(5)
    assert not cold.poll_workers[-1].is_alive()
    assert cold.live.db.noting_idle_state(cold.ref) is None
    assert cold.live.db.notebook_current(cold.ref) is None and cold.client.chat.completions.create.call_count == 0
    cold.live.db.notebook_set_local_enabled(cold.ref, True)
    sid = result["result"]["session_id"]
    server._maybe_fire_tui_noting_idle(sid, server._sessions[sid])
    assert "result" in rpc("session.close", session_id=sid)
    assert "result" in rpc("session.resume", session_id="stored", eager_build=True, source="tui")
    assert cold.live.db.noting_idle_state(cold.ref) is None
    assert cold.live.db.notebook_current(cold.ref) is None and cold.client.chat.completions.create.call_count == 0


@pytest.mark.parametrize("window", ["root_io", "attached_before_ready"])
def test_main_claim_during_cold_build_cannot_consume_old_deadline(cold, monkeypatch, window):
    from agent import conversation_loop
    entered, release = threading.Event(), threading.Event()
    original = conversation_loop._restore_or_build_system_prompt
    def paused(*a):
        entered.set()
        assert release.wait(5)
        return original(*a)
    if window == "root_io":
        monkeypatch.setattr(conversation_loop, "_restore_or_build_system_prompt", paused)
    else:
        announce = server._announce_built_agent
        def pause_announce(*a):
            entered.set()
            assert release.wait(5)
            return announce(*a)
        monkeypatch.setattr(server, "_announce_built_agent", pause_announce)
    thread, results = spawn_resume(eager_build=True)
    assert entered.wait(5)
    sid, record = next(iter(server._sessions.items()))
    # Accepted through the real submit/history owner while the real build is still pending.
    assert "result" in rpc("prompt.submit", session_id=sid, text="real next Main")
    parent = cold.built[0]
    monkeypatch.setattr(parent, "_interruptible_api_call", lambda kwargs: _mock_response(content="next complete", finish_reason="stop"))
    release.set()
    assert "result" in join_resume(thread, results)
    deadline = time.monotonic() + 10
    while record["running"] and time.monotonic() < deadline:
        time.sleep(.01)
    assert not record["running"]
    # The earlier idle period must be cancelled by actual Main, never freeze an accepted-but-unrun row.
    with cold.live.db._read_ctx() as conn:
        count = conn.execute("SELECT COUNT(*) FROM secretary_noting_admissions WHERE conversation_ref=?", (cold.ref,)).fetchone()[0]
    assert count == 0
    assert cold.live.db.noting_idle_state(cold.ref)["trigger_produced_at"] is None
    anchor = record["history"][-1]["message_uid"]
    from secretary import noting_timers
    timer = noting_timers._timers[noting_timers._runtime_key(cold.live.db, cold.ref)][0]
    timer.target()  # Deliver the held scheduler's actual new-period callback.
    wait_snapshot(cold)
    assert cold.live.db.notebook_current(cold.ref)["anchor_message_uid"] == anchor


def test_cold_host_history_lock_allows_native_compaction_receipt(cold, monkeypatch):
    from agent.context_compressor import COMPRESSED_SUMMARY_METADATA_KEY, SUMMARY_PREFIX
    from tests.hermes_state._secretary_noting_harness import empty_state
    # A legal prior Force Snapshot is fixture input, not a new Main/timer event.
    for index in range(2):
        cold.live.db.append_message("stored", "user", f"historical {index}: " + "context " * 150)
        cold.live.db.append_message("stored", "assistant", f"historical answer {index}: " + "answer " * 150)
    anchor = cold.live.db.get_messages("stored")[-1]["message_uid"]
    cold.live.db.notebook_commit_snapshot(cold.ref, empty_state(), anchor_message_uid=anchor, trigger_type="force")
    config = cold.live.home / "config.yaml"
    config.write_text(config.read_text().replace("idle_delay_seconds: 0", "idle_delay_seconds: 0\n  auto_compact_after_force_noting_idle: true")
                      .replace("compression:\n  enabled: false", "compression:\n  enabled: true"))
    poll = server._start_notification_poller
    summaries = []
    def measured_poll(sid, record):
        parent = record["agent"]
        parent._compression_feasibility_checked = True
        compressor = parent.context_compressor
        compressor.context_length, compressor.threshold_tokens = 130000, 75000
        compressor.last_real_prompt_tokens = 70000
        def summary(messages, **kwargs):
            summaries.append(threading.current_thread().name)
            return [{"role": "user", "content": SUMMARY_PREFIX + "\nNative cold handoff.",
                     COMPRESSED_SUMMARY_METADATA_KEY: True}, copy.deepcopy(messages[-1])]
        monkeypatch.setattr(compressor, "compress", summary)
        return poll(sid, record)
    monkeypatch.setattr(server, "_start_notification_poller", measured_poll)
    result = rpc("session.resume", session_id="stored", eager_build=True, source="tui")
    assert "result" in result, result
    cold.poll_workers[-1].join(5)
    assert not cold.poll_workers[-1].is_alive()
    parent = cold.built[0]
    worker = parent._native_compaction_worker
    worker.join(5)
    assert not worker.is_alive() and len(summaries) == 1
    request = parent._native_compaction_request
    assert request.was_admitted and request.committed and not request.error
    publication = parent._session_db.get_native_request_publication(parent.session_id)
    assert publication["marker"]["origin_request"] == request.publication_id
    assert any(row.get("message_uid") == publication["message_uid"] for row in parent._session_messages)
    assert cold.client.chat.completions.create.call_count == 0
