"""Task qualification shared by native cancellation, replacement and Snapshot commit."""

import logging
from contextlib import nullcontext

logger = logging.getLogger(__name__)


def task_state(child):
    admission_id = getattr(child, "_secretary_noting_admission_id", None)
    if admission_id is None:
        return "admitted"  # Explicit recovery has its own durable owner.
    row = child._session_db.noting_admission(admission_id)
    return row["state"] if row else "abandoned"


def require_commit(conn, admission_id):
    if admission_id is not None and conn.execute(
            "SELECT 1 FROM secretary_noting_task_admissions WHERE admission_id=? AND state='admitted'",
            (admission_id,)).fetchone() is None:
        raise ValueError("Noting admission no longer owns commit qualification")


def record_commit(conn, admission_id, snapshot_id):
    if admission_id is not None:
        changed = conn.execute(
            "UPDATE secretary_noting_attempts SET state='committed',snapshot_id=? "
            "WHERE admission_id=? AND state='admitted'", (snapshot_id, admission_id)).rowcount
        if changed != 1:
            raise ValueError("Noting commit qualification changed")


def retire_invalid_tasks(db, conversation_ref):
    """Freeze already-produced work under its tool lock; interruption never waits for API I/O."""
    from secretary.noting_child import _ACTIVE_NOTING_LOCK, _ACTIVE_NOTING_TASKS
    from pathlib import Path
    scope = str(Path(db.db_path).resolve())
    with _ACTIVE_NOTING_LOCK:
        children = [child for (path, _), child in _ACTIVE_NOTING_TASKS.items()
                    if path == scope and child._secretary_parent_conversation_ref == conversation_ref]
    for child in children:
        lock = getattr(child, "_noting_notebook_lock", None)
        with lock if lock is not None else nullcontext():
            state = task_state(child)
            if state not in {"superseded", "cancelled", "abandoned"}:
                continue
            child._secretary_noting_terminal_action_done = True
            child._secretary_noting_retired = state
            store = getattr(child, "_noting_notebook_store", None)
            if state == "superseded" and store is not None:
                _save_replacement_audit(db, child, store.freeze())
        interrupt = getattr(child, "interrupt", None)
        if callable(interrupt):
            interrupt("Noting task " + state)
    from secretary.noting_child import _NOTING_COMPLETIONS, _end_completion
    with _ACTIVE_NOTING_LOCK:
        handles = [handle for (path, _), handle in _NOTING_COMPLETIONS.items()
                   if path == scope and handle.admission.conversation_ref == conversation_ref]
    for handle in handles:
        admission = db.noting_admission(handle.admission.admission_id)
        if admission is not None and admission["state"] in {"superseded", "cancelled", "abandoned"}:
            if admission["state"] == "superseded" and admission["snapshot_id"] is None:
                frozen = handle.frozen_work
                if frozen is not None:
                    from secretary.notebook_contract import SECTIONS
                    base = frozen.get("base_snapshot_id")
                    prior = db.notebook_snapshot_audit(base) if base else None
                    payload = prior["payload"] if prior else {section: [] for section in SECTIONS}
                    _save_audit(db, admission["admission_id"], payload)
            _end_completion(db, handle, task_cleanup=True)


def _save_replacement_audit(db, child, state):
    _save_audit(db, child._secretary_noting_admission_id, state)


def _save_audit(db, admission_id, state):
    def write(conn):
        row = db.noting_admission_conn(conn, admission_id)
        if row["snapshot_id"] is not None or row["state"] != "superseded":
            return
        result = db.notebook_commit_snapshot_result_conn(
            conn, row["conversation_ref"], state, anchor_message_uid=row["anchor_message_uid"],
            trigger_type=row["kind"], termination={"type": "superseded"})
        conn.execute("UPDATE secretary_noting_attempts SET snapshot_id=? WHERE admission_id=?",
                     (result["snapshot_id"], admission_id))
        db.noting_child_finish_conn(conn, admission_id, status="superseded")
    db._execute_write(write)


def cancel_operation(parent, operation_id):
    """CAS against commit in one DB transaction; Force and complete Snapshots survive."""
    db = getattr(parent, "_session_db", None)
    ref = getattr(parent, "_secretary_conversation_ref", None)
    if db is None or not ref or not operation_id:
        return

    def cancel(conn):
        rows = conn.execute(
            "SELECT admission_id FROM secretary_noting_task_admissions WHERE conversation_ref=? "
            "AND operation_id=? AND kind<>'force' AND state='admitted'", (ref, operation_id)).fetchall()
        for row in rows:
            conn.execute("UPDATE secretary_noting_attempts SET state='cancelled' WHERE admission_id=?",
                         (row["admission_id"],))
            db.noting_child_finish_conn(conn, row["admission_id"], status="cancelled")
    db._execute_write(cancel)
    retire_invalid_tasks(db, ref)


def finish_operation(parent, operation_id, *, succeeded):
    if not succeeded:
        cancel_operation(parent, operation_id)
    from secretary.noting_notes import check_note_delivery
    check_note_delivery(parent)
