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

    def lookup_by_session_key(self, key):
        return self._entries.get(key)

    def advance_compression_session(self, key, expected, target):
        entry = self._entries.get(key)
        if entry is None or entry.session_id != expected:
            return None
        entry.session_id = target
        return entry


class _FakeAdapter:
    supports_async_delivery = True

    def __init__(self):
        self.events = []

    async def handle_message(self, event):
        self.events.append(event)
        event._gateway_accepted = True
        # This light ingress explicitly models the final native slot admission too.
        assert host.admit_secretary_reminder_event(self.runner, event)
        from tests.secretary.reminder_runtime import persist_native_carrier
        persist_native_carrier(self.runner.session_store_db, "s1", event.text)
        event._secretary_turn_completed = True


class _Host:
    def __init__(self, db, home, source, adapter, session_key):
        self.home = home
        self.db = db
        self._session_source = source
        self._adapter = adapter
        self.config = SimpleNamespace()
        self.session_store = _FakeStore({session_key: SimpleNamespace(origin=source, session_key=session_key,
                                                                     session_id="s1", transport_profile=None)})
        self._running = True

    def make_runner(self):
        from gateway.run import GatewayRunner
        runner = SimpleNamespace()
        runner.config = self.config
        runner.session_store_db = self.db
        runner.session_store = self.session_store
        runner._agent_cache = {"peer": self.db._reminder_test_runtime}
        runner._restored_source = lambda entry: self._session_source
        runner._delivery_adapter_for = lambda source: self._adapter
        runner._resolve_profile_home_for_source = lambda source: self.home
        runner._synthetic_prompt_event = GatewayRunner._synthetic_prompt_event
        runner._resolve_session_agent_runtime = lambda **_kwargs: ("test/reminder-runtime", {
            "provider": "openai", "api_mode": "chat_completions", "base_url": "", "max_tokens": None})
        self._adapter.runner = runner
        return runner


@pytest.fixture
def host_env(tmp_path, monkeypatch):
    home = tmp_path / "profile"
    home.mkdir()
    db = SessionDB(home / "state.db")
    db._execute_write(init_secretary_schedule_schema)
    db.create_session("s1", source="telegram", session_key="peer", profile_name="default")
    ref = db.resolve_conversation_ref("s1", ("telegram", "peer", 0))
    from tests.secretary.reminder_runtime import bind_reminder_runtime
    bind_reminder_runtime(db, ref, "s1")
    source = SessionSource(platform=Platform.TELEGRAM, chat_id="123", chat_type="dm", user_id="user1")
    adapter = _FakeAdapter()
    h = _Host(db, home, source, adapter, "peer")
    monkeypatch.setattr(host, "_profile_homes", lambda runner: [("default", home)])
    yield h, db, ref, adapter, source
    db.close()


def arm_due(db, ref, *, semantics="user_reminder", text="ping the user", entry_id="entry_1"):
    if semantics == "user_reminder":
        from tests.secretary.reminder_runtime import arm_native_reminder
        return arm_native_reminder(db, ref, {"kind": "once", "run_at": iso(-30)}, text, entry_id)
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
            "claim_token": claim["claim_token"], "source_timestamp": claim["next_run_at"],
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


@pytest.mark.asyncio
@pytest.mark.parametrize('failure', ['physical_session', 'profile', 'source', 'suspended'])
async def test_session_store_must_prove_live_owner_before_native_ingress(host_env, failure):
    h, db, ref, adapter, _source = host_env
    row = arm_due(db, ref)
    runner = h.make_runner()
    entry = runner.session_store.lookup_by_session_key('peer')
    if failure == 'physical_session':
        db.create_session('foreign', source='telegram', profile_name='default')
        entry.session_id = 'foreign'
    elif failure == 'profile':
        runner._resolve_profile_home_for_source = lambda source: h.home / 'different-profile'
    elif failure == 'source':
        runner._restored_source = lambda entry: SessionSource(platform=Platform.DISCORD, chat_id='123')
    else:
        entry.suspended = True
    await host.scan_due_secretary_schedules(runner)
    await asyncio.gather(*runner._secretary_delivery_tasks)
    assert adapter.events == []
    current = registry(db, row['schedule_id'])
    assert current['state'] == 'pending' and current['claim_token'] is None


