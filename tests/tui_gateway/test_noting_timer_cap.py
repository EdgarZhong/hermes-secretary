"""Session-cap eviction prefers armed Noting owners, without making them exempt."""

import time

pytest_plugins = ("tests.tui_gateway.test_protocol",)


def test_cap_sorts_idle_timers_last_but_can_reap_them(server, monkeypatch, tmp_path):
    from secretary.noting_timers import arm_idle_timer, cancel_idle_timer
    from tests.hermes_state._secretary_noting_harness import make, open_noting_db
    from tests.secretary.test_noting_runtime import _agent

    db = open_noting_db(tmp_path / "state.db")
    make(db, "timer")
    parent = _agent(db, "timer")
    arm_idle_timer(parent, db, parent._secretary_conversation_ref, time.time() + 60)
    evicted = []
    monkeypatch.setattr(server, "_max_live_sessions", lambda: 1)
    monkeypatch.setattr(server, "_session_is_lru_evictable", lambda *args: True)
    def close(sid, **kwargs):
        evicted.append(sid)
        server._sessions.pop(sid, None)
    monkeypatch.setattr(server, "_close_session_by_id", close)
    try:
        server._sessions.clear()
        server._sessions.update({
            "timer": {"agent": parent, "last_active": 1},
            "ordinary": {"last_active": 20},
            "other": {"last_active": 30},
        })
        server._enforce_session_cap()
        assert evicted == ["ordinary", "other"]
        server._sessions["older_timer"] = {"agent": parent, "last_active": 0}
        server._enforce_session_cap()
        assert evicted[-1] == "older_timer"
    finally:
        cancel_idle_timer(db, parent._secretary_conversation_ref)
        server._sessions.clear()
        db.close()
