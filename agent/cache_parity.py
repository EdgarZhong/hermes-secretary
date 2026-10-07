"""Parent request/cache inheritance, independent of child Session lifecycle.

Construct a child with ``parent_cache_parity_kwargs`` before applying the cached
prefix. Callers own session identity, persistence, dispatch policy and teardown.
Routed children must not inherit a different model's cache prefix.
"""

from __future__ import annotations

import copy
from typing import Any

from agent.prompt_cache_scope import resolve_prompt_cache_scope_safe


_PROVIDER_PIN_ATTRS = (
    "providers_allowed", "providers_ignored", "providers_order", "provider_sort",
    "provider_require_parameters", "provider_data_collection",
)

# Refuse live-registry rebuilds, including compaction-boundary MCP refreshes.
_FROZEN_TOOL_SNAPSHOT_GENERATION = 2_147_483_647


def parent_prompt_cache_kwargs(parent: Any) -> dict[str, Any]:
    """Constructor request knobs for a same-model child, without routing policy."""
    kwargs = {
        "reasoning_config": copy.deepcopy(getattr(parent, "reasoning_config", None)),
        "ephemeral_system_prompt": copy.deepcopy(getattr(parent, "ephemeral_system_prompt", None)),
        "prefill_messages": copy.deepcopy(getattr(parent, "prefill_messages", None) or []),
        **{attr: copy.deepcopy(getattr(parent, attr, None)) for attr in _PROVIDER_PIN_ATTRS},
    }
    return kwargs


def parent_cache_parity_kwargs(parent: Any) -> dict[str, Any]:
    """Live Parent runtime constructor kwargs for an independent same-model child.

    Credentials/pools come from the live runtime, never environment auto-resolution.
    No auxiliary route, provider downgrade or lifecycle flags are introduced here.
    Credential pools retain their object identity; mutable request data is copied.
    """
    runtime = parent._current_main_runtime()
    kwargs = {
        "model": parent.model,
        "provider": parent.provider,
        "platform": parent.platform,
        "api_mode": runtime.get("api_mode") or None,
        "base_url": runtime.get("base_url") or None,
        "api_key": runtime.get("api_key") or None,
        "credential_pool": getattr(parent, "_credential_pool", None),
        "request_overrides": copy.deepcopy(getattr(parent, "request_overrides", {}) or {}),
        "enabled_toolsets": copy.deepcopy(getattr(parent, "enabled_toolsets", None)),
        "disabled_toolsets": copy.deepcopy(getattr(parent, "disabled_toolsets", None)),
        **parent_prompt_cache_kwargs(parent),
    }
    max_tokens = getattr(parent, "max_tokens", None)
    if isinstance(max_tokens, int):
        kwargs["max_tokens"] = max_tokens
    command = getattr(parent, "acp_command", None)
    if isinstance(command, str) and command:
        kwargs.update(acp_command=command, acp_args=copy.deepcopy(getattr(parent, "acp_args", []) or []))
    return kwargs


def apply_cache_parity_from_parent(child: Any, parent: Any, *, fork_tag: str | None = "noting") -> None:
    """Apply a same-model frozen prefix without changing any Session ownership.

    The caller constructs the child using the Parent runtime first. This helper
    does not change session_id, parent_session_id, DB handles, persistence flags,
    close policy or compression. Advertising tools grants no dispatch permission.
    ``fork_tag=None`` preserves the single-extension /btw cache-scope behavior.
    """
    for attr, value in parent_prompt_cache_kwargs(parent).items():
        setattr(child, attr, value)
    child._cached_system_prompt = copy.deepcopy(parent._cached_system_prompt)
    child.session_start = copy.deepcopy(parent.session_start)
    child._inherited_cache_scope = resolve_prompt_cache_scope_safe(parent)
    child._prompt_cache_fork_tag = fork_tag
    child._cached_conversation_root = parent._conversation_root_id()
    child.tools = copy.deepcopy(getattr(parent, "tools", None) or [])
    child.valid_tool_names = {tool["function"]["name"] for tool in child.tools}
    child._tool_snapshot_generation = _FROZEN_TOOL_SNAPSHOT_GENERATION
    child._skip_mcp_refresh = True
