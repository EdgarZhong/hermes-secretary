"""Controlled SIGKILL at native SQL boundaries, followed by fresh host due scans."""
import asyncio
import contextlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from hermes_state import SessionDB
from secretary import reminders
from tests.secretary.reminder_runtime import arm_native_reminder
from tests.secretary.test_noting_surface import _agent, _requests


def _sql_fault(db, boundary):
    original = db.append_messages_batch
    def die():
        os.kill(os.getpid(), signal.SIGKILL)
    def append(*args, **kwargs):
        callback = kwargs.get("before_commit")
        if callback is None:
            return original(*args, **kwargs)
        if boundary == "before":
            die()
        if boundary == "inside":
            def mid_transaction(conn, sid, inserted):
                # Actual native INSERT has happened, but both row and finalize remain uncommitted.
                assert conn.execute("SELECT COUNT(*) FROM messages WHERE role='user'").fetchone()[0] == 1
                callback(conn, sid, inserted)
                die()
            kwargs["before_commit"] = mid_transaction
        result = original(*args, **kwargs)
        if boundary == "after":
            die()
        return result
    db.append_messages_batch = append


def _cli_scan(agent):
    from hermes_cli.cli_tui_runtime_mixin import CLITuiRuntimeMixin
    from secretary.cli_reminders import poll_cli_reminders
    cli = SimpleNamespace(agent=agent, _agent_running=False, _pending_resume_sessions=[],
                          _app=SimpleNamespace(invalidate=lambda: None))
    cli._tui_unwrap_input = lambda value: (value, False, False)
    cli._typed_voice_stop = cli.handle_bang_shell = lambda _v: False
    cli._print_user_message_preview = cli._turn_summary_begin = lambda *a: None
    cli._tui_after_turn = lambda: setattr(cli, "_agent_running", False)
    cli.chat = lambda value, **kw: agent.run_conversation(value, title_user_message="")
    cli._tui_process_one_input = lambda value: CLITuiRuntimeMixin._tui_process_one_input(cli, value)
    poll_cli_reminders(cli)


def _tui_scan(agent, home, mp):
    from tui_gateway import server as turn
    session = {"session_key": agent.session_id, "history_lock": threading.RLock(), "agent": agent,
               "running": False, "profile_home": str(home)}
    mp.setattr(turn, "_session_db", lambda _s: contextlib.nullcontext(agent._session_db))
    mp.setattr(turn, "_routing_provenance_db", lambda _s: contextlib.nullcontext(agent._session_db))
    mp.setattr(turn, "_ensure_session_db_row", lambda _s: True)
    mp.setattr(turn, "_admit_prompt_turn", lambda *a: ([], agent))
    mp.setattr(turn, "_prepare_turn_input", lambda sid, s, st, text, images: (text, str(text), None, None))
    mp.setattr(turn, "_start_usage_ticker", lambda *a: (SimpleNamespace(set=lambda: None), SimpleNamespace(join=lambda: None)))
    mp.setattr(turn, "_adopt_submit_user_row", lambda *a: None)
    mp.setattr(turn, "_load_interim_assistant_messages", lambda: False)
    mp.setattr(turn, "_sessions", {})
    mp.setattr(turn, "_sessions_lock", threading.RLock())
    mp.setattr(turn, "_start_session_work", lambda fn, **kw: (fn(), True)[1])
    mp.setattr(turn, "_absorb_turn_result", lambda *a: None)
    mp.setattr(turn, "_complete_turn_payload", lambda *a: ({}, "done", "complete"))
    mp.setattr(turn, "_goal_followup_after_turn", lambda *a: None)
    mp.setattr(turn, "_post_turn_housekeeping", lambda *a: session.update(running=False))
    for name in ("_emit", "_after_complete_turn", "_publish_session_control_snapshot", "_emit_settled_session_info", "_run_post_turn_followups"):
        mp.setattr(turn, name, lambda *a, **kw: None)
    # This is the actual reopen recovery decision, before the existing due scan.
    assert turn._maybe_schedule_auto_continue("crash-ui", session, agent.session_id) is None
    turn._maybe_fire_tui_secretary_reminder("crash-ui", session)


def _gateway_scan(agent, home, mp):
    from tests.gateway.test_secretary_reminders import _Host, _FakeAdapter, native_runner
    from gateway.platforms.base import Platform, SessionSource
    from gateway.run_turn import GatewayTurnMixin
    import gateway.secretary_reminders as host
    db = agent._session_db
    db._reminder_test_runtime = agent
    source = SessionSource(platform=Platform.TELEGRAM, chat_id="123", chat_type="dm", user_id="user1")
    adapter = _FakeAdapter()
    h = _Host(db, home, source, adapter, "peer")
    runner = h.make_runner()
    runner._resolve_session_agent_runtime = lambda **kw: (agent.model, {
        "provider": agent.provider, "api_mode": agent.api_mode, "base_url": agent.base_url, "max_tokens": agent.max_tokens})
    mp.setattr(host, "_profile_homes", lambda _r: [("default", home)])
    mp.setattr("gateway.run._load_gateway_config", lambda: {})
    async def handle(event):
        native_runner(h, event, [], mp, runner=runner)
        async def invoke(e, *_a):
            e._heartbeat_execution_started = True
            message, persist, timestamp = GatewayTurnMixin._hmwa_apply_message_timestamp(None, e, str(e.text))
            return agent.run_conversation(message, persist_user_message=persist,
                                          persist_user_timestamp=timestamp, title_user_message="")
        runner._handle_message_with_agent = invoke
        await runner.handle()
    adapter.handle_message = handle
    async def scan():
        await host.scan_due_secretary_schedules(runner)
        await asyncio.gather(*getattr(runner, "_secretary_delivery_tasks", set()))
    asyncio.run(scan())


