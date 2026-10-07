"""Secretary Schedule/Reminder gateway host wiring on a real store with a light fake ingress."""

import asyncio
import sys
import time
import types
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

# Minimal stubs so gateway code imports without heavy platform deps (same shape as other gateway tests).
_tg = types.ModuleType("telegram")
_tg.constants = types.ModuleType("telegram.constants")
_ct = MagicMock()
_ct.SUPERGROUP, _ct.GROUP, _ct.PRIVATE = "supergroup", "group", "private"
_tg.constants.ChatType = _ct
sys.modules.setdefault("telegram", _tg)
sys.modules.setdefault("telegram.constants", _tg.constants)
sys.modules.setdefault("telegram.ext", types.ModuleType("telegram.ext"))

from gateway.platforms.base import Platform, SessionSource, build_session_key  # noqa: E402
from gateway.platforms.event import MessageEvent, MessageType  # noqa: E402
from hermes_state import SessionDB  # noqa: E402
from hermes_state_secretary_schedule import init_secretary_schedule_schema, schedule_sync_conn  # noqa: E402

import gateway.secretary_reminders as host  # noqa: E402
from secretary import reminders as secretary_reminders  # noqa: E402


def iso(offset_seconds):
    return (datetime.now(timezone.utc) + timedelta(seconds=offset_seconds)).isoformat()


class _FakeStore:
    def __init__(self, entries):
        self._entries = entries

    def _ensure_loaded(self):
        return None


class _FakeAdapter:
    supports_async_delivery = True

    def __init__(self):
        self.events = []

    async def handle_message(self, event):
        self.events.append(event)
        event._gateway_accepted = True


class _Host:
    def __init__(self, db, home, source, adapter, session_key):
        self.home = home
        self.db = db
        self._session_source = source
        self._adapter = adapter
        self.config = SimpleNamespace()
        self.session_store = _FakeStore({session_key: SimpleNamespace(origin=source, transport_profile=None)})
        self._running = True

    def make_runner(self):
        from gateway.run import GatewayRunner
        runner = SimpleNamespace()
        runner.config = self.config
        runner.session_store = self.session_store
        runner._restored_source = lambda entry: self._session_source
        runner._delivery_adapter_for = lambda source: self._adapter
        runner._synthetic_prompt_event = GatewayRunner._synthetic_prompt_event
        return runner


@pytest.fixture
def host_env(tmp_path, monkeypatch):
    home = tmp_path / "profile"
    home.mkdir()
    db = SessionDB(home / "state.db")
    db._execute_write(init_secretary_schedule_schema)
    db.create_session("s1", source="test", session_key="peer")
    ref = db.resolve_conversation_ref("s1", ("test", "peer", 0))
    source = SessionSource(platform=Platform.TELEGRAM, chat_id="123", chat_type="dm", user_id="user1")
    adapter = _FakeAdapter()
    h = _Host(db, home, source, adapter, "peer")
    monkeypatch.setattr(host, "_profile_homes", lambda runner: [("default", home)])
    yield h, db, ref, adapter, source
    db.close()


def arm_due(db, ref, *, semantics="user_reminder", text="ping the user", entry_id="entry_1"):
    row = db._execute_write(lambda conn: schedule_sync_conn(
        conn, ref, entry_id, active=True, canonical_schedule={"kind": "once", "run_at": iso(-30)},
        delivery_semantics=semantics, reminder_text=text,
    ))
    db._execute_write(lambda conn: conn.execute(
        "UPDATE secretary_schedule_registry SET next_run_at = ? WHERE schedule_id = ?",
        (time.time() - 5, row["schedule_id"]),
    ))
    return row


def registry(db, schedule_id):
    return dict(db._read_one("SELECT * FROM secretary_schedule_registry WHERE schedule_id = ?", (schedule_id,)))


def pending_count(db, ref):
    return db._read_one(
        "SELECT COUNT(*) FROM secretary_pending_reminders WHERE conversation_ref = ? AND status = 'pending'",
        (ref,),
    )[0]


