"""Branch-local cron wording; native registry schemas and cache remain unchanged."""

import copy
import json
import re
from contextlib import contextmanager
from contextvars import ContextVar

SECRETARY_CRONJOB_DESCRIPTION = 'Manage independent scheduled Hermes Agent jobs. Use this for explicitly requested Hermes-wide schedule management or standalone recurring Agent work; use scheduler for reminders and follow-ups delivered into the current Conversation. A scheduled job runs in its own Session, and scheduled output follows its configured delivery target rather than re-entering this Conversation. Use list to obtain job IDs; create schedules a prompt and/or skills, update/pause/resume/remove manage an existing job, and run starts an immediate background execution whose completion can return here under the native run behavior. Do not wait or poll merely because run returned a background handle.'
SECRETARY_CRON_SCHEDULE_NOTE = 'Not for in-Conversation reminders: register those with scheduler. This field keeps the native Hermes Cron time-expression semantics.'
_REMINDER_DURATION_CLAUSE = "; use this for 'remind me in N minutes' — do NOT hand-compute an absolute timestamp"
_CRON_SCHEMA_SCOPE = ContextVar("secretary_cron_schema_scope", default=False)


@contextmanager
def cron_schema_scope(agent):
    """Carry this Turn's synchronized Main gate through native tool dispatch workers."""
    enabled = bool(getattr(agent, "_secretary_main_read_eligible", False)
                   and getattr(agent, "_secretary_scheduler_enabled", False)
                   and "scheduler" in getattr(agent, "valid_tool_names", ())
                   and not getattr(agent, "_secretary_noting_child", False))
    token = _CRON_SCHEMA_SCOPE.set(enabled)
    try:
        yield
    finally:
        _CRON_SCHEMA_SCOPE.reset(token)


def apply_scoped_cron_schema_guidance(tools):
    return apply_cron_schema_guidance(tools, enabled=True) if _CRON_SCHEMA_SCOPE.get() else tools


def apply_scoped_cron_search_guidance(result):
    """Keep this branch's complete routing directive in the native Search record."""
    if not _CRON_SCHEMA_SCOPE.get():
        return result
    payload = json.loads(result)
    cron = payload.get("tools", {}).get("cronjob_manage")
    if cron is None:
        return result
    cron["description"] = SECRETARY_CRONJOB_DESCRIPTION
    return json.dumps(payload, ensure_ascii=False)


def _cron_manifest(tool, *, enabled):
    description = tool["function"].get("description", "")
    if not re.search(r"(?m)^- cronjob_manage: ", description):
        return tool
    from tools.cronjob_tools import CRONJOB_SCHEMA
    from tools.tool_search_catalog import _short_desc
    native, target = _short_desc(CRONJOB_SCHEMA["description"]), _short_desc(SECRETARY_CRONJOB_DESCRIPTION)
    def replace(match):
        suffix = target if enabled else native if match[2] == target else match[2]
        return match[1] + suffix
    replacement = copy.deepcopy(tool)
    replacement["function"]["description"] = re.sub(r"(?m)^(- cronjob_manage: )([^\n]*)", replace, description)
    return replacement


def apply_cron_schema_guidance(tools, *, enabled):
    """Rewrite only the existing cron tool's two descriptions on a private copy."""
    resolved = []
    for tool in tools:
        schema = tool.get("function") if isinstance(tool, dict) else None
        if isinstance(schema, dict) and schema.get("name") == "tool_search":
            resolved.append(_cron_manifest(tool, enabled=enabled))
            continue
        if not isinstance(schema, dict) or schema.get("name") != "cronjob_manage":
            resolved.append(tool)
            continue
        if not enabled and schema.get("description") != SECRETARY_CRONJOB_DESCRIPTION:
            resolved.append(tool)
            continue
        from tools.cronjob_tools import CRONJOB_SCHEMA
        replacement = copy.deepcopy(tool)
        function = replacement["function"]
        function["description"] = SECRETARY_CRONJOB_DESCRIPTION if enabled else CRONJOB_SCHEMA["description"]
        native = CRONJOB_SCHEMA["parameters"]["properties"]["schedule"]["description"]
        function["parameters"]["properties"]["schedule"]["description"] = (
            native.replace(_REMINDER_DURATION_CLAUSE, "") + " " + SECRETARY_CRON_SCHEDULE_NOTE
            if enabled else native
        )
        resolved.append(replacement)
    return resolved