def _child(home, host, boundary):
    mp = pytest.MonkeyPatch()
    client = MagicMock()
    mp.setattr("agent.process_bootstrap.OpenAI", lambda **kw: client)
    mp.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **kw: {})
    mp.setattr("agent.title_generator.maybe_auto_title", lambda *a, **kw: None)
    mp.setattr("run_agent._hermes_home", home)
    db = SessionDB(home / "state.db")
    agent = _agent(db, existing=False, session_id="s1")
    seen = _requests(agent)
    _sql_fault(db, boundary)
    {"cli": lambda: _cli_scan(agent), "tui": lambda: _tui_scan(agent, home, mp),
     "gateway": lambda: _gateway_scan(agent, home, mp)}[host]()
    result = {"requests": len(seen), "rows": len([r for r in db.get_messages("s1") if r["role"] == "user"])}
    (home / "result.json").write_text(json.dumps(result))
    agent.close()
    db.close()
    mp.undo()


def child(home, host, boundary):
    env = {**os.environ, "HERMES_HOME": str(home)}
    return subprocess.run([sys.executable, "-m", "tests.secretary.test_active_reminder_crash", "child", str(home), host, boundary],
                          env=env, capture_output=True, text=True, timeout=30)


def prepare(home, host):
    home.mkdir()
    (home / "config.yaml").write_text("model:\n  context_length: 196000\nnoting:\n  enabled: true\n")
    db = SessionDB(home / "state.db")
    db.create_session("s1", source="telegram" if host == "gateway" else "cli", session_key="peer", profile_name="default")
    ref = db.resolve_conversation_ref("s1", ("telegram", "peer", 0) if host == "gateway" else None)
    row = arm_native_reminder(db, ref, {"kind": "once", "run_at": datetime.fromtimestamp(
        time.time() - 30, timezone.utc).isoformat()}, "crash recoverable")
    db.close()
    return ref, row


@pytest.mark.parametrize("host", ["cli", "tui", "gateway"])
@pytest.mark.parametrize("boundary", ["before", "inside", "after"])
def test_sigkill_native_transaction_then_fresh_host_scan(tmp_path, host, boundary):
    home = tmp_path / host
    _ref, original = prepare(home, host)
    killed = child(home, host, boundary)
    assert killed.returncode == -signal.SIGKILL, killed.stdout + killed.stderr
    db = SessionDB(home / "state.db")
    state = dict(db._read_one("SELECT * FROM secretary_schedule_registry"))
    users = [r for r in db.get_messages("s1") if r["role"] == "user"]
    committed = boundary == "after"
    assert state["state"] == ("done" if committed else "pending")
    assert len(users) == int(committed)
    if host == "tui":
        from tui_gateway.turn_marker import read_turn_marker
        marker = read_turn_marker(home, "s1")
        assert marker and marker["auto_continue"] is False
        assert marker["writer_pid"] != os.getpid()
    # Advance only existing lease clocks, representing their real expiry after process death.
    db._execute_write(lambda c: c.execute("UPDATE secretary_schedule_registry SET claim_expires_at=? WHERE claim_token IS NOT NULL", (time.time() - 1,)))
    db._execute_write(lambda c: c.execute("UPDATE session_turn_leases SET expires_at=?", (time.time() - 1,)))
    db.close()
    resumed = child(home, host, "resume")
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert json.loads((home / "result.json").read_text()) == {"requests": int(not committed), "rows": 1}
    db = SessionDB(home / "state.db")
    try:
        final = dict(db._read_one("SELECT * FROM secretary_schedule_registry"))
        assert final["state"] == "done" and final["claim_token"] is None
        users = [r for r in db.get_messages("s1") if r["role"] == "user"]
        assert len(users) == 1 and users[0]["timestamp"] == original["next_run_at"]
    finally:
        db.close()


@pytest.mark.parametrize("change", ["local_off", "cancel"])
def test_tui_crashed_marker_cannot_replay_while_current_schedule_is_off(tmp_path, change):
    home = tmp_path / "tui"
    ref, _row = prepare(home, "tui")
    killed = child(home, "tui", "before")
    assert killed.returncode == -signal.SIGKILL, killed.stdout + killed.stderr
    db = SessionDB(home / "state.db")
    if change == "local_off":
        db.notebook_set_local_enabled(ref, False)
    else:
        from hermes_state_secretary_schedule import schedule_sync_conn
        db._execute_write(lambda c: schedule_sync_conn(c, ref, "entry", active=False, cancelled=True))
    db._execute_write(lambda c: c.execute("UPDATE secretary_schedule_registry SET claim_expires_at=?", (time.time() - 1,)))
    db._execute_write(lambda c: c.execute("UPDATE session_turn_leases SET expires_at=?", (time.time() - 1,)))
    db.close()
    resumed = child(home, "tui", "resume")
    assert resumed.returncode == 0, resumed.stdout + resumed.stderr
    assert json.loads((home / "result.json").read_text()) == {"requests": 0, "rows": 0}


if __name__ == "__main__":
    _child(Path(sys.argv[2]), sys.argv[3], sys.argv[4])
