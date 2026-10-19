"""First-paint history and bounded, owner-scoped disclosure hydration."""
import copy
import json
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from hermes_cli.web_history_cards import history_cards, tool_status


@pytest.mark.parametrize("content, expected", [
    ('{"exit_code": 1, "stdout": "failed"}', "failed"),
    ('{"success": false}', "failed"),
    ('{"status": "cancelled"}', "interrupted"),
    ("[Tool execution cancelled — terminal was skipped. stop requested]", "interrupted"),
    ("", "complete"), ("done", "complete"),
    # A tool row always serializes ``content``, so a stored NULL is an empty
    # result: the client's toolResultState() already calls that "complete".
    (None, "complete"),
    # Values the client's explicitToolFailure() deliberately does not treat as
    # failures must stay non-failures here too (parity, not opinion).
    ('{"exit_code": 0, "stdout": ""}', "complete"),
    ('{"exit_code": true}', "complete"),
    ('{"error": "   "}', "complete"),
    ('{"status": "failed"}', "failed"), ('{"is_error": true}', "failed"),
    ('{"ok": false}', "failed"), ('{"error": "boom"}', "failed"),
    ('["not", "an", "object"]', "complete"), ("17", "complete"),
    # JSON has one number type: an integral float is an integer to the browser.
    ('{"exit_code": 2.0}', "failed"), ('{"exit_code": 0.0}', "complete"),
    # The browser's JSON.parse rejects these, so the card must not read them either.
    ('{"is_error": NaN}', "complete"), ('{"is_error": Infinity}', "complete"),
])
def test_tool_card_retains_actual_result_state(content, expected):
    assert tool_status(content, {}) == expected


@pytest.mark.parametrize("metadata, expected", [
    ({"status": "cancelled"}, "interrupted"),
    ({"status": "interrupted"}, "interrupted"),
    ({"status": "failed"}, "failed"),
    ({"exit_code": 3}, "failed"),
])
def test_tool_card_metadata_status_matches_the_client(metadata, expected):
    assert tool_status("ok", metadata) == expected


def test_cards_keep_visible_content_and_identity_without_mutating_sources():
    rows = [
        {"id": 1, "message_uid": "human", "role": "user", "content": "Question"},
        {"id": 2, "message_uid": "answer", "role": "assistant", "content": "Visible answer",
         "reasoning": "private thinking " * 10000,
         "display_commentary": ["Public progress"],
         "tool_calls": [{"id": "call", "tool_call_uid": "call-uid",
                         "function": {"name": "terminal", "arguments": "long params " * 1000}}]},
        {"id": 3, "message_uid": "result", "role": "tool", "tool_call_uid": "call-uid",
         "content": json.dumps({"exit_code": 2, "stdout": "long output " * 10000})},
    ]
    original = copy.deepcopy(rows)
    cards = history_cards(rows)
    assert rows == original
    assert cards[0] == rows[0]
    assert cards[1]["content"] == "Visible answer"
    assert cards[1]["display_commentary"] == ["Public progress"]
    assert cards[1]["tool_calls"][0]["function"] == {"name": "terminal"}
    assert cards[1]["deferred_details"] == ["reasoning", "tool_arguments"]
    assert cards[2]["display_tool_status"] == "failed"
    assert "content" not in cards[2]
    assert [row["message_uid"] for row in cards] == ["human", "answer", "result"]
    assert len(json.dumps(cards)) < len(json.dumps(rows)) / 100


def test_terminal_residual_cards_keep_visible_answer_and_failure_metadata():
    row = {"id": 1, "role": "user", "content": "ask", "display_metadata": {
        "other": {"keep": True}, "turn_terminal": {"status": "error", "error": "Provider unavailable",
            "outputs": [{"kind": "reasoning", "text": "thought"},
                        {"kind": "message", "text": "visible partial answer"},
                        {"kind": "tool", "state": "complete", "name": "terminal", "tool_call_uid": "tool",
                         "args": {"cmd": "test"}, "result": {"exit_code": 1}}]}}}
    card = history_cards([row])[0]
    terminal = card["display_metadata"]["turn_terminal"]
    assert card["content"] == "ask"
    assert card["display_metadata"]["other"] == {"keep": True}
    assert terminal["error"] == "Provider unavailable"
    assert terminal["outputs"][0] == {"kind": "reasoning", "deferred_details": ["text"]}
    assert terminal["outputs"][1] == row["display_metadata"]["turn_terminal"]["outputs"][1]
    assert terminal["outputs"][2]["display_tool_status"] == "failed"
    assert "result" not in terminal["outputs"][2]
    assert card["deferred_details"] == ["terminal_outputs"]


