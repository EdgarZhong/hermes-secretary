"""C8 real Snapshot/transcript transactions, queue validity and complete result bodies."""

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import Event, RLock
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from hermes_state import SessionDB
from hermes_cli.cli_secretary_commands import PERSISTENCE_PROPOSAL_INSTRUCTION
from secretary.framework_messages import (
    flush_framework_messages,
    mark_framework_turn,
    publish_external_execution_notice,
    publish_noting_completion,
    publish_noting_failure,
)
from secretary.notebook_render import render_notebook
from secretary.notebook_store import NotebookStore

FINISH = {"type": "finish_noting", "reason": "Checked all Noting responsibilities"}


@pytest.fixture
def runtime(tmp_path):
    db = SessionDB(tmp_path / "state.db")
    db.create_session("main", source="test")
    db.append_message("main", "user", "Discuss the visit", message_uid="m1", timestamp=100)
    db.append_message("main", "assistant", "Dates are open", message_uid="m2", timestamp=200)
    parent = SimpleNamespace(
        _session_db=db, session_id="main", _secretary_conversation_ref=db.resolve_conversation_ref("main"),
        _session_messages=db.get_messages_as_conversation("main"), _session_persist_lock=RLock(),
        _secretary_main_turn_running=False, platform="cli", side_agent=False, _persist_disabled=False,
        run_conversation=Mock(side_effect=AssertionError("A Framework must never start a Turn")),
    )
    parent.displays = []
    parent._print_fn = parent.displays.append
    yield parent, db
    db.close()


def book(parent, *, anchor="m2"):
    return NotebookStore(parent._session_db, parent._secretary_conversation_ref, anchor_message_uid=anchor)


def create(store, description="Plan the visit"):
    return store.create("matter", {"description": description, "completion_condition": "Dates agreed"},
                        source_message_identities=[{"conversation_ref": store.conversation_ref, "message_uid": "m1"}])["entry"]


def commit(store, termination=None):
    return store.commit(termination=FINISH if termination is None else termination)


def publish(parent, result, *, termination=None, summary="Updated the accepted responsibility"):
    return publish_noting_completion(parent, result, termination=FINISH if termination is None else termination,
                                     summary=summary)


def notices(db):
    return [row for row in db.get_messages("main") if (row.get("display_metadata") or {}).get("noting_run_output")]


def config(parent, char_threshold, entry_threshold):
    Path(parent._session_db.db_path).with_name("config.yaml").write_text(
        "noting:\n  enabled: true\n  persistence_proposal:\n"
        f"    char_threshold: {char_threshold}\n    entry_threshold: {entry_threshold}\n")


def test_single_carrier_contains_complete_snapshot_and_native_identity(runtime):
    parent, db = runtime
    state = book(parent)
    entry = create(state, "为家人确定探访日期 🌄")
    result = commit(state)
    snapshot = db.notebook_current(parent._secretary_conversation_ref)
    assert publish(parent, result)
    rows = notices(db)
    assert len(rows) == len(parent.displays) == 1
    row = rows[0]
    body = row["display_metadata"]["display_text"]
    assert body.startswith("NOTING RESULT\nConversation: " + state.conversation_ref)
    assert render_notebook(snapshot, profile_home=Path(db.db_path).parent, db=db, model_visible=True) in body
    assert '"history_message_count": 2' in body
    assert '"through_time": "1970-01-01T00:03:20+00:00"' in body
    assert entry["entry_id"] in body and entry["version_id"] in body
    assert "为家人确定探访日期 🌄" in body
    assert "Snapshot:" not in body and "Coverage anchor:" not in body
    assert result["snapshot_id"] not in body and "Termination: finish_noting" in body
    assert row["display_metadata"]["noting_snapshot_id"] == result["snapshot_id"]
    assert row["content"] == "<framework-message>\n" + body + "\n</framework-message>"
    assert "<timestamp>" not in row["content"]
    assert row["timestamp"] == result["committed_at"]
    assert parent._session_messages[-1]["message_uid"] == row["message_uid"]
    assert parent._session_messages[-1]["content"] == row["content"]
    parent.run_conversation.assert_not_called()


