"""Schedule Table control operations and a read-only 24-hour coverage query.

The caller owns the profile scope and transaction. The existing registry is the sole
Schedule definition store; neither Notebook snapshots nor pointer selection participate.
The model-facing service in schedules.py adds authorization, config and error handling.
"""

import json
import logging
import uuid

from hermes_time import readable_schedule_display
from hermes_state_secretary_schedule import (
    ScheduleError,
    occurrence_payload,
    render_source_timestamp,
    schedule_definition_conn,
)
from secretary.scheduler_time import (
    canonical_schedule,
    epoch,
    iso_to_epoch,
    parse_schedule_expression,
    schedule_advance_epoch,
    schedule_initial_next_run,
    schedule_timezone,
    validate_canonical_schedule,
)

logger = logging.getLogger(__name__)

NO_INSTANT_NOTICE = (
    "No instant reminder is currently scheduled to trigger in this Conversation within "
    "the next 24 hours. Consider whether a follow-up is needed."
)
UNKNOWN_INSTANT_NOTICE = (
    "Could not determine whether an instant reminder can trigger in this Conversation "
    "within the next 24 hours."
)
_ACTION_FIELDS = {
    "list": {"state", "delivery_mode"},
    "create": {"name", "content", "schedule", "delivery_mode"},
    "update": {"schedule_id", "name", "content", "schedule", "delivery_mode"},
    "pause": {"schedule_id"}, "resume": {"schedule_id"}, "delete": {"schedule_id"},
}
_MUTABLE_FIELDS = {"name", "content", "schedule", "delivery_mode"}
_MODES = {"instant": "user_reminder", "deferred": "system_reminder"}


def _invalid(field, message, next_action):
    raise ScheduleError("invalid_argument", message, next_action, field=field)


def validate_scheduler_arguments(args):
    """Action-specific validation, before any mutation; omitted fields stay omitted."""
    if not isinstance(args, dict) or any(not isinstance(key, str) for key in args):
        _invalid("arguments", "Expected a Scheduler argument object.", "Supply action and its documented fields.")
    action = args.get("action")
    if not isinstance(action, str) or action not in _ACTION_FIELDS:
        _invalid("action", "Unknown Scheduler action.", "Use list, create, update, pause, resume or delete.")
    extras = set(args) - (_ACTION_FIELDS[action] | {"action"})
    if extras:
        field = sorted(extras)[0]
        _invalid(field, f"{field} is not writable with {action}.",
                 "Use list for returned states; change definitions with the documented create/update fields.")
    required = ({"content", "schedule", "delivery_mode"} if action == "create" else
                {"schedule_id"} if action != "list" else set())
    for field in sorted(required - set(args)):
        _invalid(field, f"{action} requires {field}.", f"Include {field} in this {action} call.")
    if action == "update" and not _MUTABLE_FIELDS.intersection(args):
        _invalid("action", "update requires at least one definition field.",
                 "Include name, content, schedule or delivery_mode; omit fields that should stay unchanged.")
    result = dict(args)
    for field in ("schedule_id", "content", "schedule"):
        if field in result:
            value = result[field]
            if not isinstance(value, str) or not value.strip():
                _invalid(field, f"{field} must be non-empty text.", f"Set {field} to a non-empty string.")
            if field != "content":
                result[field] = value.strip()
    if "name" in result and not isinstance(result["name"], str):
        _invalid("name", "name must be text.", "Use a short name or an empty string to clear it.")
    if "delivery_mode" in result and result["delivery_mode"] not in ("instant", "deferred"):
        _invalid("delivery_mode", "Unknown delivery_mode.", "Use instant or deferred.")
    if "state" in result and result["state"] not in ("active", "paused", "completed"):
        _invalid("state", "Unknown list state filter.", "Use active, paused or completed, or omit state.")
    return result


def _require_conversation(conn, conversation_ref):
    if conn.execute("SELECT 1 FROM secretary_conversations WHERE conversation_ref=?", (conversation_ref,)).fetchone() is None:
        raise ScheduleError("scope_denied", "No authorized Conversation is bound to this Scheduler call.",
                            "Use Scheduler only from the current Main Conversation.")


def _require_schedule(conn, conversation_ref, schedule_id):
    row = schedule_definition_conn(conn, conversation_ref, schedule_id)
    if row is None:
        raise ScheduleError("schedule_not_found", "No current Schedule has that ID in this Conversation.",
                            "Use list and copy an ID from the current Schedule Table.", field="schedule_id")
    return row


