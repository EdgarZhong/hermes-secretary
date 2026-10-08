"""CLI Reminder ticks use the real serial input lane and existing busy monitor."""

import queue
import time
from datetime import datetime, timezone
from types import SimpleNamespace

import pytest

from hermes_state import SessionDB
from hermes_state_secretary_schedule import schedule_sync_conn
from secretary import cli_reminders, reminders
from tests.secretary.test_noting_surface import _agent, _requests, runtime as _native_runtime


@pytest.fixture
def native_runtime(tmp_path, monkeypatch):
    yield from _native_runtime.__wrapped__(tmp_path, monkeypatch)


@pytest.fixture
def cli_env(tmp_path, monkeypatch):
    db = SessionDB(tmp_path / "state.db")
    db.create_session("cli-main", source="cli")
    ref = db.resolve_conversation_ref("cli-main")
    from tests.secretary.reminder_runtime import bind_reminder_runtime
    agent = bind_reminder_runtime(db, ref, "cli-main")
    from hermes_cli.cli_tui_runtime_mixin import CLITuiRuntimeMixin
    import cli as cli_facade
    monkeypatch.setattr(cli_facade, "_cprint", lambda *_args, **_kwargs: None)
    cli = SimpleNamespace(agent=agent, _agent_running=False, _pending_input=queue.Queue(), calls=[])
    cli._tui_unwrap_input = lambda value: (value, False, False)
    cli._typed_voice_stop = lambda _value: False
    cli._pending_resume_sessions = []
    cli.handle_bang_shell = lambda _value: False
    cli._print_user_message_preview = lambda _value: None
    cli._turn_summary_begin = lambda: None
    cli._app = SimpleNamespace(invalidate=lambda: None)
    cli._tui_after_turn = lambda: setattr(cli, "_agent_running", False)
    def chat(value, **_kwargs):
        from tests.secretary.reminder_runtime import persist_native_carrier
        persist_native_carrier(db, agent.session_id, value)
        cli.calls.append(value)
        return "success"
    cli.chat = chat
    cli._tui_process_one_input = lambda value: CLITuiRuntimeMixin._tui_process_one_input(cli, value)
    yield cli, db, ref
    db.close()


def arm(db, ref, semantics="user_reminder"):
    if semantics == "user_reminder":
        from tests.secretary.reminder_runtime import arm_native_reminder
        return arm_native_reminder(db, ref, {"kind": "once", "run_at": datetime.fromtimestamp(
            time.time() - 30, timezone.utc).isoformat()}, "CLI reminder")
    return db._execute_write(lambda c: schedule_sync_conn(
        c, ref, "entry", active=True,
        canonical_schedule={"kind": "once", "run_at": datetime.fromtimestamp(time.time() - 30, timezone.utc).isoformat()},
        delivery_semantics=semantics, reminder_text="CLI reminder",
    ))


def test_cli_idle_tick_uses_normal_lane_and_preserves_due_timestamp(cli_env):
    cli, db, ref = cli_env
    row = arm(db, ref)
    cli_reminders.poll_cli_reminders(cli)
    assert len(cli.calls) == 1 and cli.calls[0] == reminders.user_reminder_text("CLI reminder", row["next_run_at"])
    from agent.message_metadata import TrustedUserInput, stamp_message_timestamp
    assert isinstance(cli.calls[0], TrustedUserInput)
    assert stamp_message_timestamp({"role": "user", "content": cli.calls[0]})["content"] == cli.calls[0]
    assert cli._pending_input.empty()
    assert db._read_one("SELECT state FROM secretary_schedule_registry")[0] == "done"
    assert reminders.pending_count(db, ref) == 0


