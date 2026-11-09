"""The real Session's non-reentrant history lock, with bounded child RPCs."""
import subprocess
import sys
from pathlib import Path


def test_control_rpc_chain_uses_native_plain_lock_without_deadlock(tmp_path):
    command = [sys.executable, str(Path(__file__).resolve()), "--child", str(tmp_path)]
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=15)
    except subprocess.TimeoutExpired as exc:
        raise AssertionError(f"native RPC deadlock at stdout={exc.stdout!r}, stderr={exc.stderr!r}") from exc
    assert result.returncode == 0, result.stdout + result.stderr
    assert "idle active stop complete" in result.stdout + result.stderr


def _child(path):
    import threading
    import pytest
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    from tests.tui_gateway.test_pending_native_turn import live
    from tests.tui_gateway.test_web_controlled_input import provider_gate, receipt, rpc, send, settle_all
    monkeypatch = pytest.MonkeyPatch()
    fixture = live.__wrapped__(monkeypatch, Path(path))
    lab = next(fixture)
    lab.session["history_lock"] = threading.Lock()
    assert type(lab.session["history_lock"]) is type(threading.Lock())
    gate = provider_gate(lab, monkeypatch)
    print("before idle", flush=True)
    assert send("plain-first", "ordinary native Send")["result"]["receipt"]["accepted"]
    assert gate.entered.wait(5)
    print("before active", flush=True)
    assert send("plain-steer", "same runtime correction")["result"]["receipt"]["state"] == "pending"
    print("before stop", flush=True)
    assert rpc("session.interrupt", input_policy="web_controlled")["result"]["status"] == "interrupted"
    gate.release.set()
    settle_all(lab)
    assert receipt("plain-steer")["state"] == "cancelled"
    next(fixture, None)
    monkeypatch.undo()
    print("idle active stop complete", flush=True)


if __name__ == "__main__":
    _child(sys.argv[2])
