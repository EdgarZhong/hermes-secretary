"""Heartbeat-only recovery of an already bound Conversation, independent of current peers."""

from __future__ import annotations


def heartbeat_route_conn(db, conn, conversation_ref):
    """Follow only proven native compression edges inside durable Secretary bindings.

    A peer's current generation and a Session's reset/left-interface stamp do not
    revoke the user's Conversation Heartbeat. No routing peer or binding is changed.
    The general Noting/Scheduler route deliberately retains its stricter policy.
    """
    from hermes_state_secretary_identity import ConversationIdentityError
    from secretary.noting_runtime import _CHILD_SOURCES, _delegate_child_row

    bindings = conn.execute(
        "SELECT session_id FROM secretary_session_bindings WHERE conversation_ref=?", (conversation_ref,)
    ).fetchall()
    tips = {}
    for binding in bindings:
        if conn.execute("SELECT 1 FROM sessions WHERE id=?", (binding[0],)).fetchone() is None:
            continue
        path = db._compression_path_conn(conn, binding[0])
        tip = db._secretary_session_conn(conn, path[-1])
        owner = conn.execute(
            "SELECT conversation_ref FROM secretary_session_bindings WHERE session_id=?", (tip["id"],)
        ).fetchone()
        if owner is None or owner[0] != conversation_ref:
            raise ConversationIdentityError("Heartbeat compression tip has no matching durable binding")
        if tip["source"] not in _CHILD_SOURCES and not _delegate_child_row(tip):
            tips[tip["id"]] = tip
    return max(tips.values(), key=lambda row: (row.get("started_at") or 0, row["id"])) if tips else None


def heartbeat_route(db, conversation_ref):
    with db._read_ctx() as conn:
        return heartbeat_route_conn(db, conn, conversation_ref)
