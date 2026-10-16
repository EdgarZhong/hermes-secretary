"""Main-owned Scheduler service and thin adapters for the existing due scanner.

Schedule definitions are independent of Notebook/Noting. Host dispatch remains in C9;
C6 owns actual instant/deferred admission. The service never starts an Agent or Cron job.
"""

import logging
from pathlib import Path

from hermes_state_secretary_schedule import (
    ScheduleError,
    schedule_claim_conn,
    schedule_due_scan_conn,
    schedule_finalize_conn,
    schedule_release_conn,
)
from secretary.noting_scope import owning_db_scope
from secretary.scheduler_table import apply_schedule_action_conn, coverage_notice, instant_coverage_conn
from secretary.scheduler_time import (
    epoch,
    parse_schedule_expression,
    schedule_advance_epoch as schedule_advance_epoch,
    schedule_initial_next_run as schedule_initial_next_run,
)

logger = logging.getLogger(__name__)
DEFAULT_CLAIM_LEASE_SECONDS = 3600.0
DEFAULT_DUE_BATCH = 50


def default_enablement(db):
    """Consume the frozen C4 scheduler.enabled contract, never a Noting gate.

    Use the existing profile-bound readonly loader. Missing Scheduler configuration
    defaults to enabled; malformed/unreadable configuration fails this feature closed.
    This deliberately does not parse the independent Noting configuration block.
    """
    def enabled(_conversation_ref):
        try:
            from hermes_cli.config import load_config_readonly
            from hermes_cli.config_read_errors import FailedConfigRead

            with owning_db_scope(db):
                config = load_config_readonly()
            if isinstance(config, FailedConfigRead) or not isinstance(config, dict):
                return False
            block = config.get("scheduler", {})
            if not isinstance(block, dict) or not isinstance(block.get("enabled", True), bool):
                logger.warning("Invalid scheduler.enabled: expected a boolean in the owning profile config")
                return False
            return block.get("enabled", True)
        except Exception:
            logger.warning("Scheduler config unreadable; new admission is disabled", exc_info=True)
            return False

    return enabled


