"""Read-only browser projections from the owning DB and real process registries."""

from pathlib import Path
import logging
import time

from hermes_time import format_timestamp

logger = logging.getLogger(__name__)


def global_noting_config(db):
    from hermes_cli.config import load_config_readonly
    from hermes_cli.config_read_errors import FailedConfigRead
    from secretary.noting_policy import noting_settings_from_config
    from secretary.noting_scope import owning_db_scope
    from utils import is_truthy_value

    try:
        with owning_db_scope(db):
            config = load_config_readonly()
    except Exception:
        logger.debug("Owning-profile config read unavailable", exc_info=True)
        return None, None
    if isinstance(config, FailedConfigRead) or not isinstance(config, dict):
        return None, None
    block = config.get("noting")
    block = block if isinstance(block, dict) else {}
    return is_truthy_value(block.get("enabled"), default=True), noting_settings_from_config(config)


def _tasks(db, conn, ref):
    from secretary.noting_child import _ACTIVE_NOTING_LOCK, _ACTIVE_NOTING_TASKS
    from secretary.noting_task_presence import running_tasks, task_is_live

    target = Path(db.db_path).resolve()
    home = Path(db.db_path).parent
    with _ACTIVE_NOTING_LOCK:
        children = tuple(_ACTIVE_NOTING_TASKS.items())
    # The child registry owns the durable start instant. A live child is readable only
    # while its registration row exists; never derive a start from page load or admission.
    running = running_tasks(conn, ref)
    started_at = {row["child_session_id"]: row["registered_at"]
                  for row in running if row["child_session_id"]}
    live = []
    for (_owner_path, child_id), child in children:
        owned_db = getattr(child, "_session_db", None)
        if (child_id in started_at and owned_db is not None and Path(owned_db.db_path).resolve() == target
                and getattr(child, "_secretary_parent_conversation_ref", None) == ref):
            task = {"task_id": child_id}
            if child_id in started_at:
                task["started_at"] = format_timestamp(started_at[child_id], profile_home=home)
            live.append(task)
    local_ids = {task["task_id"] for task in live}
    now = time.time()
    for child_id, started in started_at.items():
        if child_id not in local_ids and task_is_live(conn, child_id, now):
            live.append({"task_id": child_id, "started_at": format_timestamp(started, profile_home=home)})
    return ("active" if live else "unknown" if running else "idle"), live


def _next_idle(db, conn, ref, *, global_enabled, local_enabled, settings, now):
    from secretary.noting_timers import idle_timer_observation
    if global_enabled is None:
        return {"state": "unknown", "at": None}
    if not global_enabled or not local_enabled or settings is None or not settings.enabled:
        return {"state": "absent", "at": None}
    state = db.noting_idle_state_conn(conn, ref)
    if not state:
        return {"state": "absent", "at": None}
    finished, started = state.get("last_turn_finished_at"), state.get("last_turn_started_at")
    if (finished is None or (started is not None and started >= finished)
            or state.get("trigger_produced_at") is not None):
        return {"state": "absent", "at": None}
    due = idle_timer_observation(db, ref, state)
    if due is None or due <= now:
        return {"state": "unknown", "at": None}
    return {"state": "scheduled", "at": format_timestamp(due, profile_home=Path(db.db_path).parent)}


def _current_snapshot_id(db, conn, conversation_ref):
    try:
        return db._notebook_pointer_id_conn(conn, conversation_ref)
    except Exception:
        logger.debug("Optional browser Snapshot identity unavailable", exc_info=True)
        return None


_HIDDEN_SCHEDULE = "state='done' AND COALESCE(once_consumed_at,last_fired_at,updated_at,?) < ?"


def _schedule_counts(conn, ref, now):
    cutoff = now - 24 * 60 * 60
    row = conn.execute(
        f"SELECT COUNT(*), COALESCE(SUM(CASE WHEN {_HIDDEN_SCHEDULE} THEN 1 ELSE 0 END),0) "
        "FROM secretary_schedule_registry WHERE conversation_ref=?", (cutoff, cutoff, ref),
    ).fetchone()
    return int(row[0]), int(row[1])


def secretary_state(db, stored_session_id):
    now = time.time()
    global_enabled, settings = global_noting_config(db)
    home = Path(db.db_path).parent
    result = {"stored_session_id": stored_session_id, "conversation_ref": None,
              "availability": "unavailable", "global_enabled": global_enabled, "local_enabled": None,
              "task_state": "unknown", "tasks": [], "next_idle": {"state": "unknown", "at": None},
              "current_snapshot_id": None, "schedule_count": 0,
              "observed_at": format_timestamp(now, profile_home=home)}
    with db._read_ctx() as conn:
        ref = db.resolve_conversation_ref_conn(conn, stored_session_id, read_only=True)
        if ref is None:
            return result
        local = db.notebook_local_enabled_conn(conn, ref)
        task_state, tasks = _tasks(db, conn, ref)
        snapshot_id = _current_snapshot_id(db, conn, ref)
        result.update(conversation_ref=ref, availability="available", local_enabled=local,
                      schedule_count=_schedule_counts(conn, ref, now)[0],
                      current_snapshot_id=snapshot_id,
                      task_state=task_state, tasks=tasks,
                      next_idle=_next_idle(db, conn, ref, global_enabled=global_enabled, local_enabled=local,
                                           settings=settings, now=now))
    return result


def schedules_read(db, stored_session_id):
    """Read-only Schedule Table of the session's Conversation.

    Reuse the Scheduler's row projection, excluding completed rows older than 24h
    before loading their content. The model tool's complete list is unchanged.
    Unbound Conversations are reported unavailable, like ``secretary_state``.
    """
    from secretary.scheduler_table import schedule_public_conn

    now = time.time()
    home = Path(db.db_path).parent
    result = {"stored_session_id": stored_session_id, "conversation_ref": None,
              "availability": "unavailable", "observed_at": format_timestamp(now, profile_home=home),
              "schedules": [], "count": 0, "hidden_count": 0}
    with db._read_ctx() as conn:
        ref = db.resolve_conversation_ref_conn(conn, stored_session_id, read_only=True)
        if ref is None:
            return result
        _total, hidden = _schedule_counts(conn, ref, now)
        cutoff = now - 24 * 60 * 60
        rows = conn.execute(
            f"SELECT * FROM secretary_schedule_registry WHERE conversation_ref=? AND NOT ({_HIDDEN_SCHEDULE}) ORDER BY schedule_id",
            (ref, cutoff, cutoff),
        ).fetchall()
        values = [schedule_public_conn(conn, dict(row), profile_home=home) for row in rows]
        result.update(conversation_ref=ref, availability="available",
                      schedules=values, count=len(values), hidden_count=hidden)
    return result


def notebook_read(db, stored_session_id):
    from secretary.notebook_render import render_notebook
    global_enabled, _settings = global_noting_config(db)
    if global_enabled is not True:
        raise PermissionError("Global Noting read surface is disabled or unavailable")
    with db._read_ctx() as conn:
        ref = db.resolve_conversation_ref_conn(conn, stored_session_id, read_only=True)
        if ref is None:
            return {"stored_session_id": stored_session_id, "availability": "unavailable",
                    "exists": False, "output": "Current Conversation state is unavailable.", "created_at": None}
        snapshot = db.notebook_current_conn(conn, ref)
    home = Path(db.db_path).parent
    return {"stored_session_id": stored_session_id, "availability": "available", "exists": snapshot is not None,
            "output": render_notebook(snapshot, profile_home=home, db=db),
            "created_at": format_timestamp(snapshot["created_at"], profile_home=home) if snapshot else None}
