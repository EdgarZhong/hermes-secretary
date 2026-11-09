"""Independent Gateway claim + native SQLite lease versus historical source metadata."""
import os
import subprocess
import sys
from selectors import DefaultSelector, EVENT_READ

import pytest

from tests.tui_gateway.test_pending_native_turn import live as live
from tests.tui_gateway.test_web_controlled_input import send, rpc, provider_gate, settle_all


GATEWAY_OWNER = '''
import sys
from types import SimpleNamespace
from pathlib import Path
from hermes_state import SessionDB
from gateway.run_busy import GatewayBusySessionMixin
from hermes_cli.active_sessions import observe_native_turn_owner
runner = GatewayBusySessionMixin()
runner.config = {}
runner._is_session_running = lambda key: False
runner._get_max_concurrent_sessions = lambda: None
source = SimpleNamespace(platform=SimpleNamespace(value="weixin"),chat_id="chat",user_id="human")
lease, error = runner._claim_active_session_slot("gateway-route", source)
assert error is None and lease is not None
db = SessionDB(Path(sys.argv[1]))
holder = "opaque-owner-token-not-a-channel"
assert db.try_acquire_session_turn_lease("stored", holder)
parent = SimpleNamespace(_session_db=db, session_id="stored", _active_session_turn_lease_holder=holder,
                         _gateway_session_key="gateway-route")
if sys.argv[2] == "proved":
    observe_native_turn_owner(parent)
print("ready", flush=True)
sys.stdin.readline()
db.release_session_turn_lease("stored", holder)
lease.release()
db.close()
'''


@pytest.mark.parametrize("proof,code,reason", [("proved", 4009, "gateway_running"), ("unproved", 4090, "owner_unavailable")])
def test_only_exact_gateway_native_proof_returns_busy(live, proof, code, reason):
    process = subprocess.Popen([sys.executable, "-c", GATEWAY_OWNER, str(live.db.db_path), proof],
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                               text=True, env={**os.environ, "HERMES_HOME": str(live.home)})
    try:
        with DefaultSelector() as selector:
            selector.register(process.stdout, EVENT_READ)
            assert selector.select(10), "Gateway owner did not become ready"
        assert process.stdout.readline().strip() == "ready"
        result = send("rejected", "not accepted by foreign owner")
        assert result["error"]["code"] == code and result["error"]["data"] == {"accepted": False, "reason": reason}
        state = rpc("session.input_state")["result"]
        assert state["phase"] == ("gateway" if proof == "proved" else "unavailable")
        assert not state["can_submit"] and not live.session.get("queued_prompt")
    finally:
        _, error = process.communicate("release\n", timeout=10)
        assert process.returncode == 0, error


def test_historical_weixin_source_never_refuses_same_runtime_control(live, monkeypatch):
    live.db._execute_write(lambda conn: conn.execute("UPDATE sessions SET source='weixin' WHERE id='stored'"))
    live.session["source"] = "weixin"
    gate = provider_gate(live, monkeypatch)
    assert send("first", "new Web input")["result"]["receipt"]["accepted"]
    assert gate.entered.wait(5)
    assert send("second", "control this native runtime")["result"]["receipt"]["state"] == "pending"
    assert rpc("session.interrupt")["result"]["status"] == "interrupted"
    gate.release.set()
    settle_all(live)
