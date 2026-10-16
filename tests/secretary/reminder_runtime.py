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
    """Create independent Scheduler intent without a Notebook Snapshot."""
    from secretary.schedules import SchedulerStore
    route = db.resolve_conversation_route(ref)
    expression = canonical.get("run_at") or canonical.get("expression")
    if expression is None:
        raise ValueError("Fixture requires an explicit native time expression")
    store = SchedulerStore(db, ref, session_id=route["id"])
    result = store.create(text, expression, "instant", name=entry_id)
    assert result["success"], result
    return dict(db._read_one("SELECT * FROM secretary_schedule_registry WHERE schedule_id=?",
                             (result["schedule"]["schedule_id"],)))


def persist_native_carrier(db, session_id, text):
    """Transport test substitute performs the actual native batch transaction, not queue ACK."""
    from secretary.reminders import (
        active_delivery_batch_callback, active_delivery_prepare_callback, confirm_active_delivery_batch,
    )
    messages = [{"role": "user", "content": text, "timestamp": text.source_timestamp}]
    rows = [{**messages[0]}]
    callback = active_delivery_batch_callback(db, messages, rows)
    prepare = active_delivery_prepare_callback(db, messages, rows)
    db.append_messages_batch(session_id, rows, before_commit=callback, prepare_rows=prepare)
    confirm_active_delivery_batch(messages)
