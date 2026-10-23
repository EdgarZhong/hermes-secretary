"""Secretary catalog registration and explicit rejection of retired tool calls."""

from contextlib import contextmanager
from contextvars import ContextVar

from secretary.noting_contract import FINISH_NOTING_SCHEMA, NOTEBOOK_MAINTAIN_SCHEMA
from tools.registry import registry
from tools.scheduler_tool import SCHEDULER_SCHEMA, scheduler_tool

RETIRED_SECRETARY_TOOLS = frozenset({
    "session_history", "noting_memo", "notebook_mutate", "notebook_manage", "notebook_edit", "notebook_schedule", "compact_parent",
})


def legacy_tool_removed(name):
    canonical = name.lower().replace("-", "_").replace(" ", "_") if isinstance(name, str) else name
    if canonical not in RETIRED_SECRETARY_TOOLS:
        return None
    return {"success": False, "error": {
        "code": "legacy_tool_removed", "message": f"{name} is retired; this call was not executed.",
        "next_action": "Use conversation_history for original evidence, notebook_show for the current view, "
                       "scheduler in Main for reminders, or notebook_maintain and standalone finish_noting in Noting. "
                       "Main does not edit the Notebook or send maintenance memos.",
    }}


_SURFACE_AGENT = ContextVar("secretary_tool_surface_agent", default=None)


@contextmanager
def secretary_surface_scope(agent):
    token = _SURFACE_AGENT.set(agent)
    try:
        yield
    finally:
        _SURFACE_AGENT.reset(token)


def main_tool_is_direct(name, agent=None):
    """Keep enabled Main capabilities independent of native deferred-tool policy."""
    agent = _SURFACE_AGENT.get() if agent is None else agent
    if (agent is None or getattr(agent, "_secretary_noting_child", False)
            or not getattr(agent, "_secretary_main_read_eligible", False)):
        return False
    flag = {"scheduler": "_secretary_scheduler_enabled",
            "notebook_show": "_secretary_notebook_read_enabled",
            "notebook_maintain": "_secretary_notebook_read_enabled",
            "finish_noting": "_secretary_notebook_read_enabled"}.get(name)
    return bool(flag and getattr(agent, flag, False))


def filter_tool_definitions(tools, agent=None):
    """Compose runtime Main capabilities on a catalog copy, never the global schema cache.

    Native toolsets need not name the Main additions. Their raw definitions
    receive the same runtime grants; enabled Main tools remain directly listed.
    """
    agent = _SURFACE_AGENT.get() if agent is None else agent
    if agent is None:
        return tools
    main = bool(getattr(agent, "_secretary_main_read_eligible", False))
    allowed = {"conversation_history"} if main else set()
    if main and getattr(agent, "_secretary_notebook_read_enabled", False):
        allowed.update({"notebook_show", "notebook_maintain", "finish_noting"})
    if main and getattr(agent, "_secretary_scheduler_enabled", False):
        allowed.add("scheduler")
    secretary = {"conversation_history", "notebook_show", "scheduler", "notebook_maintain", "finish_noting"}
    resolved, names = [], set()
    for tool in tools:
        name = tool.get("function", {}).get("name")
        if name in secretary and (name not in allowed or name in names):
            continue
        resolved.append(tool)
        names.add(name)
    if main:
        from copy import deepcopy
        from secretary.noting_surface import _read_schema
        for name in ("conversation_history", "notebook_show", "scheduler", "notebook_maintain", "finish_noting"):
            if name in allowed and name not in names:
                resolved.append({"type": "function", "function": deepcopy(_read_schema(name))})
    return resolved


def _noting_tool(name, args, agent):
    from secretary import noting_tools
    return getattr(noting_tools, name)(agent, args)


registry.register(name="scheduler", toolset="scheduler", schema=SCHEDULER_SCHEMA,
                  handler=lambda args, **kw: scheduler_tool(args, agent=kw.get("agent")), emoji="⏰")
registry.register(name="notebook_maintain", toolset="noting", schema=NOTEBOOK_MAINTAIN_SCHEMA,
                  handler=lambda args, **kw: _noting_tool("notebook_maintain", args, kw.get("agent")), emoji="📓")
registry.register(name="finish_noting", toolset="noting", schema=FINISH_NOTING_SCHEMA,
                  handler=lambda args, **kw: _noting_tool("finish_noting", args, kw.get("agent")), emoji="📓")


def reject_noting_mixed_finish(agent, tool_calls, messages, effective_task_id):
    """Validate the complete native batch before segments, approvals or workers start."""
    import json
    from agent.tool_executor import _append_skipped_tool_results, _parse_tool_call
    from secretary.noting_tools import guard_noting_tool_batch
    if not getattr(agent, "_secretary_noting_child", False):
        return False
    names = [_parse_tool_call(agent, call).name for call in tool_calls]
    refusal = guard_noting_tool_batch(agent, names)
    if refusal is None:
        return False
    _append_skipped_tool_results(
        agent, messages, tool_calls, effective_task_id, content=json.dumps(refusal, ensure_ascii=False),
        flush_stage="invalid Noting finish batch",
    )
    return True



def secretary_validation_refusal(agent, assistant_message, finish_reason, messages):
    """Reject the original complete finish mixture before native repair or filtering."""
    import json
    from agent.message_metadata import append_message
    from agent.turn_tool_validation import ToolValidationVerdict, _append_tool_error_results
    from secretary.noting_tools import guard_noting_tool_batch
    names = [call.function.name for call in assistant_message.tool_calls]
    refusal = guard_noting_tool_batch(agent, names)
    if refusal is None:
        from secretary.noting_child import noting_dispatch_block, noting_dispatch_refusal
        denied = [noting_dispatch_block(agent, name) for name in names]
        if not any(denied):
            return None
        if not getattr(agent, "_secretary_noting_child", False) and not all(denied):
            # Native mixed-name handling preserves the other Main calls in this batch.
            return None
        append_message(messages, agent._build_assistant_message(assistant_message, finish_reason))
        _append_tool_error_results(
            messages, assistant_message.tool_calls,
            lambda call: json.dumps(noting_dispatch_refusal(
                agent, call.function.name,
                message="Skipped: another call in this batch was denied; retry the authorized call.",
            ), ensure_ascii=False),
        )
        return ToolValidationVerdict(action="continue", result=None, mixed_invalid_batch=False)
    append_message(messages, agent._build_assistant_message(assistant_message, finish_reason))
    _append_tool_error_results(messages, assistant_message.tool_calls,
                               lambda call: json.dumps(refusal, ensure_ascii=False))
    return ToolValidationVerdict(action="continue", result=None, mixed_invalid_batch=False)


def scoped_registry_dispatch(agent, *args, **kwargs):
    """Direct invoke uses the same catalog and Cron wording scopes as batch execution."""
    from agent.secretary_prompt import cron_schema_scope
    import model_tools
    from secretary.noting_child import noting_dispatch_refusal
    name = args[0] if args else kwargs.get("function_name", "")
    refusal = noting_dispatch_refusal(agent, name)
    if refusal is not None:
        import json
        return json.dumps(refusal, ensure_ascii=False)
    with cron_schema_scope(agent), secretary_surface_scope(agent):
        return model_tools.handle_function_call(*args, **kwargs)
