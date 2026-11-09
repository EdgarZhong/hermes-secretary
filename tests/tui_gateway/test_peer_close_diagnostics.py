"""Peer close metadata is bounded and never changes connection/owner behavior."""
from __future__ import annotations

import asyncio
import json
import logging
import socket

import pytest
from fastapi import FastAPI, WebSocket
from starlette.websockets import WebSocketDisconnect

from tui_gateway import server
from tui_gateway import ws as ws_mod
from tui_gateway.connection_diagnostics import ConnectionDiagnostics, peer_reported_initiator


def records(caplog):
    return [json.loads(record.message.split("connection_diagnostic ", 1)[1])
            for record in caplog.records if "connection_diagnostic " in record.message]


@pytest.fixture
def runtime(monkeypatch, caplog):
    peers = []
    caplog.set_level(logging.INFO, logger="hermes_cli.web_server")
    for name in ("_ensure_skin_watcher", "_ensure_lease_watcher", "_start_backend_heartbeat_refresher",
                 "_schedule_startup_orphan_sweep", "_release_wake_for_transport"):
        monkeypatch.setattr(server, name, lambda *args: None)
    monkeypatch.setattr(server, "resolve_skin", lambda: {})
    monkeypatch.setattr(server, "register_live_transport", peers.append)
    monkeypatch.setattr(server, "_close_sessions_for_transport", lambda *args, **kwargs: (0, 0))
    monkeypatch.setattr(ws_mod, "_note_dashboard_client_activity", lambda **kwargs: None)
    return peers


@pytest.mark.parametrize("initiator", ["ping_timeout", "ping_error", "connect_timeout", "socket_error",
                                       "bootstrap_error", "authentication", "stop"])
def test_only_fixed_application_close_reason_is_recognized(initiator):
    assert peer_reported_initiator(4100, f"hermes:{initiator}") == initiator
    assert peer_reported_initiator(1000, f"hermes:{initiator}") is None
    assert peer_reported_initiator(4100, f"hermes:{initiator} SECRET") is None
    assert peer_reported_initiator(4100, f"hermes:{initiator}\n") is None
    assert peer_reported_initiator(4100, [initiator]) is None


def test_peer_metadata_logging_rejects_unknown_strings(caplog):
    caplog.set_level(logging.INFO, logger="hermes_cli.web_server")
    diag = ConnectionDiagnostics()
    diag.log("closed", reason="disconnect_observed", peer_reported_initiator="SECRET")
    assert "peer_reported_initiator" not in records(caplog)[0]
    assert "SECRET" not in caplog.text


@pytest.mark.parametrize(("code", "reason", "reported"), [
    (4100, "hermes:ping_timeout", "ping_timeout"),
    (4100, "hermes:stop", "stop"),
    (4100, "SECRET-close-body", None),
    (1000, "hermes:ping_timeout", None),
    (1005, "", None),
])
def test_real_websocket_close_reason_reaches_existing_disconnect_owner(runtime, caplog, code, reason, reported):
    import uvicorn
    from websockets.asyncio.client import connect

    app = FastAPI()

    @app.websocket("/api/ws")
    async def route(ws: WebSocket):
        await ws_mod.handle_ws(ws)

    async def run():
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(4)
        port = listener.getsockname()[1]
        service = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="off", ws_ping_interval=None))
        serving = asyncio.create_task(service.serve(sockets=[listener]))
        try:
            while not service.started:
                await asyncio.sleep(.001)
            async with connect(f"ws://127.0.0.1:{port}/api/ws", close_timeout=1) as client:
                assert json.loads(await client.recv())["params"]["type"] == "gateway.ready"
                if code == 1005:
                    # 1005 is never transmitted: the wire control-frame payload is empty.
                    client.protocol.send_close()
                    client.send_data()
                else:
                    await client.close(code=code, reason=reason)
            async with asyncio.timeout(2):
                while not any(row["event"] == "closed" for row in records(caplog)):
                    await asyncio.sleep(.001)
        finally:
            service.should_exit = True
            await asyncio.wait_for(serving, 3)

    asyncio.run(run())
    closed = next(row for row in records(caplog) if row["event"] == "closed")
    assert closed["code"] == code
    assert closed["reason"] == "disconnect_observed"
    assert closed["initiator"] == ("peer" if reported else "unknown")
    assert closed.get("peer_reported_initiator") == reported
    assert "SECRET" not in caplog.text


def test_explicit_server_cause_keeps_priority_over_peer_claim(runtime, caplog):
    class PeerClose:
        async def accept(self):
            pass

        async def send_text(self, text):
            pass

        async def close(self, code=1000, reason=""):
            pass

        async def receive_text(self):
            runtime[0].abort(reason="fanout_overflow")
            raise WebSocketDisconnect(4100, "hermes:ping_timeout")

    asyncio.run(ws_mod.handle_ws(PeerClose()))
    closed = next(row for row in records(caplog) if row["event"] == "closed")
    assert closed["initiator"] == "server"
    assert closed["code"] == 1011
    assert closed["reason"] == "fanout_overflow"
    assert closed["peer_reported_initiator"] == "ping_timeout"
