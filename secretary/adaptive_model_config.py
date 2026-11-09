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


def _configured_window(config, model, runtime):
    from types import SimpleNamespace
    from agent.agent_init import config_context_length_for_runtime
    from agent.model_metadata import _config_override_context_length
    from hermes_cli.config import get_compatible_custom_providers, get_custom_provider_context_length
    identity = SimpleNamespace(model=model, provider=runtime["provider"], base_url=runtime.get("base_url") or "")
    custom = get_compatible_custom_providers(config)
    return (config_context_length_for_runtime(identity, config)
            or get_custom_provider_context_length(model=model, base_url=identity.base_url, custom_providers=custom)
            or _config_override_context_length(model, identity.base_url, identity.provider, custom))


def _codex_window(model, runtime, *, allow_network):
    """Read the native same-profile credential and catalog; never retain a token here."""
    from agent import model_metadata as metadata
    from hermes_cli.auth import resolve_codex_runtime_credentials
    if runtime["provider"] != "openai-codex":
        return None  # A custom gateway needs its own host's proven runtime, not this account's token.
    auth = resolve_codex_runtime_credentials(read_only=True)
    base = str(auth.get("base_url") or "").rstrip("/")
    stored_base = str(runtime.get("base_url") or "").rstrip("/")
    if stored_base and stored_base != base:
        return None  # Never send one route's credential to another persisted endpoint.
    token = auth.get("api_key")
    if not token:
        return None
    window, source = metadata._resolve_codex_oauth_context_length_with_source(
        model, access_token=token, base_url=base, allow_network=allow_network)
    return window if source in {"live", "memory"} else None


def _stored_contract(db, row, config, *, allow_network=False):
    """Consume native persisted selection, never substitute the profile's default pick."""
    from hermes_state_sessions import _parse_model_config
    from secretary.noting_capability import _native_pair
    from agent.model_metadata import _is_codex_route
    from hermes_cli.config import get_compatible_custom_providers
    raw = _parse_model_config(row.get("model_config"))
    route = db.session_gateway_runtime(row)
    model = row.get("model") or raw.get("model")
    provider = route.get("requested_provider") or route.get("provider")
    if not model or not provider or raw.get("follow_profile_config") or raw.get("room_plumbing"):
        return None
    runtime = {name: route.get(name) for name in ("provider", "base_url", "api_mode")}
    runtime["provider"] = runtime["provider"] or provider
    # Native resume does not restore historical row context_length/max_tokens fields.
    window = _configured_window(config, model, runtime)
    codex = _is_codex_route(runtime["provider"], runtime.get("base_url") or "",
                            get_compatible_custom_providers(config))
    if window is None and codex:
        window = _codex_window(model, runtime, allow_network=allow_network)
        if window is None:
            return None
    if window is None and not allow_network:
        return None  # Cold transactional reads never probe an endpoint or invent a static contract.
    pair = _native_pair(None, row["id"], config, model, runtime, resolved_context_length=window)
    return {"provider": provider, "model": model, "context_length": pair[0],
            "threshold_tokens": pair[1], "api_mode": route.get("api_mode") or "chat_completions",
            "reasoning_config": raw.get("reasoning_config"), "reasoning_effort": raw.get("reasoning_effort"),
            "service_tier": raw.get("service_tier"), "fast_mode": raw.get("fast_mode"),
            "capabilities": raw.get("capabilities") or {}}


def _target(db, ref, session_id, conn):
    from secretary.heartbeat_route import heartbeat_route_conn
    row = heartbeat_route_conn(db, conn, ref)
    if row and session_id is not None:
        binding = conn.execute("SELECT conversation_ref FROM secretary_session_bindings WHERE session_id=?",
                               (session_id,)).fetchone()
        if binding is None or binding[0] != ref:
            return None
    return row


def _parent_contract(db, ref, row, parent):
    from secretary.noting_scope import current_main_runtime
    candidate = parent if parent is not None else current_main_runtime(db, ref)
    if (candidate is not None and row and getattr(candidate, "session_id", None) == row["id"]
            and not getattr(candidate, "_secretary_parent_closed", False)):
        return parent_contract(candidate)
    return None


