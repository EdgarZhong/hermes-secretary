"""Append trusted runtime changes without rewriting the established request prefix."""

import hashlib
import json
import logging

from agent.message_metadata import append_message

logger = logging.getLogger(__name__)
_KIND = "runtime_context"
_VERSION = 1


def runtime_context_snapshot(messages):
    for message in reversed(messages):
        if not isinstance(message, dict) or message.get("role") != "system" or message.get("display_kind") != _KIND:
            continue
        metadata = message.get("display_metadata") or {}
        snapshot = metadata.get(_KIND) if isinstance(metadata, dict) else None
        if isinstance(snapshot, dict) and snapshot.get("version") == _VERSION:
            return snapshot
    return None


def _live_catalog(agent):
    import model_tools
    from tools import tool_search
    from tools.secretary_dispatch import filter_tool_definitions, secretary_surface_scope
    from tools.tool_search_catalog import build_catalog_listing_with_form

    with secretary_surface_scope(agent):
        raw = filter_tool_definitions(model_tools.get_tool_definitions(
            enabled_toolsets=getattr(agent, "enabled_toolsets", None),
            disabled_toolsets=getattr(agent, "disabled_toolsets", None),
            quiet_mode=True, skip_tool_search_assembly=True,
        ) or [], agent)
        config = tool_search.load_config_readonly()
        deferred = tool_search.classify_tools(raw, config.effective_defer_tools)[1]
        direct = set(getattr(agent, "valid_tool_names", ()))
        deferred = [tool for tool in deferred if tool.get("function", {}).get("name") not in direct]
    listing, _form = build_catalog_listing_with_form(
        deferred, max_tokens=config.listing_max_tokens, unavailable_sources=[])
    if not listing:
        listing = ("Additional tools are available; use tool_search to discover them." if deferred
                   else "No additional tools are currently listed.")
    if tool_search.connections_in_scope(raw):
        listing += "\nConnected service tools may also be discovered through tool_search."
    canonical = sorted(raw, key=lambda entry: entry.get("function", {}).get("name", ""))
    signature = hashlib.sha256(json.dumps(canonical, sort_keys=True, ensure_ascii=False,
                                           separators=(",", ":")).encode()).hexdigest()
    return listing, signature, len({tool["function"]["name"] for tool in deferred})


def _snapshot(agent, previous):
    bridge = {"tool_search", "tool_describe", "tool_call"} <= set(getattr(agent, "valid_tool_names", ()))
    try:
        listing, signature, folded_count = _live_catalog(agent)
        if not bridge:
            listing = "Additional tool discovery is unavailable in this runtime."
    except Exception:
        logger.warning("Runtime catalog unavailable; retaining known capabilities and updating current policy", exc_info=True)
        listing = (previous.get("catalog") if previous else None) or (
            "The additional tool directory is temporarily unknown because its catalog could not be read. "
            "This does not mean tools are absent; use authorized discovery tools to check availability.")
        signature = previous.get("schemas") if previous else None  # unknown until a successful read
        folded_count = None
    policy = getattr(agent, "_gateway_channel_system_prompt", None)
    if not isinstance(policy, str):
        policy = previous.get("system_policy", "") if previous else ""
    return {"version": _VERSION, "catalog": listing,
            "schemas": signature, "bridge": bridge, "folded_count": folded_count,
            "direct_tools": sorted(getattr(agent, "valid_tool_names", ())), "system_policy": policy}


def _render_update(snapshot, previous):
    previous = previous or {}
    parts = []
    if snapshot.get("folded_count") is not None and any(
            snapshot.get(key) != previous.get(key)
            for key in ("catalog", "schemas", "bridge", "direct_tools", "folded_count")):
        parts.append(f"能力可能变化，当前 {snapshot['folded_count']} 个折叠工具，调用前重新 search/describe。")
    if snapshot["system_policy"] != previous.get("system_policy", ""):
        parts.append("Current additional configured channel system instructions: " + (
            snapshot["system_policy"] or "No additional configured channel system instructions apply; "
            "any earlier additional configured channel instructions no longer apply."))
    return "\n\n".join(parts)


def append_runtime_context(agent, messages, *, previous_snapshot=None):
    """History is the durable dedup owner; failed reads never masquerade as removals."""
    if (getattr(agent, "_secretary_notebook_read_enabled", False) is not True
            or getattr(agent, "_secretary_noting_child", False)):
        return False
    previous = runtime_context_snapshot(messages)
    from agent.conversation_prefix import remember_runtime_context, request_prefix_for_pin
    prefix = request_prefix_for_pin(agent) or {}
    try:
        snapshot = _snapshot(agent, previous or previous_snapshot or prefix.get("runtime_context"))
    except Exception:
        logger.warning("Runtime capability snapshot unavailable; keeping the established context", exc_info=True)
        return False
    agent.__dict__.pop("_gateway_channel_system_prompt", None)
    if snapshot == previous:
        remember_runtime_context(agent, snapshot)
        return False
    content = _render_update(snapshot, previous)
    if not content:
        remember_runtime_context(agent, snapshot)
        return False
    append_message(messages, {"role": "system", "content": content, "display_kind": _KIND,
                              "display_metadata": {_KIND: snapshot}})
    remember_runtime_context(agent, snapshot)
    return True
