"""``compact_parent`` for the NOTING_WITH_COMPACTION profile (02 §5.7, §5.9).

Contract: the Parent either no longer requires compaction at the relevant threshold, or a
compaction request has been successfully admitted into the native Hermes compaction
lifecycle. The tool never waits for the Parent's complete compaction lifecycle, never
starts a compaction it has not proven admitted, and never forces past the native cooldown.

Native state only — no parallel admission flag, no second lock:

* usage is re-read from the Parent's live compressor right before the decision;
* "already below threshold" is the compressor's own verdict;
* "already in flight" requires the native fence's receipt after its safety checks;
* cooldown / anti-thrash gates are the compressor's own block reason, never bypassed;
* the request runs the Parent's native ``_compress_context`` entry (routing, locks, fences,
  retries, fallback and in-place-vs-rotating semantics all stay Hermes'); admission is
  proven by its safe admission receipt before summary execution.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from dataclasses import dataclass
from typing import Any, Optional

logger = logging.getLogger(__name__)

COMPACT_PARENT_SCHEMA = {
    "name": "compact_parent",
    "description": (
        "Ensure the Parent conversation no longer needs compaction: succeeds when it is already "
        "below the compaction threshold or when a compaction request was admitted into Hermes' "
        "native compaction lifecycle. Takes no arguments."
    ),
    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
}

# Bounded wait for the native safety-check receipt or a completed native outcome.
_ADMISSION_WAIT_SECONDS = 5.0
_ADMISSION_POLL_SECONDS = 0.05


@dataclass
class CompactParentResult:
    """``ok`` is the tool contract; ``status`` is the machine-readable reason."""

    ok: bool
    status: str
    usage_tokens: int = 0
    threshold_tokens: int = 0
    detail: str = ""

    def as_tool_result(self) -> str:
        return json.dumps({
            "success": self.ok,
            "status": self.status,
            "detail": self.detail,
            "usage_tokens": self.usage_tokens,
            "threshold_tokens": self.threshold_tokens,
        }, ensure_ascii=False)


def compact_parent_from_child(child: Any) -> str:
    """Tool entry for the Noting child: dispatch to the Parent this child belongs to."""
    if getattr(child, "_secretary_noting_profile", None) != "NOTING_WITH_COMPACTION":
        return json.dumps({"success": False, "status": "permission_denied"})
    parent = getattr(child, "_secretary_noting_parent", None)
    if parent is None:
        return json.dumps({"success": False, "status": "no_parent",
                           "detail": "This Noting child has no Parent binding"}, ensure_ascii=False)
    from secretary.noting_runtime import _main_conversation_ref, noting_trigger_gate
    ref = getattr(child, "_secretary_parent_conversation_ref", None)
    if (not ref or _main_conversation_ref(parent) != ref
            or not noting_trigger_gate(child._session_db, ref)[0]):
        return json.dumps({"success": False, "status": "parent_ownership_or_gate_changed"})
    result = compact_parent(parent, relevant_threshold_tokens=getattr(child, "_secretary_noting_compaction_threshold_tokens", None))
    if result.ok:
        child._secretary_noting_terminal_action_done = True
    return result.as_tool_result()


def _reread_usage(compressor: Any) -> tuple[int, int]:
    """``(usage_tokens, threshold_tokens)`` from the Parent's live compressor figures."""
    usage = max(
        int(getattr(compressor, "last_real_prompt_tokens", 0) or 0),
        int(getattr(compressor, "last_prompt_tokens", 0) or 0),
    )
    return usage, int(getattr(compressor, "threshold_tokens", 0) or 0)


def _native_inflight_evidence(parent: Any) -> str:
    """Native evidence that a materialization is already owned by the compaction lifecycle."""
    fence = getattr(parent, "_active_compression_commit_fence", None)
    if (fence is not None and getattr(fence, "_secretary_native_admitted", False) is True
            and not fence.is_cancelled):
        return "native_safe_admission"
    return ""