def _json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"), sort_keys=True)


def _state(row):
    if row["state"] == "done":
        return "completed"
    if row["state"] not in ("pending", "cancelled"):
        raise RuntimeError("Unrecognized stored Schedule state")
    return "active" if row["enabled"] and row["state"] == "pending" else "paused"


def schedule_public_conn(conn, row, *, profile_home=None):
    canonical = json.loads(row["canonical_schedule"])
    validate_canonical_schedule(canonical)
    if "run_at" in canonical:
        canonical["run_at"] = render_source_timestamp(canonical["run_at"], profile_home=profile_home)
        if "display" in canonical:
            canonical["display"] = readable_schedule_display(canonical, canonical["display"])
    if row["delivery_semantics"] not in _MODES.values():
        raise RuntimeError("Unrecognized stored Schedule delivery mode")
    pending = conn.execute(
        "SELECT COUNT(*) FROM secretary_pending_reminders "
        "WHERE conversation_ref=? AND schedule_id=? AND status='pending'",
        (row["conversation_ref"], row["schedule_id"]),
    ).fetchone()[0]
    result = {
        "schedule_id": row["schedule_id"], "content": row["reminder_text"],
        "expression": row["expression"], "canonical_schedule": canonical,
        "timezone": schedule_timezone(canonical),
        "delivery_mode": "instant" if row["delivery_semantics"] == "user_reminder" else "deferred",
        "state": _state(row),
        "next_due_at": render_source_timestamp(row["next_run_at"], profile_home=profile_home),
        "pending_count": int(pending), "last_delivery": None,
    }
    if row["name"]:
        result["name"] = row["name"]
    if row["last_delivery_at"] is not None:
        result["last_delivery"] = {
            "timestamp": render_source_timestamp(row["last_delivery_at"], profile_home=profile_home),
            "outcome": row["last_delivery_outcome"],
        }
    return result


def schedule_delivery_in_flight_conn(conn, conversation_ref, schedule_id):
    """Only durable carriers are in flight; a lease or prepared string is not evidence."""
    return conn.execute(
        "SELECT 1 FROM secretary_pending_reminders p WHERE p.conversation_ref=? AND p.schedule_id=? "
        "AND p.carrier_message_uid IS NOT NULL AND ((p.status='pending' AND p.acknowledged_at IS NULL) "
        "OR EXISTS (SELECT 1 FROM messages m JOIN secretary_session_bindings b ON b.session_id=m.session_id "
        "WHERE b.conversation_ref=p.conversation_ref AND m.message_uid=p.carrier_message_uid AND m.active=1)) LIMIT 1",
        (conversation_ref, schedule_id),
    ).fetchone() is not None


def _parse(expression, parser):
    try:
        return canonical_schedule(expression, parser)
    except ValueError as exc:
        raise ScheduleError("invalid_argument", f"Invalid schedule: {exc}",
                            "Use a native time expression, such as in 30m, every 2h or an ISO timestamp.",
                            field="schedule") from exc


def _cancel_unadmitted(conn, row):
    conn.execute(
        "UPDATE secretary_pending_reminders SET status='cancelled' "
        "WHERE conversation_ref=? AND schedule_id=? AND status='pending' AND carrier_message_uid IS NULL",
        (row["conversation_ref"], row["schedule_id"]),
    )


def _create(conn, ref, args, *, now, profile, parser):
    canonical = _parse(args["schedule"], parser)
    next_run = schedule_initial_next_run(canonical, now=now)
    sid = "sched_" + uuid.uuid4().hex
    conn.execute(
        "INSERT INTO secretary_schedule_registry "
        "(schedule_id,conversation_ref,profile,name,expression,canonical_schedule,delivery_semantics,"
        "reminder_text,next_run_at,updated_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (sid, ref, profile, args.get("name", ""), args["schedule"], _json(canonical),
         _MODES[args["delivery_mode"]], args["content"], next_run, now),
    )
    return schedule_definition_conn(conn, ref, sid), True


