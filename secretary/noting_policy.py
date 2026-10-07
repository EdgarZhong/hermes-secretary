"""Pure Noting trigger policy: enable gate, Idle due, and the Force threshold formula.

02 §4.2 (global AND conversation-local), §4.5 (Idle from main Turns only), §4.6–§4.9 (Force
threshold with K = 1,000 tokens per A23), §4.10 (Idle runtime-profile selection). Nothing here
estimates tokens or touches an agent's request path: Force consumes Hermes's already-resolved
values (``ResolvedContextWindow`` / ``HermesResolvedAutoCompactionThreshold``) and the measured
context figure read at an existing Hermes measurement seam.

Force reserve arithmetic stays in integer tenths of a token, so the 1.20 multiplier never
rounds across a stated boundary: 64K/66K/128K are exactly 64,000 / 66,000 / 128,000 tokens, the
capability comparisons stay strict, and 128K is not a clamp.
"""

import logging
from dataclasses import dataclass
from typing import Any, Optional

from utils import is_truthy_value

logger = logging.getLogger(__name__)

K_TOKENS = 1_000

# 02 §4.6: exactly two capability failures, compared strictly against exact token counts (A23).
FORCE_THRESHOLD_FLOOR_TOKENS = 64 * K_TOKENS              # ForceNotingThreshold < 64K fails
FORCE_RESERVE_FLOOR_TENTHS = 66 * K_TOKENS * 10           # max(…, 66K) floor, in tenths
FORCE_RESERVE_CEILING_TENTHS = 128 * K_TOKENS * 10        # ForceNotingReserve > 128K fails
FORCE_RESERVE_MULTIPLIER_NUM, FORCE_RESERVE_MULTIPLIER_DEN = 12, 10   # 1.20

CAPABILITY_THRESHOLD_BELOW_64K = "threshold_below_64k"
CAPABILITY_RESERVE_ABOVE_128K = "reserve_above_128k"

# Runtime profiles of a Noting Task after an Idle Trigger (02 §4.10); the Notebook sibling
# records the same two names on a committed Snapshot.
TASK_PROFILE_NOTING = "NOTING"
TASK_PROFILE_NOTING_WITH_COMPACTION = "NOTING_WITH_COMPACTION"

DEFAULT_IDLE_DELAY_SECONDS = 500.0


@dataclass(frozen=True)
class NotingSettings:
    """The effective ``noting:`` configuration block (02 §4.1)."""

    enabled: bool
    idle_delay_seconds: float
    auto_trigger_compaction_enabled: bool
    auto_trigger_compaction_threshold_tokens: Optional[int]
    auto_compact_after_force_noting_idle: bool


