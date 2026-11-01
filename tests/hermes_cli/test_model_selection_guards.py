"""Tests for the unified model-selection guard registry."""

from types import SimpleNamespace
from unittest.mock import patch

import pytest

from hermes_cli.model_selection_guards import (
    SelectionWarning,
    combined_selection_warning,
    selection_warnings,
)


def test_no_guard_fires_on_ordinary_model():
    # No pricing data (no provider), no data-policy rule match.
    assert selection_warnings("some/ordinary-model") == []
    assert combined_selection_warning("some/ordinary-model") is None


def test_data_policy_guard_fires_through_registry():
    warnings = selection_warnings("muse-spark-1.2-contributor", provider="custom")
    kinds = [w.kind for w in warnings]
    assert "data_policy" in kinds
    w = next(w for w in warnings if w.kind == "data_policy")
    assert "train" in w.message.lower()


def test_include_kinds_filters_guards():
    warnings = selection_warnings(
        "muse-spark-1.2-contributor",
        provider="custom",
        include_kinds=["cost"],
    )
    assert all(w.kind == "cost" for w in warnings)
    assert not any(w.kind == "data_policy" for w in warnings)


def test_combined_selection_warning_single():
    w = combined_selection_warning("muse-spark-1.2-contributor")
    assert w is not None
    assert w.kind == "data_policy"


def test_combined_selection_warning_merges_multiple():
    cost = SelectionWarning(
        kind="cost",
        title="Expensive Model Warning",
        model="m",
        provider="p",
        message="COST BLOCK",
    )
    policy = SelectionWarning(
        kind="data_policy",
        title="Data-Training Tier Warning",
        model="m",
        provider="p",
        message="POLICY BLOCK",
    )
    with patch(
        "hermes_cli.model_selection_guards._GUARDS",
        (lambda *a: cost, lambda *a: policy),
    ):
        merged = combined_selection_warning("m")
    assert merged is not None
    assert merged.kind == "multiple"
    assert "COST BLOCK" in merged.message
    assert "POLICY BLOCK" in merged.message


def test_misbehaving_guard_never_breaks_selection():
    def _boom(*args):
        raise RuntimeError("bad guard")

    with patch(
        "hermes_cli.model_selection_guards._GUARDS",
        (_boom,),
    ):
        assert selection_warnings("anything") == []


def test_cost_guard_still_fires_through_registry():
    # The registry must preserve the existing cost-guard behavior; feed it
    # explicit model_info so no network lookup is needed.
    from agent.models_dev import ModelInfo

    info = ModelInfo(
        id="pricey/model",
        name="pricey/model",
        family="",
        provider_id="anthropic",
        cost_input=50.0,
        cost_output=200.0,
    )
    warnings = selection_warnings(
        "pricey/model", provider="anthropic", model_info=info
    )
    assert any(w.kind == "cost" for w in warnings)


@pytest.mark.parametrize("measured", [0, -1, None])
def test_unknown_context_never_uses_cumulative_input_for_confirmation(measured):
    from hermes_cli.model_selection_guards import selection_context_for_agent

    agent = SimpleNamespace(
        model="current/model", session_prompt_tokens=390494,
        context_compressor=SimpleNamespace(last_prompt_tokens=measured))
    context = selection_context_for_agent(agent)
    assert context is None
    assert selection_warnings("next/model", include_kinds=["context_cache"],
                              selection_context=context) == []
    assert agent.session_prompt_tokens == 390494


@pytest.mark.parametrize("measured,asks", [(67067, False), (390494, True)])
def test_context_confirmation_uses_current_reading_not_lifetime_total(measured, asks):
    from hermes_cli.model_selection_guards import selection_context_for_agent

    agent = SimpleNamespace(
        model="current/model", session_prompt_tokens=25044309,
        context_compressor=SimpleNamespace(last_prompt_tokens=measured))
    context = selection_context_for_agent(agent)
    assert context.context_tokens == measured
    with patch("hermes_cli.model_selection_guards._context_cache_threshold", return_value=100000):
        warnings = selection_warnings("next/model", include_kinds=["context_cache"],
                                      selection_context=context)
    assert bool(warnings) is asks
