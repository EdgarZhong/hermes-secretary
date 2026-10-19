"""Read-only display projection for stores without complete display identities."""

from __future__ import annotations

from hermes_state_common import _placeholders


def _retired_uids(conn, session_id: str, index_hint: str) -> set:
    """Fold all UID generations once, including rewind-only and model-only rows.

    A per-candidate newest-generation subquery becomes quadratic without a UID
    index. This narrow scan retains only retired UIDs, never transcript payloads.
    """
    retired = set()
    rows = conn.execute(
        f"SELECT message_uid, active, compacted FROM messages {index_hint} "
        "WHERE session_id = ? AND NULLIF(message_uid, '') IS NOT NULL ORDER BY id ASC",
        (session_id,))
    for row in rows:
        if row["active"] == 1 or row["compacted"] == 1:
            retired.discard(row["message_uid"])
        else:
            retired.add(row["message_uid"])
    rows.close()
    return retired


def legacy_display_page(db, session_id: str, *, active_clause: str, limit: int | None,
                        offset: int, latest: bool) -> list:
    """Dedupe the full snapshot before paging; retain only identities and row ids."""
    representatives = {}
    with db._read_ctx() as conn:
        conn.execute("BEGIN")
        try:
            has_session_index = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = ?",
                ("idx_messages_session_id",),
            ).fetchone() is not None
            index_hint = "INDEXED BY idx_messages_session_id" if has_session_index else "NOT INDEXED"
            has_uid = "message_uid" in db._message_column_names(conn)
            retired = _retired_uids(conn, session_id, index_hint) if active_clause and has_uid else set()
            uid_column = "message_uid" if has_uid else "NULL AS message_uid"
            rows = conn.execute(
                "SELECT id, role, content, timestamp, tool_call_id, tool_calls, tool_name, active, "
                f"display_kind, display_metadata, {uid_column} FROM messages {index_hint} "
                f"WHERE session_id = ?{active_clause} ORDER BY id ASC", (session_id,))
            for row in rows:
                if row["message_uid"] in retired or db._is_model_only_row(row):
                    continue
                identity = db._display_identity(db._display_dedupe_key(row))
                current = representatives.get(identity)
                candidate = (row["active"], row["id"])
                if current is None or candidate > current:
                    representatives[identity] = candidate
            rows.close()

            identities = list(representatives)
            identities = identities[::-1][offset:][:limit][::-1] if latest else identities[offset:][:limit]
            selected_ids = [representatives[identity][1] for identity in identities]
            selected = {}
            for start in range(0, len(selected_ids), 900):
                chunk = selected_ids[start:start + 900]
                selected.update({row["id"]: row for row in conn.execute(
                    f"SELECT * FROM messages WHERE session_id = ?{active_clause} "
                    f"AND id IN ({_placeholders(chunk)})", (session_id, *chunk))})
            return [selected[row_id] for row_id in selected_ids if row_id in selected]
        finally:
            if conn.in_transaction:
                conn.execute("ROLLBACK")
