"""Synchronize independent Main capabilities at existing native Turn boundaries."""

import copy

_MAIN_TOOLS = {"conversation_history", "notebook_show", "scheduler"}
_NOTING_ONLY = {"notebook_create", "notebook_update", "notebook_archive", "finish_noting"}


def _tool_name(tool):
    function = tool.get("function") if isinstance(tool, dict) else None
    return function.get("name") if isinstance(function, dict) else None


def _read_schema(name):
    if name == "conversation_history":
        from tools.session_history_tool import CONVERSATION_HISTORY_SCHEMA
        return CONVERSATION_HISTORY_SCHEMA
    if name == "scheduler":
        from tools.scheduler_tool import get_scheduler_schema
        return get_scheduler_schema()
    if name in _NOTING_ONLY:
        from secretary.noting_tools import noting_tool_schemas
        return next(schema for schema in noting_tool_schemas() if schema["name"] == name)
    from tools.notebook_tool import NOTEBOOK_SHOW_SCHEMA
    return NOTEBOOK_SHOW_SCHEMA


def _refresh_noting_definitions(tools):
    """Refresh same-name contracts at an existing Main/recovery boundary, keeping order."""
    from secretary.noting_tools import noting_tool_schemas
    canonical = {schema["name"]: {"type": "function", "function": schema}
                 for schema in noting_tool_schemas()}
    resolved, refreshed = [], []
    for tool in tools:
        name = _tool_name(tool)
        if name in canonical and tool != canonical[name]:
            tool = copy.deepcopy(canonical[name])
            refreshed.append(name)
        resolved.append(tool)
    return resolved, refreshed


def notebook_read_enabled(agent):
    """Global owning-profile gate; local participation never controls Main reads."""
    from secretary.noting_runtime import is_main_conversation_agent
    from secretary.noting_scope import settings_for_db
    return is_main_conversation_agent(agent) and settings_for_db(agent._session_db).enabled


def notebook_dispatch_enabled(agent):
    from secretary.noting_runtime import is_main_conversation_agent
    return (is_main_conversation_agent(agent)
            and getattr(agent, "_secretary_main_read_eligible", False)
            and getattr(agent, "_secretary_notebook_read_enabled", False))


def _reconcile_catalog(agent, tools):
    """Reassemble an existing native bridge after capability removal, preserving native tools."""
    from tools.secretary_dispatch import filter_tool_definitions, secretary_surface_scope
    from tools import tool_search
    if not any(_tool_name(tool) == "tool_search" for tool in tools):
        return tools
    import model_tools
    raw = model_tools.get_tool_definitions(
        enabled_toolsets=getattr(agent, "enabled_toolsets", None),
        disabled_toolsets=getattr(agent, "disabled_toolsets", None),
        quiet_mode=True, skip_tool_search_assembly=True,
    )
    if not any(_tool_name(tool) in _MAIN_TOOLS | _NOTING_ONLY for tool in raw):
        return tools
    with secretary_surface_scope(agent):
        raw = filter_tool_definitions(raw, agent)
        deferred = tool_search.scoped_deferrable_names(raw)
        visible = [tool for tool in tools if not tool_search.is_bridge_tool(_tool_name(tool))]
        names = {_tool_name(tool) for tool in visible}
        catalog = [tool for tool in raw if _tool_name(tool) in deferred - names]
        return tool_search.assemble_tool_defs([*visible, *catalog], context_length=model_tools._resolve_active_context_length()).tool_defs


def main_read_surface_enabled(agent) -> bool:
    """Whether the Secretary Main read surface (and its HISTORY_SEARCH_GUIDANCE) applies.

    The same predicate that authorizes the Main History guidance decides compaction recovery
    guidance too, so a summary can never tell an eligible Main to use ``session_search`` for
    Conversation evidence.
    """
    if agent is None or getattr(agent, "_secretary_noting_child", False):
        return False
    from secretary.noting_runtime import is_main_conversation_agent
    return is_main_conversation_agent(agent)


