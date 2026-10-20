"""Cold Context is available in the first resume receipt and survives agent binding."""

import threading
from concurrent.futures import ThreadPoolExecutor
from types import SimpleNamespace

import pytest

from agent.usage_anchor import capture_usage_anchor, persist_usage_anchor
from hermes_state import SessionDB
from tui_gateway import server


@pytest.fixture
def saved_context(tmp_path, monkeypatch):
    home = tmp_path / "profile"
    home.mkdir()
    (home / "config.yaml").write_text(
        "model:\n  default: model-a\n  context_length: 100000\n", encoding="utf-8")
    db = SessionDB(home / "state.db")
    db.create_session("stored", source="desktop", model="model-a")
    db.append_message("stored", "user", "priced question")
    history = db.get_messages_as_conversation("stored")
    persist_usage_anchor(SimpleNamespace(session_id="stored", _session_db=db),
                         capture_usage_anchor(9000, 20, history, model="model-a"))
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(server, "_hermes_home", str(home))
    monkeypatch.setattr(server, "_get_db", lambda: db)
    monkeypatch.setattr(server, "_profile_home", lambda profile: home)
    monkeypatch.setattr(server, "_profile_configured_cwd", lambda home: str(tmp_path))
    monkeypatch.setattr(server, "_default_session_cwd", lambda: str(tmp_path))
    monkeypatch.setattr(server, "_enable_gateway_prompts", lambda: None)
    monkeypatch.setattr(server, "_schedule_session_cap_enforcement", lambda: None)
    monkeypatch.setattr(server, "_schedule_resume_hydration", lambda *args, **kwargs: None)
    before = set(server._sessions)
    try:
        yield home, history
    finally:
        for sid in set(server._sessions) - before:
            server._sessions.pop(sid, None)
        db.close()


def test_deferred_resume_first_receipt_restores_context_without_history_or_agent(saved_context):
    response = server.handle_request({"id": "resume", "method": "session.resume", "params": {
        "session_id": "stored", "profile": "round3", "defer_history": True,
        "omit_messages": True,
    }})
    assert "error" not in response, response
    result = response["result"]
    record = server._sessions[result["session_id"]]
    assert record["history"] == [] and record["agent"] is None
    assert result["info"]["usage"]["context_used"] == 9020
    assert result["info"]["usage"]["context_estimated"] is True


def test_bound_agent_without_a_new_reading_retains_saved_context(saved_context):
    home, history = saved_context
    agent = SimpleNamespace(model="model-a", context_compressor=SimpleNamespace(
        context_length=100000, last_prompt_tokens=0))
    usage = server._session_usage_snapshot({"agent": agent, "history": history,
        "session_key": "stored", "profile_home": str(home)})
    assert usage["context_used"] == 9020
    assert usage["context_estimated"] is True


def test_bound_agent_new_native_reading_supersedes_cold_estimate(saved_context):
    home, history = saved_context
    agent = SimpleNamespace(model="model-a", context_compressor=SimpleNamespace(
        context_length=100000, last_prompt_tokens=12000, last_real_prompt_tokens=12000))
    usage = server._session_usage_snapshot({"agent": agent, "history": history,
        "session_key": "stored", "profile_home": str(home)})
    assert usage["context_used"] == 12000
    assert usage["context_source"] == "provider_usage"


