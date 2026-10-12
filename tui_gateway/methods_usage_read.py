"""Read-only native Main usage, under the original live Session/profile owner."""
from pathlib import Path


def _usage_detail(server, rid, params):
    from agent.usage_read import main_usage_detail, unknown_usage_detail
    session, error = server._sess_nowait(params, rid)
    if error:
        return error
    if params.get("profile") is not None:
        requested = Path(server._profile_home(params["profile"]) or server._launch_home()).resolve()
        actual = Path(session.get("profile_home") or server._launch_home()).resolve()
        if requested != actual:
            return server._err(rid, 4001, "Runtime session belongs to a different profile")
    hosted = server._session_uses_compute_host(session) or session.get("_hosted_room_task")
    result = (unknown_usage_detail("hosted_owner_unavailable") if hosted
              else main_usage_detail(session.get("agent")))
    result.update(session_id=params["session_id"], stored_session_id=session.get("session_key"))
    return server._ok(rid, result)


def register(server):
    server.register_method("session.usage_detail", server._profile_scoped(
        lambda rid, params: _usage_detail(server, rid, params)))
