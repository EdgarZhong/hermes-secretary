"""Thin serve-owned due scan; Main execution remains with native session ingress."""

from __future__ import annotations

import contextlib
import logging
import os
from pathlib import Path
import threading

logger = logging.getLogger(__name__)
SCAN_INTERVAL_SECONDS = 5.0


def managed_profile_homes():
    from hermes_cli.profiles import profiles_to_serve
    from tui_gateway import server

    homes = {Path(home).resolve() for _name, home in profiles_to_serve(multiplex=True)}
    homes.add(Path(server._hermes_home).resolve())
    return sorted(homes)


def _local_route(db, conversation_ref):
    from secretary.reminders import active_route

    route = active_route(db, conversation_ref)
    from secretary.noting_runtime import _CHILD_SOURCES, _delegate_child_row
    from tui_gateway.session_lifecycle import _is_gateway_owned_source

    # The durable Main owns its schedule. Imported/local Main sources need no
    # browser-created runtime to become eligible; actual messaging lanes stay adapter-owned.
    if (not route or route.get("session_key") or route.get("source") in _CHILD_SOURCES
            or _is_gateway_owned_source(route.get("source", ""))):
        return None
    return None if _delegate_child_row(route) else route


def _deliver(db, claim, home, route, *, stop=None):
    from secretary import reminders
    from tui_gateway import server

    if claim["delivery_semantics"] != "user_reminder":
        reminders.queue_pending_for_claim(db, claim)
        return
    sid, session = resume_session(route["id"], home, route["source"])
    if stop is not None and stop.is_set():
        reminders.release_claim(db, claim)
        return
    server._secretary_deliver_claim(sid, session, db, claim, reminders)


def scan_profile(home, *, stop=None):
    """Claim only this host's legal routes, using their own configuration and database."""
    from hermes_state_registry import acquire, release
    from secretary import reminders, schedules
    from tui_gateway import server

    home = Path(home).resolve()
    if not (home / "state.db").is_file():
        return
    if home != Path(server._hermes_home).resolve():
        from tui_gateway.launch_profile_policy import activate_multi_profile_hosting
        activate_multi_profile_hosting()
        server._served_profile_homes.add(home)
    with server._session_profile_runtime_scope({"profile_home": str(home)}):
        db = acquire(home / "state.db")
        try:
            enabled = schedules.default_enablement(db)
            if not enabled(None):
                return
            # An adapter-owned prefix must not hide later local due work forever.
            for row in schedules.due_rows(db, limit=-1):
                if stop is not None and stop.is_set():
                    return
                route = _local_route(db, row["conversation_ref"])
                if route is None:
                    continue
                claim = schedules.claim_due(
                    db, row["schedule_id"], owner=f"serve:{os.getpid()}",
                    conversation_ref=row["conversation_ref"], expected_generation=row["generation"],
                    is_enabled=enabled,
                )
                if claim is None:
                    continue
                try:
                    _deliver(db, claim, home, route, stop=stop)
                except Exception:
                    logger.warning("Secretary reminder delivery failed home=%s ref=%s",
                                   home, row["conversation_ref"], exc_info=True)
                    with contextlib.suppress(Exception):
                        reminders.release_claim(db, claim)
        finally:
            release(db)


def scan_once(*, stop=None):
    for home in managed_profile_homes():
        if stop is not None and stop.is_set():
            return
        try:
            scan_profile(home, stop=stop)
        except Exception:
            logger.warning("Secretary reminder scan failed home=%s", home, exc_info=True)


class SchedulerHost:
    """One sequential scanner per lifespan; no client, Cron executor or model pool."""

    def __init__(self):
        from agent.memory_provider import spawn_context_thread

        self.stop_event = threading.Event()
        self.thread = spawn_context_thread(self._run, name="serve-secretary-scheduler")

    def start(self):
        self.thread.start()
        return self

    def stop(self):
        self.stop_event.set()
        self.thread.join(timeout=5.0)
        if self.thread.is_alive():
            logger.warning("Secretary scanner stopping after current native recovery finishes")

    def _run(self):
        while not self.stop_event.is_set():
            try:
                scan_once(stop=self.stop_event)
            except Exception:
                logger.warning("Secretary profile enumeration failed", exc_info=True)
            self.stop_event.wait(SCAN_INTERVAL_SECONDS)


def resume_session(target, home, source):
    from tui_gateway import server
    from tui_gateway.method_ctx import rebind

    return rebind(_resume_background_session, vars(server))(target, home, source)


def _resume_background_session(target, home, source):
    """Host-only native resume; never attach a peer or schedule a resume auto-continue."""
    from tui_gateway.transport import bind_transport, reset_transport

    class BackgroundResume(_Resume):
        background = True

        def info(self, cwd, overrides):
            return {}  # Host recovery has no client metadata to project.

    rid = "__secretary_resume__"
    ctx = BackgroundResume(rid, {"source": source, "omit_messages": True, "defer_history": True}, target)
    # The enumerator supplies a proven actual home: default is NOT the launch profile.
    ctx.profile_home = None if Path(home).resolve() == Path(_hermes_home).resolve() else Path(home)
    ctx.db, ctx.owns_db = _profile_session_db(ctx.profile_home)
    token = bind_transport(_detached_ws_transport)
    try:
        if ctx.db is None:
            raise RuntimeError("Session storage unavailable")
        if (error := _resume_locate(ctx)) is not None:
            raise RuntimeError(error)
        _resume_follow_tip(ctx)
        if (error := _resume_guard(ctx)) is not None:
            raise RuntimeError(error)
        ctx.profile_resume_cwd = (_resumable_stored_cwd(_str_param(ctx.found, "cwd"), ctx.profile_home)
                                  or _profile_workspace_cwd(ctx.profile_home))
        with _session_resume_lock:
            live = _find_live_session_by_key(ctx.target, ctx.profile_home)
        if live is not None:
            sid, _session = live
        else:
            response = _resume_deferred(ctx)
            if "error" in response:
                raise RuntimeError(response["error"])
            sid = response["result"]["session_id"]
        with _session_resume_lock:
            session = _sessions.get(sid)
            if _ws_session_is_detached(session) and sid not in _pending_ws_reaps:
                _schedule_ws_orphan_reap(sid)
        if session is not None and session.get("agent_error"):
            _restart_completed_failed_agent_build(sid, session, session.get("agent_ready"))
        session, error = _sess({"session_id": sid}, rid)
        if error is not None:
            raise RuntimeError(error)
        return sid, session
    finally:
        reset_transport(token)
        if ctx.owns_db and ctx.db is not None:
            _release_db(ctx.db)