class SchedulerStore:
    """Authorized Main control surface; all supplied ownership is host-only.

    session_id must be the actual caller's physical Session. No Conversation or
    profile selector is exposed in the tool schema. parser/is_enabled are dependency
    injection seams for host integration and isolated tests, not model parameters.
    """

    def __init__(self, db, conversation_ref, *, session_id, parser=None, is_enabled=None):
        self.db = db
        self.conversation_ref = conversation_ref
        self.session_id = session_id
        self.home = Path(db.db_path).resolve().parent
        self.parser = parser or parse_schedule_expression
        self.is_enabled = is_enabled or default_enablement(db)

    def _authorize_conn(self, conn):
        ref = self.db.resolve_conversation_ref_conn(conn, self.session_id, read_only=True)
        route = self.db.resolve_conversation_route_conn(conn, self.conversation_ref)
        if (not ref or ref != self.conversation_ref or not route or route["id"] != self.session_id
                or Path(self.db.db_path).resolve().parent != self.home):
            raise ScheduleError("scope_denied", "Scheduler can access only the caller's current Main Conversation.",
                                "Do not retry with another Conversation or profile identifier.")

    def _notice_conn(self, conn, result, timestamp):
        """Complete the tool's required read before commit; unknown is a real read error.

        Unlike a Reminder that is already being delivered, a tool operation can still
        roll back atomically. Do not commit a mutation and then falsely report that it
        failed because the coverage read failed. A known empty table never blocks it.
        """
        try:
            value = instant_coverage_conn(conn, self.conversation_ref, now=timestamp)
        except Exception:
            logger.warning("Scheduler coverage read failed", exc_info=True)
            value = None
        if value is None:
            raise ScheduleError(
                "temporarily_unavailable", "The current 24-hour Schedule state could not be determined; this operation was not committed.",
                "Keep the intended change and retry when the owning Schedule state can be read.",
                field="schedule_table",
            )
        notice = coverage_notice(value)
        if notice:
            result["notice"] = notice
        return result

    def _failure_notice(self, result, timestamp):
        if result["error"]["code"] == "scope_denied":
            return result  # Do not probe a denied or disabled capability.
        try:
            with owning_db_scope(self.db), self.db._read_ctx() as conn:
                self._authorize_conn(conn)
                if not self.is_enabled(self.conversation_ref):
                    return result
                value = instant_coverage_conn(conn, self.conversation_ref, now=timestamp)
                if value is False:
                    result["notice"] = coverage_notice(False)
        except Exception:
            # Preserve the original operation error, not an empty-table claim. The
            # UNKNOWN_INSTANT_NOTICE text is for C6's already-delivering Reminder.
            logger.debug("Scheduler failed-operation coverage remains unknown", exc_info=True)
        return result

    def execute(self, args, *, now=None):
        """Return §7 JSON-compatible results; commit uncertainty is not reported as failure-to-write."""
        timestamp = epoch(now)
        write = not isinstance(args, dict) or args.get("action") != "list"
        callback_returned = False

        def apply(conn):
            nonlocal callback_returned
            self._authorize_conn(conn)
            if not self.is_enabled(self.conversation_ref):
                raise ScheduleError("scope_denied", "Scheduler is disabled or its owning configuration is unreadable.",
                                    "Check scheduler.enabled in this profile; Noting switches do not enable Scheduler.")
            from hermes_constants import profile_name_for_home

            result = apply_schedule_action_conn(
                conn, self.conversation_ref, args, now=timestamp,
                profile=profile_name_for_home(self.home), parser=self.parser, profile_home=self.home,
            )
            result = self._notice_conn(conn, result, timestamp)
            callback_returned = True
            return result

        try:
            with owning_db_scope(self.db):
                if write:
                    return self.db._execute_write(apply)
                with self.db._read_ctx() as conn:
                    return apply(conn)
        except ScheduleError as exc:
            result = {"success": False, "error": exc.error}
        except Exception:
            logger.warning("Scheduler control operation did not return normally", exc_info=True)
            uncertain = write and callback_returned
            result = {"success": False, "error": {
                "code": "outcome_unknown" if uncertain else "temporarily_unavailable",
                "message": ("The operation's outcome could not be established." if uncertain else
                            "The Schedule operation could not complete; its transaction was not published."),
                "next_action": ("Inspect the current Schedule Table before retrying; do not create a duplicate." if uncertain else
                                "Keep the intended change and retry through the normal Main tool path when storage is available."),
            }}
        return self._failure_notice(result, timestamp)

    def list(self, *, state=None, delivery_mode=None, now=None):
        args = {"action": "list"}
        if state is not None:
            args["state"] = state
        if delivery_mode is not None:
            args["delivery_mode"] = delivery_mode
        return self.execute(args, now=now)

    def create(self, content, schedule, delivery_mode, *, name="", now=None):
        return self.execute({"action": "create", "content": content, "schedule": schedule,
                             "delivery_mode": delivery_mode, "name": name}, now=now)

    def update(self, schedule_id, *, now=None, **changes):
        return self.execute({**changes, "action": "update", "schedule_id": schedule_id}, now=now)

    def pause(self, schedule_id, *, now=None):
        return self.execute({"action": "pause", "schedule_id": schedule_id}, now=now)

    def resume(self, schedule_id, *, now=None):
        return self.execute({"action": "resume", "schedule_id": schedule_id}, now=now)

    def delete(self, schedule_id, *, now=None):
        return self.execute({"action": "delete", "schedule_id": schedule_id}, now=now)


