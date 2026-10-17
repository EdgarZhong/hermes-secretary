"""Usage-anchored token accounting: the provider's real ``usage.prompt_tokens`` is the only
authoritative context size; the local ``bytes/4`` estimate covers ONLY messages appended since.

An anchor = provider usage at capture + a snapshot of the transcript position it priced:
``base_count`` (len(messages) at capture; the reply is not yet appended and is covered by
``completion_tokens``, so the delta walk skips an assistant row at that index), ``base_last_role``
and ``base_last_fp`` (content fingerprint of the last priced message; compaction, splices and
rewinds replace it → anchor fails closed → full estimation until the next real reading).

The fingerprint (not ``id()``) is the identity: the gateway re-reads the transcript from the DB
every turn and a resumed session runs in a fresh process, so object identity is never stable
across the surfaces where the estimate mattered most (#99421, #104462). The anchor also persists
on the session row (``model_config._usage_anchor``) so a restarted process can restore it; a
restored anchor is honored only while the durable transcript still matches its fingerprint.
The separate optional ``_usage_context`` metadata is a cold display estimate only: compaction
may replace it with native rough usage, and it never restores an exact engine anchor.
"""

from __future__ import annotations

import hashlib
import json
import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

USAGE_ANCHOR_MODEL_CONFIG_KEY = "_usage_anchor"
USAGE_CONTEXT_MODEL_CONFIG_KEY = "_usage_context"

# Identity of a priced message = the provider-visible fields that round-trip the session DB
# byte-for-byte. Display/persistence metadata (timestamps, row ids, display kinds) is rewritten
# on reload and would only ever fail the match closed.
_FINGERPRINT_KEYS = ("role", "content", "api_content", "tool_call_id", "tool_calls")


def message_fingerprint(msg: Any) -> Optional[str]:
    """Stable digest of one transcript message over its provider-visible, persisted fields."""
    if not isinstance(msg, dict):
        return None
    payload = {k: msg.get(k) for k in _FINGERPRINT_KEYS if msg.get(k) is not None}
    try:
        raw = json.dumps(payload, sort_keys=True, default=str, ensure_ascii=True, separators=(",", ":"))
    except (TypeError, ValueError):
        raw = repr(sorted(payload.items()))
    return hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest()