@pytest.mark.asyncio
async def test_compression_tip_proof_accepts_owned_ancestor_entry(host_env):
    h, db, ref, adapter, _source = host_env
    arm_due(db, ref)
    db.end_session('s1', 'compression')
    db.create_session('s2', source='telegram', parent_session_id='s1', profile_name='default')
    runner = h.make_runner()
    await host.scan_due_secretary_schedules(runner)
    await asyncio.gather(*runner._secretary_delivery_tasks)
    assert len(adapter.events) == 1


@pytest.mark.asyncio
async def test_scan_and_delivery_release_their_own_registry_handles(host_env, monkeypatch):
    h, db, ref, adapter, _source = host_env
    arm_due(db, ref)
    acquired, released = [], []
    acquire, release = host._acquire_db, host._release_db
    def record_acquire(home):
        handle = acquire(home)
        acquired.append(handle)
        return handle
    def record_release(handle):
        released.append(handle)
        release(handle)
    monkeypatch.setattr(host, '_acquire_db', record_acquire)
    monkeypatch.setattr(host, '_release_db', record_release)
    runner = h.make_runner()
    await host.scan_due_secretary_schedules(runner)
    await asyncio.gather(*runner._secretary_delivery_tasks)
    assert len(adapter.events) == 1
    assert len(acquired) == len(released) == 3
    assert sorted(map(id, acquired)) == sorted(map(id, released))


@pytest.mark.asyncio
async def test_scan_cancellation_releases_acquired_registry_handle(host_env, monkeypatch):
    h, _db, _ref, _adapter, _source = host_env
    started = asyncio.Event()
    released = []
    release = host._release_db
    async def blocked(*args, **kwargs):
        started.set()
        await asyncio.Future()
    def record_release(handle):
        released.append(handle)
        release(handle)
    monkeypatch.setattr(host, '_run_blocking', blocked)
    monkeypatch.setattr(host, '_release_db', record_release)
    task = asyncio.create_task(host.scan_due_secretary_schedules(h.make_runner()))
    await started.wait()
    task.cancel()
    with pytest.raises(asyncio.CancelledError):
        await task
    assert len(released) == 1


@pytest.mark.asyncio
@pytest.mark.parametrize('rejection', ['global_off', 'local_off', 'admission'])
async def test_scan_to_ingress_rechecks_gate_and_requires_native_receipt(host_env, monkeypatch, rejection):
    h, db, ref, adapter, _source = host_env
    row = arm_due(db, ref)
    runner = h.make_runner()
    if rejection == 'local_off':
        original = host._spawn_delivery
        def disable_then_spawn(*args):
            db.notebook_set_local_enabled(ref, False)
            return original(*args)
        monkeypatch.setattr(host, '_spawn_delivery', disable_then_spawn)
    elif rejection == 'global_off':
        from secretary import schedules
        calls = []
        def gate(_db):
            calls.append(True)
            return lambda _ref: len(calls) == 1
        monkeypatch.setattr(schedules, 'default_enablement', gate)
    else:
        async def refuse(event):
            event._gateway_accepted = False
        adapter.handle_message = refuse
    await host.scan_due_secretary_schedules(runner)
    await asyncio.gather(*runner._secretary_delivery_tasks)
    assert adapter.events == []
    current = registry(db, row['schedule_id'])
    assert current['state'] == 'pending' and current['claim_token'] is None


