"""只在隔离 Profile 复现后台 Heartbeat → orphan reap → Idle 的生命周期。"""
import json
import threading
import time
from pathlib import Path
import gc
import weakref
from types import SimpleNamespace

import pytest

from tests.tui_gateway.test_cold_scheduler_host import settle
from tests.secretary.test_noting_child import mock_response, _tool_response
from tui_gateway import server, scheduler_host
from secretary import noting_runtime as rt, noting_timers as timers, noting_child

pytest_plugins = ["tests.tui_gateway.test_cold_scheduler_host"]

EVIDENCE = Path(__file__).resolve().parents[2] / ".hermes-dev/incremental-sync-20261027/idle-owner"


@pytest.mark.parametrize("compact", [False, True], ids=["no-compact", "native-compact"])
@pytest.mark.parametrize("reap", [False, True], ids=["keep-owner", "native-orphan-reap"])
def test_background_heartbeat_then_idle(cold, monkeypatch, reap, compact):
    from hermes_cli.heartbeat import HeartbeatState, save_heartbeat

    home, db = cold.homes[1], cold.dbs[1]
    (home / "config.yaml").write_text(
        "scheduler:\n  enabled: true\nnoting:\n  enabled: true\n"
        "  idle:\n    enabled: true\n    delay_seconds: 0.8\n    threshold_tokens: 1000\n"
        "compression:\n  enabled: false\nmodel:\n  default: test/b\n"
        "  base_url: http://invalid.local/v1\n  context_length: 262144\n"
        f"terminal:\n  cwd: {home}\n", encoding="utf-8")
    save_heartbeat("stored", HeartbeatState(prompt="Review synthetic pending work", interval_seconds=3600,
                   status="active", created_at=time.time() - 4000), db=db)
    child_calls, main_calls, freezes, outcomes = [], [], [], []
    idle_done = threading.Event()
    original_make, original_freeze, original_event = server._make_agent, noting_child.freeze_parent_active_prefix, rt._run_idle_event
    original_child_builder = noting_child.build_noting_child

    def main_respond(agent, request):
        main_calls.append(agent)
        rt.note_actual_main_execution(agent, "native")
        response = mock_response("Synthetic heartbeat complete. " + "Synthetic reviewed result. " * 300)
        response.usage = SimpleNamespace(prompt_tokens=50000, completion_tokens=10, total_tokens=50010)
        return response

    def make(*args, **kwargs):
        agent = original_make(*args, **kwargs)
        agent._interruptible_api_call = lambda request: main_respond(agent, request)
        return agent

    def child_respond(agent, request):
        child_calls.append(agent)
        assert getattr(agent, "_secretary_noting_child", False)
        return _tool_response("finish_noting", {"reason": "Synthetic Notebook needs no changes."}, "synthetic-finish")

    def build_child(*args, **kwargs):
        child = original_child_builder(*args, **kwargs)
        child._disable_streaming = True
        child._interruptible_api_call = lambda request: child_respond(child, request)
        return child

    def observe_freeze(parent, anchor, messages=None, **kwargs):
        source = messages if messages is not None else getattr(parent, "_session_messages", None)
        freezes.append({"owner_id": id(parent), "source_len": len(source) if source is not None else None,
                        "in_live_registry": any(s.get("agent") is parent for s in server._sessions.values())})
        return original_freeze(parent, anchor, messages, **kwargs)

    def observe_event(*args, **kwargs):
        try:
            result = original_event(*args, **kwargs)
            outcomes.append(result)
            return result
        finally:
            idle_done.set()

    monkeypatch.setattr(server, "_make_agent", make)
    monkeypatch.setattr(noting_child, "build_noting_child", build_child)
    monkeypatch.setattr(noting_child, "freeze_parent_active_prefix", observe_freeze)
    monkeypatch.setattr(rt, "_run_idle_event", observe_event)
    scheduler_host.scan_profile(home)
    assert len(server._sessions) == 1
    sid, session = next(iter(server._sessions.items()))
    settle(session)
    parent = session["agent"]
    ref = parent._secretary_conversation_ref
    before_len = len(parent._session_messages)
    assert len(main_calls) == 1 and before_len > 0
    assert session["transport"] is server._detached_ws_transport
    assert sid in server._pending_ws_reaps and timers.holds_pending_timer(parent)
    period = dict(db.noting_idle_state(ref))
    summaries = []
    if compact:
        from agent.context_compaction_request import trust_default_system_message
        trust_default_system_message(parent)
        parent.compression_enabled = True
        parent.compression_in_place = True
        parent._compression_feasibility_checked = True
        def summarize(prompt, started):
            assert db.notebook_current(ref) is not None
            assert timers.holds_maintenance(parent)
            assert not any((m.get("display_metadata") or {}).get("noting_run_output")
                           for m in parent._session_messages)
            orphan = server._pending_ws_reaps[sid]
            orphan.cancel()
            orphan.function()
            assert sid in server._sessions
            summaries.append(prompt)
            return "## Summary\nSynthetic pending work has been reviewed."
        monkeypatch.setattr(parent.context_compressor, "_call_summary_llm", summarize)
    if reap:
        native_timer = server._pending_ws_reaps[sid]
        native_timer.cancel()
        native_timer.function()
        assert sid in server._sessions and not session.get("_finalized")
        assert parent._session_messages
        assert timers.holds_pending_timer(parent)
    try:
        assert idle_done.wait(8)
        deadline = time.monotonic() + 8
        rows = []
        while time.monotonic() < deadline:
            rows = [dict(r) for r in db._read_all("SELECT * FROM secretary_noting_children")]
            if rows and rows[-1]["status"] in {"failed", "completed"}:
                break
            time.sleep(.01)
        record = {"reaped": reap, "parent_id": id(parent), "pre_reap_message_count": before_len,
                  "freezes": freezes, "event_outcomes": outcomes, "children": rows,
                  "main_fake_requests": len(main_calls), "noting_fake_requests": len(child_calls),
                  "real_network_requests": 0, "original_period": period,
                  "final_period": db.noting_idle_state(ref),
                  "post_failure_attach": rt.maybe_run_idle_noting(parent, db, ref),
                  "effective_snapshot": db.notebook_current(ref)}
        EVIDENCE.mkdir(parents=True, exist_ok=True)
        (EVIDENCE / f"result-{reap}-{compact}.json").write_text(json.dumps(record, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        assert freezes[0]["owner_id"] == id(parent) and freezes[0]["source_len"] > 0
        assert outcomes == ["admitted"]
        assert rows[-1]["status"] == "completed" and rows[-1]["child_session_id"]
        assert len(child_calls) == 1 and record["effective_snapshot"] is not None
        assert bool(summaries) is compact
        deadline = time.monotonic() + 8
        while timers.holds_maintenance(parent) and time.monotonic() < deadline:
            time.sleep(.01)
        assert not timers.holds_maintenance(parent)
        if compact:
            assert parent._native_compaction_request.durable_commit_succeeded
            from agent.context_compressor import is_compaction_summary_message
            assert is_compaction_summary_message(parent._session_messages[0])
            assert (parent._session_messages[-1].get("display_metadata") or {}).get("noting_run_output")
        orphan = server._pending_ws_reaps[sid]
        orphan.cancel()
        orphan.function()
        assert sid not in server._sessions and session["_finalized"]

    finally:
        timers.cancel_idle_timer(db, ref)


@pytest.fixture
def hosted(cold):
    home, db = cold.homes[1], cold.dbs[1]
    (home / "config.yaml").write_text(
        "noting:\n  enabled: true\n  idle:\n    enabled: true\n    delay_seconds: 3600\n"
        "    threshold_tokens: 1000\ncompression:\n  enabled: false\nmodel:\n  default: test/b\n"
        "  base_url: http://invalid.local/v1\n  context_length: 262144\n"
        f"terminal:\n  cwd: {home}\n", encoding="utf-8")
    sid, session = scheduler_host.resume_session("stored", home, "tui")
    assert session["agent_ready"].wait(5)
    parent = session["agent"]
    parent.context_compressor.update_from_response({"prompt_tokens": 50000})
    assert rt.note_main_turn_finished(parent)
    yield sid, session, parent, db, parent._secretary_conversation_ref
    timers.cancel_parent_idle_timer(parent)


def reap_now(sid):
    orphan = server._pending_ws_reaps[sid]
    orphan.cancel()
    orphan.function()


def test_orphan_ttl_and_cap_share_exact_owner_wait_exemption(hosted, monkeypatch):
    sid, session, parent, db, ref = hosted
    session["last_active"] = session["created_at"] = time.time() - 10000
    monkeypatch.setattr(server, "_SESSION_TTL_S", 1)
    monkeypatch.setattr(server, "_max_live_sessions", lambda: 1)
    server._sessions["unrelated"] = {"transport": object(), "running": True}
    try:
        for _ in range(3):
            reap_now(sid)
            assert timers.holds_maintenance(parent) and sid in server._sessions
        server._reap_idle_sessions()
        assert sid in server._sessions
        assert not server._session_is_lru_evictable(sid, session)
        # The real claim revalidates the same period: another Main period removes protection.
        db.noting_idle_turn_started(ref, time.time())
        server._enforce_session_cap()
        assert sid not in server._sessions and session["_finalized"]
    finally:
        server._sessions.pop("unrelated", None)


@pytest.mark.parametrize("boundary", ["close", "epoch", "archive", "global", "local", "idle"])
def test_invalid_boundary_releases_wait_without_consuming_period(hosted, boundary):
    from agent.context_compaction_request import cancel_native_request
    sid, session, parent, db, ref = hosted
    before = dict(db.noting_idle_state(ref))
    old_timer = timers._timers[timers._runtime_key(db, ref)].timer
    old_timer.cancel()
    config_path = Path(db.db_path).parent / "config.yaml"
    actions = {
        "close": parent.close,
        "epoch": lambda: cancel_native_request(parent, boundary=True),
        "archive": lambda: db._execute_write(lambda conn: conn.execute(
            "UPDATE sessions SET archived=1 WHERE id=?", (parent.session_id,))),
        "local": lambda: db.notebook_set_local_enabled(ref, False),
        "global": lambda: config_path.write_text("noting:\n  enabled: false\n"),
        "idle": lambda: config_path.write_text("noting:\n  enabled: true\n  idle:\n    enabled: false\n"),
    }
    actions[boundary]()
    timers.refresh_maintenance(parent)
    assert not timers.holds_maintenance(parent)
    # Close/replacement callbacks must be unable to bind or consume the old period.
    if boundary in {"close", "epoch"}:
        old_timer.function()
        assert db.noting_idle_state(ref) == before
        assert not db._read_all("SELECT * FROM secretary_noting_admissions")
    reap_now(sid)
    assert sid not in server._sessions
    assert db.noting_idle_state(ref) == before


def test_old_callback_and_close_cannot_cancel_new_owner_timer(hosted, cold):
    from tests.secretary.test_noting_child import make_agent
    from secretary.noting_scope import bind_main_runtime
    sid, session, old, db, ref = hosted
    original = timers._timers[timers._runtime_key(db, ref)]
    replacement = make_agent(old.session_id, old._session_db)
    replacement._secretary_conversation_ref = ref
    replacement._session_messages = list(old._session_messages)
    assert bind_main_runtime(replacement)
    try:
        assert rt.maybe_run_idle_noting(replacement, db, ref) == "skip:timer_armed"
        current = timers._timers[timers._runtime_key(db, ref)]
        assert current is not original and current.parent_ref() is replacement
        original.timer.cancel()
        original.timer.function()
        assert rt.maybe_run_idle_noting(old, db, ref) == "skip:not_main_owner"
        assert timers._timers[timers._runtime_key(db, ref)] is current
        old.close()
        assert not bind_main_runtime(old)
        assert timers._timers[timers._runtime_key(db, ref)] is current
        assert timers.holds_maintenance(replacement) and not timers.holds_maintenance(old)
        # Same ref in another DB cannot be cancelled by this Profile.
        timers.cancel_idle_timer(cold.dbs[0], ref)
        assert timers._timers[timers._runtime_key(db, ref)] is current
    finally:
        replacement.close()


def test_missing_prefix_keeps_period_for_real_attach(hosted, monkeypatch):
    sid, session, parent, db, ref = hosted
    timers.cancel_parent_idle_timer(parent)
    now = time.time()
    db.noting_idle_turn_finished(ref, now - 10, due_at=now - 1)
    before = dict(db.noting_idle_state(ref))
    prefix, parent._session_messages = parent._session_messages, []
    assert rt.maybe_run_idle_noting(parent, db, ref) == "skip:parent_context_unavailable"
    assert db.noting_idle_state(ref) == before
    assert not db._read_all("SELECT * FROM secretary_noting_admissions")
    parent._session_messages = prefix
    children = []
    original = noting_child.build_noting_child
    def build(*args, **kwargs):
        child = original(*args, **kwargs)
        child._disable_streaming = True
        child._interruptible_api_call = lambda request: _tool_response(
            "finish_noting", {"reason": "Synthetic existing work reviewed."}, "finish")
        children.append(child)
        return child
    monkeypatch.setattr(noting_child, "build_noting_child", build)
    assert rt.maybe_run_idle_noting(parent, db, ref) == "admitted"
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline and timers.holds_maintenance(parent):
        time.sleep(.01)
    assert children and db.notebook_current(ref) is not None
    assert db.noting_idle_state(ref)["trigger_produced_at"] is not None


def test_weak_owner_disappearance_leaves_durable_deadline(hosted):
    from tests.secretary.test_noting_runtime import _agent
    sid, session, parent, db, ref = hosted
    # Use a native-lifecycle weak runtime with no host strong owner; no child/freeze is stubbed.
    temporary = _agent(db, parent.session_id)
    state = dict(db.noting_idle_state(ref))
    timers.arm_idle_timer(temporary, db, ref, state["due_at"])
    entry = timers._timers[timers._runtime_key(db, ref)]
    entry.timer.cancel()
    db._test_runtime_agents.remove(temporary)
    weak = weakref.ref(temporary)
    del temporary
    gc.collect()
    assert weak() is None
    entry.timer.function()
    assert db.noting_idle_state(ref) == state
    assert not timers.holds_maintenance(parent)


def test_long_main_survives_repeated_orphan_checks_then_arms_from_real_end(hosted, monkeypatch):
    sid, session, parent, db, ref = hosted
    entered, release = threading.Event(), threading.Event()
    def respond(request):
        entered.set()
        assert release.wait(8)
        response = mock_response("Synthetic Main work completed.")
        response.usage = SimpleNamespace(prompt_tokens=50000, completion_tokens=10, total_tokens=50010)
        return response
    monkeypatch.setattr(parent, "_interruptible_api_call", respond)
    response = server.handle_request({"jsonrpc": "2.0", "id": "long-main", "method": "prompt.submit",
                                      "params": {"session_id": sid, "text": "Review synthetic work"}})
    assert response["result"]["status"] == "streaming" and entered.wait(8)
    try:
        for _ in range(3):
            reap_now(sid)
            assert sid in server._sessions and session["running"]
            assert not session.get("_client_gone_interrupt_requested")
            assert not timers.holds_pending_timer(parent)
            assert db.noting_idle_state(ref)["due_at"] is None
    finally:
        before_end = time.time()
        release.set()
        settle(session)
    state = db.noting_idle_state(ref)
    assert state["last_turn_finished_at"] >= before_end
    assert state["due_at"] == state["last_turn_finished_at"] + 3600
    assert timers.holds_maintenance(parent)


@pytest.mark.parametrize("close_first", [False, True], ids=["freeze-wins", "close-wins"])
def test_close_and_real_freeze_have_one_order_without_reaper_deadlock(hosted, monkeypatch, close_first):
    sid, session, parent, db, ref = hosted
    timers.cancel_parent_idle_timer(parent)
    db.noting_idle_turn_finished(ref, time.time() - 10, due_at=time.time() - 1)
    original_period = dict(db.noting_idle_state(ref))
    timers.arm_idle_timer(parent, db, ref, time.time() + 3600)
    timer = timers._timers[timers._runtime_key(db, ref)].timer
    timer.cancel()
    if close_first:
        parent.close()
        timer.function()
        assert db.noting_idle_state(ref) == original_period
        assert not db._read_all("SELECT * FROM secretary_noting_admissions")
        return
    entered, release, close_started, closed = (threading.Event() for _ in range(4))
    sizes, errors = [], []
    original_freeze = noting_child.freeze_parent_active_prefix
    original_child = noting_child.build_noting_child
    def freeze(owner, anchor, messages=None, **kwargs):
        sizes.append(len(messages if messages is not None else owner._session_messages))
        if len(sizes) == 1:
            entered.set()
            assert release.wait(8)
        return original_freeze(owner, anchor, messages, **kwargs)
    def build(*args, **kwargs):
        child = original_child(*args, **kwargs)
        child._disable_streaming = True
        child._interruptible_api_call = lambda request: _tool_response(
            "finish_noting", {"reason": "Synthetic work reviewed."}, "finish")
        return child
    def fire():
        try:
            timer.function()
        except BaseException as exc:
            errors.append(exc)
    def close():
        close_started.set()
        parent.close()
        closed.set()
    monkeypatch.setattr(noting_child, "freeze_parent_active_prefix", freeze)
    monkeypatch.setattr(noting_child, "build_noting_child", build)
    firing, closing = threading.Thread(target=fire), threading.Thread(target=close)
    firing.start()
    try:
        assert entered.wait(8)
        closing.start()
        assert close_started.wait(8) and not closed.is_set()
        # This native reap only reads cached registration facts inside its lock.
        # It must neither wait for the held persistence lock nor pop the owner.
        reap_now(sid)
        assert sid in server._sessions and timers.holds_maintenance(parent)
    finally:
        release.set()
        firing.join(8)
        if closing.ident is not None:
            closing.join(8)
    assert not firing.is_alive() and not closing.is_alive() and not errors
    assert sizes and all(size > 0 for size in sizes)
    assert db.noting_idle_state(ref)["trigger_produced_at"] is not None
    deadline = time.monotonic() + 8
    while time.monotonic() < deadline:
        rows = db._read_all("SELECT * FROM secretary_noting_children")
        if rows and rows[-1]["status"] != "running":
            break
        time.sleep(.01)
    assert rows and len(rows) == 1
    assert not timers.holds_maintenance(parent)


@pytest.mark.parametrize("ending", ["prepare", "dispatch", "provider", "forced", "cancelled"])
def test_unsuccessful_noting_releases_parent_and_never_requests_idle_compaction(hosted, monkeypatch, ending):
    from tests.hermes_state._secretary_noting_harness import empty_state
    from agent.interrupt_compat import request_hard_interrupt
    sid, session, parent, db, ref = hosted
    previous = db.notebook_commit_snapshot(
        ref, empty_state(), anchor_message_uid=db.get_messages("stored")[0]["message_uid"], trigger_type="manual",
        termination={"type": "finish_noting", "reason": "Synthetic prior Notebook reviewed."})
    previous_id = db.notebook_current(ref)["snapshot_id"]
    assert previous
    timers.cancel_parent_idle_timer(parent)
    db.noting_idle_turn_finished(ref, time.time() - 10, due_at=time.time() - 1)
    calls = []
    monkeypatch.setattr(parent, "request_context_compaction", lambda **kwargs: calls.append(kwargs))
    original = noting_child.build_noting_child
    def build(*args, **kwargs):
        child = original(*args, **kwargs)
        child._disable_streaming = True
        def respond(request):
            if ending == "provider":
                raise RuntimeError("Synthetic provider failed")
            if ending == "cancelled":
                request_hard_interrupt(child)
                raise InterruptedError("Synthetic explicit stop during provider call")
            return mock_response("Synthetic unfinished work.")
        child._interruptible_api_call = respond
        return child
    monkeypatch.setattr(noting_child, "build_noting_child", build)
    if ending == "dispatch":
        def dispatch_unavailable(*args, **kwargs):
            raise RuntimeError("Synthetic dispatch unavailable")
        monkeypatch.setattr(rt, "_dispatch_joint_decision", dispatch_unavailable)
    if ending == "prepare":
        def unavailable(owner):
            raise OSError("Synthetic runtime freeze unavailable")
        monkeypatch.setattr(noting_child, "freeze_parent_runtime", unavailable)
    result = rt.maybe_run_idle_noting(parent, db, ref)
    assert result == ("skip:trigger_error" if ending in {"prepare", "dispatch"} else "admitted")
    deadline = time.monotonic() + 10
    while timers.holds_maintenance(parent) and time.monotonic() < deadline:
        time.sleep(.01)
    assert not timers.holds_maintenance(parent) and not calls
    rows = db._read_all("SELECT * FROM secretary_noting_children")
    assert len(rows) == 1
    if ending == "forced":
        current = db.notebook_current(ref)
        assert current and db.notebook_snapshot_audit(current["snapshot_id"])["termination"]["type"] == "forced"
    else:
        assert db.notebook_current(ref)["snapshot_id"] == previous_id
    assert rt.maybe_run_idle_noting(parent, db, ref) == "skip:idle_trigger_produced"
    reap_now(sid)
    assert sid not in server._sessions



def test_reaper_maintenance_predicate_is_only_short_registered_fact_read(hosted, monkeypatch):
    sid, session, parent, db, ref = hosted
    def forbidden(*args, **kwargs):
        raise AssertionError("Maintenance predicate must not query storage or resolve paths under host locks")
    monkeypatch.setattr(parent._session_db, "_read_ctx", forbidden)
    monkeypatch.setattr(parent._session_db, "get_session", forbidden)
    monkeypatch.setattr(timers, "_runtime_key", forbidden)
    with server._sessions_lock:
        assert timers.holds_maintenance(parent)
        assert not server._session_is_lru_evictable(sid, session)
    # Restore before the normal teardown / exact timer cancellation.
    monkeypatch.undo()



def test_timer_start_failure_releases_exact_registration_and_keeps_attach_deadline(hosted, monkeypatch):
    sid, session, parent, db, ref = hosted
    period = dict(db.noting_idle_state(ref))
    def unavailable(timer):
        raise RuntimeError("Synthetic timer thread unavailable")
    with monkeypatch.context() as patch:
        patch.setattr(threading.Timer, "start", unavailable)
        with pytest.raises(RuntimeError, match="timer thread unavailable"):
            timers.arm_idle_timer(parent, db, ref, period["due_at"])
    assert not timers.holds_maintenance(parent)
    assert db.noting_idle_state(ref) == period
    assert rt.maybe_run_idle_noting(parent, db, ref) == "skip:timer_armed"
    assert timers.holds_maintenance(parent)
