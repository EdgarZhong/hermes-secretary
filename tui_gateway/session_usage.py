"""Cold Session usage restoration through native profile and SessionDB owners.

Helpers are rebound onto server.py, preserving the facade's public/patchable seams.
"""

from .method_ctx import bind_module


def _retain_context_breakdown_estimate(agent, payload: dict) -> dict:
    """Keep an existing native rough readout for restart recovery without changing its response."""
    try:
        from agent.usage_anchor import persist_context_estimate, persisted_context_estimate

        previous = persisted_context_estimate(
            getattr(agent, "_session_db", None), getattr(agent, "session_id", None), model=getattr(agent, "model", None),
        )
        if previous and previous.get("invalidation_reason"):
            payload.update(context_available=False, context_invalidated=True,
                           context_invalidation_reason=previous["invalidation_reason"])
            return payload
        tokens = payload.get("context_used")
        if (payload.get("context_source") == "local_estimate" and isinstance(tokens, int)
                and not isinstance(tokens, bool) and tokens >= 0):
            persist_context_estimate(agent, tokens)
    except Exception:
        logger.debug("native context estimate retention failed", exc_info=True)
    return payload


def _cold_context_breakdown(session: dict) -> dict:
    """Preserve the existing cold response's numeric shape, with optional availability hints."""
    restored = _session_usage_snapshot(session)
    usage = restored or _get_usage(None)
    return {
        "categories": [], "context_max": usage.get("context_max", 0) or 0,
        "context_percent": usage.get("context_percent", 0) or 0, "context_used": usage.get("context_used", 0) or 0,
        "estimated_total": 0, "context_estimated": usage.get("context_estimated", False),
        "context_source": usage.get("context_source", "provider_usage"),
        "model": _live_session_identity(session)[0],
        "context_available": "context_used" in restored and not restored.get("context_invalidated", False),
        **({"context_invalidated": True, "context_invalidation_reason": restored["context_invalidation_reason"]}
           if restored.get("context_invalidated") else {}),
    }


def _restored_cold_usage(session: dict) -> dict:
    """Reuse the owning Session's persisted native reading as a cold Context estimate.

    Exact native anchors retain their delta accounting when possible; a prior display reading
    survives replay repair and compaction until a model switch or durable rewind invalidates it.
    """
    history = session.get("history")
    stored_id = str(session.get("stored_session_id") or session.get("session_key") or "")
    if not stored_id:
        return {}
    try:
        with _session_profile_runtime_scope(session, hydrate_secrets=False), _session_db(session) as db:
            if db is None:
                return {}
            model, _provider = _live_session_identity(session)
            if not model:
                getter = getattr(db, "get_session_model_config_value", None)
                model = str(getter(stored_id, "model", "") or "") if callable(getter) else ""
            from agent.usage_anchor import persisted_context_estimate

            context = persisted_context_estimate(db, stored_id, history, model=model)
            if not context:
                return {}
            if context.get("invalidation_reason"):
                return {"context_invalidated": True, "context_invalidation_reason": context["invalidation_reason"]}
            used = int(context["tokens"])
            # The anchor describes Context, never session-lifetime totals. Preserve the
            # existing empty-session counter shape; native persisted totals have their own path.
            usage = {
                "calls": 0, "input": 0, "output": 0, "total": 0,
                "context_used": used,
                "context_estimated": True, "context_source": context["source"],
            }
            limit = _restored_context_length(session, db, stored_id, model, _provider)
            if limit > 0:
                usage["context_max"] = limit
                usage["context_percent"] = max(0, min(100, round(used / limit * 100)))
            return usage
    except Exception:
        logger.debug("cold session usage restore failed", exc_info=True)
        return {}


def _restored_context_length(session, db, stored_id, model, provider) -> int:
    """Resolve the saved route's window without constructing an Agent or probing a provider."""
    try:
        from types import SimpleNamespace
        from agent.agent_init import config_context_length_for_runtime
        from agent.model_metadata import _endpoint_scoped_context_length, get_cached_context_length
        from hermes_cli.config import get_compatible_custom_providers, get_custom_provider_context_length, load_config_readonly

        config = load_config_readonly() or {}
        row = db.get_session(stored_id) or {}
        saved = _parse_model_config(row.get("model_config"), quiet=True)
        runtime = session.get("agent")
        route = saved.get("gateway_runtime") or {}
        provider = provider or saved.get("provider") or route.get("provider") or ""
        base_url = (getattr(runtime, "base_url", "") or saved.get("base_url")
                    or route.get("base_url") or "")
        identity = SimpleNamespace(model=model, provider=provider, base_url=base_url)
        pin = config_context_length_for_runtime(identity, config)
        custom = get_custom_provider_context_length(
            model=model, base_url=base_url, custom_providers=get_compatible_custom_providers(config))
        known = _endpoint_scoped_context_length(model, base_url)
        cached = get_cached_context_length(model, base_url)
        value = pin or custom or known or cached
        if not value:
            from agent.models_dev import get_model_info
            info = get_model_info(provider, model, config=config, allow_network=False)
            value = getattr(info, "context_window", None)
        return int(value) if isinstance(value, int) and not isinstance(value, bool) and value > 0 else 0
    except Exception:
        logger.debug("saved route context length read failed", exc_info=True)
        return 0


def register(server) -> None:
    """Publish helpers onto the existing facade without a module-level server import."""
    bind_module(globals(), server)