def native_runner(h, event, calls, monkeypatch, runner=None):
    """Use the real Gateway _handle_message; fake unrelated auth/transport/model boundaries."""
    from gateway.run import GatewayRunner
    runner = h.make_runner() if runner is None else runner
    async def admitted(_event):
        return _event, _event.source, True
    async def none(*_args):
        return None
    async def commands(*_args):
        return False, None
    async def model(*_args):
        _args[0]._heartbeat_execution_started = True
        from tests.secretary.reminder_runtime import persist_native_carrier
        persist_native_carrier(h.db, h.db.resolve_conversation_route(h.db.resolve_conversation_ref("s1"))["id"], _args[0].text)
        calls.append(_args[0].text)
        return "accepted"
    runner._hm_admit_event = admitted
    runner._hm_estop_gate = lambda *_args: None
    runner._session_key_for_source = lambda _source: "peer"
    runner._hm_pending_reply_intercepts = none
    runner._hm_evict_idle_stale_agent = lambda _key: None
    runner._hm_evict_reaped_agent = lambda _key: None
    runner._is_session_running = lambda _key: False
    runner._hm_dispatch_idle_commands = commands
    runner._claim_active_session_slot = lambda *_args: (None, None)
    runner._hm_rescue_orphaned_fifo = lambda e, s, internal, _key: (e, s, internal)
    state = SimpleNamespace(turn=SimpleNamespace(), conversation=SimpleNamespace())
    runner._session_state = lambda _key: state
    runner._persist_active_agents = lambda: None
    runner._begin_session_run_generation = lambda _key: 1
    runner._handle_message_with_agent = model
    runner._run_post_turn_hooks = none
    runner._restore_pending_one_turn_model_override = lambda *_args: None
    runner._clear_durable_active_turn = none
    runner.released = []
    runner._release_running_agent_state = lambda *args, **kwargs: runner.released.append("slot")
    runner._release_turn_lease = lambda *args, **kwargs: runner.released.append("lease")
    monkeypatch.setattr("hermes_cli.observability.shared_metrics_gateway.start_reply_clock", lambda *a, **k: None)
    runner.handle = lambda: GatewayRunner._handle_message(runner, event)
    return runner


def claim_event(h, db, ref, claim):
    resolved = secretary_reminders.resolve_active_reminder(db, claim)
    event = MessageEvent(text=resolved["text"], message_type=MessageType.TEXT, source=h._session_source,
                         internal=True, allow_gateway_control=False,
                         metadata={"gateway_session_key": "peer", "gateway_session_id": "s1",
                                   "secretary_user_reminder": {"conversation_ref": ref,
                                                              "schedule_id": claim["schedule_id"],
                                                              "claim_token": claim["claim_token"],
                                                              "source_timestamp": claim["next_run_at"]}})
    return event


@pytest.mark.asyncio
@pytest.mark.parametrize("change", ["local_off", "cancel", "reclaim"])
async def test_native_admission_rechecks_after_adapter_task_ack(host_env, monkeypatch, change):
    h, db, ref, _adapter, _source = host_env
    row = arm_due(db, ref)
    from secretary.schedules import claim_due
    claim = claim_due(db, row["schedule_id"], owner="old")
    event = claim_event(h, db, ref, claim)
    event._gateway_accepted = True  # Adapter already reserved its background dispatch task.
    if change == "local_off":
        db.notebook_set_local_enabled(ref, False)
    elif change == "cancel":
        db._execute_write(lambda conn: schedule_sync_conn(conn, ref, "entry_1", active=False, cancelled=True))
    else:
        db._execute_write(lambda conn: conn.execute(
            "UPDATE secretary_schedule_registry SET claim_expires_at = ? WHERE schedule_id = ?",
            (time.time() - 1, row["schedule_id"])))
        claim_due(db, row["schedule_id"], owner="new")
    calls = []
    runner = native_runner(h, event, calls, monkeypatch)
    assert await runner.handle() is None
    assert calls == [] and runner.released == ["slot", "lease"]
    assert registry(db, row["schedule_id"])["state"] != "done"
    if change == "reclaim":
        assert registry(db, row["schedule_id"])["claim_owner"] == "new"