def compact_parent(parent: Any, *, wait_seconds: Optional[float] = None,
                   relevant_threshold_tokens: Optional[float] = None) -> CompactParentResult:
    """One ``compact_parent`` call against the Parent agent (see module docstring)."""
    compressor = getattr(parent, "context_compressor", None)
    if compressor is None or not hasattr(compressor, "should_compress_info"):
        return CompactParentResult(False, "no_compressor", detail="The Parent has no context compressor")
    usage, native_threshold = _reread_usage(compressor)
    threshold = native_threshold if relevant_threshold_tokens is None else relevant_threshold_tokens
    if usage < threshold:
        return CompactParentResult(True, "already_below_threshold", usage, threshold)
    inflight = _native_inflight_evidence(parent)
    if inflight:
        return CompactParentResult(True, "already_in_flight", usage, threshold, inflight)
    reason = _native_block_reason(parent)
    if reason:
        # Query native guards directly; no invented usage or threshold mutation.
        return CompactParentResult(False, f"blocked:{reason}", usage, threshold)
    messages = getattr(parent, "_session_messages", None)
    if not isinstance(messages, list):
        return CompactParentResult(False, "no_parent_transcript", usage, threshold)
    return _request_native_compaction(parent, messages, usage, threshold,
                                      wait_seconds=wait_seconds)


def _request_native_compaction(
    parent: Any, messages: list, usage: int, threshold: int, *, wait_seconds: Optional[float]
) -> CompactParentResult:
    """Run the Parent's native entry on a worker and return once admission is PROVEN."""
    from agent.memory_provider import spawn_context_thread

    state: dict = {}
    receipt = threading.Event()
    prompt = getattr(parent, "_cached_system_prompt", None) or ""
    session_id = parent.session_id

    def _run() -> None:
        try:
            from secretary.noting_scope import owning_db_scope
            with owning_db_scope(parent._session_db):
                state["result"] = parent._compress_context(
                    messages, prompt, approx_tokens=usage, trigger="noting_compact_parent",
                    admission_receipt=receipt, snapshot_is_current=lambda: parent.session_id == session_id,
                )
        except BaseException as exc:  # the native entry owns retries/fallbacks; this is terminal
            logger.debug("native compaction attempt ended with an error", exc_info=True)
            state["error"] = exc

    # Context-bound spawn: the attempt must run under the Parent's profile/conversation scope.
    worker = spawn_context_thread(_run, name="noting-compact-parent", daemon=True)
    worker.start()
    deadline = time.monotonic() + (_ADMISSION_WAIT_SECONDS if wait_seconds is None else wait_seconds)
    while True:
        if receipt.is_set():
            return CompactParentResult(True, "admitted", usage, threshold, "native_safe_admission")
        if not worker.is_alive():
            break
        if time.monotonic() >= deadline:
            return CompactParentResult(
                False, "admission_timeout", usage, threshold,
                "The native compaction lifecycle did not admit the request in time",
            )
        time.sleep(_ADMISSION_POLL_SECONDS)
    return _classify_finished_attempt(parent, messages, state, usage, threshold)


def _classify_finished_attempt(
    parent: Any, messages: list, state: dict, usage: int, threshold: int
) -> CompactParentResult:
    """The worker finished within the admission window: classify by native outcome."""
    if "error" in state:
        return CompactParentResult(False, "native_error", usage, threshold, str(state["error"]))
    result = state.get("result")
    result_messages = result[0] if isinstance(result, tuple) and result else None
    if isinstance(result_messages, list) and result_messages is not messages:
        return CompactParentResult(True, "compacted", usage, threshold)
    compressor = getattr(parent, "context_compressor", None)
    current_usage, _native_threshold = _reread_usage(compressor) if compressor is not None else (usage, 0)
    if current_usage < threshold:
        return CompactParentResult(True, "already_below_threshold", current_usage, threshold)
    reason = _native_block_reason(parent)
    if reason:
        return CompactParentResult(False, f"blocked:{reason}", usage, threshold)
    return CompactParentResult(
        False, "not_admitted", usage, threshold,
        "Still above the compaction threshold and the native lifecycle did not admit the request",
    )


def _native_block_reason(parent: Any) -> str:
    """The same refreshed automatic safety guard the native entry enforces, without token inputs."""
    from agent.conversation_compression import _automatic_compression_gate_blocks

    if not _automatic_compression_gate_blocks(parent, False):
        return ""
    reason = getattr(parent.context_compressor, "_compression_block_reason", None)
    return (reason() if callable(reason) else None) or "native_guard"
