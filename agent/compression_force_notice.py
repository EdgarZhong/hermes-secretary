"""Native per-attempt expiry of genuine Force dispatch notices at compaction."""
from __future__ import annotations

import copy
import contextlib
import logging
from contextvars import ContextVar
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger('agent.conversation_compression')
_summary_plan = ContextVar('native_force_notice_summary_plan', default=None)


def is_force_dispatch(row):
    from agent.message_metadata import is_framework_message
    return (isinstance(row, dict) and is_framework_message(row)
            and (row.get('display_metadata') or {}).get('noting_force_dispatch') is True
            and isinstance(row.get('message_uid'), str) and bool(row['message_uid']))


@dataclass
class ForceNoticePlan:
    parent: Any
    db: Any
    conversation_ref: str
    original: list
    comparison: list
    queued: tuple
    expired_uids: frozenset
    priority_uids: frozenset
    verbatim: Optional[list]
    original_verbatim: Optional[list]
    committed: bool = False

    def working(self):
        return copy.deepcopy(self.comparison) if self.expired_uids else self.original


def capture_force_notices(agent, messages, verbatim_tail=None):
    original = list(messages) + list(verbatim_tail or ())
    uids = frozenset(row['message_uid'] for row in original if is_force_dispatch(row))
    if not uids and not getattr(agent, '_secretary_framework_messages', None):
        return None
    if not getattr(agent, '_session_db', None) or not getattr(agent, '_secretary_conversation_ref', None):
        return None
    from secretary.noting_runtime import is_main_conversation_agent
    if not is_main_conversation_agent(agent):
        return None
    from secretary.framework_messages import capture_queued_force_notices
    queued = capture_queued_force_notices(agent)
    if not queued and not uids:
        return None
    indices = [i for i, row in enumerate(original) if is_force_dispatch(row)]
    priority = original[indices[-1] + 1:] if indices else []
    return ForceNoticePlan(agent, agent._session_db, agent._secretary_conversation_ref,
                           messages, copy.deepcopy([row for row in messages if row.get('message_uid') not in uids]),
                           queued, uids, frozenset(row.get('message_uid') for row in priority if row.get('message_uid')),
                           [row for row in (verbatim_tail or ()) if row.get('message_uid') not in uids], verbatim_tail)


@contextlib.contextmanager
def force_summary_scope(plan):
    token = _summary_plan.set(plan)
    try:
        yield
    finally:
        _summary_plan.reset(token)


def summary_focus_for_force(compressor, turns, focus):
    plan = _summary_plan.get()
    if plan is None or not plan.priority_uids:
        return focus
    newer = [row for row in turns if row.get('message_uid') in plan.priority_uids]
    if not newer:
        return focus
    # This is only the existing auxiliary summary's formatting/focus argument.
    # Neither the expired dispatch nor this instruction becomes Parent content.
    material = compressor._serialize_for_summary(newer)
    return ((focus + '\n\n') if focus else '') + (
        'For this compaction only, give priority to preserving the following newer original material. '
        'This is an ephemeral summary instruction: do not reproduce the dispatch notice or this instruction in the handoff.\n'
        + material)


def force_comparison(phase):
    plan = phase.force_notice_plan
    return None if plan is None else plan.comparison


def force_candidate_source(phase):
    return phase.messages if phase.force_notice_plan is None else phase.force_notice_plan.comparison


def force_verbatim(plan, verbatim):
    return verbatim if plan is None else plan.verbatim


def force_original_verbatim(plan, verbatim):
    return verbatim if plan is None else plan.original_verbatim


def force_verbatim_count(plan, verbatim):
    return 0 if plan is not None and plan.expired_uids else len(verbatim)


def force_commit_carry(plan, compressed, tail_ids, carried, tail_count):
    if plan is None or not plan.expired_uids:
        return carried, tail_count
    tail_uids = {row.get('message_uid') for row in compressed if id(row) in tail_ids}
    # Use the authentic originals, not a rewritten summary-bearing tail copy.
    originals = list(plan.original) + list(plan.verbatim or ())
    precise = [row for row in originals if row.get('message_uid') in tail_uids]
    return list(carried or ()) + precise + list(plan.verbatim or ()), 0


def retire_committed_force(plan, native_request=None):
    """Only called on return from the actual native database transaction."""
    if plan is None:
        return
    plan.committed = True
    if native_request is not None:
        native_request.durable_commit_succeeded = True
    from secretary.framework_messages import retire_queued_force_notices
    retire_queued_force_notices(plan.parent, plan.db, plan.conversation_ref, plan.queued)