def test_newer_coverage_finishes_first_late_snapshot_is_successful_without_notice(runtime):
    parent, db = runtime
    older, newer = book(parent, anchor="m1"), book(parent, anchor="m2")
    create(older, "Old coverage")
    create(newer, "Current coverage")
    new_result = commit(newer)
    old_result = commit(older)
    assert old_result["pointer_changed"] is False
    assert db.notebook_snapshot_audit(old_result["snapshot_id"])
    assert publish(parent, old_result) is False
    assert not notices(db)
    assert publish(parent, new_result)
    assert len(notices(db)) == 1
    assert "Current coverage" in notices(db)[0]["content"]
    assert "Old coverage" not in notices(db)[0]["content"]


def test_carried_old_uid_cannot_suppress_new_human_anchor_completion(runtime):
    parent, db = runtime
    original = book(parent)
    entry = create(original, "Original outcome")
    commit(original)
    db.append_message("main", "assistant", "Notebook read-only feedback", message_uid="human",
                      display_metadata={"human_only": True}, timestamp=300)
    current, late = book(parent, anchor="human"), book(parent)
    visible = [row for row in db.get_messages_as_conversation("main")
               if not (row.get("display_metadata") or {}).get("human_only")]
    db.archive_and_compact("main", [{"role": "assistant", "content": "Compaction summary",
                                     "message_uid": "summary", "_compressed_summary": True}, *visible])
    parent._session_messages = db.get_messages_as_conversation("main")
    current.update(entry["entry_id"], {"fields": {"description": "Current accepted outcome"}})
    result = commit(current)
    assert publish(parent, result)
    late.update(entry["entry_id"], {"fields": {"description": "Older task outcome"}})
    late_result = commit(late)
    assert not late_result["pointer_changed"] and not publish(parent, late_result)
    rows = notices(db)
    assert [row["display_metadata"]["noting_snapshot_id"] for row in rows] == [result["snapshot_id"]]
    snapshot = db.notebook_current(current.conversation_ref)
    assert render_notebook(snapshot, profile_home=Path(db.db_path).parent, db=db, model_visible=True) in rows[0]["content"]
    assert '"history_message_count": 3' in rows[0]["content"]
    assert '"through_time": "1970-01-01T00:05:00+00:00"' in rows[0]["content"]
    assert "Current accepted outcome" in rows[0]["content"]
    assert "Older task outcome" not in rows[0]["content"]
    parent.run_conversation.assert_not_called()


def test_queued_old_snapshot_and_its_proposal_are_dropped_entirely(runtime):
    parent, db = runtime
    config(parent, 1, 1)
    mark_framework_turn(parent, running=True)
    first = book(parent, anchor="m1")
    create(first, "Superseded draft")
    a = commit(first)
    assert publish(parent, a)
    second = book(parent, anchor="m2")
    second.update(second.show()["work"][0]["entry_id"], {"fields": {"description": "Effective new result"}})
    b = commit(second)
    assert publish(parent, b)
    assert not notices(db) and not parent.displays
    assert parent._secretary_framework_messages[0].snapshot_id == a["snapshot_id"]
    mark_framework_turn(parent, running=False)
    rows = notices(db)
    assert len(rows) == len(parent.displays) == 1
    assert rows[0]["display_metadata"]["noting_snapshot_id"] == b["snapshot_id"]
    assert b["snapshot_id"] not in rows[0]["content"]
    assert a["snapshot_id"] not in rows[0]["content"]
    assert "Superseded draft" not in rows[0]["content"]
    assert rows[0]["content"].count("PERSISTENCE PROPOSAL REQUEST") == 1
    assert not parent._secretary_framework_messages


def test_already_appended_then_newer_result_forms_normal_two_step_history(runtime):
    parent, db = runtime
    a = book(parent, anchor="m1")
    create(a, "Earlier current result")
    ar = commit(a)
    publish(parent, ar)
    b = book(parent)
    b.update(b.show()["work"][0]["entry_id"], {"fields": {"description": "Later current result"}})
    br = commit(b)
    publish(parent, br)
    assert [r["display_metadata"]["noting_snapshot_id"] for r in notices(db)] == [ar["snapshot_id"], br["snapshot_id"]]
    assert len(parent.displays) == 2


