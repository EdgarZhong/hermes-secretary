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
        assert main_usage_detail(child)["session_total"]["total_tokens"] is None


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
    assert latest["total_tokens"] is None
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
    assert latest["total_tokens"] is None
    abandon_main_turn_usage(a)
    finish_main_turn_usage(a, "t", {})
    assert main_usage_detail(a)["session_total"]["turns"] == 1


def test_total_uses_full_canonical_prompt_including_cache_writes():
    a = agent()
    begin_main_turn_usage(a, "first", has_prior_history=False)
    observe(a, {"prompt_tokens": 100, "completion_tokens": 20,
                "prompt_tokens_details": {"cached_tokens": 30, "cache_write_tokens": 40}})
    finish_main_turn_usage(a, "first", {})
    first = main_usage_detail(a)
    assert first["latest_completed_turn"]["total_tokens"] == 120
    assert first["latest_completed_turn"]["input_tokens"] == 30
    assert first["latest_completed_turn"]["cache_hit_rate"] == 0.5
    begin_main_turn_usage(a, "next", has_prior_history=True)
    observe(a, {"prompt_tokens": 50, "completion_tokens": 5})
    # The native full prompt remains exact despite omitted cache subdivisions.
    active = main_usage_detail(a)
    assert active["session_total"]["total_tokens"] == 175
    assert active["latest_completed_turn"]["total_tokens"] == 120
    finish_main_turn_usage(a, "next", {})
    finish_main_turn_usage(a, "next", {})
    assert main_usage_detail(a)["latest_completed_turn"]["total_tokens"] == 55
    assert main_usage_detail(a)["session_total"]["total_tokens"] == 175


def test_anthropic_total_requires_explicit_cache_write_including_zero():
    for write, expected in ((None, None), (0, 45), (40, 85)):
        a = agent()
        a.provider, a.api_mode = "anthropic", "anthropic_messages"
        usage = {"input_tokens": 10, "output_tokens": 5, "cache_read_input_tokens": 30}
        if write is not None:
            usage["cache_creation_input_tokens"] = write
        begin_main_turn_usage(a, "turn", has_prior_history=False)
        observe(a, usage)
        finish_main_turn_usage(a, "turn", {})
        detail = main_usage_detail(a)
        assert detail["session_total"]["total_tokens"] == expected
        assert detail["latest_completed_turn"]["total_tokens"] == expected


def test_cold_total_and_session_rotation_never_relabel_latest():
    a = agent()
    begin_main_turn_usage(a, "restored", has_prior_history=True)
    observe(a, {"prompt_tokens": 100, "completion_tokens": 20})
    finish_main_turn_usage(a, "restored", {})
    assert main_usage_detail(a)["session_total"]["total_tokens"] is None
    assert main_usage_detail(a)["latest_completed_turn"]["total_tokens"] == 120
    a.session_id = "rotated"
    begin_main_turn_usage(a, "new", has_prior_history=False)
    assert main_usage_detail(a)["latest_completed_turn"] is None
    observe(a, {"prompt_tokens": 10, "completion_tokens": 2})
    finish_main_turn_usage(a, "new", {})
    assert main_usage_detail(a)["session_total"]["total_tokens"] == 12


def test_inconsistent_complete_prompt_or_missing_output_keeps_total_unknown():
    for usage in ({"prompt_tokens": 10, "completion_tokens": 5, "cached_tokens": 30},
                  {"prompt_tokens": 10, "cached_tokens": 0}):
        a = agent()
        begin_main_turn_usage(a, "turn", has_prior_history=False)
        observe(a, usage)
        finish_main_turn_usage(a, "turn", {})
        assert main_usage_detail(a)["latest_completed_turn"]["total_tokens"] is None


def test_responses_total_known_without_cache_write_but_external_dispatch_unknown():
    for endpoint, expected in (("https://example.invalid", 120), ("acp://example", None)):
        a = agent(base_url=endpoint)
        a.api_mode = "codex_responses"
        begin_main_turn_usage(a, "turn", has_prior_history=False)
        observe(a, {"input_tokens": 100, "output_tokens": 20,
                    "input_tokens_details": {"cached_tokens": 30}})
        finish_main_turn_usage(a, "turn", {})
        assert main_usage_detail(a)["latest_completed_turn"]["total_tokens"] == expected
