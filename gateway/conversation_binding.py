"""Explicit messaging ingress bindings to durable Conversations, independent of runtimes."""

import json
import logging
from contextlib import nullcontext
from dataclasses import replace

from hermes_state_common import _BOUNDARY_END_REASONS, _RECOVERABLE_END_REASONS

logger = logging.getLogger(__name__)

BINDING_KEY = "conversation_binding"
_RUNTIME_ENDS = frozenset(_RECOVERABLE_END_REASONS) | {"ws_disconnect", "idle_timeout", "lru_evict", "tui_shutdown"}


def is_bound(entry):
    return isinstance(getattr(entry, "metadata", None), dict) and BINDING_KEY in entry.metadata


def agent_session_key(store, session_key, session_id):
    """Keep a bound Main's own identity key separate from its messaging ingress."""
    store._ensure_loaded()
    with store._lock:
        entry = store._entries.get(session_key)
        if not is_bound(entry):
            return session_key
        binding = entry.metadata[BINDING_KEY]
        ref = binding.get("conversation_ref") if isinstance(binding, dict) else None
        db = store._db_for_key(session_key)
        row = db.get_session(session_id) if db is not None else None
        if not ref or row is None or db.resolve_conversation_ref(session_id) != ref:
            raise ValueError("Bound Conversation does not own the Agent Session")
        # The peer key is a mutable delivery locator. Passing it to a different Main
        # would claim the peer's declared alias during native Agent initialization.
        return row.get("session_key") or None


def allows_bound_target(store, entry, session_id, *, current_tip=False):
    """True permits this owner, False rejects it, None is unavailable proof. Writers hold _lock."""
    if not is_bound(entry):
        return True
    binding = entry.metadata[BINDING_KEY]
    ref = binding.get("conversation_ref") if isinstance(binding, dict) else None
    db = store._db_for_key(entry.session_key)
    if not ref or db is None:
        return None
    try:
        if not db.get_session(session_id) or db.resolve_conversation_ref(session_id) != ref:
            return False
        route = db.resolve_conversation_route(ref) if current_tip else None
        return not current_tip or bool(route and route["id"] == session_id)
    except Exception:
        logger.debug("Bound target ownership is unavailable for %s", entry.session_key, exc_info=True)
        return None


def restore_binding(store, entry, *, lock_held=False):
    """Serialize restoration with explicit binding changes, including the database lookup."""
    with nullcontext() if lock_held else store._lock:
        return _restore_binding_locked(store, entry)


def _restore_binding_locked(store, entry):
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
        candidate = replace(entry, metadata={**(entry.metadata or {}), BINDING_KEY: {"conversation_ref": ref}})
        restore_binding(store, candidate, lock_held=True)
        store._save_entry(session_key, entry_data=candidate.to_dict(), lock_held=True, require_primary=True)
        entry.metadata = candidate.metadata
        entry.session_id, entry.model_override = candidate.session_id, candidate.model_override
    return entry


def unbind_conversation(store, source):
    """Explicit control operation: persist an independent native route before publishing it."""
    from gateway.session import SessionEntry
    from gateway.session_lifecycle import _new_session_id, _now
    store._ensure_loaded()
    key = store._generate_session_key(source)
    with store._lock:
        old = store._entry_locked(key)
        if old is None:
            raise ValueError("Messaging route does not exist")
        if not is_bound(old):
            return old
        now = _now()
        candidate = SessionEntry(
            session_key=key, session_id=_new_session_id(now), created_at=now, updated_at=now,
            origin=old.origin, display_name=old.display_name, platform=old.platform,
            chat_type=old.chat_type, transport_profile=old.transport_profile,
        )
        db = store._db_for_key(key)
        if db is None:
            raise ValueError("Conversation storage is unavailable")
        db.create_session(**store._session_create_kwargs(
            session_id=candidate.session_id, session_key=key, origin=old.origin,
            source_value=old.platform.value if old.platform else "unknown",
            display_name=old.display_name, parent_session_id=None,
        ))
        try:
            store._save_entry(key, entry_data=candidate.to_dict(), lock_held=True, require_primary=True)
        except Exception:
            try:
                db.delete_session(candidate.session_id)
            except Exception:
                logger.warning("Failed to remove unpublished unbind candidate %s", candidate.session_id, exc_info=True)
            raise
        store._entries[key] = candidate
    return candidate