@pytest.mark.asyncio
async def test_real_native_admission_consumes_once_and_keeps_existing_finally(host_env, monkeypatch):
    h, db, ref, _adapter, _source = host_env
    row = arm_due(db, ref)
    from secretary.schedules import claim_due
    claim = claim_due(db, row["schedule_id"], owner="old")
    event = claim_event(h, db, ref, claim)
    calls = []
    runner = native_runner(h, event, calls, monkeypatch)
    assert await runner.handle() == "accepted"
    assert len(calls) == 1 and registry(db, row["schedule_id"])["state"] == "done"
    assert runner.released == ["slot", "lease"]
    assert claim_due(db, row["schedule_id"], owner="new", now=claim["claim_expires_at"] + 1) is None


@pytest.mark.asyncio
async def test_native_invoke_failure_restores_due_without_overwriting_new_intent(host_env, monkeypatch):
    h, db, ref, _adapter, _source = host_env
    row = arm_due(db, ref)
    from secretary.schedules import claim_due
    claim = claim_due(db, row["schedule_id"], owner="old")
    event = claim_event(h, db, ref, claim)
    runner = native_runner(h, event, [], monkeypatch)
    async def fail(*_args):
        raise RuntimeError("actual invoke refused")
    runner._handle_message_with_agent = fail
    with pytest.raises(RuntimeError, match="actual invoke"):
        await runner.handle()
    current = registry(db, row["schedule_id"])
    assert current["state"] == "pending" and current["next_run_at"] == claim["next_run_at"]
    assert current["claim_token"] is None and runner.released == ["slot", "lease"]


@pytest.mark.asyncio
@pytest.mark.parametrize("stale", [False, True])
async def test_adapter_idle_task_that_loses_native_slot_converts_at_runner_busy_gate(host_env, monkeypatch, stale):
    h, db, ref, _adapter, _source = host_env
    row = arm_due(db, ref)
    from secretary.schedules import claim_due
    claim = claim_due(db, row["schedule_id"], owner="old")
    event = claim_event(h, db, ref, claim)
    if stale:
        db.notebook_set_local_enabled(ref, False)
    runner = native_runner(h, event, [], monkeypatch)
    runner._is_session_running = lambda _key: True
    async def forbidden(*_args):
        raise AssertionError("Reminder cannot interrupt or enqueue through the human busy path")
    runner._hm_handle_running_session_message = forbidden
    assert await runner.handle() is None
    assert pending_count(db, ref) == (0 if stale else 1)
    assert runner.released == []  # No second slot was ever acquired.
    assert registry(db, row["schedule_id"])["state"] == ("pending" if stale else "done")


@pytest.mark.asyncio
async def test_runner_busy_delegate_preserves_the_ordinary_message_path(host_env, monkeypatch):
    h, _db, _ref, _adapter, source = host_env
    event = MessageEvent(text="ordinary user input", message_type=MessageType.TEXT, source=source)
    runner = native_runner(h, event, [], monkeypatch)
    runner._is_session_running = lambda _key: True
    calls = []
    async def ordinary(e, s, key):
        calls.append((e, s, key))
        return "original busy path"
    runner._hm_handle_running_session_message = ordinary
    assert await runner.handle() == "original busy path"
    assert calls == [(event, source, "peer")]


def install_native_cold_route(runner, monkeypatch):
    """Use the real Gateway route resolver; replace credential discovery, never capability."""
    from gateway.run import GatewayRunner
    monkeypatch.setattr("gateway.run._resolve_runtime_agent_kwargs", lambda: {
        "provider": "openai", "api_mode": "chat_completions", "base_url": "", "api_key": "test-placeholder"})
    runner._resolve_session_key_or_none = lambda source, key: key or "peer"
    runner._rehydrate_session_model_override = lambda _key: None
    runner._peek_session_state = lambda _key: None
    cold_state = SimpleNamespace(conversation=SimpleNamespace())
    runner._session_state = lambda _key: cold_state
    runner._sessions_map = lambda: {}
    runner._resolve_session_agent_runtime = lambda **kwargs: GatewayRunner._resolve_session_agent_runtime(runner, **kwargs)


