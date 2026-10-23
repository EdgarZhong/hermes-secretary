"""K3 naming through native RPCs and the turn prologue, with real SDK/store wiring."""

import json
import threading
from types import SimpleNamespace

import httpx
import pytest

from agent import auxiliary_client as aux
from agent.title_generator import wait_for_title_upgrades
from agent.turn_context import _maybe_title_session_at_turn_start
from hermes_state import SessionDB
from tui_gateway import server


@pytest.fixture
def naming_runtime(tmp_path, monkeypatch):
    home = tmp_path / "profile"
    home.mkdir()
    (home / "config.yaml").write_text("model:\n  provider: kimi-coding\n  default: k3-256k\n")
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(server, "_hermes_home", home)
    requests = []
    reject = {"enabled": False}

    def respond(request):
        payload = json.loads(request.content)
        requests.append((request.url.path, payload))
        # Same rejection observed in production, without a remote request.
        if reject["enabled"] or payload.get("temperature", 1) != 1:
            return httpx.Response(400, json={"error": {
                "message": "invalid temperature: only 1 is allowed for this model",
                "type": "invalid_request_error",
            }})
        return httpx.Response(200, json={
            "id": "chatcmpl-title", "object": "chat.completion", "created": 1,
            "model": payload["model"], "choices": [{"index": 0, "finish_reason": "stop",
                "message": {"role": "assistant", "content": '{"title":"修复后台标题链路"}'}}],
        })

    def http_kwargs(_base_url, *, async_mode=False, **_kwargs):
        client = httpx.AsyncClient if async_mode else httpx.Client
        return {"http_client": client(transport=httpx.MockTransport(respond))}

    aux.shutdown_cached_clients()
    monkeypatch.setattr(aux, "_openai_http_client_kwargs", http_kwargs)
    db = SessionDB(home / "state.db")
    db.create_session("stored", source="web", model="k3-256k")
    db.set_session_title("stored", "原有标题")
    agent = SimpleNamespace(provider="kimi-coding", model="k3-256k",
                            base_url="https://api.kimi.com/coding/v1", api_key="offline-key",
                            api_mode="chat_completions", session_id="stored", _session_db=db,
                            _session_db_created=True, platform="web")
    session = {"agent": agent, "session_key": "stored", "profile_home": str(home),
               "history": [], "history_lock": threading.RLock(), "running": False}
    monkeypatch.setattr(server, "_sessions", {"runtime": session})
    frames = []
    monkeypatch.setattr(server, "_emit", lambda kind, sid, payload=None: frames.append((kind, sid, payload)))
    # Ancillary status reads are irrelevant; title is still read through the native session-info owner.
    monkeypatch.setattr(server, "_display_session_cwd", lambda _session: str(tmp_path))
    monkeypatch.setattr("hermes_cli.banner.get_available_skills", lambda: [])
    monkeypatch.setattr("hermes_cli.banner.get_update_result", lambda **_kwargs: None)
    yield SimpleNamespace(db=db, agent=agent, requests=requests, frames=frames, reject=reject)
    wait_for_title_upgrades()
    aux.shutdown_cached_clients()
    db.close()


def rpc(name, **params):
    return server.handle_request({"jsonrpc": "2.0", "id": name, "method": name,
                                  "params": {"session_id": "runtime", **params}})


@pytest.mark.parametrize("model", ["k3", "k3-256k", "moonshot/k3-256k"])
def test_ai_title_uses_real_oneshot_then_native_persistence_and_push(naming_runtime, model):
    runtime = naming_runtime
    runtime.agent.model = model
    generated = rpc("llm.oneshot", instructions="Return only a title", input="修复后台自动标题",
                    max_tokens=256, temperature=0.3)
    assert generated["result"]["text"] == '{"title":"修复后台标题链路"}'
    # Generating is stateless; the Web command applies its cleaned proposal with the native write.
    assert runtime.db.get_session_title("stored") == "原有标题"
    proposed = json.loads(generated["result"]["text"])["title"]
    applied = rpc("session.title", title=proposed)
    assert applied["result"] == {"pending": False, "title": "修复后台标题链路"}
    assert runtime.db.get_session_title("stored") == "修复后台标题链路"
    assert any(kind == "session.info" and sid == "runtime" and payload["title"] == "修复后台标题链路"
               for kind, sid, payload in runtime.frames)
    assert len(runtime.requests) == 1
    path, request = runtime.requests[0]
    assert path == "/coding/v1/chat/completions"
    assert request["model"] == model.rsplit("/", 1)[-1]
    assert "temperature" not in request


def test_failed_ai_title_preserves_existing_title(naming_runtime):
    runtime = naming_runtime
    runtime.reject["enabled"] = True
    generated = rpc("llm.oneshot", instructions="Return a title", input="修复标题", temperature=0.3)
    assert generated["error"]["code"] == 5030
    assert runtime.db.get_session_title("stored") == "原有标题"
    assert runtime.frames == []


def test_turn_prologue_auto_title_persists_and_notifies_after_model_upgrade(naming_runtime):
    runtime = naming_runtime
    runtime.db.create_session("new", source="web", model="k3-256k")
    runtime.agent.session_id = "new"
    titles = []
    runtime.agent._on_session_title = lambda title, source: titles.append((title, source))
    _maybe_title_session_at_turn_start(runtime.agent, [{"role": "user", "content": "修复后台自动标题"}])
    wait_for_title_upgrades()
    assert runtime.db.get_session_title("new") == "修复后台标题链路"
    assert runtime.db.get_session_title_source("new") == "llm"
    assert titles == [("修复后台自动标题", "derived"), ("修复后台标题链路", "llm")]
    assert len(runtime.requests) == 1
    assert "_reasoning_config" not in runtime.requests[0][1]
    assert runtime.requests[0][1]["thinking"] == {"type": "disabled"}
