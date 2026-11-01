"""Profile-bound llm.oneshot title branch; the native database owns its context."""

import contextlib
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _runtime_needs_recovery(parent, row):
    from hermes_state import SessionDB
    from tui_gateway import server
    if (parent is None or getattr(parent, "_native_compaction_turn", None) is not None
            or getattr(parent, "_active_compression_commit_fence", None) is not None):
        return True
    runtime = parent._current_main_runtime()
    saved = SessionDB.session_gateway_runtime(row)
    if row.get("model") and row["model"] != parent.model:
        return True
    if any(saved.get(key) and str(saved[key]).rstrip("/") != str(runtime.get(key) or "").rstrip("/")
           for key in ("provider", "base_url", "api_mode")):
        return True
    config = server._parse_model_config(row.get("model_config"), quiet=True)
    return (isinstance(config.get("reasoning_config"), dict)
            and config["reasoning_config"] != parent.reasoning_config)


@contextlib.contextmanager
def _title_runtime(session, context):
    from tui_gateway import server
    parent = session.get("agent")
    temporary = _runtime_needs_recovery(parent, context.reader.row)
    if temporary:
        parent = server._make_agent_in_context(
            session.get("_sid", ""), context.session_id, session_db=context.reader,
            platform_override=server._session_source(session),
            cwd_override=server._session_cwd(session), detached_context=True,
            **server._stored_session_runtime_overrides(context.reader.row))
    try:
        yield parent
    finally:
        if temporary:
            parent.close()


def current_conversation_title(params, *, max_tokens):
    from agent.conversation_title import (
        TitleContextUnavailable, generate_conversation_title, snapshot_title_context,
    )
    from tui_gateway import server
    from hermes_state import SessionDB

    session = server._sessions.get(params.get("session_id") or "")
    if not session:
        raise TitleContextUnavailable("The current Main Conversation is unavailable.")
    home = Path(session.get("profile_home") or server._launch_home()).resolve()
    if params.get("profile"):
        requested = Path(server._profile_home(params["profile"]) or server._launch_home()).resolve()
        if requested != home:
            raise TitleContextUnavailable("The title request Profile does not own this Main Conversation.")
    if session.get("running"):
        raise TitleContextUnavailable("The Main is running; retry title generation when it is idle.")
    parent = session.get("agent")
    parent_db = getattr(parent, "_session_db", None)
    if parent is not None and (parent_db is None or Path(parent_db.db_path).resolve() != home / "state.db"):
        raise TitleContextUnavailable("The Main runtime does not belong to the requested Profile storage.")
    with server._session_profile_runtime_scope(session), SessionDB(home / "state.db", read_only=True) as db:
        context = snapshot_title_context(parent, db, server._submit_row_target_key(session))
        tokens = server._set_session_context(context.session_id, cwd=server._session_cwd(session))
        try:
            with _title_runtime(session, context) as current:
                return generate_conversation_title(current, context, max_tokens=max_tokens)
        finally:
            server._clear_session_context(tokens)


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