@pytest.mark.parametrize("semantics,busy", [("system_reminder", False), ("user_reminder", True)])
def test_cli_busy_or_passive_due_never_queues_another_turn(cli_env, semantics, busy):
    cli, db, ref = cli_env
    row = arm(db, ref, semantics)
    cli._agent_running = busy
    cli_reminders.poll_cli_reminders(cli, busy=busy)
    assert cli.calls == [] and cli._pending_input.empty()
    pending = reminders.pull_pending(db, ref)
    assert len(pending) == 1 and pending[0]["source_timestamp"] == row["next_run_at"]
    assert reminders.ack(db, pending[0]["reminder_id"])
    assert reminders.pull_pending(db, ref) == []


def test_cli_local_off_then_on_retains_schedule_and_fires_once(cli_env):
    cli, db, ref = cli_env
    arm(db, ref)
    db.notebook_set_local_enabled(ref, False)
    cli_reminders.poll_cli_reminders(cli)
    assert cli.calls == []
    db.notebook_set_local_enabled(ref, True)
    cli._secretary_reminder_next_poll = 0
    cli_reminders.poll_cli_reminders(cli)
    cli._secretary_reminder_next_poll = 0
    cli_reminders.poll_cli_reminders(cli)
    assert len(cli.calls) == 1


def test_cli_lane_rechecks_claim_after_poll(cli_env):
    cli, db, ref = cli_env
    arm(db, ref)
    lane = cli._tui_process_one_input
    def disable_then_lane(value):
        db.notebook_set_local_enabled(ref, False)
        return lane(value)
    cli._tui_process_one_input = disable_then_lane
    cli_reminders.poll_cli_reminders(cli)
    assert cli.calls == [] and reminders.pending_count(db, ref) == 0
    assert db._read_one("SELECT state FROM secretary_schedule_registry")[0] == "pending"


def test_cli_invoke_failure_releases_the_original_occurrence(cli_env):
    cli, db, ref = cli_env
    row = arm(db, ref)
    cli.chat = lambda *_args, **_kwargs: None
    cli_reminders.poll_cli_reminders(cli)
    pending = reminders.pull_pending(db, ref)
    assert pending == []
    current = db._read_one("SELECT * FROM secretary_schedule_registry WHERE schedule_id=?", (row["schedule_id"],))
    assert current["state"] == "pending" and current["claim_token"] is None
    assert current["next_run_at"] == row["next_run_at"]
    assert cli._pending_input.empty()


def test_existing_cli_idle_housekeeping_is_the_real_scanner_entry(cli_env):
    from hermes_cli.cli_tui_runtime_mixin import CLITuiRuntimeMixin
    cli, db, ref = cli_env
    arm(db, ref)
    cli._check_config_mcp_changes = cli._check_termios_drift = lambda: None
    cli._drain_process_notifications = lambda _reason: None
    cli._maybe_fire_loop_tick = cli._maybe_resume_parked_goal = lambda: None
    CLITuiRuntimeMixin._tui_idle_tick(cli)
    assert len(cli.calls) == 1


def test_existing_chat_busy_monitor_tick_scans_without_any_input_queue(cli_env):
    from hermes_cli.cli_chat_turn_mixin import CLIChatTurnMixin
    cli, db, ref = cli_env
    arm(db, ref)
    cli._agent_running = True
    cli._voice_mode = False
    cli._interrupt_queue = queue.Queue()
    cli._invalidate = lambda **_kwargs: None
    states = iter([True, False])
    thread = SimpleNamespace(is_alive=lambda: next(states), join=lambda **_kwargs: None)
    assert CLIChatTurnMixin._chat_monitor_agent_thread(cli, SimpleNamespace(), thread) is None
    assert cli.calls == [] and cli._pending_input.empty()
    assert len(reminders.pull_pending(db, ref)) == 1