def resolve_contract(db, ref, config, *, parent=None, session_id=None, conn=None):
    if conn is not None:
        row = _target(db, ref, session_id, conn)
        actual = _parent_contract(db, ref, row, parent)
        return actual or (_stored_contract(db, row, config) if row and parent is None else None)
    with db._read_ctx() as connection:
        row = _target(db, ref, session_id, connection)
        actual = _parent_contract(db, ref, row, parent)
    if actual or not row or parent is not None:
        return actual
    # Credential reads / native catalog HTTP occur only after releasing the database context.
    result = _stored_contract(db, row, config, allow_network=True)
    from hermes_cli.config import load_config_readonly
    if digest(load_config_readonly()) != digest(config):
        return None
    with db._read_ctx() as connection:
        current = _target(db, ref, session_id, connection)
        if current != row:
            return None
        actual = _parent_contract(db, ref, current, parent)
    return actual or result


def cache_contract(contract, *, base_url=None):
    """Cache identity excludes prices/capacity and never exposes route credentials."""
    value = {key: contract.get(key) for key in
             ('provider', 'model', 'api_mode', 'reasoning_config', 'reasoning_effort')}
    if base_url:
        from hermes_cli.route_identity import normalize_route_base_url
        value['route_fingerprint'] = digest(normalize_route_base_url(str(base_url)))
    elif contract.get('route_fingerprint'):
        value['route_fingerprint'] = contract['route_fingerprint']
    return value


def resolve_cache_contract(db, ref, *, parent=None, session_id=None, conn):
    """Read the current native selection without capability lookup or network I/O."""
    row = _target(db, ref, session_id, conn)
    if not row:
        return None
    if parent is not None:
        actual = _parent_contract(db, ref, row, parent)
        return cache_contract(actual, base_url=getattr(parent, 'base_url', None)) if actual else None
    from hermes_state_sessions import _parse_model_config
    raw = _parse_model_config(row.get('model_config'))
    route = db.session_gateway_runtime(row)
    model = row.get('model') or raw.get('model')
    provider = route.get('requested_provider') or route.get('provider')
    if not model or not provider or raw.get('follow_profile_config') or raw.get('room_plumbing'):
        return None
    value = dict(provider=provider, model=model, api_mode=route.get('api_mode') or 'chat_completions',
                 reasoning_config=raw.get('reasoning_config'), reasoning_effort=raw.get('reasoning_effort'))
    # Persisted settings are authoritative for an upcoming HB. A live runtime
    # that has not adopted them cannot lend its older cache identity.
    return cache_contract(value, base_url=route.get('base_url'))


def selection_is_current(db, ref, parent, *, conn):
    """Reject known persisted selection changes when adopting runtime plans.

    This does not relabel actual request receipts, construct a runtime, or gate
    ordinary Main work. Missing historical route metadata is not a change.
    """
    if parent is None:
        return True
    stored = resolve_cache_contract(db, ref, conn=conn)
    actual = resolve_cache_contract(db, ref, parent=parent, conn=conn)
    if stored is None:
        # An old row may lack a routable provider while still carrying a known
        # model/effort change. Missing fields are not evidence of compatibility.
        row = _target(db, ref, None, conn)
        if not row:
            return False
        from hermes_state_sessions import _parse_model_config
        raw = _parse_model_config(row.get('model_config'))
        if raw.get('follow_profile_config') or raw.get('room_plumbing'):
            return True
        route = db.session_gateway_runtime(row)
        stored = cache_contract(dict(provider=route.get('requested_provider') or route.get('provider'),
                                     model=row.get('model') or raw.get('model'), api_mode=route.get('api_mode'),
                                     reasoning_config=raw.get('reasoning_config'),
                                     reasoning_effort=raw.get('reasoning_effort')), base_url=route.get('base_url'))
    if actual is None:
        return False
    from hermes_cli.config import load_config_readonly
    from hermes_constants import resolve_reasoning_config
    from secretary.noting_scope import owning_db_scope
    with owning_db_scope(db):
        default = resolve_reasoning_config(load_config_readonly(), stored['model']) if stored.get('model') else None
    # Native resume inherits defaults only for None; {} is a real persisted
    # override and must not silently inherit an enabled profile effort.
    def normalized(contract):
        value = dict(contract)
        reasoning = value.get('reasoning_config')
        value['reasoning_config'] = (default if reasoning is None else reasoning) or None
        value['reasoning_effort'] = value.get('reasoning_effort') or None
        return value
    stored, actual = normalized(stored), normalized(actual)
    keys = ('provider', 'model', 'api_mode')
    return (all(stored.get(key) is None or stored[key] == actual.get(key) for key in keys)
            and all(stored.get(key) == actual.get(key) for key in ('reasoning_config', 'reasoning_effort'))
            and (not stored.get('route_fingerprint')
                 or stored['route_fingerprint'] == actual.get('route_fingerprint')))
