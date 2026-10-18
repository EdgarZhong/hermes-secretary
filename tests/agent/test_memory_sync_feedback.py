"""Optional sync observations use existing notices; no external model/provider traffic."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agent.context_compaction_request import enter_native_turn, leave_native_turn
from agent.memory_manager import MemoryManager
from agent.memory_provider import MemorySyncFeedback
from agent.memory_sync_feedback import capture_sync_feedback


class Provider:
    name = "fixture"

    def __init__(self, result):
        self.result = result
        self.calls = []

    def get_tool_schemas(self): return []
    def queue_prefetch(self, query, *, session_id=""): pass
    def on_session_end(self, messages): pass
    def shutdown(self): pass
    def prefetch(self, query, *, session_id=""): return ""
    def recall_status(self): return None
    def on_turn_start(self, number, query): pass

    def sync_turn(self, user, assistant, *, session_id=""):
        self.calls.append((user, assistant, session_id))
        return self.result


def manager_for(result):
    manager = MemoryManager()
    provider = Provider(result)
    manager.add_provider(provider)
    return manager, provider


@pytest.mark.parametrize("result", [None, True, {"status": "error"}, {"feedback": "unknown"}])
def test_legacy_returns_and_signatures_do_not_emit_or_gain_feedback_state(result):
    manager, provider = manager_for(result)
    callback = MagicMock(return_value=True)
    try:
        manager.sync_all("question", "answer", session_id="s", messages=[], feedback_callback=callback)
        assert manager.flush_pending(timeout=5)
        assert provider.calls == [("question", "answer", "s")]
        callback.assert_not_called()
        assert manager._sync_feedback_attempted == {}
        assert manager._sync_feedback_pending == {}
    finally:
        manager.shutdown_all()


def test_state_transitions_dedup_but_failed_attempt_can_retry():
    paused = MemorySyncFeedback("profile-and-conversation", "paused", "archive paused")
    manager, provider = manager_for({"feedback": paused})
    attempts = []

    def callback(feedback):
        attempts.append(feedback)
        if len(attempts) == 1:
            raise RuntimeError("driver unavailable")
        return len(attempts) != 2

    try:
        for _ in range(4):
            manager.sync_all("question", "answer", feedback_callback=callback)
            assert manager.flush_pending(timeout=5)
        assert len(attempts) == 3
        provider.result = {"feedback": MemorySyncFeedback(paused.scope, "compatible", "checked compatible")}
        manager.sync_all("question", "answer", feedback_callback=callback)
        assert manager.flush_pending(timeout=5)
        provider.result = {"feedback": paused}
        manager.sync_all("question", "answer", feedback_callback=callback)
        assert manager.flush_pending(timeout=5)
        assert [entry.state for entry in attempts] == ["paused", "paused", "paused", "compatible", "paused"]
    finally:
        manager.shutdown_all()


def test_captured_native_owner_cannot_emit_into_next_turn_callback_or_session():
    notices = []
    agent = SimpleNamespace(session_id="same", _memory_manager=object(), notice_callback=notices.append,
                            status_callback=None)
    token, _ = enter_native_turn(agent, None, [])
    captured = capture_sync_feedback(agent)
    feedback = MemorySyncFeedback("opaque", "paused", "archive paused")
    assert captured(feedback) is True
    assert notices[0].ttl_ms == 5000 and notices[0].kind == "ttl"
    leave_native_turn(agent, token)
    assert captured(feedback) is False
    new_notices = []
    agent.notice_callback = new_notices.append
    next_token, _ = enter_native_turn(agent, None, [])
    assert captured(feedback) is False
    current = capture_sync_feedback(agent)
    agent.session_id = "other-profile-same-stored-id"
    assert current(feedback) is False
    leave_native_turn(agent, next_token)
    assert len(notices) == 1 and new_notices == []


def test_status_fallback_and_error_notice_keep_existing_lifetime_semantics():
    statuses, notices = [], []
    agent = SimpleNamespace(session_id="s", _memory_manager=object(), notice_callback=None,
                            status_callback=lambda *args: statuses.append(args))
    token, _ = enter_native_turn(agent, None, [])
    feedback = MemorySyncFeedback("scope", "paused", "archive paused")
    assert capture_sync_feedback(agent)(feedback) is True
    assert statuses == [("warn", "archive paused")]
    agent.notice_callback = notices.append
    assert capture_sync_feedback(agent)(MemorySyncFeedback("scope", "error", "error", "error")) is True
    assert notices[0].kind == "sticky" and notices[0].ttl_ms is None
    agent._memory_provider_shutdown = True
    assert capture_sync_feedback(agent)(feedback) is False
    leave_native_turn(agent, token)


def test_pending_feedback_same_stored_id_never_replays_in_another_profile(tmp_path):
    from hermes_constants import reset_hermes_home_override, set_hermes_home_override
    manager, provider = manager_for({"feedback": MemorySyncFeedback("scope-A", "paused", "archive paused")})
    attempts = []
    try:
        for profile, result, callback in [
            ("A", provider.result, lambda feedback: False),
            ("B", None, lambda feedback: attempts.append("wrong profile") or True),
            ("A", None, lambda feedback: attempts.append(feedback.text) or True),
        ]:
            token = set_hermes_home_override(tmp_path / profile)
            try:
                provider.result = result
                manager.sync_all("question", "answer", session_id="same", feedback_callback=callback)
                assert manager.flush_pending(timeout=5)
            finally:
                reset_hermes_home_override(token)
        assert attempts == ["archive paused"]
        assert manager._sync_feedback_pending == {}
    finally:
        manager.shutdown_all()


@pytest.mark.parametrize("delivery", ["attempted", "pending"])
def test_identical_provider_scope_state_and_stored_id_are_profile_isolated(tmp_path, delivery):
    from hermes_constants import get_hermes_home, reset_hermes_home_override, set_hermes_home_override
    feedback = MemorySyncFeedback("identical-opaque-scope", "paused", "archive paused")
    manager, _ = manager_for({"feedback": feedback})
    attempts = []

    def submit(profile, accept):
        home = (tmp_path / profile).resolve()
        token = set_hermes_home_override(home)

        def callback(observation):
            assert get_hermes_home().resolve() == home
            if accept:
                attempts.append((profile, observation.text))
            return accept

        try:
            manager.sync_all("question", "answer", session_id="identical-stored-id", feedback_callback=callback)
            assert manager.flush_pending(timeout=5)
        finally:
            reset_hermes_home_override(token)

    try:
        submit("A", delivery == "attempted")
        submit("B", delivery == "attempted")
        if delivery == "pending":
            assert len(manager._sync_feedback_pending) == 2
            submit("A", True)
            assert len(manager._sync_feedback_pending) == 1
            submit("B", True)
        assert attempts == [("A", feedback.text), ("B", feedback.text)]
        assert len(manager._sync_feedback_attempted) == 2
        assert manager._sync_feedback_pending == {}
        submit("A", True)
        submit("B", True)
        assert len(attempts) == 2  # each profile deduplicates only its own observation
    finally:
        manager.shutdown_all()


def test_ordinary_native_main_has_real_token_and_existing_notification_event(tmp_path, monkeypatch):
    """Real AIAgent entry/admission/finalizer, controlled final model response only."""
    from hermes_state import SessionDB
    from run_agent import AIAgent
    import tui_gateway.agent_callbacks as callbacks

    monkeypatch.setattr("model_tools.get_tool_definitions", lambda **kw: [])
    monkeypatch.setattr("model_tools.check_toolset_requirements", lambda *a, **kw: {})
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **kw: MagicMock())
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **kw: {})
    monkeypatch.setattr("agent.context_compressor.get_model_context_length", lambda *a, **kw: 130000)
    monkeypatch.setattr("agent.title_generator.maybe_auto_title", lambda *a, **kw: None)
    monkeypatch.setattr("run_agent._hermes_home", tmp_path)
    events, tokens = [], []
    monkeypatch.setitem(callbacks._agent_notice_update.__globals__, "_agent_presentation_enabled", lambda *a, **kw: True)
    monkeypatch.setitem(callbacks._agent_notice_update.__globals__, "_emit", lambda *args: events.append(args))
    db = SessionDB(db_path=tmp_path / "state.db")
    db.create_session("ordinary", source="cli")
    agent = AIAgent(api_key="fixture-only", base_url="https://example.invalid/v1", model="test/model",
                    quiet_mode=True, skip_context_files=True, skip_memory=True, session_db=db, session_id="ordinary")
    manager, _ = manager_for({"feedback": MemorySyncFeedback("opaque-profile-conversation", "paused", "fixture paused")})
    agent._memory_manager = manager
    agent._cached_system_prompt = "Stable native root"
    agent._compression_feasibility_checked = True
    agent.context_compressor.threshold_tokens = 1000000
    agent.save_trajectories = False
    agent.notice_callback = lambda n: callbacks._agent_notice_update("runtime-owner", n)

    def response(request):
        tokens.append(agent._native_compaction_turn)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
            content="A completed native response.", tool_calls=None, reasoning_content=None, reasoning=None),
            finish_reason="stop")], model="test/model", usage=None)

    monkeypatch.setattr(agent, "_interruptible_api_call", response)
    monkeypatch.setattr(agent, "_interruptible_streaming_api_call", response)
    # Hold the finalizer at its existing sync seam while the worker returns.
    original_sync = agent._sync_external_memory_for_turn

    def sync(**kwargs):
        original_sync(**kwargs)
        assert manager.flush_pending(timeout=5)

    monkeypatch.setattr(agent, "_sync_external_memory_for_turn", sync)
    try:
        result = agent.run_conversation("A meaningful ordinary native question")
        assert result["completed"] is True and not result.get("failed")
        assert tokens and all(token is not None for token in tokens)
        assert agent._native_compaction_turn is None
        assert events == [("notification.show", "runtime-owner", {
            "text": "fixture paused", "level": "warn", "kind": "ttl", "ttl_ms": 5000,
            "key": "memory-sync.opaque-profile-conversation", "id": "memory-sync.opaque-profile-conversation"})]
        assert any(row["role"] == "assistant" for row in db.get_messages("ordinary"))
    finally:
        agent.close()
        db.close()
