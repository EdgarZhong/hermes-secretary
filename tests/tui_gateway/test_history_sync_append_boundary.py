"""Finite Thinking append recovery over formal REST/RPC and real SQLite writes."""
from __future__ import annotations

import pytest

from hermes_state import SessionDB
from tests.tui_gateway.test_history_sync import synced_request
from tests.tui_gateway.test_recovery_view import activate, begin_web
from tui_gateway import recovery_view

pytest_plugins = ["tests.tui_gateway.test_history_sync"]


def _thinking_rows(db):
    db.append_messages_batch("stored", [
        {"role": "assistant", "content": "first", "reasoning": "first thought"},
        {"role": "assistant", "content": "second", "reasoning": "second thought"},
    ])
    return [row for row in db.get_messages("stored") if row.get("reasoning")]


def _rewrite(writer, rows, index):
    writer._write_sql("UPDATE messages SET reasoning=? WHERE id=?", (f"rewrite-{index}", rows[-1]["id"]))


def _delete(writer, rows, _index):
    writer._write_sql("DELETE FROM messages WHERE id=?", (rows[-1]["id"],))


def _reorder(writer, rows, _index):
    first, last = rows[0]["id"], rows[-1]["id"]
    def swap(conn):
        positions = {row["id"]: row["display_order"] for row in conn.execute(
            "SELECT id,display_order FROM messages WHERE id IN (?,?)", (first, last))}
        for left, right in [(first, last), (last, first)]:
            conn.execute("UPDATE messages SET display_order=? WHERE id=?", (positions[right], left))
    writer._execute_write(swap)


def _source(writer, _rows, index):
    writer.append_message("stored", "user", f"new source-{index}")


def _representative(writer, _rows, index):
    replacement = writer.get_messages("stored")
    replacement[-1]["reasoning"] = f"replacement-{index}"
    writer.replace_messages("stored", replacement)


_MUTATIONS = {"rewrite": _rewrite, "delete": _delete, "reorder": _reorder,
              "source": _source, "representative": _representative}


@pytest.mark.parametrize("running", [False, True])
@pytest.mark.parametrize("padding", [0, 210])
def test_formal_sync_accepts_same_source_thinking_tail_once(native, rest, monkeypatch, running, padding):
    db, session, home = native
    rows = _thinking_rows(db)
    db.append_messages_batch("stored", [{"role": "assistant", "content": f"padding-{index}"} for index in range(padding)])
    if running:
        begin_web(db, session)
    req, page = synced_request(rest)
    req["details"] = [row["id"] for row in rows]
    original, calls = recovery_view.snapshot, []

    def capture(*args, **kwargs):
        state = original(*args, **kwargs)
        with SessionDB(db_path=home / "state.db") as writer:
            writer.append_messages_batch("stored", [{"role": "assistant", "content": "tail",
                                                      "reasoning": "tail thought"}])
        calls.append(True)
        return state

    monkeypatch.setattr(recovery_view, "snapshot", capture)
    result = activate(req)
    assert result["complete"], result
    assert len(calls) == 1
    assert result["running"] is running
    assert [row["reasoning"] for row in result["details"]] == ["first thought", "second thought"]
    bundle = result["windows"][0]["sync"]["latest_thinking"]
    assert bundle["source"] == page["sync"]["latest_thinking"]["source"]
    assert bundle["order"][:2] == [row["id"] for row in rows]
    assert bundle["rows"][-1]["reasoning"] == "tail thought"
    for row in rows:
        key = str(row["id"])
        assert bundle["revisions"][key] == page["sync"]["latest_thinking"]["revisions"][key]


@pytest.mark.parametrize("mutation", ["rewrite", "delete", "reorder", "source", "representative"])
@pytest.mark.parametrize("repeated", [False, True])
def test_formal_sync_rejects_old_thinking_changes_and_reproves(native, rest, monkeypatch, mutation, repeated):
    db, _session, home = native
    _thinking_rows(db)
    req, _page = synced_request(rest)
    original, calls, captures = recovery_view.snapshot, [], []

    def capture(*args, **kwargs):
        state = original(*args, **kwargs)
        captures.append(True)
        if not calls or repeated:
            with SessionDB(db_path=home / "state.db") as writer:
                rows = [row for row in writer.get_messages("stored") if row.get("reasoning")]
                _MUTATIONS[mutation](writer, rows, len(calls))
            calls.append(True)
        return state

    monkeypatch.setattr(recovery_view, "snapshot", capture)
    result = activate(req)
    assert len(captures) == 2
    assert len(calls) == (2 if repeated else 1)
    if repeated:
        assert not result["complete"] and result["reason"] == "view_changed", result
    else:
        assert result["complete"], result
        # A complete result requires a second D0/S/D1 proof after the destructive race.
        latest = result["windows"][0]["sync"]["latest_thinking"]
        expected = [row["id"] for row in db.get_messages("stored") if row.get("reasoning") and mutation != "source"]
        assert latest["order"] == (list(reversed(expected)) if mutation == "reorder" else expected)


def test_old_non_thinking_row_cannot_become_a_new_thinking_tail(native, rest, monkeypatch):
    db, _session, home = native
    db.append_messages_batch("stored", [{"role": "assistant", "content": f"old-{index}"} for index in range(220)])
    old = db.get_messages("stored")[1]
    req, _page = synced_request(rest)
    original, captures = recovery_view.snapshot, []

    def capture(*args, **kwargs):
        state = original(*args, **kwargs)
        with SessionDB(db_path=home / "state.db") as writer:
            if captures:
                writer._write_sql("UPDATE messages SET reasoning=? WHERE id=?", ("changed again", old["id"]))
            else:
                writer._write_sql("UPDATE messages SET reasoning=? WHERE id=?", ("new old reasoning", old["id"]))
        captures.append(True)
        return state

    monkeypatch.setattr(recovery_view, "snapshot", capture)
    result = activate(req)
    assert len(captures) == 2
    assert not result["complete"] and result["reason"] == "view_changed"
