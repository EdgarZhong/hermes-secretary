"""Native cache-only catalog reads preserve authenticated bump/cap rules without HTTP."""
from types import SimpleNamespace

import pytest

from agent import model_metadata as metadata


@pytest.fixture
def catalog(monkeypatch):
    token, base = 'test-key', 'https://catalog.test.invalid/codex'
    key = metadata._codex_oauth_token_fingerprint(token, base)
    metadata._codex_oauth_context_cache.pop(key, None)
    metadata._codex_oauth_max_context_cache.pop(key, None)
    calls = []
    def get(url, **kwargs):
        calls.append(url)
        return SimpleNamespace(status_code=200, json=lambda: {'models': [
            {'slug': 'gpt-6.1-sol', 'context_window': 500000, 'max_context_window': 660000}]})
    monkeypatch.setattr(metadata.model_metadata_http, 'get', get)
    return token, base, key, calls


def test_cache_only_missing_and_expired_catalog_never_fetch(catalog):
    token, base, key, calls = catalog
    resolve = metadata._resolve_codex_oauth_context_length_with_source
    assert resolve('gpt-6.1-sol-900k', token, base, allow_network=False) == (None, '')
    metadata._codex_oauth_context_cache[key] = ({'gpt-6.1-sol': 500000},
        metadata.time.time() - metadata._CODEX_OAUTH_CONTEXT_CACHE_TTL - 1)
    metadata._codex_oauth_max_context_cache[key] = {'gpt-6.1-sol': 660000}
    assert resolve('gpt-6.1-sol-900k', token, base, allow_network=False) == (None, '')
    assert calls == []


def test_default_live_path_and_cache_only_path_agree_on_native_cap(catalog):
    token, base, _key, calls = catalog
    resolve = metadata._resolve_codex_oauth_context_length_with_source
    assert resolve('gpt-6.1-sol-900k', token, base) == (660000, 'live')
    assert len(calls) == 1
    assert resolve('gpt-6.1-sol-900k', token, base, allow_network=False) == (660000, 'memory')
    assert len(calls) == 1
    assert resolve('missing-model', token, base, allow_network=False) == (None, '')
    assert resolve('gpt-6.1-sol-900k', 'other-token', base, allow_network=False) == (None, '')
    assert resolve('gpt-6.1-sol-900k', token, 'https://other.test.invalid', allow_network=False) == (None, '')
    assert len(calls) == 1


def test_default_no_auth_fallback_is_unchanged_but_cache_only_rejects_it(catalog):
    _token, _base, _key, calls = catalog
    value, source = metadata._resolve_codex_oauth_context_length_with_source('gpt-6.1-sol-900k')
    assert value and source == 'fallback'
    assert metadata._resolve_codex_oauth_context_length_with_source(
        'gpt-6.1-sol-900k', allow_network=False) == (None, '')
    assert calls == []
