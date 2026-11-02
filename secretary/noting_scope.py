"""Bind Secretary background/request policy reads to the owning state.db profile."""

from contextlib import contextmanager
import logging
from pathlib import Path
import threading
from weakref import WeakValueDictionary

logger = logging.getLogger(__name__)


@contextmanager
def owning_db_scope(db):
    from hermes_constants import reset_hermes_home_override, set_hermes_home_override

    path = getattr(db, "db_path", None)
    if path is None:
        raise ValueError("Secretary runtime requires an owning state.db")
    token = set_hermes_home_override(Path(path).parent)
    try:
        yield
    finally:
        reset_hermes_home_override(token)


def _conversation_idle_config(config, conversation_ref):
    """Overlay only native Idle controls for one stable Conversation, before native validation."""
    if conversation_ref is None or not isinstance(config, dict):
        return config
    noting = config.get("noting")
    idle = noting.get("idle") if isinstance(noting, dict) else None
    if not isinstance(idle, dict):
        return config
    overrides = idle.get("conversations", {})
    if not isinstance(overrides, dict):
        raise ValueError("noting.idle.conversations must be a mapping")
    if conversation_ref not in overrides:
        return config
    selected = overrides[conversation_ref]
    if not isinstance(selected, dict) or set(selected) - {"enabled", "delay_seconds", "threshold_tokens"}:
        raise ValueError("Conversation Idle override permits only enabled, delay_seconds and threshold_tokens")
    return {**config, "noting": {**noting, "idle": {**idle, **selected}}}


def settings_for_db(db, conversation_ref=None):
    from secretary.noting_policy import disabled_noting_settings, resolve_noting_settings, noting_settings_from_config

    try:
        with owning_db_scope(db):
            if conversation_ref is None:
                return resolve_noting_settings()
            from hermes_cli.config import load_config_readonly
            from hermes_cli.config_read_errors import FailedConfigRead
            config = load_config_readonly()
            if isinstance(config, FailedConfigRead):
                return disabled_noting_settings()
            return noting_settings_from_config(_conversation_idle_config(config, conversation_ref))
    except Exception:
        logger.debug("Owning-profile Noting policy unavailable", exc_info=True)
        return disabled_noting_settings()


def scheduler_settings_for_db(db):
    """Resolve independent Scheduler policy in the owning database profile."""
    from secretary.noting_policy import disabled_scheduler_settings, resolve_scheduler_settings

    try:
        with owning_db_scope(db):
            return resolve_scheduler_settings()
    except Exception:
        logger.debug("Owning-profile Scheduler policy unavailable", exc_info=True)
        return disabled_scheduler_settings()


# Read-only associations with existing main Agents, not durable capability state. A cold
# host must resolve its normal target main runtime before scanning/admitting Secretary work.
_main_runtimes = WeakValueDictionary()
_main_runtime_lock = threading.RLock()


def _runtime_key(db, conversation_ref):
    return str(Path(db.db_path).resolve()), conversation_ref


def bind_main_runtime(agent):
    """Remember a proven main runtime at its existing construction/Turn/Idle boundary."""
    from secretary.noting_runtime import is_main_conversation_agent

    if (getattr(agent, "_persist_disabled", False)
            or getattr(agent, "_secretary_parent_closed", False) or not is_main_conversation_agent(agent)):
        return False
    db = agent._session_db
    ref = getattr(agent, "_secretary_conversation_ref", None)
    if not ref:
        return False
    try:
        with _main_runtime_lock:
            if getattr(agent, "_secretary_parent_closed", False):
                return False
            key = _runtime_key(db, ref)
            agent._secretary_main_runtime_binding = (db, ref, key)
            _main_runtimes[key] = agent
        from secretary.noting_cache_owner import recover_dead_tasks
        recover_dead_tasks(db, ref)
        from secretary.noting_notes import check_note_delivery
        check_note_delivery(agent)
        return True
    except TypeError:
        return False  # Scripted runtimes without lifetime ownership are not proof.


def is_current_main_runtime(parent):
    """Read only the exact construction/attach owner; safe under host session locks."""
    db = getattr(parent, "_session_db", None)
    ref = getattr(parent, "_secretary_conversation_ref", None)
    if db is None or not ref or getattr(parent, "_secretary_parent_closed", False):
        return False
    binding = getattr(parent, "_secretary_main_runtime_binding", None)
    if binding is None or binding[0] is not db or binding[1] != ref:
        return False
    with _main_runtime_lock:
        return _main_runtimes.get(binding[2]) is parent


def runtime_configuration_failure(db, conversation_ref):
    """Consume only the current owner's Hermes-resolved pair; unknown capability fails closed."""
    from secretary.noting_policy import force_thresholds

    agent = _main_runtimes.get(_runtime_key(db, conversation_ref))
    if agent is None or getattr(agent, "_secretary_conversation_ref", None) != conversation_ref:
        from secretary.noting_capability import cold_configuration_failure
        return cold_configuration_failure(db, conversation_ref)
    try:
        with db._read_ctx() as conn:
            route = db.resolve_conversation_route_conn(conn, conversation_ref)
        if not route or route["id"] != agent.session_id:
            return "runtime_unresolved"
        compressor = agent.context_compressor
        return force_thresholds(compressor.context_length, compressor.threshold_tokens).capability_failure or ""
    except (AttributeError, TypeError, ValueError):
        return "runtime_unresolved"


def current_main_runtime(db, conversation_ref):
    with _main_runtime_lock:
        return _main_runtimes.get(_runtime_key(db, conversation_ref))
