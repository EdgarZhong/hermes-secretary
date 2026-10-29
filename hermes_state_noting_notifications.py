"""Read-only proof of native Noting audit sessions for bounded invalidation."""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)
NOTING_HISTORY_SCOPE_LIMIT = 256

# Registry membership is durable task ownership, independent of a session ID's
# spelling, source label, live process or whether the task has finished.
_NOTING_SESSION = """
EXISTS (
    SELECT 1 FROM secretary_noting_task_children c
    JOIN secretary_noting_task_admissions a USING(admission_id)
    WHERE c.child_session_id=s.id
) OR (
    json_valid(s.model_config)
    AND json_type(s.model_config,'$._noting_recovery')='object'
    AND EXISTS (
        SELECT 1 FROM secretary_noting_task_children c
        JOIN secretary_noting_task_admissions a USING(admission_id)
        WHERE c.child_session_id=json_extract(s.model_config,'$._noting_recovery.failed_child_session_id')
        AND a.admission_id=json_extract(s.model_config,'$._noting_recovery.admission_id')
        AND a.conversation_ref=json_extract(s.model_config,'$._noting_recovery.conversation_ref')
    )
)
"""


def is_noting_history_owner(db, session_id):
    if not isinstance(session_id, str) or not session_id:
        return False
    try:
        with db._read_ctx() as conn:
            return conn.execute(f"SELECT 1 FROM sessions s WHERE s.id=? AND ({_NOTING_SESSION})",
                                (session_id,)).fetchone() is not None
    except Exception:
        logger.debug("Noting history owner unavailable; using native global invalidation", exc_info=True)
        return False


def noting_history_scope(conn):
    """Cover every proven child because an opaque wake can merge many writers."""
    rows = conn.execute(
        "SELECT s.id,b.conversation_ref FROM sessions s "
        "LEFT JOIN secretary_session_bindings b ON b.session_id=s.id "
        f"WHERE ({_NOTING_SESSION}) ORDER BY s.id LIMIT ?", (NOTING_HISTORY_SCOPE_LIMIT + 1,),
    ).fetchall()
    if not rows or len(rows) > NOTING_HISTORY_SCOPE_LIMIT:
        return None
    result = []
    for identity, ref in rows:
        if not isinstance(identity, str) or not identity or not isinstance(ref, str) or not ref:
            return None
        result.append((identity, ref))
    return tuple(result) if len({row[0] for row in result}) == len(result) else None
