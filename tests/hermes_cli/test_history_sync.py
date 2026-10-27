"""Opt-in history sync through formal REST and real SQLite facts."""
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

import pytest

from hermes_state import SessionDB
import hermes_state_history_sync as history_sync
pytest_plugins = ["tests.hermes_cli.test_recovery_view"]


def page(client, *, cursor=None, sid="recovery", **query):
    params = {"recovery_view": 1, "history_sync": 1, **query}
    if cursor is not None:
        params["sync_cursor"] = cursor
    response = client.get(f"/api/sessions/{sid}/messages", params=params)
    assert response.status_code == 200, response.text
    return response.json()


def seed(db, count=3):
    db.append_messages_batch("recovery", [{"role": "user", "content": "opening", "timestamp": 1}, *[
        {"role": "assistant", "content": f"answer-{i}", "timestamp": i + 2,
         "reasoning": f"complete thought-{i}"} for i in range(count)]])


def test_snapshot_no_change_append_delete_and_authoritative_order(store):
    db, client, _ = store
    seed(db)
    first = page(client)
    assert first["sync"]["mode"] == "snapshot"
    assert first["sync"]["order"] == [row["id"] for row in first["messages"]]
    unchanged = page(client, cursor=first["sync"]["cursor"])
    assert unchanged["messages"] == [] and unchanged["sync"]["mode"] == "delta"
    assert unchanged["sync"]["latest_thinking"]["rows"] == []
    assert unchanged["pagination"]["returned"] == 4
    db.append_message("recovery", "assistant", "external channel append", reasoning="new thought")
    changed = page(client, cursor=unchanged["sync"]["cursor"])
    assert [row["content"] for row in changed["messages"]] == ["external channel append"]
    removed = first["messages"][1]["id"]
    db._write_sql("DELETE FROM messages WHERE id=?", (removed,))
    deleted = page(client, cursor=changed["sync"]["cursor"])
    assert deleted["messages"] == []
    assert removed not in deleted["sync"]["order"]
    assert removed not in deleted["sync"]["latest_thinking"]["order"]


@pytest.mark.parametrize("cursor", [None, "", "unrecognized", "lost-process-cursor"])
def test_empty_unknown_cursor_is_bounded_snapshot(store, cursor):
    db, client, _ = store
    seed(db, 8)
    result = page(client, cursor=cursor, limit=2)
    assert result["sync"]["mode"] == "snapshot" and len(result["messages"]) == 2
    assert "base_cursor" not in result["sync"]


def test_expiry_lru_restart_and_cross_conversation_or_selector(store, monkeypatch):
    db, client, _ = store
    seed(db)
    now = [0.]
    cache = history_sync.HistorySyncCache(max_windows=2, clock=lambda: now[0])
    monkeypatch.setattr(history_sync, "_CACHE", cache)
    first = page(client)
    page(client)
    page(client)
    assert len(cache._windows) == 2
    assert page(client, cursor=first["sync"]["cursor"])["sync"]["mode"] == "snapshot"
    first = page(client)
    now[0] += history_sync.TTL_SECONDS + 1
    assert page(client, cursor=first["sync"]["cursor"])["sync"]["mode"] == "snapshot"
    first = page(client)
    assert page(client, cursor=first["sync"]["cursor"], limit=2)["sync"]["mode"] == "snapshot"
    db.create_session("another", source="weixin")
    db.append_message("another", "assistant", "other owner")
    assert page(client, cursor=first["sync"]["cursor"], sid="another")["sync"]["mode"] == "snapshot"
    monkeypatch.setattr(history_sync, "_CACHE", history_sync.HistorySyncCache())
    assert page(client, cursor=first["sync"]["cursor"])["sync"]["mode"] == "snapshot"


def test_actual_fresh_server_process_cannot_reuse_old_cursor(store):
    db, client, home = store
    seed(db)
    first = page(client)
    script = '''import json,sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
import hermes_state
hermes_state.DEFAULT_DB_PATH=Path(sys.argv[1])
from hermes_cli.web_routers.sessions import manage_router
app=FastAPI(); app.include_router(manage_router)
with TestClient(app) as client:
    result=client.get('/api/sessions/recovery/messages',params={'recovery_view':1,'history_sync':1,'sync_cursor':sys.argv[2]}).json()
    print(json.dumps(result))
'''
    child = subprocess.run([sys.executable, "-c", script, str(home / "state.db"), first["sync"]["cursor"]],
                           text=True, capture_output=True, check=True, timeout=20)
    current = json.loads(child.stdout)
    assert current["sync"]["mode"] == "snapshot" and len(current["messages"]) == 4


