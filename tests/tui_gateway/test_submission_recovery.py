"""Recover a lost Web admission receipt from its real native user row."""
import json

import pytest

from tests.tui_gateway.test_submit_idle import live as live, provider_gate, rpc, wait_all


def status(identity, **params):
    return rpc("prompt.submission_status", client_submission_id=identity, **params)


def test_lost_ack_recovers_exact_commit_and_rejects_reuse(live, monkeypatch):
    gate = provider_gate(live, monkeypatch)
    response = rpc(text="one real prompt", client_submission_id="send-one")
    assert gate.entered.wait(5)
    receipt = response["result"]["accepted_user"]
    assert receipt["client_submission_id"] == "send-one"
    assert receipt["message"]["display_metadata"]["client_submission_id"] == "send-one"
    assert len([kind for kind, _, _ in live.frames if kind == "message.user_committed"]) == 1
    assert status("send-one")["result"] == {"status": "accepted", "accepted_user": receipt}
    assert status("other-send")["result"]["status"] == "unknown"
    gate.release.set()
    wait_all(live)
    assert status("send-one")["result"]["status"] == "accepted"
    duplicate = rpc(text="different text cannot reuse the identity", client_submission_id="send-one")
    assert duplicate["error"]["code"] == 4031
    assert len(gate.calls) == 1
    users = [m for m in live.db.get_messages("stored") if m["role"] == "user"]
    assert len(users) == 1
    assert users[0]["display_metadata"]["client_submission_id"] == "send-one"
    assert all("client_submission_id" not in json.dumps(call["messages"]) for call in gate.calls)


def test_same_text_other_conversation_and_retired_row_are_not_false_success(live, monkeypatch):
    gate = provider_gate(live, monkeypatch)
    assert rpc(text="identical", client_submission_id="right")["result"]["status"] == "streaming"
    assert gate.entered.wait(5)
    gate.release.set()
    wait_all(live)
    assert status("wrong")["result"]["status"] == "unknown"
    live.db.create_session("other", source="tui", model="test")
    live.db.append_message("other", "user", content="identical", display_metadata={"client_submission_id": "foreign"})
    assert status("foreign")["result"]["status"] == "unknown"
    # Acceptance is historical fact; reading it must not revive a rewound row.
    with live.db._read_ctx() as conn:
        before = conn.execute("select count(*) from messages").fetchone()[0]
    live.db._execute_write(lambda conn: conn.execute("update messages set active=0 where session_id='stored'"))
    assert status("right")["result"]["status"] == "accepted"
    assert live.db.get_messages("stored") == []
    with live.db._read_ctx() as conn:
        assert conn.execute("select count(*) from messages").fetchone()[0] == before


@pytest.mark.parametrize("identity", ["", "   ", "a" * 129])
def test_invalid_submission_identity_refuses_before_submit(live, identity):
    assert rpc(text="not submitted", client_submission_id=identity)["error"]["code"] == 4000
    assert status(identity)["error"]["code"] == 4000
    assert live.db.get_messages("stored") == []


def test_legacy_caller_still_submits_without_correlation(live, monkeypatch):
    gate = provider_gate(live, monkeypatch)
    response = rpc(text="legacy web")
    assert "client_submission_id" not in response["result"]["accepted_user"]
    assert gate.entered.wait(5)
    gate.release.set()
    wait_all(live)
    assert status("not-supplied")["result"]["status"] == "unknown"


def test_receipt_is_profile_scoped_and_survives_database_reopen(live, monkeypatch):
    import hermes_state_registry
    from tui_gateway import server
    gate = provider_gate(live, monkeypatch)
    assert rpc(text="saved", client_submission_id="restart-proof")["result"]["accepted_user"]
    assert gate.entered.wait(5)
    gate.release.set()
    wait_all(live)
    monkeypatch.setattr(server, "_profile_home", lambda _profile: str(live.home / "foreign"))
    assert status("restart-proof", profile="foreign")["error"]["code"] == 4003
    # The runtime has a profile_home, so _session_db acquires the profile registry,
    # not server._db. Close the original connection and observe the actual opener.
    hermes_state_registry.close_all_under(live.home)
    live.db.close()
    opened = []
    original_open = hermes_state_registry._open_session_db
    def observe_open(path):
        db = original_open(path)
        opened.append(db)
        return db
    monkeypatch.setattr(hermes_state_registry, "_open_session_db", observe_open)
    assert status("restart-proof")["result"]["status"] == "accepted"
    assert len(opened) == 1 and opened[0] is not live.db
    assert opened[0].db_path == live.db.db_path


