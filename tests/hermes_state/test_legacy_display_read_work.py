"""Read-only legacy display keeps full-history semantics with linear UID filtering."""

import json
import sqlite3
import time

import pytest

from agent.context_compressor import MODEL_ONLY_DISPLAY_METADATA_KEY
from hermes_state import SessionDB


def _invalidate_two(db, sid):
    db._execute_write(lambda conn: conn.execute(
        "UPDATE messages SET display_order = NULL, display_identity = NULL "
        "WHERE id IN (SELECT id FROM messages WHERE session_id = ? ORDER BY id LIMIT 2)", (sid,)))


def _mixed_generations(db, sid):
    db.create_session(sid, source="test")
    # Copies keep the original identity/timestamp; the newest UID generation alone
    # decides retirement, independently of which display representative wins.
    rows = [
        ("A", 1, 1, 0, "a", None),
        ("B", 2, 0, 1, "b", None),
        ("retired", 3, 0, 1, "retired", None),
        ("rewound", 4, 0, 0, "retired", None),
        ("C", 5, 1, 0, "c", None),
        ("A", 1, 0, 1, "a", None),
        ("B", 2, 0, 1, "b", None),
        ("A", 1, 1, 0, "a", None),
        ("hidden", 6, 1, 0, "hidden", json.dumps({MODEL_ONLY_DISPLAY_METADATA_KEY: True})),
        ("no uid", 7, 1, 0, None, None),
        ("empty uid", 8, 1, 0, "", None),
        ("revived", 9, 0, 0, "revived", None),
        ("revived", 9, 1, 0, "revived", None),
        ("model retired", 10, 0, 1, "model-retired", None),
        ("hidden retirement", 11, 0, 0, "model-retired", json.dumps({MODEL_ONLY_DISPLAY_METADATA_KEY: True})),
        ("model live", 12, 0, 1, "model-live", None),
        ("hidden live", 13, 1, 0, "model-live", json.dumps({MODEL_ONLY_DISPLAY_METADATA_KEY: True})),
    ]
    db._execute_write(lambda conn: conn.executemany(
        "INSERT INTO messages (session_id, role, content, timestamp, active, compacted, "
        "message_uid, display_metadata) VALUES (?, 'assistant', ?, ?, ?, ?, ?, ?)",
        [(sid, *row) for row in rows]))
    db._execute_write(lambda conn: conn.execute(
        "UPDATE messages SET message_uid = NULL WHERE session_id = ? AND content = 'no uid'", (sid,)))
    return db.get_messages(sid, include_inactive=True)


@pytest.mark.parametrize("latest", [False, True])
@pytest.mark.parametrize("limit,offset", [(None, 0), (2, 1), (0, 0), (2, 100), (-1, 0), (3, -1)])
@pytest.mark.parametrize("include_inactive", [False, True])
def test_partial_index_legacy_matches_indexed_paging(tmp_path, latest, limit, offset, include_inactive):
    path = tmp_path / "state.db"
    writer = SessionDB(path)
    raw = _mixed_generations(writer, "chat")
    # A foreign segment sharing UID must never retire this session's A.
    writer.create_session("foreign", source="test")
    writer._execute_write(lambda conn: conn.execute(
        "INSERT INTO messages (session_id, role, content, timestamp, active, compacted, message_uid) "
        "VALUES ('foreign', 'assistant', 'foreign retirement', 10, 0, 0, 'a')"))
    expected = writer.get_messages("chat", include_compacted=True, include_inactive=include_inactive)
    if not include_inactive:
        assert [m["content"] for m in expected] == ["A", "B", "C", "no uid", "empty uid", "revived", "model live"]
        assert expected[0]["id"] == raw[7]["id"]  # Newest active A stays first.
        assert expected[1]["id"] == raw[6]["id"]  # Newest compacted B wins.
    model_before = writer.get_messages("chat")
    _invalidate_two(writer, "chat")
    writer.close()
    before = path.read_bytes()
    reader = SessionDB(path, read_only=True)
    try:
        reader._conn.execute("PRAGMA query_only = ON")
        changes = reader._conn.total_changes
        all_rows = reader.get_messages("chat", include_compacted=True, include_inactive=include_inactive)
        page = reader.get_messages("chat", include_compacted=True, include_inactive=include_inactive,
                                   latest=latest, limit=limit, offset=offset)
        assert all_rows == expected
        assert page == (expected[::-1][offset:][:limit][::-1] if latest else expected[offset:][:limit])
        assert reader.get_messages("chat") == model_before
        assert reader._conn.total_changes == changes
        assert not reader._conn.in_transaction
    finally:
        reader.close()
    assert path.read_bytes() == before


