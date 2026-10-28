"""Force startup gates the first model request on acceptance of its stable native FM."""

import threading


def dispatch_force(parent, admission, messages):
    from secretary.noting_child import spawn_noting_task, finish_child_admission
    from secretary.framework_messages import _lock, publish_framework_message
    ready = threading.Event()
    try:
        worker = spawn_noting_task(parent, admission, parent_active_messages=messages, start_gate=ready)
        with _lock(parent):
            published = publish_framework_message(
                parent,
                "The context is nearing its limit, and a Notebook update task has been dispatched. Consider compacting soon. When you do, prioritize preserving the content after this message.",
                expected_conversation_ref=admission.conversation_ref,
                display_metadata={"noting_force_dispatch": True, "noting_admission_id": admission.admission_id},
                _producer="force_dispatch")
            rows = [*getattr(parent, "_session_messages", ()),
                    *(message.row for message in getattr(parent, "_secretary_framework_messages", ()))]
            accepted = published and any((row.get("display_metadata") or {}).get("noting_admission_id")
                                         == admission.admission_id for row in rows)
            if not accepted:
                finish_child_admission(parent._session_db, admission.admission_id, status="failed")
                raise RuntimeError("Force dispatch notice was not accepted by its owning runtime")
        return worker
    finally:
        ready.set()
