"""Formal JSON-RPC dispatch to native recovery and profile-owned persistence."""
from pathlib import Path

import pytest

from hermes_constants import get_hermes_home
from hermes_state import SessionDB
from secretary.noting_recovery import recovery_state
from tests.secretary.test_noting_recovery import failed_task, factory, wait_recovery
from tests.secretary.test_r3_child import (
    database as database, enabled_runtime as enabled_runtime, native_parent as native_parent,
    ref, response, tool_response,
)
from tui_gateway import server


def test_rpc_starts_target_profile_native_runner_and_state_query(native_parent, database, monkeypatch, tmp_path):
    parent, client = native_parent
    failed = failed_task(native_parent, database)
    launch = SessionDB(tmp_path / "launch" / "state.db")
    monkeypatch.setattr(server, "_get_db", lambda: launch)
    monkeypatch.setattr(server, "_profile_home", lambda name: database.db_path.parent if name == "target" else None)
    seen = []
    def make(sid, key, **kwargs):
        seen.append((Path(get_hermes_home()).resolve(), kwargs["session_db"].db_path.resolve(), key))
        return factory(parent)(kwargs["session_db"], None)
    monkeypatch.setattr(server, "_make_agent", make)
    client.chat.completions.create.side_effect = [tool_response("finish_noting", {"reason": "RPC recovered"}), response("Done")]
    params = {"profile": "target", "conversation_ref": ref(database),
              "failed_child_session_id": failed.child_session_id, "request_id": "r1"}
    try:
        ack = server.handle_request({"jsonrpc": "2.0", "id": "start", "method": "secretary.noting_recover", "params": params})
        assert "error" not in ack, ack
        state = wait_recovery(database, failed)
        assert state["committed"], state
        queried = server.handle_request({"jsonrpc": "2.0", "id": "state", "method": "secretary.noting_recovery_state", "params": params})
        assert queried["result"] == recovery_state(database, ref(database), failed.child_session_id, "r1")
        assert seen == [(database.db_path.parent.resolve(), database.db_path.resolve(), "parent")]
        assert launch.get_session(ack["result"]["child_session_id"]) is None
    finally:
        launch.close()


@pytest.mark.parametrize("change", [{"request_id": " "}, {"conversation_ref": ""}, {"failed_child_session_id": ""}, {"request_id": "x" * 129}])
def test_rpc_rejects_invalid_identity_before_dispatch(monkeypatch, change):
    params = {"conversation_ref": "conv", "failed_child_session_id": "failed", "request_id": "r1", **change}
    result = server.handle_request({"id": "bad", "method": "secretary.noting_recover", "params": params})
    assert result["error"]["code"] == 4002


def test_rpc_contract_rejects_unknown_field():
    result = server.handle_request({"id": "bad", "method": "secretary.noting_recover", "params": {
        "conversation_ref": "conv", "failed_child_session_id": "failed", "request_id": "r1", "force": True}})
    assert result["error"]["code"] == 4000
