"""Persist native Turn provenance and exceptional outcomes on the accepted source.

Uses the existing message metadata writer/transaction; no message, schema or event journal.
"""
from __future__ import annotations

import json


def persist_turn_source(db, session_id, row_id, marker, *, turn_lease_holder=None, compression_lock_holder=None):
    """Backfill only this exact native UID's display metadata, under native guards."""
    uid, turn_id = marker.get("message_uid"), marker.get("turn_id")
    if type(row_id) is not int or not isinstance(uid, str) or not uid or not isinstance(turn_id, str) or not turn_id.strip():
        return False
    lineage = db._resume_lineage_ids(session_id)
    marks = ",".join("?" for _ in lineage)
    def write(conn):
        db._check_transcript_write_guards(conn, session_id, compression_lock_holder,
                                         turn_lease_holder=turn_lease_holder, reject_active_turn_lease=True)
        source = conn.execute("SELECT role,message_uid FROM messages WHERE id=? "
                              f"AND session_id IN ({marks})", (row_id, *lineage)).fetchone()
        if source is None or tuple(source) != ("user", uid):
            return False
        generation = conn.execute("SELECT active,compacted FROM messages WHERE message_uid=? "
                                  f"AND session_id IN ({marks}) ORDER BY id DESC LIMIT 1", (uid, *lineage)).fetchone()
        if generation is None or not (generation[0] or generation[1]):
            return False
        row = conn.execute("SELECT id,display_metadata FROM messages WHERE role='user' AND message_uid=? "
                           f"AND session_id IN ({marks}) AND (active=1 OR compacted=1) "
                           "ORDER BY active DESC,id DESC LIMIT 1", (uid, *lineage)).fetchone()
        if row is None:
            return False
        metadata = db._decode_display_metadata(row["display_metadata"]) or {}
        if metadata.get("turn_source") == marker:
            return True
        metadata["turn_source"] = dict(marker)
        conn.execute("UPDATE messages SET display_metadata=? WHERE id=?",
                     (db._encode_display_metadata(metadata), row["id"]))
        return True
    return db._execute_write(write, patience_s=0.0)


def _reconcile_outputs(outcome, rows):
    """Only native occurrence identity joins an observed call to its durable result."""
    durable = {row["tool_call_uid"]: row["message_uid"] for row in rows
               if row["role"] == "tool" and row["tool_call_uid"]}
    messages = {row["message_uid"]: row for row in rows if row["role"] == "assistant"}
    outputs = []
    for segment in outcome.get("outputs", []):
        segment = dict(segment)
        before_commit = segment.pop("_before_commit", False)
        message = messages.get(segment.get("message_uid"))
        if message is not None and before_commit:
            facet = "reasoning" if segment["kind"] == "reasoning" else "content"
            if message[facet]:
                continue  # exact native object + observed commit covers this earlier facet
        if not segment.get("message_uid") and not segment.get("tool_call_uid") and rows:
            # No source identity can prove whether this fallback duplicates a persisted facet.
            # Keep the native transcript authoritative rather than guess from text/provider id.
            outcome["outputs_complete"] = False
            continue
        if segment.get("tool_call_uid") in durable:
            continue  # the exact occurrence has a native result; History owns its full call/result
        outputs.append(segment)
    if outputs:
        outcome["outputs"] = outputs
    else:
        outcome.pop("outputs", None)


def persist_terminal_metadata(db, session_id, source, terminal, *, turn_lease_holder=None):
    from hermes_state_messages import _DISPLAY_ACTIVE_CLAUSE
    lineage = db._resume_lineage_ids(session_id)
    if source["session_id"] not in lineage:
        return None
    placeholders = ",".join("?" for _ in lineage)

    def write(conn):
        db._check_transcript_write_guards(conn, session_id, None, turn_lease_holder=turn_lease_holder,
                                         reject_active_turn_lease=True)
        proof = conn.execute("SELECT role, message_uid FROM messages WHERE id = ? AND session_id = ?",
                             (source["row_id"], source["session_id"])).fetchone()
        if proof is None or tuple(proof) != ("user", source["message_uid"]):
            return None
        rows = conn.execute(
            f"SELECT id, display_metadata FROM messages WHERE session_id IN ({placeholders}) "
            "AND role = 'user' AND message_uid = ?" + _DISPLAY_ACTIVE_CLAUSE,
            (*lineage, source["message_uid"])).fetchall()
        if not rows:
            return None
        for row in rows:
            previous = db._decode_display_metadata(row["display_metadata"]) or {}
            outcome = previous.get("turn_terminal")
            if isinstance(outcome, dict) and outcome.get("source_message_uid") == source["message_uid"]:
                return outcome  # first terminal fact wins; reentry never duplicates a message
        outcome = dict(terminal)
        durable = conn.execute(
            f"SELECT role, message_uid, tool_call_uid, content, reasoning FROM messages WHERE session_id IN ({placeholders}) "
            "AND id > ? AND role IN ('assistant', 'tool')" + _DISPLAY_ACTIVE_CLAUSE,
            (*lineage, source["row_id"])).fetchall()
        _reconcile_outputs(outcome, durable)
        final_uid = outcome.get("final_assistant_message_uid")
        if final_uid and conn.execute(
                f"SELECT 1 FROM messages WHERE session_id IN ({placeholders}) AND message_uid = ? "
                "AND role = 'assistant'" + _DISPLAY_ACTIVE_CLAUSE, (*lineage, final_uid)).fetchone() is None:
            outcome.pop("final_assistant_message_uid", None)
        for row in rows:
            metadata = db._decode_display_metadata(row["display_metadata"]) or {}
            metadata["turn_terminal"] = outcome
            conn.execute("UPDATE messages SET display_metadata = ? WHERE id = ?", (json.dumps(metadata), row["id"]))
        return outcome

    return db._execute_write(write, patience_s=0.0)
