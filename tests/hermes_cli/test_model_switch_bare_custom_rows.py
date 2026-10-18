"""Configured bare custom endpoints remain selectable across provider switches."""

import hermes_cli.providers as providers_mod
import pytest

from hermes_cli.model_switch import list_authenticated_providers


@pytest.fixture(autouse=True)
def _disable_live_custom_provider_model_probe(monkeypatch):
    """Keep custom-provider picker fixtures independent of local model servers."""
    monkeypatch.setattr("hermes_cli.models.fetch_api_models", lambda *_a, **_kw: None)
    monkeypatch.setattr(
        "hermes_cli.models.cached_provider_model_ids", lambda *_a, **_kw: []
    )
    monkeypatch.setattr(
        "hermes_cli.models.provider_model_ids", lambda *_a, **_kw: []
    )
    monkeypatch.setattr(
        "hermes_cli.models_local.fetch_ollama_local_models", lambda *_a, **_kw: None
    )



def test_bare_custom_row_survives_a_switch_to_another_provider(monkeypatch):
    """#59702: the configured bare custom endpoint stays selectable after switching away.

    It used to be emitted only while it happened to be the active provider, so a session that
    moved to a canonical provider made the row vanish and offered no way back.
    """
    monkeypatch.setattr("agent.models_dev.fetch_models_dev", lambda: {})
    monkeypatch.setattr(providers_mod, "HERMES_OVERLAYS", {})
    monkeypatch.setattr("hermes_cli.models.fetch_api_models", lambda *a, **k: None)
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"model": {"provider": "custom", "base_url": "https://api.deepseek.com",
                           "default": "deepseek-flash"}},
    )

    rows = list_authenticated_providers(
        current_provider="deepseek",
        current_base_url="https://api.deepseek.com/v1",
        current_model="deepseek-flash",
        user_providers={},
        custom_providers=[],
        max_models=50,
        probe_custom_providers=False,
    )

    row = next(p for p in rows if p["slug"] == "custom")
    assert row["is_current"] is False
    assert row["api_url"] == "https://api.deepseek.com"
    assert row["models"] == ["deepseek-flash"]


def test_bare_custom_row_is_current_when_the_session_uses_it(monkeypatch):
    """The same row keeps its checkmark when the session is actually on that endpoint."""
    monkeypatch.setattr("agent.models_dev.fetch_models_dev", lambda: {})
    monkeypatch.setattr(providers_mod, "HERMES_OVERLAYS", {})
    monkeypatch.setattr("hermes_cli.models.fetch_api_models", lambda *a, **k: None)
    monkeypatch.setattr(
        "hermes_cli.config.load_config",
        lambda: {"model": {"provider": "custom", "base_url": "https://api.deepseek.com",
                           "default": "deepseek-flash"}},
    )

    rows = list_authenticated_providers(
        current_provider="custom",
        current_base_url="https://api.deepseek.com",
        current_model="deepseek-flash",
        user_providers={},
        custom_providers=[],
        max_models=50,
        probe_custom_providers=False,
    )

    row = next(p for p in rows if p["slug"] == "custom")
    assert row["is_current"] is True
