"""Existing canonical gateway router rewrites the original Turn prompt under its profile."""

from types import SimpleNamespace

import pytest

from gateway.config import GatewayConfig, Platform
from gateway.platforms.event import MessageEvent, MessageType
from gateway.run import GatewayRunner
from gateway.session import SessionSource, SessionStore
from hermes_state import SessionDB
from secretary.notebook_store import NotebookStore


@pytest.fixture
def routed(tmp_path):
    home = tmp_path / "routed"
    home.mkdir()
    (home / "config.yaml").write_text("noting:\n  enabled: true\n")
    db = SessionDB(home / "state.db")
    db.create_session("gateway-main", source="telegram")
    db.append_message("gateway-main", "user", "Always preserve original evidence.", message_uid="source")
    ref = db.resolve_conversation_ref("gateway-main")
    state = NotebookStore(db, ref)
    state.create("rule_candidate", {"draft_rule": "Preserve evidence", "reason": "Auditability", "scope": "project"},
                 source_message_identities=[{"conversation_ref": ref, "message_uid": "source"}])
    db.notebook_commit_snapshot(ref, state.show(), anchor_message_uid="source")
    runner = GatewayRunner.__new__(GatewayRunner)
    runner.config = GatewayConfig(multiplex_profiles=True)
    runner._resolve_profile_home_for_source = lambda _: home
    runner._session_db = SimpleNamespace(_db=db)
    async def get_session(*args, **kwargs):
        return SimpleNamespace(session_id="gateway-main")
    async def executor(fn):
        return fn()
    runner.session_store = SessionStore(home / "sessions", runner.config)
    runner.session_store._db = db
    async def append(session_id, message):
        runner.session_store.append_to_transcript(session_id, message)
    runner._async_session_store = SimpleNamespace(_store=runner.session_store, get_or_create_session=get_session, append_to_transcript=append)
    runner._run_in_executor_with_context = executor
    source = SessionSource(platform=Platform.TELEGRAM, user_id="u", user_name="u", chat_id="c", chat_type="dm", profile="beta")
    try:
        yield runner, source, home, db, ref
    finally:
        db.close()


def event(source, text):
    return MessageEvent(text=text, source=source, message_type=MessageType.TEXT, message_id="request")


@pytest.mark.asyncio
async def test_canonical_prompt_keeps_original_identity_and_tail(routed):
    runner, source, _, db, ref = routed
    request = event(source, "/noting off")
    handled, output = await runner._hm_dispatch_canonical_command(request, source, "key", "noting")
    assert handled and "is off" in output
    durable = db.get_messages_as_conversation("gateway-main")
    assert durable[-1]["content"] == output
    assert durable[-2]["content"].endswith("/noting off")
    assert runner.session_store.load_transcript("gateway-main")[-1]["content"] == output
    request = event(source, "/propose-persistence Retain My Natural text 提议")
    handled, output = await runner._hm_dispatch_canonical_command(request, source, "key", "propose-persistence")
    assert not handled and output is None
    assert request.text.endswith("Retain My Natural text 提议")
    assert "Always preserve original evidence." not in request.text
    assert request.source is source and request.message_id == "request"
    assert not db.notebook_local_enabled(ref)


@pytest.mark.asyncio
async def test_global_off_returns_unavailable_without_turn_rewrite(routed):
    runner, source, home, _, _ = routed
    (home / "config.yaml").write_text("noting:\n  enabled: false\n")
    request = event(source, "/propose-persistence tail")
    handled, output = await runner._hm_dispatch_canonical_command(request, source, "key", "propose-persistence")
    assert handled and "unavailable" in output
    assert request.text == "/propose-persistence tail"


@pytest.mark.asyncio
async def test_existing_plan_learn_and_review_routes_remain_canonical(routed):
    runner, source, *_ = routed
    calls = []
    async def rewrite(request, source, name, ack, builder):
        calls.append(name)
        request.text = builder()
        return False, None
    runner._hm_rewrite_turn_to_prompt = rewrite
    for name in ("plan", "learn"):
        request = event(source, f"/{name} My TASK")
        assert await runner._hm_dispatch_canonical_command(request, source, "key", name) == (False, None)
        assert "My TASK" in request.text
    assert calls == ["plan", "learn"]
    async def review(request):
        calls.append("review")
        return "independent review"
    runner._handle_review_command = review
    assert await runner._hm_dispatch_canonical_command(event(source, "/review"), source, "key", "review") == (True, "independent review")
    assert not hasattr(runner, "_handle_refine_command")


@pytest.mark.asyncio
async def test_feedback_stays_with_command_conversation_if_route_moves(routed):
    runner, source, _, db, ref = routed
    db.create_session("new-main", source="telegram")
    new_ref = db.resolve_conversation_ref("new-main")
    calls = []
    async def moving_route(*args, **kwargs):
        calls.append(True)
        return SimpleNamespace(session_id="gateway-main" if len(calls) == 1 else "new-main")
    runner._async_session_store.get_or_create_session = moving_route
    handled, output = await runner._hm_dispatch_canonical_command(event(source, "/noting off"), source, "key", "noting")
    assert handled and "is off" in output
    assert not db.notebook_local_enabled(ref)
    assert db.notebook_local_enabled(new_ref)
    assert db.get_messages_as_conversation("gateway-main")[-1]["content"] == output
    assert db.get_messages_as_conversation("new-main") == []
