"""Cold Context restoration keeps native Session/profile and current model ownership."""

from types import SimpleNamespace

import pytest

from agent.usage_anchor import capture_usage_anchor, set_usage_anchor
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

    assert server._session_usage_snapshot(session) == {
        "context_invalidated": True, "context_invalidation_reason": "model_changed",
    }


def _persist_reading(db, session_id="same-id"):
    db.append_message(session_id, "user", "same text")
    history = db.get_messages_as_conversation(session_id)
    agent = SimpleNamespace(session_id=session_id, _session_db=db)
    set_usage_anchor(agent, capture_usage_anchor(9000, 20, history, model="model-a"))
    return agent


def test_cold_context_restores_without_loading_deferred_history(homes, monkeypatch):
    _launch, target, _launch_home, target_home = homes
    _persist_reading(target)
    monkeypatch.setattr(target, "get_messages_as_conversation", lambda *a, **k: pytest.fail("history was loaded"))

    result = server._session_usage_snapshot(_session(target_home, history=None))

    assert result["context_used"] == 9020
    assert result["context_estimated"] is True
    assert result["context_max"] == 20000


def test_cold_context_survives_compaction_anchor_clear_and_disk_reopen(homes):
    from hermes_state import SessionDB

    _launch, target, _launch_home, target_home = homes
    agent = _persist_reading(target)
    target.replace_messages("same-id", [{"role": "user", "content": "native summary handoff"}])
    set_usage_anchor(agent, None, context_estimate=41914)
    assert target.get_session_model_config_value("same-id", "_usage_anchor") is None
    target.close()
    reopened = SessionDB(db_path=target_home / "state.db")
    try:
        assert reopened.get_session("same-id")["rewind_count"] == 0
        result = server._session_usage_snapshot(_session(target_home, history=None))
        assert result["context_used"] == 41914
        assert result["context_source"] == "local_estimate"
    finally:
        reopened.close()


def test_cold_context_same_model_restores_after_database_reopen(homes):
    from hermes_state import SessionDB

    _launch, target, _launch_home, target_home = homes
    _persist_reading(target)
    target.close()
    reopened = SessionDB(db_path=target_home / "state.db")
    try:
        assert reopened.get_session_model_config_value("same-id", "_usage_anchor") is not None
        assert server._session_usage_snapshot(_session(target_home, history=None))["context_used"] == 9020
    finally:
        reopened.close()


def test_cold_context_retains_native_reading_when_replay_prefix_changes(homes):
    _launch, target, _launch_home, target_home = homes
    _persist_reading(target)

    result = server._session_usage_snapshot(_session(target_home, history=[{"role": "user", "content": "replayed"}]))

    assert result["context_used"] == 9020


def test_cold_context_rewind_invalidates_even_if_priced_prefix_survives(homes):
    _launch, target, _launch_home, target_home = homes
    _persist_reading(target)
    target.append_message("same-id", "assistant", "priced reply")
    target.append_message("same-id", "user", "later turn")
    target.rewind_user_turn("same-id", 1)
    history = target.get_messages_as_conversation("same-id")

    assert server._session_usage_snapshot(_session(target_home, history=history)) == {
        "context_invalidated": True, "context_invalidation_reason": "rewind",
    }


def test_cold_context_compaction_estimate_still_rejects_model_switch(homes):
    _launch, target, _launch_home, target_home = homes
    set_usage_anchor(_persist_reading(target), None)

    result = server._session_usage_snapshot(_session(
        target_home, history=None, model_override={"model": "model-b", "provider": "custom"},
    ))

    assert result == {"context_invalidated": True, "context_invalidation_reason": "model_changed"}


def test_cold_context_does_not_reuse_another_session_reading(homes):
    _launch, target, _launch_home, target_home = homes
    set_usage_anchor(_persist_reading(target), None)
    target.create_session("other-id", source="cli")

    assert server._session_usage_snapshot(_session(target_home, session_key="other-id", history=None)) == {}


