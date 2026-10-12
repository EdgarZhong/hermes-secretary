"""Native cold Parent preparation, before the existing build owner publishes readiness.

The native build/eager bodies below remain late-bound to the gateway facade. Only an
eligible globally-enabled cold context uses preparation; no timer/admission code lives here.
"""
from contextlib import suppress

from .method_ctx import rebind


def cold_context_enabled(agent):
    from secretary.noting_runtime import is_main_conversation_agent
    if not is_main_conversation_agent(agent):
        return False
    from secretary.noting_scope import settings_for_db
    return settings_for_db(agent._session_db).enabled


def prepare_resumed_parent_context(agent, history):
    if not history or not cold_context_enabled(agent):
        return None
    from agent.conversation_loop import _restore_or_build_system_prompt
    from secretary.noting_surface import apply_main_read_surface, synchronize_main_read_prompt
    apply_main_read_surface(agent)
    if agent._cached_system_prompt is None:
        _restore_or_build_system_prompt(agent, None, history)
    synchronize_main_read_prompt(agent)
    return True


def close_prepared_agent(agent, *, close_db=False):
    if agent is None:
        return
    # Until native _finish_agent_build transfers it, the prepared agent borrows this DB ref.
    db = getattr(agent, "_session_db", None)
    owns = getattr(agent, "_owns_session_db", False)
    with suppress(Exception):
        agent.close()
    if close_db and db is not None and not owns:
        with suppress(Exception):
            db.close()


def attach_recovered_agent(namespace, sid, current, agent):
    return rebind(_attach_recovered_agent, namespace)(sid, current, agent)


def _attach_recovered_agent(sid, current, agent):
    # Native root preparation only reads replay history (surface notes are Agent-side).
    # Publish the LATEST host-owned history; do not rerun side-effecting restore on version churn.
    with current["history_lock"], _sessions_lock:
        if _sessions.get(sid) is not current:
            return False
        history = current.get("history", [])
        agent._session_messages = history
        # Born-durable replay markers remain intact. The native flush handles any unpersisted tail.
        agent._last_flushed_db_idx = 0
        agent._db_flush_scan_prefix = None
        current["agent"] = agent
    _register_session_cwd(current)
    _session_todo_state(current)
    current["config_model_seen"] = _config_model_target()
    return True


def resume_prepared_eager(namespace, *args):
    return rebind(_resume_prepared_eager, namespace)(*args)


def _resume_prepared_eager(ctx, sid, source, cwd, agent, history, display, raw, prefix, overrides):
    from tui_gateway.session_agent_context import close_prepared_agent
    record = ctx.record(source, cwd, history, overrides, display_history_prefix=prefix,
                        todo_state=_todo_state_from_history(history))
    if (reused := ctx.claim(sid, record)) is not None:
        close_prepared_agent(agent)
        return reused
    # One existing build owner takes the already-constructed real Agent, or a concurrent
    # native builder already owns the record. Only actual adoption transfers the reader ref.
    adopted = _start_agent_build(sid, record, prepared_agent=agent)
    if adopted:
        if ctx.owns_db:
            ctx.owns_db = False
    else:
        close_prepared_agent(agent)
    error = _wait_agent(record, ctx.rid, timeout=_agent_build_wait_cap())
    if error is not None or record.get("agent") is None:
        message = ((error or {}).get("error") or {}).get("message") or AGENT_BUILD_ABANDONED
        return _err(ctx.rid, 5000, resume_failed_message(RuntimeError(message)))
    with _session_resume_lock:
        if (refusal := _reattach_refusal(ctx.rid, sid, record)) is not None:
            return refusal
    _schedule_session_cap_enforcement()
    return _resume_response(ctx, sid, record, info=_session_info(record["agent"], record),
                            display=display, count_source=raw, started_at=record["created_at"],
                            auto_continue=_maybe_schedule_auto_continue(sid, record, ctx.target))


def start_agent_build(namespace, sid, session, *, prepared_agent=None):
    return rebind(_native_start_agent_build, namespace)(sid, session, prepared_agent=prepared_agent)


def resume_eager(namespace, ctx):
    return rebind(_native_resume_eager, namespace)(ctx)


