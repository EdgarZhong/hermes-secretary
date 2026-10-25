"""Real SQLite and formal REST recovery windows, with bounded payload reads."""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from hermes_state import SessionDB
from hermes_state_recovery_view import RecoveryViewError, project_view, read_view, selector


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr("hermes_state.DEFAULT_DB_PATH", home / "state.db")
    db = SessionDB(db_path=home / "state.db")
    db.create_session("recovery", source="desktop")
    from hermes_cli.web_routers.sessions import manage_router
    app = FastAPI()
    app.include_router(manage_router)
    with TestClient(app) as client:
        yield db, client, home
    db.close()


def append(db, count, sid="recovery"):
    db.append_messages_batch(sid, [{"role": "assistant", "content": f"answer-{i}", "timestamp": i+1}
                                   for i in range(count)])


def test_latest_default_and_arbitrary_deep_anchor_are_bounded(store, monkeypatch):
    db, client, _ = store
    append(db, 1400)
    reads = []
    original = SessionDB._row_to_message_dict
    def track(self, row, **kwargs):
        reads.append(row["id"])
        return original(self, row, **kwargs)
    monkeypatch.setattr(SessionDB, "_row_to_message_dict", track)
    page = client.get("/api/sessions/recovery/messages?recovery_view=1").json()
    assert len(page["messages"]) == len(reads) == 200
    assert page["messages"][0]["content"] == "answer-1200"
    window = page["coverage"]["window"]
    assert window["start"] == 1200 and window["end"] == 1399
    assert window["is_end"] and not window["is_start"]
    reads.clear()
    anchor = db._read_one("SELECT id,message_uid FROM messages WHERE session_id='recovery' ORDER BY id LIMIT 1 OFFSET 30")
    deep = client.get("/api/sessions/recovery/messages", params={
        "recovery_view": 1, "anchor_uid": anchor["message_uid"], "before": 2, "after": 2}).json()
    assert len(deep["messages"]) == len(reads) == 5
    assert [row["content"] for row in deep["messages"]] == [f"answer-{i}" for i in range(28,33)]
    assert deep["coverage"]["window"]["predecessor"]["position"] == 27
    assert deep["coverage"]["window"]["successor"]["position"] == 33


def test_legacy_call_stays_unchanged_and_conflicts_rejected(store):
    db, client, _ = store
    append(db, 4)
    old = client.get("/api/sessions/recovery/messages?view=cards").json()
    assert "coverage" not in old and old["pagination"]["limit"] == 500
    for query in ("recovery_view=2", "recovery_view=1&offset=1", "recovery_view=1&detail_row_ids=1",
                  "recovery_view=1&before=2", "recovery_view=1&anchor_row_id=1&limit=3",
                  "recovery_view=1&anchor_row_id=1&before=300&after=300", "anchor_row_id=1"):
        assert client.get("/api/sessions/recovery/messages?"+query).status_code == 400
    assert client.get("/api/sessions/absent/messages?recovery_view=1").status_code == 404
    assert client.get("/api/sessions/recovery/messages?recovery_view=1&anchor_row_id=99999").status_code == 404


@pytest.mark.parametrize("legacy", [False, True])
def test_lineage_representatives_retired_uids_branch_and_details(store, legacy):
    db, client, _ = store
    db.append_messages_batch("recovery", [{"role":"user","content":"ask"},
                                         {"role":"assistant","content":"answer","reasoning":"hidden"}])
    original = db.get_messages("recovery")
    db.archive_and_compact("recovery", original)
    db.end_session("recovery", end_reason="compression")
    db.create_session("tip", source="desktop", parent_session_id="recovery")
    db.append_messages_batch("tip", original)
    db.append_message("tip", "assistant", "tip answer")
    db.create_session("branch", source="tool", parent_session_id="tip")
    db.append_message("branch", "assistant", "private branch")
    if legacy:
        db._write_sql("UPDATE messages SET display_identity=NULL,display_order=NULL")
    page = client.get("/api/sessions/recovery/messages?recovery_view=1").json()
    assert page["session_id"] == "tip" and page["coverage"]["lineage"] == ["recovery","tip"]
    assert [row["content"] for row in page["messages"]] == ["ask","answer","tip answer"]
    assert "reasoning" not in page["messages"][1]
    answer = page["messages"][1]
    view = project_view(read_view(db,"recovery","default",[selector()],details=[answer["id"]]))
    assert view["details"][0]["reasoning"] == "hidden"
    # Formal rewind retires the latest generation: old aliases must stay gone.
    db.rewind_to_message("tip", page["messages"][0]["id"])
    current = client.get("/api/sessions/recovery/messages?recovery_view=1").json()
    assert "answer" not in [row.get("content") for row in current["messages"]]
    with pytest.raises(RecoveryViewError):
        read_view(db,"recovery","foreign",[selector()])
    with pytest.raises(RecoveryViewError):
        read_view(db,"recovery","default",[selector()],details=list(range(1,14)))


def test_explicit_snapshot_uses_one_connection_across_external_append(store, monkeypatch):
    db, _client, home = store
    append(db, 2)
    from hermes_state_recovery_view import _lineage
    def concurrent(owner, conn, requested, profile):
        rows = _lineage(owner,conn,requested,profile)
        with SessionDB(db_path=home/"state.db") as writer:
            writer.append_message("recovery","assistant","after snapshot")
        return rows
    monkeypatch.setattr("hermes_state_recovery_view._lineage", concurrent)
    captured = read_view(db,"recovery","default",[selector()])
    assert len(captured["windows"][0]["messages"]) == 2
    assert db._read_one("SELECT COUNT(*) FROM messages")[0] == 3


def test_fixture_is_formal_rest_output(store):
    db, client, _ = store
    db.append_messages_batch("recovery", [{"role":"user","content":"Recovery question","timestamp":1},
        {"role":"assistant","content":"Durable answer","timestamp":2,"reasoning":"Expanded detail"}])
    response = client.get("/api/sessions/recovery/messages?recovery_view=1")
    assert response.status_code == 200
    assert len(response.json()["coverage"]["digest"]) == 64


def test_retired_uid_and_physical_alias_cannot_anchor_to_another_equal_message(store):
    db,client,_home=store
    db.append_messages_batch("recovery",[{"role":"user","content":"same","timestamp":1,"message_uid":"retired"}])
    old=db.get_messages("recovery")[0]
    db.rewind_to_message("recovery",old["id"])
    db.append_messages_batch("recovery",[{"role":"user","content":"same","timestamp":1,"message_uid":"other"}])
    for key,value in (("anchor_uid","retired"),("anchor_row_id",old["id"])):
        assert client.get("/api/sessions/recovery/messages",params={"recovery_view":1,key:value}).status_code==404


def test_recovery_keeps_existing_multimodal_attachment_projection(store):
    db,client,_home=store
    content=[{"type":"text","text":"Describe this attachment"},
             {"type":"image_url","image_url":{"url":"data:image/png;base64,fixture"}}]
    db.append_message("recovery","user",content)
    legacy=client.get("/api/sessions/recovery/messages?view=cards").json()
    recovery=client.get("/api/sessions/recovery/messages?recovery_view=1").json()
    assert recovery["messages"][0]["content"] == legacy["messages"][0]["content"] == content
