"""Native new-Turn provenance survives persistence without changing provider bytes."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from agent.transcript_repair import transcript_row_snapshot
from hermes_state import SessionDB
from hermes_state_turn_terminal import persist_turn_source
from tests.secretary.test_noting_child import mock_response

pytest_plugins = ["tests.secretary.test_noting_child"]


@pytest.fixture
def native_turn(parent, db, stub_client, monkeypatch):
    parent._disable_streaming = True
    parent._api_max_retries = 1
    parent.client = SimpleNamespace()
    client = MagicMock()
    requests = []
    def create(**kwargs):
        requests.append(copy.deepcopy(kwargs))
        response = mock_response("native answer")
        response.choices[0].message.reasoning_content = "complete latest typed thought"
        return response
    client.chat.completions.create.side_effect = create
    monkeypatch.setattr(parent, "_create_request_openai_client", lambda *a, **k: client)
    monkeypatch.setattr(parent, "_close_request_openai_client", lambda *a, **k: None)
    yield parent, db, requests
    parent.close()


def run(agent, db, text="typed notification", **kwargs):
    return agent.run_conversation(text, conversation_history=db.get_messages_as_conversation(agent.session_id),
                                  persist_user_display_kind="process_complete",
                                  persist_user_display_metadata={"origin": "process", "keep": "native metadata"},
                                  title_user_message="", **kwargs)


def rest_page(db, monkeypatch, sid="S17"):
    monkeypatch.setattr("hermes_state.DEFAULT_DB_PATH", Path(db.db_path))
    from hermes_cli.web_routers.sessions import manage_router
    app = FastAPI()
    app.include_router(manage_router)
    with TestClient(app) as client:
        response = client.get(f"/api/sessions/{sid}/messages", params={"recovery_view": 1, "history_sync": 1})
        assert response.status_code == 200, response.text
        return response.json()


def test_real_typed_turn_persists_source_before_provider_and_survives_fresh_process(native_turn, monkeypatch):
    agent, db, requests = native_turn
    original = agent._create_request_openai_client
    def create(*args, **kwargs):
        users = [row for row in db.get_messages(agent.session_id) if row.get("display_kind") == "process_complete"]
        assert len(users) == 1
        source = users[0]["display_metadata"]["turn_source"]
        assert source["message_uid"] == users[0]["message_uid"] and source["turn_id"] == agent._current_turn_id
        return original(*args, **kwargs)
    monkeypatch.setattr(agent, "_create_request_openai_client", create)
    result = run(agent, db)
    assert result["completed"]
    latest = rest_page(db, monkeypatch)["sync"]["latest_thinking"]
    assert [row["reasoning"] for row in latest["rows"]] == ["complete latest typed thought"]
    assert latest["source"]["message_uid"] == db.get_messages(agent.session_id)[-2]["message_uid"]
    assert "turn_source" not in json.dumps(requests)
    script = '''import json,sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
import hermes_state
hermes_state.DEFAULT_DB_PATH=Path(sys.argv[1])
from hermes_cli.web_routers.sessions import manage_router
app=FastAPI();app.include_router(manage_router)
with TestClient(app) as client:
 print(json.dumps(client.get('/api/sessions/S17/messages',params={'recovery_view':1,'history_sync':1}).json()))
'''
    fresh = subprocess.run([sys.executable, "-c", script, str(db.db_path)], capture_output=True, text=True, check=True, timeout=20)
    cold = json.loads(fresh.stdout)["sync"]["latest_thinking"]
    assert cold["source"] == latest["source"]
    assert cold["rows"] == latest["rows"]


def test_fresh_flush_needs_no_extra_metadata_transaction(native_turn, monkeypatch):
    agent, db, _ = native_turn
    writer = MagicMock(wraps=persist_turn_source)
    monkeypatch.setattr("hermes_state_turn_terminal.persist_turn_source", writer)
    assert run(agent, db)["completed"]
    writer.assert_not_called()
    assert all("turn_source" not in (row.get("display_metadata") or {})
               for row in db.get_messages(agent.session_id) if row["message_uid"] in ("m1", "m2"))


def test_cli_prewritten_source_backfill_merges_metadata_without_rewriting_row(native_turn, monkeypatch):
    agent, db, _ = native_turn
    db.append_message(agent.session_id, "user", "prewritten CLI input", timestamp=1234,
                      display_metadata={"existing": "keep", "reactions": [{"emoji": "ok"}]})
    history = db.get_messages_as_conversation(agent.session_id, include_row_ids=True)
    staged = history.pop()
    before = dict(db._read_one("SELECT * FROM messages WHERE id=?", (staged["_row_id"],)))
    agent._pending_cli_user_message = staged
    writer = MagicMock(wraps=persist_turn_source)
    monkeypatch.setattr("hermes_state_turn_terminal.persist_turn_source", writer)
    result = agent.run_conversation("prewritten CLI input", conversation_history=history,
        persist_user_display_metadata={"stage_only": "merged"}, title_user_message="")
    assert result["completed"] and writer.call_count == 1
    after = dict(db._read_one("SELECT * FROM messages WHERE id=?", (before["id"],)))
    assert (after["role"], after["content"], after["timestamp"], after["message_uid"]) == (
        before["role"], before["content"], before["timestamp"], before["message_uid"])
    assert transcript_row_snapshot(before) == transcript_row_snapshot(after)
    metadata = db._decode_display_metadata(after["display_metadata"])
    assert metadata["existing"] == "keep" and metadata["reactions"] == [{"emoji": "ok"}]
    assert metadata["turn_source"] == {"message_uid": staged["message_uid"], "turn_id": result["turn_id"]}
    assert staged["display_metadata"]["stage_only"] == "merged"
    assert sum(row["message_uid"] == staged["message_uid"] for row in db.get_messages(agent.session_id)) == 1


def test_backfill_failure_is_display_only_and_does_not_abort_turn(native_turn, monkeypatch):
    agent, db, requests = native_turn
    db.append_message(agent.session_id, "user", "staged", display_metadata={"keep": True})
    history = db.get_messages_as_conversation(agent.session_id, include_row_ids=True)
    staged = history.pop()
    agent._pending_cli_user_message = staged
    monkeypatch.setattr("hermes_state_turn_terminal.persist_turn_source", MagicMock(side_effect=RuntimeError("writer unavailable")))
    result = agent.run_conversation("staged", conversation_history=history, title_user_message="")
    assert result["completed"] and requests
    assert db.get_messages(agent.session_id)[-1]["content"] == "native answer"


def test_marker_is_stripped_from_native_provider_wire_and_cached_prefix(native_turn, monkeypatch):
    agent, db, requests = native_turn
    assert run(agent, db, "first native turn")["completed"]
    first = copy.deepcopy(requests[-1])
    assert run(agent, db, "second native turn")["completed"]
    second = requests[-1]
    assert "turn_source" not in json.dumps(requests) and "display_metadata" not in json.dumps(requests)
    assert second["messages"][:len(first["messages"])] == first["messages"]
    from agent.turn_context import build_api_messages
    from agent.model_metadata import estimate_messages_tokens_rough
    messages = db.get_messages_as_conversation(agent.session_id)
    without = copy.deepcopy(messages)
    for row in without:
        if isinstance(row.get("display_metadata"), dict):
            row["display_metadata"].pop("turn_source", None)
    args = dict(current_turn_user_idx=None, ext_prefetch_cache="", plugin_user_context="", moa_config=None,
                active_system_prompt=agent._cached_system_prompt)
    assert build_api_messages(agent, messages, **args) == build_api_messages(agent, without, **args)
    assert estimate_messages_tokens_rough(messages) == estimate_messages_tokens_rough(without)


@pytest.mark.parametrize("mutation", ["none", "rewind", "compression", "representative"])
def test_marker_tracks_native_uid_through_history_operations(native_turn, monkeypatch, mutation):
    agent, db, _ = native_turn
    assert run(agent, db)["completed"]
    rows = db.get_messages(agent.session_id)
    source = rows[-2]
    if mutation == "rewind":
        db.rewind_to_message(agent.session_id, source["id"])
        assert rest_page(db, monkeypatch)["sync"]["latest_thinking"]["order"] == []
        return
    if mutation in ("compression", "representative"):
        db.archive_and_compact(agent.session_id, rows)
        if mutation == "representative":
            db.end_session(agent.session_id, end_reason="compression")
            db.create_session("continued", source="weixin", parent_session_id=agent.session_id)
            db.append_messages_batch("continued", rows)
    latest = rest_page(db, monkeypatch)["sync"]["latest_thinking"]
    assert latest["source"]["message_uid"] == source["message_uid"]
    assert [row["reasoning"] for row in latest["rows"]] == ["complete latest typed thought"]


def test_db_metadata_guard_preserves_owner_and_ordinary_append_compression_contract(native_turn):
    _agent, db, _ = native_turn
    db.append_message("S17", "user", "metadata source", display_metadata={"keep": True})
    source = db.get_messages("S17")[-1]
    marker = {"message_uid": source["message_uid"], "turn_id": "native-known-turn"}
    assert db.try_acquire_session_turn_lease("S17", "real-owner")
    assert db.try_acquire_compression_lock("S17", "compression-owner")
    from hermes_state_errors import SessionTurnLeaseLostError
    with pytest.raises(SessionTurnLeaseLostError):
        persist_turn_source(db, "S17", source["id"], marker, turn_lease_holder="old-owner")
    assert "turn_source" not in db.get_messages("S17")[-1]["display_metadata"]
    assert persist_turn_source(db, "S17", source["id"], marker, turn_lease_holder="real-owner")
    db.create_session("branch", source="desktop", parent_session_id="S17", model_config={"_branched_from": "S17"})
    db.append_messages_batch("branch", [source])
    assert not persist_turn_source(db, "branch", source["id"], marker)
    assert db.get_messages("branch")[0]["display_metadata"] == source["display_metadata"]
    db.release_session_turn_lease("S17", "real-owner")
    db.release_compression_lock("S17", "compression-owner")


def test_prewritten_cli_source_backfills_same_uid_after_early_in_place_compaction(native_turn, monkeypatch):
    agent, db, _ = native_turn
    db.append_message(agent.session_id, 'user', 'early staged input', display_metadata={'keep': 'original'})
    history = db.get_messages_as_conversation(agent.session_id, include_row_ids=True)
    staged = history.pop()
    old_row_id = staged['_row_id']
    agent._pending_cli_user_message = staged
    from agent import turn_context_compaction
    original = turn_context_compaction.run_turn_start_compaction
    def compact_then_continue(*args, **kwargs):
        db.archive_and_compact(agent.session_id, db.get_messages(agent.session_id))
        return original(*args, **kwargs)
    monkeypatch.setattr(turn_context_compaction, 'run_turn_start_compaction', compact_then_continue)
    result = agent.run_conversation('early staged input', conversation_history=history, title_user_message='')
    assert result['completed']
    source = next(row for row in db.get_messages(agent.session_id) if row['message_uid'] == staged['message_uid'])
    assert source['id'] != old_row_id and source['display_metadata']['keep'] == 'original'
    assert source['display_metadata']['turn_source']['turn_id'] == result['turn_id']
    assert source['content'] == 'early staged input'


def test_native_marker_copies_to_explicit_branch_without_relabeling_history(native_turn, monkeypatch):
    agent, db, _ = native_turn
    assert run(agent, db)['completed']
    history = db.get_messages(agent.session_id)
    source = history[-2]
    db.create_session('branch-copy', source='desktop', parent_session_id=agent.session_id,
                      model_config={'_branched_from': agent.session_id})
    db.append_messages_batch('branch-copy', history)
    latest = rest_page(db, monkeypatch, sid='branch-copy')['sync']['latest_thinking']
    assert latest['source']['session_id'] == 'branch-copy'
    assert latest['source']['message_uid'] == source['message_uid']
    assert [row['reasoning'] for row in latest['rows']] == ['complete latest typed thought']
