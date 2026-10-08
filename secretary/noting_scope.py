"""Bind Secretary background/request policy reads to the owning state.db profile."""

from contextlib import contextmanager
import logging
from pathlib import Path
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


def settings_for_db(db):
    from secretary.noting_policy import disabled_noting_settings, resolve_noting_settings

    try:
        with owning_db_scope(db):
            return resolve_noting_settings()
    except Exception:
        logger.debug("Owning-profile Noting policy unavailable", exc_info=True)
        return disabled_noting_settings()


# Read-only associations with existing main Agents, not durable capability state. A cold
# host must resolve its normal target main runtime before scanning/admitting Secretary work.
_main_runtimes = WeakValueDictionary()


def _runtime_key(db, conversation_ref):
    return str(Path(db.db_path).resolve()), conversation_ref


def bind_main_runtime(agent):
    """Remember a proven main runtime at its existing construction/Turn/Idle boundary."""
    from secretary.noting_runtime import is_main_conversation_agent

    if not is_main_conversation_agent(agent):
        return False
    db = agent._session_db
    ref = getattr(agent, "_secretary_conversation_ref", None)
    if not ref:
        return False
    try:
        _main_runtimes[_runtime_key(db, ref)] = agent
        return True
    except TypeError:
        return False  # Scripted runtimes without lifetime ownership are not proof.


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
