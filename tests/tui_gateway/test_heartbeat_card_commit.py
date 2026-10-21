"""Real native Heartbeat persistence publishes before provider work, without waiting for turn end."""
import threading

from secretary.heartbeat import render_heartbeat
from tests.agent.test_run_agent import _mock_response
from tests.tui_gateway.test_submit_idle import live as live, wait_all
from tui_gateway import server


def test_heartbeat_native_user_commit_is_visible_before_output_and_deduplicated(live, monkeypatch):
    text = render_heartbeat("Check current matters", 1800000000)
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    def provider(kwargs):
        entered.set()
        assert release.wait(5)
        return _mock_response(content="HEARTBEAT_OVER", finish_reason="stop")
    monkeypatch.setattr(live.agent, "_interruptible_api_call", provider)
    assert server._run_prompt_submit("heartbeat", "runtime", live.session, text)
    assert entered.wait(5)
    committed = [p for kind, sid, p in live.frames if kind == "message.user_committed"]
    assert len(committed) == 1
    payload = committed[0]
    row = live.db.get_messages("stored")[0]
    assert payload["stored_session_id"] == "stored"
    assert payload["message"] == {"row_id": row["id"], "message_uid": row["message_uid"],
                                   "role": "user", "content": text, "timestamp": row["timestamp"]}
    assert not any(kind == "message.complete" for kind, _, _ in live.frames)
    # Repeated persistence notification must not publish a duplicate card.
    durable = {**row, "_row_id": row["id"], "_db_persisted": True}
    live.agent._on_turn_user_persisted([durable], 0)
    assert len([p for kind, _, p in live.frames if kind == "message.user_committed"]) == 1
    release.set()
    wait_all(live)
    assert len([m for m in live.db.get_messages("stored") if m["role"] == "user"]) == 1


def test_only_actual_user_row_can_publish_not_thinking_or_assistant(live, monkeypatch):
    def provider(kwargs):
        live.agent.thinking_callback("Heartbeat — this is only model reasoning")
        return _mock_response(content="<heartbeat>assistant text</heartbeat>", finish_reason="stop")
    monkeypatch.setattr(live.agent, "_interruptible_api_call", provider)
    server._run_prompt_submit("normal", "runtime", live.session, "ordinary user")
    wait_all(live)
    assert not [p for kind, _, p in live.frames if kind == "message.user_committed"]


def test_retired_or_uncommitted_heartbeat_row_never_fabricates_a_card(live):
    from agent.context_compressor import _DB_PERSISTED_MARKER
    from tui_gateway.heartbeat_presentation import user_observer
    from tui_gateway.turn_terminal import token
    text = render_heartbeat("only actual commit", 1800000000)
    row_id = live.db.append_message("stored", "user", text, message_uid="heartbeat-retired")
    live.db._execute_write(lambda conn: conn.execute("UPDATE messages SET active=0 WHERE id=?", (row_id,)))
    source = {"role": "user", "content": text, "message_uid": "heartbeat-retired", "_row_id": row_id,
              _DB_PERSISTED_MARKER: True}
    observer = user_observer("runtime", live.session, live.agent, token(live.session), text, None)
    observer([source], 0)
    source["_row_id"] = row_id + 100
    observer([source], 0)
    assert not [p for kind, _, p in live.frames if kind == "message.user_committed"]


def test_actual_heartbeat_storage_failure_does_not_publish_a_card(live, monkeypatch):
    text = render_heartbeat("storage is unavailable", 1800000000)
    calls = []
    def unavailable(*args, **kwargs):
        raise OSError("controlled storage failure")
    def provider(kwargs):
        calls.append(kwargs)
        assert not [p for kind, _, p in live.frames if kind == "message.user_committed"]
        return _mock_response(content="HEARTBEAT_OVER", finish_reason="stop")
    monkeypatch.setattr(live.db, "append_messages_batch", unavailable)
    monkeypatch.setattr(live.agent, "_interruptible_api_call", provider)
    assert server._run_prompt_submit("heartbeat-failure", "runtime", live.session, text)
    wait_all(live)
    assert calls
    assert not [p for kind, _, p in live.frames if kind == "message.user_committed"]
    assert not [row for row in live.db.get_messages("stored") if row["role"] == "user"]
