"""Attempt-local Secretary full-compaction policy, without changing engine configuration."""

from contextlib import contextmanager
from contextvars import ContextVar
import logging

logger = logging.getLogger(__name__)
NATIVE_THRESHOLD_TRIGGER = "native_context_threshold"
_NO_DEFAULT_TAIL = ContextVar("secretary_no_default_compaction_tail", default=False)


def native_threshold_trigger(compressor, tokens, *, provider_overflow=False):
    """A compressor request below its native threshold is maintenance, not threshold pressure."""
    if provider_overflow:
        return "overflow"
    threshold = getattr(compressor, "threshold_tokens", None)
    if isinstance(threshold, (int, float)) and not isinstance(threshold, bool) and threshold > 0 and tokens >= threshold:
        return NATIVE_THRESHOLD_TRIGGER
    return "engine_maintenance"


def select_no_default_tail(agent, *, trigger=None, verbatim_tail=None):
    """Only a real native-threshold dispatch or an explicit kept tail uses native recency."""
    if trigger == NATIVE_THRESHOLD_TRIGGER or verbatim_tail:
        return False
    if getattr(agent, "_secretary_noting_child", False):
        return False
    from secretary.noting_runtime import noting_local_enabled
    from secretary.noting_surface import notebook_read_enabled
    if not notebook_read_enabled(agent):
        return False
    return noting_local_enabled(agent._session_db, getattr(agent, "_secretary_conversation_ref", None))


def no_default_tail():
    return _NO_DEFAULT_TAIL.get()


@contextmanager
def tail_policy_scope(enabled):
    token = _NO_DEFAULT_TAIL.set(enabled)
    try:
        yield
    finally:
        _NO_DEFAULT_TAIL.reset(token)


def required_tail_start(compressor, messages):
    """Keep every unresolved inbound request and the unread tool round, with its call owner.

    A final assistant reply settles the requests before it. All inbound rows after
    that boundary belong to the still-open work, including consecutive requests
    and legal steer rows. Recency, message floors and old replies are not anchors.
    """
    from agent.context_compressor import _pending_tool_round, _content_text_for_contains

    end = len(messages)
    settled = -1
    for index in range(end - 1, -1, -1):
        message = messages[index]
        if (message.get("role") == "assistant" and not message.get("tool_calls")
                and _content_text_for_contains(message.get("content")).strip()):
            settled = index
            break
    pending_users = [index for index in range(settled + 1, end) if _pending_request(compressor, messages[index])]
    cut = min(pending_users, default=end)
    pending = _pending_tool_round(messages)
    if pending:
        cut = min(cut, compressor._align_boundary_backward(messages, pending.start))
    # An assistant call can be the last row while the host is waiting for tool
    # results. A missing result must not be silently converted into a summary.
    if end and messages[-1].get("tool_calls"):
        cut = min(cut, end - 1)
    return cut


def _pending_request(compressor, message):
    from agent.context_compressor import _is_text_only_content, user_originated_turn_view
    from agent.conversation_compression import _is_real_user_message
    if compressor._has_merged_inflight_replay(message):
        return True
    if compressor._is_context_summary_message(message):
        return user_originated_turn_view(message) is not None
    return (compressor._is_actionable_user_turn(message)
            and (_is_real_user_message(message) or not _is_text_only_content(message.get("content"))))


def compress_window(compressor, messages):
    if not no_default_tail():
        return native_compress_window(compressor, messages)
    start = 1 if messages and messages[0].get("role") == "system" else 0
    cut = max(start, required_tail_start(compressor, messages))
    # A prior carrier can contain both a handoff and still-unanswered input.
    # Native handoff scanning would unwrap it into the summary input; defer this
    # attempt instead of reclassifying that live request as completed history.
    if any(compressor._is_context_summary_message(message) for message in messages[cut:]):
        return start, start
    return start, cut


def prune_for_attempt(compressor, messages):
    """Old tool bodies may be pruned; unresolved requests/results stay verbatim."""
    pruned, count = compressor._prune_old_tool_results(
        messages, protect_tail_count=compressor.protect_last_n, protect_tail_tokens=compressor.tail_token_budget,
    )
    if no_default_tail():
        cut = required_tail_start(compressor, messages)
        pruned[cut:] = [message.copy() for message in messages[cut:]]
    return pruned, count


def prepare_candidate_anchors(agent, source, compressed, *, verbatim_tail=None, remove_default_tail=False):
    """Apply native presentation anchors only when this attempt keeps native recency."""
    from agent.conversation_compression import _ensure_compressed_has_user_turn, _fold_todo_snapshot
    from agent.conversation_compression_reply_anchor import _ensure_compressed_keeps_last_assistant_reply

    if remove_default_tail:
        # The engine retained every still-open request, so a completed historical
        # user or reply must not be resurrected after the full summary.
        _fold_todo_snapshot(agent, compressed)
        return None, "already_present"
    reply = None if verbatim_tail else _ensure_compressed_keeps_last_assistant_reply(
        source, compressed, session_id=agent.session_id,
    )
    if reply is not None:
        logger.info("Compression: reinserted the last delivered assistant reply (session=%s).", agent.session_id or "none")
    _fold_todo_snapshot(agent, compressed)
    return reply, _ensure_compressed_has_user_turn(source, compressed)


def native_compress_window(self, messages):
    """Return ``(compress_start, compress_end)`` for the summarizable middle."""
    compress_start = self._align_boundary_forward(messages, self._protect_head_size(messages))
    compress_end = self._find_tail_cut_by_tokens(messages, compress_start)
    # A role collision can merge the summary into the first tail row; keep an actionable user
    # event out of that slot by retaining an older assistant/tool bridge.
    latest_actionable_idx = self._find_last_user_message_idx(messages, 0)
    if compress_end == latest_actionable_idx:
        bridge_idx = latest_actionable_idx - 1
        bridge_role = messages[bridge_idx].get("role") if bridge_idx >= 0 else None
        if bridge_role == "tool":
            bridge_idx = self._align_boundary_backward(messages, latest_actionable_idx)
        elif bridge_role != "assistant":
            bridge_idx = -1
        if bridge_idx > compress_start:
            compress_end = bridge_idx
    return compress_start, compress_end
