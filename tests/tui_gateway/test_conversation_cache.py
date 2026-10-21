"""The formal cache-clear RPC stays in its requested Profile and normal lease boundary."""

import os

import pytest

from hermes_state import SessionDB


@pytest.fixture
def rpc(tmp_path, monkeypatch):
    # The parent integration owns aggregate registration; exercise this module's
    # public register(server) against the real dispatcher before that integration.
    from tui_gateway.contracts import conversation_cache  # noqa: F401
    from tui_gateway import methods_conversation_cache, server
    methods_conversation_cache.register(server)
    homes = {name: tmp_path / name for name in ("launch", "target")}
    stores = {}
    for name, home in homes.items():
        home.mkdir()
        stores[name] = SessionDB(home / "state.db")
        stores[name].create_session("same-id", source="cli", system_prompt=f"{name} root")
        stores[name].append_message("same-id", "user", "history", message_uid=f"{name}-message")
        stores[name].update_session_tool_names("same-id", {"version": "build", "tools": [
            {"type": "function", "function": {"name": "scheduler", "description": "old"}}]})
    refs = {name: db.resolve_conversation_ref("same-id") for name, db in stores.items()}
    monkeypatch.setattr(server, "_profile_home", lambda name: homes[name])
    yield server, stores, refs
    for db in stores.values():
        db.close()


def _request(server, params):
    return server.handle_request({"jsonrpc": "2.0", "id": 19,
                                  "method": "conversation.context_cache_clear", "params": params})


def test_rpc_clears_only_requested_profile_and_is_idempotent(rpc):
    server, stores, refs = rpc
    before_env = dict(os.environ)
    params = {"profile": "target", "conversation_ref": refs["target"]}
    result = _request(server, params)
    assert result["result"] == {**params, "stored_session_id": "same-id", "status": "cleared"}
    assert stores["target"].get_session("same-id")["system_prompt"] is None
    assert stores["target"].get_session("same-id")["tool_names"] is None
    assert stores["launch"].get_session("same-id")["system_prompt"] == "launch root"
    assert stores["launch"].get_session("same-id")["tool_names"] is not None
    assert _request(server, params)["result"]["status"] == "already_clear"
    assert dict(os.environ) == before_env


def test_rpc_rejects_active_native_turn_without_clearing(rpc):
    server, stores, refs = rpc
    db = stores["target"]
    assert db.try_acquire_session_turn_lease("same-id", "native-owner")
    try:
        result = _request(server, {"profile": "target", "conversation_ref": refs["target"]})
        assert result["error"]["code"] == 4010
        assert db.get_session("same-id")["system_prompt"] == "target root"
        assert db.get_session("same-id")["tool_names"] is not None
    finally:
        db.release_session_turn_lease("same-id", "native-owner")


@pytest.mark.parametrize("params, code", [
    ({"profile": "target", "conversation_ref": "missing"}, 4001),
    ({"profile": "target", "conversation_ref": ""}, 4000),
    ({"profile": "", "conversation_ref": "missing"}, 4000),
    ({"profile": "target", "conversation_ref": "missing", "rebuild": True}, 4000),
])
def test_rpc_unknown_or_invalid_input_is_bounded(rpc, params, code):
    server, stores, _refs = rpc
    assert _request(server, params)["error"]["code"] == code
    assert stores["target"].get_session("same-id")["system_prompt"] == "target root"
