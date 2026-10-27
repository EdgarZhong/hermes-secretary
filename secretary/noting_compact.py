"""Parent-only adapter to Hermes native compaction requests; no Noting tool exists here."""

import logging

logger = logging.getLogger(__name__)


def request_parent_compaction(parent, *, threshold_tokens=None, expected_owner=None, wait_for_completion=False):
    """Reuse the native lock/fence/cooldown path, never await a Noting child."""
    request = getattr(parent, "request_context_compaction", None)
    if not callable(request):
        raise RuntimeError("The parent has no native compaction request interface")
    options = {}
    if expected_owner is not None:
        options["expected_owner"] = expected_owner
    if wait_for_completion:
        options["wait_for_completion"] = True
    return request(relevant_threshold_tokens=threshold_tokens, wait_seconds=5.0, **options)


def idle_compaction_after_commit(parent, *, conversation_ref, threshold_tokens, admission=None):
    """Bind one Idle owner; wait for native completion before its Framework result.

    The native request's receipt means admission, not completion. Waiting on the
    request event covers both an idle worker and a safe-point consumer in Main;
    no Main, Framework or persistence lock is held while waiting.
    """
    from agent.context_compaction_request import _epoch

    db, owner = parent._session_db, _epoch(parent)

    def relevant():
        if admission is None:
            return False
        from secretary.noting_child import normal_noting_snapshot_conn
        with db._read_ctx() as conn:
            return normal_noting_snapshot_conn(db, conn, admission) is not None

    def compact(*, wait_for_completion=True):
        try:
            if not relevant():
                return False
            result = request_parent_compaction(
                parent, threshold_tokens=threshold_tokens, expected_owner=(owner, db, conversation_ref, relevant),
                wait_for_completion=wait_for_completion,
            )
            logger.info("Joint Idle native compaction outcome: %s", getattr(result, "status", result))
            return bool(getattr(result, "ok", False))
        except Exception:
            # The Notebook is already committed; native compression failure must
            # not discard its completion carrier or relabel its termination.
            logger.warning("Joint Idle native compaction request failed", exc_info=True)
            return False

    compact._native_relevance_check = relevant
    return compact
