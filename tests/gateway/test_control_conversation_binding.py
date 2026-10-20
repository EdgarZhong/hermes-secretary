import asyncio
import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from gateway.control_conversation_binding import ConversationBindingControl, conversation_binding_verb
from gateway.control_socket import GatewayControlServer
from gateway.conversation_binding import BINDING_KEY
from tests.gateway.test_conversation_binding import bound_store as bound_store


@pytest.fixture
def control(bound_store):
    store, db, source, key = bound_store
    runner = SimpleNamespace(session_store=store, _running_agents={},
                             _evict_cached_agent=Mock(), _clear_conversation_scope=Mock())
    service = ConversationBindingControl(runner)
    profile = key.split(":")[1]
    return service, runner, db, source, key, profile


def call(control, action, **params):
    service, _runner, _db, _source, _key, profile = control
    return service.execute({"profile": profile, "action": action, **params})


def test_bind_ref_is_durable_idempotent_and_hides_physical_locator(control):
    service, runner, db, source, key, profile = control
    ref = db.resolve_conversation_ref("imported")
    result = call(control, "bind", conversation_ref=ref)
    assert result["ok"] and result["changed"]
    assert result["binding"]["conversation"]["conversation_ref"] == ref
    saved = runner.session_store._routing_db_method("load_gateway_routing_entries")(
        scope=runner.session_store._routing_scope())
    assert json.loads(saved[key])["metadata"][BINDING_KEY]["conversation_ref"] == ref
    assert "session_id" not in json.dumps(result)
    repeated = call(control, "bind", conversation_ref=ref)
    assert repeated["ok"] and not repeated["changed"]
    runner._evict_cached_agent.assert_called_once_with(key)


def test_current_requires_actual_caller_and_never_uses_binding_or_recent_chat(control):
    ref = control[2].resolve_conversation_ref("imported")
    assert call(control, "bind", conversation_ref=ref)["ok"]
    for locator in (None, "missing"):
        result = call(control, "current", caller_locator=locator)
        assert not result["ok"] and result["error"]["code"] == "current_unavailable"
    current = call(control, "current", caller_locator="imported")
    assert current["conversation"]["conversation_ref"] == ref


def test_busy_route_refuses_move_but_allows_binding_same_current_conversation(control):
    service, runner, db, source, key, profile = control
    entry = runner.session_store._entries[key]
    entry.active_turn_token = "active"
    before = entry.session_id
    rejected = call(control, "bind", conversation_ref=db.resolve_conversation_ref("imported"))
    assert not rejected["ok"] and rejected["error"]["code"] == "route_busy"
    assert entry.session_id == before and BINDING_KEY not in entry.metadata
    result = call(control, "bind", caller_locator=before)
    assert result["ok"] and result["binding"]["bound"]
    assert not call(control, "unbind")["ok"]


def test_unbind_preserves_original_main_and_creates_independent_route(control):
    service, runner, db, source, key, profile = control
    original = db.resolve_conversation_ref("imported")
    assert call(control, "bind", conversation_ref=original)["ok"]
    result = call(control, "unbind")
    assert result["ok"] and not result["binding"]["bound"]
    entry = runner.session_store._entries[key]
    assert entry.session_id != "imported"
    assert db.get_session("imported")["end_reason"] is None
    assert db.resolve_conversation_ref(entry.session_id) != original
    assert not call(control, "unbind")["changed"]


def test_list_distinguishes_branch_and_binding_stays_original(control):
    db = control[2]
    original = db.resolve_conversation_ref("imported")
    assert call(control, "bind", conversation_ref=original)["ok"]
    db.create_session("branch", "desktop", parent_session_id="imported",
                      model_config={"_branched_from": "imported"})
    refs = [row["conversation_ref"] for row in call(control, "list")["conversations"]]
    assert original in refs and db.resolve_conversation_ref("branch") in refs
    assert call(control, "status")["binding"]["conversation"]["conversation_ref"] == original
    db.set_session_archived("branch", True)
    result = call(control, "bind", conversation_ref=db.resolve_conversation_ref("branch"))
    assert not result["ok"] and result["error"]["code"] == "conversation_unavailable"


