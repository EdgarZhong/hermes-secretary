"""Read native Conversation model identity and compatibility without selecting a model."""
from __future__ import annotations

import hashlib
import json


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, allow_nan=False, default=str).encode()).hexdigest()


def parent_contract(parent):
    compressor = getattr(parent, "context_compressor", None)
    return {"provider": getattr(parent, "requested_provider", None) or getattr(parent, "provider", None),
            "model": getattr(parent, "model", None),
            "context_length": getattr(compressor, "context_length", None),
            "threshold_tokens": getattr(compressor, "threshold_tokens", None),
            "api_mode": getattr(parent, "api_mode", None) or "chat_completions",
            "reasoning_config": getattr(parent, "reasoning_config", None),
            "reasoning_effort": getattr(parent, "reasoning_effort", None),
            "service_tier": getattr(parent, "service_tier", None),
            "fast_mode": getattr(parent, "fast_mode", None),
            "capabilities": getattr(parent, "capabilities", None) or {}}


def _stored_contract(db, row, config):
    """Consume native persisted selection, never substitute the profile's default pick."""
    from hermes_state_sessions import _parse_model_config
    from secretary.noting_capability import _native_pair
    raw = _parse_model_config(row.get("model_config"))
    # Native resume restores model/provider/reasoning, not historical row-level
    # context_length/max_tokens fields. Window pins remain native route-scoped
    # config (model/custom-provider/model_overrides) and current metadata.
    route = db.session_gateway_runtime(row)
    model = row.get("model") or raw.get("model")
    provider = route.get("requested_provider") or route.get("provider")
    if not model or not provider:
        return None
    # Follow-profile rows need the native host to resolve/prime the new selection first.
    if raw.get("follow_profile_config") or raw.get("room_plumbing"):
        return None
    # Match native stored-session resume's route fields. Arbitrary historical
    # gateway_runtime members (notably max_tokens) are not current host receipts.
    runtime = {name: route.get(name) for name in ("provider", "base_url", "api_mode")}
    runtime["provider"] = runtime["provider"] or provider
    # Re-evaluate through the native factory on every cold read. Its metadata sources
    # own their caches/refresh rules; an extra pair memo would hide those updates.
    # Passing no DB keeps plugin state binding out of the caller's write transaction.
    pair = _native_pair(None, row["id"], config, model, runtime)
    return {"provider": provider, "model": model, "context_length": pair[0],
            "threshold_tokens": pair[1], "api_mode": route.get("api_mode") or "chat_completions",
            "reasoning_config": raw.get("reasoning_config"), "reasoning_effort": raw.get("reasoning_effort"),
            "service_tier": raw.get("service_tier"), "fast_mode": raw.get("fast_mode"),
            "capabilities": raw.get("capabilities") or {}}


def resolve_contract(db, ref, config, *, parent=None, session_id=None, conn=None):
    from secretary.heartbeat_route import heartbeat_route_conn
    from secretary.noting_scope import current_main_runtime
    if conn is None:
        with db._read_ctx() as connection:
            return resolve_contract(db, ref, config, parent=parent, session_id=session_id, conn=connection)
    row = heartbeat_route_conn(db, conn, ref)
    if not row:
        return None
    if session_id is not None:
        binding = conn.execute("SELECT conversation_ref FROM secretary_session_bindings WHERE session_id=?",
                               (session_id,)).fetchone()
        if binding is None or binding[0] != ref:
            return None
    candidate = parent if parent is not None else current_main_runtime(db, ref)
    if (candidate is not None and getattr(candidate, "session_id", None) == row["id"]
            and not getattr(candidate, "_secretary_parent_closed", False)):
        return parent_contract(candidate)
    if parent is not None:
        return None
    return _stored_contract(db, row, config)