def test_pointer_check_and_live_append_are_ordered_with_competing_snapshot_commit(runtime, monkeypatch):
    parent, db = runtime
    first, second = book(parent, anchor="m1"), book(parent)
    create(first, "Original coverage")
    create(second, "Newer coverage")
    a = commit(first)
    checked, contender, release, writer_done = Event(), Event(), Event(), Event()
    original = db.notebook_snapshot_if_current_conn
    native_append = db.append_messages_batch
    observed, observed_live = [], []
    def inspect(conn, conversation_ref, snapshot_id):
        result = original(conn, conversation_ref, snapshot_id)
        if not checked.is_set():
            checked.set()
            assert contender.wait(2)
            assert release.wait(2)
        return result
    monkeypatch.setattr(db, "notebook_snapshot_if_current_conn", inspect)
    def append_then_wait(*args, **kwargs):
        result = native_append(*args, **kwargs)
        # Hold the publisher immediately after native COMMIT, before its outer
        # post-commit code. The competing Snapshot must already observe live A.
        assert writer_done.wait(2)
        return result
    monkeypatch.setattr(db, "append_messages_batch", append_then_wait)
    def commit_second():
        assert checked.wait(2)
        contender.set()
        value = commit(second)
        observed.extend(row["display_metadata"]["noting_snapshot_id"] for row in notices(db))
        observed_live.extend(row["display_metadata"]["noting_snapshot_id"]
                             for row in parent._session_messages
                             if (row.get("display_metadata") or {}).get("noting_run_output"))
        writer_done.set()
        return value
    with ThreadPoolExecutor(max_workers=2) as pool:
        publisher = pool.submit(publish, parent, a)
        writer = pool.submit(commit_second)
        assert contender.wait(2)
        assert not writer.done()  # native write lock prevents pointer replacement mid-append
        release.set()
        assert publisher.result(timeout=3)
        b = writer.result(timeout=3)
    assert observed == observed_live == [a["snapshot_id"]]
    assert db.notebook_current(parent._secretary_conversation_ref)["snapshot_id"] == b["snapshot_id"]
    assert parent._session_messages[-1]["display_metadata"]["noting_snapshot_id"] == a["snapshot_id"]


def test_owner_change_during_native_transaction_rolls_back_and_never_publishes_live(runtime, monkeypatch):
    parent, db = runtime
    state = book(parent)
    result = commit(state)
    append = db.append_messages_batch
    def change_owner(*args, **kwargs):
        prepare = kwargs["prepare_rows"]
        def swap(conn, sid, rows):
            prepare(conn, sid, rows)
            parent._secretary_conversation_ref = "different-owner"
        kwargs["prepare_rows"] = swap
        return append(*args, **kwargs)
    monkeypatch.setattr(db, "append_messages_batch", change_owner)
    publish(parent, result)
    assert not notices(db) and not parent.displays
    assert len(parent._session_messages) == 2
    assert flush_framework_messages(parent) == 0


def test_append_failure_keeps_committed_snapshot_and_drops_notice_at_most_once(runtime, monkeypatch):
    parent, db = runtime
    state = book(parent)
    result = commit(state)
    monkeypatch.setattr(db, "append_messages_batch", Mock(side_effect=RuntimeError("native append failed")))
    assert publish(parent, result)
    assert db.notebook_current(parent._secretary_conversation_ref)["snapshot_id"] == result["snapshot_id"]
    assert not notices(db) and len(parent._session_messages) == 2
    assert flush_framework_messages(parent) == 0
    assert db.append_messages_batch.call_count == 1


def test_coverage_display_failure_does_not_block_the_formal_completion(runtime, monkeypatch):
    parent, db = runtime
    state = book(parent)
    create(state)
    result = commit(state)
    def unavailable(*_args):
        raise RuntimeError("History display temporarily unavailable")
    monkeypatch.setattr("secretary.notebook_render._evidence_coverage_conn", unavailable)
    assert publish(parent, result)
    rows = notices(db)
    assert len(rows) == 1
    assert '"status": "unavailable"' in rows[0]["content"]
    assert "Plan the visit" in rows[0]["content"]
    assert rows[0]["display_metadata"]["noting_snapshot_id"] == result["snapshot_id"]


@pytest.mark.parametrize("difference", [0, 1])
def test_unicode_character_threshold_is_strict_and_excludes_framework_wrapper(runtime, difference):
    parent, db = runtime
    state = book(parent)
    create(state, "日期未定 🌄" * 20)
    result = commit(state)
    snapshot = db.notebook_current(parent._secretary_conversation_ref)
    rendered = render_notebook(snapshot, profile_home=Path(db.db_path).parent, db=db, model_visible=True)
    config(parent, len(rendered) - difference, 1000)
    publish(parent, result)
    text = notices(db)[0]["content"]
    assert ("PERSISTENCE PROPOSAL REQUEST" in text) is bool(difference)
    assert rendered in text
    if difference:
        assert f"contains {len(rendered)} characters and 1 current entries" in text
        assert PERSISTENCE_PROPOSAL_INSTRUCTION in text