@pytest.mark.asyncio
@pytest.mark.parametrize("invalid", [None, "window", "reserve", "idle_config"])
async def test_cold_restart_resolves_native_capability_before_scan_and_main_admission(host_env, monkeypatch, caplog, invalid):
    from secretary import noting_scope
    from secretary.noting_capability import _cold_capabilities
    h, db, ref, adapter, _source = host_env
    row = arm_due(db, ref)
    runner = h.make_runner()
    runner._agent_cache.clear()
    noting_scope._main_runtimes.pop(noting_scope._runtime_key(db, ref), None)
    _cold_capabilities.pop(noting_scope._runtime_key(db, ref), None)
    length = {"window": 63000, "reserve": 600000}.get(invalid, 196000)
    threshold = 0.5 if invalid == "reserve" else 0.85
    idle = 300 if invalid == "idle_config" else 0
    (h.home / "config.yaml").write_text(
        f"model:\n  default: test/reminder-runtime\n  provider: openai\n  context_length: {length}\n"
        f"compression:\n  threshold: {threshold}\n  threshold_tokens: null\n  idle_compact_after_seconds: {idle}\nnoting:\n  enabled: true\n")
    install_native_cold_route(runner, monkeypatch)
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **_kwargs: pytest.fail("cold scan created SDK client"))
    calls = []
    async def native_handle(event):
        adapter.events.append(event)
        event._gateway_accepted = True
        native_runner(h, event, calls, monkeypatch, runner=runner)
        assert await runner.handle() == "accepted"
    adapter.handle_message = native_handle
    dispatched = await host.scan_due_secretary_schedules(runner)
    await asyncio.gather(*getattr(runner, "_secretary_delivery_tasks", set()))
    if invalid:
        assert dispatched == 0 and adapter.events == [] and calls == []
        from secretary.noting_runtime import noting_trigger_gate
        assert noting_trigger_gate(db, ref)[0] is False
        current = registry(db, row["schedule_id"])
        assert current["state"] == "pending" and current["claim_token"] is None
        if invalid == "idle_config":
            assert "idle_compact_after_seconds" in caplog.text
    else:
        assert dispatched == 1 and len(adapter.events) == 1 and len(calls) == 1
        assert registry(db, row["schedule_id"])["state"] == "done"
        assert _cold_capabilities[noting_scope._runtime_key(db, ref)]["pair"] == (196000, 166600)


@pytest.mark.asyncio
async def test_native_runtime_resolution_failure_releases_only_its_claim_and_slot(host_env, monkeypatch):
    h, db, ref, _adapter, _source = host_env
    row = arm_due(db, ref)
    from secretary.schedules import claim_due
    claim = claim_due(db, row["schedule_id"], owner="old")
    event = claim_event(h, db, ref, claim)
    runner = native_runner(h, event, [], monkeypatch)
    def unavailable(**_kwargs):
        raise RuntimeError("owner runtime unavailable")
    runner._resolve_session_agent_runtime = unavailable
    with pytest.raises(RuntimeError, match="owner runtime"):
        await runner.handle()
    current = registry(db, row["schedule_id"])
    assert current["state"] == "pending" and current["claim_token"] is None
    assert current["next_run_at"] == claim["next_run_at"]
    assert runner.released == ["slot", "lease"]


@pytest.mark.asyncio
@pytest.mark.parametrize("refusal", [None, "native preparation refused"])
async def test_native_prepare_normal_return_before_execution_recovers_occurrence(host_env, monkeypatch, refusal):
    h, db, ref, _adapter, _source = host_env
    row = arm_due(db, ref)
    from secretary.schedules import claim_due
    claim = claim_due(db, row["schedule_id"], owner="old")
    event = claim_event(h, db, ref, claim)
    runner = native_runner(h, event, [], monkeypatch)
    async def refuse(*_args):
        return refusal
    runner._handle_message_with_agent = refuse
    assert await runner.handle() == refusal
    current = registry(db, row["schedule_id"])
    assert current["state"] == "pending" and current["claim_token"] is None
    assert current["next_run_at"] == claim["next_run_at"]
    assert runner.released == ["slot", "lease"]
