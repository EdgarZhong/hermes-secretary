"""Profile-bound llm.oneshot title branch; the native database owns its context."""

import contextlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def current_conversation_title(params, *, max_tokens):
    from agent.conversation_title import (
        TitleContextUnavailable, generate_conversation_title, snapshot_title_context,
    )
    from tui_gateway import server

    session = server._sessions.get(params.get("session_id") or "")
    if not session or session.get("agent") is None:
        raise TitleContextUnavailable("The current Main runtime is unavailable; reopen the Conversation and retry.")
    home = Path(session.get("profile_home") or server._launch_home()).resolve()
    if params.get("profile"):
        requested = Path(server._profile_home(params["profile"]) or server._launch_home()).resolve()
        if requested != home:
            raise TitleContextUnavailable("The title request Profile does not own this Main Conversation.")
    if session.get("running"):
        raise TitleContextUnavailable("The Main is running; retry title generation when it is idle.")
    parent = session["agent"]
    parent_db = getattr(parent, "_session_db", None)
    if parent_db is None or Path(parent_db.db_path).resolve() != home / "state.db":
        raise TitleContextUnavailable("The Main runtime does not belong to the requested Profile storage.")
    with server._session_profile_runtime_scope(session), server._session_db(session) as db:
        if db is None:
            raise TitleContextUnavailable("The owning Main storage is unavailable.")
        context = snapshot_title_context(parent, db, server._submit_row_target_key(session))
        return generate_conversation_title(parent, context, max_tokens=max_tokens)


def oneshot_rpc(rid, params):
    """Existing stateless templates plus the dedicated complete-context title task."""
    from agent.conversation_title import is_conversation_title_request
    from tui_gateway import server

    template = (params.get("template") or "").strip() or None
    instructions = params.get("instructions") or ""
    user_input = params.get("input") or ""
    variables = params.get("variables") if isinstance(params.get("variables"), dict) else {}
    try:
        temperature = float(params["temperature"]) if params.get("temperature") is not None else 0.3
    except (TypeError, ValueError):
        temperature = 0.3
    if not template and not str(instructions).strip() and not str(user_input).strip():
        return server._err(rid, 4030, "llm.oneshot requires a template or instructions/input")
    session = server._sessions.get(params.get("session_id") or "")
    try:
        if is_conversation_title_request(params):
            return server._ok(rid, {"text": current_conversation_title(
                params, max_tokens=server._int_param(params, "max_tokens", 256) or 256)})
        from agent.oneshot import run_oneshot
        with (server._session_profile_runtime_scope(session) if session else contextlib.nullcontext()):
            return server._ok(rid, {"text": run_oneshot(
                instructions=instructions, user_input=user_input, template=template, variables=variables,
                task=(params.get("task") or "title_generation").strip() or "title_generation",
                max_tokens=server._int_param(params, "max_tokens", 1024) or 1024, temperature=temperature,
                main_runtime=server._main_runtime_from_agent(session.get("agent")) if session else None)})
    except (KeyError, ValueError) as e:
        return server._err(rid, 4031 if isinstance(e, KeyError) else 4032, str(e))
    except Exception as e:
        logger.warning("llm.oneshot failed: %s", e, exc_info=True)
        return server._err(rid, 5030, f"one-shot generation failed: {e}")