@pytest.mark.parametrize("count", [60, 61])
def test_entry_threshold_is_strict_and_candidate_references_do_not_duplicate_entries(runtime, count):
    parent, db = runtime
    config(parent, 1_000_000, 60)
    state = book(parent)
    entries = [create(state, f"Accepted responsibility {i}") for i in range(count - 1)]
    state.create("candidate", {"description": "Retain the work outcomes", "targets": ["memory"],
                              "notebook_refs": [e["entry_id"] for e in entries], "source_types": ["matter"]})
    result = commit(state)
    publish(parent, result)
    text = notices(db)[0]["content"]
    assert ("PERSISTENCE PROPOSAL REQUEST" in text) is (count > 60)
    if count > 60:
        assert "and 61 current entries" in text
    assert "candidate_refs" in text


@pytest.mark.parametrize("kind", ["forced", "context_overflow"])
def test_legal_fallback_commit_is_success_message_with_limits_and_no_failed_snapshot_claim(runtime, kind):
    parent, db = runtime
    state = book(parent)
    create(state)
    termination = {"type": kind}
    result = commit(state, termination)
    publish(parent, result, termination=termination, summary="Retained current legal work")
    text = notices(db)[0]["content"]
    assert f"Termination: {kind}" in text and "may remain unfinished" in text
    assert "CURRENT NOTEBOOK SNAPSHOT" in text
    assert "No new Snapshot" not in text
    assert "termination" not in db.notebook_current(state.conversation_ref)["payload"]


def test_failure_message_never_attaches_a_snapshot_or_proposal(runtime):
    parent, db = runtime
    assert publish_noting_failure(parent, conversation_ref=parent._secretary_conversation_ref,
                                 specific_reason="The frozen Anchor left the current path")
    text = notices(db)[0]["content"]
    assert "No new Snapshot was committed by this task: The frozen Anchor left the current path." in text
    assert "CURRENT NOTEBOOK SNAPSHOT" not in text and "PERSISTENCE PROPOSAL" not in text
    assert db.notebook_current(parent._secretary_conversation_ref) is None
    assert not publish_noting_failure(parent, conversation_ref="other", specific_reason="Wrong owner")


def test_noting_and_external_framework_do_not_depend_on_scheduler_injection_lane(runtime):
    parent, db = runtime
    Path(db.db_path).with_name("config.yaml").write_text("scheduler:\n  enabled: false\n")
    parent._secretary_reminder_injection_disabled = True
    state = book(parent)
    result = commit(state)
    assert publish(parent, result)
    parent._secretary_last_main_execution = "external"
    assert publish_external_execution_notice(parent, expected_conversation_ref=state.conversation_ref)
    assert len(parent.displays) == 2


def test_pointer_reselection_without_task_completion_does_not_create_message(runtime):
    parent, db = runtime
    first = book(parent, anchor="m1")
    ar = commit(first)
    db.append_message("main", "user", "New direction", message_uid="m3", timestamp=300)
    second = book(parent, anchor="m3")
    br = commit(second)
    assert br["pointer_changed"]
    target = db._read_one("SELECT id FROM messages WHERE session_id='main' AND message_uid='m3'")[0]
    db.rewind_to_message("main", target)
    db.notebook_reselect_pointer(first.conversation_ref)
    assert db.notebook_current(first.conversation_ref)["snapshot_id"] == ar["snapshot_id"]
    assert not notices(db) and not parent.displays


def test_fence_waiter_drops_superseded_completion_after_fence_clears(runtime):
    parent, db = runtime
    parent._active_compression_commit_fence = Event()
    displayed = Event()
    parent._print_fn = lambda text: (parent.displays.append(text), displayed.set())
    first = book(parent, anchor="m1")
    create(first, "Before compaction fence")
    ar = commit(first)
    publish(parent, ar)
    second = book(parent, anchor="m2")
    second.update(second.show()["work"][0]["entry_id"], {"fields": {"description": "Current after fence"}})
    br = commit(second)
    publish(parent, br)
    assert not notices(db)
    parent._active_compression_commit_fence = None
    assert displayed.wait(2)
    # The real fence waiter flushes the existing queue, not a new queue/scheduler.
    assert [row["display_metadata"]["noting_snapshot_id"] for row in notices(db)] == [br["snapshot_id"]]
    assert len(parent.displays) == 1 and ar["snapshot_id"] not in parent.displays[0]
