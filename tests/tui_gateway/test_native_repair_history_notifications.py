"""Formal same-count replay/CAS writes must wake the existing Gateway watcher."""
from __future__ import annotations

import pytest

from agent.message_metadata import DB_ROW_SNAPSHOT
from hermes_state import SessionDB
from hermes_state_history_notifications import notification_path
from tui_gateway import server

pytest_plugins = ["tests.tui_gateway.test_change_watcher"]


@pytest.fixture
def stores(watcher_home, monkeypatch):
    home, events = watcher_home
    monkeypatch.setattr(server, "_served_profile_homes", [])
    reader = SessionDB(db_path=home / "state.db")
    writer = SessionDB(db_path=home / "state.db")
    reader.create_session("stored", source="desktop")
    messages = [{"role": "user", "content": "question"}, {"role": "assistant", "content": "answer"}]
    assert reader.append_messages_batch("stored", messages) == 2
    server._broadcast_watched_changes(now=0)
    yield reader, writer, messages, events
    writer.close()
    reader.close()


@pytest.mark.parametrize("legacy", [False, True])
def test_same_count_native_repair_reaches_watcher_after_commit(stores, legacy):
    reader, writer, messages, events = stores
    if legacy:
        writer._write_sql("UPDATE messages SET content='' WHERE id=?", (messages[-1]["_row_id"],))
        messages[-1].pop(DB_ROW_SNAPSHOT)
    baseline = server._session_db_content_sig(reader.db_path)
    signal = notification_path(reader.db_path)
    initial_signal = signal.read_bytes() if signal.exists() else None
    before_content = reader.get_messages("stored")[-1]["content"]
    observed = []

    def before_commit(conn, _session_id, inserted):
        assert conn.in_transaction and not inserted
        assert (signal.read_bytes() if signal.exists() else None) == initial_signal
        assert reader.get_messages("stored")[-1]["content"] == before_content
        server._broadcast_watched_changes(now=5)
        assert events == []
        observed.append(True)

    messages[-1]["content"] = "repaired"
    assert writer.append_messages_batch("stored", messages, before_commit=before_commit) == 0
    assert observed == [True]
    assert reader.get_messages("stored")[-1]["content"] == "repaired"
    assert reader.get_session("stored")["message_count"] == 2
    assert server._session_db_content_sig(reader.db_path) == baseline
    server._broadcast_watched_changes(now=10)
    assert events == [("sessions.changed", {})]
    assert notification_path(reader.db_path).exists()


def _no_op(_writer, _messages):
    pass


def _stale_cas(writer, messages):
    writer._write_sql("UPDATE messages SET content='concurrent winner' WHERE id=?", (messages[-1]["_row_id"],))
    messages[-1]["content"] = "stale edit"


def _rollback(_writer, messages):
    messages[-1]["content"] = "must roll back"


def _legacy_no_op(writer, messages):
    writer._write_sql("UPDATE messages SET content='' WHERE id=?", (messages[-1]["_row_id"],))
    messages[-1].pop(DB_ROW_SNAPSHOT)
    messages[-1]["content"] = ""


def _rejected_update(writer, messages):
    writer._write_sql("CREATE TRIGGER reject_repair BEFORE UPDATE OF content ON messages "
                      "WHEN NEW.content='rejected' BEGIN SELECT RAISE(IGNORE); END")
    messages[-1]["content"] = "rejected"


@pytest.mark.parametrize("prepare", [_no_op, _stale_cas, _rollback, _legacy_no_op, _rejected_update])
def test_uncommitted_or_unchanged_repairs_do_not_notify(stores, prepare):
    reader, writer, messages, events = stores
    prepare(writer, messages)
    before = notification_path(reader.db_path)
    signature = before.read_bytes() if before.exists() else None

    def fail_commit(*_args):
        raise RuntimeError("controlled rollback after rewrite")

    if prepare is _rollback:
        with pytest.raises(RuntimeError, match="controlled rollback"):
            writer.append_messages_batch("stored", messages, before_commit=fail_commit)
        assert reader.get_messages("stored")[-1]["content"] == "answer"
    else:
        assert writer.append_messages_batch("stored", messages) == 0
    assert (before.read_bytes() if before.exists() else None) == signature
    server._broadcast_watched_changes(now=10)
    assert events == []
