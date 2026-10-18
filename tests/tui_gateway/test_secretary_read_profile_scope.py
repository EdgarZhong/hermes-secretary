"""Secretary read RPCs retain the target profile runtime owner."""

import os

import pytest

from hermes_state import SessionDB


@pytest.mark.parametrize("schedule", ["every 2h", "0 10 * * *", "2030-10-18T10:00:00+08:00"])
def test_schedule_rpc_reports_target_profiles_timezone(tmp_path, monkeypatch, schedule):
    from tui_gateway import server
    from secretary.scheduler_table import apply_schedule_action_conn
    from hermes_constants import get_hermes_home, set_hermes_home_override, reset_hermes_home_override
    from hermes_time import reset_cache
    launch = tmp_path / "launch"; launch.mkdir()
    target = tmp_path / "target"; target.mkdir()
    (launch / "config.yaml").write_text("timezone: Asia/Tokyo\n")
    (target / "config.yaml").write_text("timezone: America/Los_Angeles\n")
    db = SessionDB(target / "state.db")
    db.create_session("s", source="cli")
    db.append_message("s", "user", "schedule please", message_uid="u1")
    ref = db.resolve_conversation_ref("s")
    db._execute_write(lambda conn: apply_schedule_action_conn(conn, ref, {"action":"create", "content":"check", "schedule":schedule, "delivery_mode":"instant"}, now=1792200000))
    monkeypatch.setattr(server, "_profile_home", lambda _: target)
    monkeypatch.delenv("HERMES_TIMEZONE", raising=False)
    token = set_hermes_home_override(str(launch)); reset_cache()
    before_env = dict(os.environ)
    try:
        result = server.handle_request({"jsonrpc":"2.0", "id":1, "method":"secretary.schedules", "params":{"profile":"target", "stored_session_id":"s"}})
        assert result["result"]["schedules"][0]["timezone"] == "America/Los_Angeles", result
        assert get_hermes_home() == launch
        assert dict(os.environ) == before_env
    finally:
        reset_hermes_home_override(token); reset_cache(); db.close()

