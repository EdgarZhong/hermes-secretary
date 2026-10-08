"""Existing framed supervisor/control transport reaches the owning host/profile's dispatcher."""

import json
import sys
import threading

from hermes_state import SessionDB
from secretary.notebook_store import NotebookStore
from tui_gateway import server
from tui_gateway.compute_host import ComputeHost
from tui_gateway.host_supervisor import HostSupervisor
from tui_gateway.transport import StdioTransport


class ReplyStream:
    def __init__(self, supervisor):
        self.supervisor = supervisor
        self.buffer = ""

    def write(self, text):
        self.buffer += text
        while "\n" in self.buffer:
            line, self.buffer = self.buffer.split("\n", 1)
            if line:
                self.supervisor._handle_host_frame(json.loads(line))
        return len(text)

    def flush(self):
        pass


def test_remote_secretary_control_ack_keeps_profile_identity_and_busy_policy(tmp_path, monkeypatch):
    launch, target = tmp_path / "launch", tmp_path / "target"
    launch.mkdir()
    target.mkdir()
    (launch / "config.yaml").write_text("noting:\n  enabled: false\n")
    (target / "config.yaml").write_text("noting:\n  enabled: true\n")
    db = SessionDB(target / "state.db")
    db.create_session("host-main", source="tui")
    db.append_message("host-main", "user", "TARGET evidence only", message_uid="target-evidence")
    ref = db.resolve_conversation_ref("host-main")
    state = NotebookStore(db, ref)
    state.create("memory_candidate", {"draft": "TARGET candidate"},
                 source_message_identities=[{"conversation_ref": ref, "message_uid": "target-evidence"}])
    db.notebook_commit_snapshot(ref, state.show(), anchor_message_uid="target-evidence")
    sid = "secretary-host"
    base = {"agent": None, "history": [], "history_lock": threading.Lock(), "running": False,
            "cwd": "", "source": "tui", "transport": StdioTransport(lambda: None, threading.Lock())}
    mirror = {**base, "session_key": "launch-stale", "profile_home": str(launch), "_compute_host_active": True}
    owner = {**base, "session_key": "host-main", "profile_home": str(target)}
    server._sessions[sid] = mirror
    supervisor = HostSupervisor(argv=[sys.executable, "-c", ""], autostart=False)
    supervisor.start = lambda: None
    host = ComputeHost(stdout=ReplyStream(supervisor), heartbeat_secs=0)
    frames = []

    def transmit(frame):
        frames.append(frame)
        server._sessions[sid] = owner
        try:
            with monkeypatch.context() as child:
                # The actual compute process has this marker: its dispatcher must stay local.
                child.setenv("HERMES_COMPUTE_HOST_CHILD", "1")
                host.handle_frame(frame)
        finally:
            server._sessions[sid] = mirror

    supervisor._send_frame = transmit
    monkeypatch.setattr(server, "_get_compute_host_supervisor", lambda *a, **kw: supervisor)
    monkeypatch.setattr(server, "_session_uses_compute_host", lambda session: session is mirror)
    try:
        def slash(text):
            return server._methods["slash.exec"]("test", {"session_id": sid, "command": text})["result"]
        assert "is off" in slash("/notebook off")["output"]
        assert not db.notebook_local_enabled(ref)
        shown = slash("/notebook")["output"]
        assert "TARGET candidate" in shown
        assert "target-evidence" not in shown
        proposal = slash("/propose-persistence Original Tail 保留")
        assert proposal["type"] == "send"
        assert proposal["message"].endswith("Original Tail 保留")
        assert "TARGET evidence only" in proposal["message"]
        assert not db.notebook_local_enabled(ref)
        assert not (launch / "state.db").exists()
        assert mirror["session_key"] == "launch-stale" and owner["session_key"] == "host-main"
        owner["running"] = True
        assert "session busy" in slash("/propose-persistence busy tail")["output"]
        assert "TARGET candidate" in slash("/notebook")["output"]
        assert frames[-1]["route_name"] == "slash.notebook"
        (target / "config.yaml").write_text("noting:\n  enabled: false\n")
        owner["running"] = False
        assert "unavailable" in slash("/propose-persistence no bypass")["output"]
    finally:
        server._sessions.pop(sid, None)
        host.close()
        db.close()