def instant_coverage(db, conversation_ref, *, now=None, exclude_occurrences=()):
    """I-S: read-only True/False/None. C6 uses the conn variant in admission transactions."""
    try:
        with owning_db_scope(db), db._read_ctx() as conn:
            return instant_coverage_conn(conn, conversation_ref, now=epoch(now),
                                         exclude_occurrences=exclude_occurrences)
    except Exception:
        logger.warning("Scheduler 24-hour coverage unavailable", exc_info=True)
        return None


def due_rows(db, *, now=None, limit=DEFAULT_DUE_BATCH, profile=None, conversation_ref=None):
    with owning_db_scope(db), db._read_ctx() as conn:
        return schedule_due_scan_conn(conn, now=epoch(now), limit=limit, profile=profile,
                                      conversation_ref=conversation_ref)


def claim_due(db, schedule_id, *, owner, now=None, lease_seconds=DEFAULT_CLAIM_LEASE_SECONDS,
              conversation_ref=None, expected_generation=None, is_enabled=None):
    timestamp = epoch(now)
    enabled = is_enabled or default_enablement(db)

    def claim(conn):
        found = conn.execute("SELECT conversation_ref FROM secretary_schedule_registry WHERE schedule_id=?",
                             (schedule_id,)).fetchone()
        if found is None or (conversation_ref is not None and found[0] != conversation_ref) or not enabled(found[0]):
            return None
        return schedule_claim_conn(conn, schedule_id, owner=owner, now=timestamp, lease_seconds=lease_seconds,
                                   conversation_ref=found[0], expected_generation=expected_generation)

    with owning_db_scope(db):
        return db._execute_write(claim)


def scan_and_claim_due(db, *, owner, now=None, limit=DEFAULT_DUE_BATCH, profile=None,
                       conversation_ref=None, is_enabled=None):
    """Existing scanner entry: default gate is independent Scheduler, never Notebook local state."""
    timestamp = epoch(now)
    enabled = is_enabled or default_enablement(db)
    claims = []
    for row in due_rows(db, now=timestamp, limit=limit, profile=profile, conversation_ref=conversation_ref):
        if not enabled(row["conversation_ref"]):
            continue
        current = claim_due(db, row["schedule_id"], owner=owner, now=timestamp,
                            conversation_ref=row["conversation_ref"], expected_generation=row["generation"],
                            is_enabled=enabled)
        if current is not None:
            claims.append(current)
    return claims


def finalize_delivery(db, schedule_id, claim_token, *, now=None,
                      carrier_message_uid=None, carrier_content=None):
    """Instant settlement requires native proof; C6 normally uses its append conn directly."""
    def finalize(conn):
        row = conn.execute("SELECT conversation_ref FROM secretary_schedule_registry WHERE schedule_id=?",
                           (schedule_id,)).fetchone()
        if row is None or not default_enablement(db)(row[0]):
            return None
        return schedule_finalize_conn(conn, schedule_id, claim_token, now=epoch(now),
                                      carrier_message_uid=carrier_message_uid, carrier_content=carrier_content)

    with owning_db_scope(db):
        return db._execute_write(finalize)


def release_claim(db, schedule_id, claim_token, *, now=None):
    return db._execute_write(lambda conn: schedule_release_conn(conn, schedule_id, claim_token, now=epoch(now)))


def stale_disable(db, schedule_id, *, now=None, expected_generation=None):
    """Quarantine only a witnessed corrupt definition, never an unseen newer update."""
    if expected_generation is None:
        return False

    def disable(conn):
        cursor = conn.execute(
            "UPDATE secretary_schedule_registry SET enabled=0,state='cancelled',generation=generation+1,"
            "claim_owner=NULL,claim_token=NULL,claim_expires_at=NULL,updated_at=? "
            "WHERE schedule_id=? AND generation=?", (epoch(now), schedule_id, expected_generation),
        )
        if cursor.rowcount:
            conn.execute("UPDATE secretary_pending_reminders SET status='cancelled' WHERE schedule_id=? "
                         "AND status='pending' AND carrier_message_uid IS NULL", (schedule_id,))
        return cursor.rowcount == 1

    return db._execute_write(disable)
