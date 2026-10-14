"""Additive Main usage projection. Unknown counters are explicit nulls."""
from typing import Literal

from pydantic import Field

from .base import Params, Result
from .registry import method

UsageReason = Literal["owner_unavailable", "hosted_owner_unavailable", "restored_session_totals_unknown",
                      "overlapping_turns", "failed_dispatch", "missing_usage", "incomplete_usage_fields",
                      "incompatible_cache_semantics", "opaque_moa_calls", "opaque_external_dispatch",
                      "unobserved_dispatch", "unaccounted_response", "turn_exception",
                      "unobserved_iteration_summary"]


class UsageDetailParams(Params):
    session_id: str = Field(min_length=1)
    profile: str | None = None


class UsageCounters(Result):
    input_tokens: int | None
    cache_read_tokens: int | None
    output_tokens: int | None
    total_tokens: int | None = None
    cache_hit_rate: float | None
    availability: Literal["available", "partial", "unknown"]
    source: Literal["native_canonical_accounting", "unknown"]
    reasons: list[UsageReason]


class SessionUsageTotal(UsageCounters):
    turns: int | None
    scope: Literal["session"]


class CompletedTurnUsage(UsageCounters):
    turn_id: str
    model_calls: int | None
    model_calls_source: Literal["native_model_dispatch", "unknown"]
    scope: Literal["completed_main_turn"]
    completed_at: str


class UsageDetailResult(Result):
    session_id: str
    stored_session_id: str | None
    session_total: SessionUsageTotal
    latest_completed_turn: CompletedTurnUsage | None
    latest_turn_availability: Literal["available", "partial", "unknown"]
    observed_at: str


method("session.usage_detail", params=UsageDetailParams, result=UsageDetailResult)
