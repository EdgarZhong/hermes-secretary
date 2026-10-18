"""Minimal additive read/control handlers; native adapters and slash remain untouched."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _compression_handler(server, rid, params, *, cancel=False):
    from agent.compression_read import cancel_compression, compression_state
    session, error = server._sess_nowait(params, rid)
    if error:
        return error
    if params.get("profile") is not None:
        requested_home = Path(server._profile_home(params["profile"]) or server._launch_home()).resolve()
        owned_home = Path(session.get("profile_home") or server._launch_home()).resolve()
        if requested_home != owned_home:
            return server._err(rid, 4001, "Runtime session belongs to a different profile")
    if server._session_uses_compute_host(session):
        return server._err(rid, 4010, "Compaction observation requires the owning compute host")
    agent = session.get("agent")
    result = cancel_compression(agent, params["operation_id"]) if cancel else compression_state(agent)
    return server._ok(rid, result)


def _secretary_handler(server, rid, params, *, read=None):
    from hermes_state import SessionDB
    from secretary import web_read as secretary_reads
    try:
        profile_home = server._profile_home(params["profile"])
        home = Path(profile_home or server._launch_home())
        path = home / "state.db"
        if not path.is_file():
            return server._err(rid, 5010, "Owning profile state is unavailable")
        # Use the same native owner scope as other profile reads: the Scheduler's
        # shared projection resolves its timezone through the active Hermes clock.
        with server._session_profile_runtime_scope({"profile_home": profile_home}, hydrate_secrets=False):
            db = SessionDB(path, read_only=True)
            try:
                if db.get_session(params["stored_session_id"]) is None:
                    return server._err(rid, 4001, "Unknown stored session")
                result = (read or secretary_reads.secretary_state)(db, params["stored_session_id"])
                result["profile"] = params["profile"]
                result["profile_home"] = str(home.resolve())
                return server._ok(rid, result)
            finally:
                db.close()
    except PermissionError as exc:
        return server._err(rid, 4030, str(exc))
    except server.ProfileUnavailableError:
        raise  # preserve the native 4064 profile error at dispatch
    except Exception:
        logger.debug("Owning Conversation read unavailable", exc_info=True)
        return server._err(rid, 5010, "Owning Conversation read is unavailable")


def _invalidation_sink(server, profile_home, ref, reason, *, completion_snapshot_id=None):
    payload = {"profile_home": str(profile_home), "conversation_ref": ref, "reason": reason}
    if completion_snapshot_id is not None:
        payload["completion_snapshot_id"] = completion_snapshot_id
    if ref is None:
        server._broadcast_global_event("secretary.changed", payload)
        return
    # Existing transport owns each runtime; no new socket or read-created runtime mapping.
    for sid, session in list(server._sessions.items()):
        home = Path(session.get("profile_home") or server._launch_home()).resolve()
        if home != profile_home:
            continue
        agent = session.get("agent")
        if getattr(agent, "_secretary_conversation_ref", None) == ref:
            server._emit("secretary.changed", sid, payload)
    # Stored-only views have no runtime/transport attachment. Existing live WS peers receive
    # this small owner-qualified hint and decide whether the current Conversation must refetch.
    server._broadcast_global_event("secretary.changed", payload)


def register(server):
    from secretary import web_read as secretary_reads
    from secretary.web_events import subscribe
    server.register_method("session.compaction_state", lambda rid, params: _compression_handler(server, rid, params))
    server.register_method("session.compaction_cancel", lambda rid, params: _compression_handler(server, rid, params, cancel=True))
    server.register_method("secretary.state", lambda rid, params: _secretary_handler(server, rid, params))
    server.register_method("secretary.notebook_read", lambda rid, params: _secretary_handler(
        server, rid, params, read=secretary_reads.notebook_read))
    server.register_method("secretary.schedules", lambda rid, params: _secretary_handler(
        server, rid, params, read=secretary_reads.schedules_read))
    subscribe("tui_gateway", lambda home, ref, reason, **metadata: _invalidation_sink(
        server, home, ref, reason, **metadata), include_metadata=True)
