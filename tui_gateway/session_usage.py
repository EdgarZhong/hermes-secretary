"""Cold Session usage restoration through native profile and SessionDB owners.

Helpers are rebound onto server.py, preserving the facade's public/patchable seams.
"""

from .method_ctx import bind_module


def _restored_cold_usage(session: dict) -> dict:
    """Reuse a matching persisted usage anchor as a cold Context estimate.

    Native anchor accounting includes the provider's previous prompt/completion count and a
    rough delta for appended messages. This is not a fresh provider occupancy measurement.
    """
    history = session.get("history")
    stored_id = str(session.get("stored_session_id") or session.get("session_key") or "")
    if not stored_id or not isinstance(history, list) or not history:
        return {}
    try:
        with _session_profile_runtime_scope(session, hydrate_secrets=False), _session_db(session) as db:
            if db is None:
                return {}
            model, _provider = _live_session_identity(session)
            if not model:
                getter = getattr(db, "get_session_model_config_value", None)
                model = str(getter(stored_id, "model", "") or "") if callable(getter) else ""
            from agent.usage_anchor import persisted_anchor_context

            context = persisted_anchor_context(db, stored_id, history, model=model)
            if not context or context.get("model_matches") is False:
                return {}
            used = int(context["tokens"])
            # The anchor describes Context, never session-lifetime totals. Preserve the
            # existing empty-session counter shape; native persisted totals have their own path.
            usage = {
                "calls": 0, "input": 0, "output": 0, "total": 0,
                "context_used": used,
                "context_estimated": True, "context_source": "usage_anchor",
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