def test_cursor_owner_contains_actual_database_path(store, monkeypatch, tmp_path):
    db, client, _ = store
    seed(db)
    first = page(client)
    other_path = tmp_path / "other.db"
    with SessionDB(db_path=other_path) as other:
        other.create_session("recovery", source="desktop")
        other.append_message("recovery", "assistant", "different database")
    monkeypatch.setattr("hermes_cli.web_routers.sessions._open_session_db_for_profile",
                        lambda profile, read_only: SessionDB(db_path=other_path, read_only=read_only))
    result = page(client, cursor=first["sync"]["cursor"])
    assert result["sync"]["mode"] == "snapshot"
    assert result["messages"][0]["content"] == "different database"


@pytest.mark.parametrize("field,value", [("reasoning", "updated thought"),
    ("tool_calls", json.dumps([{"id": "call", "function": {"name": "terminal", "arguments": "new args"}}]))])
def test_in_place_detail_changes_invalidate_unchanged_cards_and_detail_revision(store, field, value):
    db, client, _ = store
    db.append_messages_batch("recovery", [{"role": "user", "content": "opening"}, {
        "role": "assistant", "content": "answer", "reasoning": "old thought", "tool_calls": [
            {"id": "call", "function": {"name": "terminal", "arguments": "old args"}}]}])
    first = page(client)
    row_id = first["messages"][-1]["id"]
    db._write_sql(f"UPDATE messages SET {field}=? WHERE id=?", (value, row_id))
    changed = page(client, cursor=first["sync"]["cursor"])
    assert changed["coverage"] == first["coverage"]
    assert len(changed["messages"]) == 1
    assert changed["sync"]["revisions"][str(row_id)] != first["sync"]["revisions"][str(row_id)]
    detail = client.get("/api/sessions/recovery/messages", params={
        "history_sync": 1, "detail_row_ids": str(row_id)}).json()["messages"][0]
    assert detail["detail_revision"] == changed["sync"]["revisions"][str(row_id)]
    if field == "reasoning":
        assert detail["reasoning"] == value


def test_internal_source_marker_does_not_change_visible_detail_revision(store):
    db, client, _ = store
    db.append_message("recovery", "user", "opening", message_uid="native-source")
    first = page(client)
    row_id = first["messages"][0]["id"]
    db._write_sql("UPDATE messages SET display_metadata=? WHERE id=?", (json.dumps({
        "turn_source": {"message_uid": "native-source", "turn_id": "native-turn"}}), row_id))
    current = page(client, cursor=first["sync"]["cursor"])
    assert current["sync"]["revisions"] == first["sync"]["revisions"]
    assert current["messages"] == []


def test_provider_hidden_replay_changes_do_not_change_visible_detail_revision(store):
    db, client, _ = store
    db.append_message("recovery", "assistant", "visible", reasoning="shown", reasoning_details=[
        {"type": "reasoning.text", "text": "shown", "signature": "old"},
        {"type": "reasoning.encrypted", "data": "private-old"}])
    first = page(client)
    row_id = first["messages"][0]["id"]
    db._write_sql("UPDATE messages SET api_content=?,codex_reasoning_items=?,reasoning_details=? WHERE id=?",
                 ("hidden model text", '[{"encrypted_content":"private-new"}]', json.dumps([
                     {"type": "reasoning.text", "text": "shown", "signature": "new"},
                     {"type": "reasoning.encrypted", "data": "private-new"}]), row_id))
    current = page(client, cursor=first["sync"]["cursor"])
    assert current["sync"]["revisions"] == first["sync"]["revisions"]
    assert current["messages"] == []


def test_compaction_representative_rewind_and_cross_channel_changes(store):
    db, client, _ = store
    seed(db)
    first = page(client)
    original = db.get_messages("recovery")
    db.archive_and_compact("recovery", original)
    db.end_session("recovery", end_reason="compression")
    db.create_session("tip", source="weixin", parent_session_id="recovery")
    db.append_messages_batch("tip", original)
    changed = page(client, cursor=first["sync"]["cursor"])
    assert changed["session_id"] == "tip" and changed["sync"]["mode"] == "delta"
    assert changed["sync"]["order"] != first["sync"]["order"]
    assert {row["message_uid"] for row in changed["messages"]} == {row["message_uid"] for row in first["messages"]}
    db.rewind_to_message("tip", changed["messages"][0]["id"])
    rewound = page(client, cursor=changed["sync"]["cursor"])
    assert len(rewound["sync"]["order"]) < len(changed["sync"]["order"])
    assert not set(rewound["sync"]["order"]) & set(first["sync"]["order"])


