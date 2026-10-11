"""Branch-local cron wording; native registry schemas and cache remain unchanged."""

import copy
import json
import re
from contextlib import contextmanager
from contextvars import ContextVar

SECRETARY_CRONJOB_DESCRIPTION = "Manage scheduled cron jobs. A cron job is a separate, standalone scheduled agent task: it runs in a fresh session with no chat context of this Conversation, and its scheduled firing has nothing to do with this Conversation's turns. Use cron only when the user explicitly asks for Hermes-wide scheduled task management, or to dispatch recurring real agent tasks that need no per-run review. In-Conversation schedules — especially reminders — belong to the Notebook/Noting system, NOT to cron; never create a cron job for an in-Conversation reminder. action='create' schedules a job from a prompt and/or skills (fires on 'schedule'; its output is POSTed one-way to the job's deliver target and never re-enters this session); 'list' inspects jobs; 'update'/'pause'/'resume'/'remove' manage one by job_id (always list first — never guess job IDs); 'run' fires a job immediately in the BACKGROUND (the one exception: returns a handle at once and its outcome re-enters this conversation when done — do not wait or poll; optional 'prompt' adds transient context for that fire only)."
SECRETARY_CRON_SCHEDULE_NOTE = 'Not for in-Conversation reminders — "remind me in N minutes" belongs to the Notebook Schedule, not cron.'
_REMINDER_DURATION_CLAUSE = "; use this for 'remind me in N minutes' — do NOT hand-compute an absolute timestamp"
_CRON_SCHEMA_SCOPE = ContextVar("secretary_cron_schema_scope", default=False)


@contextmanager
def cron_schema_scope(agent):
    """Carry this Turn's synchronized Main gate through native tool dispatch workers."""
    enabled = bool(getattr(agent, "_secretary_main_read_eligible", False)
                   and getattr(agent, "_secretary_notebook_read_enabled", False)
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
