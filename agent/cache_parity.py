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


def _exclude_main_read_additions(child):
    """Ordinary forks inherit native capabilities, excluding V1.5's user-Main additions."""
    from agent.system_prompt import HISTORY_SEARCH_GUIDANCE, SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE

    prompt = getattr(child, "_cached_system_prompt", None)
    if isinstance(prompt, str):
        for module in (HISTORY_SEARCH_GUIDANCE, SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE):
            if module + "\n\n" in prompt:
                prompt = prompt.replace(module + "\n\n", "", 1)
            else:
                prompt = prompt.replace(module, "", 1)
        child._cached_system_prompt = prompt
    child.tools = [tool for tool in child.tools if tool.get("function", {}).get("name") not in {"notebook_show", "notebook_maintain", "notebook_create", "notebook_update", "notebook_archive", "finish_noting"}]
    child.valid_tool_names.difference_update({"notebook_show", "notebook_maintain", "notebook_create", "notebook_update", "notebook_archive", "finish_noting"})
    child._secretary_main_read_eligible = child._secretary_notebook_read_enabled = False


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
    child.valid_tool_names.difference_update({"notebook_maintain", "notebook_create", "notebook_update", "notebook_archive", "finish_noting"})
    if fork_tag != "noting":
        _exclude_main_read_additions(child)
    child._tool_snapshot_generation = _FROZEN_TOOL_SNAPSHOT_GENERATION
    child._skip_mcp_refresh = True


def split_frozen_cache_prefix(agent, messages, *, api=False):
    """Separate this Noting child's immutable Parent prefix from its own suffix."""
    count = getattr(agent, "_cache_parity_frozen_prefix_count", 0)
    if not count:
        return 0, messages
    if api:
        count += int(bool(messages and messages[0].get("role") == "system")) + len(agent.prefill_messages or [])
    if count > len(messages):
        raise RuntimeError("The frozen Parent cache prefix is missing from the Noting request")
    return count, messages[count:]


def normalize_frozen_cache_segments(messages, count, normalize, **kwargs):
    """Apply the existing native send normalization without crossing the frozen boundary."""
    return normalize(messages[:count], **kwargs) + normalize(messages[count:], **kwargs)


def normalize_cache_parity_request(agent, messages, **kwargs):
    """Unbound native callers keep their exact existing sanitizer call signature."""
    count, _suffix = split_frozen_cache_prefix(agent, messages, api=True)
    if count:
        kwargs["preserve_prefix_count"] = count
    return agent._drop_thinking_only_and_merge_users(messages, **kwargs)


def frozen_current_user_message(parent, message, index, cloned):
    """Materialize only the Parent current turn's already-issued multimodal marker."""
    from agent.message_metadata import (
        FreshUserTimestampMarker, TimestampedUserParts, prepend_user_timestamp_marker, user_input_timestamp_marker,
    )
    marker = message.get("_fresh_user_timestamp")
    content = cloned.get("content")
    if (index != getattr(parent, "_persist_user_message_idx", None) or message.get("role") != "user"
            or not isinstance(content, list) or not isinstance(marker, FreshUserTimestampMarker) or not marker
            or isinstance(message.get("content"), TimestampedUserParts)):
        return cloned
    cloned["content"] = prepend_user_timestamp_marker(content, user_input_timestamp_marker(message))
    return cloned


class FrozenParentPrefix(list):
    """Internal request copy, optionally bound after a verified Parent Anchor freeze."""

    __slots__ = ("__anchor_identity",)

    def __init__(self, messages=()):
        super().__init__(messages)
        self.__anchor_identity = None

    @property
    def anchor_identity(self):
        return self.__anchor_identity

    @staticmethod
    def _from_verified_anchor(messages, *, conversation_ref, anchor_message_uid):
        prefix = FrozenParentPrefix(messages)
        prefix.__anchor_identity = (conversation_ref, anchor_message_uid)
        return prefix


def freeze_parent_replay_prefix(parent, messages, *, source_length):
    """Replay-clean only the Parent's historical portion, once at its existing Turn clock."""
    from agent.message_visibility import model_visible_messages
    from agent.replay_cleanup import canonicalize_replay_history

    current = getattr(parent, "_persist_user_message_idx", None)
    now = getattr(parent, "_current_turn_timestamp", None)
    # Anchor truncation may omit this Turn's not-yet-durable user; prove its
    # index against the complete source before limiting the historical slice.
    split = min(current, len(messages)) if isinstance(current, int) and 0 <= current < source_length else 0
    if split and now is not None:
        messages = canonicalize_replay_history(messages[:split], now=now) + messages[split:]
    return FrozenParentPrefix(model_visible_messages(messages))


def canonicalize_cache_parity_history(agent, messages, split, now):
    """The frozen Parent is already normalized; each child Turn cleans only its own history."""
    from agent.replay_cleanup import canonicalize_replay_history

    count, _suffix = split_frozen_cache_prefix(agent, messages)
    split = max(count, split)
    return messages[:count] + canonicalize_replay_history(messages[count:split], now=now) + messages[split:]