def _number(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def _positive_int(value: Any) -> Optional[int]:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        return None
    return value


def noting_settings_from_config(config: Any) -> NotingSettings:
    """Parse the ``noting`` block tolerantly; spec defaults apply to missing or malformed keys."""
    block = config.get("noting") if isinstance(config, dict) else None
    if not isinstance(block, dict):
        block = {}
    enabled = is_truthy_value(block.get("enabled"), default=True)
    delay = _number(block.get("idle_delay_seconds"))
    if delay is None or delay < 0:
        delay = DEFAULT_IDLE_DELAY_SECONDS
    selection = block.get("auto_trigger_compaction_after_noting")
    selection = selection if isinstance(selection, dict) else {}
    return NotingSettings(
        enabled=bool(enabled),
        idle_delay_seconds=delay,
        auto_trigger_compaction_enabled=bool(selection.get("enabled", False)),
        auto_trigger_compaction_threshold_tokens=_positive_int(selection.get("threshold_tokens")),
        auto_compact_after_force_noting_idle=bool(block.get("auto_compact_after_force_noting_idle", False)),
    )


def disabled_noting_settings() -> NotingSettings:
    """Everything inert — the fail-closed fallback when the config cannot be read."""
    return NotingSettings(False, DEFAULT_IDLE_DELAY_SECONDS, False, None, False)


def resolve_noting_settings() -> NotingSettings:
    """Read the live config; an unreadable config disables Noting rather than guessing."""
    try:
        from hermes_cli.config import load_config_readonly

        return noting_settings_from_config(load_config_readonly())
    except Exception:
        logger.warning("noting config unreadable; treating Noting as disabled", exc_info=True)
        return disabled_noting_settings()


def effective_noting_enabled(settings: NotingSettings, local_enabled: bool) -> bool:
    """02 §4.2: global Noting AND conversation-local participation."""
    return bool(settings.enabled) and bool(local_enabled)


def idle_due(
    last_turn_started_at: Optional[float],
    last_turn_finished_at: Optional[float],
    *,
    now: float,
    delay_seconds: float,
) -> bool:
    """02 §4.5: a main Turn finished, no newer main Turn started, and the delay has elapsed."""
    if last_turn_finished_at is None:
        return False
    if last_turn_started_at is not None and last_turn_started_at >= last_turn_finished_at:
        return False
    return float(now) - float(last_turn_finished_at) >= float(delay_seconds)


@dataclass(frozen=True)
class ForceThresholds:
    """02 §4.6 derived values. Comparisons stay exact in tenths of a token."""

    resolved_context_window: int
    hermes_auto_compaction_threshold: int
    auto_compaction_reserve: int
    force_noting_reserve_tenths: int
    force_noting_threshold_tenths: int
    capability_failure: Optional[str]

    @property
    def force_noting_reserve(self) -> float:
        return self.force_noting_reserve_tenths / 10

    @property
    def force_noting_threshold(self) -> float:
        return self.force_noting_threshold_tenths / 10

    @property
    def usable(self) -> bool:
        return self.capability_failure is None

    @property
    def invariant_holds(self) -> bool:
        """``ForceNotingThreshold < HermesResolvedAutoCompactionThreshold`` (02 §4.6)."""
        return self.force_noting_threshold_tenths < self.hermes_auto_compaction_threshold * 10

    def measured_usage_triggers(self, measured_tokens: Any) -> bool:
        """02 §4.11: ``measured usage >= ForceNotingThreshold`` (never a locally estimated figure)."""
        tokens = _positive_int(measured_tokens)
        if self.capability_failure is not None or tokens is None:
            return False
        return tokens * 10 >= self.force_noting_threshold_tenths


def force_thresholds(resolved_context_window: Any, hermes_auto_compaction_threshold: Any) -> ForceThresholds:
    """Derive the Force values from Hermes's already-resolved pair (02 §4.6)."""
    window = _positive_int(resolved_context_window)
    hermes = _positive_int(hermes_auto_compaction_threshold)
    if window is None or hermes is None:
        raise ValueError("Force thresholds require Hermes-resolved positive token counts")
    auto_reserve = window - hermes
    reserve_tenths = max(auto_reserve * FORCE_RESERVE_MULTIPLIER_NUM, FORCE_RESERVE_FLOOR_TENTHS)
    threshold_tenths = window * 10 - reserve_tenths
    return ForceThresholds(
        resolved_context_window=window,
        hermes_auto_compaction_threshold=hermes,
        auto_compaction_reserve=auto_reserve,
        force_noting_reserve_tenths=reserve_tenths,
        force_noting_threshold_tenths=threshold_tenths,
        capability_failure=force_capability_failure(
            force_noting_reserve_tenths=reserve_tenths,
            force_noting_threshold_tenths=threshold_tenths,
        ),
    )


def force_capability_failure(
    *, force_noting_reserve_tenths: int, force_noting_threshold_tenths: int
) -> Optional[str]:
    """The exactly-two capability failures of 02 §4.6, compared strictly in tenths of a token.

    ``ForceNotingThreshold < 64,000`` and ``ForceNotingReserve > 128,000`` fail; exact equality
    passes, and 128K never clamps the derived values.
    """
    if force_noting_threshold_tenths < FORCE_THRESHOLD_FLOOR_TOKENS * 10:
        return CAPABILITY_THRESHOLD_BELOW_64K
    if force_noting_reserve_tenths > FORCE_RESERVE_CEILING_TENTHS:
        return CAPABILITY_RESERVE_ABOVE_128K
    return None


@dataclass(frozen=True)
class ContextMeasurement:
    """One context reading at a Hermes measurement seam, with the resolved window pair."""

    measured_tokens: int
    resolved_context_window: int
    hermes_auto_compaction_threshold: int


def measurement_from_agent(agent: Any, measured_tokens: Any) -> Optional[ContextMeasurement]:
    """Pair a measured usage figure with the agent's already-resolved window/threshold.

    ``context_compressor.context_length`` and ``.threshold_tokens`` are the values Hermes
    resolved for this agent (config overrides, catalog, endpoint probe); nothing is estimated
    here, and an agent without them (e.g. a scripted client) yields None.
    """
    tokens = _positive_int(measured_tokens)
    compressor = getattr(agent, "context_compressor", None)
    window = _positive_int(getattr(compressor, "context_length", None))
    threshold = _positive_int(getattr(compressor, "threshold_tokens", None))
    if tokens is None or window is None or threshold is None:
        return None
    return ContextMeasurement(tokens, window, threshold)


def idle_task_profile(settings: NotingSettings, measurement: Optional[ContextMeasurement]) -> str:
    """02 §4.10 below-Force branch: which runtime profile an admitted Idle Task gets."""
    if not settings.auto_trigger_compaction_enabled:
        return TASK_PROFILE_NOTING
    threshold = settings.auto_trigger_compaction_threshold_tokens
    if measurement is None or threshold is None:
        return TASK_PROFILE_NOTING
    if measurement.measured_tokens >= threshold:
        return TASK_PROFILE_NOTING_WITH_COMPACTION
    return TASK_PROFILE_NOTING
