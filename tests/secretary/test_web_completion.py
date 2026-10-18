"""Real Noting outcomes -> Gateway wire -> optional browser evidence fixture."""
import json
from pathlib import Path

from tests.secretary.test_noting_child import _tool_response, empty_state, mock_response

pytest_plugins = ("tests.secretary.test_noting_child",)


def test_formal_completion_events(stub_client, parent, db, monkeypatch, record_property):
    from secretary.noting_child import run_noting_task
    from tests.tui_gateway.test_multi_client_fanout import RecordingTransport
    from tui_gateway import server

    home = Path(db.db_path).parent
    (home / "config.yaml").write_text("noting:\n  enabled: true\n")
    ref = parent._secretary_conversation_ref
    db.append_message("S17", "user", "New coverage", message_uid="m3", timestamp=1002)
    parent._session_messages = db.get_messages_as_conversation("S17")
    monkeypatch.setattr(server, "_sessions", {})
    monkeypatch.setattr(server, "_profile_home", lambda _profile: home)
    peer = RecordingTransport()
    server.register_live_transport(peer)

    def read():
        reply = server.handle_request({"jsonrpc": "2.0", "id": 1, "method": "secretary.state",
                                       "params": {"stored_session_id": "S17", "profile": "default"}})
        assert "error" not in reply, reply
        return reply["result"]

    def run(anchor, *, fail=False):
        peer.frames.clear()
        stub_client.chat.completions.create.side_effect = (RuntimeError("provider down") if fail else [
            _tool_response("finish_noting", {"reason": "Reviewed the Notebook."}, "finish"), mock_response("done")])
        admission = db.noting_admit(ref, anchor, kind="idle")
        assert admission is not None
        outcome = run_noting_task(
            parent, admission_id=admission, conversation_ref=ref, anchor_message_uid=anchor,
            trigger_type="idle", runtime_profile="NOTING", task_instruction="Maintain the Notebook.",
            parent_active_messages=parent._session_messages, state_provider=lambda _child: empty_state())
        events = [frame["params"] for frame in peer.frames
                  if frame.get("params", {}).get("type") == "secretary.changed"]
        return outcome, {"events": events, "state": read()}

    try:
        cold = read()
        failed, failed_wire = run("m2", fail=True)
        winner, winner_wire = run("m3")
        late, late_wire = run("m1")
        evidence = {"cold": cold, "failed": failed_wire, "winner": winner_wire, "nonwinner": late_wire}
        record_property("completion_wire", json.dumps(evidence, ensure_ascii=False))
        assert not failed.committed
        assert winner.committed and winner.commit_result["pointer_changed"] is True
        assert late.committed and late.commit_result["pointer_changed"] is False
        assert all(not event["payload"].get("completion_snapshot_id") for event in failed_wire["events"])
        assert all(not event["payload"].get("completion_snapshot_id") for event in late_wire["events"])
        completions = [event for event in winner_wire["events"]
                       if event["payload"].get("completion_snapshot_id")]
        assert len(completions) == 1
        assert completions[0]["payload"]["completion_snapshot_id"] == winner.snapshot_id
        assert winner_wire["state"]["current_snapshot_id"] == late_wire["state"]["current_snapshot_id"] == winner.snapshot_id
    finally:
        server.unregister_live_transport(peer)


def test_completion_metadata_is_opt_in_and_observer_failures_do_not_affect_commit(db):
    from secretary.noting_child import commit_noting_snapshot
    from secretary.web_events import subscribe, unsubscribe
    from tests.secretary.test_noting_runtime import _agent

    db.create_session("metadata", source="test")
    db.append_message("metadata", "user", "Evidence", message_uid="metadata-input")
    ref = db.resolve_conversation_ref("metadata")
    _agent(db, "metadata")
    legacy, modern = [], []
    subscribe("completion-legacy", lambda home, owner, reason: legacy.append((home, owner, reason)))
    subscribe("completion-modern", lambda home, owner, reason, **metadata: modern.append(metadata), include_metadata=True)
    subscribe("completion-broken", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("offline")), include_metadata=True)
    try:
        result = commit_noting_snapshot(
            db, ref, empty_state(), anchor_message_uid="metadata-input", trigger_type="idle",
            runtime_profile="NOTING", termination={"type": "finish_noting", "reason": "Reviewed"})
        assert result["pointer_changed"] is True
        assert legacy[-1][1:] == (ref, "notebook_changed")
        assert modern == [{"completion_snapshot_id": result["snapshot_id"]}]
        assert db.notebook_current(ref)["snapshot_id"] == result["snapshot_id"]
    finally:
        for key in ("completion-legacy", "completion-modern", "completion-broken"):
            unsubscribe(key)


def test_optional_pointer_read_failure_keeps_original_state_available(db, monkeypatch):
    from secretary.web_read import secretary_state

    db.create_session("optional", source="test")
    ref = db.resolve_conversation_ref("optional")
    monkeypatch.setattr(db, "_notebook_pointer_id_conn", lambda *args: (_ for _ in ()).throw(RuntimeError("pointer unavailable")))
    result = secretary_state(db, "optional")
    assert result["availability"] == "available" and result["conversation_ref"] == ref
    assert result["task_state"] == "idle" and result["current_snapshot_id"] is None
