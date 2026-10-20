"""An explicit binding survives runtime disposal without changing its Conversation owner."""
import pytest

from gateway.config import GatewayConfig, Platform
from gateway.conversation_binding import BINDING_KEY, bind_conversation, restore_binding
from gateway.session import SessionSource, SessionStore
from hermes_state import SessionDB


@pytest.fixture
def bound_store(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    db = SessionDB(home / "state.db")
    config = GatewayConfig()
    store = SessionStore(sessions_dir=home / "sessions", config=config)
    store._db = db
    source = SessionSource(platform=Platform.WEIXIN, chat_id="peer", user_id="peer")
    entry = store.get_or_create_session(source)
    db.create_session("imported", "pi-import", model="k3-256k", model_config={
        "model": "k3-256k", "provider": "kimi-coding", "base_url": "https://api.kimi.com/coding"})
    yield store, db, source, entry.session_key
    store.close_all_db_handles()
    db.close()


def test_bound_imported_main_survives_reap_and_store_restart(bound_store):
    store, db, source, key = bound_store
    entry = bind_conversation(store, key, "imported")
    ref = db.resolve_conversation_ref("imported")
    db.end_session("imported", "ws_orphan_reap")
    assert store.get_or_create_session(source).session_id == "imported"
    assert db.get_session("imported")["end_reason"] is None
    db.end_session("imported", "agent_close")
    restarted = SessionStore(sessions_dir=store.sessions_dir, config=store.config)
    restarted._db = db
    restored = restarted.get_or_create_session(source)
    assert restored.session_id == "imported"
    assert restored.metadata[BINDING_KEY]["conversation_ref"] == ref
    assert restored.model_override["provider"] == "kimi-coding"
    assert restored.model_override["model"] == "k3-256k"
    assert entry.origin.platform == Platform.WEIXIN


def test_adapter_peer_refresh_preserves_imported_identity(bound_store):
    store, db, source, key = bound_store
    bind_conversation(store, key, "imported")
    store._record_gateway_session_peer("imported", key, source)
    row = db.get_session("imported")
    assert row["source"] == "pi-import"
    assert not row["session_key"]


def test_explicit_end_never_falls_back_to_another_peer_conversation(bound_store):
    store, db, source, key = bound_store
    bind_conversation(store, key, "imported")
    db.end_session("imported", "session_reset")
    with pytest.raises(ValueError, match="Bound Conversation"):
        store.get_or_create_session(source)
    assert store._entries[key].session_id == "imported"
    store._prune_stale_sessions_locked()
    assert BINDING_KEY in store._entries[key].metadata


def test_binding_tracks_model_changed_from_web(bound_store):
    store, db, source, key = bound_store
    entry = bind_conversation(store, key, "imported")
    db.patch_session_model_config("imported", {"model": "deepseek-flash", "provider": "deepseek",
                                              "base_url": "https://api.deepseek.com/v1"})
    assert restore_binding(store, entry)
    assert entry.model_override["model"] == "deepseek-flash"
    assert entry.model_override["provider"] == "deepseek"


def test_bound_conversation_follows_compression_without_rebinding(bound_store):
    store, db, source, key = bound_store
    entry = bind_conversation(store, key, "imported")
    ref = db.resolve_conversation_ref("imported")
    db.end_session("imported", "compression")
    db.create_session("tip", "pi-import", parent_session_id="imported", model="k3-256k",
                      model_config={"model": "k3-256k", "provider": "kimi-coding"})
    assert store.get_or_create_session(source).session_id == "tip"
    assert entry.metadata[BINDING_KEY]["conversation_ref"] == ref
