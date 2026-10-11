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
        child._secretary_noting_termination = {"type": "compact_parent"}
    return result.as_tool_result()


def compact_parent(parent: Any, *, wait_seconds: Optional[float] = None,
                   relevant_threshold_tokens: Optional[float] = None) -> CompactParentResult:
    """Noting only requests compaction; the native Parent owns its context."""
    request = getattr(parent, 'request_context_compaction', None)
    if not callable(request):
        return CompactParentResult(False, 'no_compressor' if getattr(parent, 'context_compressor', None) is None
                                   else 'no_native_request_interface')
    result = request(relevant_threshold_tokens=relevant_threshold_tokens,
                     wait_seconds=_ADMISSION_WAIT_SECONDS if wait_seconds is None else wait_seconds)
    return CompactParentResult(result.ok, result.status, result.usage_tokens,
                               result.threshold_tokens, result.detail)
