"""Best-effort completed-sync notices, bound to the submitting native turn.

The driver callbacks have no delivery ACK. A late observation is offered again by
the provider at a later completed boundary; it never uses a later turn's callback.
"""
from agent.credits_tracker import AgentNotice


def capture_sync_feedback(agent):
    """Capture immutable driver/owner references, without changing native turn admission."""
    token = getattr(agent, "_native_compaction_turn", None)
    session_id = getattr(agent, "session_id", None)
    manager = getattr(agent, "_memory_manager", None)
    notice_callback = getattr(agent, "notice_callback", None)
    status_callback = getattr(agent, "status_callback", None)
    # No native turn means no legal asynchronous driver opportunity.
    if token is None or not (callable(notice_callback) or callable(status_callback)):
        return None

    def attempt(feedback):
        if (getattr(agent, "_native_compaction_turn", None) is not token
                or getattr(agent, "session_id", None) != session_id
                or getattr(agent, "_memory_manager", None) is not manager
                or getattr(agent, "notice_callback", None) is not notice_callback
                or getattr(agent, "status_callback", None) is not status_callback
                or getattr(agent, "_memory_provider_shutdown", False)):
            return False
        key = "memory-sync." + feedback.scope
        if callable(notice_callback):
            notice_callback(AgentNotice(text=feedback.text, level=feedback.level,
                kind="ttl" if feedback.level != "error" else "sticky",
                ttl_ms=5000 if feedback.level != "error" else None, key=key, id=key))
        else:
            status_callback(feedback.level, feedback.text)
        return True  # attempted, not acknowledged by the driver or human

    return attempt
