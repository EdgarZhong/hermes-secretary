"""Ordinary Web sends expose only their real committed source before starting the turn."""
import threading

import pytest

from hermes_state import SessionDB
from tests.tui_gateway.test_inflight_output_recovery import Peer
from tests.tui_gateway.test_pending_native_turn import live as live
from tests.tui_gateway.test_submit_idle import image_file, provider_gate, rpc, wait_all
from tui_gateway import event_replay, inflight_output, server
from tui_gateway.transport import bind_transport, reset_transport

_native_emit = server._emit


class StartedPeer(Peer):
    def __init__(self):
        super().__init__()
        self.started = threading.Event()

    def write(self, frame):
        result = super().write(frame)
        if frame.get("params", {}).get("type") == "message.start":
            self.started.set()
        return result


def test_real_row_receipt_precedes_worker_and_replays_to_both_clients(live, monkeypatch):
    event_replay.reset_replay_state()
    first, second = StartedPeer(), StartedPeer()
    live.session.update(transport=first, viewers={first: 1, second: 1})
    server._attach_session_transport(live.session, second)
    monkeypatch.setattr(server, "_emit", _native_emit)
    gate = provider_gate(live, monkeypatch)
    original = server._run_after_agent_ready
    before_worker = []

    def run(*args, **kwargs):
        before_worker.append(inflight_output.snapshot(live.session, "runtime"))
        return original(*args, **kwargs)

    monkeypatch.setattr(server, "_run_after_agent_ready", run)
    token = bind_transport(first)
    try:
        response = rpc(text="authoritative committed user")
    finally:
        reset_transport(token)
    assert gate.entered.wait(5)
    accepted = response["result"]["accepted_user"]
    row = next(row for row in live.db.get_messages("stored") if row["role"] == "user")
    assert accepted == {"stored_session_id": "stored", "message": {
        "role": "user", "row_id": row["id"], "message_uid": row["message_uid"],
        "content": row["content"], "timestamp": row["timestamp"]}}
    early = [event for event in before_worker[0]["events"] if event["type"] == "message.user_committed"]
    assert len(early) == 1 and early[0]["payload"] == accepted
    for peer in (first, second):
        assert peer.started.wait(5)
        frames = [frame["params"] for frame in peer.frames]
        assert [frame["payload"] for frame in frames if frame["type"] == "message.user_committed"] == [accepted]
        assert next(i for i, f in enumerate(frames) if f["type"] == "message.user_committed") < next(
            i for i, f in enumerate(frames) if f["type"] == "message.start")
    live.session["transport"] = Peer()
    for _ in range(600):
        server._emit("thinking.delta", "runtime", {"text": "bounded display projection"})
    assert event_replay.is_truncated("runtime", 0)
    # A compacted state snapshot's watermark must never skip the committed driving row.
    snapshot = inflight_output.snapshot(live.session, "runtime")
    assert [event["payload"] for event in snapshot["events"] if event["type"] == "message.user_committed"] == [accepted]
    assert all(event["seq"] <= snapshot["seq"] for event in snapshot["events"])
    activated = rpc("session.activate", omit_messages=True)["result"]["state_snapshot"]
    assert [event["payload"] for event in activated["events"] if event["type"] == "message.user_committed"] == [accepted]
    replay = rpc("session.events.since", last_seen=snapshot["seq"])["result"]
    assert replay["events"] == []
    gate.release.set()
    wait_all(live)
    assert [event["payload"] for event in inflight_output.snapshot(live.session, "runtime")["events"]
            if event["type"] == "message.user_committed"] == [accepted]
    legacy = rpc("prompt.submit", text="legacy source")
    wait_all(live)
    assert "accepted_user" not in legacy["result"]
    assert not any(event["type"] == "message.user_committed" for event in inflight_output.snapshot(
        live.session, "runtime")["events"])


@pytest.mark.parametrize("mutation", ["missing", "wrong_uid", "wrong_owner", "wrong_db", "stale", "read_failure"])
def test_unproven_or_stale_rows_never_acknowledge_but_submit_continues(live, monkeypatch, mutation):
    original = server._persist_submit_user_row
    old = {"role": "user", "content": "older send", "_row_id": 123, "message_uid": "old"}
    live.session["_submit_user_row"] = old

    def persist(session, *args, **kwargs):
        if mutation == "stale":
            return
        original(session, *args, **kwargs)
        staged = session.get("_submit_user_row")
        mutations = {
            "missing": lambda: session.pop("_submit_user_row", None),
            "wrong_uid": lambda: staged.update(message_uid="uncommitted-uid"),
            "wrong_owner": lambda: staged.update(_submit_row_session_id="unrelated-session"),
            "wrong_db": lambda: staged.update(_submit_row_db_path=str(live.home / "unrelated.db")),
        }
        mutations.get(mutation, lambda: None)()

    monkeypatch.setattr(server, "_persist_submit_user_row", persist)
    monkeypatch.setattr(server, "_run_after_agent_ready", lambda *a, **k: None)
    if mutation == "read_failure":
        monkeypatch.setattr(server, "_idle_committed_user", lambda *a: (_ for _ in ()).throw(OSError("read failed")))
    result = rpc(text="new accepted send")
    wait_all(live)
    assert result["result"]["status"] == "streaming" and "accepted_user" not in result["result"]
    assert not any(kind == "message.user_committed" for kind, _, _ in live.frames)


