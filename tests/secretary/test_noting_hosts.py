"""Existing host idle ticks and native token measurements start real Noting workers."""

import asyncio
import contextlib
import copy
import time
from pathlib import Path
from types import SimpleNamespace
import pytest

from tests.secretary import test_noting_child as harness


@pytest.fixture
def db(tmp_path):
    yield from harness.db.__wrapped__(tmp_path)


@pytest.fixture
def stub_client(monkeypatch, tmp_path):
    return harness.stub_client.__wrapped__(monkeypatch, tmp_path)


@pytest.fixture
def parent(db):
    return harness.parent.__wrapped__(db)


def _ready(parent, db, client):
    from tools.notebook_tool import NOTEBOOK_SHOW_SCHEMA
    parent.tools = [{"type": "function", "function": copy.deepcopy(NOTEBOOK_SHOW_SCHEMA)}]
    client.chat.completions.create.side_effect = harness._read_then_mutate_responses()
    db.noting_idle_turn_finished(parent._secretary_conversation_ref, time.time() - 1000)


def _wait_snapshot(db, ref):
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        snapshot = db.notebook_current(ref)
        if snapshot is not None:
            return snapshot
        time.sleep(0.01)
    raise AssertionError("The host tick did not complete its Noting Snapshot")


def test_cli_existing_idle_tick_starts_real_child(parent, db, stub_client):
    from hermes_cli.cli_tui_runtime_mixin import CLITuiRuntimeMixin
    _ready(parent, db, stub_client)
    noop = lambda *args: None
    cli = SimpleNamespace(agent=parent, _agent_running=False, _check_config_mcp_changes=noop,
                          _check_termios_drift=noop, _drain_process_notifications=noop,
                          _maybe_fire_loop_tick=noop, _maybe_resume_parked_goal=noop)
    CLITuiRuntimeMixin._tui_idle_tick(cli)
    assert _wait_snapshot(db, parent._secretary_conversation_ref)["trigger_type"] == "idle"


def test_messaging_housekeeping_scope_starts_real_child(parent, db, stub_client, monkeypatch):
    from secretary.noting_hosts import poll_gateway_noting
    from secretary.noting_scope import owning_db_scope
    _ready(parent, db, stub_client)
    homes = []
    @contextlib.asynccontextmanager
    async def scope(home):
        homes.append(home)
        with owning_db_scope(db):
            yield
    monkeypatch.setattr("gateway.secretary_reminders._delivery_scope", scope)
    runner = SimpleNamespace(_agent_cache={"session": (parent, "sig"), "alias": (parent, "sig")})
    asyncio.run(poll_gateway_noting(runner))
    assert _wait_snapshot(db, parent._secretary_conversation_ref)["trigger_type"] == "idle"
    assert homes == [Path(db.db_path).parent]


def test_turn_start_measurement_spawns_force_and_once_pending(parent, db, stub_client, monkeypatch):
    from agent.turn_context import _preflight_request_tokens
    _ready(parent, db, stub_client)
    parent.context_compressor.context_length = 130_000
    parent.context_compressor.threshold_tokens = 75_000
    monkeypatch.setattr("agent.turn_context._resolved_preflight_request_tokens", lambda *a: 64_000)
    tokens = _preflight_request_tokens(parent, parent._session_messages, parent._cached_system_prompt)
    assert tokens == 64_000
    ref = parent._secretary_conversation_ref
    current = _wait_snapshot(db, ref)
    assert current["trigger_type"] == "force"
    _preflight_request_tokens(parent, parent._session_messages, parent._cached_system_prompt)
    with db._read_ctx() as conn:
        pending = db.reminder_pull_pending_conn(conn, ref)
        admitted = conn.execute("SELECT admitted_at FROM secretary_noting_admissions WHERE conversation_ref = ?", (ref,)).fetchone()[0]
    assert len(pending) == 1 and pending[0]["source_timestamp"] == admitted


def test_owner_profile_off_overrides_enabled_launch_and_reminder_read_failure(parent, db, stub_client, monkeypatch):
    from secretary.noting_hosts import poll_parent_idle
    from secretary.reminder_request import inject_pending_reminders
    from hermes_state_secretary_schedule import reminder_append_pending_conn
    _ready(parent, db, stub_client)
    ref = parent._secretary_conversation_ref
    (Path(db.db_path).parent / "config.yaml").write_text("noting:\n  enabled: false\n")
    assert poll_parent_idle(parent) == "skip:global_disabled"
    db._execute_write(lambda conn: reminder_append_pending_conn(conn, ref, "pending", source_timestamp=1234))
    api_messages = []
    assert inject_pending_reminders(parent, api_messages) == (0, 0)
    (Path(db.db_path).parent / "config.yaml").write_text("noting:\n  enabled: true\n")
    def unavailable(*args):
        raise RuntimeError("unavailable local state")
    monkeypatch.setattr(db, "notebook_local_enabled_conn", unavailable)
    assert inject_pending_reminders(parent, api_messages) == (0, 0)
    with db._read_ctx() as conn:
        assert len(db.reminder_pull_pending_conn(conn, ref)) == 1


def test_force_pending_failure_rolls_back_admission(parent, db, stub_client, monkeypatch):
    from secretary.noting_policy import ContextMeasurement
    from secretary.noting_runtime import try_admit_force
    def fail(*args, **kwargs):
        raise RuntimeError("pending store failed")
    monkeypatch.setattr("hermes_state_secretary_schedule.reminder_append_pending_conn", fail)
    decision = try_admit_force(db, parent._secretary_conversation_ref, ContextMeasurement(64_000, 130_000, 75_000))
    assert decision.reason == "trigger_error"
    with db._read_ctx() as conn:
        assert conn.execute("SELECT COUNT(*) FROM secretary_noting_admissions").fetchone()[0] == 0
