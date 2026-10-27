"""History sync over formal REST receipts and session.activate with real SQLite."""
from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from hermes_state import SessionDB
import hermes_state_history_sync as history_sync
from tests.tui_gateway.test_recovery_view import activate, begin_web, request
from tui_gateway import event_replay, recovery_view, server

pytest_plugins = ["tests.tui_gateway.test_recovery_view"]


@pytest.fixture
def rest(native, monkeypatch):
    db, session, home = native
    monkeypatch.setattr("hermes_state.DEFAULT_DB_PATH", home / "state.db")
    from hermes_cli.web_routers.sessions import manage_router
    app = FastAPI()
    app.include_router(manage_router)
    with TestClient(app) as client:
        yield client


def synced_request(client, *, limit=200):
    response = client.get("/api/sessions/stored/messages", params={"recovery_view": 1, "history_sync": 1, "limit": limit})
    assert response.status_code == 200, response.text
    page = response.json()
    return {"version": 1, "sync_version": 1, "profile": page["profile"], "stored_id": "stored", "windows": [
        {"selector": page["selector"], "receipt": page["coverage"], "cursor": page["sync"]["cursor"]}]}, page


def test_formal_rest_cursor_activate_match_delta_and_lost_process_fallback(native, rest, monkeypatch):
    db, session, _ = native
    req, first = synced_request(rest)
    current = activate(req)
    window = current["windows"][0]
    assert current["complete"] and window["matched"] and "messages" not in window
    assert window["sync"]["mode"] == "delta" and window["sync"]["base_cursor"] == first["sync"]["cursor"]
    db.append_message("stored", "assistant", "cross channel write")
    changed = activate(req)["windows"][0]
    assert not changed["matched"] and [row["content"] for row in changed["messages"]] == ["cross channel write"]
    monkeypatch.setattr(history_sync, "_CACHE", history_sync.HistorySyncCache())
    fallback = activate(req)["windows"][0]
    assert not fallback["matched"] and fallback["sync"]["mode"] == "snapshot"
    assert len(fallback["messages"]) == fallback["coverage"]["window"]["returned"] == 3


def test_same_cards_changed_details_force_rpc_unmatched_and_return_new_shell(native, rest):
    db, _session, _ = native
    row_id = db.get_messages("stored")[1]["id"]
    db._write_sql("UPDATE messages SET reasoning=? WHERE id=?", ("first thought", row_id))
    req, before = synced_request(rest)
    db._write_sql("UPDATE messages SET reasoning=? WHERE id=?", ("changed thought", row_id))
    req["details"] = [row_id]
    result = activate(req)
    window = result["windows"][0]
    assert window["coverage"] == req["windows"][0]["receipt"]
    assert not window["matched"] and len(window["messages"]) == 1
    assert window["messages"][0]["id"] == row_id
    assert window["sync"]["revisions"][str(row_id)] != before["sync"]["revisions"][str(row_id)]
    assert result["details"][0]["detail_revision"] == window["sync"]["revisions"][str(row_id)]
    assert result["details"][0]["reasoning"] == "changed thought"


@pytest.mark.parametrize("repeated", [False, True])
def test_d0_s_d1_in_place_detail_change_uses_real_snapshot_race(native, rest, monkeypatch, repeated):
    db, session, home = native
    row_id = db.get_messages("stored")[1]["id"]
    db._write_sql("UPDATE messages SET reasoning=? WHERE id=?", ("initial thought", row_id))
    req, _ = synced_request(rest)
    original, mutations = recovery_view.snapshot, []
    def capture(*args, **kwargs):
        result = original(*args, **kwargs)
        if not mutations or repeated:
            with SessionDB(db_path=home / "state.db") as writer:
                writer._write_sql("UPDATE messages SET reasoning=? WHERE id=?", (f"changed-{len(mutations)}", row_id))
            mutations.append(True)
        return result
    monkeypatch.setattr(recovery_view, "snapshot", capture)
    result = activate(req)
    if repeated:
        assert not result["complete"] and result["reason"] == "view_changed" and len(mutations) == 2
    else:
        assert result["complete"] and not result["windows"][0]["matched"]
        assert result["windows"][0]["sync"]["latest_thinking"]["rows"][0]["reasoning"] == "changed-0"


