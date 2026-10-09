"""Shared main-Turn prompt adapters and profile-bound Secretary slash commands."""

import logging

logger = logging.getLogger(__name__)

def _cmd_queue(rid, params, session, name, arg):
    from tui_gateway import server as s
    return s._ok(rid, {"type": "send", "message": arg}) if arg else s._err(rid, 4004, "usage: /queue <prompt>")


def _prompt_builtin(module: str, fn: str, kw: str = ""):
    """/learn, /plan, /init: submit ``module.fn(arg)`` as a normal turn (the live agent does the work)."""

    def cmd(rid, params, session, name, arg):
        from tui_gateway import server as s
        build = getattr(s._tools_mod(module), fn)
        return s._ok(rid, {"type": "send", "message": build(**{kw: arg}) if kw else build(arg)})
    return cmd


def _remote_secretary(rid, params, session, name, arg):
    from tui_gateway import server as s
    sid = params.get("session_id", "")
    try:
        ack = s._send_compute_host_control(
            sid, route_name=f"slash.{name}", command=f"/{name}" + (f" {arg}" if arg else ""), wait=True)
    except Exception as exc:
        logger.warning("Compute-host Secretary slash failed", exc_info=True)
        return s._exec_out(rid, f"Secretary command unavailable: {exc}")
    if ack.get("type") in {"control.error", "error"}:
        return s._exec_out(rid, str(ack.get("message") or "Secretary command unavailable."))
    result = ack.get("result")
    if not isinstance(result, dict) or result.get("type") not in {"exec", "send"}:
        return s._exec_out(rid, "Secretary command unavailable: invalid host result.")
    return s._ok(rid, result)


def _cmd_secretary(rid, params, session, name, arg):
    """Read current Notebook in the owning profile; a proposal is a normal main-Turn send."""
    from tui_gateway import server as s
    from hermes_cli.cli_secretary_commands import (notebook_command, noting_command, propose_persistence_command,
                                                 persist_secretary_feedback, secretary_feedback_messages)
    if not session:
        return s._exec_out(rid, "Current Conversation state is unavailable.")
    if s._session_uses_compute_host(session):
        return _remote_secretary(rid, params, session, name, arg)
    with s._session_profile_runtime_scope(session):
        if name in {"notebook", "noting"}:
            if s._ensure_session_db_row(session) is False:
                return s._exec_out(rid, "Current Conversation state is unavailable.")
        with s._session_db(session) as db:
            command = {"notebook": notebook_command, "noting": noting_command,
                       "propose-persistence": propose_persistence_command}[name]
            target = str(getattr(session.get("agent"), "session_id", None) or session.get("session_key") or "")
            result = command(db, target, arg, **({"source": session.get("source") or "tui"}
                                               if name == "noting" else {}))
            if result.output and name in {"notebook", "noting"}:
                messages = secretary_feedback_messages(f"/{name}" + (f" {arg}" if arg else ""), result.output)
                try:
                    persist_secretary_feedback(db, target, messages)
                except Exception as exc:
                    logger.warning("Secretary slash feedback could not be saved", exc_info=True)
                    return s._exec_out(rid, result.output + f"\nSecretary feedback could not be saved: {exc}")
                with session["history_lock"]:
                    session.setdefault("history", []).extend(messages)
                    session["history_version"] = int(session.get("history_version", 0)) + 1
    if result.prompt:
        return s._ok(rid, {"type": "send", "message": result.prompt})
    return s._exec_out(rid, result.output)
