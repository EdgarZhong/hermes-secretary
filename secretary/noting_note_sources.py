"""Internal recovery provenance, independent from Notebook content and task ownership."""


def recovery_origin_conn(db, conn, ref, anchor, admission_id, child_session_id=None):
    """Validate the runner's original task in the Snapshot write transaction."""
    if admission_id is None:
        return None
    row = db.noting_admission_conn(conn, admission_id)
    if (row is None or row["conversation_ref"] != ref or row["anchor_message_uid"] != anchor
            or row["state"] in {"cancelled", "superseded"}):
        raise ValueError("Recovery Snapshot source no longer matches its original task")
    origin = {"admission_id": row["admission_id"], "compression_interval_id": row["compression_interval_id"]}
    if child_session_id is not None:
        witness = conn.execute(
            "SELECT json_extract(model_config,'$._noting_recovery.lease_holder') AS expected_holder "
            "FROM sessions WHERE id=? AND json_valid(model_config) "
            "AND json_extract(model_config,'$._noting_recovery.conversation_ref')=? "
            "AND json_extract(model_config,'$._noting_recovery.admission_id')=?",
            (child_session_id, ref, admission_id)).fetchone()
        if witness is None:
            raise ValueError("Recovery Snapshot child does not own the original source")
        lease = conn.execute("SELECT holder,expires_at FROM session_turn_leases WHERE conversation_id=?",
                             ("recovery:" + child_session_id,)).fetchone()
        import time
        if lease is None or not recovery_lease_live(
                lease["holder"], lease["expires_at"], witness["expected_holder"], now=time.time()):
            raise ValueError("Recovery Snapshot child no longer owns its native execution lease")
        origin["recovery_session_id"] = child_session_id
    return origin


# Only metadata in this Conversation is returned. The legacy arm reads the existing
# committed recovery witness; it never reads message/tool bodies or changes old rows.
_SOURCE_SQL = """
WITH snapshots AS (
    SELECT snapshot_id,conversation_ref,anchor_message_uid,termination_json
    FROM secretary_notebook_snapshots WHERE conversation_ref=?
      AND COALESCE(json_extract(termination_json,'$.type'),'')<>'superseded'
), proofs AS (
    SELECT s.snapshot_id,a.admission_id,NULL AS claimed_interval,1 AS parent_valid
    FROM snapshots s JOIN secretary_noting_task_admissions a ON a.snapshot_id=s.snapshot_id
    UNION ALL
    SELECT s.snapshot_id,json_extract(s.termination_json,'$.noting_origin.admission_id'),
           json_extract(s.termination_json,'$.noting_origin.compression_interval_id'),1
    FROM snapshots s WHERE json_type(s.termination_json,'$.noting_origin') IS NOT NULL
    UNION ALL
    SELECT s.snapshot_id,json_extract(r.model_config,'$._noting_recovery.admission_id'),NULL,
           f.id IS NOT NULL AND f.parent_session_id=r.parent_session_id
    FROM snapshots s JOIN sessions r
      ON json_valid(r.model_config)
     AND json_extract(r.model_config,'$._noting_recovery.snapshot_id')=s.snapshot_id
     AND json_extract(r.model_config,'$._noting_recovery.conversation_ref')=s.conversation_ref
     AND json_extract(r.model_config,'$._noting_recovery.committed')=1
    LEFT JOIN sessions f ON f.id=json_extract(r.model_config,'$._noting_recovery.failed_child_session_id')
)
SELECT p.*,s.conversation_ref,s.anchor_message_uid,a.conversation_ref AS source_ref,
       a.anchor_message_uid AS source_anchor,a.compression_interval_id,a.state
FROM proofs p JOIN snapshots s USING(snapshot_id)
LEFT JOIN secretary_noting_task_admissions a ON a.admission_id=p.admission_id
"""