@pytest.mark.parametrize("output, marked, expected", [
    # An ABSENT result is the client's "unknown" fallback: no marker may overwrite it.
    ({"kind": "tool", "state": "complete", "name": "terminal", "args": {"cmd": "x"}}, False, None),
    # A present-but-NULL result is an empty successful result on both sides.
    ({"kind": "tool", "state": "complete", "name": "terminal", "args": {"cmd": "x"}, "result": None},
     True, "complete"),
    # Non-complete outputs keep the client's own terminal-status fallback.
    ({"kind": "tool", "state": "running", "name": "terminal", "result": {"exit_code": 1}}, False, None),
])
def test_terminal_card_status_only_marks_what_the_client_would_compute(output, marked, expected):
    row = {"id": 1, "role": "user", "content": "ask", "display_metadata": {
        "turn_terminal": {"status": "error", "outputs": [output]}}}
    card = history_cards([row])[0]
    projected = card["display_metadata"]["turn_terminal"]["outputs"][0]
    assert ("display_tool_status" in projected) is marked
    if marked:
        assert projected["display_tool_status"] == expected


@pytest.fixture
def endpoint(tmp_path, monkeypatch):
    from hermes_state import SessionDB
    from hermes_cli.web_routers.sessions import manage_router

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    home = tmp_path / ".hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr("hermes_state.DEFAULT_DB_PATH", home / "state.db")
    db = SessionDB(home / "state.db")
    db.create_session("chat", source="desktop")
    first = db.append_message("chat", "user", "Question", message_uid="user-uid")
    answer = db.append_message("chat", "assistant", "Answer", reasoning="Thinking body",
                               message_uid="answer-uid")
    tool = db.append_message("chat", "tool", '{"exit_code": 1, "stdout": "detail"}',
                             tool_name="terminal", message_uid="tool-uid")
    db.create_session("foreign", source="desktop")
    foreign = db.append_message("foreign", "user", "Other conversation")
    app = FastAPI()
    app.include_router(manage_router)
    with TestClient(app) as client:
        yield client, db, first, answer, tool, foreign
    db.close()


def test_default_full_response_and_cards_then_exact_details(endpoint):
    client, _, _, answer, tool, _ = endpoint
    path = "/api/sessions/chat/messages"
    full = client.get(path).json()
    cards = client.get(path, params={"view": "cards"}).json()
    assert "projection" not in full
    assert cards["projection"] == "cards"
    assert cards["pagination"] == full["pagination"]
    assert cards["messages"][0] == {
        key: value for key, value in full["messages"][0].items()
        if key not in ("api_content", "codex_message_items", "codex_reasoning_items")}
    assert cards["messages"][1]["deferred_details"] == ["reasoning"]
    assert cards["messages"][2]["display_tool_status"] == "failed"
    detail = client.get(path, params={"detail_row_ids": f"{answer},{tool}"}).json()
    assert detail["projection"] == "details"
    assert detail["messages"] == full["messages"][1:]


def test_cards_plus_details_restore_every_withheld_body_field_for_field(endpoint):
    """The property the client relies on: cards + one detail read == the full display page.

    Covers every body kind the projection can defer — reasoning, tool-call arguments,
    a tool result row, and terminal residual outputs — not just one representative.
    """
    client, db, *_ = endpoint
    db.create_session("rich", source="desktop")
    db.append_message(
        "rich", "assistant", "answer", reasoning="deep thought",
        reasoning_details=[{"type": "reasoning", "text": "deep thought"}],
        tool_calls=[{"id": "c1", "function": {"name": "terminal", "arguments": '{"cmd": "ls"}'}}],
        api_content="model-facing", codex_reasoning_items=[{"x": 1}], codex_message_items=[{"y": 2}],
        message_uid="rich-answer")
    db.append_message("rich", "tool", '{"exit_code": 0, "stdout": "ok"}', tool_name="terminal",
                      tool_call_id="c1", message_uid="rich-tool")
    db.append_message(
        "rich", "user", "run it", message_uid="rich-user",
        display_metadata={"turn_terminal": {"status": "error", "source_message_uid": "rich-user",
            "outputs": [{"kind": "tool", "name": "terminal", "tool_call_uid": "t1", "state": "complete",
                         "args": {"cmd": "ls"}, "result": {"exit_code": 1}},
                        {"kind": "message", "text": "visible partial answer"}]}})
    path = "/api/sessions/rich/messages"
    full = client.get(path, params={"limit": 50}).json()
    cards = client.get(path, params={"limit": 50, "view": "cards"}).json()
    assert full["pagination"] == cards["pagination"]
    deferred = [row for row in cards["messages"] if row.get("deferred_details")]
    assert len(deferred) == 3  # assistant body, tool result, terminal outputs
    detail = client.get(path, params={
        "detail_row_ids": ",".join(str(row["id"]) for row in deferred),
        "include_compacted": "true"}).json()
    restored = {row["id"]: row for row in detail["messages"]}
    for card in deferred:
        original = next(row for row in full["messages"] if row["id"] == card["id"])
        # Every withheld body comes back byte-for-byte, and nothing extra is added.
        assert restored[card["id"]] == original


