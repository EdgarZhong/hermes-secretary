"""Runtime-owned, at-most-once Framework timeline messages (02 §5.6)."""

import logging
import threading
import time
from contextlib import nullcontext
from dataclasses import dataclass

from agent.message_metadata import append_message, build_framework_message_wrapper

logger = logging.getLogger(__name__)

_EXTERNAL_EXECUTION_NOTICE = (
    "Background: Noting is unavailable because this Conversation's latest model request used an external agent runtime. "
    "Notebook updates can resume after native execution resumes."
)
_EXTERNAL_NOTICE_PRODUCER = "external_unavailability"


@dataclass(frozen=True)
class _QueuedFrameworkMessage:
    conversation_ref: str
    row: dict
    producer: str | None = None

    def __iter__(self):
        yield self.conversation_ref
        yield self.row


def publish_external_execution_notice(parent, *, expected_conversation_ref):
    """One D01 rejection notice per live owner until an actual Native dispatch."""
    with _lock(parent):
        if (not _runtime_valid(parent)
                or parent._secretary_conversation_ref != expected_conversation_ref
                or expected_conversation_ref in getattr(parent, "_secretary_external_notice_refs", ())
                or getattr(parent, "_secretary_last_main_execution", None) == "native"):
            return False
        published = publish_framework_message(
            parent, _EXTERNAL_EXECUTION_NOTICE, expected_conversation_ref=expected_conversation_ref,
            _producer=_EXTERNAL_NOTICE_PRODUCER,
        )
        if published:
            vars(parent).setdefault("_secretary_external_notice_refs", set()).add(expected_conversation_ref)
        return published


def reset_external_execution_notice(parent):
    """Called only by a confirmed actual Native Main request, never by hydration."""
    if not getattr(parent, "_secretary_external_notice_refs", None):
        return
    with _lock(parent):
        ref = getattr(parent, "_secretary_conversation_ref", None)
        parent._secretary_external_notice_refs.discard(ref)
        pending = getattr(parent, "_secretary_framework_messages", None)
        if pending:
            pending[:] = [message for message in pending if not (
                message.conversation_ref == ref and message.producer == _EXTERNAL_NOTICE_PRODUCER)]


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


class _FrameworkDisplayText(str):
    """Committed-row provenance on the existing two-argument status callback."""

    def __new__(cls, parent, row):
        value = super().__new__(cls, row["display_metadata"]["display_text"])
        value.parent, value.row = parent, row
        value.db = parent._session_db
        value.session_id = parent.session_id
        value.conversation_ref = parent._secretary_conversation_ref
        value.message_uid, value.content = row["message_uid"], row["content"]
        value.metadata = dict(row["display_metadata"])
        return value


def framework_display_owned(parent, text):
    """Only the native publisher's current live row can authorize presentation."""
    if (not isinstance(text, _FrameworkDisplayText) or text.parent is not parent
            or getattr(parent, "_session_db", None) is not text.db
            or getattr(parent, "_secretary_conversation_ref", None) != text.conversation_ref):
        return False
    if parent.session_id != text.session_id:
        # A same-Conversation native continuation may retain this row. A pre-id
        # reset/branch with a stale runtime ref must not borrow its display sink.
        with text.db._read_ctx() as conn:
            binding = conn.execute("SELECT conversation_ref FROM secretary_session_bindings WHERE session_id=?",
                                   (parent.session_id,)).fetchone()
        if not binding or binding[0] != text.conversation_ref:
            return False
    return any(row.get("message_uid") == text.message_uid and row.get("role") == "user"
               and row.get("content") == text.content and row.get("display_metadata") == text.metadata
               for row in getattr(parent, "_session_messages", ()) or ())


def _display_committed_row(parent, row):
    text = _FrameworkDisplayText(parent, row)
    # No fallback print: RPC/headless agents without a bound sink must stay quiet.
    for sink, args in ((getattr(parent, "_print_fn", None), (str(text),)),
                       (getattr(parent, "status_callback", None), ("framework", text))):
        if callable(sink) and framework_display_owned(parent, text):
            try:
                sink(*args)
            except Exception:
                logger.warning("Framework timeline presentation failed", exc_info=True)


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


def publish_framework_message(parent, body, *, display_metadata=None, expected_conversation_ref=None, _producer=None):
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
        vars(parent).setdefault("_secretary_framework_messages", []).append(
            _QueuedFrameworkMessage(conversation_ref, row, _producer))
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
        pending[:] = [message for message in pending if message.conversation_ref == conversation_ref]
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
        for message in rows:
            try:
                append_runtime_row(parent, parent._session_messages, message.row,
                                   expected_conversation_ref=message.conversation_ref)
                written += 1
                _display_committed_row(parent, message.row)
            except Exception:
                logger.warning("Framework tail write failed", exc_info=True)
        return written