def test_secondary_profile_and_rotated_owner_use_actual_store(live, monkeypatch, tmp_path):
    launch = SessionDB(tmp_path / "launch" / "state.db")
    try:
        launch.create_session("rotated", source="tui")
        launch.append_message("rotated", "user", content="foreign launch row")
        live.db.publish_compression_child(
            parent_session_id="stored", child_session_id="rotated", source="tui",
            messages=[{"role": "assistant", "content": "compressed context"}],
            require_compression_lease=False)
        live.agent.session_id = "rotated"
        monkeypatch.setattr(server, "_get_db", lambda: launch)
        monkeypatch.setattr(server, "_run_after_agent_ready", lambda *a, **k: None)
        result = rpc(text="secondary profile committed")
        wait_all(live)
        receipt = result["result"]["accepted_user"]
        assert receipt["stored_session_id"] == "rotated"
        row = next(row for row in live.db.get_messages("rotated") if row["role"] == "user")
        assert receipt["message"]["message_uid"] == row["message_uid"]
        assert receipt["message"]["content"] == "secondary profile committed"
        assert launch.get_messages("rotated")[0]["content"] == "foreign launch row"
    finally:
        launch.close()


def test_persist_failure_never_emits_receipt_or_starts_worker(live, monkeypatch):
    def disk_full(*args, **kwargs):
        import errno
        raise OSError(errno.ENOSPC, "controlled full disk")

    monkeypatch.setattr(server, "_persist_submit_user_row", disk_full)
    result = rpc(text="cannot be saved")
    assert result["error"]["code"] == 5070
    assert not live.session.get("_run_thread") and not live.session["running"]
    assert not any(kind == "message.user_committed" for kind, _, _ in live.frames)


def test_receipt_emit_failure_is_best_effort_after_admission(live, monkeypatch):
    def emit(kind, *args):
        if kind == "message.user_committed":
            raise OSError("controlled detached peer")

    monkeypatch.setattr(server, "_emit", emit)
    monkeypatch.setattr(server, "_run_after_agent_ready", lambda *a, **k: None)
    result = rpc(text="accepted even without display delivery")
    wait_all(live)
    assert result["result"]["accepted_user"]["message"]["content"] == "accepted even without display delivery"


@pytest.mark.parametrize("image_only", [False, True])
def test_empty_image_only_and_isolation_do_not_reuse_older_source(live, monkeypatch, image_only):
    monkeypatch.setattr(server, "_run_after_agent_ready", lambda *a, **k: None)
    first = rpc(text="previous send")
    wait_all(live)
    assert first["result"]["accepted_user"]
    live.session["running"] = False
    image = image_file(live)
    result = rpc(image_paths=[str(image)] if image_only else [])
    wait_all(live)
    assert result["result"]["status"] == "streaming" and "accepted_user" not in result["result"]
    assert len([row for row in live.db.get_messages("stored") if row["role"] == "user"]) == 1
    live.session["running"] = False
    monkeypatch.setattr(server, "_session_uses_compute_host", lambda *a, **k: True)
    monkeypatch.setattr(server, "_submit_prompt_to_compute_host",
                        lambda rid, *a, **k: server._ok(rid, {"status": "streaming", "turn_isolation": True}))
    isolated = rpc(text="child not yet committed")
    assert "accepted_user" not in isolated["result"]
    assert len([kind for kind, _, _ in live.frames if kind == "message.user_committed"]) == 1


def test_hidden_row_receipt_preserves_real_display_kind(live, monkeypatch):
    # Native idle context still honors internal hidden rows; it does not mint display kinds.
    from tui_gateway.methods_submit_idle import _idle_submit_scope
    monkeypatch.setattr(server, "_run_after_agent_ready", lambda *a, **k: None)
    original = server._persist_submit_user_row

    def persist(session, text, display_kind):
        original(session, text, display_kind, accept_metadata={"title_preview": "durable preview"})
        session["_submit_user_row"]["content"] = "forged staging content is not authoritative"

    monkeypatch.setattr(server, "_persist_submit_user_row", persist)
    with _idle_submit_scope():
        result = server._native_prompt_submit_handler("hidden", {
            "session_id": "runtime", "text": "hidden real row", "display_kind": "hidden"})
    wait_all(live)
    message = result["result"]["accepted_user"]["message"]
    assert message["display_kind"] == "hidden" and message["content"] == "hidden real row"
    assert message["display_metadata"] == {"title_preview": "durable preview"}