@pytest.mark.parametrize("trusted", [True, False])
def test_cold_cli_construct_then_real_chat_preserves_source_on_wire_and_durable(native_runtime, monkeypatch, trusted):
    from hermes_cli.cli_chat_turn_mixin import CLIChatTurnMixin
    import cli as facade
    db, config = native_runtime
    config.write_text("model:\n  context_length: 196000\nnoting:\n  enabled: true\n")
    db.create_session("surface-main", source="cli")
    ref = db.resolve_conversation_ref("surface-main")
    row = arm(db, ref)
    from secretary import noting_scope
    from secretary.noting_capability import _cold_capabilities
    noting_scope._main_runtimes.pop(noting_scope._runtime_key(db, ref), None)
    _cold_capabilities.pop(noting_scope._runtime_key(db, ref), None)
    agent = _agent(db, existing=False)
    assert not any(m["role"] == "user" for m in db.get_messages(agent.session_id))
    seen = _requests(agent)
    cli = SimpleNamespace(agent=agent, conversation_history=[], _active_agent_route_signature="same",
                          _secret_capture_callback=None, _voice_mode=False, _reasoning_shown_this_turn=False)
    cli._ensure_runtime_credentials = lambda: True
    cli._resolve_turn_agent_config = lambda _m: {"signature": "same", "model": agent.model, "runtime": {}}
    cli._init_agent = lambda **_kwargs: True
    cli._sync_fallback_chain_with_config = lambda _a: None
    cli._chat_route_images = lambda m, _images: m
    # The existing context/surrogate path can rebuild ordinary strings; provenance must survive it.
    cli._chat_expand_context_references = lambda m: (str(m), None)
    cli._chat_stage_user_message = lambda a, m: CLIChatTurnMixin._chat_stage_user_message(cli, a, m)
    cli._reset_stream_state = lambda: None
    cli._chat_setup_turn_audio = lambda *_args: None
    cli._chat_run_agent = lambda turn, m: setattr(turn, "result", agent.run_conversation(
        user_message=m, conversation_history=cli.conversation_history[:-1], title_user_message=""))
    cli._chat_monitor_agent_thread = lambda _turn, thread: thread.join()
    cli._chat_settle_turn = cli._chat_release_turn_audio = lambda _turn: None
    cli._chat_render_turn = lambda turn, *_args: turn.result
    monkeypatch.setattr(facade, "_cprint", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(facade, "ChatConsole", lambda: SimpleNamespace(print=lambda *_args: None))
    try:
        source = time.time() - 30
        carrier = reminders.user_reminder_text("source @ reminder", source)
        if trusted:
            from hermes_cli.cli_tui_runtime_mixin import CLITuiRuntimeMixin
            cli._tui_unwrap_input = lambda value: (value, False, False)
            cli._typed_voice_stop = cli.handle_bang_shell = lambda _value: False
            cli._pending_resume_sessions = []
            cli._print_user_message_preview = lambda _value: None
            cli._turn_summary_begin = lambda: None
            cli._app = SimpleNamespace(invalidate=lambda: None)
            cli._tui_after_turn = lambda: setattr(cli, "_agent_running", False)
            cli.chat = lambda value, **kwargs: CLIChatTurnMixin.chat(cli, value, **kwargs)
            cli._tui_process_one_input = lambda value: CLITuiRuntimeMixin._tui_process_one_input(cli, value)
            carrier = reminders.user_reminder_text(row["reminder_text"], row["next_run_at"])
            cli_reminders.poll_cli_reminders(cli)
            assert db._read_one("SELECT state FROM secretary_schedule_registry")[0] == "done"
        else:
            assert CLIChatTurnMixin.chat(cli, str(carrier))["completed"]
        durable_row = next(r for r in db.get_messages(agent.session_id) if r["role"] == "user")
        durable = durable_row["content"]
        wire = next(r["content"] for r in seen[0]["messages"] if r["role"] == "user")
        assert wire == durable
        if trusted:
            assert wire == carrier and wire.splitlines()[0] == "<user-reminder>"
            assert durable_row["timestamp"] == row["next_run_at"]
        else:
            assert wire.splitlines()[0].startswith("<timestamp>") and wire.endswith(carrier)
    finally:
        agent.close()
