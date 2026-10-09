"""Main-turn read surface, synchronized only at native construction/Turn boundaries."""

import copy
import logging

logger = logging.getLogger(__name__)
_READ_TOOLS = {"session_history", "notebook_show"}


def _tool_name(tool):
    function = tool.get("function") if isinstance(tool, dict) else None
    return function.get("name") if isinstance(function, dict) else None


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


def notebook_read_enabled(agent):
    """Only proven user Main + live owning-profile global enable; local state is irrelevant."""
    from secretary.noting_runtime import is_main_conversation_agent
    from secretary.noting_scope import owning_db_scope

    if not is_main_conversation_agent(agent):
        return False
    try:
        from hermes_cli.config import load_config_readonly
        from hermes_cli.config_read_errors import FailedConfigRead
        from utils import is_truthy_value

        with owning_db_scope(agent._session_db):
            config = load_config_readonly()
        if isinstance(config, FailedConfigRead) or not isinstance(config, dict):
            return False
        block = config.get("noting")
        block = block if isinstance(block, dict) else {}
        return is_truthy_value(block.get("enabled"), default=True)
    except Exception:
        logger.debug("Notebook owning-profile config unavailable", exc_info=True)
        return False


def notebook_dispatch_enabled(agent):
    """Use this Turn's synchronized read permission; config changes wait for the next Turn."""
    from secretary.noting_runtime import is_main_conversation_agent

    return (is_main_conversation_agent(agent)
            and getattr(agent, "_secretary_main_read_eligible", False)
            and getattr(agent, "_secretary_notebook_read_enabled", False))


def apply_main_read_surface(agent):
    """Reconcile schema + actual dispatch names; preserve lawful auxiliary History tools."""
    from secretary.noting_runtime import is_main_conversation_agent

    # Noting's advertised frozen Parent surface belongs to its V1 parity contract.
    if getattr(agent, "_secretary_noting_child", False):
        return False
    tools = getattr(agent, "tools", None)
    if not isinstance(tools, list):
        return False
    main = is_main_conversation_agent(agent)
    if main:
        from secretary.noting_scope import bind_main_runtime
        bind_main_runtime(agent)
    enabled = notebook_read_enabled(agent) if main else False
    agent._secretary_main_read_eligible = main
    agent._secretary_notebook_read_enabled = enabled
    desired = {"session_history"} | ({"notebook_show"} if enabled else set()) if main else set()
    removed = _READ_TOOLS - desired if main else {"notebook_show"}
    resolved = [tool for tool in tools if _tool_name(tool) not in removed]
    names = {_tool_name(tool) for tool in resolved}
    for name in ("session_history", "notebook_show"):
        if name in desired and name not in names:
            schema = _read_schema(name)
            if isinstance(schema, dict):
                resolved.append({"type": "function", "function": copy.deepcopy(schema)})
                names.add(name)
    agent.tools = resolved
    agent.valid_tool_names = (set(getattr(agent, "valid_tool_names", set())) - removed) | (desired & names)
    return enabled


def synchronize_main_read_prompt(agent, system_message=None):
    """Use native builder/persistence when a Main's restored root has a stale read surface."""
    if not getattr(agent, "_secretary_main_read_eligible", False):
        return False
    from agent.system_prompt import HISTORY_SEARCH_GUIDANCE, SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE

    prompt = getattr(agent, "_cached_system_prompt", None)
    if not isinstance(prompt, str):
        return False
    notebook = bool(getattr(agent, "_secretary_notebook_read_enabled", False))
    if (prompt.count(HISTORY_SEARCH_GUIDANCE) == 1
            and prompt.count(SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE) == int(notebook)):
        return False
    from hermes_cli.observability.shared_metrics_efficiency import record_cache_break
    from agent.conversation_loop import _persist_system_prompt

    agent._cached_system_prompt = agent._build_system_prompt(system_message)
    record_cache_break(agent, "toolset_change")
    _persist_system_prompt(agent, "Main read-surface prompt persistence failed (session=%s): %s", persist_tools=True)
    return True