@pytest.mark.parametrize("repeated", [False, True])
def test_thinking_outside_first_page_is_part_of_d0_s_d1(native, rest, monkeypatch, repeated):
    db, _session, home = native
    row_id = db.get_messages("stored")[1]["id"]
    db._write_sql("UPDATE messages SET reasoning=? WHERE id=?", ("outside first page", row_id))
    db.append_messages_batch("stored", [{"role": "assistant", "content": f"later-{i}"} for i in range(220)])
    req, before = synced_request(rest)
    assert before["sync"]["latest_thinking"]["order"] == [row_id]
    assert row_id not in before["sync"]["order"]
    original, mutations = recovery_view.snapshot, []
    def capture(*args, **kwargs):
        result = original(*args, **kwargs)
        if not mutations or repeated:
            with SessionDB(db_path=home / "state.db") as writer:
                writer._write_sql("UPDATE messages SET reasoning=? WHERE id=?", (f"raced-{len(mutations)}", row_id))
            mutations.append(True)
        return result
    monkeypatch.setattr(recovery_view, "snapshot", capture)
    result = activate(req)
    if repeated:
        assert not result["complete"] and result["reason"] == "view_changed" and len(mutations) == 2
    else:
        assert result["complete"]
        window = result["windows"][0]
        assert window["matched"] and "messages" not in window
        assert window["sync"]["latest_thinking"]["rows"][0]["reasoning"] == "raced-0"


def test_native_source_precedes_later_user_rows_and_state_snapshot_remains_native(native, rest):
    db, session, _ = native
    begin_web(db, session)
    source = session["inflight_turn"]["_terminal_source"]
    db.append_messages_batch("stored", [{"role": "assistant", "content": "running committed piece", "reasoning": "native turn thought"},
        {"role": "user", "content": "later user row without a new native Turn"},
        {"role": "user", "content": "steer", "display_kind": "steer"},
        {"role": "user", "content": "control", "display_kind": "process_complete"}])
    req, _ = synced_request(rest)
    result = activate(req)
    assert result["complete"] and result["running"]
    bundle = result["windows"][0]["sync"]["latest_thinking"]
    assert bundle["source"]["message_uid"] == source["message_uid"]
    assert bundle["rows"][0]["reasoning"] == "native turn thought"
    assert result["state_snapshot"]["complete"] is True
    assert any(event["type"] == "message.delta" and event["payload"]["text"] == "old live answer"
               for event in result["state_snapshot"]["events"])
    # Live native output is NOT forged into an additional durable Thinking row.
    assert all("_output_identity" not in row and "epoch" not in row for row in bundle["rows"])


def test_full_hash_projection_stays_outside_db_history_and_replay_locks(native, rest, monkeypatch):
    db, session, _ = native
    req, _ = synced_request(rest)
    db_contexts = [0]
    original_ctx, original_revision = db._read_ctx, history_sync.detail_revision
    @contextmanager
    def observed_ctx():
        with original_ctx() as conn:
            db_contexts[0] += 1
            try:
                yield conn
            finally:
                db_contexts[0] -= 1
    calls = []
    def revision(row):
        assert db_contexts[0] == 0 and not session["history_lock"].locked()
        assert not event_replay._replay_lock.locked()
        calls.append(row["id"])
        return original_revision(row)
    monkeypatch.setattr(db, "_read_ctx", observed_ctx)
    monkeypatch.setattr(history_sync, "detail_revision", revision)
    assert activate(req)["complete"] and calls


def test_terminal_thinking_keeps_reasoning_only_and_tool_disclosures_lazy(native, rest):
    db, _session, _ = native
    user_id = db.get_messages("stored")[0]["id"]
    metadata = {"turn_terminal": {"source_message_uid": db.get_messages("stored")[0]["message_uid"],
        "status": "error", "outputs": [{"kind": "reasoning", "text": "complete residual thought"},
            {"kind": "tool", "name": "terminal", "args": {"cmd": "lazy args"}, "result": "lazy result"}]}}
    db._write_sql("UPDATE messages SET display_metadata=? WHERE id=?", (json.dumps(metadata), user_id))
    req, _ = synced_request(rest)
    result = activate(req)
    bundle = result["windows"][0]["sync"]["latest_thinking"]
    # Receipt cursor may omit unchanged bundle rows; order still proves the candidate.
    assert result["complete"] and bundle["order"] == [user_id]
    req["windows"][0].pop("cursor")
    snapshot = activate(req)["windows"][0]["sync"]["latest_thinking"]
    row = snapshot["rows"][0]
    assert row["display_metadata"]["turn_terminal"]["outputs"] == [{"kind": "reasoning", "text": "complete residual thought"}]
    assert "lazy args" not in json.dumps(snapshot) and "lazy result" not in json.dumps(snapshot)