def raise_if_force_committed(plan):
    if plan is not None and plan.committed:
        raise RuntimeError('Committed Force interval could not be safely published')


def _candidate_rejected(
    agent: Any, compressed: Any, messages: list, messages_before_compression: list, *,
    attempt_generation: Any, attempt_started_at: float, comparison_before: Optional[list] = None,
) -> bool:
    """Reject an unusable compression candidate before any session mutation.
    Order matters: compressor-reported abort, no progress, empty transcript, superseded attempt. Each branch surfaces
    its own warning/telemetry; the caller releases the lease and returns the input unchanged when True.
    """
    from agent.conversation_compression import (
        _emit_aborted_attempt_telemetry, _strip_marker_for_comparison, _swallow,
        _working_attempt_is_current, _restore_messages_snapshot,
    )
    comparison = messages_before_compression if comparison_before is None else comparison_before
    # Aborted compression returns input unchanged: surface the error, skip rotation
    # (no session ended); auto-compress callers detect no-op via equal lengths.
    if getattr(agent.context_compressor, "_last_compress_aborted", False):
        _summary_error = getattr(agent.context_compressor, "_last_summary_error", None)
        _err = _summary_error or "unknown error"
        if getattr(agent, "_last_compression_summary_warning", None) != _err:
            agent._last_compression_summary_warning = _err
            agent._emit_warning(
                f"⚠ Compression aborted: {_err}. "
                "No messages were dropped — conversation continues unchanged. "
                "Run /compress to retry, or /new to start a fresh session."
            )
        _emit_aborted_attempt_telemetry(
            agent, attempt_started_at, _summary_error and "summary_generation_aborted"
        )
        return True

    # Compare semantic state, not identity: engines may return an equal copy or
    # mutate the live list. ``==`` first (subclass __eq__), then marker-insensitive.
    # Neither case may rotate or rewrite the session. The raw ``==`` leg runs FIRST so a list subclass
    # returned by an engine keeps its ``__eq__`` semantics (tests seam on this); the marker-insensitive leg
    # (#92231) then covers the cold-resume shape where the stamped snapshot differs from the marker-swept
    # compress() output only by ``_db_persisted``.
    if compressed == comparison or (
        _strip_marker_for_comparison(compressed) == _strip_marker_for_comparison(comparison)
    ):
        if messages != messages_before_compression:
            messages[:] = copy.deepcopy(messages_before_compression)
        logger.info(
            "Compression made no progress (session=%s) — skipping boundary rewrite.", agent.session_id or "none"
        )
        # Unchanged output would fail identically next turn; arm structural backoff so
        # auto-compress stops re-firing each turn (success lifts it, force overrides).
        with _swallow('no-progress backoff arm failed', exc_info=True):
            if callable(_recorder := getattr(agent.context_compressor, "_record_structural_no_op", None)):
                _recorder("compaction returned the transcript unchanged (no_progress)")
        _emit_aborted_attempt_telemetry(agent, attempt_started_at, "no_progress")
        return True
    if not compressed:
        logger.error(
            "context compression returned an empty transcript; refusing to rotate session=%s so the parent remains resumable",
            agent.session_id or "none",
        )
        with contextlib.suppress(Exception):
            agent._emit_warning(
                "⚠ Compression returned an empty transcript. No session split was performed; conversation continues unchanged."
            )
        return True

    # A newer WORKING attempt supersedes us; discard the late candidate. No-op
    # entry claims (sit-outs that never ran a summary) do not: keying on them
    # discards a completed candidate and livelocks compression. Without a
    # published working marker, fence poison alone misses a successor that
    # minted its own fence — fall back to the entry-generation check.
    if not _working_attempt_is_current(agent.context_compressor, attempt_generation):
        _working_gen = getattr(
            agent.context_compressor, "_compression_working_attempt_generation", None
        )
        logger.warning(
            "Discarding late compression candidate: attempt generation "
            "%s was superseded by a newer working attempt (current working: %s) (session=%s).",
            attempt_generation,
            _working_gen,
            agent.session_id or "none",
        )
        _restore_messages_snapshot(messages, messages_before_compression)
        agent._last_compaction_in_place = False
        _emit_aborted_attempt_telemetry(agent, attempt_started_at, "attempt_superseded")
        return True
    return False