def test_detail_reads_do_not_expose_foreign_or_rewound_rows(endpoint):
    client, db, first, answer, tool, foreign = endpoint
    db.rewind_to_message("chat", first)
    data = client.get("/api/sessions/chat/messages", params={
        "detail_row_ids": f"{answer},{tool},{foreign}"}).json()
    assert data["messages"] == []


def test_detail_rows_follow_only_verified_compression_ancestry(endpoint):
    client, db, first, _, _, _ = endpoint
    db.end_session("chat", "compression")
    db.create_session("tip", source="desktop", parent_session_id="chat")
    own = db.append_message("tip", "assistant", "continued")
    data = client.get("/api/sessions/tip/messages", params={
        "detail_row_ids": f"{first},{own}"}).json()
    assert [row["id"] for row in data["messages"]] == [first, own]
    db.create_session("branch", source="desktop", parent_session_id="tip")
    branch_row = db.append_message("branch", "assistant", "separate branch")
    data = client.get("/api/sessions/branch/messages", params={
        "detail_row_ids": f"{first},{own},{branch_row}"}).json()
    assert [row["id"] for row in data["messages"]] == [branch_row]


def test_details_never_revive_an_active_alias_of_a_retired_uid(endpoint):
    client, db, _, answer, _, _ = endpoint
    retired = db.append_message("chat", "assistant", "new generation", message_uid="answer-uid")
    db._execute_write(lambda conn: conn.execute(
        "UPDATE messages SET active = 0, compacted = 0 WHERE id = ?", (retired,)))
    data = client.get("/api/sessions/chat/messages", params={
        "detail_row_ids": f"{answer},{retired}"}).json()
    assert data["messages"] == []


def test_detail_retirement_follows_uid_into_a_compression_child(endpoint):
    client, db, _, answer, _, _ = endpoint
    db.end_session("chat", "compression")
    db.create_session("tip", source="desktop", parent_session_id="chat")
    retired = db.append_message("tip", "assistant", "descendant generation", message_uid="answer-uid")
    db._execute_write(lambda conn: conn.execute(
        "UPDATE messages SET active = 0, compacted = 0 WHERE id = ?", (retired,)))
    data = client.get("/api/sessions/tip/messages", params={"detail_row_ids": str(answer)}).json()
    assert data["messages"] == []


def test_detail_retirement_ignores_a_generation_on_an_explicit_branch(endpoint):
    """Only the verified compression spine may retire a uid; /branch copies are exempt."""
    client, db, _, answer, _, _ = endpoint
    db.end_session("chat", "compression")
    db.create_session("tip", source="desktop", parent_session_id="chat")
    db.end_session("tip", "branched")
    db.create_session("branch", source="desktop", parent_session_id="tip",
                      model_config={"_branched_from": "tip"})
    retired = db.append_message("branch", "assistant", "branch generation", message_uid="answer-uid")
    db._execute_write(lambda conn: conn.execute(
        "UPDATE messages SET active = 0, compacted = 0 WHERE id = ?", (retired,)))
    data = client.get("/api/sessions/tip/messages", params={"detail_row_ids": str(answer)}).json()
    assert [row["id"] for row in data["messages"]] == [answer]
    assert retired not in [row["id"] for row in data["messages"]]


def test_detail_reads_respect_include_compacted(endpoint):
    """A caller that never asked for archived display history cannot fetch one row of it."""
    client, db, _, answer, _, _ = endpoint
    db._execute_write(lambda conn: conn.execute(
        "UPDATE messages SET active = 0, compacted = 1 WHERE id = ?", (answer,)))
    default = client.get("/api/sessions/chat/messages", params={"detail_row_ids": str(answer)}).json()
    assert default["messages"] == []
    opted = client.get("/api/sessions/chat/messages", params={
        "detail_row_ids": str(answer), "include_compacted": "true"}).json()
    assert [row["id"] for row in opted["messages"]] == [answer]


def test_detail_page_never_widens_the_page_it_was_asked_to_explain(endpoint):
    """A detail request is addressed by physical id, not by count: it cannot page."""
    client, db, _, answer, _, _ = endpoint
    extra = db.append_message("chat", "assistant", "another row", message_uid="extra-uid")
    data = client.get("/api/sessions/chat/messages", params={
        "detail_row_ids": f"{answer},{extra + 5000}"}).json()
    assert [row["id"] for row in data["messages"]] == [answer]
    assert data["pagination"]["returned"] == 1


@pytest.mark.parametrize("params", [
    {"view": "unknown"}, {"detail_row_ids": ""}, {"detail_row_ids": "0"},
    {"detail_row_ids": "-1"}, {"detail_row_ids": "1 OR 1=1"},
    {"detail_row_ids": "9223372036854775808"},
    {"detail_row_ids": ",".join(str(i) for i in range(1, 14))},
    {"view": "cards", "detail_row_ids": "1"},
])
def test_invalid_detail_requests_fail_without_unbounded_reads(endpoint, params):
    client, *_ = endpoint
    assert client.get("/api/sessions/chat/messages", params=params).status_code == 400
