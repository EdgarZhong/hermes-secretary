"""Real native Heartbeat persistence publishes before provider work, without waiting for turn end."""
import threading
import copy

import pytest

from secretary.heartbeat import render_heartbeat
from tests.agent.test_run_agent import _mock_response
from tests.tui_gateway.test_submit_idle import live as live, wait_all
from tui_gateway import server

_native_emit = server._emit


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


@pytest.mark.parametrize("failure", ["before_ring", "transport_false", "after_ring"])
def test_native_heartbeat_publication_recovers_only_before_replay_commit(live, monkeypatch, failure):
    from tui_gateway import event_replay
    text = render_heartbeat("publication boundary", 1800000000)
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    attempts = []
    faulted = []
    original_freeze = event_replay._freeze_params
    def freeze(params):
        if failure == "before_ring" and params.get("type") == "message.user_committed" and not faulted:
            faulted.append(True)
            raise OSError("transient freeze failure before replay commit")
        return original_freeze(params)
    class Transport:
        def write(self, frame):
            attempts.append(copy.deepcopy(frame))
            if frame.get("params", {}).get("type") == "message.user_committed":
                if failure == "after_ring":
                    raise OSError("transport exception after replay commit")
                if failure == "transport_false":
                    return False
            return True
        def close(self):
            pass
    def provider(kwargs):
        entered.set()
        assert release.wait(5)
        return _mock_response(content="HEARTBEAT_OVER", finish_reason="stop")
    live.session["transport"] = Transport()
    monkeypatch.setattr(server, "_emit", _native_emit)
    monkeypatch.setattr(event_replay, "_freeze_params", freeze)
    monkeypatch.setattr(live.agent, "_interruptible_api_call", provider)
    server._emit("error", "runtime", {"message": "an older unrelated event"})
    assert server._run_prompt_submit("heartbeat-publication", "runtime", live.session, text)
    assert entered.wait(5)
    row = next(row for row in live.db.get_messages("stored") if row["role"] == "user")
    def retained():
        return [event for event in event_replay.events_since("runtime", 0)
                if event["type"] == "message.user_committed"
                and event.get("payload", {}).get("message", {}).get("message_uid") == row["message_uid"]]
    def writes():
        return [frame for frame in attempts if frame.get("params", {}).get("type") == "message.user_committed"]
    expected_first = 0 if failure == "before_ring" else 1
    assert len(retained()) == expected_first
    assert len(writes()) == expected_first
    assert bool(faulted) == (failure == "before_ring")
    durable = {**row, "_row_id": row["id"], "_db_persisted": True}
    live.agent._on_turn_user_persisted([durable], 0)
    live.agent._on_turn_user_persisted([durable], 0)
    # A failed pre-ring attempt recovers once; False and post-ring errors already
    # have the real replay fact and must not create another seq or transport write.
    assert len(retained()) == 1
    assert len(writes()) == 1
    assert retained()[0]["payload"]["message"]["row_id"] == row["id"]
    release.set()
    wait_all(live)
