"""F19: native compaction names only the visible source it actually summarized."""

from copy import deepcopy
from threading import Event

import pytest

from agent.conversation_compression_manual import compress_now, parse_compress_args
from hermes_cli.cli_secretary_commands import secretary_feedback_messages
from secretary.noting_scope import owning_db_scope
from tests.secretary.test_r3_child import database as database, native_parent as native_parent, response, tool_response


def _seed(parent, db, placement):
    hidden = []
    for number in range(18):
        db.append_messages_batch("parent", [
            {"role": "user", "content": f"Earlier question {number}: " + "original work " * 60},
            {"role": "assistant", "content": f"Earlier answer {number}: " + "confirmed facts " * 60}])
        if placement == "middle" and number == 8:
            hidden = secretary_feedback_messages("/notebook", "PRIVATE HUMAN VIEW " * 70, human_only=True)
            db.append_messages_batch("parent", hidden)
    if placement == "tail":
        hidden = secretary_feedback_messages("/notebook", "PRIVATE HUMAN VIEW " * 70, human_only=True)
        db.append_messages_batch("parent", hidden)
    parent._session_messages = db.get_messages_as_conversation("parent", include_row_ids=True)
    return {row["message_uid"] for row in hidden}


@pytest.mark.parametrize("placement", ["tail", "middle", "none"])
@pytest.mark.parametrize("partial", [False, True], ids=["full", "here-one"])
def test_native_compaction_preserves_hidden_anchor_and_commits_frozen_child(
        native_parent, database, monkeypatch, tmp_path, placement, partial):
    import secretary.noting_child as owner

    (tmp_path / "config.yaml").write_text("noting:\n  enabled: true\n  idle:\n    enabled: false\n")
    parent, client = native_parent
    parent.compression_enabled = True
    parent.compression_in_place = True
    parent._compression_feasibility_checked = True
    compressor = parent.context_compressor
    compressor.context_length = 130000
    compressor.protect_first_n = 2
    compressor.protect_last_n = 4
    compressor.tail_token_budget = 2000
    hidden = _seed(parent, database, placement)
    before = deepcopy(parent._session_messages)
    ref = parent._secretary_conversation_ref
    entered, release = Event(), Event()
    workers, child_wires, summaries, commits, arrivals = [], [], [], [], []
    original_spawn, original_archive = owner.spawn_noting_task, database.archive_and_compact

    def capture_spawn(*args, **kwargs):
        worker = original_spawn(*args, **kwargs)
        workers.append(worker)
        return worker

    def summary(prompt, _started):
        summaries.append(prompt)
        assert entered.wait(10), "the real Noting child must start before native publication"
        arrival = {"role": "user", "content": "Concurrent input outside the held compression source."}
        database.append_messages_batch("parent", [arrival])
        arrivals.append(arrival["message_uid"])
        return "## Progress\nEarlier questions were answered.\n## Open\nRetain current work."

    replies = iter([tool_response("finish_noting", {"reason": "The frozen work needs no edits."}), response()])

    def provider(**kwargs):
        entered.set()
        assert release.wait(10), "child commit must follow the actual native archive"
        child_wires.append(deepcopy(kwargs))
        return next(replies)

    def archive(*args, **kwargs):
        commits.append(deepcopy(kwargs))
        return original_archive(*args, **kwargs)

    monkeypatch.setattr(owner, "spawn_noting_task", capture_spawn)
    monkeypatch.setattr(compressor, "_call_summary_llm", summary)
    monkeypatch.setattr(database, "archive_and_compact", archive)
    client.chat.completions.create.side_effect = provider
    try:
        with owning_db_scope(database):
            result = compress_now(parent, parent._session_messages,
                                  parse_compress_args("here 1" if partial else ""), system_message="")
        assert result.status == "compressed" and summaries and len(commits) == 1
        assert "PRIVATE HUMAN VIEW" not in str(summaries)
        release.set()
        for worker in workers:
            worker.join(10)
            assert not worker.is_alive()
        admission = database._read_one("SELECT * FROM secretary_noting_admissions WHERE conversation_ref=?", (ref,))
        assert admission is not None
        child = database.noting_child(admission["admission_id"])
        assert child["status"] == "completed", child
        snapshot = database.notebook_current(ref)
        assert snapshot["anchor_message_uid"] == admission["anchor_message_uid"]
        full = database.get_full_foreground(conversation_ref=ref)
        full_uids = {row.get("message_uid") for row in full}
        assert hidden | set(arrivals) <= full_uids
        active = database.get_messages_as_conversation("parent")
        assert hidden | set(arrivals) <= {row.get("message_uid") for row in active}
        assert "PRIVATE HUMAN VIEW" not in str(child_wires)
        assert len(child_wires) == 2
        visible_before = [row for row in before if row["message_uid"] not in hidden]
        boundary = len(visible_before) + 1  # frozen root plus the complete visible Parent
        assert child_wires[0]["messages"][:boundary] == child_wires[1]["messages"][:boundary]
        main_wires = []
        client.chat.completions.create.side_effect = lambda **kw: main_wires.append(deepcopy(kw)) or response()
        parent.compression_enabled = False
        resumed = parent.run_conversation("Continue the visible work without external actions.",
                                          conversation_history=result.after_messages, title_user_message="")
        assert resumed["completed"] and main_wires
        assert "PRIVATE HUMAN VIEW" not in str(main_wires)
        assert database._read_one("SELECT COUNT(*) AS n FROM compression_locks")["n"] == 0
    finally:
        release.set()
        for worker in workers:
            worker.join(10)


@pytest.mark.parametrize("failure", ["no-op", "summary-failure", "db-failure"])
def test_rejected_visible_compaction_preserves_raw_hidden_history(
        native_parent, database, monkeypatch, tmp_path, failure):
    (tmp_path / "config.yaml").write_text("noting:\n  enabled: false\n")
    parent, _client = native_parent
    parent.compression_enabled = parent.compression_in_place = True
    parent._compression_feasibility_checked = True
    compressor = parent.context_compressor
    compressor.context_length = 130000
    compressor.protect_first_n = 2
    compressor.protect_last_n = 4
    compressor.tail_token_budget = 2000
    _seed(parent, database, "tail")
    before = deepcopy(parent._session_messages)
    original_ids = {row["_row_id"] for row in before}
    if failure == "no-op":
        compressor.protect_first_n = 1000
    elif failure == "summary-failure":
        compressor.abort_on_summary_failure = True

        def unavailable(*args):
            raise RuntimeError("controlled summary service failure")

        monkeypatch.setattr(compressor, "_call_summary_llm", unavailable)
    else:
        monkeypatch.setattr(compressor, "_call_summary_llm", lambda *args: "## Progress\nEarlier work retained.")

        def refused(*args, **kwargs):
            raise RuntimeError("controlled atomic archive failure")

        monkeypatch.setattr(database, "archive_and_compact", refused)
    with owning_db_scope(database):
        result = compress_now(parent, parent._session_messages, parse_compress_args(""), system_message="")
    assert result.after_messages == before
    assert {row["_row_id"] for row in database.get_messages_as_conversation("parent", include_row_ids=True)} == original_ids
    assert database._read_one("SELECT COUNT(*) AS n FROM compression_locks")["n"] == 0