def test_list_marks_caller_and_binding_as_independent_conversation_attributes(control):
    db = control[2]
    db.create_session("caller", "desktop", model="caller-model")
    db.set_session_title("caller", "Caller")
    original = db.resolve_conversation_ref("imported")
    caller = db.resolve_conversation_ref("caller")
    assert call(control, "bind", conversation_ref=original)["ok"]
    result = call(control, "list", caller_locator="caller")
    rows = {item["conversation_ref"]: item for item in result["conversations"]}
    assert rows[caller]["is_self"] is True and rows[caller]["is_current_binding"] is False
    assert rows[original]["is_self"] is False and rows[original]["is_current_binding"] is True
    assert rows[caller]["title"] == "Caller" and rows[caller]["model"] == "caller-model"
    assert rows[caller]["last_activity_at"] is not None
    assert result["caller_context"]["conversation_ref"] == caller
    assert "session_id" not in json.dumps(result)


def test_bind_caller_needs_one_operation_and_list_can_mark_both_roles(control):
    result = call(control, "bind", caller_locator="imported")
    assert result["ok"] and result["changed"]
    listing = call(control, "list", caller_locator="imported")
    matches = [row for row in listing["conversations"] if row["is_self"]]
    assert len(matches) == 1 and matches[0]["is_current_binding"] is True


@pytest.mark.parametrize("locator", [None, "other-profile-only"])
def test_list_without_resolvable_caller_reports_unknown_instead_of_guessing(control, locator):
    assert call(control, "bind", caller_locator="imported")["ok"]
    result = call(control, "list", caller_locator=locator)
    assert result["ok"] and result["conversations"]
    assert result["caller_context"]["available"] is False
    assert all(item["is_self"] is None for item in result["conversations"])
    assert sum(item["is_current_binding"] for item in result["conversations"]) == 1


def test_list_limit_keeps_identity_information_and_compression_is_one_conversation(control):
    db = control[2]
    ref = db.resolve_conversation_ref("imported")
    assert call(control, "bind", caller_locator="imported")["ok"]
    db.end_session("imported", "compression")
    db.create_session("tip", "pi-import", parent_session_id="imported", model="k3-256k")
    db.create_session("newest", "desktop")
    db._write_sql("UPDATE sessions SET last_activity_at=? WHERE id=?", (9999999999, "newest"))
    result = call(control, "list", caller_locator="imported", limit=1)
    assert len(result["conversations"]) == 1
    assert result["conversations"][0]["conversation_ref"] == db.resolve_conversation_ref("newest")
    assert result["caller_context"]["conversation_ref"] == ref
    assert result["binding"]["conversation"]["conversation_ref"] == ref
    all_rows = call(control, "list", caller_locator="imported")["conversations"]
    matches = [row for row in all_rows if row["conversation_ref"] == ref]
    assert len(matches) == 1 and matches[0]["is_self"] and matches[0]["is_current_binding"]


def test_invalid_ref_and_multiple_peers_do_not_guess(control):
    for ref in ("", "imported", "conv_short"):
        assert call(control, "bind", conversation_ref=ref)["error"]["code"] == "invalid_ref"
    runner, source = control[1], control[3]
    from dataclasses import replace
    runner.session_store.get_or_create_session(replace(source, chat_id="another-peer"))
    assert call(control, "status")["error"]["code"] == "peer_unavailable"


def test_explicitly_closed_conversation_is_rejected_without_repoint(control):
    service, runner, db, source, key, profile = control
    original = runner.session_store._entries[key].session_id
    ref = db.resolve_conversation_ref("imported")
    db.end_session("imported", "tui_close")
    result = call(control, "bind", conversation_ref=ref)
    assert result["error"]["code"] == "conversation_unavailable"
    assert runner.session_store._entries[key].session_id == original


def test_native_control_protocol_executes_on_gateway_loop(control):
    async def exercise():
        server = GatewayControlServer(verb_handlers={
            "conversation-binding": conversation_binding_verb(control[1], asyncio.get_running_loop())})
        params = {"profile": control[-1], "action": "bind", "conversation_ref": control[2].resolve_conversation_ref("imported")}
        response = await asyncio.to_thread(server.handle_request_line,
                                          json.dumps({"verb": "conversation-binding", "params": params}).encode())
        result = json.loads(response)
        assert result["ok"] and result["result"]["ok"] and result["result"]["changed"]
    asyncio.run(exercise())