def test_latest_turn_thinking_crosses_first_page_without_hydrating_other_payloads(store, monkeypatch):
    db, client, _ = store
    db.append_messages_batch("recovery", [{"role": "user", "content": "old source"},
        {"role": "assistant", "content": "old answer", "reasoning": "old thought"},
        {"role": "user", "content": "latest source"}, {
        "role": "assistant", "content": "not requested body", "reasoning": "full latest thought",
        "tool_calls": [{"id": "call", "function": {"name": "terminal", "arguments": "private lazy args"}}]},
        *[{"role": "assistant", "content": f"body-{i}"} for i in range(220)],
        {"role": "user", "content": "mid turn correction", "display_kind": "steer"},
        {"role": "user", "content": "<framework-message>\nnot a new turn\n</framework-message>",
         "display_kind": "process_complete", "display_metadata": {"display_text": "not a new turn", "origin": "framework"}}])
    hydrated = []
    convert = SessionDB._row_to_message_dict
    def observe(self, row, **kwargs):
        hydrated.append((row["id"], kwargs.get("warn_context")))
        return convert(self, row, **kwargs)
    monkeypatch.setattr(SessionDB, "_row_to_message_dict", observe)
    first = page(client)
    thinking = first["sync"]["latest_thinking"]
    assert len(first["messages"]) == 200 and len(thinking["rows"]) == 1
    row = thinking["rows"][0]
    assert row["reasoning"] == "full latest thought" and "content" not in row and "tool_calls" not in row
    assert thinking["positions"][str(row["id"])] == 3
    assert len(hydrated) == 201
    assert "private lazy args" not in json.dumps(first)
    assert thinking["source"]["row_id"] == db._read_one("SELECT id FROM messages WHERE content='latest source'")[0]
    db._write_sql("UPDATE messages SET tool_calls=? WHERE id=?", (json.dumps([
        {"id": "call", "function": {"name": "terminal", "arguments": "changed lazy args"}}]), row["id"]))
    changed = page(client, cursor=first["sync"]["cursor"])
    assert changed["messages"] == []
    latest = changed["sync"]["latest_thinking"]
    assert latest["revisions"][str(row["id"])] != thinking["revisions"][str(row["id"])]
    assert len(latest["rows"]) == 1 and "changed lazy args" not in json.dumps(changed)
    db.append_message("recovery", "user", "new actual turn")
    next_turn = page(client, cursor=changed["sync"]["cursor"])
    assert next_turn["sync"]["latest_thinking"]["order"] == []


def test_thinking_is_limited_to_recent_500_and_not_requested_by_legacy(store, monkeypatch):
    db, client, _ = store
    seed(db, 520)
    count = []
    convert = SessionDB._row_to_message_dict
    def observe(self, row, **kwargs):
        count.append(kwargs.get("warn_context"))
        return convert(self, row, **kwargs)
    monkeypatch.setattr(SessionDB, "_row_to_message_dict", observe)
    old = client.get("/api/sessions/recovery/messages", params={"recovery_view": 1, "limit": 2}).json()
    assert "sync" not in old and len(count) == 2
    count.clear()
    result = page(client, limit=2)
    bundle = result["sync"]["latest_thinking"]
    assert len(bundle["order"]) == 500 and min(bundle["positions"].values()) == 21
    assert len(count) == 502
    assert len(history_sync._CACHE._windows) <= history_sync.MAX_WINDOWS
    assert all(len(set(entry.revisions) | set(entry.thinking_revisions)) <= 500
               for entry in history_sync._CACHE._windows.values())


def test_legacy_defaults_and_opt_in_validation(store):
    db, client, _ = store
    seed(db)
    ordinary = client.get("/api/sessions/recovery/messages", params={"view": "cards"}).json()
    ignored = client.get("/api/sessions/recovery/messages", params={"view": "cards", "history_sync": 1}).json()
    assert ordinary == ignored and "sync" not in ignored
    row_id = ordinary["messages"][0]["id"]
    legacy_detail = client.get("/api/sessions/recovery/messages", params={"detail_row_ids": str(row_id)}).json()
    assert "detail_revision" not in legacy_detail["messages"][0]
    assert client.get("/api/sessions/recovery/messages", params={"recovery_view": 1, "history_sync": 2}).status_code == 400


