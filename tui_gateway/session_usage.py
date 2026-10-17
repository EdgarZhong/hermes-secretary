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
        "model": _metadata_mirror(session).get("model", ""),
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
            limit = _configured_context_length()
            if limit > 0:
                usage["context_max"] = limit
                usage["context_percent"] = max(0, min(100, round(used / limit * 100)))
            return usage
    except Exception:
        logger.debug("cold session usage restore failed", exc_info=True)
        return {}


def _configured_context_length() -> int:
    """The scoped profile's declared ``model.context_length``, or 0 if undeclared/unreadable."""
    try:
        from hermes_cli.config import load_config_readonly

        model = (load_config_readonly() or {}).get("model")
        value = model.get("context_length") if isinstance(model, dict) else None
        return int(value) if isinstance(value, int) and not isinstance(value, bool) and value > 0 else 0
    except Exception:
        logger.debug("configured context length read failed", exc_info=True)
        return 0


def register(server) -> None:
    """Publish helpers onto the existing facade without a module-level server import."""
    bind_module(globals(), server)
