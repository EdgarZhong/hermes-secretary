"""Cold Context restoration keeps native Session/profile and current model ownership."""

import pytest

from agent.usage_anchor import capture_usage_anchor
from hermes_state_registry import acquire
from tui_gateway import server


HISTORY = [{"role": "user", "content": "same text"}]


def _profile_db(home, tokens, *, limit=100000, model="model-a", anchor_model="model-a"):
    home.mkdir()
    (home / "config.yaml").write_text(
        f"model:\n  default: {model}\n  context_length: {limit}\n", encoding="utf-8",
    )
    db = acquire(home / "state.db")
    db.create_session("same-id", source="cli")
    db.patch_session_model_config("same-id", {
        "model": model,
        "_usage_anchor": capture_usage_anchor(tokens, 20, HISTORY, model=anchor_model),
    })
    return db


@pytest.fixture
def homes(tmp_path, monkeypatch):
    launch_home, target_home = tmp_path / "launch", tmp_path / "foreign"
    launch = _profile_db(launch_home, 1000, limit=100000)
    target = _profile_db(target_home, 9000, limit=20000)
    monkeypatch.setenv("HERMES_HOME", str(launch_home))
    monkeypatch.setattr(server, "_hermes_home", str(launch_home))
    monkeypatch.setattr(server, "_get_db", lambda: launch)
    try:
        yield launch, target, launch_home, target_home
    finally:
        launch.close()
        target.close()


def _session(home=None, **extra):
    return {"agent": None, "history": list(HISTORY), "session_key": "same-id",
            **({"profile_home": str(home)} if home else {}), **extra}


def test_cold_context_uses_owning_profile_database(homes):
    _launch, _target, _launch_home, target_home = homes

    result = server._session_usage_snapshot(_session(target_home))

    assert result["context_used"] == 9020
    assert result["context_max"] == 20000


def test_cold_context_honors_current_session_model_override(homes):
    _launch, _target, launch_home, _target_home = homes
    session = _session(launch_home, model_override={"model": "model-b", "provider": "custom"})
    assert server._live_session_identity(session)[0] == "model-b"

    assert server._session_usage_snapshot(session) == {}
