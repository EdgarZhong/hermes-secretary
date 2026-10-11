"""Internal immutable item rows; no Agent history or recovery surface."""

import json
from copy import deepcopy

from secretary.notebook_model import SECTIONS, section_for_type

ITEM_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS secretary_notebook_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_ref TEXT NOT NULL,
    lineage_id INTEGER NOT NULL,
    payload_json TEXT NOT NULL,
    archived INTEGER NOT NULL CHECK (archived IN (0, 1))
);
CREATE INDEX IF NOT EXISTS idx_secretary_item_lineage
    ON secretary_notebook_item(lineage_id);
CREATE TRIGGER IF NOT EXISTS secretary_item_insert_only_update
BEFORE UPDATE ON secretary_notebook_item BEGIN
    SELECT RAISE(ABORT, 'Notebook items are INSERT-only');
END;
CREATE TRIGGER IF NOT EXISTS secretary_item_insert_only_delete
BEFORE DELETE ON secretary_notebook_item BEGIN
    SELECT RAISE(ABORT, 'Notebook items are INSERT-only');
END;
"""


def init_item_schema(cursor):
    # Triggers contain semicolons, so execute complete statements explicitly.
    import sqlite3

    statement = ""
    for line in ITEM_SCHEMA_SQL.splitlines():
        statement += line + "\n"
        if sqlite3.complete_statement(statement):
            cursor.execute(statement)
            statement = ""


def item_row_conn(conn, item_id):
    if not isinstance(item_id, str) or not item_id.isascii() or not item_id.isdecimal() or int(item_id) < 1:
        raise ValueError(f"Unknown Notebook entry: {item_id}")
    row = conn.execute("SELECT * FROM secretary_notebook_item WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        raise ValueError(f"Unknown Notebook entry: {item_id}")
    return row


def _referenced_in_conversation(conn, conversation_ref, item_id):
    return any(item_id in json.loads(row[0]) for row in conn.execute(
        "SELECT payload_json FROM secretary_notebook_snapshots WHERE conversation_ref = ?",
        (conversation_ref,),
    ))


def require_item_owner(conn, row, conversation_ref):
    if row["conversation_ref"] != conversation_ref and not _referenced_in_conversation(
        conn, conversation_ref, str(row["id"])
    ):
        raise ValueError(f"Unknown Notebook entry: {row['id']}")


def item_entry(row, conversation_ref):
    entry = json.loads(row["payload_json"])
    entry["entry_id"] = str(row["id"])
    entry["archived"] = bool(row["archived"])
    # Branch shares immutable versions; only its hydrated provenance is rebound.
    if row["conversation_ref"] != conversation_ref:
        for source in entry.get("source_message_identities") or []:
            source["conversation_ref"] = conversation_ref
    return entry


def insert_item_conn(conn, conversation_ref, entry, previous_id=None):
    """Allocate the row/version handle and lineage together in one INSERT, never UPDATE."""
    predecessor = None if previous_id is None else item_row_conn(conn, previous_id)
    if predecessor is not None:
        require_item_owner(conn, predecessor, conversation_ref)
        if predecessor["archived"]:
            raise ValueError(f"Unknown Notebook entry: {previous_id}")
    sequence = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 'secretary_notebook_item'"
    ).fetchone()
    item_id = (sequence[0] if sequence else 0) + 1
    lineage = predecessor["lineage_id"] if predecessor is not None else item_id
    body = deepcopy(entry)
    body.pop("entry_id", None)
    archived = body.pop("archived")
    conn.execute(
        "INSERT INTO secretary_notebook_item (id, conversation_ref, lineage_id, payload_json, archived) "
        "VALUES (?, ?, ?, ?, ?)",
        (item_id, conversation_ref, lineage, json.dumps(body, ensure_ascii=False, sort_keys=True), int(archived)),
    )
    return str(item_id)


def hydrate_snapshot_conn(conn, conversation_ref, item_ids, *, include_archived=False):
    if not isinstance(item_ids, list) or len(set(item_ids)) != len(item_ids):
        raise ValueError("Snapshot requires ordered unique item ids")
    state = {section: [] for section in SECTIONS}
    for item_id in item_ids:
        row = item_row_conn(conn, item_id)
        entry = item_entry(row, conversation_ref)
        if include_archived or not entry["archived"]:
            state[section_for_type(entry["type"])].append(entry)
    return state


def snapshot_item_ids_conn(conn, conversation_ref, payload):
    """Only exact immutable versions owned/shared by this Conversation may be committed."""
    ids, lineages = [], set()
    for section in SECTIONS:
        for entry in payload[section]:
            row = item_row_conn(conn, entry["entry_id"])
            require_item_owner(conn, row, conversation_ref)
            if row["lineage_id"] in lineages:
                raise ValueError("A Snapshot may reference only one version per lineage")
            lineages.add(row["lineage_id"])
            if entry != item_entry(row, conversation_ref):
                raise ValueError(f"Notebook entry differs from immutable version: {entry['entry_id']}")
            ids.append(entry["entry_id"])
    return ids
