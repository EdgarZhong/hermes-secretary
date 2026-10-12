"""Ephemeral, read-only accounting over native Main model dispatch and canonical usage.

No persisted Turn ledger, provider adapter, response estimates, or changes to native counters.
Observation failures must never alter the model call, transcript, or Reminder lifecycle.
"""
from __future__ import annotations

import copy
import logging
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
_BUCKETS = ("input_tokens", "cache_read_tokens", "output_tokens")


def _now():
    return datetime.now(timezone.utc).isoformat()


def _main(agent):
    return not (getattr(agent, "is_subagent", False)
                or getattr(agent, "_secretary_noting_child", False)
                or getattr(agent, "_turn_origin", None))


@dataclass
class _Turn:
    turn_id: str
    calls: int = 0
    accounted: int = 0
    responded: int = 0
    failed: int = 0
    last_response: object = None
    tokens: dict = field(default_factory=lambda: dict.fromkeys(_BUCKETS, 0))
    unknown: set = field(default_factory=set)
    reasons: set = field(default_factory=set)


@dataclass
class _Owner:
    session_id: str
    cold: bool
    lock: object = field(default_factory=threading.RLock)
    active: _Turn | None = None
    latest: dict | None = None
    turns: int = 0
    tokens: dict = field(default_factory=lambda: dict.fromkeys(_BUCKETS, 0))
    unknown: set = field(default_factory=set)
    reasons: set = field(default_factory=set)


def begin_main_turn_usage(agent, turn_id, *, has_prior_history):
    """Called at the actual native prologue, before compaction or any provider call."""
    try:
        if not _main(agent):
            return
        sid = str(getattr(agent, "session_id", "") or "")
        owner = getattr(agent, "_main_usage_read", None)
        if owner is None or owner.session_id != sid:
            # Restored user rows include Steer. They prove prior history, not its Turn count.
            owner = _Owner(sid, bool(has_prior_history))
            agent._main_usage_read = owner
        with owner.lock:
            if owner.active is not None:
                owner.cold = True
                owner.reasons.add("overlapping_turns")
            owner.active = _Turn(turn_id)
            if getattr(agent, "api_mode", None) == "codex_app_server":
                owner.active.reasons.add("opaque_external_dispatch")
                owner.active.unknown.update(_BUCKETS)
    except Exception:
        logger.debug("Main usage prologue observation failed", exc_info=True)


@contextmanager
def observe_main_model_dispatch(agent):
    """Bracket the real native dispatch; SDK-internal HTTP retries remain opaque."""
    owner = getattr(agent, "_main_usage_read", None)
    turn = None
    try:
        if owner is not None and _main(agent):
            with owner.lock:
                turn = owner.active
                if turn is not None:
                    turn.calls += 1
                    if getattr(agent, "provider", None) == "moa":
                        turn.reasons.add("opaque_moa_calls")
                    base = str(getattr(agent, "base_url", "") or "").lower()
                    from hermes_cli.runtime_provider_backends import _is_external_process_provider
                    if base.startswith(("acp://", "acp+tcp://")) or _is_external_process_provider(
                            getattr(agent, "provider", "")):
                        turn.reasons.add("opaque_external_dispatch")
    except Exception:
        logger.debug("Main dispatch start observation failed", exc_info=True)
        turn = None
    receipt = [None]
    try:
        yield receipt
    except BaseException:
        if turn is not None:
            try:
                with owner.lock:
                    turn.failed += 1
                    turn.reasons.add("failed_dispatch")
            except Exception:
                logger.debug("Main dispatch failure observation failed", exc_info=True)
        raise
    else:
        if turn is not None:
            try:
                with owner.lock:
                    turn.responded += 1
                    turn.last_response = receipt[0]
            except Exception:
                logger.debug("Main response observation failed", exc_info=True)


def _has_usage_path(raw, paths):
    for path in paths:
        value = raw
        for key in path:
            value = value.get(key) if isinstance(value, dict) else getattr(value, key, None)
        if isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0:
            return True
    return False


def _unknown_buckets(agent, response):
    # Reuse native accounting's field semantics, never implement another normalizer.
    from agent.usage_pricing import _ANTHROPIC_USAGE_SHAPE, _CHAT_USAGE_SHAPE, _CODEX_USAGE_SHAPE
    mode = getattr(agent, "api_mode", None)
    provider = str(getattr(agent, "provider", "") or "").lower()
    shape = (_ANTHROPIC_USAGE_SHAPE if mode == "anthropic_messages" or provider == "anthropic"
             else _CODEX_USAGE_SHAPE if mode == "codex_responses" else _CHAT_USAGE_SHAPE)
    raw = getattr(response, "usage", None)
    unknown = set()
    if not _has_usage_path(raw, shape[0]):
        unknown.add("input_tokens")
    if not _has_usage_path(raw, shape[1]):
        unknown.add("output_tokens")
    if not _has_usage_path(raw, shape[2]):
        unknown.add("cache_read_tokens")
        if shape is not _ANTHROPIC_USAGE_SHAPE:
            unknown.add("input_tokens")
    return unknown