def test_native_context_retention_failure_preserves_the_existing_response(monkeypatch):
    from unittest.mock import Mock
    import agent.usage_anchor as usage_anchor

    saver = Mock(side_effect=RuntimeError("storage unavailable"))
    monkeypatch.setattr(usage_anchor, "persist_context_estimate", saver)
    payload = {"context_used": 1234, "context_source": "local_estimate", "categories": []}

    assert server._retain_context_breakdown_estimate(object(), payload) is payload
    saver.assert_called_once()


@pytest.mark.parametrize("payload", [
    {"context_used": 1234, "context_source": "provider_usage"},
    {"context_source": "local_estimate"},
    {"context_used": True, "context_source": "local_estimate"},
    {"context_used": -1, "context_source": "local_estimate"},
])
def test_context_retention_only_saves_valid_native_rough_readings(monkeypatch, payload):
    from unittest.mock import Mock
    import agent.usage_anchor as usage_anchor

    saver = Mock()
    monkeypatch.setattr(usage_anchor, "persist_context_estimate", saver)

    assert server._retain_context_breakdown_estimate(object(), payload) is payload
    saver.assert_not_called()


@pytest.mark.parametrize("reason", ["model_changed", "rewind"])
def test_rough_breakdown_does_not_revive_an_invalidated_reading(homes, reason):
    _launch, target, _launch_home, _target_home = homes
    agent = _persist_reading(target)
    agent.model = "model-b" if reason == "model_changed" else "model-a"
    if reason == "rewind":
        target.rewind_user_turn("same-id", 0)
    before = target.get_session_model_config_value("same-id", "_usage_context")
    payload = {"context_used": 1234, "context_source": "local_estimate"}

    assert server._retain_context_breakdown_estimate(agent, payload) is payload
    assert payload["context_used"] == 1234
    assert payload["context_available"] is False
    assert payload["context_invalidation_reason"] == reason
    assert target.get_session_model_config_value("same-id", "_usage_context") == before
    # A new real provider reading, unlike a rough breakdown poll, re-establishes the readout.
    history = [{"role": "user", "content": "new provider-priced request"}]
    set_usage_anchor(agent, capture_usage_anchor(2000, 20, history, model=agent.model))
    restored = server._retain_context_breakdown_estimate(agent, {"context_used": 2020, "context_source": "provider_usage"})
    assert "context_invalidated" not in restored


def test_cold_breakdown_preserves_legacy_numbers_with_optional_availability(homes):
    _launch, target, _launch_home, target_home = homes
    target.create_session("other-id", source="cli")

    empty = server._cold_context_breakdown(_session(target_home, session_key="other-id", history=None))

    assert empty["context_used"] == empty["context_max"] == empty["context_percent"] == 0
    assert empty["context_available"] is False
    assert "context_invalidated" not in empty
    _persist_reading(target)
    restored = server._cold_context_breakdown(_session(target_home, history=None))
    assert restored["context_used"] == 9020
    assert restored["context_available"] is True


@pytest.mark.parametrize("model_pick", [None, "override", "pending"])
def test_cold_context_breakdown_rpc_keeps_owner_and_current_model(homes, monkeypatch, model_pick):
    _launch, target, _launch_home, target_home = homes
    _persist_reading(target)
    session = _session(target_home, history=[])
    if model_pick == "override":
        session["model_override"] = {"model": "model-b", "provider": "custom"}
    elif model_pick == "pending":
        session["pending_model_switch"] = {"display_model": "model-b", "display_provider": "custom"}
    monkeypatch.setitem(server._sessions, "cold-owner-rpc", session)

    response = server.handle_request({"id": "breakdown", "method": "session.context_breakdown",
                                    "params": {"session_id": "cold-owner-rpc"}})

    assert "error" not in response, response
    result = response["result"]
    assert session["agent"] is None
    if model_pick is None:
        assert result["context_available"] is True
        assert result["context_used"] == 9020
        assert result["context_max"] == 20000
        assert result["context_estimated"] is True
    else:
        assert result["context_available"] is False
        assert result["context_invalidated"] is True
        assert result["context_invalidation_reason"] == "model_changed"
