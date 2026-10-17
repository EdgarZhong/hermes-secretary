from pathlib import Path
from types import SimpleNamespace
from agent.usage_anchor import capture_usage_anchor
from hermes_state import SessionDB


def test_cold_context_uses_owning_profile_database(tmp_path, monkeypatch):
    from tui_gateway import server
    messages = [{"role": "user", "content": "same text"}]
    databases = []
    for name, tokens in [("launch", 1000), ("foreign", 9000)]:
        home = tmp_path / name
        home.mkdir()
        (home / "config.yaml").write_text("model:\n  context_length: 100000\n")
        db = SessionDB(home / "state.db")
        db.create_session("same-id", source="cli")
        db.patch_session_model_config("same-id", {"model":"model-a", "_usage_anchor":capture_usage_anchor(tokens, 20, messages, model="model-a")})
        databases.append(db)
    monkeypatch.setattr(server, "_get_db", lambda: databases[0])
    monkeypatch.setattr(server, "_configured_context_length", lambda: 100000)
    try:
        session = {"agent":None, "history":messages, "session_key":"same-id", "profile_home":str(tmp_path / "foreign")}
        result = server._session_usage_snapshot(session)
        assert result["context_used"] == 9020, result
    finally:
        for db in databases: db.close()


def test_cold_context_does_not_claim_estimated_delta_is_provider_measurement(monkeypatch):
    from tui_gateway import server
    priced = [{"role":"user", "content":"hello"}]
    anchor = capture_usage_anchor(1000, 20, priced, model="model-a")
    db = SimpleNamespace(get_session_model_config_value=lambda sid, key, default=None: anchor if key == "_usage_anchor" else "model-a")
    monkeypatch.setattr(server, "_get_db", lambda: db)
    monkeypatch.setattr(server, "_configured_context_length", lambda: 100000)
    history = priced + [{"role":"assistant", "content":"answer"}, {"role":"user", "content":"unpriced " * 500}]
    result = server._session_usage_snapshot({"agent":None, "session_key":"s", "history":history})
    assert result["context_used"] == 1020, result


def test_schedule_rpc_reports_target_profiles_timezone(tmp_path, monkeypatch):
    from tui_gateway import server
    from secretary.scheduler_table import apply_schedule_action_conn
    from hermes_constants import set_hermes_home_override, reset_hermes_home_override
    from hermes_time import reset_cache
    launch = tmp_path / "launch"; launch.mkdir()
    target = tmp_path / "target"; target.mkdir()
    (launch / "config.yaml").write_text("timezone: Asia/Tokyo\n")
    (target / "config.yaml").write_text("timezone: America/Los_Angeles\n")
    db = SessionDB(target / "state.db")
    db.create_session("s", source="cli")
    db.append_message("s", "user", "schedule please", message_uid="u1")
    ref = db.resolve_conversation_ref("s")
    db._execute_write(lambda conn: apply_schedule_action_conn(conn, ref, {"action":"create", "content":"check", "schedule":"every 2h", "delivery_mode":"instant"}, now=1792200000))
    monkeypatch.setattr(server, "_profile_home", lambda _: target)
    monkeypatch.delenv("HERMES_TIMEZONE", raising=False)
    token = set_hermes_home_override(str(launch)); reset_cache()
    try:
        result = server.handle_request({"jsonrpc":"2.0", "id":1, "method":"secretary.schedules", "params":{"profile":"target", "stored_session_id":"s"}})
        assert result["result"]["schedules"][0]["timezone"] == "America/Los_Angeles", result
    finally:
        reset_hermes_home_override(token); reset_cache(); db.close()


def test_cold_context_honors_current_session_model_override(monkeypatch):
    from tui_gateway import server
    history = [{"role":"user", "content":"hello"}]
    anchor = capture_usage_anchor(1000, 20, history, model="model-a")
    db = SimpleNamespace(get_session_model_config_value=lambda sid, key, default=None: anchor if key == "_usage_anchor" else "model-a")
    monkeypatch.setattr(server, "_get_db", lambda: db)
    monkeypatch.setattr(server, "_configured_context_length", lambda: 100000)
    session = {"agent":None, "session_key":"s", "history":history, "model_override":{"model":"model-b","provider":"custom"}}
    assert server._live_session_identity(session)[0] == "model-b"
    assert server._session_usage_snapshot(session) == {}
