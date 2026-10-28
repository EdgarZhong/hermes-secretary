"""Additive attempt facts over the existing immutable Anchor admission history.

Legacy admission and child rows remain untouched. New attempts have negative integer
handles, disjoint from SQLite's historical positive admission IDs. Public methods
continue to expose one opaque admission handle, never decode its representation.
"""

import time

SCHEMA = """
CREATE TABLE IF NOT EXISTS secretary_noting_attempts (
    admission_id INTEGER PRIMARY KEY,
    anchor_record_id INTEGER NOT NULL REFERENCES secretary_noting_admissions(admission_id),
    conversation_ref TEXT NOT NULL REFERENCES secretary_conversations(conversation_ref),
    anchor_message_uid TEXT NOT NULL,
    kind TEXT NOT NULL,
    compression_interval_id TEXT NOT NULL,
    admitted_at REAL NOT NULL,
    operation_id TEXT,
    state TEXT NOT NULL DEFAULT 'admitted',
    snapshot_id TEXT REFERENCES secretary_notebook_snapshots(snapshot_id),
    child_session_id TEXT,
    profile TEXT,
    status TEXT,
    registered_at REAL,
    finished_at REAL
);
CREATE INDEX IF NOT EXISTS idx_secretary_attempt_scope
    ON secretary_noting_attempts(conversation_ref, state);
CREATE VIEW IF NOT EXISTS secretary_noting_task_admissions AS
    SELECT admission_id,conversation_ref,anchor_message_uid,kind,compression_interval_id,admitted_at,
           operation_id,state,snapshot_id FROM secretary_noting_attempts
    UNION ALL
    SELECT a.*,NULL AS operation_id,
           CASE WHEN json_valid(s.model_config)
                     AND json_extract(s.model_config,'$._secretary_noting_commit.snapshot_id') IS NOT NULL
                THEN 'committed' ELSE COALESCE(c.status,'admitted') END AS state,
           CASE WHEN json_valid(s.model_config)
                THEN json_extract(s.model_config,'$._secretary_noting_commit.snapshot_id') END AS snapshot_id
    FROM secretary_noting_admissions a LEFT JOIN secretary_noting_children c USING(admission_id)
    LEFT JOIN sessions s ON s.id=c.child_session_id
    WHERE NOT EXISTS (SELECT 1 FROM secretary_noting_attempts t WHERE t.anchor_record_id=a.admission_id)
       OR EXISTS (SELECT 1 FROM secretary_noting_children c WHERE c.admission_id=a.admission_id);
CREATE VIEW IF NOT EXISTS secretary_noting_task_children AS
    SELECT admission_id,child_session_id,profile,status,registered_at,finished_at
    FROM secretary_noting_attempts WHERE status IS NOT NULL
    UNION ALL
    SELECT c.* FROM secretary_noting_children c
    WHERE c.child_session_id IS NOT NULL
"""


def init_attempts(cursor):
    for statement in SCHEMA.split(";"):
        if statement.strip():
            cursor.execute(statement)


def admit_attempt(conn, ref, anchor, kind, interval, operation_id):
    existing = conn.execute(
        "SELECT 1 FROM secretary_noting_task_admissions WHERE conversation_ref=? AND anchor_message_uid=? "
        "AND state NOT IN ('cancelled','superseded','failed','abandoned')", (ref, anchor)).fetchone()
    if existing is not None:
        return None
    conn.execute("UPDATE secretary_noting_attempts SET state='superseded',status='superseded',finished_at=? "
                 "WHERE conversation_ref=? AND kind<>'force' AND state='admitted'", (time.time(), ref))
    # The historical Anchor identity remains single and retains its original audit.
    conn.execute("INSERT OR IGNORE INTO secretary_noting_admissions "
                 "(conversation_ref,anchor_message_uid,kind,compression_interval_id,admitted_at) VALUES (?,?,?,?,?)",
                 (ref, anchor, kind, interval, time.time()))
    record = conn.execute("SELECT admission_id FROM secretary_noting_admissions "
                          "WHERE conversation_ref=? AND anchor_message_uid=?", (ref, anchor)).fetchone()[0]
    handle = conn.execute("SELECT MIN(COALESCE((SELECT MIN(admission_id) FROM secretary_noting_attempts),0),"
                          "COALESCE((SELECT MIN(admission_id) FROM secretary_noting_admissions),0),0)-1").fetchone()[0]
    conn.execute("INSERT INTO secretary_noting_attempts "
                 "(admission_id,anchor_record_id,conversation_ref,anchor_message_uid,kind,compression_interval_id,"
                 "admitted_at,operation_id) VALUES (?,?,?,?,?,?,?,?)",
                 (handle, record, ref, anchor, kind, interval, time.time(), operation_id))
    return handle


def register_attempt_child(conn, admission_id, child_session_id, profile):
    changed = conn.execute("UPDATE secretary_noting_attempts SET child_session_id=?,profile=?,status='running',"
                           "registered_at=COALESCE(registered_at,?) WHERE admission_id=? AND state='admitted' "
                           "AND (status IS NULL OR status='running')",
                           (child_session_id, profile, time.time(), admission_id)).rowcount
    if changed != 1:
        from hermes_state_secretary_noting import NotingChildSnapshotOwnershipError
        raise NotingChildSnapshotOwnershipError("Noting attempt no longer owns child registration")


def finish_attempt_child(conn, admission_id, status):
    changed = conn.execute(
        "UPDATE secretary_noting_attempts SET status=?,finished_at=?,state=CASE WHEN state='admitted' "
        "THEN ? ELSE state END WHERE admission_id=? AND (status IS NULL OR status='running')",
        (status, time.time(), status, admission_id)).rowcount
    return changed == 1
