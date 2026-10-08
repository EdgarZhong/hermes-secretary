"""Idle checks on existing host ticks, always against the live Parent's owning profile."""

import contextlib
import logging
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def poll_parent_idle(parent):
    from secretary.noting_runtime import _main_conversation_ref, is_main_conversation_agent, maybe_run_idle_noting
    from secretary.noting_scope import owning_db_scope

    if not is_main_conversation_agent(parent):
        return "skip:not_main"
    db = parent._session_db
    with owning_db_scope(db):
        ref = _main_conversation_ref(parent)
        if not ref:
            return "skip:no_ref"
        return maybe_run_idle_noting(parent, db, ref)


def poll_cli_noting(cli):
    """The existing CLI queue-empty tick calls this; no daemon or new scheduler."""
    if getattr(cli, "_agent_running", False):
        return
    now = time.monotonic()
    if now < getattr(cli, "_secretary_noting_next_poll", 0.0):
        return
    cli._secretary_noting_next_poll = now + 5.0
    try:
        poll_parent_idle(getattr(cli, "agent", None))
    except Exception:
        logger.debug("CLI Noting idle check failed", exc_info=True)


async def poll_gateway_noting(runner):
    """Reuse messaging housekeeping; preserve profile runtime scope on the copied-context worker."""
    from gateway.secretary_reminders import _delivery_scope, _run_blocking
    from gateway.run_agent_cache import _first_agent

    lock = getattr(runner, "_agent_cache_lock", None)
    with lock if lock is not None else contextlib.nullcontext():
        entries = list((getattr(runner, "_agent_cache", None) or {}).values())
    seen = set()
    for entry in entries:
        parent = _first_agent(entry)
        if parent is None or id(parent) in seen:
            continue
        seen.add(id(parent))
        db = getattr(parent, "_session_db", None)
        if getattr(db, "db_path", None) is None:
            continue
        try:
            async with _delivery_scope(Path(db.db_path).parent):
                await _run_blocking(runner, poll_parent_idle, parent)
        except Exception:
            logger.debug("Gateway Noting idle check failed", exc_info=True)