def _update(conn, row, args, *, now, parser):
    updated = dict(row)
    mapping = {"name": "name", "content": "reminder_text", "schedule": "expression"}
    for field, column in mapping.items():
        if field in args:
            updated[column] = args[field]
    if "delivery_mode" in args:
        updated["delivery_semantics"] = _MODES[args["delivery_mode"]]
    if all(updated[key] == row[key] for key in (*mapping.values(), "delivery_semantics")):
        return row, False
    reschedule = updated["expression"] != row["expression"]
    if reschedule:
        if row["once_consumed_at"] is not None:
            raise ScheduleError("state_conflict", "This one-shot Schedule has already been consumed.",
                                "Create a new Schedule for another occurrence.")
        canonical = _parse(updated["expression"], parser)
        updated.update(canonical_schedule=_json(canonical), sequence=row["sequence"] + 1,
                       next_run_at=schedule_initial_next_run(canonical, now=now), state="pending")
    updated["generation"] += 1
    conn.execute(
        "UPDATE secretary_schedule_registry SET name=?,reminder_text=?,expression=?,canonical_schedule=?,"
        "delivery_semantics=?,generation=?,sequence=?,next_run_at=?,state=?,claim_owner=NULL,"
        "claim_token=NULL,claim_expires_at=NULL,updated_at=? WHERE schedule_id=? AND generation=?",
        (updated["name"], updated["reminder_text"], updated["expression"], updated["canonical_schedule"],
         updated["delivery_semantics"], updated["generation"], updated["sequence"], updated["next_run_at"],
         updated["state"], now, row["schedule_id"], row["generation"]),
    )
    if reschedule:
        _cancel_unadmitted(conn, row)
    else:
        # Update unsent content in place. A pending occurrence stays in the existing
        # deferred lane; changing a definition never manufactures a queued Main Turn.
        # origin_instant remains its original source, for C6's eventual notice hook.
        conn.execute(
            "UPDATE secretary_pending_reminders SET content=?,entry_payload=?,schedule_generation=? "
            "WHERE conversation_ref=? AND schedule_id=? AND schedule_generation=? "
            "AND status='pending' AND carrier_message_uid IS NULL",
            (updated["reminder_text"], _json(occurrence_payload(updated)), updated["generation"],
             row["conversation_ref"], row["schedule_id"], row["generation"]),
        )
    return schedule_definition_conn(conn, row["conversation_ref"], row["schedule_id"]), True


def _participation(conn, row, action, *, now):
    if row["state"] == "done" or row["once_consumed_at"] is not None:
        raise ScheduleError("state_conflict", "This one-shot Schedule has already been consumed.",
                            "Create a new Schedule for another occurrence.")
    wants_enabled = action == "resume"
    if _state(row) == ("active" if wants_enabled else "paused"):
        return row, False
    next_run, sequence = row["next_run_at"], row["sequence"]
    if wants_enabled:
        canonical = json.loads(row["canonical_schedule"])
        if canonical["kind"] == "once":
            next_run = schedule_initial_next_run(canonical, now=now)
        elif next_run is not None and iso_to_epoch(next_run) > epoch(now):
            # The pause did not consume a still-future occurrence: recompute from the
            # clock instead of advancing past the slot the user is resuming for.
            next_run = schedule_initial_next_run(canonical, now=now)
        else:
            next_run = schedule_advance_epoch(canonical, next_run, now=now)
        # Withdrawn receipts stay withdrawn; a new enable epoch cannot revive an old worker.
        sequence += 1
    else:
        _cancel_unadmitted(conn, row)
    conn.execute(
        "UPDATE secretary_schedule_registry SET enabled=?,state='pending',generation=generation+1,"
        "sequence=?,next_run_at=?,claim_owner=NULL,claim_token=NULL,claim_expires_at=NULL,updated_at=? "
        "WHERE schedule_id=? AND generation=?",
        (int(wants_enabled), sequence, next_run, now, row["schedule_id"], row["generation"]),
    )
    return schedule_definition_conn(conn, row["conversation_ref"], row["schedule_id"]), True


