"""Search is bounded per row; canonical precise Read returns the authentic complete body."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from agent.context_compressor import SUMMARY_PREFIX, _SUMMARY_END_MARKER
from tests.tools.test_session_history_identity import invoke
from tools.session_history_tool import SESSION_HISTORY_SCHEMA

pytest_plugins = ("tests.tools.test_session_history_identity",)


def test_history_schema_stays_frozen_without_full_body_option():
    spec = (Path(__file__).resolve().parents[2] / "docs/02-noting-system-specification.md").read_text()
    section = spec.split("#### 3.1 `session_history`", 1)[1].split("#### 3.2", 1)[0]
    frozen = json.loads(section.split("```json\n", 1)[1].split("\n```", 1)[0])
    assert SESSION_HISTORY_SCHEMA == frozen


@pytest.mark.parametrize("size", [799, 800, 801, 4000])
def test_search_budget_preserves_metadata_and_precise_read_returns_full_original(db, size):
    db.create_session("main", source="cli")
    content = "证据" + "中" * (size - 2)
    db.append_message("main", "user", content, message_uid="authentic-source", timestamp=123.25)
    found = invoke(db, {"mode": "search", "query": "证据"})
    assert found["success"] and found["count"] == 1
    row = found["messages"][0]
    assert found["conversation_ref"] == db.resolve_conversation_ref("main")
    assert (row["message_uid"], datetime.fromisoformat(row["timestamp"]).timestamp()) == ("authentic-source", 123.25)
    assert set(row) == {"message_uid", "timestamp", "role", "content"} | ({"truncated"} if size > 800 else set())
    if size > 800:
        assert len(row["content"]) == 800
        assert row["content"].endswith("[truncated]")
        assert row["truncated"] is True
    else:
        assert row["content"] == content
        assert not row.get("truncated", False)
    identity = {"conversation_ref": found["conversation_ref"], "message_uid": row["message_uid"]}
    read = invoke(db, {"mode": "read", "message_identity": identity, "before": 0, "after": 0})
    assert read["messages"][0]["content"] == content
    assert datetime.fromisoformat(read["messages"][0]["timestamp"]).timestamp() == 123.25
    assert read["messages"][0]["message_uid"] == "authentic-source"


def test_search_truncation_is_per_row_across_compaction_with_complete_read(db):
    db.create_session("main", source="cli")
    originals = [(f"source-{i}", f"evidence {i}: " + "x" * 1500, 100 + i) for i in range(20)]
    for uid, content, stamp in originals:
        db.append_message("main", "user", content, message_uid=uid, timestamp=stamp)
    db.archive_and_compact("main", [{"role": "user", "content": SUMMARY_PREFIX + "summary\n" + _SUMMARY_END_MARKER,
                                     "_compressed_summary": True, "message_uid": "boundary"}], tail_count=0)
    search = invoke(db, {"mode": "search", "query": "evidence"})
    assert search["count"] == 20
    assert sum(len(row["content"]) for row in search["messages"]) == 16000
    for row, (uid, body, stamp) in zip(search["messages"], originals):
        assert row["message_uid"] == uid and datetime.fromisoformat(row["timestamp"]).timestamp() == stamp
        assert row["truncated"] is True
        identity = {"conversation_ref": search["conversation_ref"], "message_uid": row["message_uid"]}
        full = invoke(db, {"mode": "read", "message_identity": identity, "before": 0, "after": 0})
        assert full["messages"][0]["content"] == body
    assert not invoke(db, {"mode": "search", "query": "evidence", "full_body": True})["success"]


@pytest.mark.parametrize("field", ["message_uid", "timestamp"])
def test_invalid_source_metadata_fails_closed_without_inventing_values(db, monkeypatch, field):
    db.create_session("main", source="cli")
    db.append_message("main", "user", "evidence", message_uid="original", timestamp=123)
    read = db.get_history_foreground_conn
    def damaged(conn, ref):
        rows = read(conn, ref)
        rows[0][field] = None
        return rows
    monkeypatch.setattr(db, "get_history_foreground_conn", damaged)
    result = invoke(db, {"mode": "search", "query": "evidence"})
    assert result["success"] is False
    assert "entry timestamp or canonical message_uid" in result["error"]