@pytest.mark.parametrize("field,value", [("sync_version", 2), ("sync_version", True), ("cursor", 123)])
def test_opt_in_validation_preserves_original_rpc_receipt_requirement(native, field, value):
    db, _, _ = native
    req = request(db)
    req["sync_version"] = 1
    if field == "cursor":
        req["windows"][0]["cursor"] = value
    else:
        req[field] = value
    response = server._methods["session.activate"]("invalid", {"session_id": "runtime", "recovery_view": req})
    assert response["error"]["code"] == -32602
    req = {"version": 1, "sync_version": 1, "stored_id": "stored", "profile": "default", "windows": [{"cursor": "opaque"}]}
    response = server._methods["session.activate"]("missing", {"session_id": "runtime", "recovery_view": req})
    assert response["error"]["code"] == -32602


def test_rpc_fixture_for_frontend(native, rest):
    req, page = synced_request(rest)
    result = activate(req)
    path = Path(__file__).resolve().parents[2] / ".hermes-dev/incremental-sync-20261027/backend/rpc-wire-fixture.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"request": req, "rest": page, "result": result}, ensure_ascii=False, indent=2))


def test_retained_complete_native_snapshot_keeps_provable_source_after_settlement(native, rest):
    from tests.tui_gateway.test_recovery_view import settled_web_output
    db, session, _ = native
    db._write_sql("UPDATE messages SET reasoning=? WHERE role='assistant'", ("completed thought",))
    settled_web_output(db, session)
    # A later queued row must not replace the completed native source.
    db.append_message("stored", "user", "queued after settlement", display_metadata={"_queued_prompt": True})
    req, _ = synced_request(rest)
    req["windows"][0].pop("cursor")
    result = activate(req)
    bundle = result["windows"][0]["sync"]["latest_thinking"]
    assert result["complete"] and not result["running"]
    assert bundle["source"]["message_uid"] == db.get_messages("stored")[0]["message_uid"]
    assert bundle["rows"][0]["reasoning"] == "completed thought"


@pytest.mark.parametrize("active", [False, True])
def test_retained_local_source_cannot_override_new_external_turn(native, rest, active):
    from tests.tui_gateway.test_recovery_view import settled_web_output
    db, session, _ = native
    db._write_sql("UPDATE messages SET reasoning=? WHERE role='assistant'", ("previous local thought",))
    settled_web_output(db, session)
    db.append_messages_batch("stored", [{"role": "user", "content": "new external question"},
        {"role": "assistant", "content": "external answer", "reasoning": "external thinking"}])
    if active:
        assert db.try_acquire_session_turn_lease("stored", "opaque-external-channel-owner")
    req, _ = synced_request(rest)
    req["windows"][0].pop("cursor")
    result = activate(req)
    bundle = result["windows"][0]["sync"]["latest_thinking"]
    assert result["complete"] and result["running"] is active
    if active:
        assert result["live_output_available"] is False
    assert [row["reasoning"] for row in bundle["rows"]] == ["external thinking"]
    db.release_session_turn_lease("stored", "opaque-external-channel-owner")


def test_completed_local_snapshot_does_not_guess_past_unknown_legacy_typed_row(native, rest):
    from tests.tui_gateway.test_recovery_view import settled_web_output
    db, session, _ = native
    db._write_sql('UPDATE messages SET reasoning=? WHERE role=?', ('old thought', 'assistant'))
    settled_web_output(db, session)
    db.append_messages_batch('stored', [{'role': 'user', 'content': 'legacy unknown typed input', 'display_kind': 'process_complete'},
        {'role': 'assistant', 'content': 'legacy answer', 'reasoning': 'ambiguous newest thought'}])
    req, _ = synced_request(rest)
    req['windows'][0].pop('cursor')
    result = activate(req)
    assert result['complete'] and not result['running']
    bundle = result['windows'][0]['sync']['latest_thinking']
    assert bundle['source'] is None and bundle['order'] == [] and bundle['rows'] == []
