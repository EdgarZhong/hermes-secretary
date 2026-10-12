"""Projection safety at unknown/opaque boundaries; actual loops are tested separately."""
from types import SimpleNamespace

from agent.usage_pricing import normalize_usage
from agent.usage_read import (abandon_main_turn_usage, begin_main_turn_usage, finish_main_turn_usage, main_usage_detail,
                              observe_main_canonical_usage, observe_main_model_dispatch)


def agent(**kw):
    return SimpleNamespace(session_id="stored", provider="openai", api_mode="chat_completions", **kw)


def observe(a, usage):
    answer = SimpleNamespace(usage=usage)
    with observe_main_model_dispatch(a) as receipt:
        receipt[0] = answer
    observe_main_canonical_usage(a, answer, normalize_usage(usage, provider=a.provider, api_mode=a.api_mode))


def test_read_never_creates_owner():
    a = agent()
    assert main_usage_detail(a)["latest_completed_turn"] is None
    assert not hasattr(a, "_main_usage_read")


def test_noting_and_generic_subagents_are_not_parent_main_usage():
    for flags in ({"_secretary_noting_child": True}, {"is_subagent": True}, {"_turn_origin": "review"}):
        child = agent(**flags)
        begin_main_turn_usage(child, "child", has_prior_history=False)
        observe(child, {"prompt_tokens": 100, "completion_tokens": 20})
        finish_main_turn_usage(child, "child", {})
        assert not hasattr(child, "_main_usage_read")
        assert main_usage_detail(child)["session_total"]["input_tokens"] is None


def test_provider_response_rejected_before_canonical_never_guesses_tokens():
    a = agent()
    begin_main_turn_usage(a, "t", has_prior_history=False)
    with observe_main_model_dispatch(a) as receipt:
        receipt[0] = SimpleNamespace(usage={"prompt_tokens": 100})
    finish_main_turn_usage(a, "t", {})
    latest = main_usage_detail(a)["latest_completed_turn"]
    assert latest["model_calls"] == 1 and latest["input_tokens"] is None
    assert "unaccounted_response" in latest["reasons"]


def test_missing_cache_fields_are_not_reported_as_zero_or_exact_uncached_input():
    a = agent()
    begin_main_turn_usage(a, "t", has_prior_history=False)
    observe(a, {"prompt_tokens": 100, "completion_tokens": 20})
    finish_main_turn_usage(a, "t", {})
    latest = main_usage_detail(a)["latest_completed_turn"]
    assert latest["input_tokens"] is None and latest["cache_read_tokens"] is None
    assert latest["output_tokens"] == 20 and latest["cache_hit_rate"] is None


def test_session_boundary_does_not_relabel_old_total_as_new_session():
    a = agent()
    begin_main_turn_usage(a, "t", has_prior_history=False)
    observe(a, {"prompt_tokens": 100, "completion_tokens": 20, "prompt_cache_hit_tokens": 30})
    finish_main_turn_usage(a, "t", {})
    a.session_id = "rotated"
    assert main_usage_detail(a)["session_total"]["availability"] == "unknown"
    begin_main_turn_usage(a, "next", has_prior_history=True)
    assert main_usage_detail(a)["latest_completed_turn"] is None


def test_moa_opaque_calls_and_tokens_remain_unknown():
    a = agent()
    a.provider = "moa"
    begin_main_turn_usage(a, "t", has_prior_history=False)
    observe(a, {"prompt_tokens": 100, "completion_tokens": 20, "prompt_cache_hit_tokens": 30})
    finish_main_turn_usage(a, "t", {})
    latest = main_usage_detail(a)["latest_completed_turn"]
    assert latest["model_calls"] is None and latest["input_tokens"] is None
    assert latest["model_calls_source"] == "unknown" and "opaque_moa_calls" in latest["reasons"]


def test_abandon_and_unbound_finish_cannot_refinish_previous_turn():
    a = agent(_current_turn_id="t")
    finish_main_turn_usage(a, "t", {})
    assert not hasattr(a, "_main_usage_read")
    begin_main_turn_usage(a, "t", has_prior_history=False)
    observe(a, {"prompt_tokens": 100, "completion_tokens": 20, "prompt_cache_hit_tokens": 30})
    abandon_main_turn_usage(a)
    latest = main_usage_detail(a)["latest_completed_turn"]
    assert latest["availability"] == "unknown" and "turn_exception" in latest["reasons"]
    assert latest["input_tokens"] is None and main_usage_detail(a)["session_total"]["turns"] == 1
    abandon_main_turn_usage(a)
    finish_main_turn_usage(a, "t", {})
    assert main_usage_detail(a)["session_total"]["turns"] == 1