def apply_main_read_surface(agent):
    """Keep frozen Noting prefixes; reconcile Main's schemas and execution names together."""
    from secretary.noting_scope import bind_main_runtime, scheduler_settings_for_db
    from tools.secretary_dispatch import RETIRED_SECRETARY_TOOLS

    if getattr(agent, "_secretary_noting_child", False):
        return False
    tools = getattr(agent, "tools", None)
    if not isinstance(tools, list):
        return False
    main = main_read_surface_enabled(agent)
    if main:
        bind_main_runtime(agent)
    notebook = notebook_read_enabled(agent) if main else False
    scheduler = scheduler_settings_for_db(agent._session_db).enabled if main else False
    agent._secretary_main_read_eligible = main
    agent._secretary_notebook_read_enabled = notebook
    agent._secretary_scheduler_enabled = scheduler
    desired = ({"conversation_history"} | ({"notebook_show"} if notebook else set())
               | ({"scheduler"} if scheduler else set())
               | (_NOTING_ONLY if notebook else set())) if main else set()
    removed = ((_MAIN_TOOLS | _NOTING_ONLY) - desired) | RETIRED_SECRETARY_TOOLS
    resolved = [tool for tool in tools if _tool_name(tool) not in removed]
    resolved, refreshed = _refresh_noting_definitions(resolved)
    names = {_tool_name(tool) for tool in resolved}
    for name in ("conversation_history", "notebook_show", "scheduler", "notebook_create", "notebook_update", "notebook_archive", "finish_noting"):
        if name in desired and name not in names:
            resolved.append({"type": "function", "function": copy.deepcopy(_read_schema(name))})
            names.add(name)
    from agent.secretary_prompt import apply_cron_schema_guidance
    agent.tools = apply_cron_schema_guidance(_reconcile_catalog(agent, resolved), enabled=scheduler)
    agent.valid_tool_names = ((set(getattr(agent, "valid_tool_names", set())) - removed)
                              | (desired & names)) - _NOTING_ONLY
    if refreshed:
        from hermes_cli.observability.shared_metrics_efficiency import record_cache_break
        from tools.mcp_tool_agent import persist_agent_tool_names
        record_cache_break(agent, "toolset_change")
        if not getattr(agent, "_persist_disabled", False):
            persist_agent_tool_names(agent)
    return notebook


def synchronize_main_read_prompt(agent, system_message=None):
    """Repair restored roots through the native builder and canonical persistence."""
    if not getattr(agent, "_secretary_main_read_eligible", False):
        return False
    from agent.system_prompt import (
        HISTORY_SEARCH_GUIDANCE, SCHEDULER_GUIDANCE, SECRETARY_SESSION_SEARCH_GUIDANCE,
        SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE,
    )
    from agent.prompt_builder import (
        SECRETARY_MEMORY_APPROVAL, SECRETARY_SKILL_GATE, TASK_COMPLETION_GUIDANCE,
    )
    prompt = getattr(agent, "_cached_system_prompt", None)
    if not isinstance(prompt, str):
        return False
    names = set(getattr(agent, "valid_tool_names", set()))
    secretary = bool(
        getattr(agent, "_secretary_main_read_eligible", False)
        and getattr(agent, "_secretary_notebook_read_enabled", False)
    )
    memory = bool(
        secretary
        and "memory" in names
        and (getattr(agent, "_memory_enabled", True) or getattr(agent, "_user_profile_enabled", True))
    )
    task_completion = (
        bool(getattr(agent, "_task_completion_guidance", True))
        and not bool(getattr(agent, "_secretary_notebook_read_enabled", False))
    )
    expected = (
        (TASK_COMPLETION_GUIDANCE, task_completion),
        (HISTORY_SEARCH_GUIDANCE, True),
        (SECRETARY_WORK_AND_NOTEBOOK_GUIDANCE, bool(getattr(agent, "_secretary_notebook_read_enabled", False))),
        (SCHEDULER_GUIDANCE, bool(getattr(agent, "_secretary_scheduler_enabled", False)) and "scheduler" in names),
        (SECRETARY_SESSION_SEARCH_GUIDANCE, "session_search" in names),
        (SECRETARY_MEMORY_APPROVAL, memory),
        (SECRETARY_SKILL_GATE, bool(secretary and "skill_manage" in names)),
    )
    if all(prompt.count(text) == int(enabled) for text, enabled in expected):
        return False
    from hermes_cli.observability.shared_metrics_efficiency import record_cache_break
    from agent.conversation_loop import _persist_system_prompt
    agent._cached_system_prompt = agent._build_system_prompt(system_message)
    record_cache_break(agent, "toolset_change")
    _persist_system_prompt(agent, "Main read-surface prompt persistence failed (session=%s): %s", persist_tools=True)
    return True