def _priced_prefix_fingerprint(messages: List[Dict[str, Any]], base_count: int) -> Optional[str]:
    """Stable digest of the whole provider-priced prefix.

    The last priced message fingerprint proves only that one row survived at
    ``base_count - 1``. A compaction can preserve that row while rewriting the
    earlier prefix, so the anchor must also bind to the full priced prefix it
    represents.
    """
    if base_count <= 0 or len(messages) < base_count:
        return None
    fps = []
    for msg in messages[:base_count]:
        fp = message_fingerprint(msg)
        if not fp:
            return None
        role = msg.get("role") if isinstance(msg, dict) else None
        fps.append((role, fp))
    raw = json.dumps(fps, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(raw.encode("utf-8", "replace")).hexdigest()


def capture_usage_anchor(
    prompt_tokens: Any, completion_tokens: Any, messages: List[Dict[str, Any]],
    model: Any = None,
) -> Optional[Dict[str, Any]]:
    """Build a usage anchor from provider-reported usage, or None when usage is unusable.

    ``model`` records WHICH route priced ``prompt_tokens`` so a later restore can tell whether the
    number still describes the current model. It is optional and additive: anchors persisted before
    this field existed simply have no opinion (consumers treat them as unknown, never stale)."""
    try:
        pt = int(prompt_tokens or 0)
        ct = int(completion_tokens or 0)
    except (TypeError, ValueError):
        return None
    if pt <= 0 or not isinstance(messages, list) or not messages:
        return None  # some endpoints omit usage — caller keeps its anchor
    last = messages[-1]
    anchor = {
        "prompt_tokens": pt,
        "completion_tokens": max(0, ct),
        "base_count": len(messages),
        "base_last_role": last.get("role") if isinstance(last, dict) else None,
        "base_last_fp": message_fingerprint(last),
        "base_prefix_fp": _priced_prefix_fingerprint(messages, len(messages)),
    }
    priced_by = _normalized_model(model)
    if priced_by:
        anchor["model"] = priced_by
    return anchor


def _normalized_model(model: Any) -> Optional[str]:
    """Comparable model identity for the anchor; None when unknown (never a stale verdict)."""
    value = str(model or "").strip().lower()
    return value or None


def _anchor_matches(messages: List[Dict[str, Any]], anchor: Dict[str, Any]) -> bool:
    try:
        base_count = int(anchor.get("base_count") or 0)
    except (TypeError, ValueError):
        return False
    if base_count <= 0 or len(messages) < base_count:
        return False
    base_msg = messages[base_count - 1]
    if not isinstance(base_msg, dict) or base_msg.get("role") != anchor.get("base_last_role"):
        return False
    fp = anchor.get("base_last_fp")
    if not isinstance(fp, str) or not fp or message_fingerprint(base_msg) != fp:
        return False
    prefix_fp = anchor.get("base_prefix_fp")
    return (
        isinstance(prefix_fp, str)
        and bool(prefix_fp)
        and _priced_prefix_fingerprint(messages, base_count) == prefix_fp
    )


def anchored_context_tokens(messages: List[Dict[str, Any]], anchor: Optional[Dict[str, Any]], *, charge_stale_thinking: bool = True) -> Optional[int]:
    """Anchored prompt+completion tokens plus a rough estimate of ONLY the messages appended since;
    None when the anchor is missing or stale. The anchored response's own reply is skipped (already
    in completion_tokens). ``charge_stale_thinking`` is forwarded to the delta estimate."""
    if not isinstance(anchor, dict) or not isinstance(messages, list) or not _anchor_matches(messages, anchor):
        return None
    from agent.model_metadata import estimate_messages_tokens_rough

    total = int(anchor["prompt_tokens"]) + int(anchor.get("completion_tokens") or 0)
    delta = messages[int(anchor["base_count"]):]
    if delta and isinstance(delta[0], dict) and delta[0].get("role") == "assistant":
        delta = delta[1:]
    if delta:
        total += estimate_messages_tokens_rough(delta, charge_stale_thinking=charge_stale_thinking)
    return total


def _serialize(anchor: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(anchor, dict):
        return None
    try:
        pt, ct, base_count = (int(anchor.get(k) or 0) for k in ("prompt_tokens", "completion_tokens", "base_count"))
    except (TypeError, ValueError):
        return None
    fp, role = anchor.get("base_last_fp"), anchor.get("base_last_role")
    prefix_fp = anchor.get("base_prefix_fp")
    if (
        pt <= 0
        or base_count <= 0
        or not isinstance(fp, str)
        or not fp
        or not isinstance(prefix_fp, str)
        or not prefix_fp
    ):
        return None
    serialized = {"prompt_tokens": pt, "completion_tokens": max(0, ct), "base_count": base_count,
                  "base_last_role": role if isinstance(role, str) else None, "base_last_fp": fp,
                  "base_prefix_fp": prefix_fp}
    priced_by = _normalized_model(anchor.get("model"))
    if priced_by:
        serialized["model"] = priced_by
    return serialized


def _display_context_snapshot(agent: Any, anchor: Any, context_estimate: Any) -> Optional[Dict[str, Any]]:
    """Prepare display metadata without making native exact-anchor persistence depend on it."""
    if anchor is None and context_estimate is None:
        return None
    try:
        row_getter = getattr(agent._session_db, "get_session", None)
        row = row_getter(agent.session_id) if callable(row_getter) else None
        if not isinstance(row, dict):
            return None
        tokens = anchor["prompt_tokens"] + anchor["completion_tokens"] if anchor else int(context_estimate)
        if tokens < 0:
            return None
        return {
            "session_id": agent.session_id, "tokens": tokens, "rewind_count": int(row.get("rewind_count") or 0),
            "model": anchor.get("model") if anchor else _normalized_model(getattr(agent, "model", None)),
            "source": "usage_anchor" if anchor else "local_estimate",
        }
    except Exception:
        logger.debug("display context snapshot unavailable", exc_info=True)
        return None


def persist_usage_anchor(
    agent: Any, anchor: Optional[Dict[str, Any]], *, context_estimate: Optional[int] = None,
) -> None:
    """Write (or clear, ``None``) the session row's anchor blob. Best-effort: the row may not exist yet."""
    if getattr(agent, "_persist_disabled", False):
        return
    session_id = getattr(agent, "session_id", None)
    patcher = getattr(getattr(agent, "_session_db", None), "patch_session_model_config", None)
    if not session_id or not callable(patcher):
        return
    try:
        serialized = _serialize(anchor)
        patch = {USAGE_ANCHOR_MODEL_CONFIG_KEY: serialized}
        snapshot = _display_context_snapshot(agent, serialized, context_estimate)
        if snapshot is not None:
            patch[USAGE_CONTEXT_MODEL_CONFIG_KEY] = snapshot
        patcher(session_id, patch)
    except Exception:
        logger.debug("usage anchor persist failed", exc_info=True)


def persist_context_estimate(agent: Any, tokens: int) -> None:
    """Save a native display estimate without touching the exact anchor; unchanged polls do not write."""
    if getattr(agent, "_persist_disabled", False):
        return
    snapshot = _display_context_snapshot(agent, None, tokens)
    if snapshot is None:
        return
    db = getattr(agent, "_session_db", None)
    try:
        current = db.get_session_model_config_value(agent.session_id, USAGE_CONTEXT_MODEL_CONFIG_KEY, None)
        if current != snapshot:
            db.patch_session_model_config(agent.session_id, {USAGE_CONTEXT_MODEL_CONFIG_KEY: snapshot})
    except Exception:
        logger.debug("display context estimate persist failed", exc_info=True)


def set_usage_anchor(
    agent: Any, anchor: Optional[Dict[str, Any]], *, turn_base: bool = False, context_estimate: Optional[int] = None,
) -> None:
    """Install ``anchor`` on the agent (``None`` clears) and mirror it to the session row."""
    agent._usage_anchor = anchor
    if turn_base or anchor is None:
        agent._turn_base_usage_anchor = anchor
    persist_usage_anchor(agent, anchor, context_estimate=context_estimate)


def restore_usage_anchor(agent: Any, conversation_history: Optional[List[Dict[str, Any]]]) -> None:
    """On a resumed session, adopt the persisted anchor when ``conversation_history`` still carries
    the priced prefix; otherwise clear the stale blob so it can never suppress compression."""
    if getattr(agent, "_usage_anchor", None) is not None or getattr(agent, "_persist_disabled", False):
        return
    session_id = getattr(agent, "session_id", None)
    getter = getattr(getattr(agent, "_session_db", None), "get_session_model_config_value", None)
    if not session_id or not callable(getter) or not isinstance(conversation_history, list):
        return
    try:
        anchor = _serialize(getter(session_id, USAGE_ANCHOR_MODEL_CONFIG_KEY, None))
    except Exception:
        logger.debug("usage anchor load failed", exc_info=True)
        return
    if anchor is None:
        return
    if _anchor_matches(conversation_history, anchor):
        agent._usage_anchor = anchor
    else:
        persist_usage_anchor(agent, None)


def persisted_anchor_tokens(session_db: Any, session_id: Any, messages: Any) -> Optional[int]:
    """Anchored token figure from the session row's persisted anchor, for callers without a live
    agent (gateway hygiene); None when absent, unreadable, or stale against ``messages``."""
    context = persisted_anchor_context(session_db, session_id, messages)
    return context["tokens"] if context else None


def persisted_anchor_context(
    session_db: Any, session_id: Any, messages: Any, *, model: Any = None,
) -> Optional[Dict[str, Any]]:
    """Anchored context figure plus a model verdict, for callers without a live agent.

    Returns ``{"tokens": <prompt+completion>, "model_matches": True | False | None}``. The overall
    result is None when the anchor is absent, unreadable, or stale against ``messages`` — the
    fingerprint check is the caller's proof that the number still describes this transcript.
    ``model_matches`` is None when the stored anchor predates model recording (no opinion) and
    False only when the anchor names a different route than the caller's ``model``."""
    getter = getattr(session_db, "get_session_model_config_value", None)
    if not session_id or not callable(getter) or not isinstance(messages, list):
        return None
    try:
        anchor = _serialize(getter(session_id, USAGE_ANCHOR_MODEL_CONFIG_KEY, None))
    except Exception:
        logger.debug("usage anchor load failed", exc_info=True)
        return None
    if not anchor or not _anchor_matches(messages, anchor):
        return None
    tokens = anchored_context_tokens(messages, anchor)
    if tokens is None:
        return None
    current = _normalized_model(model)
    priced_by = _normalized_model(anchor.get("model"))
    verdict = None if not current or not priced_by else priced_by == current
    return {"tokens": tokens, "model_matches": verdict}


def persisted_context_estimate(
    session_db: Any, session_id: Any, messages: Any = None, *, model: Any = None,
) -> Optional[Dict[str, Any]]:
    """Read-only cold display estimate, never an input to native compression accounting.

    Native exact anchors may be cleared on compaction or replay repair. Their last observed
    reading, or the compaction owner's rough estimate, survives for the display until another
    native reading replaces it. A durable rewind or known model mismatch invalidates it.
    No transcript load or agent construction is needed for deferred-history resumes.
    A known invalidation returns only ``invalidation_reason`` so incremental clients can
    retire a previous readout; absent or unreadable readings return None.
    """
    getter = getattr(session_db, "get_session", None)
    if not session_id or not callable(getter):
        return None
    try:
        row = getter(session_id)
        if not isinstance(row, dict):
            return None
        config = row.get("model_config") or {}
        if isinstance(config, str):
            config = json.loads(config)
        if not isinstance(config, dict):
            return None
        anchor = _serialize(config.get(USAGE_ANCHOR_MODEL_CONFIG_KEY))
        reading = config.get(USAGE_CONTEXT_MODEL_CONFIG_KEY)
        rewind_count = int(row.get("rewind_count") or 0)
        if isinstance(reading, dict):
            if reading.get("session_id") != session_id:
                return None
            if int(reading["rewind_count"]) != rewind_count:
                return {"invalidation_reason": "rewind"}
        elif anchor and rewind_count == 0:
            # Earlier native anchors have no rewind generation; only an untouched Session
            # can safely reuse one as a display estimate.
            reading = {"tokens": anchor["prompt_tokens"] + anchor["completion_tokens"],
                       "model": anchor.get("model"), "source": "usage_anchor"}
        elif anchor and rewind_count > 0:
            return {"invalidation_reason": "rewind"}
        else:
            return None
        current, priced_by = _normalized_model(model), _normalized_model(reading.get("model"))
        if current and priced_by and current != priced_by:
            return {"invalidation_reason": "model_changed"}
        tokens = int(reading["tokens"])
        if tokens < 0:
            return None
        # Preserve the native delta estimate when the exact priced prefix still matches.
        precise = anchored_context_tokens(messages, anchor) if isinstance(messages, list) else None
        return {"tokens": precise if precise is not None else tokens,
                "source": "usage_anchor" if precise is not None else reading.get("source") or "usage_anchor"}
    except Exception:
        logger.debug("cold display estimate load failed", exc_info=True)
        return None