@pytest.mark.asyncio
async def test_idle_scan_delivers_active_reminder_through_ingress(host_env):
    h, db, ref, adapter, source = host_env
    row = arm_due(db, ref)
    runner = h.make_runner()
    assert await host.scan_due_secretary_schedules(runner) == 1
    tasks = getattr(runner, "_secretary_delivery_tasks", set())
    if tasks:
        await asyncio.gather(*tasks)
    assert len(adapter.events) == 1
    event = adapter.events[0]
    assert event.source is source
    assert event.text.startswith("<user-reminder>\n<timestamp>")
    assert "ping the user" in event.text
    assert event.text.splitlines()[1].startswith("<timestamp>")
    assert registry(db, row["schedule_id"])["state"] == "done"
    assert pending_count(db, ref) == 0
    # No cron_* session and no second Turn session: the ingress ran the reminder's own turn.
    assert db._read_one("SELECT COUNT(*) FROM sessions")[0] == 1


@pytest.mark.asyncio
async def test_scan_queues_passive_reminder_without_any_turn(host_env):
    h, db, ref, adapter, _source = host_env
    row = arm_due(db, ref, semantics="system_reminder", text="commitment due")
    runner = h.make_runner()
    assert await host.scan_due_secretary_schedules(runner) == 1
    assert adapter.events == []
    items = secretary_reminders.pull_pending(db, ref)
    assert len(items) == 1
    assert items[0]["text"].startswith("<system-reminder>\n<timestamp>")
    assert "commitment due" in items[0]["text"]
    assert registry(db, row["schedule_id"])["state"] == "done"


@pytest.mark.asyncio
async def test_unresolvable_route_defers_delivery_and_keeps_the_occurrence(host_env):
    h, db, ref, adapter, _source = host_env
    row = arm_due(db, ref)
    db.end_session("s1", "session_reset")
    db.create_session("s2", source="test", session_key="peer")
    runner = h.make_runner()
    assert await host.scan_due_secretary_schedules(runner) == 0
    assert adapter.events == []
    current = registry(db, row["schedule_id"])
    assert current["state"] == "pending" and current["claim_token"] is None
    assert current["next_run_at"] <= time.time()  # still due: retried, never discarded


@pytest.mark.asyncio
async def test_busy_gate_converts_secretary_reminder_to_pending_not_a_second_turn(host_env):
    h, db, ref, adapter, source = host_env
    row = arm_due(db, ref)
    from secretary.schedules import scan_and_claim_due
    claim = scan_and_claim_due(db, owner="gateway-test", conversation_ref=ref)[0]
    from gateway.run import GatewayRunner
    runner = object.__new__(GatewayRunner)
    runner._running_agents = {}
    runner._draining = False
    runner.adapters = {}
    runner._queued_events = {}
    runner._pending_messages = {}
    runner.config = MagicMock()
    runner._is_user_authorized_for_source = lambda _source: True
    runner._admit_bot_message_for_source = lambda _source: True
    runner._resolve_profile_home_for_source = lambda _source: h.home
    event = MessageEvent(
        text="<user-reminder>\n<timestamp>x</timestamp>\nping the user\n</user-reminder>",
        message_type=MessageType.TEXT, source=source, internal=True, allow_gateway_control=False,
        metadata={"secretary_user_reminder": {
            "conversation_ref": ref, "schedule_id": row["schedule_id"],
            "claim_token": claim["claim_token"], "source_timestamp": time.time() - 5,
            "content": "ping the user",
        }},
    )
    assert await GatewayRunner._handle_active_session_busy_message(runner, event, build_session_key(source)) is True
    assert runner._queued_events == {}  # not a queued future Turn
    items = secretary_reminders.pull_pending(db, ref)
    assert len(items) == 1 and "ping the user" in items[0]["text"]
    assert registry(db, row["schedule_id"])["state"] == "done"


def test_busy_conversion_helper_ignores_other_events():
    runner = SimpleNamespace()
    assert host.convert_busy_reminder_event(runner, SimpleNamespace(metadata={})) is False
    assert host.convert_busy_reminder_event(runner, SimpleNamespace(metadata=None)) is False
