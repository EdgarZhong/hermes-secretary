"""Busy Secretary feedback must preserve the native Main result and its image blocks."""
import base64
import contextlib
import copy
import threading
import time

import pytest

from tui_gateway import server
from tests.secretary.test_noting_surface import _agent, runtime as _native_runtime
from tests.secretary.test_noting_child import mock_response


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    yield from _native_runtime.__wrapped__(tmp_path, monkeypatch)


def wait_idle(session):
    deadline = time.monotonic() + 10
    while session.get("running") and time.monotonic() < deadline:
        time.sleep(.01)
    assert not session.get("running"), "native prompt thread did not finish"


@pytest.mark.parametrize("commands", [["noting"], ["noting off", "noting on"], ["notebook"]])
def test_busy_slash_preserves_native_multimodal_main(runtime, monkeypatch, commands):
    db, config = runtime
    home = config.parent
    config.write_text("noting:\n  enabled: true\nmodel:\n  supports_vision: true\n  context_length: 196000\n")
    agent = _agent(db, model="gpt-4o")
    agent.client.chat.completions.create.return_value = mock_response("Opening reply.")
    opening = agent.run_conversation(user_message="Opening context.", title_user_message="")
    assert opening["completed"]
    session = {"agent": agent, "session_key": agent.session_id, "profile_home": str(home),
               "source": "cli", "history": opening["messages"], "history_lock": threading.RLock(),
               "history_version": 0, "running": False, "attached_images": [],
               "image_counter": 0, "cols": 80, "slash_worker": None,
               "show_reasoning": False, "tool_progress_mode": "all"}
    entered, release = threading.Event(), threading.Event()
    calls, events = [], []
    def provider(**kwargs):
        calls.append(copy.deepcopy(kwargs))
        if len(calls) == 1:
            entered.set()
            assert release.wait(10), "test did not release provider"
        return mock_response("The square is red." if len(calls) == 1 else "Continue done.")
    agent.client.chat.completions.create.side_effect = provider
    monkeypatch.setattr(server, "_session_db", lambda _session: contextlib.nullcontext(db))
    monkeypatch.setattr(server, "_emit", lambda *args: events.append(args))
    monkeypatch.setattr(server, "_sync_agent_model_with_config", lambda *a: None)
    monkeypatch.setattr(server, "_sync_agent_compression_with_config", lambda *a: None)
    monkeypatch.setattr(server, "_sync_agent_fallback_with_config", lambda *a: None)
    monkeypatch.setattr(server, "_sync_bot_capabilities", lambda *a: None)
    monkeypatch.setattr(server, "_start_turn_voice", lambda: (None, False))
    monkeypatch.setattr(server, "_get_usage", lambda _a: {})
    server._sessions["feedback-race"] = session
    image = home / "square.png"
    image.write_bytes(base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+a4V0AAAAASUVORK5CYII="))
    session["attached_images"] = [str(image)]
    content = "Identify the square."
    try:
        result = server.handle_request({"id": "main", "method": "prompt.submit", "params": {
            "session_id": "feedback-race", "text": content}})
        assert "error" not in result, result
        assert entered.wait(10), events
        for command in commands:
            reply = server.handle_request({"id": command, "method": "slash.exec", "params": {
                "session_id": "feedback-race", "command": "/" + command}})
            assert "error" not in reply, reply
            if command in {"noting off", "noting on"}:
                assert db.notebook_local_enabled(agent._secretary_conversation_ref) is command.endswith(" on")
        release.set()
        wait_idle(session)
        users = [m for m in session["history"] if m.get("role") == "user"]
        assert any(isinstance(m.get("content"), list) and any(
            b.get("type") == "image_url" for b in m["content"]) for m in users), session["history"]
        assert any(m.get("content") == "The square is red." for m in session["history"])
        assert not any("warning" in e[2] for e in events if e[0] == "message.complete")
        assert agent._session_messages is session["history"]
        assert all(m.get("_db_persisted") for m in session["history"])
        from agent.message_visibility import is_model_visible
        from secretary.noting_child import freeze_parent_active_prefix
        visible = [m for m in session["history"] if is_model_visible(m)]
        frozen = freeze_parent_active_prefix(agent, visible[-1]["message_uid"])
        assert any(isinstance(m.get("content"), list) and any(
            b.get("type") == "image_url" for b in m["content"]) for m in frozen)
        feedback = [m for m in session["history"] if m.get("display_metadata", {}).get("human_only")]
        assert bool(feedback) is (commands == ["notebook"])
        assert not any(m in frozen for m in feedback)
        root = agent._cached_system_prompt
        following = server.handle_request({"id": "next", "method": "prompt.submit", "params": {
            "session_id": "feedback-race", "text": "Continue."}})
        assert "error" not in following, following
        wait_idle(session)
        assert len(calls) == 2
        assert agent._cached_system_prompt == root
        assert any(isinstance(m.get("content"), list) and any(
            b.get("type") == "image_url" for b in m["content"]) for m in calls[-1]["messages"])
        assert not any(m.get("content") == row["content"] for row in feedback for m in calls[-1]["messages"])
        for command in commands:
            matching = [m for m in session["history"] if isinstance(m.get("content"), str)
                        and m["content"].endswith("/" + command)]
            assert len(matching) == 1
        replay, display, _ = server._load_resume_transcript(db, agent.session_id)
        image_user = next(m for m in session["history"] if isinstance(m.get("content"), list))
        restored_user = next(m for m in replay if m.get("message_uid") == image_user["message_uid"])
        assert "Identify the square." in str(restored_user["content"])
        assert str(image) in str(restored_user["content"])
        durable = db.get_messages_as_conversation(agent.session_id)
        assert sum(bool(m.get("display_metadata", {}).get("human_only")) for m in durable) == len(feedback)
        summary = [{"role": m["role"], "human_only": m.get("display_metadata", {}).get("human_only"),
                    "main_reply": "The square is red." in str(m.get("content")),
                    "notebook_reply": "Notebook Snapshot" in str(m.get("content"))} for m in replay]
        assert any(is_model_visible(m) and "The square is red." in str(m.get("content"))
                   for m in replay), summary
        if feedback:
            assert not any(is_model_visible(m) and "Notebook Snapshot" in str(m.get("content"))
                           for m in replay), summary
            assert sum(bool(m.get("display_metadata", {}).get("human_only")) for m in display) == len(feedback)
        cold = _agent(db, existing=False, model="gpt-4o")
        try:
            cold_result = cold.run_conversation(user_message="Cold follow-up.", conversation_history=replay,
                                                title_user_message="")
            assert cold_result["completed"]
            assert len(calls) == 3
            assert any("The square is red." in str(m.get("content")) for m in calls[-1]["messages"])
            assert not any("Notebook Snapshot" in str(m.get("content")) for m in calls[-1]["messages"])
        finally:
            cold.close()
    finally:
        release.set()
        wait_idle(session)
        server._sessions.pop("feedback-race", None)
        agent.close()


@pytest.mark.parametrize("mode", ["shorter", "already_in_result", "preserved_pivot", "unknown_before", "unknown_after", "forged"])
def test_registered_feedback_reconciliation_boundaries(runtime, monkeypatch, mode):
    from agent.message_metadata import stamp_message_uid
    db, config = runtime
    agent = _agent(db)
    def message(role, content):
        row = {"role": role, "content": content}
        stamp_message_uid(row)
        return row
    baseline = [message(role, f"old-{i}-{role}")
                for i in range(4) for role in ("user", "assistant")]
    if mode == "preserved_pivot":
        baseline.insert(0, {"role": "user", "content": "Answer tersely.", "display_kind": "personality_switch"})
    session = {"agent": agent, "session_key": agent.session_id, "profile_home": str(config.parent),
               "source": "cli", "history": list(baseline), "history_lock": threading.RLock(),
               "history_version": 0, "running": True}
    monkeypatch.setattr(server, "_session_db", lambda _: contextlib.nullcontext(db))
    server._sessions["feedback-boundary"] = session
    def mutate():
        with session["history_lock"]:
            session["history"].append(message("user", "unowned change"))
            session["history_version"] += 1
    try:
        if mode == "unknown_before":
            mutate()
        for command in ("noting off", "noting on"):
            response = server.handle_request({"id": command, "method": "slash.exec", "params": {
                "session_id": "feedback-boundary", "command": "/" + command}})
            assert "error" not in response, response
            if command == "noting off":
                server._append_model_switch_marker(session, model="new-model", provider="openai")
        feedback = [row for batch in session["_secretary_feedback_appends"] for row in batch["messages"]]
        if mode == "unknown_after":
            mutate()
        if mode == "forged":
            session.pop("_secretary_feedback_appends")
        returned = [message("user", "compressed summary"), message("assistant", "native reply")]
        if mode == "already_in_result":
            returned.extend(copy.deepcopy(feedback))
        if mode == "preserved_pivot":
            returned.insert(0, baseline[0])
        result = {"messages": returned}
        before = copy.deepcopy(session["history"])
        warning = server._commit_turn_history(session, result, baseline, 0)
        if mode in {"unknown_before", "unknown_after", "forged"}:
            assert warning and session["history"] == before
        else:
            assert warning is None
            assert session["history"][:2] == returned[:2]
            assert not any(m["content"].startswith("old-") for m in session["history"])
            for row in feedback:
                assert sum(m.get("message_uid") == row["message_uid"] for m in session["history"]) == 1
            assert sum(server._is_pivot_marker(m) for m in session["history"]) == (2 if mode == "preserved_pivot" else 1)
            if mode == "preserved_pivot":
                assert session["history"][0] is baseline[0]
            tail = session["history"][len(returned) if mode == "preserved_pivot" else 2:]
            assert [m.get("message_uid") for m in tail if not server._is_pivot_marker(m)] == [
                m["message_uid"] for m in feedback]
            assert server._is_pivot_marker(tail[2])
            assert agent._session_messages is session["history"]
        assert "_secretary_feedback_appends" not in session
    finally:
        server._sessions.pop("feedback-boundary", None)
        agent.close()


def test_idle_feedback_publishes_the_current_active_reference(runtime, monkeypatch):
    db, config = runtime
    agent = _agent(db)
    session = {"agent": agent, "session_key": agent.session_id, "profile_home": str(config.parent),
               "source": "cli", "history": [], "history_lock": threading.RLock(),
               "history_version": 0, "running": False}
    monkeypatch.setattr(server, "_session_db", lambda _: contextlib.nullcontext(db))
    server._sessions["feedback-idle"] = session
    try:
        response = server.handle_request({"id": "idle", "method": "slash.exec", "params": {
            "session_id": "feedback-idle", "command": "/noting off"}})
        assert "error" not in response, response
        assert agent._session_messages is session["history"]
        assert len(session["history"]) == 2
        assert "_secretary_feedback_appends" not in session
        assert not db.notebook_local_enabled(agent._secretary_conversation_ref)
    finally:
        server._sessions.pop("feedback-idle", None)
        agent.close()