def test_cold_k3_uses_its_native_window_after_profile_switch_to_deepseek(saved_context):
    home, history = saved_context
    db = server._get_db()
    db.patch_session_model_config("stored", {
        "model": "k3-256k", "provider": "kimi-coding", "base_url": "https://api.kimi.com/coding"})
    persist_usage_anchor(SimpleNamespace(session_id="stored", _session_db=db),
                         capture_usage_anchor(9000, 20, history, model="k3-256k"))
    (home / "config.yaml").write_text(
        "model:\n  default: deepseek-flash\n  provider: deepseek\n  context_length: 500000\n")
    session = {"agent": None, "history": [], "session_key": "stored", "profile_home": str(home),
               "model_override": {"model": "k3-256k", "provider": "kimi-coding"}}
    cold = server._session_usage_snapshot(session)
    assert cold["context_used"] == 9020
    assert cold["context_max"] == 262144
    assert cold["context_percent"] == 3
    session["agent"] = SimpleNamespace(model="k3-256k", provider="kimi-coding",
        context_compressor=SimpleNamespace(context_length=262144, last_prompt_tokens=0))
    assert server._session_usage_snapshot(session)["context_max"] == 262144
    from agent.model_metadata import get_model_context_length, save_context_length
    save_context_length("k3-256k", "https://api.kimi.com/coding", 256000)
    assert get_model_context_length("k3-256k", base_url="https://api.kimi.com/coding",
                                    provider="kimi-coding") == 262144


def test_native_breakdown_read_keeps_its_estimate_for_next_cold_binding(saved_context, monkeypatch):
    home, history = saved_context
    db = server._get_db()
    agent = SimpleNamespace(model="model-a", session_id="stored", _session_db=db)
    session = {"agent": agent, "history": history, "history_lock": threading.RLock(),
               "session_key": "stored", "profile_home": str(home)}
    server._sessions["context-read"] = session
    payload = {"categories": [], "context_used": 42771, "context_max": 100000,
               "context_percent": 43, "estimated_total": 42771, "context_estimated": True,
               "context_source": "local_estimate", "model": "model-a"}
    monkeypatch.setattr("agent.context_breakdown.compute_session_context_breakdown", lambda *_: payload)
    monkeypatch.setattr("agent.context_file_sources.context_file_sources_for_agent", lambda *_: [])

    response = server.handle_request({"id": "read", "method": "session.context_breakdown",
                                    "params": {"session_id": "context-read"}})

    assert "error" not in response, response
    assert response["result"]["context_used"] == 42771
    from agent.usage_anchor import set_usage_anchor
    set_usage_anchor(agent, None)
    restored = server._session_usage_snapshot({"agent": None, "history": [],
        "session_key": "stored", "profile_home": str(home)})
    assert restored["context_used"] == 42771


def test_rewind_cannot_stamp_an_inflight_old_estimate_with_its_new_generation(saved_context, monkeypatch):
    home, history = saved_context
    db = server._get_db()
    db.patch_session_model_config("stored", {"_usage_anchor": None, "_usage_context": None})
    agent = SimpleNamespace(model="model-a", session_id="stored", _session_db=db)
    session = {"agent": agent, "history": history, "history_lock": threading.RLock(),
               "session_key": "stored", "profile_home": str(home)}
    server._sessions["context-read"] = session
    entered, release = threading.Event(), threading.Event()

    def compute(*_):
        entered.set()
        assert release.wait(5)
        return {"categories": [], "context_used": 42771, "context_max": 100000,
                "context_percent": 43, "estimated_total": 42771, "context_estimated": True,
                "context_source": "local_estimate", "model": "model-a"}

    monkeypatch.setattr("agent.context_breakdown.compute_session_context_breakdown", compute)
    monkeypatch.setattr("agent.context_file_sources.context_file_sources_for_agent", lambda *_: [])
    with ThreadPoolExecutor(max_workers=1) as pool:
        reading = pool.submit(server.handle_request, {"id": "read", "method": "session.context_breakdown",
                              "params": {"session_id": "context-read"}})
        try:
            assert entered.wait(5)
            raced = session["history_lock"].acquire(blocking=False)
            if raced:
                try:
                    db.rewind_user_turn("stored", 0)
                finally:
                    session["history_lock"].release()
        finally:
            release.set()
        assert "error" not in reading.result(timeout=5)
    if not raced:
        with session["history_lock"]:
            db.rewind_user_turn("stored", 0)
    restored = server._session_usage_snapshot({"agent": None, "history": [],
        "session_key": "stored", "profile_home": str(home)})
    assert restored == {"context_invalidated": True, "context_invalidation_reason": "rewind"}