def _native_start_agent_build(sid: str, session: dict, *, prepared_agent=None):
    """Start building the real AIAgent for a TUI session, once. Deferred until the first prompt (or any
    command needing the agent) so the composer isn't blocked on tool discovery / model metadata;
    the ready/error event contract is unchanged."""
    from tui_gateway.session_agent_context import prepare_resumed_parent_context, close_prepared_agent
    ready = session.get("agent_ready")
    if ready is None:
        return False if prepared_agent is not None else None
    # A lazy watch session spectating an in-flight child must stay lazy so the subagent live-mirror keeps
    # flowing (it bails once agent is set); incidental RPCs via _sess() would upgrade it mid-stream.
    if session.get("lazy") and _child_run_active(
            str(session.get("session_key") or ""), session.get("profile_home") or None):
        return False if prepared_agent is not None else None
    with session.setdefault("agent_build_lock", threading.Lock()):
        if ready.is_set() or session.get("agent_build_started"):
            return False if prepared_agent is not None else None
        session["agent_build_started"] = True
        session.pop("lazy", None)  # now genuinely mid-construction: restore the "still starting" eviction exemption
    key = session["session_key"]

    def _build() -> None:
        with _sessions_lock:
            current = _sessions.get(sid)
        if current is None:
            # Closed/reaped before the build started: nothing will ever attach an agent to this
            # record, yet ``agent_ready`` must be set so a prompt waiting on it fails instead of hanging.
            close_prepared_agent(prepared_agent, close_db=bool(session.get("profile_home")))
            session["agent_error"] = AGENT_BUILD_ABANDONED
            ready.set()
            return
        notify_registered, scopes = False, None
        agent = prepared_agent
        profile_home = current.get("profile_home")
        session_db = prepared_agent._session_db if prepared_agent is not None and profile_home else None
        try:
            if not _await_resume_history(sid, current):
                # Replaced mid-build: the finally still sets ``agent_ready`` with ``agent`` None, so record
                # why — a turn admitted against this record refuses with the real reason (#111531).
                current["agent_error"] = AGENT_BUILD_ABANDONED
                return
            tokens = _set_session_context(key, cwd=_session_cwd(current))
            # Global-remote: bind the session profile's HERMES_HOME and hand the agent that profile's db —
            # DEDICATED and ours until _transfer_db_to_agent in the finally; FAIL CLOSED rather than
            # binding the launch DB and bleeding rows into the wrong state.db.
            scopes = _bind_build_profile_scopes(profile_home)
            if profile_home:
                session_db = (prepared_agent._session_db if prepared_agent is not None
                              else _open_profile_session_db(profile_home))
            try:
                from tui_gateway.entry import ensure_mcp_discovery_started
                ensure_mcp_discovery_started()
            except Exception:
                logger.warning("MCP discovery startup failed", exc_info=True)
            try:
                if prepared_agent is None:
                    agent = _make_agent(sid, key, **_deferred_build_agent_kwargs(current, session_db))
                with current["history_lock"]:
                    history = list(current.get("history") or [])
                recovered = prepare_resumed_parent_context(agent, history)
            finally:
                _clear_session_context(tokens)
            # Attach atomically against session teardown: ``session.close`` may have popped this
            # session while the expensive build was in flight, in which case teardown could not close
            # an agent that did not exist yet. Release the orphan immediately and do not keep wiring
            # workers/callbacks for a dead session (#49852).
            attached = (_attach_built_agent(sid, current, agent) if recovered is None
                        else _attach_built_agent(sid, current, agent, recovered=recovered))
            if not attached:
                # Same contract as the replaced-before-attach exit above: a turn admitted against
                # this record must refuse with the real reason rather than a generic missing agent.
                current["agent_error"] = AGENT_BUILD_ABANDONED
                return
            # No eager slash-worker pre-warm (slash.exec spawns on demand): each worker forks the full stdio
            # MCP fleet, and live-transport sessions are never reaped, so fleets would accumulate.
            notify_registered = _wire_session_agent(sid, key, agent)
            _announce_built_agent(sid, key, current, agent)
        except Exception as e:
            from agent.auxiliary_unavailable import ProviderNotConfiguredError
            logger.warning("Native session agent build failed", exc_info=True)
            current["agent_error"] = str(e)
            # A client can route "no provider is set up" to its setup flow instead of a dead-end
            # error toast — but only if it can tell. The sentence is for the reader, the code is
            # for the client; older clients keep matching the text.
            _emit("error", sid, {
                "message": agent_init_failed_message(e),
                **({"code": "provider_not_configured"} if isinstance(e, ProviderNotConfiguredError) else {})})
        finally:
            if agent is not current.get("agent"):
                close_prepared_agent(agent)
            _finish_agent_build(
                sid, key, current, notify_registered=notify_registered, scopes=scopes, session_db=session_db)
            ready.set()

    build_thread = threading.Thread(target=_build, daemon=True)
    # _wait_agent_for_prompt handle: dead thread + unset agent_ready = died hard; waiters must not sit out the cap.
    session["_agent_build_thread"] = build_thread
    try:
        build_thread.start()
    except RuntimeError as exc:
        if prepared_agent is None:
            raise
        close_prepared_agent(prepared_agent, close_db=bool(session.get("profile_home")))
        session["agent_error"] = str(exc)
        ready.set()
    return True if prepared_agent is not None else None


