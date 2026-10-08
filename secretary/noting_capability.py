"""Cold owner capability from the same native context-engine construction used by main Agents.

No SDK client, prompt, inference, Turn, or new Agent manager is created. The host resolves
its normal target model/provider route first; this module consumes that route inside its
owning profile and calls Hermes's existing compression/context-engine factories.
"""
import hashlib
import json
import logging

from secretary.noting_policy import configuration_guidance, force_thresholds
from secretary.noting_scope import _runtime_key, owning_db_scope

logger = logging.getLogger(__name__)
_cold_capabilities = {}


def _owner_signature(db, conversation_ref, config, model, runtime):
    with db._read_ctx() as conn:
        route = db.resolve_conversation_route_conn(conn, conversation_ref)
        bindings = tuple(tuple(row) for row in conn.execute(
            "SELECT session_id,declared_source,declared_key,declared_generation FROM secretary_session_bindings "
            "WHERE conversation_ref=? ORDER BY session_id", (conversation_ref,)))
    if not route:
        raise ValueError("Unknown Conversation owner")
    digest = hashlib.sha256(json.dumps(config, sort_keys=True, default=str).encode()).hexdigest()
    from hermes_state_common import stat_db_file_identity
    identity = (route.get("id"), bindings, route.get("source"), route.get("profile_name"), stat_db_file_identity(db.db_path))
    runtime_identity = tuple(str(runtime.get(key) or "") for key in ("provider", "api_mode", "base_url", "max_tokens"))
    return identity + (model,) + runtime_identity + (digest,)


def _native_pair(db, session_id, config, model, runtime):
    from agent.agent_init import _build_context_engine, _parse_compression_config, _resolve_context_length
    from run_agent import AIAgent

    # Same route predicate as native _ensure_lmstudio_runtime_loaded: that path can
    # activate a model. A cold capability read must wait for a real main binding.
    if str(runtime.get("provider") or "").strip().lower() == "lmstudio":
        raise ValueError("Cold LM Studio capability requires a live main runtime; native preload is not read-only")

    # Use the native class's existing context-resolution methods without running init_agent.
    # Only parsing/factory fields exist: there is no client, root prompt, or Agent loop.
    agent = AIAgent.__new__(AIAgent)
    agent.model = model
    agent.provider = runtime.get("provider")
    agent.api_mode = runtime.get("api_mode") or "chat_completions"
    agent.api_key = runtime.get("api_key") or ""
    agent.base_url = runtime.get("base_url") or ""
    agent.max_tokens = runtime.get("max_tokens")
    agent.request_overrides = dict(runtime.get("request_overrides") or {})
    agent.quiet_mode = True
    agent.session_id = session_id
    agent._session_db = db
    agent.memory_manager = None
    settings = _parse_compression_config(agent, config)
    _pin, custom, effective, _model = _resolve_context_length(agent, config, agent.base_url)
    _build_context_engine(agent, config, settings, custom, effective, db)
    compressor = agent.context_compressor
    return compressor.context_length, compressor.threshold_tokens


def prime_cold_main_capability(db, conversation_ref, model, runtime):
    """Called after the host proves its normal target route; unresolved/invalid stays closed."""
    from hermes_cli.config import load_config_readonly
    from hermes_cli.config_read_errors import FailedConfigRead
    from secretary.noting_policy import noting_settings_from_config
    from secretary.noting_runtime import noting_local_enabled
    from secretary.noting_scope import _main_runtimes

    with owning_db_scope(db):
        config = load_config_readonly()
        if isinstance(config, FailedConfigRead):
            return False
        settings = noting_settings_from_config(config)
        if not settings.enabled or not noting_local_enabled(db, conversation_ref):
            if settings.configuration_failure:
                logger.warning("%s", configuration_guidance(settings.configuration_failure))
            return False
        key = _runtime_key(db, conversation_ref)
        _main_runtimes.pop(key, None)  # The host has resolved a newer/cold target route.
        try:
            signature = _owner_signature(db, conversation_ref, config, model, runtime)
            existing = _cold_capabilities.get(key)
            if existing and existing["signature"] == signature:
                return not existing["failure"]
            window, threshold = _native_pair(db, signature[0], config, model, runtime)
            failure = force_thresholds(window, threshold).capability_failure or ""
            _cold_capabilities[key] = {"signature": signature, "model": model, "runtime": {
                name: runtime.get(name) for name in ("provider", "api_mode", "base_url", "max_tokens")},
                "failure": failure, "pair": (window, threshold)}
            if failure:
                logger.warning("%s", configuration_guidance(failure))
            return not failure
        except Exception:
            _cold_capabilities.pop(key, None)
            logger.warning("%s", configuration_guidance("runtime_unresolved"), exc_info=True)
            return False


def cold_configuration_failure(db, conversation_ref):
    from hermes_cli.config import load_config_readonly
    from hermes_cli.config_read_errors import FailedConfigRead

    entry = _cold_capabilities.get(_runtime_key(db, conversation_ref))
    if not entry:
        return "runtime_unresolved"
    with owning_db_scope(db):
        config = load_config_readonly()
        if isinstance(config, FailedConfigRead):
            return "runtime_unresolved"
        try:
            current = _owner_signature(db, conversation_ref, config, entry["model"], entry["runtime"])
            return entry["failure"] if current == entry["signature"] else "runtime_unresolved"
        except Exception:
            logger.debug("Cold capability ownership or config unavailable", exc_info=True)
            return "runtime_unresolved"