def snapshot_source_intervals_conn(conn, ref):
    """Resolve all ordinary/new/legacy source proofs once; conflicting proof fails closed."""
    intervals = {}
    owners = {}
    for row in conn.execute(_SOURCE_SQL, (ref,)):
        if (row["source_ref"] != ref or row["source_anchor"] != row["anchor_message_uid"]
                or not row["parent_valid"] or row["state"] in {"cancelled", "superseded"}):
            raise ValueError("Invalid Note source proof for " + row["snapshot_id"])
        interval = row["compression_interval_id"]
        if row["claimed_interval"] is not None and row["claimed_interval"] != interval:
            raise ValueError("Conflicting Note source interval for " + row["snapshot_id"])
        proof = (row["admission_id"], interval)
        previous = owners.setdefault(row["snapshot_id"], proof)
        if previous != proof:
            raise ValueError("Conflicting Note source owners for " + row["snapshot_id"])
        intervals[row["snapshot_id"]] = interval
    return intervals


# A valid native owner is mandatory even when a process still has a queued/running
# audit. No Python registry lock is taken while the caller owns a DB transaction.
_RECOVERY_SOURCES_SQL = """
SELECT r.id,a.anchor_message_uid,a.compression_interval_id,
       json_extract(r.model_config,'$._noting_recovery.created_at') AS admitted_at,
       json_extract(r.model_config,'$._noting_recovery.status') AS recovery_status,
       json_extract(r.model_config,'$._noting_recovery.lease_holder') AS expected_holder,
       l.holder,l.expires_at,
       EXISTS (
           SELECT 1 FROM secretary_notebook_snapshots s
           WHERE s.conversation_ref=a.conversation_ref AND s.anchor_message_uid=a.anchor_message_uid
             AND COALESCE(json_extract(s.termination_json,'$.type'),'')<>'superseded'
             AND ((json_extract(s.termination_json,'$.noting_origin.recovery_session_id')=r.id
                   AND json_extract(s.termination_json,'$.noting_origin.admission_id')=a.admission_id
                   AND json_extract(s.termination_json,'$.noting_origin.compression_interval_id')=a.compression_interval_id)
                  OR (json_extract(r.model_config,'$._noting_recovery.committed')=1
                      AND json_extract(r.model_config,'$._noting_recovery.snapshot_id')=s.snapshot_id))
       ) AS snapshot_committed
FROM sessions r JOIN secretary_noting_task_admissions a
  ON json_valid(r.model_config)
 AND json_extract(r.model_config,'$._noting_recovery.admission_id')=a.admission_id
 AND json_extract(r.model_config,'$._noting_recovery.conversation_ref')=a.conversation_ref
JOIN sessions f ON f.id=json_extract(r.model_config,'$._noting_recovery.failed_child_session_id')
               AND f.parent_session_id=r.parent_session_id
LEFT JOIN session_turn_leases l ON l.conversation_id='recovery:'||r.id
WHERE a.conversation_ref=? AND a.state NOT IN ('superseded','cancelled')
"""


def recovery_lease_live(holder, expires_at, expected_holder=None, *, now):
    from hermes_state import _compression_lock_holder_process_is_dead
    return bool(holder and expires_at > now and (expected_holder is None or holder == expected_holder)
                and not _compression_lock_holder_process_is_dead(holder))


def recovery_source_tasks_conn(conn, ref):
    """Overlay explicit recovery owners on the existing latest-source qualification."""
    import time
    now = time.time()
    sources = []
    for row in conn.execute(_RECOVERY_SOURCES_SQL, (ref,)):
        pending = (not row["snapshot_committed"] and row["recovery_status"] in {"queued", "running"}
                   and recovery_lease_live(row["holder"], row["expires_at"], row["expected_holder"], now=now))
        sources.append({"anchor_message_uid": row["anchor_message_uid"],
                        "compression_interval_id": row["compression_interval_id"],
                        "admitted_at": row["admitted_at"] or 0, "state": "admitted" if pending else "settled"})
    return sources
