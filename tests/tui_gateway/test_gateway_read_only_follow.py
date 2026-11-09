"""External native writer observation; no second Web writer or message scan."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import time

import pytest

from hermes_state import SessionDB
from hermes_state_recovery_view import project_view, read_view, selector
from tests.tui_gateway.test_pending_native_turn import live as live, rpc
from tui_gateway import server


GATEWAY_OWNER = r'''
import json, os, sys
from pathlib import Path
from types import SimpleNamespace
from gateway.config import GatewayConfig, Platform
from gateway.run import GatewayRunner
from gateway.session import SessionSource
from hermes_cli.active_sessions import observe_native_turn_owner
from hermes_state import SessionDB
home = Path(os.environ["HERMES_HOME"])
runner = GatewayRunner(GatewayConfig(sessions_dir=home / "sessions", multiplex_profiles=False))
source = SessionSource(platform=Platform.TELEGRAM, chat_id="local-read-only-probe", chat_type="dm")
slot, error = runner._claim_active_session_slot("read-only-route", source)
assert slot is not None and error is None, error
db = SessionDB(home / "state.db")
target = os.environ.get("GATEWAY_NATIVE_SESSION", "stored")
holder = "opaque-external-native-owner"
assert db.try_acquire_session_turn_lease(target, holder)
agent = SimpleNamespace(_session_db=db, session_id=target,
    _gateway_session_key="read-only-route", _active_session_turn_lease_holder=holder)
if not os.environ.get("GATEWAY_LEGACY_METADATA"):
    agent._current_turn_id = "external-native-turn"
observe_native_turn_owner(agent)
print(json.dumps({"ready": True, "pid": os.getpid()}), flush=True)
try:
    for line in sys.stdin:
        if line.strip() == "release":
            break
        if line.strip() == "source":
            uid = "source-" + holder
            metadata = {"turn_source": {"message_uid": uid, "turn_id": getattr(agent, "_current_turn_id", "legacy")}}
            db.append_message(target, "user", "Controlled native source", message_uid=uid,
                              display_metadata=metadata, turn_lease_holder=holder)
            db.append_messages_batch(target, [{"role": "assistant", "content": "Visible suffix " + str(i)}
                                              for i in range(8)], turn_lease_holder=holder)
            print(json.dumps({"source": uid}), flush=True)
            continue
        assert line.strip() == "next"
        db.release_session_turn_lease(target, holder)
        holder = "opaque-next-native-owner"
        assert db.try_acquire_session_turn_lease(target, holder)
        agent._active_session_turn_lease_holder = holder
        if not os.environ.get("GATEWAY_LEGACY_METADATA"):
            agent._current_turn_id = "next-external-native-turn"
        observe_native_turn_owner(agent)
        print(json.dumps({"next": True}), flush=True)
finally:
    db.release_session_turn_lease(target, holder)
    slot.release()
    db.close()
'''


@pytest.mark.parametrize("continued", [False, True])
@pytest.mark.parametrize("legacy", [False, True])
def test_formal_gateway_claim_reports_running_without_web_writer(live, continued, legacy):
    env = {**os.environ, "HERMES_HOME": str(live.home), "PYTHONPATH": str(Path(__file__).resolve().parents[2])}
    if continued:
        live.db.end_session("stored", "compression")
        live.db.create_session("compression-tip", parent_session_id="stored", source="desktop")
        live.agent.session_id = "compression-tip"
        live.session["session_key"] = "compression-tip"
        env["GATEWAY_NATIVE_SESSION"] = "compression-tip"
    if legacy:
        env["GATEWAY_LEGACY_METADATA"] = "1"
    process = subprocess.Popen([sys.executable, "-c", GATEWAY_OWNER], cwd=live.home, env=env,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    def recover():
        page = project_view(read_view(live.db, "stored", "default", [selector({"kind": "latest", "limit": 3})]))
        window = page["windows"][0]
        result = rpc("session.activate", omit_messages=True, recovery_view={"version": 1, "profile": "default",
            "stored_id": "stored", "windows": [{"selector": window["selector"], "receipt": window["coverage"]}]})
        view = result["result"]["recovery_view"]
        assert view["complete"] and view["live_output_available"] is False, view.get("reason")
        return view
    try:
        line = process.stdout.readline()
        assert line, process.stderr.read()
        ready = json.loads(line)
        assert ready["ready"] and ready["pid"] != os.getpid()
        state = rpc("session.input_state")["result"]
        assert state["phase"] == "gateway" and state["reason"] == "gateway"
        assert state["running"] is True
        assert state["turn_id"] == (None if legacy else "external-native-turn")
        assert state["can_submit"] is False and state["can_stop"] is False
        assert live.session["running"] is False
        source = recover()["turn_source"]
        assert source == {"state": "unknown", "turn_id": None} if legacy else source == {
            "state": "uncommitted", "turn_id": "external-native-turn"}
        process.stdin.write("source\n")
        process.stdin.flush()
        uid = json.loads(process.stdout.readline())["source"]
        view = recover()
        if not legacy:
            assert view["turn_source"]["state"] == "committed"
            assert view["turn_source"]["source"]["message_uid"] == uid
            assert view["turn_source"]["source"]["position"] < view["windows"][0]["coverage"]["window"]["first"]["position"]
        denied = rpc("prompt.submit", input_policy="web_controlled", operation_id="not-a-second-writer", text="local probe")
        assert denied["error"]["data"] == {"accepted": False, "reason": "gateway_running"}
        process.stdin.write("next\n")
        process.stdin.flush()
        assert json.loads(process.stdout.readline())["next"]
        state = rpc("session.input_state")["result"]
        assert state["phase"] == "gateway" and state["running"]
        assert state["turn_id"] == (None if legacy else "next-external-native-turn")
        if not legacy:
            assert recover()["turn_source"] == {"state": "uncommitted", "turn_id": "next-external-native-turn"}
    finally:
        if process.poll() is None:
            process.communicate("release\n", timeout=20)
        assert process.returncode == 0, process.stderr.read()
    state = rpc("session.input_state")["result"]
    assert state["phase"] == "idle" and not state["running"] and state["can_submit"]


def test_turn_lease_start_renewal_and_expiry_share_scoped_session_watch(tmp_path, monkeypatch):
    db = SessionDB(tmp_path / "state.db")
    try:
        db.create_session("stored", source="wechat")
        ref = db.resolve_conversation_ref("stored")
        monkeypatch.setattr(server, "_watcher_home", lambda: tmp_path)
        monkeypatch.setattr(server, "_served_profile_homes", [])
        monkeypatch.setattr(server, "_sessions_broadcast_scope", {})
        before = server._sessions_sig()
        server._sessions_broadcast_scope.update(server._sessions_probe_scope)
        assert db.try_acquire_session_turn_lease("stored", "opaque-owner", ttl_seconds=10)
        started = server._sessions_sig()
        assert started != before
        assert server._sessions_changed_payload() == {"scope_complete": True, "changed_sessions": [
            {"profile_home": str(tmp_path), "session_id": "stored", "conversation_ref": ref}]}
        server._sessions_broadcast_scope.update(server._sessions_probe_scope)
        assert db.refresh_session_turn_lease("stored", "opaque-owner", ttl_seconds=20)
        assert server._sessions_sig() == started
        future = time.time() + 21
        monkeypatch.setattr(server.time, "time", lambda: future)
        assert server._sessions_sig() == before
        assert server._sessions_changed_payload()["changed_sessions"][0]["session_id"] == "stored"
    finally:
        db.close()


def test_prewritten_source_metadata_commit_wakes_existing_session_watch_once(tmp_path, monkeypatch):
    from hermes_state_turn_terminal import persist_turn_source
    db = SessionDB(tmp_path / "state.db")
    try:
        db.create_session("stored", source="wechat")
        row_id = db.append_message("stored", "user", "prewritten native input")
        uid = db.get_messages("stored")[0]["message_uid"]
        assert db.try_acquire_session_turn_lease("stored", "source-owner")
        monkeypatch.setattr(server, "_watcher_home", lambda: tmp_path)
        monkeypatch.setattr(server, "_served_profile_homes", [])
        before = server._sessions_sig()
        marker = {"message_uid": uid, "turn_id": "current-external-turn"}
        assert persist_turn_source(db, "stored", row_id, marker, turn_lease_holder="source-owner")
        committed = server._sessions_sig()
        assert committed != before
        assert persist_turn_source(db, "stored", row_id, marker, turn_lease_holder="source-owner")
        assert server._sessions_sig() == committed
    finally:
        db.close()


def test_source_wake_failure_keeps_native_commit_success(tmp_path, monkeypatch):
    from hermes_state_turn_terminal import persist_turn_source
    db = SessionDB(tmp_path / "state.db")
    try:
        db.create_session("stored", source="wechat")
        row_id = db.append_message("stored", "user", "native input")
        uid = db.get_messages("stored")[0]["message_uid"]
        def failed_wake(*args, **kwargs):
            raise RuntimeError("controlled notification failure")
        monkeypatch.setattr("hermes_state_history_notifications.notify_history_changed", failed_wake)
        marker = {"message_uid": uid, "turn_id": "current-native-turn"}
        assert persist_turn_source(db, "stored", row_id, marker)
        assert db.get_messages("stored")[0]["display_metadata"]["turn_source"] == marker
    finally:
        db.close()


def test_unknown_external_holder_never_claims_gateway_or_allows_second_writer(live):
    assert live.db.try_acquire_session_turn_lease("stored", "unclassified-live-owner")
    try:
        state = rpc("session.input_state")["result"]
        assert state["phase"] == "unavailable" and state["turn_id"] is None
        assert not state["can_submit"] and not state["can_stop"]
        denied = rpc("prompt.submit", input_policy="web_controlled", operation_id="unknown-owner-input", text="local probe")
        assert denied["error"]["code"] == 4090
        assert denied["error"]["data"] == {"accepted": False, "reason": "owner_unavailable"}
    finally:
        live.db.release_session_turn_lease("stored", "unclassified-live-owner")
