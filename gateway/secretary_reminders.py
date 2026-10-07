"""Secretary Schedule/Reminder gateway host wiring (messaging surfaces).

One scan pass per housekeeping tick claims due ConversationScheduleRegistry rows for every
served profile's own store, then dispatches by delivery semantics:

- ``system_reminder`` (commitment / task / watchpoint due): durable pending row only — no Turn;
- ``user_reminder``: ownership-proven route, then the existing synthetic internal ingress
  (``adapter.handle_message``) whose own admission decides idle (a normal Turn) versus busy
  (the narrow policy in ``run_busy.py`` converts it to a pending System Reminder).

No Cron job, no ``cron_*`` Session, and no second main-agent busy gate are involved.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
import os
import time
from pathlib import Path

logger = logging.getLogger("gateway.run")

SCAN_INTERVAL_SECONDS = 15.0
OWNER = f"gateway:{os.getpid()}"


def _launch_home():
    from gateway.run import _hermes_home
    return Path(_hermes_home)


def _profile_homes(runner):
    try:
        from gateway.run import _cron_tick_profile_homes
        return _cron_tick_profile_homes(runner.config)
    except Exception:
        logger.debug("Secretary reminder profile enumeration failed; using the launch home", exc_info=True)
        return [("default", _launch_home())]


def _acquire_db(home):
    from hermes_state_registry import acquire
    return acquire(Path(home) / "state.db")


def _delivery_scope(home):
    """Bind the owning profile's runtime scope (home + secrets + terminal), never ambient env."""
    from gateway.run import _async_profile_runtime_scope
    if Path(home).resolve() != _launch_home().resolve():
        return _async_profile_runtime_scope(Path(home))
    from tui_gateway.launch_profile_policy import async_launch_profile_scope_if_multiplexed
    return async_launch_profile_scope_if_multiplexed()


async def _run_blocking(runner, fn, *args, **kwargs):
    """DB work off the event loop; keep the ContextVar scope on the worker when available."""
    executor = getattr(runner, "_run_in_executor_with_context", None)
    if callable(executor):
        import functools
        return await executor(functools.partial(fn, *args, **kwargs))
    return await asyncio.to_thread(fn, *args, **kwargs)


def _route_session_key(runner, conversation_ref, db):
    from secretary import reminders as secretary_reminders
    route = None
    with contextlib.suppress(Exception):
        route = secretary_reminders.active_route(db, conversation_ref)
    return str((route or {}).get("session_key") or "")


def _source_for_session_key(runner, session_key):
    """The persisted origin of a live gateway session; None fails closed (no heuristic source)."""
    if not session_key:
        return None
    try:
        runner.session_store._ensure_loaded()
        entry = runner.session_store._entries.get(session_key)
    except Exception as exc:
        logger.debug("Secretary reminder session-store lookup failed for %s: %s", session_key, exc, exc_info=True)
        return None
    if entry is None:
        return None
    with contextlib.suppress(Exception):
        return runner._restored_source(entry)
    return None


def _claim_store(db, profile):
    from secretary import schedules as secretary_schedules
    return secretary_schedules.scan_and_claim_due(
        db, owner=OWNER, profile=profile, is_enabled=secretary_schedules.default_enablement(db),
    )


async def scan_due_secretary_schedules(runner) -> int:
    """Claim and dispatch every due occurrence; returns the number dispatched this pass."""
    dispatched = 0
    for profile, home in _profile_homes(runner):
        try:
            db = _acquire_db(home)
            claims = await _run_blocking(runner, _claim_store, db, profile)
        except Exception as exc:
            logger.debug("Secretary schedule scan failed for profile %s: %s", profile, exc, exc_info=True)
            continue
        for claim in claims:
            try:
                if claim["delivery_semantics"] == "user_reminder":
                    if not _route_session_key(runner, claim["conversation_ref"], db):
                        # No live messaging session for this Conversation: keep the occurrence
                        # claimable so the surface that owns it (TUI/Web poller) delivers it.
                        await _run_blocking(runner, _release, db, claim)
                        continue
                    _spawn_delivery(runner, db, claim, profile, home)
                else:
                    from secretary import reminders as secretary_reminders
                    await _run_blocking(runner, secretary_reminders.queue_pending_for_claim, db, claim)
                dispatched += 1
            except Exception as exc:
                logger.warning("Secretary reminder dispatch failed for %s: %s", claim.get("schedule_id"), exc,
                               exc_info=True)
                with contextlib.suppress(Exception):
                    await _run_blocking(runner, _release, db, claim)
    return dispatched