def test_legacy_compaction_rewind_and_ancestor_projection(tmp_path):
    path = tmp_path / "lineage.db"
    writer = SessionDB(path)
    writer.create_session("parent", source="test")
    writer.append_message("parent", "user", "original")
    writer.append_message("parent", "assistant", "old answer")
    live = writer.get_messages_as_conversation("parent")
    writer.archive_and_compact("parent", [{"role": "user", "content": "summary"}, *live[-1:]], tail_count=1)
    writer.append_message("parent", "user", "rewind this")
    writer.append_message("parent", "assistant", "discard this")
    target = writer.get_messages("parent")[-2]["id"]
    writer.rewind_to_message("parent", target)
    writer.end_session("parent", "compression")
    writer.create_session("child", source="test", parent_session_id="parent")
    writer.append_message("child", "assistant", "continuation")
    expected = writer.get_messages("parent", include_compacted=True)
    ancestor = writer.get_messages("child", include_compacted=True, include_ancestors=True)
    model = writer.get_messages_as_conversation("child", include_ancestors=True)
    _invalidate_two(writer, "parent")
    writer.close()
    reader = SessionDB(path, read_only=True)
    try:
        assert reader.get_messages("parent", include_compacted=True) == expected
        assert reader.get_messages("child", include_compacted=True, include_ancestors=True) == ancestor
        assert reader.get_messages_as_conversation("child", include_ancestors=True) == model
        assert "discard this" not in [m["content"] for m in ancestor]
    finally:
        reader.close()


def test_legacy_profile_readers_do_not_share_uid_retirement(tmp_path):
    paths = [tmp_path / f"profile-{i}.db" for i in range(2)]
    for index, path in enumerate(paths):
        writer = SessionDB(path)
        writer.create_session("same-session", source="test")
        writer.append_message("same-session", "assistant", f"profile-{index}", message_uid="shared-uid")
        if index:
            writer._execute_write(lambda conn: conn.execute(
                "UPDATE messages SET active = 0, compacted = 0"))
            writer.append_message("same-session", "assistant", "sentinel")
        _invalidate_two(writer, "same-session")
        writer.close()
    readers = [SessionDB(path, read_only=True) for path in paths]
    try:
        for index in (0, 1, 0):
            rows = readers[index].get_messages("same-session", include_compacted=True, include_inactive=False)
            assert [row["content"] for row in rows] == (["sentinel"] if index else ["profile-0"])
    finally:
        for reader in readers:
            reader.close()


@pytest.mark.parametrize("has_uid", [False, True])
@pytest.mark.parametrize("has_index", [False, True])
def test_legacy_schema_without_display_columns(tmp_path, has_uid, has_index):
    path = tmp_path / "pre-display.db"
    with sqlite3.connect(path) as conn:
        conn.execute(
            "CREATE TABLE messages (id INTEGER PRIMARY KEY, session_id TEXT, role TEXT, content TEXT, "
            "timestamp REAL, tool_call_id TEXT, tool_calls TEXT, tool_name TEXT, active INTEGER, "
            "compacted INTEGER, display_kind TEXT, display_metadata TEXT"
            + (", message_uid TEXT" if has_uid else "") + ")")
        if has_index:
            conn.execute("CREATE INDEX idx_messages_session_id ON messages(session_id, id)")
        conn.executemany(
            "INSERT INTO messages (session_id, role, content, timestamp, active, compacted) "
            "VALUES ('chat', 'assistant', ?, ?, ?, ?)",
            [("old", 1, 0, 1), ("retirement", 2, 0, 0), ("visible", 3, 1, 0)])
        if has_uid:
            conn.execute("UPDATE messages SET message_uid = CASE WHEN id < 3 THEN 'retired' ELSE 'live' END")
    before = path.read_bytes()
    reader = SessionDB(path, read_only=True)
    try:
        reader._conn.execute("PRAGMA query_only = ON")
        rows = reader.get_messages("chat", include_compacted=True)
        assert [row["content"] for row in rows] == (["visible"] if has_uid else ["old", "visible"])
        assert reader._conn.total_changes == 0
    finally:
        reader.close()
    assert path.read_bytes() == before


def _measure_legacy_read(tmp_path, count):
    path = tmp_path / f"synthetic-{count}.db"
    writer = SessionDB(path)
    writer.create_session("synthetic", source="test")
    writer.append_messages_batch("synthetic", [
        {"role": "assistant", "content": f"synthetic row {index}", "timestamp": float(index)}
        for index in range(count)], chunk_rows=500)
    _invalidate_two(writer, "synthetic")
    writer.close()
    reader = SessionDB(path, read_only=True)
    callbacks = 0

    def progress():
        nonlocal callbacks
        callbacks += 1
        return 0

    reader._conn.set_progress_handler(progress, 100)
    started = time.perf_counter()
    try:
        page = reader.get_messages("synthetic", include_compacted=True, latest=True, limit=50)
        elapsed = time.perf_counter() - started
    finally:
        reader._conn.set_progress_handler(None, 0)
        reader.close()
    assert [row["content"] for row in page] == [f"synthetic row {i}" for i in range(count - 50, count)]
    return {"rows": count, "vm_steps_approx": callbacks * 100, "seconds": elapsed}


def test_legacy_generation_filter_sql_work_is_linear(tmp_path):
    small = _measure_legacy_read(tmp_path, 219)
    large = _measure_legacy_read(tmp_path, 2191)
    print(json.dumps({"small": small, "large": large}, sort_keys=True))
    # Ten times more source rows may cost linear work, never a per-row session
    # scan (which costs roughly one hundred times more VM instructions).
    assert large["vm_steps_approx"] < small["vm_steps_approx"] * 15
