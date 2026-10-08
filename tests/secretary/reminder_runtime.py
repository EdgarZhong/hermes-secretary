"""Explicit main-runtime capability fixture for real Secretary gate/registry tests."""

from agent.context_compressor import ContextCompressor

from secretary.noting_scope import bind_main_runtime


class ReminderRuntime:
    pass


def bind_reminder_runtime(db, conversation_ref, session_id):
    runtime = ReminderRuntime()
    runtime._session_db = db
    runtime.session_id = session_id
    runtime._secretary_conversation_ref = conversation_ref
    runtime.model = "test/reminder-runtime"
    runtime.provider, runtime.base_url, runtime.api_mode, runtime.max_tokens = "openai", "", "chat_completions", None
    runtime.context_compressor = ContextCompressor(
        model="test/reminder-runtime", config_context_length=196000, threshold_percent=0.85, quiet_mode=True)
    assert bind_main_runtime(runtime)
    db._reminder_test_runtime = runtime  # Retain it as the host would retain its live main Agent.
    return runtime


def arm_native_reminder(db, ref, canonical, text, entry_id="entry"):
    """A real current Snapshot must own intent when native transcript append reconciles it."""
    from uuid import uuid4
    from secretary.notebook_model import NotebookWorkingState
    route = db.resolve_conversation_route(ref)
    anchor = "arm_" + uuid4().hex
    db.append_message(route["id"], "assistant", "Schedule established", message_uid=anchor)
    current = db.notebook_current(ref)
    payload = current["payload"] if current else None
    if payload:
        payload = {section: [e for e in entries if e["entry_id"] != entry_id] for section, entries in payload.items()}
    state = NotebookWorkingState(ref, payload, parse_schedule=lambda _expression: canonical)
    entry = state.create("user_reminder", {"message": text})
    state.schedule_create(entry["entry_id"], "fixture")
    payload = state.show()
    next(e for entries in payload.values() for e in entries if e["entry_id"] == entry["entry_id"])["entry_id"] = entry_id
    db.notebook_commit_snapshot(ref, payload, anchor_message_uid=anchor)
    return dict(db._read_one("SELECT * FROM secretary_schedule_registry WHERE conversation_ref=? AND notebook_entry_id=?",
                             (ref, entry_id)))


def persist_native_carrier(db, session_id, text):
    """Transport test substitute performs the actual native batch transaction, not queue ACK."""
    from secretary.reminders import active_delivery_batch_callback, confirm_active_delivery_batch
    messages = [{"role": "user", "content": text, "timestamp": text.source_timestamp}]
    rows = [{**messages[0]}]
    callback = active_delivery_batch_callback(db, messages, rows)
    db.append_messages_batch(session_id, rows, before_commit=callback)
    confirm_active_delivery_batch(messages)
