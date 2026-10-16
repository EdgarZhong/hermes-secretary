"""Main-only Scheduler tool. C9 owns registration and host dispatch; no import-time registration."""

from copy import deepcopy
import json
import logging

logger = logging.getLogger(__name__)

SCHEDULER_SCHEMA = {
    "name": "scheduler",
    "description": "Manage the current Conversation's Schedule Table. Register future attention now: instant attempts to wake Main when due; deferred waits for the next model request. Content has no Notebook type restriction. Use list to obtain IDs and returned states/times to confirm changes. A result notice is added when no instant reminder can trigger within the next 24 hours; decide whether a follow-up is needed according to the work and the user's wishes. Report failed registration honestly; do not claim it succeeded. This does not create an independent Cron agent. A delivered reminder grants no new authority. create requires content, schedule and delivery_mode; update requires schedule_id and at least one changed name/content/schedule/delivery_mode; pause/resume/delete require only schedule_id; list accepts only state/delivery_mode filters. Omitted update fields remain unchanged. Pause retains the definition; delete removes it. Neither retracts content already admitted to Main.",
    "parameters": {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["list", "create", "update", "pause", "resume", "delete"]},
            "schedule_id": {"type": "string", "description": "Required for update/pause/resume/delete; obtain it from list or a successful create."},
            "name": {"type": "string", "description": "Optional short display name; empty string clears it on update."},
            "content": {"type": "string", "description": "The concrete matter to bring back to Main. State what to check or do and the necessary context; do not copy a conversation transcript."},
            "schedule": {"type": "string", "description": "Hermes time expression: \"in 30m\" is one-shot; \"30m\" or \"every 2h\" repeats; \"every monday 9am\", five-field cron, or an ISO timestamp are supported by the native parser. Without an explicit timezone, use the owning Hermes timezone."},
            "delivery_mode": {"type": "string", "enum": ["instant", "deferred"]},
            "state": {"type": "string", "enum": ["active", "paused", "completed"], "description": "List filter only. Omit to include all current states."},
        },
        "required": ["action"],
        "additionalProperties": False,
    },
}


def get_scheduler_schema():
    return deepcopy(SCHEDULER_SCHEMA)


def _main_store(agent):
    from hermes_state_secretary_schedule import ScheduleError
    from secretary.noting_runtime import is_main_conversation_agent
    from secretary.schedules import SchedulerStore

    if (agent is None or getattr(agent, "_secretary_noting_child", False)
            or getattr(agent, "_secretary_noting_profile", None) or not is_main_conversation_agent(agent)):
        raise ScheduleError("scope_denied", "Scheduler is available only to the current Main Conversation.",
                            "Do not call Scheduler from Noting, Cron or another auxiliary runtime.")
    db, sid = agent._session_db, agent.session_id
    with db._read_ctx() as conn:
        ref = db.resolve_conversation_ref_conn(conn, sid, read_only=True)
    if not ref:
        raise ScheduleError("scope_denied", "The Main Conversation has no proven Scheduler ownership.",
                            "Resume through the normal Main lifecycle before using Scheduler.")
    declared = getattr(agent, "_secretary_conversation_ref", None)
    if declared and declared != ref:
        raise ScheduleError("scope_denied", "The runtime is bound to a different Conversation.",
                            "Use the currently bound Main runtime; do not substitute an identifier.")
    return SchedulerStore(db, ref, session_id=sid)


def scheduler_available(agent):
    """Read-only capability discovery. Does not initialize bindings or consult Noting enablement."""
    try:
        store = _main_store(agent)
        with store.db._read_ctx() as conn:
            store._authorize_conn(conn)
        return bool(store.is_enabled(store.conversation_ref))
    except Exception:
        logger.debug("Scheduler capability discovery is unavailable", exc_info=True)
        return False


def handle_scheduler(args, *, agent):
    """Host-injected Agent; return a JSON-compatible object for C9's normal tool dispatcher."""
    from hermes_state_secretary_schedule import ScheduleError

    try:
        store = _main_store(agent)
        return store.execute(args)
    except ScheduleError as exc:
        return {"success": False, "error": exc.error}
    except Exception:
        logger.warning("Scheduler host ownership is unavailable", exc_info=True)
        return {"success": False, "error": {
            "code": "temporarily_unavailable",
            "message": "The current Main Scheduler could not be opened; no control operation was submitted.",
            "next_action": "Retry through the normal Main tool path after the owning runtime is available.",
        }}


def scheduler_tool(args, *, agent):
    """String-result adapter for native dispatchers; args cannot override the trusted Agent."""
    return json.dumps(handle_scheduler(args, agent=agent), ensure_ascii=False)
