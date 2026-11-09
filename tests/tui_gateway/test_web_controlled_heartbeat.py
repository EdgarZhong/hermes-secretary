"""V4 real pre-dispatch guard + native Pending handoff, with only provider output controlled."""
import json
import threading
import time

from hermes_cli.heartbeat import HeartbeatState, save_heartbeat
from secretary import adaptive_runtime, adaptive_store
from tests.agent.test_run_agent import _mock_response
from tests.secretary.test_adaptive_runtime import adaptive_config
from tests.tui_gateway.test_pending_native_turn import live as live
from tests.tui_gateway.test_web_controlled_input import send, receipt, settle_all
from tui_gateway import server


def test_cold_first_heartbeat_guard_keeps_accepted_human_for_real_user_followup(live, monkeypatch):
    parent, db = live.agent, live.db
    monkeypatch.setattr("model_tools.get_tool_definitions", lambda **kwargs: parent.tools)
    monkeypatch.setattr("model_tools.check_toolset_requirements", lambda *a, **k: {})
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **k: {})
    ref = db.resolve_conversation_ref(parent.session_id)
    config = adaptive_config(ref)
    config["model"].update(default="test/model", base_url="http://invalid.local/v1", context_length=256000)
    models = config["noting"]["adaptive_idle_token_saving"]["models"]["openai"]
    models["test/model"] = models.pop("test/runtime")
    config["noting"]["idle"]["enabled"] = False
    (live.home / "config.yaml").write_text(json.dumps(config))
    parent.provider = "openai"
    parent.requested_provider = "openai"
    parent.context_compressor.context_length = 256000
    parent.context_compressor.threshold_tokens = 200000
    db.patch_session_model_config(parent.session_id, {"provider": "openai", "api_mode": "chat_completions", "base_url": parent.base_url})
    calls = []
    warm_request = threading.Event()

    def provider(**kwargs):
        calls.append((parent._adaptive_turn_source, kwargs))
        warm_request.set()
        response = _mock_response(content="finished", finish_reason="stop")
        from types import SimpleNamespace
        response.usage = SimpleNamespace(prompt_tokens=100, completion_tokens=2, total_tokens=102,
                                         prompt_tokens_details=SimpleNamespace(cached_tokens=80))
        return response

    parent.client.chat.completions.create.side_effect = provider
    assert send("warm", "initial actual user request")["result"]["receipt"]["accepted"]
    assert warm_request.wait(5)
    settle_all(live)
    assert [source for source, _ in calls] == ["user"]
    now = time.time()
    save_heartbeat("stored", HeartbeatState("", 60, created_at=now - 180, last_fired_at=now - 120), db=db)
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    original = adaptive_runtime.request_started
    guarded = []

    def dispatch(parent):
        if parent._adaptive_turn_source == "heartbeat":
            entered.set()
            assert release.wait(15)
        result = original(parent)
        if parent._adaptive_turn_source == "heartbeat":
            guarded.append(result)
        return result

    monkeypatch.setattr(adaptive_runtime, "request_started", dispatch)
    with server._session_profile_runtime_scope(live.session):
        server._maybe_fire_tui_heartbeat_tick("runtime", live.session)
    assert entered.wait(10)
    accepted = send("human-during-heartbeat", "real human input accepted before HB request")["result"]["receipt"]
    assert accepted["state"] == "pending"
    parent.reasoning_config = {"effort": "changed-after-HB-admission"}
    db.patch_session_model_config(parent.session_id, {"reasoning_config": parent.reasoning_config})
    release.set()
    settle_all(live)
    assert guarded == [False]
    assert [source for source, _ in calls] == ["user", "user"]
    assert receipt("human-during-heartbeat")["state"] == "consumed"
    events = adaptive_store.history(db, ref, time.time())
    arrivals = [item for item in events if item["kind"] == "user_activity" and item["event_id"] == "web:human-during-heartbeat"]
    assert len(arrivals) == 1
    assert not [item for item in events if item["kind"] == "blocked_send"]
    assert not [item for item in events if item["kind"] == "request_start" and item.get("source") == "heartbeat"]