def test_native_flush_publishes_identity_when_inline_prewrite_was_unavailable(live, monkeypatch):
    gate = provider_gate(live, monkeypatch)
    # The native submit prewrite is best effort. Its real Turn must still persist
    # and publish the same correlation if the later native flush succeeds.
    from hermes_state import SessionDB
    original_append = SessionDB.append_message
    attempted = []
    def fail_once(db, *args, **kwargs):
        attempted.append(args)
        if len(attempted) == 1:
            raise OSError("transient user-row prewrite failure")
        return original_append(db, *args, **kwargs)
    monkeypatch.setattr(SessionDB, "append_message", fail_once)
    response = rpc(text="eventually persisted", client_submission_id="late-native-flush")
    assert response["result"]["status"] == "streaming"
    assert "accepted_user" not in response["result"]
    assert gate.entered.wait(5)
    committed = [payload for kind, _, payload in live.frames if kind == "message.user_committed"]
    assert len(committed) == 1, (live.db.get_messages("stored"), live.session.get("inflight_turn"))
    assert committed[0]["client_submission_id"] == "late-native-flush"
    assert status("late-native-flush")["result"]["accepted_user"] == committed[0]
    gate.release.set()
    wait_all(live)
    assert len([row for row in live.db.get_messages("stored") if row["role"] == "user"]) == 1


def test_compression_tip_keeps_acceptance_and_other_profile_does_not(live, monkeypatch):
    from hermes_state import SessionDB
    from tui_gateway import server
    gate = provider_gate(live, monkeypatch)
    assert rpc(text="before compression", client_submission_id="before-tip")["result"]["accepted_user"]
    assert gate.entered.wait(5)
    gate.release.set()
    wait_all(live)
    ref = live.db.resolve_conversation_ref("stored")
    live.db.publish_compression_child(parent_session_id="stored", child_session_id="compressed",
                                      source="tui", messages=[{"role": "assistant", "content": "native summary"}],
                                      require_compression_lease=False)
    # Runtime adoption normally binds the new tip; do the same through the public
    # identity resolver before asking the read-only receipt RPC.
    assert live.db.resolve_conversation_ref("compressed") == ref
    live.agent.session_id = "compressed"
    live.session["session_key"] = "compressed"
    assert status("before-tip")["result"]["status"] == "accepted"
    assert rpc(text="cannot resend after compression", client_submission_id="before-tip")["error"]["code"] == 4031
    foreign_home = live.home / "foreign-profile"
    foreign_home.mkdir()
    foreign = SessionDB(foreign_home / "state.db")
    try:
        foreign.create_session("compressed", source="tui")
        server._sessions["foreign-runtime"] = {**live.session, "agent": None, "profile_home": str(foreign_home)}
        assert status("before-tip", session_id="foreign-runtime")["result"]["status"] == "unknown"
    finally:
        server._sessions.pop("foreign-runtime", None)
        foreign.close()


def test_compute_worker_native_entry_persists_and_publishes_submission_identity(live, monkeypatch):
    from io import StringIO
    from tui_gateway import server
    from tui_gateway.compute_host import ComputeHost
    from tests.agent.test_run_agent import _mock_response
    calls = []
    def provider(kwargs):
        calls.append(kwargs)
        assert any(kind == "message.user_committed" for kind, _, _ in live.frames)
        return _mock_response(content="worker finished", finish_reason="stop")
    monkeypatch.setattr(live.agent, "_interruptible_api_call", provider)
    frame = server._compute_host_turn_frame("worker-request", "runtime", live.session, "isolated source",
                                           display_metadata={"client_submission_id": "worker-send"})
    host = ComputeHost(stdout=StringIO(), max_workers=1, heartbeat_secs=0)
    try:
        # Exercise the real child frame consumer and native loop in-process.
        # This verifies the formal metadata seam, not OS pipe/restart behavior.
        host._run_real_turn(frame)
        committed = [payload for kind, _, payload in live.frames if kind == "message.user_committed"]
        assert len(committed) == 1 and committed[0]["client_submission_id"] == "worker-send"
        assert status("worker-send")["result"]["accepted_user"] == committed[0]
        assert len(calls) == 1 and "client_submission_id" not in json.dumps(calls[0]["messages"])
    finally:
        host._closed.set()
        host._executor.shutdown(wait=True)