def observe_main_canonical_usage(agent, response, canonical_usage):
    """Observe exactly native recorded usage (after MoA folding), including no-usage calls."""
    try:
        owner = getattr(agent, "_main_usage_read", None)
        if owner is None or not _main(agent):
            return
        with owner.lock:
            turn = owner.active
            if turn is None:
                return
            if turn.last_response is not response:
                turn.reasons.add("unobserved_dispatch")
                turn.unknown.update(_BUCKETS)
            turn.accounted += 1
            # Drop the transient SDK object as soon as correspondence has been checked.
            turn.last_response = None
            if canonical_usage is None:
                turn.reasons.add("missing_usage")
                turn.unknown.update(_BUCKETS)
            else:
                for key in _BUCKETS:
                    count = getattr(canonical_usage, key)
                    turn.tokens[key] += count
                    owner.tokens[key] += count
                unknown = _unknown_buckets(agent, response)
                turn.unknown.update(unknown)
                if unknown:
                    turn.reasons.add("incomplete_usage_fields")
                if canonical_usage.request_count > 1:
                    turn.reasons.add("opaque_moa_calls")
                if "opaque_moa_calls" in turn.reasons:
                    turn.unknown.update(_BUCKETS)
                if (str(getattr(agent, "provider", "") or "").lower() in {"minimax", "minimax-cn"}
                        and getattr(agent, "api_mode", None) == "anthropic_messages"):
                    turn.reasons.add("incompatible_cache_semantics")
            owner.unknown.update(turn.unknown)
            owner.reasons.update(turn.reasons)
    except Exception:
        logger.debug("Canonical Main usage observation failed", exc_info=True)


def _metrics(tokens, unknown, reasons):
    values = {key: None if key in unknown else tokens[key] for key in _BUCKETS}
    input_count, cache = values["input_tokens"], values["cache_read_tokens"]
    denominator = input_count + cache if input_count is not None and cache is not None else 0
    values["cache_hit_rate"] = (cache / denominator if denominator
                               and "incompatible_cache_semantics" not in reasons else None)
    values["availability"] = "partial" if unknown or reasons else "available"
    values["reasons"] = sorted(reasons)
    return values


def note_unobserved_main_summary(agent):
    """Native iteration summary has no canonical accounting or authoritative call count."""
    try:
        owner = getattr(agent, "_main_usage_read", None)
        if owner is not None and _main(agent):
            with owner.lock:
                if owner.active is not None:
                    owner.active.reasons.add("unobserved_iteration_summary")
                    owner.active.unknown.update(_BUCKETS)
                    owner.unknown.update(_BUCKETS)
                    owner.reasons.add("unobserved_iteration_summary")
    except Exception:
        logger.debug("Main iteration summary observation failed", exc_info=True)


def finish_main_turn_usage(agent, turn_id, result):
    """Freeze only when the real finalizer has ended this Turn; don't rewrite old result."""
    try:
        owner = getattr(agent, "_main_usage_read", None)
        if owner is None or not _main(agent):
            return
        with owner.lock:
            turn = owner.active
            if turn is None or turn.turn_id != turn_id:
                return
            if turn.responded != turn.accounted:
                turn.reasons.add("unaccounted_response")
            if turn.failed or turn.responded != turn.accounted or "unobserved_dispatch" in turn.reasons:
                turn.unknown.update(_BUCKETS)
            opaque = {"opaque_moa_calls", "opaque_external_dispatch", "unobserved_iteration_summary"} & turn.reasons
            owner.latest = {
                **_metrics(turn.tokens, turn.unknown, turn.reasons),
                "turn_id": turn_id, "model_calls": None if opaque or "unobserved_dispatch" in turn.reasons else turn.calls,
                "model_calls_source": "unknown" if opaque or "unobserved_dispatch" in turn.reasons else "native_model_dispatch",
                "source": "native_canonical_accounting", "scope": "completed_main_turn",
                "completed_at": _now(),
            }
            if "turn_exception" in turn.reasons:
                owner.latest["availability"] = "unknown"
            owner.turns += 1
            owner.unknown.update(turn.unknown)
            owner.reasons.update(turn.reasons)
            owner.active = None
    except Exception:
        logger.debug("Main usage finalizer observation failed", exc_info=True)


def abandon_main_turn_usage(agent):
    """Gateway worker's real exception exit, without fabricating a successful envelope."""
    try:
        owner = getattr(agent, "_main_usage_read", None)
        if owner is None or not _main(agent):
            return
        with owner.lock:
            turn = owner.active
            if turn is None or turn.turn_id != getattr(agent, "_current_turn_id", None):
                return
            turn.reasons.add("turn_exception")
            turn.unknown.update(_BUCKETS)
            finish_main_turn_usage(agent, turn.turn_id, {})
    except Exception:
        logger.debug("Main exception exit observation failed", exc_info=True)


def unknown_usage_detail(reason="owner_unavailable"):
    return {"session_total": {**dict.fromkeys((*_BUCKETS, "cache_hit_rate", "turns")),
                              "availability": "unknown", "source": "unknown", "scope": "session",
                              "reasons": [reason]},
            "latest_completed_turn": None, "latest_turn_availability": "unknown", "observed_at": _now()}


def main_usage_detail(agent):
    """No owner creation, history scan, DB write, snapshot, or scheduling from reads."""
    owner = getattr(agent, "_main_usage_read", None)
    if owner is None or not _main(agent):
        return unknown_usage_detail()
    with owner.lock:
        current = str(getattr(agent, "session_id", "") or "")
        if owner.cold or current != owner.session_id:
            total = unknown_usage_detail("restored_session_totals_unknown")["session_total"]
        else:
            reasons = set(owner.reasons)
            unknown = set(owner.unknown)
            if owner.active is not None:
                reasons.update(owner.active.reasons)
                unknown.update(owner.active.unknown)
                if owner.active.failed or owner.active.responded != owner.active.accounted:
                    unknown.update(_BUCKETS)
                    reasons.add("unaccounted_response")
            total = {**_metrics(owner.tokens, unknown, reasons), "turns": owner.turns,
                     "source": "native_canonical_accounting", "scope": "session"}
        return {"session_total": total, "latest_completed_turn": copy.deepcopy(owner.latest),
                "latest_turn_availability": owner.latest["availability"] if owner.latest else "unknown",
                "observed_at": _now()}
