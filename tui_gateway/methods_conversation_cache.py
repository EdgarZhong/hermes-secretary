"""Profile-qualified context-prefix cache clearing for Conversation debugging."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def _clear(server, rid, params):
    from hermes_state_errors import SessionTurnLeaseLostError
    from hermes_state import SessionCompressionInProgressError
    from secretary.conversation_cache import clear_context_cache

    if (not isinstance(params, dict) or not isinstance(params.get("profile"), str)
            or not params["profile"].strip()
            or not isinstance(params.get("conversation_ref"), str)
            or not params["conversation_ref"].strip()):
        return server._err(rid, 4000, "profile and conversation_ref are required")
    try:
        home = server._profile_home(params["profile"]) or server._launch_home()
        if not (Path(home) / "state.db").is_file():
            return server._err(rid, 5010, "Owning profile state is unavailable")
        with server._profile_db(params, writer=True) as db:
            if db is None:
                return server._err(rid, 5010, "Owning profile state is unavailable")
            result = clear_context_cache(db, params["conversation_ref"])
        if result is None:
            return server._err(rid, 4001, "Unknown Conversation")
        return server._ok(rid, {"profile": params["profile"], **result})
    except (SessionTurnLeaseLostError, SessionCompressionInProgressError) as exc:
        return server._err(rid, 4010, str(exc))
    except server.ProfileUnavailableError:
        raise
    except Exception:
        logger.warning("Conversation context cache clear failed", exc_info=True)
        return server._err(rid, 5010, "Conversation context cache clear is unavailable")


def register(server):
    server.register_method("conversation.context_cache_clear", server._profile_scoped(
        lambda rid, params: _clear(server, rid, params)))
