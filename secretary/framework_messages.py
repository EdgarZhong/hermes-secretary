"""Runtime-owned, at-most-once Framework timeline messages (02 §5.6)."""

import logging
import threading
import time
from contextlib import nullcontext
from dataclasses import dataclass
from typing import Callable

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
    snapshot_id: str | None = None
    termination: dict | None = None
    summary: str | None = None
    on_settled: Callable[[], None] | None = None

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


def append_runtime_row(parent, messages, row, *, expected_conversation_ref=None,
                       snapshot_id=None, termination=None, summary=None):
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
        if snapshot_id is None:
            append_message(messages, row)
        settings = None
        if snapshot_id is not None:
            from secretary.noting_scope import settings_for_db
            settings = settings_for_db(db)

        def prepare_completion(conn, target_session_id, _rows):
            from secretary.noting_notifications import completion_body
            from pathlib import Path

            from secretary.noting_notes import qualified_snapshot_conn
            snapshot = qualified_snapshot_conn(db, conn, expected_conversation_ref, snapshot_id,
                                               row["display_metadata"].get("noting_target_interval"))
            audit = db.notebook_snapshot_audit_conn(conn, snapshot_id)
            if audit["termination"] != termination:
                raise RuntimeError("Noting completion audit differs from the committed Snapshot")
            body = completion_body(snapshot, termination=termination, summary=summary,
                                   settings=settings, profile_home=Path(db.db_path).parent, db=db, conn=conn)
            row["content"] = build_framework_message_wrapper(body)
            row["display_metadata"]["display_text"] = body
            row["timestamp"] = snapshot["created_at"]

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
            if snapshot_id is not None:
                from secretary.noting_notes import qualified_snapshot_conn
                interval = row["display_metadata"].get("noting_target_interval")
                qualified_snapshot_conn(db, conn, expected_conversation_ref, snapshot_id, interval)
                conn.execute("INSERT INTO secretary_noting_note_receipts "
                             "(conversation_ref,interval_id,snapshot_id,carrier_message_uid) VALUES (?,?,?,?)",
                             (expected_conversation_ref, interval, snapshot_id, row["message_uid"]))
                # The DB write lock orders this live append with all Snapshot
                # commits. The outer framework/persist locks hide retry drafts
                # from Main; on rollback the live row is removed before release.
                if not any(message is row for message in messages):
                    append_message(messages, row)
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
                **({"prepare_rows": prepare_completion} if snapshot_id is not None else {}),
            )
        except BaseException:
            for index, message in enumerate(messages):
                if message is row:
                    del messages[index]
                    break
            raise
        sync_flushed_message_markers([row], [row])
        row[_DB_PERSISTED_MARKER] = True


def _runtime_valid(parent):
    from secretary.noting_runtime import is_main_conversation_agent
    db = getattr(parent, "_session_db", None)
    ref = getattr(parent, "_secretary_conversation_ref", None)
    return bool(db is not None and ref and is_main_conversation_agent(parent)
                and not getattr(parent, "_secretary_noting_child", False)
                and not getattr(parent, "_secretary_noting_profile", None)
                and isinstance(getattr(parent, "_session_messages", None), list))


def capture_queued_force_notices(parent):
    """Snapshot this owner's existing producer objects for one native attempt."""
    from agent.message_metadata import is_framework_message
    with _lock(parent):
        ref = getattr(parent, "_secretary_conversation_ref", None)
        return tuple(message for message in getattr(parent, "_secretary_framework_messages", ())
                     if message.conversation_ref == ref and message.producer == "force_dispatch"
                     and is_framework_message(message.row)
                     and message.row["display_metadata"].get("noting_force_dispatch") is True)


def retire_queued_force_notices(parent, db, conversation_ref, captured):
    """Native commit retired this interval; never turn an unappended row into history."""
    with _lock(parent):
        if (getattr(parent, "_session_db", None) is not db
                or getattr(parent, "_secretary_conversation_ref", None) != conversation_ref):
            return
        expired = {id(message) for message in captured}
        pending = getattr(parent, "_secretary_framework_messages", None)
        if pending:
            pending[:] = [message for message in pending if id(message) not in expired]


def publish_framework_message(parent, body, *, display_metadata=None, expected_conversation_ref=None, _producer=None,
                              _snapshot_id=None, _termination=None, _summary=None, _on_settled=None):
    """Publish only through the owning runtime; never start a Turn or durable pending work."""
    with _lock(parent):
        if not _runtime_valid(parent):
            _settle_callback(_on_settled)
            return False
        conversation_ref = parent._secretary_conversation_ref
        if expected_conversation_ref is not None and conversation_ref != expected_conversation_ref:
            _settle_callback(_on_settled)
            return False
        metadata = {"display_text": str(body), "origin": "framework",
                    "producer": _producer or "framework", **dict(display_metadata or {})}
        if _snapshot_id is not None:
            metadata.update(origin="notebook", producer="noting_result")
        row = {"role": "user", "content": build_framework_message_wrapper(body),
               "timestamp": time.time(), "display_kind": "process_complete",
               "display_metadata": metadata}
        message = _QueuedFrameworkMessage(
            conversation_ref, row, _producer, _snapshot_id, _termination, _summary, _on_settled)
        vars(parent).setdefault("_secretary_framework_messages", []).append(message)
    try:
        flush_framework_messages(parent)
    except BaseException:
        if _on_settled is not None:
            with _lock(parent):
                pending = parent._secretary_framework_messages
                pending[:] = [queued for queued in pending if queued is not message]
            _settle_callback(_on_settled)
        raise
    return True


def _settle_callback(callback):
    """Callbacks only release an in-memory claim; never close task owners here."""
    if callback is not None:
        try:
            callback()
        except Exception:
            logger.warning("Framework carrier settlement callback failed", exc_info=True)


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
        for message in pending:
            if message.conversation_ref != conversation_ref:
                _settle_callback(message.on_settled)
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
            for message in rows:
                _settle_callback(message.on_settled)
            return 0
        written = 0
        for message in rows:
            try:
                append_runtime_row(parent, parent._session_messages, message.row,
                                   expected_conversation_ref=message.conversation_ref,
                                   snapshot_id=message.snapshot_id, termination=message.termination,
                                   summary=message.summary)
                written += 1
                _display_committed_row(parent, message.row)
            except Exception as exc:
                from secretary.noting_notifications import SupersededNotingResult
                if isinstance(exc, SupersededNotingResult):
                    logger.debug("Superseded Noting Framework carrier discarded")
                else:
                    logger.warning("Framework tail write failed", exc_info=True)
            finally:
                _settle_callback(message.on_settled)
        return written


def publish_noting_completion(parent, commit_result, *, termination, summary, on_settled=None):
    from secretary.noting_notes import check_note_delivery
    try:
        return check_note_delivery(parent)
    finally:
        _settle_callback(on_settled)


def publish_noting_failure(parent, *, conversation_ref, specific_reason, on_settled=None):
    """A real no-Snapshot failure is a Framework fact, never a successful receipt."""
    if not isinstance(specific_reason, str) or not specific_reason.strip():
        _settle_callback(on_settled)
        return False
    from secretary.noting_notifications import failure_body
    return publish_framework_message(
        parent, failure_body(conversation_ref, specific_reason),
        display_metadata={"noting_run_output": True}, expected_conversation_ref=conversation_ref,
        _producer="noting_failure", _on_settled=on_settled,
    )