def test_record_long_body_wire_cost_and_frontend_consumable_fixtures(store):
    db, client, _ = store
    db.append_messages_batch("recovery", [{"role": "user", "content": "long opening"}, *[
        {"role": "assistant", "content": f"body-{i}:" + "long body 文本 " * 2000} for i in range(199)]])
    first = page(client)
    unchanged = page(client, cursor=first["sync"]["cursor"])
    db.append_message("recovery", "assistant", "small append")
    appended = page(client, cursor=unchanged["sync"]["cursor"])
    encode = lambda value: json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode()
    sizes = {name: len(encode(value)) for name, value in (
        ("snapshot_200", first), ("unchanged_200", unchanged), ("one_append_200", appended))}
    assert sizes["unchanged_200"] < sizes["snapshot_200"] / 50
    assert sizes["one_append_200"] < sizes["snapshot_200"] / 50
    output = Path(__file__).resolve().parents[2] / ".hermes-dev/incremental-sync-20261027/backend"
    output.mkdir(parents=True, exist_ok=True)
    (output / "wire-bytes.json").write_text(json.dumps({"json_bytes": sizes, "requests_per_case": 1}, indent=2))


def test_small_frontend_consumable_wire_fixtures(store):
    db, client, _ = store
    seed(db, 2)
    first = page(client)
    unchanged = page(client, cursor=first["sync"]["cursor"])
    db.append_message("recovery", "assistant", "small append", reasoning="new complete thought")
    appended = page(client, cursor=unchanged["sync"]["cursor"])
    output = Path(__file__).resolve().parents[2] / ".hermes-dev/incremental-sync-20261027/backend"
    output.mkdir(parents=True, exist_ok=True)
    (output / "wire-fixtures.json").write_text(json.dumps(
        {"snapshot": first, "unchanged": unchanged, "appended": appended}, ensure_ascii=False))
    assert (output / "wire-fixtures.json").stat().st_size < 20000


@pytest.mark.parametrize("kind,metadata", [
    ("steer", {}), ("hidden", {}), ("model_switch", {}), ("skill_invocation", {}), ("compaction", {}),
    ("process_complete", {"origin": "framework"}), ("process_complete", {"origin": "notebook"}),
    ("process_complete", {"producer": "noting_result"}), (None, {"_queued_prompt": True}),
])
def test_non_turn_user_rows_do_not_empty_latest_thinking(store, kind, metadata):
    db, client, _ = store
    seed(db)
    original = page(client)
    db.append_message("recovery", "user", "native control or delivery", display_kind=kind, display_metadata=metadata)
    result = page(client, cursor=original["sync"]["cursor"])
    assert result["sync"]["latest_thinking"]["source"] == original["sync"]["latest_thinking"]["source"]
    assert result["sync"]["latest_thinking"]["order"] == original["sync"]["latest_thinking"]["order"]


@pytest.mark.parametrize("source_kind", ["auto_continue", "process_complete"])
def test_explicit_continuation_or_durable_terminal_source_starts_new_thinking_scope(store, source_kind):
    db, client, _ = store
    seed(db)
    db.append_message("recovery", "user", "proven new source", display_kind=source_kind)
    source = db.get_messages("recovery")[-1]
    if source_kind == "process_complete":
        db._write_sql("UPDATE messages SET display_metadata=? WHERE id=?", (json.dumps({
            "turn_terminal": {"source_message_uid": source["message_uid"], "status": "error"}}), source["id"]))
    db.append_message("recovery", "assistant", "new answer", reasoning="new thinking only")
    result = page(client)
    assert result["sync"]["latest_thinking"]["source"]["message_uid"] == source["message_uid"]
    assert [row["reasoning"] for row in result["sync"]["latest_thinking"]["rows"]] == ["new thinking only"]


def test_unmarked_typed_turn_keeps_old_ambiguous_thinking_lazy(store):
    db, client, _ = store
    seed(db, 1)
    original = page(client)
    db.append_message("recovery", "user", "unmarked synthetic trigger", display_kind="process_complete")
    db.append_message("recovery", "assistant", "new typed-turn answer", reasoning="latest unmarked thought")
    result = page(client)
    bundle = result["sync"]["latest_thinking"]
    assert original["sync"]["latest_thinking"]["source"] is not None
    assert bundle["source"] is None and bundle["order"] == [] and bundle["rows"] == []


def test_real_named_profile_does_not_accept_default_owner_cursor(store):
    db, client, home = store
    seed(db)
    first = page(client)
    profile_home = home / "profiles" / "alex"
    profile_home.mkdir(parents=True)
    (profile_home / "config.yaml").write_text("{}\n")
    with SessionDB(db_path=profile_home / "state.db") as other:
        other.create_session("recovery", source="weixin")
        other.append_message("recovery", "assistant", "named owner content")
    result = page(client, cursor=first["sync"]["cursor"], profile="alex")
    assert result["profile"] == "alex" and result["sync"]["mode"] == "snapshot"
    assert result["messages"][0]["content"] == "named owner content"


