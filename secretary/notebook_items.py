"""INSERT-only Notebook versions and item-bound provenance inheritance.

``lineage_id`` is the stable entry_id; ``id`` is the immutable version_id.
Snapshots hold ordered version IDs. No Agent can fetch arbitrary versions here.
"""

import json
from copy import deepcopy

from secretary.notebook_contract import (
    SECTIONS, canonical_notebook_entry, public_state, same_source_claim, section_for_type,
)

ITEM_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS secretary_notebook_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    conversation_ref TEXT NOT NULL,
    lineage_id INTEGER NOT NULL,
    source_basis_id INTEGER,
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
    import sqlite3

    statement = ""
    for line in ITEM_SCHEMA_SQL.splitlines():
        statement += line + "\n"
        if sqlite3.complete_statement(statement):
            cursor.execute(statement)
            statement = ""


def item_row_conn(conn, version_id):
    if (not isinstance(version_id, str) or not version_id.isascii()
            or not version_id.isdecimal() or int(version_id) < 1):
        raise ValueError("Unknown Notebook version")
    row = conn.execute("SELECT * FROM secretary_notebook_item WHERE id = ?", (version_id,)).fetchone()
    if row is None:
        raise ValueError("Unknown Notebook version")
    return row


def _referenced_in_conversation(conn, conversation_ref, version_id):
    return any(version_id in json.loads(row[0]) for row in conn.execute(
        "SELECT payload_json FROM secretary_notebook_snapshots WHERE conversation_ref = ?",
        (conversation_ref,),
    ))


def require_item_owner(conn, row, conversation_ref):
    if row["conversation_ref"] != conversation_ref and not _referenced_in_conversation(
        conn, conversation_ref, str(row["id"])
    ):
        raise ValueError("Notebook version is not owned or inherited by this Conversation")


def canonical_notebook_payload(payload):
    """Read old working payloads through the same retired-field projection.

    This changes no row. The Store's existing exact immutable-version and source
    gates still validate every projected body before publishing a Snapshot.
    New create/update input never goes through this compatibility function.
    """
    result = deepcopy(payload)
    if isinstance(result, dict):
        for section, entries in result.items():
            if isinstance(entries, list):
                result[section] = [canonical_notebook_entry(entry) for entry in entries]
    return result


def item_entry(row, conversation_ref):
    entry = canonical_notebook_entry(json.loads(row["payload_json"]))
    entry["entry_id"] = str(row["lineage_id"])
    entry["version_id"] = str(row["id"])
    entry["archived"] = bool(row["archived"])
    # Fork shares immutable rows; only the hydrated Message Identity is rebound.
    if row["conversation_ref"] != conversation_ref:
        for source in entry["source_message_identities"]:
            source["conversation_ref"] = conversation_ref
    return entry


def _archive_cleanup_claim(conn, conversation_ref, left, right):
    """Only confirmed archived targets license automatic relation removal."""
    if not same_source_claim(left, right, allow_relation_removal=True):
        return False
    removed = [relation for relation in left["relations"] if relation not in right["relations"]]
    for relation in removed:
        rows = conn.execute(
            "SELECT * FROM secretary_notebook_item WHERE lineage_id=? AND archived=1",
            (relation["entry_id"],),
        ).fetchall()
        if not rows:
            return False
        # Branches may legitimately share the archived immutable version.
        if not any(row["conversation_ref"] == conversation_ref or
                   _referenced_in_conversation(conn, conversation_ref, str(row["id"])) for row in rows):
            return False
    return True


def source_basis_conn(conn, conversation_ref, row, entry, *, allow_relation_removal=False):
    """Only this exact claim's committed version licenses off-path inheritance.

    Unchanged sources on unrelated new content do NOT inherit a historical
    permission. A new claim must pass the current-path validator instead.
    """
    require_item_owner(conn, row, conversation_ref)
    previous = item_entry(row, conversation_ref)
    if not same_source_claim(previous, entry) and not (
        allow_relation_removal and _archive_cleanup_claim(conn, conversation_ref, previous, entry)
    ):
        return None
    if _referenced_in_conversation(conn, conversation_ref, str(row["id"])):
        return row["id"]
    if row["source_basis_id"] is None:
        return None
    basis = item_row_conn(conn, str(row["source_basis_id"]))
    require_item_owner(conn, basis, conversation_ref)
    if (basis["lineage_id"] != row["lineage_id"]
            or not _referenced_in_conversation(conn, conversation_ref, str(basis["id"]))
            or not _archive_cleanup_claim(conn, conversation_ref, item_entry(basis, conversation_ref), entry)):
        raise ValueError("Invalid Notebook source inheritance basis")
    return basis["id"]


