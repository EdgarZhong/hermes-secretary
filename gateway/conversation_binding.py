"""Explicit messaging ingress bindings to durable Conversations, independent of runtimes."""

import json

from hermes_state_common import _BOUNDARY_END_REASONS, _RECOVERABLE_END_REASONS

BINDING_KEY = "conversation_binding"
_RUNTIME_ENDS = frozenset(_RECOVERABLE_END_REASONS) | {"ws_disconnect", "idle_timeout", "lru_evict", "tui_shutdown"}


def is_bound(entry):
    return isinstance(getattr(entry, "metadata", None), dict) and BINDING_KEY in entry.metadata


def restore_binding(store, entry):
    """Resolve only an explicitly bound Conversation; never substitute a peer's other chat."""
    if not is_bound(entry):
        return False
    binding = entry.metadata[BINDING_KEY]
    ref = binding.get("conversation_ref") if isinstance(binding, dict) else None
    db = store._db_for_key(entry.session_key)
    if not ref or db is None:
        raise ValueError("Bound Conversation storage is unavailable")
    row = db.resolve_conversation_route(ref)
    if not row or row.get("archived") or row.get("end_reason") in _BOUNDARY_END_REASONS:
        raise ValueError("Bound Conversation is unavailable; explicitly select or unbind it")
    reason = row.get("end_reason")
    if reason and reason not in _RUNTIME_ENDS:
        raise ValueError("Bound Conversation was explicitly ended")
    from secretary.noting_runtime import _CHILD_SOURCES, _delegate_child_row
    if row.get("source") in _CHILD_SOURCES or _delegate_child_row(row):
        raise ValueError("Only a Main Conversation can be bound")
    config = row.get("model_config") or {}
    config = json.loads(config) if isinstance(config, str) else config
    from gateway.session import sanitize_model_override
    route = config.get("gateway_runtime") or {}
    override = sanitize_model_override({
        "model": config.get("model") or row.get("model"),
        "provider": config.get("provider") or route.get("provider"),
        "base_url": config.get("base_url") or route.get("base_url"),
    })
    changed = entry.session_id != row["id"] or entry.model_override != (override or None)
    entry.session_id, entry.model_override = row["id"], override or None
    if reason:
        db.reopen_session(row["id"])
    return changed


def bind_conversation(store, session_key, session_id):
    """Explicit host operation. Call while ingress is stopped or through its owning store."""
    store._ensure_loaded()
    db = store._db_for_key(session_key)
    if db is None:
        raise ValueError("Conversation storage is unavailable")
    ref = db.resolve_conversation_ref(session_id)
    with store._lock:
        entry = store._entries.get(session_key)
        if entry is None:
            raise ValueError("Messaging route does not exist")
        old_metadata = dict(entry.metadata or {})
        old_id, old_override = entry.session_id, entry.model_override
        entry.metadata = {**old_metadata, BINDING_KEY: {"conversation_ref": ref}}
        try:
            restore_binding(store, entry)
        except Exception:
            entry.metadata, entry.session_id, entry.model_override = old_metadata, old_id, old_override
            raise
    store._save_entries()
    return entry
