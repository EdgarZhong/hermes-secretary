"""Main-turn Secretary read tools, resolved only at construction or the turn boundary."""

import copy
import logging

logger = logging.getLogger(__name__)
_READ_TOOLS = {"session_history", "notebook_show"}


def _tool_name(tool):
    function = tool.get("function") if isinstance(tool, dict) else None
    return function.get("name") if isinstance(function, dict) else None


def _main_surface_agent(agent):
    return not (
        getattr(agent, "side_agent", False) or getattr(agent, "_persist_disabled", False)
        or getattr(agent, "_parent_session_id", None) or getattr(agent, "_delegate_depth", 0)
        or getattr(agent, "platform", None) in {"subagent", "gateway_hygiene"}
    )


def _read_schema(name):
    from tools.registry import registry

    if registry.get_schema(name) is None:
        if name == "session_history":
            from tools.session_history_tool import SESSION_HISTORY_SCHEMA
            name = SESSION_HISTORY_SCHEMA["name"]
        else:
            from tools.notebook_tool import NOTEBOOK_SHOW_SCHEMA
            name = NOTEBOOK_SHOW_SCHEMA["name"]
    return registry.get_schema(name)


def _notebook_enabled(agent):
    from secretary.noting_runtime import noting_trigger_gate

    try:
        db = getattr(agent, "_secretary_history_db", None) or getattr(agent, "_session_db", None)
        ref = getattr(agent, "_secretary_conversation_ref", None)
        return bool(db is not None and ref and noting_trigger_gate(db, ref)[0])
    except Exception:
        logger.debug("Notebook ownership or policy unavailable at main-turn boundary", exc_info=True)
        return False


def apply_main_read_surface(agent):
    """History is always available; Notebook requires a provable effective gate.

    Child/fork surfaces belong to their frozen runtime. Main surfaces are resolved once before
    the first request of a Turn, never during the request/tool loop.
    """
    tools = getattr(agent, "tools", None)
    if not _main_surface_agent(agent) or not isinstance(tools, list):
        return False
    enabled = _notebook_enabled(agent)
    desired = {"session_history"} | ({"notebook_show"} if enabled else set())
    resolved = [tool for tool in tools if _tool_name(tool) not in _READ_TOOLS - desired]
    names = {_tool_name(tool) for tool in resolved}
    for name in ("session_history", "notebook_show"):
        if name in desired and name not in names:
            schema = _read_schema(name)
            if isinstance(schema, dict):
                resolved.append({"type": "function", "function": copy.deepcopy(schema)})
                names.add(name)
    agent.tools = resolved
    valid = set(getattr(agent, "valid_tool_names", set())) - _READ_TOOLS
    agent.valid_tool_names = valid | (_READ_TOOLS & names)
    return "notebook_show" in names
