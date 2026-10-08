"""Secretary due delivery on the classic CLI's existing REPL and busy monitor ticks."""

import logging
import os
import time
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CLISecretaryClaim:
    """Internal input-lane envelope; never a queued future Reminder Turn or model value."""
    db: object
    claim: dict


def poll_cli_reminders(cli, *, busy=False):
    """Idle caller owns the serial REPL lane; busy monitor only creates passive pending."""
    now = time.monotonic()
    if now < getattr(cli, "_secretary_reminder_next_poll", 0.0):
        return
    cli._secretary_reminder_next_poll = now + 5.0
    from secretary import reminders, schedules
    from secretary.noting_runtime import _main_conversation_ref, is_main_conversation_agent
    from secretary.noting_scope import owning_db_scope

    agent = getattr(cli, "agent", None)
    if not is_main_conversation_agent(agent):
        return
    db = agent._session_db
    try:
        with owning_db_scope(db):
            ref = _main_conversation_ref(agent)
            if not ref:
                return
            claims = schedules.scan_and_claim_due(
                db, owner=f"cli:{os.getpid()}", conversation_ref=ref, limit=5,
                is_enabled=schedules.default_enablement(db),
            )
            for claim in claims:
                if busy or claim["delivery_semantics"] != "user_reminder":
                    reminders.queue_pending_for_claim(db, claim)
                else:
                    # Synchronous dispatch on the REPL's existing input lane, never a
                    # separate run_conversation invocation or a future queued Reminder Turn.
                    cli._tui_process_one_input(CLISecretaryClaim(db, claim))
    except Exception:
        logger.warning("CLI Secretary reminder poll failed", exc_info=True)


def dispatch_cli_reminder_input(cli, value):
    """Narrow synthetic-input policy at the CLI's existing serial input admission."""
    if not isinstance(value, CLISecretaryClaim):
        return False
    from secretary import reminders
    from secretary.noting_scope import owning_db_scope

    with owning_db_scope(value.db):
        if getattr(cli, "_agent_running", False):
            reminders.convert_claim_to_pending(value.db, value.claim)
            return True
        receipt = reminders.admit_active_reminder(
            value.db, value.claim, session_id=str(getattr(cli.agent, "session_id", "") or ""))
        if receipt is None:
            reminders.release_claim(value.db, value.claim)
            return True
        cli._secretary_active_reminder_receipt = receipt
        cli._secretary_active_reminder_completed = False
        try:
            cli._tui_process_one_input(receipt["resolved"]["text"])
        finally:
            if not cli._secretary_active_reminder_completed:
                reminders.recover_active_reminder(value.db, receipt, passive=True)
            cli._secretary_active_reminder_receipt = None
    return True


def finish_cli_reminder_input(cli, result):
    """The ordinary chat lane reports acceptance/result; no new admission or busy state."""
    if getattr(cli, "_secretary_active_reminder_receipt", None) is not None:
        cli._secretary_active_reminder_completed = result is not None


def cli_reminder_input_text(cli, text):
    """Preserve the trusted carrier after the ordinary input lane's text sanitization."""
    receipt = getattr(cli, "_secretary_active_reminder_receipt", None)
    if receipt is None:
        return text
    from agent.message_metadata import preserve_user_input_origin
    return preserve_user_input_origin(receipt["resolved"]["text"], text)
