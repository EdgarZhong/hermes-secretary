"""Conversation cache maintenance; construction stays at the native Turn boundary."""

import json
import logging

logger = logging.getLogger(__name__)


def clear_context_cache(db, conversation_ref):
    """Use the owning SessionDB writer; no Agent or model work happens here."""
    return db.clear_conversation_context_cache(conversation_ref)


def _refresh_current_tools(agent):
    from hermes_cli.config import load_config
    from tools.mcp_tool_agent import refresh_agent_mcp_tools, reprobe_tool_availability
    from toolsets import session_disabled_toolsets

    platform = getattr(agent, "platform", None) or "cli"
    if platform in ("tui", "desktop"):
        from tui_gateway.server import _load_disabled_toolsets, _load_enabled_toolsets
        enabled = _load_enabled_toolsets(platform)
        disabled = _load_disabled_toolsets()
    else:
        config = load_config()
        # Gateway's cache signature already refreshes config-selected enabled
        # sets; its adapter may also override them for this exact source. CLI
        # invocations can select an explicit set. Keep those native selections.
        enabled = getattr(agent, "enabled_toolsets", None)
        from agent.skill_utils import parse_config_string_list
        disabled = parse_config_string_list((config.get("agent") or {}).get("disabled_toolsets"))
    # Assign explicitly: the native refresh's None override means "keep the old
    # selection", while a newly absent disabled selection must remove that filter.
    agent.enabled_toolsets = enabled
    agent.disabled_toolsets = session_disabled_toolsets(disabled, platform)
    reprobe_tool_availability()
    refresh_agent_mcp_tools(agent, content_aware=True, preserve_prefix=False)


def _owned_cache_row(agent):
    """Only an established Main cache under its native Turn lease can observe."""
    if (getattr(agent, "_secretary_noting_child", False)
            or getattr(agent, "_persist_disabled", False)
            or not getattr(agent, "_active_session_turn_lease_holder", None)
            or not isinstance(getattr(agent, "_cached_system_prompt", None), str)):
        return None
    db = getattr(agent, "_session_db", None)
    if db is None:
        return None
    from secretary.noting_runtime import is_main_conversation_agent
    if not is_main_conversation_agent(agent):
        return None
    try:
        row = db.get_session(agent.session_id)
        if row is None:
            return None
        ref = db.resolve_conversation_ref(agent.session_id)
        route = db.resolve_conversation_route(ref) if ref else None
        if route is None or route["id"] != agent.session_id:
            return None
        return row
    except Exception:
        # Observation alone must not introduce a new persistence gate to native
        # Turns. The existing restore/write owners handle unavailable storage.
        logger.debug("Conversation context cache observation unavailable", exc_info=True)
        return None


def _fingerprint(row):
    return row["id"], row.get("system_prompt"), row.get("tool_names")


def remember_context_cache(agent):
    """Remember only the durable cache this native Turn actually established.

    This process-local observation is not a persistent revision or a new cache
    source. Local surface additions may differ from the persisted pin; that is a
    normal native merge and must not trigger a refresh every Turn.
    """
    row = _owned_cache_row(agent)
    if row and row.get("system_prompt") == agent._cached_system_prompt and row.get("tool_names"):
        agent._conversation_context_cache_seen = _fingerprint(row)


def synchronize_context_cache(agent):
    """Honor a clear or another native runtime's rebuild at the next normal Turn.

    A missing durable root on an established cache signals clearing, including a
    late native MCP refresh that republished only the pin. If another runtime
    rebuilt it, a changed durable root/full pin is adopted through native restore.
    Fresh agents and frozen Noting children keep their native paths.
    """
    row = _owned_cache_row(agent)
    if row is None:
        return False
    root, saved = row.get("system_prompt"), row.get("tool_names")
    previous = getattr(agent, "_conversation_context_cache_seen", None)
    # A new row starts with NULLs before native first-build persistence. With no
    # prior cache observation or durable history it is not evidence of a clear.
    cleared = root is None and bool(previous or row.get("message_count"))
    changed = previous is not None and previous[0] == agent.session_id and previous != _fingerprint(row)
    if not cleared and not (root and saved):
        return False
    pin = None
    if not cleared:
        try:
            pin = json.loads(saved)
        except (TypeError, ValueError):
            return False
        if not isinstance(pin, dict) or not isinstance(pin.get("tools"), list):
            return False
        if previous is None:
            # Eager native resume can have restored a root before its first Turn
            # (and thus before the observation below). Compare its complete cache
            # once; subsequent Turns use durable observations, not local extras.
            changed = root != agent._cached_system_prompt or pin["tools"] != agent.tools
        if not changed:
            return False
    from agent.system_prompt import invalidate_system_prompt
    invalidate_system_prompt(agent)
    if cleared and saved is not None:
        # Native late MCP discovery may publish a pin without a Turn lease after
        # the RPC's atomic clear. Under THIS Turn's lease, retire that late pin
        # before native restore can carry old definitions back into the request.
        agent._session_db.update_session_tool_names(agent.session_id, None)
    _refresh_current_tools(agent)
    if pin is not None:
        # Native refresh persists its snapshot. Restore the authoritative pin
        # before the normal root/merge owner reads it below.
        agent._session_db.update_session_tool_names(agent.session_id, pin)
    return True
