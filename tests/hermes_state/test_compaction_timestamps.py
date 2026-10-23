"""Carried logical messages retain authoring time across native compaction commits."""
import copy

import pytest

from hermes_cli.web_history_cards import history_cards, read_detail_rows
from hermes_cli.web_routers.sessions import _project_for_display
from hermes_state import SessionDB
from tui_gateway.server import _history_to_messages


@pytest.fixture
def db(tmp_path):
    handle = SessionDB(tmp_path / "state.db")
    handle.create_session("parent", source="test")
    yield handle
    handle.close()


@pytest.mark.parametrize("mode", ["in_place", "covered", "rotation"])
def test_native_compaction_and_all_history_views_preserve_original_times(db, mode):
    rows = [
        {"role": "user", "content": "earlier", "timestamp": 1700000000.0},
        {"role": "user", "content": "<heartbeat>source event</heartbeat>", "timestamp": 1700000100.0},
        {"role": "assistant", "content": "HEARTBEAT_OVER", "timestamp": 1700000101.0, "reasoning": "first"},
        {"role": "user", "content": "<framework-message>update</framework-message>", "timestamp": 1700000200.0},
        {"role": "assistant", "content": "HEARTBEAT_OVER", "timestamp": 1700000201.0, "reasoning": "second"},
    ]
    db.append_messages_batch("parent", rows)
    # Runtime copies need not carry a row id or timestamp; UID still names the source occurrence.
    carried = [{key: value for key, value in row.items() if key not in {"timestamp", "_row_id"}}
               for row in rows[1:]]
    # Identical assistant bodies deliberately ride in the opposite order: content cannot choose time.
    carried[1], carried[3] = carried[3], carried[1]
    boundary = {"role": "user", "content": "[CONTEXT COMPACTION] earlier turns", "_compressed_summary": True}
    compacted = [boundary, *carried]
    if mode == "rotation":
        db.publish_compression_child(parent_session_id="parent", child_session_id="child", source="test",
                                     messages=compacted, require_compression_lease=False)
        sid = "child"
    else:
        kwargs = {"covered_ids": [row["_row_id"] for row in rows]} if mode == "covered" else {}
        db.archive_and_compact("parent", compacted, tail_count=4, **kwargs)
        sid = "parent"
    expected = {row["message_uid"]: row["timestamp"] for row in rows[1:]}
    assert {row["message_uid"]: row["timestamp"] for row in carried} == expected
    assert boundary["timestamp"] > max(expected.values())
    stored = db.get_messages(sid, include_compacted=True, include_ancestors=True)
    full = _project_for_display(stored)
    cards = history_cards(full)
    details = _project_for_display(read_detail_rows(db, sid, [row["id"] for row in full], include_compacted=True))
    resume = _history_to_messages(db.get_messages_as_conversation(sid, include_ancestors=True, include_row_ids=True))
    for projection in (stored, full, cards, details, resume):
        actual = {row["message_uid"]: row["timestamp"] for row in projection if row.get("message_uid") in expected}
        assert actual == expected


def test_explicit_time_is_kept_and_new_uid_does_not_borrow_identical_content_time(db):
    db.append_message("parent", "assistant", "same", timestamp=1700000000.0)
    carried = [{"role": "assistant", "content": "same", "message_uid": "new-occurrence"},
               {"role": "user", "content": "new control", "timestamp": 1700000300.0}]
    db.archive_and_compact("parent", carried)
    assert carried[0]["timestamp"] > 1700000000.0
    assert carried[1]["timestamp"] == 1700000300.0


def test_gateway_replay_keeps_original_assistant_and_tool_times_on_compaction(db):
    from gateway.run import _build_gateway_agent_history

    rows = [{"role": "user", "content": "question", "timestamp": 1700000000.0},
            {"role": "assistant", "content": "", "timestamp": 1700000100.0,
             "tool_calls": [{"id": "call", "type": "function", "function": {"name": "terminal", "arguments": "{}"}}]},
            {"role": "tool", "content": "done", "tool_call_id": "call", "timestamp": 1700000101.0},
            {"role": "assistant", "content": "answer", "timestamp": 1700000102.0}]
    db.append_messages_batch("parent", rows)
    replay, _ = _build_gateway_agent_history(db.get_messages("parent"))
    assert "timestamp" not in replay[-1]
    expected = {row["message_uid"]: row["timestamp"] for row in rows}
    db.archive_and_compact("parent", replay, tail_count=len(replay))
    assert {row["message_uid"]: row["timestamp"] for row in replay} == expected
    # New output after the boundary must keep advancing instead of inheriting a carried time.
    db.append_message("parent", "assistant", "later", timestamp=1700000300.0)
    assert db.get_messages("parent")[-1]["timestamp"] == 1700000300.0


def test_archive_failure_restores_caller_timestamps(db, monkeypatch):
    db.append_message("parent", "assistant", "answer", timestamp=1700000000.0)
    carried = db.get_messages_as_conversation("parent")
    carried[0].pop("timestamp")
    original = copy.deepcopy(carried)
    monkeypatch.setattr(db, "_insert_message_rows", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("write failed")))
    with pytest.raises(RuntimeError, match="write failed"):
        db.archive_and_compact("parent", carried)
    assert carried == original
    assert db.get_messages("parent")[0]["timestamp"] == 1700000000.0
