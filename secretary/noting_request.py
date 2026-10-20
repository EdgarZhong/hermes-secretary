"""Request-only Kimi Chat tool declarations for the bound Noting child.

The declaration belongs at the first child-owned boundary, before native send
sanitization. It is never inserted into the durable transcript or parent tools.
"""

from __future__ import annotations

import copy
import hashlib
import json
from urllib.parse import urlsplit


_KIMI_CODING_PROVIDERS = frozenset({"kimi-coding", "kimi", "moonshot", "kimi-for-coding"})


def _official_coding_chat_endpoint(url):
    try:
        parsed = urlsplit(str(url or "").strip())
        return (parsed.scheme.lower() == "https" and parsed.hostname == "api.kimi.com"
                and parsed.port in (None, 443) and parsed.username is None and parsed.password is None
                and parsed.path in ("/coding/v1", "/coding/v1/") and not parsed.query and not parsed.fragment)
    except ValueError:
        return False


def uses_dynamic_noting_tools(agent):
    """Read only the child's inherited, actual runtime; never resolve live config."""
    if not getattr(agent, "_secretary_noting_child", False) or getattr(agent, "api_mode", "") != "chat_completions":
        return False
    provider = str(getattr(agent, "provider", "") or "").strip().lower()
    model = str(getattr(agent, "model", "") or "").strip().lower()
    return (provider in _KIMI_CODING_PROVIDERS and model == "k3-256k"
            and _official_coding_chat_endpoint(getattr(agent, "base_url", "")))


def prepare_noting_request(agent, messages):
    """Declare canonical tools missing from frozen top-level tools at the child boundary.

    Return its request-local object identity so sanitizers may remove/merge parent
    rows without mistaking the raw prefix length for the final wire position.
    No history text, wrapper tags, or user-supplied schemas establish authority.
    """
    if not uses_dynamic_noting_tools(agent) or not getattr(agent, "_cache_parity_frozen_prefix_count", 0):
        return None
    from agent.cache_parity import split_frozen_cache_prefix
    from secretary.noting_tools import noting_tool_schemas

    boundary, _ = split_frozen_cache_prefix(agent, messages, api=True)
    # Kimi rejects duplicate names between top-level and message tools. Freeze the
    # missing subset once; the textual four-tool surface and dispatch stay intact.
    tools = getattr(agent, "_secretary_noting_dynamic_tools", None)
    if tools is None:
        parent_tools = getattr(agent, "_secretary_noting_parent_tools", agent.tools)
        advertised = {tool.get("function", {}).get("name") for tool in parent_tools}
        tools = [{"type": "function", "function": schema}
                 for schema in noting_tool_schemas(agent._secretary_noting_profile)
                 if schema["name"] not in advertised]
        agent._secretary_noting_dynamic_tools = copy.deepcopy(tools)
    if not tools:
        return None
    declaration = {"role": "system", "tools": copy.deepcopy(tools)}
    messages.insert(boundary, declaration)
    return declaration


def normalize_noting_request(agent, messages, declaration, **kwargs):
    """Preserve the native prefix/suffix split using the surviving boundary row."""
    if declaration is None:
        from agent.cache_parity import normalize_cache_parity_request

        return normalize_cache_parity_request(agent, messages, **kwargs)
    boundary = next(index for index, row in enumerate(messages) if row is declaration)
    return agent._drop_thinking_only_and_merge_users(messages, preserve_prefix_count=boundary, **kwargs)


def audit_noting_request(agent, kwargs):
    """Audit the transport-built request, including dynamic schema bytes and price.

    Rough pressure naturally includes the structured message before assembly's
    estimate; provider usage anchors already include it and need no added charge.
    This small audit stores hashes, not another complete copy of the transcript.
    """
    if not uses_dynamic_noting_tools(agent):
        return
    tools = getattr(agent, "_secretary_noting_dynamic_tools", None)
    if tools is None:
        return
    messages = kwargs.get("messages") or []
    boundary = next((index for index, row in enumerate(messages)
                     if row.get("role") == "system" and row.get("tools") == tools), None)
    if boundary is None:
        return
    from agent.model_metadata import estimate_request_tokens_rough

    def digest(value):
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode()).hexdigest()

    audit = {
        "message_index": boundary,
        "declaration_sha256": digest(messages[boundary]),
        "parent_prefix_sha256": digest(messages[:boundary]),
        "top_level_tools_sha256": digest(kwargs.get("tools") or []),
        "request_sha256": digest(messages),
        "estimated_request_tokens": estimate_request_tokens_rough(messages, tools=kwargs.get("tools")),
    }
    history = getattr(agent, "_secretary_noting_dynamic_request_history", None)
    if not isinstance(history, list):
        history = agent._secretary_noting_dynamic_request_history = []
    history.append(audit)