def test_thinking_detail_wire_has_no_opaque_provider_replay_material(store):
    db, client, _ = store
    db.append_messages_batch("recovery", [{"role": "user", "content": "source"}, {
        "role": "assistant", "content": "visible body", "reasoning_details": [
            {"type": "reasoning.text", "text": "visible full thought", "signature": "secret signature"},
            {"type": "reasoning.encrypted", "data": "opaque replay data"}]}])
    bundle = page(client)["sync"]["latest_thinking"]
    assert bundle["rows"][0]["reasoning_details"] == [{"type": "reasoning.text", "text": "visible full thought"}]
    assert "secret signature" not in json.dumps(bundle) and "opaque replay data" not in json.dumps(bundle)


def test_opaque_and_malformed_sidecars_do_not_hydrate_unseen_non_thinking_rows(store, monkeypatch):
    db, client, _ = store
    db.append_messages_batch("recovery", [{"role": "user", "content": "source"},
        {"role": "assistant", "content": "unseen body", "reasoning_details": [
            {"type": "reasoning.encrypted", "data": "opaque only"}]},
        {"role": "user", "content": "delivery", "display_kind": "process_complete", "display_metadata": {
            "origin": "framework", "turn_terminal": {"outputs": ["malformed", 4, None]}}},
        {"role": "assistant", "content": "requested last row"}])
    hydrated = []
    original = SessionDB._row_to_message_dict
    def observe(self, row, **kwargs):
        hydrated.append(row["id"])
        return original(self, row, **kwargs)
    monkeypatch.setattr(SessionDB, "_row_to_message_dict", observe)
    result = page(client, limit=1)
    assert result["sync"]["latest_thinking"]["order"] == []
    assert hydrated == result["sync"]["order"]


@pytest.mark.parametrize('marker,valid', [
    (None, False), ([], False), ({}, False),
    ({'message_uid': 'other', 'turn_id': 'turn'}, False),
    ({'message_uid': 'typed-source', 'turn_id': ''}, False),
    ({'message_uid': 'typed-source', 'turn_id': '   '}, False),
    ({'message_uid': 'typed-source', 'turn_id': 12}, False),
    ({'message_uid': 'typed-source', 'turn_id': 'native-turn'}, True),
])
def test_typed_source_requires_valid_native_marker(store, marker, valid):
    db, client, _ = store
    seed(db, 1)
    db.append_messages_batch('recovery', [
        {'role': 'user', 'content': 'typed source', 'message_uid': 'typed-source',
         'display_kind': 'process_complete', 'display_metadata': {'turn_source': marker}},
        {'role': 'assistant', 'content': 'latest', 'reasoning': 'latest native thought'}])
    bundle = page(client)['sync']['latest_thinking']
    if valid:
        assert bundle['source']['message_uid'] == 'typed-source'
        assert [row['reasoning'] for row in bundle['rows']] == ['latest native thought']
    else:
        assert bundle['source'] is None and bundle['order'] == [] and bundle['rows'] == []


@pytest.mark.parametrize('started', [False, True])
def test_source_marker_distinguishes_started_from_merely_queued(store, started):
    db, client, _ = store
    seed(db, 1)
    old = page(client)['sync']['latest_thinking']
    metadata = {'_queued_prompt': True}
    if started:
        metadata['turn_source'] = {'message_uid': 'queued-native', 'turn_id': 'actual-turn'}
    db.append_messages_batch('recovery', [{'role': 'user', 'content': 'queued', 'message_uid': 'queued-native',
        'display_metadata': metadata, 'display_kind': 'process_complete'}])
    if started:
        db.append_message('recovery', 'assistant', 'actual answer', reasoning='actual thought')
    bundle = page(client)['sync']['latest_thinking']
    if started:
        assert bundle['source']['message_uid'] == 'queued-native'
        assert [row['reasoning'] for row in bundle['rows']] == ['actual thought']
    else:
        assert bundle['source'] == old['source'] and bundle['order'] == old['order']


def test_append_only_typed_delivery_never_fabricates_a_turn_source(store):
    db, client, _ = store
    seed(db, 1)
    db.append_message('recovery', 'user', 'delivery only', display_kind='process_complete',
                      display_metadata={'display_text': 'delivery only'})
    delivery = db.get_messages('recovery')[-1]
    assert 'turn_source' not in delivery['display_metadata']
    bundle = page(client)['sync']['latest_thinking']
    assert bundle['source'] is None and bundle['rows'] == []
