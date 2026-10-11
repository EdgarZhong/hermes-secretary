"""Runtime-owned, at-most-once Framework timeline messages (02 §5.6)."""

import logging
import threading
import time
from contextlib import nullcontext

from agent.message_metadata import append_message, build_framework_message_wrapper

logger = logging.getLogger(__name__)


def _lock(parent):
    return vars(parent).setdefault("_secretary_framework_lock", threading.RLock())


def mark_framework_turn(parent, *, running):
    """Serialize an existing Turn observation with framework tail writes, not admission."""
    with _lock(parent):
        parent._secretary_main_turn_running = running
        if not running and getattr(parent, "_secretary_framework_messages", None):
            flush_framework_messages(parent)


def _busy(parent):
    return bool(getattr(parent, "_relay_pending_turn_id", None)
                or getattr(parent, "_secretary_main_turn_running", False)
                or getattr(parent, "_active_compression_commit_fence", None))


def _framework_target_matches(parent, db, messages, conversation_ref):
    return (getattr(parent, "_session_db", None) is db
            and getattr(parent, "_session_messages", None) is messages
            and getattr(parent, "_secretary_conversation_ref", None) == conversation_ref)


def append_runtime_row(parent, messages, row, *, expected_conversation_ref=None):
    """Use native flush/dedup so the live row and its durable row have one identity."""
    from agent.context_compressor import _DB_PERSISTED_MARKER
    from agent.transcript_repair import sync_flushed_message_markers

    lock = getattr(parent, "_session_persist_lock", None)
    with nullcontext() if lock is None else lock:
        db = parent._session_db
        if expected_conversation_ref is not None and not _framework_target_matches(
                parent, db, messages, expected_conversation_ref):
            raise RuntimeError("Framework runtime owner changed")
        # Existing live rows must land first: never insert a framework/reminder into
        # the durable middle ahead of still-unflushed tool results or assistant output.
        flush = getattr(parent, "_flush_messages_to_session_db", None)
        if callable(flush) and flush(messages) is False:
            raise RuntimeError("Native transcript tail flush failed")
        if expected_conversation_ref is not None and not _framework_target_matches(
                parent, db, messages, expected_conversation_ref):
            raise RuntimeError("Framework runtime owner changed during tail flush")
        # Native flush may adopt a same-Conversation compression child. Freeze its
        # resulting physical target rather than reading mutable parent fields later.
        session_id = parent.session_id
        append_message(messages, row)
        def record_carrier(conn, target_session_id, _rows):
            if expected_conversation_ref is not None:
                binding = conn.execute(
                    "SELECT conversation_ref FROM secretary_session_bindings WHERE session_id=?",
                    (target_session_id,),
                ).fetchone()
                # Provenance validation in the existing append transaction; never
                # look up or route to another owner. CLI reset does not take our lock.
                if (not _framework_target_matches(parent, db, messages, expected_conversation_ref)
                        or parent.session_id != target_session_id
                        or binding is None or binding[0] != expected_conversation_ref):
                    raise RuntimeError("Framework target no longer belongs to its runtime")
            for rid in (row.get("display_metadata") or {}).get("reminder_ids", []):
                conn.execute("UPDATE secretary_pending_reminders SET carrier_content=?, carrier_message_uid=? "
                             "WHERE reminder_id=? AND status='pending'",
                             (str(row["content"]), row["message_uid"], rid))

        try:
            db.append_messages_batch(
                session_id, [row],
                compression_lock_holder=getattr(parent, "_active_compression_lock_holder", None),
                turn_lease_holder=getattr(parent, "_active_session_turn_lease_holder", None),
                turn_lease_ttl_seconds=getattr(parent, "_active_session_turn_lease_ttl_seconds", 300.0),
                before_commit=record_carrier,
            )
        except BaseException:
            messages.remove(row)
            raise
        sync_flushed_message_markers([row], [row])
        row[_DB_PERSISTED_MARKER] = True


def _runtime_valid(parent):
    from secretary.noting_runtime import is_main_conversation_agent
    db = getattr(parent, "_session_db", None)
    ref = getattr(parent, "_secretary_conversation_ref", None)
    from secretary.reminder_request import injection_eligible
    return bool(db is not None and ref and injection_eligible(parent) and is_main_conversation_agent(parent)
                and isinstance(getattr(parent, "_session_messages", None), list))


def publish_framework_message(parent, body, *, display_metadata=None, expected_conversation_ref=None):
    """Publish only through the owning runtime; never start a Turn or durable pending work."""
    with _lock(parent):
        if not _runtime_valid(parent):
            return False
        conversation_ref = parent._secretary_conversation_ref
        if expected_conversation_ref is not None and conversation_ref != expected_conversation_ref:
            return False
        row = {"role": "user", "content": build_framework_message_wrapper(body),
               "timestamp": time.time(), "display_kind": "process_complete",
               "display_metadata": {"display_text": str(body), **dict(display_metadata or {})}}
        vars(parent).setdefault("_secretary_framework_messages", []).append((conversation_ref, row))
    flush_framework_messages(parent)
    return True


def _wait_for_fence(parent):
    from agent.memory_provider import spawn_context_thread

    if getattr(parent, "_secretary_framework_fence_waiter", False):
        return
    parent._secretary_framework_fence_waiter = True

    def wait():
        try:
            while getattr(parent, "_active_compression_commit_fence", None) is not None:
                time.sleep(0.02)
            flush_framework_messages(parent)
        finally:
            parent._secretary_framework_fence_waiter = False

    spawn_context_thread(wait, name="secretary-framework-tail", daemon=True).start()


def flush_framework_messages(parent):
    """Turn-end/fence-clear tail flush; a process crash intentionally loses queued rows."""
    with _lock(parent):
        pending = getattr(parent, "_secretary_framework_messages", None)
        if not pending:
            return 0
        conversation_ref = getattr(parent, "_secretary_conversation_ref", None)
        pending[:] = [(ref, row) for ref, row in pending if ref == conversation_ref]
        if not pending:
            return 0
        if _busy(parent):
            if getattr(parent, "_active_compression_commit_fence", None) is not None:
                _wait_for_fence(parent)
            return 0
        rows = list(pending)
        pending.clear()  # at-most-once, including persistence failure
        if not _runtime_valid(parent):
            return 0
        written = 0
        for ref, row in rows:
            try:
                append_runtime_row(parent, parent._session_messages, row, expected_conversation_ref=ref)
                written += 1
            except Exception:
                logger.warning("Framework tail write failed", exc_info=True)
        return written
