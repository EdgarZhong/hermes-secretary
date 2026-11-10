"""Shared display visibility and read-only projection for unindexed stores."""

from __future__ import annotations

from agent.context_compressor import MODEL_ONLY_DISPLAY_METADATA_KEY
from hermes_state_common import _placeholders, _sql_json_extract

# Unqualified fields bind to the innermost messages alias; recovery qualifies both fields.
DISPLAY_VISIBLE_SQL = (
    f" AND COALESCE({_sql_json_extract('display_metadata', '$.' + MODEL_ONLY_DISPLAY_METADATA_KEY)}, 0) = 0"
    f" AND NOT (COALESCE(role,'')='user' AND COALESCE({_sql_json_extract('display_metadata', '$._queued_prompt')},0)=1"
    " AND COALESCE(json_type(CASE WHEN json_valid(display_metadata) THEN display_metadata ELSE '{}' END,"
    " '$.web_input'),'')='object')")


def is_web_input_custody(role, metadata):
    """An accepted queued witness has custody, not a consumed native source identity."""
    return (role == "user" and isinstance(metadata, dict) and metadata.get("_queued_prompt") == 1
            and isinstance(metadata.get("web_input"), dict))


def is_display_excluded(role, metadata):
    """Python twin of DISPLAY_VISIBLE_SQL after metadata decoding."""
    return bool((metadata or {}).get(MODEL_ONLY_DISPLAY_METADATA_KEY)) or is_web_input_custody(role, metadata)


def without_web_input_custody(messages):
    """Keep old display projections' own handling of malformed/non-message inputs."""
    return (item for item in messages if not isinstance(item, dict)
            or not is_web_input_custody(item.get("role"), item.get("display_metadata")))


def display_filter_sql(display_only):
    return DISPLAY_VISIBLE_SQL if display_only else ""


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
