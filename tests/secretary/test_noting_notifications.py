"""Completion guidance through real Note qualification, SQLite FM and native Main request."""

import copy
from pathlib import Path

import pytest

from secretary.framework_messages import mark_framework_turn, publish_noting_completion
from secretary.notebook_store import NotebookStore
from secretary.noting_notes import check_note_delivery
from secretary.noting_notifications import SCHEDULE_SUGGESTION_INSTRUCTION

pytest_plugins = ["tests.secretary.test_noting_child"]

GUIDANCE = (
    "Summary reports only the Noting task's work. For Conversation facts, uncertainty, "
    "user acceptance and decisions, use the CURRENT NOTEBOOK SNAPSHOT below; "
    "do not infer or strengthen them from Summary."
)
# Exact finish reason and correct decision text from the authorized synthetic K04 sample.
REASON = (
    "已记录本科身份与复盘习惯、周六下午面谈及Mira/陈老师的不同职责、毕业项目与面谈准备、"
    "仍开放的毕业资格核实问题，以及不休学、不交项目给导师、不注册外部提醒和不发消息的明确边界。"
    "另建立一项Memory候选，尚未提议或执行外部写入；无实际写入可结算，也未添加Schedule建议。"
)
DECISION = (
    "用户明确未决定休学，也未决定把毕业项目交给导师；不得将这两个未采纳的AI建议记为用户决定。"
    "当前按实际情况继续，不注册外部提醒，不发消息。"
)


class RequestCaptured(BaseException):
    """Stop at native model dispatch without inventing a provider reply."""


@pytest.fixture
def notification_runtime(parent, db, stub_client, tmp_path, monkeypatch):
    outside = tmp_path / "terminal-outside-git"
    outside.mkdir()
    monkeypatch.chdir(outside)
    parent.session_cwd = str(outside)
    parent.context_compressor.context_length = 262144
    parent.context_compressor.threshold_tokens = 196608
    db.append_message(parent.session_id, "user", DECISION, message_uid="k04-user", timestamp=1002)
    parent._session_messages = db.get_messages_as_conversation(parent.session_id)
    yield parent, db, Path(db.db_path).with_name("config.yaml")
    parent.close()


def _new_native_boundary(parent, db):
    from agent.context_compressor import COMPRESSED_SUMMARY_METADATA_KEY
    # Controlled external summary only. Real durable native publication and Note selection remain intact.
    rows = [{"role": "assistant", "content": "Synthetic preparation context.",
             COMPRESSED_SUMMARY_METADATA_KEY: True}, *copy.deepcopy(parent._session_messages)]
    db.archive_and_compact(parent.session_id, rows)
    parent._session_messages = db.get_messages_as_conversation(parent.session_id, include_row_ids=True)


@pytest.mark.parametrize("kind", ["finish_noting", "forced", "context_overflow"])
@pytest.mark.parametrize("attachments", [False, True])
def test_summary_boundary_survives_qualified_note_publish_and_next_native_request(
        notification_runtime, monkeypatch, kind, attachments):
    parent, db, config = notification_runtime
    config.write_text(
        "noting:\n  enabled: true\n  idle:\n    enabled: false\n  persistence_proposal:\n"
        f"    char_threshold: {1 if attachments else 1000000}\n    entry_threshold: 100\n"
        "terminal:\n  cwd: " + parent.session_cwd + "\n")
    ref = parent._secretary_conversation_ref
    store = NotebookStore(db, ref, anchor_message_uid="k04-user", task_id="synthetic-k04")
    kwargs = {"schedule_suggestion": {"content": "Discuss the remaining question", "schedule": "Next review"}} if attachments else {}
    store.create("decision", {"description": DECISION, "rationale": "用户会继续准备面谈，紧张不代表放弃。",
                 "scope": "毕业项目与面谈的当前安排，以及本次后续操作", "valid_when": "直至用户另行更改"},
                 source_message_uids=["k04-user"], **kwargs)
    termination = {"type": kind, **({"reason": REASON} if kind == "finish_noting" else {})}
    summary = REASON if kind == "finish_noting" else {
        "forced": "The Noting execution budget ended.",
        "context_overflow": "The Noting context window was exhausted.",
    }[kind]
    result = store.commit(termination=termination)
    assert not publish_noting_completion(parent, result, termination=termination, summary=REASON)
    assert not db._read_all("SELECT * FROM secretary_noting_note_receipts")
    _new_native_boundary(parent, db)
    root, tools = parent._cached_system_prompt, copy.deepcopy(parent.tools)
    mark_framework_turn(parent, running=True)
    assert publish_noting_completion(parent, result, termination=termination, summary=REASON)
    assert not publish_noting_completion(parent, result, termination=termination, summary=REASON)
    assert not db._read_all("SELECT * FROM secretary_noting_note_receipts")
    mark_framework_turn(parent, running=False)
    rows = [row for row in db.get_messages(parent.session_id)
            if (row.get("display_metadata") or {}).get("noting_run_output")]
    assert len(rows) == 1
    row, = rows
    body = row["content"]
    assert body.index("Summary: " + summary) < body.index(GUIDANCE) < body.index("\n\nCURRENT NOTEBOOK SNAPSHOT")
    assert body.count(GUIDANCE) == 1 and DECISION in body
    assert f"Termination: {kind}" in body
    assert ("may remain unfinished" in body) is (kind != "finish_noting")
    assert ("PERSISTENCE PROPOSAL REQUEST" in body) is attachments
    assert (SCHEDULE_SUGGESTION_INSTRUCTION in body) is attachments
    assert db.notebook_snapshot_audit(result["snapshot_id"])["termination"] == termination
    receipt, = db._read_all("SELECT * FROM secretary_noting_note_receipts")
    assert receipt["snapshot_id"] == result["snapshot_id"]
    assert receipt["carrier_message_uid"] == row["message_uid"]
    assert not check_note_delivery(parent)
    assert len(db._read_all("SELECT * FROM secretary_noting_note_receipts")) == 1
    assert parent._cached_system_prompt == root and parent.tools == tools
    requests = []

    def capture(request):
        requests.append(copy.deepcopy(request))
        raise RequestCaptured()

    parent._disable_streaming = True
    monkeypatch.setattr(parent, "_interruptible_api_call", capture)
    with pytest.raises(RequestCaptured):
        parent.run_conversation("请只说明当前已决定和仍未决定的事项。", conversation_history=list(parent._session_messages))
    assert len(requests) == 1
    payload = "\n".join(str(message.get("content", "")) for message in requests[0]["messages"])
    assert row["content"] in payload and payload.count(GUIDANCE) == 1
    assert payload.index("Summary: " + summary) < payload.index(GUIDANCE) < payload.index("\n\nCURRENT NOTEBOOK SNAPSHOT")
