"""Codex context selection with the native catalog/cache and its existing bump/cap rules."""
from __future__ import annotations

from agent import model_metadata as metadata


def _catalog(access_token, base_url, *, allow_network):
    if allow_network:
        return metadata._fetch_codex_oauth_context_lengths_with_source(access_token, base_url=base_url)
    # Select the existing native snapshot here; a cache-only caller never enters fetch.
    key = metadata._codex_oauth_token_fingerprint(access_token, base_url)
    cached = metadata._codex_oauth_context_cache.get(key)
    if cached and cached[0] and metadata.time.time() - cached[1] < metadata._CODEX_OAUTH_CONTEXT_CACHE_TTL:
        return cached[0], False
    return {}, False


def resolve_context(model, access_token="", base_url="", *, allow_network=True):
    """Existing native selection; cache-only reads reject absent/expired catalog evidence."""
    model_bare = metadata._strip_provider_prefix(model).strip()
    if not model_bare:
        return None, ""

    def apply_verified_bump(ctx, source, catalog_max=None):
        bumped = metadata._verified_codex_ctx_for_slug(model_bare)
        if bumped is not None and (catalog_max is not None or ctx == metadata._CODEX_OAUTH_STALE_ADVERTISED_CTX):
            bumped = min(bumped, catalog_max) if catalog_max else bumped
            metadata.logger.debug("Codex OAuth context for %s: advertised %d resolved to live-verified %d",
                                  model_bare, ctx, bumped)
            return bumped, source
        return ctx, source

    lookup_bare = metadata._bare_codex_slug(metadata.strip_codex_context_variant_suffix(model_bare))
    catalog_max = None
    if access_token:
        live, fresh_probe = _catalog(access_token, base_url, allow_network=allow_network)
        # Read after the fetch; a failed refresh past the TTL keeps the cap already observed.
        catalog_max = metadata._cached_codex_catalog_max(access_token, base_url, lookup_bare)
        slug = metadata._codex_catalog_key(live, lookup_bare)
        if slug is not None:
            return apply_verified_bump(live[slug], "live" if fresh_probe else "memory", catalog_max)
    if not allow_network:
        return None, ""
    hit = metadata._longest_key_match(metadata._CODEX_OAUTH_CONTEXT_FALLBACK, lookup_bare.lower())
    return apply_verified_bump(hit[1], "fallback", catalog_max) if hit else (None, "")
