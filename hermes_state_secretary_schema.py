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
"""


def init_secretary_schema(cursor):
    """Execute statement-by-statement, preserving the caller's transaction."""
    for statement in SECRETARY_SCHEMA_SQL.split(";"):
        if statement.strip():
            cursor.execute(statement)
