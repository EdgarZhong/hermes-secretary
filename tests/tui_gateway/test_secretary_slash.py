"""Shared catalog/completion/slash.exec/command.dispatch behavior over real native DB state."""

import contextlib
import threading

import pytest

from hermes_state import SessionDB
from secretary.notebook_store import NotebookStore
from tui_gateway import server
from tui_gateway.transport import StdioTransport


@pytest.fixture
def live(tmp_path, monkeypatch):
    home = tmp_path / "secretary-profile"
    home.mkdir()
    (home / "config.yaml").write_text("noting:\n  enabled: true\n")
    db = SessionDB(home / "state.db")
    db.create_session("secretary-main", source="tui")
    db.append_message("secretary-main", "user", "Use reusable procedures.", message_uid="source-original")
    ref = db.resolve_conversation_ref("secretary-main")
    working = NotebookStore(db, ref)
    working.create("skill_candidate", {"capability": "Reusable procedure", "workflow_draft": "Step one", "why_reusable": "Repeat work"},
                   source_message_identities=[{"conversation_ref": ref, "message_uid": "source-original"}])
    db.notebook_commit_snapshot(ref, working.show(), anchor_message_uid="source-original")
    sid = "secretary-runtime"
    session = {"agent": None, "session_key": "secretary-main", "profile_home": str(home),
               "history": [], "history_lock": threading.Lock(), "running": False,
               "transport": StdioTransport(lambda: None, threading.Lock()), "cwd": "", "source": "tui"}
    server._sessions[sid] = session
    @contextlib.contextmanager
    def session_db(_session):
        yield db
    monkeypatch.setattr(server, "_session_db", session_db)
    monkeypatch.setattr(server, "_session_uses_compute_host", lambda _session: False)
    try:
        yield sid, session, home, db, ref
    finally:
        server._sessions.pop(sid, None)
        db.close()


def call(method, sid, **params):
    return server._methods[method]("test", {"session_id": sid, **params})


def test_catalog_and_completion_discover_new_commands_and_remove_refine(live):
    sid, *_ = live
    catalog = call("commands.catalog", sid)["result"]
    commands = {pair[0] for pair in catalog["pairs"]}
    assert {"/notebook", "/propose-persistence", "/review"} <= commands
    assert "/refine" not in commands
    for prefix, wanted in (("/note", "/notebook"), ("/propose", "/propose-persistence")):
        result = call("complete.slash", sid, text=prefix)["result"]
        assert wanted.lstrip("/") in {item["text"].lstrip("/") for item in result["items"]}
    result = call("complete.slash", sid, text="/notebook ")["result"]
    assert {"on", "off"} <= {item["text"].strip() for item in result["items"]}


def test_slash_exec_uses_live_state_and_send_keeps_tail(live):
    sid, session, home, db, ref = live
    before = db.notebook_current(ref)
    result = call("slash.exec", sid, command="/notebook off")["result"]
    assert "is off" in result["output"]
    result = call("slash.exec", sid, command="/notebook")["result"]
    assert str(before["created_at"]) in result["output"]
    assert "source-original" not in result["output"]
    assert before["snapshot_id"] not in result["output"]
    result = call("slash.exec", sid, command="/propose-persistence Keep THIS tail 文本")["result"]
    assert result["type"] == "send"
    assert result["message"].endswith("Keep THIS tail 文本")
    assert "Use reusable procedures." in result["message"]
    assert session.get("slash_worker") is None
    assert session["session_key"] == "secretary-main"
    assert db.notebook_current(ref) == before
    assert not db.notebook_local_enabled(ref)
    (home / "config.yaml").write_text("noting:\n  enabled: false\n")
    result = call("slash.exec", sid, command="/propose-persistence tail")["result"]
    assert result["type"] == "exec" and "unavailable" in result["output"]


def test_direct_dispatch_and_unknown_notebook_usage(live):
    sid, *_ = live
    result = call("command.dispatch", sid, name="notebook", arg="please edit")["result"]
    assert result["output"] == "Usage: /notebook [on|off]"
    result = call("command.dispatch", sid, name="propose-persistence", arg="Natural text")["result"]
    assert result["type"] == "send" and result["message"].endswith("Natural text")


def test_existing_prompt_commands_keep_the_normal_send_path(live):
    sid, *_ = live
    for name in ("queue", "plan", "learn"):
        result = call("command.dispatch", sid, name=name, arg="Preserve THIS intent")["result"]
        assert result["type"] == "send" and "Preserve THIS intent" in result["message"]
