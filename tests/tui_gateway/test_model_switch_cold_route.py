"""A Web model switch survives cold resume on its actual provider and usage owner."""

import json
from types import SimpleNamespace

from agent.usage_anchor import capture_usage_anchor, set_usage_anchor
from hermes_cli.cli_model_switch_mixin import stored_session_route
from hermes_state import SessionDB
from tui_gateway import server


def test_web_switch_replaces_gateway_route_and_restores_cold_context(tmp_path, monkeypatch):
    home = tmp_path / "alex"
    home.mkdir()
    (home / "config.yaml").write_text(
        "model:\n  default: deepseek-flash\n  provider: deepseek\n  context_length: 1000000\n")
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(server, "_hermes_home", str(home))
    with SessionDB(home / "state.db") as db:
        monkeypatch.setattr(server, "_get_db", lambda: db)
        db.create_session("stored", "desktop", model="k3-256k", model_config={
            "model": "k3-256k", "provider": "kimi-coding", "_branched_from": "parent",
            "gateway_runtime": {"provider": "kimi-coding", "base_url": "https://api.kimi.com/coding/v1",
                                "api_mode": "chat_completions", "fallback_active": True}})
        db.append_message("stored", "user", "An existing conversation")
        history = db.get_messages_as_conversation("stored")
        agent = SimpleNamespace(model="deepseek-flash", provider="deepseek",
                                base_url="https://api.deepseek.com/v1", api_mode="chat_completions",
                                reasoning_config={"effort": "high"}, service_tier=None,
                                session_id="stored", _session_db=db)
        set_usage_anchor(agent, capture_usage_anchor(142118, 512, history, model=agent.model))
        before = db.get_messages("stored")
        server._persist_live_session_runtime({"agent": agent, "session_key": "stored"})
        row = db.get_session("stored")
        saved = json.loads(row["model_config"])
        expected = {"model": "deepseek-flash", "provider": "deepseek",
                    "base_url": "https://api.deepseek.com/v1", "api_mode": "chat_completions"}
        overrides = server._stored_session_runtime_overrides(row)
        assert overrides["model_override"] == expected
        assert "gateway_runtime" not in saved
        assert db.session_gateway_runtime(row) == {key: expected[key] for key in ("provider", "base_url", "api_mode")}
        assert saved["_branched_from"] == "parent" and saved["_usage_context"]["tokens"] == 142630
        assert stored_session_route(row, current_model="k3-256k", current_provider="kimi-coding")[:4] == (
            "deepseek-flash", "deepseek", "https://api.deepseek.com/v1", "chat_completions")
        session = {"agent": None, "history": None, "session_key": "stored",
                   "stored_session_id": "stored", "profile_home": str(home), **overrides}
        context = server._cold_context_breakdown(session)
        assert context["model"] == "deepseek-flash" and context["context_available"] is True
        assert context["context_used"] == 142630 and context["context_max"] == 1000000
        assert context["context_percent"] == 14
        assert db.get_messages("stored") == before