def _native_resume_eager(ctx):
    """Synchronous build OUTSIDE _session_resume_lock (it would stall session.close), then double-checked."""
    sid, source, _cwd = ctx.mint()
    with _profile_build_scope(ctx.profile_home):
        try:
            history, display_history, raw_history = ctx.restore()
            display_history_prefix = ctx.display_prefix()
            # Profile db so turns persist to the right state.db; stored runtime identity so switching chats does
            # not inherit another chat's global model.
            stored_runtime_overrides = _stored_session_runtime_overrides(ctx.found)
            agent = _make_agent_in_context(
                sid, ctx.target, session_db=ctx.db, platform_override=source,
                cwd_override=ctx.profile_resume_cwd or None,
                context_cwd_is_launch_artifact=(source in _LAUNCH_CWD_NOT_A_WORKSPACE and not ctx.profile_resume_cwd),
                auth_user_id=_transport_auth_user_id(current_transport()), **stored_runtime_overrides)
        except Exception as e:
            logger.warning("Native eager session construction failed", exc_info=True)
            return _err(ctx.rid, 5000, resume_failed_message(e))
    from tui_gateway.session_agent_context import cold_context_enabled, resume_prepared_eager
    if history and cold_context_enabled(agent):
        return resume_prepared_eager(globals(), ctx, sid, source, _cwd, agent, history,
                                     display_history, raw_history, display_history_prefix, stored_runtime_overrides)
    with _session_resume_lock:
        live = _find_live_session_by_key(ctx.target, ctx.profile_home)
        if live is not None:
            with contextlib.suppress(Exception):
                agent.close()
            return _resume_reuse_live_locked(ctx, *live)
        try:
            with _profile_build_scope(ctx.profile_home):
                _init_session(sid, ctx.target, agent, history, cols=ctx.cols, cwd=ctx.profile_resume_cwd,
                              session_db=ctx.db, source=source, explicit_cwd=bool(ctx.profile_resume_cwd))
                # Ownership TRANSFER: the agent holds the handle for life (AIAgent.close() releases it). The
                # owns_db drop is UNCONDITIONAL — the session is registered against the handle, so the finally
                # must not close it even if the transfer was refused (a leak beats "closed database" every
                # turn). Gated on owns_db: the SHARED launch handle must never move onto one session.
                if ctx.owns_db:
                    _transfer_db_to_agent(agent, ctx.db)
                ctx.owns_db = False
            if (session := _sessions.get(sid)) is not None:
                if stored_runtime_overrides.get("model_override") is not None:
                    session["model_override"] = stored_runtime_overrides["model_override"]
                model_config = _parse_model_config(ctx.found.get("model_config"), quiet=True)
                if _row_follows_profile(ctx.found):
                    session["follow_profile_config"] = True
                    session["composer_override_profile"] = (
                        model_config.get("composer_override_profile")
                        if stored_runtime_overrides.get("model_override") else None)
                # Each turn re-binds HERMES_HOME (mid-turn memory/skills reads); lease claimed lazily on turn 1.
                if ctx.profile_home is not None:
                    session["profile_home"] = str(ctx.profile_home)
                session.update(display_history_prefix=display_history_prefix, active_session_lease=None)
        except Exception as e:
            logger.warning("Native eager session publication failed", exc_info=True)
            # _init_session registers _sessions[sid] BEFORE its first db read; left in place the fast path
            # would serve that dead session forever.
            if ctx.owns_db:
                with _sessions_lock:
                    _sessions.pop(sid, None)
            return _err(ctx.rid, 5000, resume_failed_message(e))
        session = _sessions.get(sid) or {}
    return _resume_response(
        ctx, sid, session, info=_session_info(agent, session), display=display_history, count_source=raw_history,
        started_at=float(session.get("created_at") or time.time()),
        auto_continue=_maybe_schedule_auto_continue(sid, session, ctx.target) if session else None)