def apply_schedule_action_conn(conn, conversation_ref, args, *, now, profile=None,
                               parser=parse_schedule_expression, profile_home=None):
    """Validated CRUD in one caller-owned transaction, returning the public result.

    No callbacks or model calls run here. Exceptions roll back the whole control
    operation. All writers use the same SessionDB transaction as claim/materialize.
    """
    args = validate_scheduler_arguments(args)
    _require_conversation(conn, conversation_ref)
    timestamp, action = epoch(now), args["action"]
    if action == "list":
        rows = conn.execute(
            "SELECT * FROM secretary_schedule_registry WHERE conversation_ref=? ORDER BY schedule_id",
            (conversation_ref,),
        ).fetchall()
        values = [schedule_public_conn(conn, dict(row), profile_home=profile_home) for row in rows]
        values = [value for value in values if all(value[field] == args[field]
                  for field in ("state", "delivery_mode") if field in args)]
        return {"success": True, "conversation_ref": conversation_ref, "schedules": values, "count": len(values)}
    in_flight = False
    if action == "create":
        row, changed = _create(conn, conversation_ref, args, now=timestamp, profile=profile, parser=parser)
    else:
        row = _require_schedule(conn, conversation_ref, args["schedule_id"])
        in_flight = schedule_delivery_in_flight_conn(conn, conversation_ref, row["schedule_id"])
        if action == "delete":
            _cancel_unadmitted(conn, row)
            conn.execute("DELETE FROM secretary_schedule_registry WHERE schedule_id=? AND generation=?",
                         (row["schedule_id"], row["generation"]))
            result = {"success": True, "changed": True, "schedule_id": row["schedule_id"], "deleted": True}
            if in_flight:
                result["delivery_in_flight"] = True
            return result
        if action == "update":
            row, changed = _update(conn, row, args, now=timestamp, parser=parser)
        else:
            row, changed = _participation(conn, row, action, now=timestamp)
    result = {"success": True, "changed": changed,
              "schedule": schedule_public_conn(conn, row, profile_home=profile_home)}
    if in_flight:
        result["delivery_in_flight"] = True
    return result


def _row_instant_coverage(conn, row, *, now, excluded):
    canonical = json.loads(row["canonical_schedule"])
    validate_canonical_schedule(canonical)
    if not isinstance(row["reminder_text"], str) or not row["reminder_text"].strip():
        return None
    receipts = conn.execute(
        "SELECT source_timestamp FROM secretary_pending_reminders WHERE conversation_ref=? "
        "AND schedule_id=? AND schedule_sequence=? AND status IN ('pending','delivered','terminated')",
        (row["conversation_ref"], row["schedule_id"], row["sequence"]),
    ).fetchall()
    blocked = excluded | {(row["schedule_id"], epoch(item[0])) for item in receipts}
    due = row["next_run_at"]
    if due is None:
        # A queued one-shot has no future instant. A missing recurring next run is
        # uncomputable state, not proof that no future attention exists.
        return False if canonical["kind"] == "once" and receipts else None
    due = epoch(due)
    for _ in range(len(blocked) + 1):
        if (row["schedule_id"], due) not in blocked:
            return max(now, due) <= now + 24 * 60 * 60
        if canonical["kind"] == "once":
            return False
        due = schedule_advance_epoch(canonical, due, now=max(now, due))
    return None


def instant_coverage_conn(conn, conversation_ref, *, now, exclude_occurrences=()):
    """True=some instant within [now,now+24h], False=none, None=unknown.

    Reads the COMPLETE formal table independently of list filters. Exclusions are
    (schedule_id, due_epoch) pairs, not whole Schedule IDs. Pure reads: no advance,
    claim, receipt consumption, Notebook lookup, or timer registration takes place.
    SQL failures propagate; a caller may render the common unknown notice.
    """
    _require_conversation(conn, conversation_ref)
    timestamp = epoch(now)
    excluded = {(sid, epoch(due)) for sid, due in exclude_occurrences}
    rows = conn.execute(
        "SELECT * FROM secretary_schedule_registry WHERE conversation_ref=? "
        "AND state='pending' AND enabled=1 AND delivery_semantics='user_reminder'",
        (conversation_ref,),
    ).fetchall()
    unknown = False
    for found in rows:
        try:
            present = _row_instant_coverage(conn, dict(found), now=timestamp, excluded=excluded)
        except (ValueError, TypeError, KeyError, RuntimeError, ImportError, OverflowError):
            logger.warning("Scheduler coverage calculation unavailable for %s", found["schedule_id"], exc_info=True)
            present = None
        if present is True:
            return True
        unknown |= present is None
    return None if unknown else False


def coverage_notice(coverage):
    if coverage is True:
        return None
    return NO_INSTANT_NOTICE if coverage is False else UNKNOWN_INSTANT_NOTICE