def _release(db, claim):
    from secretary import reminders as secretary_reminders
    return secretary_reminders.release_claim(db, claim)


def _spawn_delivery(runner, db, claim, profile, home):
    """Deliver one active reminder off the scan path: a full Turn may run inside handle_message."""
    task = asyncio.create_task(_deliver_active_claim(runner, db, claim, profile, home))
    tasks = getattr(runner, "_secretary_delivery_tasks", None)
    if tasks is None:
        tasks = runner._secretary_delivery_tasks = set()
    tasks.add(task)
    task.add_done_callback(tasks.discard)


async def _warn_unroutable(runner, key: str, message: str) -> None:
    warned = getattr(runner, "_secretary_route_warned", None)
    if warned is None:
        warned = runner._secretary_route_warned = set()
    if key not in warned:
        warned.add(key)
        logger.warning("%s", message)


async def _deliver_active_claim(runner, db, claim, profile, home) -> None:
    from secretary import reminders as secretary_reminders

    try:
        resolved = await _run_blocking(runner, secretary_reminders.resolve_active_reminder, db, claim)
        if not resolved.get("route"):
            await _warn_unroutable(
                runner, claim["conversation_ref"],
                f"Secretary reminder route unproven for {claim['conversation_ref']}; deferring delivery",
            )
            await _run_blocking(runner, _release, db, claim)
            return
        session_key = str(resolved["route"].get("session_key") or "")
        source = _source_for_session_key(runner, session_key)
        if source is None:
            await _warn_unroutable(
                runner, claim["conversation_ref"],
                f"Secretary reminder has no live session origin ({session_key}); deferring delivery",
            )
            await _run_blocking(runner, _release, db, claim)
            return
        adapter = runner._delivery_adapter_for(source)
        if adapter is None:
            await _warn_unroutable(
                runner, claim["conversation_ref"],
                f"Secretary reminder has no delivery adapter for {session_key}; deferring delivery",
            )
            await _run_blocking(runner, _release, db, claim)
            return
        event = runner._synthetic_prompt_event(source, resolved["text"], internal=True)
        # Never let the reminder text resolve gateway commands, and never let the "gateway wake"
        # branch queue it as a future Turn when busy: the narrow busy policy converts it instead.
        event.allow_gateway_control = False
        metadata = dict(getattr(event, "metadata", None) or {})
        metadata["secretary_user_reminder"] = {
            "conversation_ref": claim["conversation_ref"],
            "schedule_id": claim["schedule_id"],
            "claim_token": claim["claim_token"],
            "source_timestamp": resolved["source_timestamp"],
            "content": resolved["content"],
        }
        event.metadata = metadata
        async with _delivery_scope(home):
            await adapter.handle_message(event)
        # The busy gate finalizes the claim itself when it converted the occurrence; a still-owned
        # claim means the ingress accepted the Turn.
        await _run_blocking(runner, secretary_reminders.finalize_claim, db, claim)
    except Exception as exc:
        logger.warning("Secretary active reminder delivery failed for %s: %s", claim.get("schedule_id"), exc,
                       exc_info=True)
        with contextlib.suppress(Exception):
            await _run_blocking(runner, _release, db, claim)


def convert_busy_reminder_event(runner, event) -> bool:
    """Narrow busy policy (§3.12): a Secretary user_reminder while busy becomes pending, not a Turn.

    Called from ``run_busy.py`` at the existing busy gate, before internal events are queued as a
    future Turn. Returns True when the event was a Secretary reminder and has been handled.
    """
    metadata = getattr(event, "metadata", None) or {}
    reminder = metadata.get("secretary_user_reminder")
    if not reminder:
        return False
    from secretary import reminders as secretary_reminders
    from hermes_state_registry import acquire

    home = None
    with contextlib.suppress(Exception):
        home = runner._resolve_profile_home_for_source(event.source)
    if home is None:
        logger.warning("Secretary busy reminder could not resolve the owning profile home")
        return True
    db = acquire(Path(home) / "state.db")
    claim = {
        "conversation_ref": reminder.get("conversation_ref"),
        "schedule_id": reminder.get("schedule_id"),
        "claim_token": reminder.get("claim_token"),
        "next_run_at": reminder.get("source_timestamp"),
        "reminder_text": reminder.get("content"),
    }
    try:
        secretary_reminders.convert_claim_to_pending(db, claim)
        logger.info(
            "Secretary user reminder converted to pending System Reminder (busy gate): %s",
            reminder.get("schedule_id"),
        )
    except Exception as exc:
        logger.warning("Secretary busy reminder conversion failed for %s: %s", reminder.get("schedule_id"), exc,
                       exc_info=True)
    return True
