"""Additive Secretary identity/path schema in the owning Hermes state.db."""

SECRETARY_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS secretary_conversations (
    conversation_ref TEXT PRIMARY KEY,
    created_at REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS secretary_conversation_aliases (
    alias_kind TEXT NOT NULL,
    alias_value TEXT NOT NULL,
    conversation_ref TEXT NOT NULL REFERENCES secretary_conversations(conversation_ref),
    created_at REAL NOT NULL,
    PRIMARY KEY(alias_kind, alias_value)
);
CREATE INDEX IF NOT EXISTS idx_secretary_alias_ref
    ON secretary_conversation_aliases(conversation_ref);
CREATE TABLE IF NOT EXISTS secretary_session_bindings (
    session_id TEXT PRIMARY KEY,
    conversation_ref TEXT NOT NULL REFERENCES secretary_conversations(conversation_ref),
    declared_source TEXT,
    declared_key TEXT,
    declared_generation INTEGER
);
CREATE INDEX IF NOT EXISTS idx_secretary_binding_ref
    ON secretary_session_bindings(conversation_ref);
CREATE TABLE IF NOT EXISTS secretary_branch_messages (
    conversation_ref TEXT NOT NULL REFERENCES secretary_conversations(conversation_ref),
    position INTEGER NOT NULL,
    message_id INTEGER NOT NULL,
    message_uid TEXT NOT NULL,
    is_compaction INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY(conversation_ref, position)
);
CREATE TABLE IF NOT EXISTS secretary_branch_freezes (
    conversation_ref TEXT PRIMARY KEY REFERENCES secretary_conversations(conversation_ref),
    parent_session_id TEXT NOT NULL,
    through_message_uid TEXT,
    created_at REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_secretary_branch_source ON secretary_branch_messages(message_id);
CREATE TABLE IF NOT EXISTS secretary_branch_exclusions (
    conversation_ref TEXT NOT NULL REFERENCES secretary_conversations(conversation_ref),
    message_uid TEXT NOT NULL,
    PRIMARY KEY(conversation_ref, message_uid)
);
"""

_MISSING_BRANCH_FREEZES_SQL = """
    SELECT DISTINCT b.conversation_ref, json_extract(s.model_config, '$._branched_from'), NULL, s.started_at
    FROM secretary_session_bindings b JOIN sessions s ON s.id=b.session_id
    WHERE json_valid(s.model_config) AND json_extract(s.model_config, '$._branched_from') IS NOT NULL
    AND (s.parent_session_id IS NULL OR json_extract(s.model_config, '$._branched_from')=s.parent_session_id)
    AND EXISTS(SELECT 1 FROM secretary_branch_messages m WHERE m.conversation_ref=b.conversation_ref)
    AND NOT EXISTS(SELECT 1 FROM secretary_branch_freezes f WHERE f.conversation_ref=b.conversation_ref)
"""


def init_secretary_schema(cursor):
    """Execute statement-by-statement, preserving the caller's transaction."""
    for statement in SECRETARY_SCHEMA_SQL.split(";"):
        if statement.strip():
            cursor.execute(statement)
    # A no-op INSERT still takes SQLite's write lock. Settled opens only probe.
    if cursor.execute(_MISSING_BRANCH_FREEZES_SQL + " LIMIT 1").fetchone() is not None:
        cursor.execute("INSERT OR IGNORE INTO secretary_branch_freezes " + _MISSING_BRANCH_FREEZES_SQL)
