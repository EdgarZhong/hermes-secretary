"""Note-only eligibility and durable append receipt; the native FM publisher owns delivery."""

import logging

logger = logging.getLogger(__name__)

NOTE_RECEIPT_SCHEMA = """
CREATE TABLE IF NOT EXISTS secretary_noting_note_receipts (
    conversation_ref TEXT NOT NULL,
    interval_id TEXT NOT NULL,
    snapshot_id TEXT NOT NULL REFERENCES secretary_notebook_snapshots(snapshot_id),
    carrier_message_uid TEXT NOT NULL,
    PRIMARY KEY(conversation_ref, interval_id)
)
"""


def _path(db, conn, ref):
    full = [row for row in db.get_full_foreground_conn(conn, ref) if row.get("message_identity")]
    introduced = {}
    for index, row in enumerate(db._foreground_source_rows_conn(conn, ref)):
        introduced.setdefault(row["message_uid"], index)
    boundaries = {row["message_uid"] for row in full if row.get("is_compaction")}
    position = {row["message_uid"]: (introduced[row["message_uid"]], int(row["message_uid"] in boundaries))
                for row in full if not row.get("is_compaction") and row["message_uid"] in introduced
                and (row.get("display_metadata") or {}).get("noting_run_output") is not True}
    boundary = max(((introduced[uid], 0) for uid in boundaries if uid in introduced), default=None)
    latest = max((row for row in full if row.get("is_compaction") and row["message_uid"] in introduced),
                 key=lambda row: introduced[row["message_uid"]], default=None)
    return position, boundary, latest


def select_note_conn(db, conn, ref):
    """Select by legal original coverage, independent of commit wall clock and global pointer."""
    positions, boundary, latest_boundary = _path(db, conn, ref)
    if boundary is None:
        return None
    interval = db._noting_publication_interval(latest_boundary)
    if conn.execute("SELECT 1 FROM secretary_noting_note_receipts WHERE conversation_ref=? AND interval_id=?",
                    (ref, interval)).fetchone() is not None:
        return None
    snapshots = conn.execute(
        "SELECT s.snapshot_id,s.anchor_message_uid,s.rowid AS sequence FROM secretary_notebook_snapshots s "
        "WHERE s.conversation_ref=? AND COALESCE(json_extract(s.termination_json,'$.type'),'')<>'superseded' "
        "AND NOT EXISTS (SELECT 1 FROM secretary_noting_task_admissions a WHERE a.snapshot_id=s.snapshot_id "
        "AND a.compression_interval_id=?)",
        (ref, interval)).fetchall()
    candidates = [(positions[row["anchor_message_uid"]], row["sequence"], row["snapshot_id"])
                  for row in snapshots if row["anchor_message_uid"] in positions
                  and positions[row["anchor_message_uid"]] < boundary]
    if not candidates:
        return None
    position, _sequence, snapshot_id = max(candidates)
    # Only the most recent source task can still change the selected result.
    latest = [(positions[row["anchor_message_uid"]], row["admitted_at"], row["state"])
              for row in conn.execute("SELECT * FROM secretary_noting_task_admissions WHERE conversation_ref=? "
                                      "AND state<>'superseded' AND compression_interval_id<>?", (ref, interval))
              if row["anchor_message_uid"] in positions and positions[row["anchor_message_uid"]] < boundary]
    if latest:
        source, _admission_id, state = max(latest)
        if source >= position and state == "admitted":
            return None
    return {"snapshot_id": snapshot_id, "interval_id": interval}


def qualified_snapshot_conn(db, conn, ref, snapshot_id, interval):
    from secretary.noting_notifications import SupersededNotingResult
    selected = select_note_conn(db, conn, ref)
    if selected != {"snapshot_id": snapshot_id, "interval_id": interval}:
        raise SupersededNotingResult("The Note target or source is no longer eligible")
    return db.notebook_snapshot_audit_conn(conn, snapshot_id)


def check_note_delivery(parent):
    """Idempotent notification at commit/publication/attach/request; never inject inside a Turn."""
    try:
        from secretary.noting_scope import current_main_runtime
        db = getattr(parent, "_session_db", None)
        ref = getattr(parent, "_secretary_conversation_ref", None)
        if db is not None and ref:
            parent = current_main_runtime(db, ref) or parent
        from secretary.framework_messages import _lock, _runtime_valid, publish_framework_message
        from secretary.noting_runtime import noting_trigger_gate
        with _lock(parent):
            if not _runtime_valid(parent):
                return False
            db, ref = parent._session_db, parent._secretary_conversation_ref
            if not noting_trigger_gate(db, ref)[0]:
                return False
            with db._read_ctx() as conn:
                selected = select_note_conn(db, conn, ref)
                if selected is None:
                    return False
                snapshot = db.notebook_snapshot_audit_conn(conn, selected["snapshot_id"])
            for queued in getattr(parent, "_secretary_framework_messages", ()):
                metadata = queued.row.get("display_metadata") or {}
                if (queued.snapshot_id == selected["snapshot_id"]
                        and metadata.get("noting_target_interval") == selected["interval_id"]):
                    return False
            termination = snapshot["termination"]
            summary = termination.get("reason") or {
                "forced": "The Noting execution budget ended.",
                "context_overflow": "The Noting context window was exhausted.",
            }.get(termination["type"], "Notebook maintenance completed.")
            return publish_framework_message(
                parent, "", expected_conversation_ref=ref, _producer="noting_completion",
                _snapshot_id=selected["snapshot_id"], _termination=termination, _summary=summary,
                display_metadata={"noting_run_output": True, "noting_snapshot_id": selected["snapshot_id"],
                                  "noting_target_interval": selected["interval_id"]})
    except Exception:
        logger.warning("Note eligibility check failed", exc_info=True)
        return False
