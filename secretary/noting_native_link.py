"""Associate a Secretary task with the native compression registration identity."""

import logging

logger = logging.getLogger(__name__)


def operation_for_fence(parent, fence):
    lock = vars(parent).get("_compression_commit_fence_lock")
    if lock is None or fence is None:
        return None
    with lock:
        for entry in vars(parent).get("_compression_commit_fence_stack", ()):
            if entry.fence is fence:
                return entry.observation.operation_id
    return None


def finish_native_joint(parent, registration):
    try:
        from secretary.noting_joint import finish_operation
        finish_operation(parent, registration.observation.operation_id,
                         succeeded=registration.observation.state == "completed")
    except Exception:
        logger.warning("Native joint Noting settlement failed", exc_info=True)


def adopt_native_publication(parent, registration, messages, result):
    """The owned runtime follows the native committed list before a Note can target it."""
    try:
        _adopt_note_target(parent, registration, messages, result)
    except Exception:
        logger.warning("Note-only native publication observation failed", exc_info=True)


def _adopt_note_target(parent, registration, messages, result):
    if not getattr(registration.fence, "_commit_started", False):
        return
    if not isinstance(result, tuple) or not result or not isinstance(result[0], list):
        return
    from agent.context_compaction_request import _lock
    from secretary.noting_notes import select_note_conn
    db = getattr(parent, "_session_db", None)
    ref = getattr(parent, "_secretary_conversation_ref", None)
    if db is None or not ref:
        return
    with db._read_ctx() as conn:
        if select_note_conn(db, conn, ref) is None:
            return
    with _lock(parent):
        if getattr(parent, "_session_messages", None) is messages and result[0] is not messages:
            parent._session_messages = result[0]