def insert_item_conn(conn, conversation_ref, entry, previous_id=None, *, source_basis_id=None,
                     allow_relation_removal=False):
    """Allocate stable lineage and version under the caller's write transaction.

    ``previous_id`` is a version_id, not an entry_id. Return the complete internal
    entry. The caller checks the candidate full state and revalidates its sources
    on this same connection before invoking this function.
    """
    predecessor = None if previous_id is None else item_row_conn(conn, previous_id)
    if predecessor is not None:
        require_item_owner(conn, predecessor, conversation_ref)
        old = item_entry(predecessor, conversation_ref)
        if predecessor["archived"]:
            raise ValueError("Archived Notebook versions cannot be edited")
        if (entry["entry_id"] != old["entry_id"] or entry["entry_type"] != old["entry_type"]
                or entry["created_at"] != old["created_at"]):
            raise ValueError("Entry identity, type and first-created time are immutable")
    if source_basis_id is not None and (predecessor is None or source_basis_id != source_basis_conn(
        conn, conversation_ref, predecessor, entry, allow_relation_removal=allow_relation_removal
    )):
        raise ValueError("Invalid Notebook source inheritance basis")
    sequence = conn.execute(
        "SELECT seq FROM sqlite_sequence WHERE name = 'secretary_notebook_item'"
    ).fetchone()
    version = (sequence[0] if sequence else 0) + 1
    lineage = predecessor["lineage_id"] if predecessor is not None else version
    body = deepcopy(entry)
    body.pop("entry_id")
    body.pop("version_id")
    archived = body.pop("archived")
    conn.execute(
        "INSERT INTO secretary_notebook_item "
        "(id, conversation_ref, lineage_id, source_basis_id, payload_json, archived) VALUES (?, ?, ?, ?, ?, ?)",
        (version, conversation_ref, lineage, source_basis_id,
         json.dumps(body, ensure_ascii=False, sort_keys=True), int(archived)),
    )
    return item_entry(item_row_conn(conn, str(version)), conversation_ref)


def hydrate_snapshot_conn(conn, conversation_ref, item_ids, *, include_archived=False):
    if not isinstance(item_ids, list) or any(not isinstance(item, str) for item in item_ids):
        raise ValueError("Snapshot requires ordered unique version IDs")
    if len(set(item_ids)) != len(item_ids):
        raise ValueError("Snapshot repeats an immutable version")
    state = {section: [] for section in SECTIONS}
    lineages = set()
    for version_id in item_ids:
        row = item_row_conn(conn, version_id)
        require_item_owner(conn, row, conversation_ref)
        if row["lineage_id"] in lineages:
            raise ValueError("A Snapshot may reference only one version per entry")
        lineages.add(row["lineage_id"])
        entry = item_entry(row, conversation_ref)
        state[section_for_type(entry["entry_type"])].append(entry)
    return state if include_archived else public_state(state)


def snapshot_item_ids_conn(conn, conversation_ref, payload):
    """Accept exact owned/shared immutable versions, not caller-reconstructed bodies."""
    ids, lineages = [], set()
    for section in SECTIONS:
        for entry in payload[section]:
            entry = canonical_notebook_entry(entry)
            row = item_row_conn(conn, entry["version_id"])
            require_item_owner(conn, row, conversation_ref)
            if row["lineage_id"] in lineages:
                raise ValueError("A Snapshot may reference only one version per entry")
            lineages.add(row["lineage_id"])
            if entry != item_entry(row, conversation_ref) or section_for_type(entry["entry_type"]) != section:
                raise ValueError("Notebook entry differs from its immutable version")
            ids.append(entry["version_id"])
    return ids
