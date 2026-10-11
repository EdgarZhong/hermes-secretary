"""Conversation-local Noting scratch pad; mutations never admit a background task."""

import json
import time

MEMO_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS secretary_noting_memo (
    memo_id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_ref TEXT NOT NULL,
    memo_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at REAL NOT NULL,
    UNIQUE (conversation_ref, memo_index)
);
CREATE TRIGGER IF NOT EXISTS secretary_memo_immutable_content
BEFORE UPDATE OF memo_id, conversation_ref, content, created_at ON secretary_noting_memo
BEGIN
    SELECT RAISE(ABORT, 'Memo content identities are immutable');
END;
CREATE TABLE IF NOT EXISTS secretary_noting_memo_archive (
    archive_id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_ref TEXT NOT NULL,
    anchor_message_uid TEXT NOT NULL,
    snapshot_id TEXT NOT NULL,
    entries_json TEXT NOT NULL,
    entry_count INTEGER NOT NULL,
    trigger_type TEXT NOT NULL,
    runtime_profile TEXT NOT NULL,
    archived_at REAL NOT NULL
);
"""


def init_memo_schema(cursor):
    # Trigger contains an internal semicolon; use native complete_statement parsing.
    import sqlite3
    statement = ""
    for line in MEMO_SCHEMA_SQL.splitlines(keepends=True):
        statement += line
        if sqlite3.complete_statement(statement):
            cursor.execute(statement)
            statement = ""


def memo_entries_conn(conn, conversation_ref):
    return [dict(row) for row in conn.execute(
        "SELECT memo_id, memo_index AS 'index', content, created_at FROM secretary_noting_memo "
        "WHERE conversation_ref = ? ORDER BY memo_index", (conversation_ref,))]


def render_memo(entries):
    return "\n".join(f"{entry['index']}. {entry['content']}" for entry in entries) if entries else "No memo after last noting"


def mutate_memo_conn(db, conn, conversation_ref, args):
    """Validate and atomically mutate the owning memo and its participation preference."""
    db._notebook_require_conversation_conn(conn, conversation_ref)
    operation = args.get("operation")
    allowed = {"add": {"operation", "content"}, "replace": {"operation", "index", "content"},
               "delete": {"operation", "index"}, "list": {"operation"}}
    if operation not in allowed or set(args) != allowed[operation]:
        raise ValueError("Invalid Noting Memo operation or arguments")
    entries = memo_entries_conn(conn, conversation_ref)
    if operation == "list":
        return render_memo(entries)
    if operation in {"add", "replace"} and not isinstance(args["content"], str):
        raise ValueError("Memo content must be a string")
    if operation == "add":
        index = len(entries) + 1
        auto_enabled = not db.notebook_local_enabled_conn(conn, conversation_ref)
        conn.execute("INSERT INTO secretary_noting_memo (conversation_ref, memo_index, content, created_at) VALUES (?, ?, ?, ?)",
                     (conversation_ref, index, args["content"], time.time()))
        db.notebook_set_local_enabled_conn(conn, conversation_ref, True)
        result = f"created: {args['content']}, index={index}"
        return result + ("\nBackground Noting was automatically enabled for this Conversation." if auto_enabled else "")
    index = args["index"]
    if isinstance(index, bool) or not isinstance(index, int) or not 1 <= index <= len(entries):
        raise ValueError("Unknown Noting Memo index")
    previous = entries[index - 1]["content"]
    conn.execute("DELETE FROM secretary_noting_memo WHERE memo_id = ?", (entries[index - 1]["memo_id"],))
    if operation == "replace":
        conn.execute("INSERT INTO secretary_noting_memo (conversation_ref, memo_index, content, created_at) VALUES (?, ?, ?, ?)",
                     (conversation_ref, index, args["content"], time.time()))
    else:
        reindex_memo_conn(conn, conversation_ref)
    return f"{'replaced' if operation == 'replace' else 'deleted'}: {previous}\n" + render_memo(memo_entries_conn(conn, conversation_ref))


def reindex_memo_conn(conn, conversation_ref):
    """Only indices change: surviving immutable content identities stay stable."""
    entries = memo_entries_conn(conn, conversation_ref)
    conn.execute("UPDATE secretary_noting_memo SET memo_index = -memo_index WHERE conversation_ref = ?",
                 (conversation_ref,))
    conn.executemany("UPDATE secretary_noting_memo SET memo_index = ? WHERE memo_id = ?",
                     [(index, entry["memo_id"]) for index, entry in enumerate(entries, 1)])


def consume_memo_conn(conn, conversation_ref, frozen_entries, *, snapshot_id, anchor_message_uid,
                      trigger_type, runtime_profile, archived_at):
    """Consume only still-active identities seen by this task, in the Snapshot transaction."""
    active_ids = {entry["memo_id"] for entry in memo_entries_conn(conn, conversation_ref)}
    consumed = [entry for entry in frozen_entries if entry["memo_id"] in active_ids]
    if not consumed:
        return
    audit_entries = [{key: entry[key] for key in ("index", "content", "created_at")} for entry in consumed]
    conn.execute("INSERT INTO secretary_noting_memo_archive "
                 "(conversation_ref, anchor_message_uid, snapshot_id, entries_json, entry_count, trigger_type, runtime_profile, archived_at) "
                 "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                 (conversation_ref, anchor_message_uid, snapshot_id, json.dumps(audit_entries, ensure_ascii=False),
                  len(consumed), trigger_type, runtime_profile, archived_at))
    conn.executemany("DELETE FROM secretary_noting_memo WHERE conversation_ref = ? AND memo_id = ?",
                     [(conversation_ref, entry["memo_id"]) for entry in consumed])
    reindex_memo_conn(conn, conversation_ref)
