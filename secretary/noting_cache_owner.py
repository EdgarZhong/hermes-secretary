"""Ordinary Gateway reclamation and synchronous prefix freeze share the native owner lock."""


def claim_cache_release(parent):
    """Either maintenance owns the runtime, or retirement wins before any new freeze."""
    if parent is None or not hasattr(parent, "__dict__"):
        return True
    from secretary.noting_timers import holds_maintenance, refresh_maintenance, cancel_parent_idle_timer
    from agent.context_compaction_request import _lock, cancel_native_request
    refresh_maintenance(parent)
    with _lock(parent):
        if holds_maintenance(parent):
            return False
        _retire_disabled_period(parent)
        parent._secretary_parent_closed = True
        cancel_native_request(parent, boundary=True)
        cancel_parent_idle_timer(parent, notify=False)
        return True


def recover_dead_tasks(db, ref):
    """Expired execution evidence retires both schema generations without moving Snapshots."""
    import time
    from agent.turn_facade_lease import LEASE_TTL_SECONDS
    now = time.time()

    def reap(conn):
        rows = conn.execute(
            "SELECT a.*,c.child_session_id,c.status,c.registered_at FROM secretary_noting_task_admissions a "
            "LEFT JOIN secretary_noting_task_children c USING(admission_id) WHERE a.conversation_ref=? "
            "AND (a.state IN ('admitted','running') OR c.status='running')", (ref,)).fetchall()
        for row in rows:
            started = row["registered_at"] or row["admitted_at"]
            if now - started <= LEASE_TTL_SECONDS or _task_has_execution(db, conn, row["child_session_id"], now):
                continue
            _abandon_task(conn, row, now)
    db._execute_write(reap)


def _task_has_execution(db, conn, child_id, now):
    if not child_id:
        return False
    from secretary.noting_task_presence import task_is_live
    from secretary.noting_child import active_noting_task
    if active_noting_task(child_id, db=db) is not None or task_is_live(conn, child_id, now):
        return True
    key = db._session_turn_lease_key_on_conn(conn, child_id)
    return conn.execute("SELECT 1 FROM session_turn_leases WHERE conversation_id=? AND expires_at>?",
                        (key, now)).fetchone() is not None


def _abandon_task(conn, row, now):
    admission_id = row["admission_id"]
    if conn.execute("SELECT 1 FROM secretary_noting_attempts WHERE admission_id=?", (admission_id,)).fetchone():
        conn.execute("UPDATE secretary_noting_attempts SET state=CASE WHEN state='admitted' THEN 'abandoned' "
                     "ELSE state END,status='abandoned',finished_at=? WHERE admission_id=?",
                     (now, admission_id))
    else:
        conn.execute("INSERT INTO secretary_noting_children (admission_id,status,registered_at,finished_at) "
                     "VALUES (?,'abandoned',?,?) ON CONFLICT(admission_id) DO UPDATE SET "
                     "status='abandoned',finished_at=excluded.finished_at",
                     (admission_id, row["admitted_at"], now))


def _retire_disabled_period(parent):
    """A disabled owner being reclaimed cannot retain an orphaned off-period timer."""
    from secretary.noting_scope import is_current_main_runtime, settings_for_db
    if not is_current_main_runtime(parent):
        return  # A temporary owner loss must retain its due fact.
    db, ref = parent._session_db, parent._secretary_conversation_ref
    settings = settings_for_db(db)
    if not settings.enabled or not settings.idle_enabled or not db.notebook_local_enabled(ref):
        db._execute_write(lambda conn: conn.execute(
            "DELETE FROM secretary_noting_idle_state WHERE conversation_ref=? AND trigger_produced_at IS NULL",
            (ref,)))
