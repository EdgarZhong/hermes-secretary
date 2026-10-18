"""Live roster preserves legacy fields and omits finalized runtimes."""
import threading
import types
from pathlib import Path

import pytest

from hermes_constants import reset_hermes_home_override, set_hermes_home_override

from tui_gateway import server


def _session(agent=None, **extra):
    return {"agent": agent or types.SimpleNamespace(), "session_key": "session-key", "history": [],
            "history_lock": threading.Lock(), "running": False, **extra}


# ── active live TUI sessions ─────────────────────────────────────────


def test_session_active_list_reports_live_sessions(monkeypatch):
    class _DB:
        def get_session_title(self, key):
            return {"key-a": "Research", "key-b": "Implement"}.get(key, "")

    previous_sessions = dict(server._sessions)
    server._sessions.clear()
    monkeypatch.setattr(server, "_get_db", lambda: _DB())
    server._sessions["sid-a"] = _session(
        agent=types.SimpleNamespace(model="model-a"),
        history=[{"role": "user", "content": "find docs"}],
        session_key="key-a",
        created_at=10.0,
        last_active=20.0,
    )
    server._sessions["sid-b"] = _session(
        agent=types.SimpleNamespace(model="model-b"),
        history=[{"role": "assistant", "content": "writing code"}],
        running=True,
        session_key="key-b",
        created_at=11.0,
        last_active=30.0,
    )
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.active_list",
                "params": {"current_session_id": "sid-b"},
            }
        )
    finally:
        server._sessions.clear()
        server._sessions.update(previous_sessions)

    session_rows = resp["result"]["sessions"]
    assert [row["id"] for row in session_rows] == ["sid-a", "sid-b"]

    rows = {row["id"]: row for row in session_rows}
    assert rows["sid-a"] == {
        "current": False,
        "id": "sid-a",
        "last_active": 20.0,
        "message_count": 1,
        "model": "model-a",
        "preview": "find docs",
        "session_key": "key-a",
        "started_at": 10.0,
        "status": "idle",
        "title": "Research",
        "stored_session_id": "key-a", "profile_name": server.profile_name_for_home(server._launch_home()) or "custom",
        "profile_home": str(Path(server._launch_home()).resolve()),
        "running": False, "turn_started_at": None,
    }
    assert rows["sid-b"]["current"] is True
    assert rows["sid-b"]["status"] == "working"
    assert rows["sid-b"]["title"] == "Implement"
    assert rows["sid-b"]["preview"] == "writing code"


def test_session_active_list_excludes_finalized_sessions(monkeypatch):
    """#38950: a finalized-but-not-yet-popped session must not inflate the count.

    The WS grace-reap and idle reaper set ``_finalized`` inside
    ``_teardown_session`` before popping the entry from ``_sessions``. During
    that window ``session.active_list`` would otherwise still report the dead
    session, which is exactly the footer "N sessions" count that only ever grew
    until a gateway restart. A live session on the real stdio transport (the
    standalone ``hermes --tui`` case) must still be reported.
    """
    class _DB:
        def get_session_title(self, key):
            return {"key-live": "Live", "key-dead": "Dead"}.get(key, "")

    previous_sessions = dict(server._sessions)
    server._sessions.clear()
    monkeypatch.setattr(server, "_get_db", lambda: _DB())
    server._sessions["sid-live"] = _session(
        agent=types.SimpleNamespace(model="model-live"),
        history=[{"role": "user", "content": "still here"}],
        session_key="key-live",
        created_at=10.0,
        last_active=20.0,
    )
    dead = _session(
        agent=types.SimpleNamespace(model="model-dead"),
        history=[{"role": "user", "content": "gone"}],
        session_key="key-dead",
        created_at=11.0,
        last_active=21.0,
    )
    dead["_finalized"] = True
    server._sessions["sid-dead"] = dead
    try:
        resp = server.handle_request(
            {
                "id": "1",
                "method": "session.active_list",
                "params": {},
            }
        )
    finally:
        server._sessions.clear()
        server._sessions.update(previous_sessions)

    session_rows = resp["result"]["sessions"]
    assert [row["id"] for row in session_rows] == ["sid-live"]




@pytest.mark.parametrize("launch_kind", ["default", "named", "custom"])
@pytest.mark.parametrize("legacy_profile", [None, "foreign"])
def test_launch_owner_does_not_follow_foreign_request_context(monkeypatch, tmp_path, launch_kind, legacy_profile):
    root = tmp_path / "hermes-root"
    foreign = root / "profiles" / "foreign"
    foreign.mkdir(parents=True)
    launch = {"default": root, "named": root / "profiles" / "launch-main", "custom": tmp_path / "custom-home"}[launch_kind]
    launch.mkdir(parents=True, exist_ok=True)
    expected = {"default": "default", "named": "launch-main", "custom": "custom"}[launch_kind]
    monkeypatch.setenv("HERMES_HOME", str(root))
    monkeypatch.setattr(server, "_launch_home", lambda: launch)
    monkeypatch.setattr(server, "_session_live_title", lambda session, key: key)
    monkeypatch.setattr(server, "_sessions", {
        "launch-runtime": _session(agent=types.SimpleNamespace(model="launch-model"),
                                   session_key="same-stored", profile_home=None),
        "foreign-runtime": _session(agent=types.SimpleNamespace(model="foreign-model"),
                                    session_key="same-stored", profile_home=str(foreign)),
    })
    token = set_hermes_home_override(str(foreign))
    try:
        assert server._current_profile_name() == "foreign"
        params = {} if legacy_profile is None else {"profile": legacy_profile}
        response = server.handle_request({"id": "foreign-read", "method": "session.active_list", "params": params})
        rows = {row["id"]: row for row in response["result"]["sessions"]}
        assert list(rows) == ["launch-runtime", "foreign-runtime"]
        assert rows["launch-runtime"]["profile_home"] == str(launch.resolve())
        assert rows["launch-runtime"]["profile_name"] == expected
        assert rows["foreign-runtime"]["profile_home"] == str(foreign.resolve())
        assert rows["foreign-runtime"]["profile_name"] == "foreign"
        assert {row["stored_session_id"] for row in rows.values()} == {"same-stored"}
        hints = []
        monkeypatch.setattr(server, "_broadcast_global_event", lambda kind, payload: hints.append((kind, payload)))
        launch_session = server._sessions["launch-runtime"]
        launch_session["running"] = True
        server._publish_session_running("launch-runtime", launch_session)
        assert hints[-1][0] == "sessions.changed"
        assert hints[-1][1]["profile_home"] == rows["launch-runtime"]["profile_home"]
        assert hints[-1][1]["profile_name"] == rows["launch-runtime"]["profile_name"]
        assert server._current_profile_name() == "foreign"  # no mutation of the caller's scope
    finally:
        reset_hermes_home_override(token)
