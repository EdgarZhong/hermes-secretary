"""Burst, real-socket and content-free diagnostics contracts; no model or production I/O."""
from __future__ import annotations

import asyncio
import json
import logging
import socket
import time
import pytest
from fastapi import WebSocket

from tui_gateway import server
from tui_gateway.connection_diagnostics import ConnectionDiagnostics
from tui_gateway.transport import FanoutTransport
from tui_gateway.ws import WSTransport


def event(n, kind="reasoning.delta", text="x"):
    payload = {"text": text} if kind == "reasoning.delta" else {
        "source_event_seq": n - 1, "native_type": "reasoning.delta", "native_payload": {"text": text}}
    return {"jsonrpc": "2.0", "method": "event", "params": {
        "type": kind, "session_id": "audit", "seq": n, "payload": payload}}


class FastWS:
    def __init__(self):
        self.frames = []
        self.closed = []
        self.gate = None
        self.started = asyncio.Event()

    async def send_text(self, text):
        self.started.set()
        if self.gate is not None:
            await self.gate.wait()
        self.frames.append(json.loads(text))

    async def close(self, code=1000, reason=""):
        self.closed.append((code, reason))
        if self.gate is not None:
            self.gate.set()


async def drained(fan, peers, expected, timeout=5):
    async with asyncio.timeout(timeout):
        while any(len(peer.frames) < expected for peer in peers):
            await asyncio.sleep(.001)
    assert all(fan.contains(transport) for transport in fan.transports())


def test_healthy_unpaced_burst_keeps_every_legacy_and_typed_event(monkeypatch):
    from agent import async_utils
    schedule = async_utils.safe_schedule_threadsafe
    handoffs = []

    def measured(*args, **kwargs):
        handoffs.append(1)
        return schedule(*args, **kwargs)
    monkeypatch.setattr(async_utils, "safe_schedule_threadsafe", measured)

    async def run():
        sockets = [FastWS(), FastWS()]
        peers = [WSTransport(ws, asyncio.get_running_loop()) for ws in sockets]
        fan = FanoutTransport(*peers)

        def emit():
            for n in range(2000):
                assert fan.write(event(n, "reasoning.delta" if n % 2 == 0 else "message.output_delta"))
        await asyncio.to_thread(emit)
        await drained(fan, sockets, 2000)
        assert len(handoffs) < 500  # 4000 wire events use bounded batches, not 4000 round trips.
        print("burst_metrics", json.dumps({"wire_events": 4000, "worker_loop_handoffs": len(handoffs)}))
        assert not any(ws.closed for ws in sockets)
        for ws in sockets:
            assert [item["params"]["seq"] for item in ws.frames] == list(range(2000))
            assert all(item["params"]["payload"]["source_event_seq"] == n - 1
                       for n, item in enumerate(ws.frames) if n % 2)
        fan.close()
    asyncio.run(run())


@pytest.mark.parametrize("size", [5 * 1024 * 1024 // 2, 5 * 1024 * 1024])
def test_large_legacy_typed_pair_is_one_existing_event_slot_not_poison(size):
    async def run():
        sockets = [FastWS(), FastWS()]
        fan = FanoutTransport(*(WSTransport(ws, asyncio.get_running_loop()) for ws in sockets))
        text = "x" * size
        assert fan.write(event(0, text=text))
        assert fan.write(event(1, "message.output_delta", text))
        assert fan.write(event(2, text="tail"))
        await drained(fan, sockets, 3)
        assert all(not ws.closed and ws.frames[0]["params"]["payload"]["text"] == text for ws in sockets)
        assert all(ws.frames[-1]["params"]["seq"] == 2 for ws in sockets)
        fan.close()
    asyncio.run(run())


def test_sustained_slow_peer_is_byte_bounded_and_other_peer_keeps_streaming(monkeypatch):
    async def run():
        healthy, slow = FastWS(), FastWS()
        slow.gate = asyncio.Event()
        peers = [WSTransport(ws, asyncio.get_running_loop()) for ws in (healthy, slow)]
        fan = FanoutTransport(*peers)
        maximum = 0
        for n in range(100):
            assert fan.write(event(n, text="x" * (64 * 1024)))
            await drained(fan, [healthy], n + 1)
            with fan._lock:
                maximum = max([maximum, *(p.pending_bytes for p in fan._peers)])
            if slow.closed:
                break
        await asyncio.sleep(.01)
        assert slow.closed == [(1011, "fanout_overflow")]
        assert maximum <= fan._MAX_PENDING_BYTES
        assert not healthy.closed and fan.contains(peers[0]) and not fan.contains(peers[1])
        assert fan.write(event(n + 1))
        await drained(fan, [healthy], n + 2)
        fan.close()
    asyncio.run(run())


def test_recovery_send_lock_wait_does_not_misclassify_small_live_burst():
    async def run():
        ws = FastWS()
        peer = WSTransport(ws, asyncio.get_running_loop())
        fan = FanoutTransport(peer)
        await peer._send_lock.acquire()
        for n in range(1000):
            assert fan.write(event(n))
        await asyncio.sleep(.05)
        assert not ws.closed and not peer.closed
        peer._send_lock.release()
        await drained(fan, [ws], 1000)
        assert [item["params"]["seq"] for item in ws.frames] == list(range(1000))
        fan.close()
    asyncio.run(run())


def test_detach_reattach_cannot_replay_unsent_tail_of_old_batch():
    async def run():
        ws = FastWS()
        ws.gate = asyncio.Event()
        peer = WSTransport(ws, asyncio.get_running_loop())
        fan = FanoutTransport(peer)
        for n in range(100):
            assert fan.write(event(n))
        await asyncio.wait_for(ws.started.wait(), 1)  # later batch frames haven't been sent.
        assert fan.detach(peer) and fan.attach(peer)
        assert fan.write(event(100)) and fan.write(event(101))
        ws.gate.set()
        await drained(fan, [ws], 3)
        assert [item["params"]["seq"] for item in ws.frames] == [0, 100, 101]
        fan.close()
    asyncio.run(run())


@pytest.mark.parametrize("buffered_count", [1, 20])
def test_fanout_generation_fence_never_discards_other_session_buffered_tokens(monkeypatch, buffered_count):
    monkeypatch.setattr("tui_gateway.ws._TOKEN_COALESCE_S", 60)

    async def run():
        ws = FastWS()
        peer = WSTransport(ws, asyncio.get_running_loop())
        fan = FanoutTransport(peer)
        await peer._send_lock.acquire()
        for n in range(buffered_count):
            other = event(n)
            other["params"]["session_id"] = "other"
            assert peer.write(other)
        assert fan.write(event(0))
        async with asyncio.timeout(1):
            while peer._pending_tokens:
                await asyncio.sleep(0)
        # Current fanout is waiting for send_lock after taking the other
        # session's pre-existing tokens. Only its own old generation is stale.
        assert fan.detach(peer) and fan.attach(peer)
        later = event(buffered_count)
        later["params"]["session_id"] = "other"
        assert peer.write(later)
        assert fan.write(event(100))
        peer._send_lock.release()
        await drained(fan, [ws], buffered_count + 2, timeout=1)
        assert [(item["params"]["session_id"], item["params"]["seq"]) for item in ws.frames] == [
            *(("other", n) for n in range(buffered_count + 1)), ("audit", 100)]
        fan.close()
        peer.close()
    asyncio.run(run())


def test_same_socket_direct_prefix_cannot_be_overtaken_by_later_nonstream_event(monkeypatch):
    monkeypatch.setattr("tui_gateway.ws._TOKEN_COALESCE_S", 60)

    def other_event(seq, kind="reasoning.delta"):
        item = event(seq, text="prefix")
        item["params"]["session_id"] = "other"
        item["params"]["type"] = kind
        return item

    async def run():
        class ConcurrentWS(FastWS):
            async def send_text(self, text):
                await super().send_text(text)
                params = self.frames[-1]["params"]
                if params["session_id"] == "other" and params["seq"] == 15:
                    # A later, non-streaming write must not overtake the
                    # already-admitted prefix when fanout yields its own batch.
                    assert peer.write(other_event(20, "message.interim"))

        ws = ConcurrentWS()
        peer = WSTransport(ws, asyncio.get_running_loop())
        fan = FanoutTransport(peer)
        try:
            for n in range(20):
                assert peer.write(other_event(n))
            assert fan.write(event(0))
            await drained(fan, [ws], 22)
            observed = [item["params"]["seq"] for item in ws.frames
                        if item["params"]["session_id"] == "other"]
            print("same_socket_direct_order", observed)
            assert observed == list(range(21))
        finally:
            fan.close()
            peer.close()
    asyncio.run(run())


@pytest.mark.parametrize("failure", ["error", "timeout"])
def test_failed_atomic_prefix_never_sends_fanout_tail_or_reports_success(monkeypatch, failure):
    monkeypatch.setattr("tui_gateway.ws._TOKEN_COALESCE_S", 60)
    monkeypatch.setattr("tui_gateway.ws._WS_SEND_DEADLINE_S", .01)

    async def run():
        attempted = []

        class FailingWS(FastWS):
            async def send_text(self, text):
                attempted.append(json.loads(text)["params"]["session_id"])
                if failure == "error":
                    raise RuntimeError("send failed")
                await asyncio.Event().wait()

        ws = FailingWS()
        peer = WSTransport(ws, asyncio.get_running_loop())
        prefix = event(0)
        prefix["params"]["session_id"] = "other"
        assert peer.write(prefix)
        result = await peer.write_lines_async([json.dumps(event(100))], queued_at=time.monotonic(),
                                              is_current=lambda: True)
        await asyncio.sleep(0)
        assert result is False and attempted == ["other"]
        assert ws.closed == [(1011, "send_error" if failure == "error" else "send_deadline")]
        peer.close()
    asyncio.run(run())


def test_own_fanout_slices_yield_to_heartbeat_already_waiting_for_send_lock():
    async def run():
        replies = []

        class HeartbeatWS(FastWS):
            async def send_text(self, text):
                await super().send_text(text)
                params = self.frames[-1].get("params", {})
                if params.get("seq") == 15:
                    replies.append(asyncio.create_task(peer.write_async({
                        "jsonrpc": "2.0", "id": "heartbeat", "result": {"ok": True}})))

        ws = HeartbeatWS()
        peer = WSTransport(ws, asyncio.get_running_loop())
        fan = FanoutTransport(peer)
        try:
            for n in range(64):
                assert fan.write(event(n))
            await drained(fan, [ws], 65)
            await asyncio.gather(*replies)
            reply_at = next(n for n, item in enumerate(ws.frames) if item.get("id") == "heartbeat")
            assert 15 < reply_at <= 32
            assert [item["params"]["seq"] for item in ws.frames if "params" in item] == list(range(64))
        finally:
            fan.close()
            peer.close()
    asyncio.run(run())


@pytest.mark.parametrize("known_server_close", [False, True])
def test_close_diagnostics_keep_unobserved_code_unknown(monkeypatch, caplog, known_server_close):
    from tui_gateway import ws as ws_mod
    peers = []
    caplog.set_level(logging.INFO, logger="hermes_cli.web_server")
    for name in ("_ensure_skin_watcher", "_ensure_lease_watcher", "_start_backend_heartbeat_refresher",
                 "_schedule_startup_orphan_sweep", "_release_wake_for_transport"):
        monkeypatch.setattr(server, name, lambda *args: None)
    monkeypatch.setattr(server, "resolve_skin", lambda: {})
    monkeypatch.setattr(server, "register_live_transport", peers.append)
    monkeypatch.setattr(server, "_close_sessions_for_transport", lambda *args, **kwargs: (0, 0))
    monkeypatch.setattr(ws_mod, "_note_dashboard_client_activity", lambda **kwargs: None)

    class ReceiveFailure(FastWS):
        async def accept(self):
            pass

        async def receive_text(self):
            if known_server_close:
                peers[0].abort(reason="fanout_overflow")
                await asyncio.sleep(0)
            raise RuntimeError("receive failed")

    asyncio.run(ws_mod.handle_ws(ReceiveFailure()))
    records = [json.loads(record.message.split("connection_diagnostic ", 1)[1])
               for record in caplog.records if "connection_diagnostic " in record.message]
    closed = next(record for record in records if record["event"] == "closed")
    assert closed.get("code") == (1011 if known_server_close else None)
    assert closed["initiator"] == ("server" if known_server_close else "unknown")


def test_second_unrelated_large_event_cannot_accumulate_behind_slow_peer():
    async def run():
        healthy, slow = FastWS(), FastWS()
        slow.gate = asyncio.Event()
        peers = [WSTransport(ws, asyncio.get_running_loop()) for ws in (healthy, slow)]
        fan = FanoutTransport(*peers)
        text = "x" * (5 * 1024 * 1024)
        assert fan.write(event(0, text=text))
        await drained(fan, [healthy], 1)
        assert fan.write(event(2, text=text))
        await drained(fan, [healthy], 2)
        await asyncio.sleep(.01)
        assert slow.closed == [(1011, "fanout_overflow")]
        assert not healthy.closed
        assert [item["params"]["seq"] for item in healthy.frames] == [0, 2]
        fan.close()
    asyncio.run(run())


def test_diagnostics_are_correlated_whitelisted_and_fail_open(caplog, monkeypatch):
    caplog.set_level(logging.INFO, logger="hermes_cli.web_server")
    diag = ConnectionDiagnostics("a" * 32)
    diag.log("queue_overflow", reason="fanout_overflow", event_type="reasoning.delta",
             pending_frames=257, frame_bytes=123, text="SECRET", url="https://SECRET", params={"SECRET": 1})
    diag.log("closed", reason="SECRET", initiator="SECRET")
    assert "SECRET" not in caplog.text
    records = [json.loads(record.message.split("connection_diagnostic ", 1)[1]) for record in caplog.records]
    assert records[0]["client_connection_id"] == "a" * 32
    assert len(records[0]["connection_id"]) == 32
    assert records[0]["pending_frames"] == 257
    assert "reason" not in records[1]
    assert ConnectionDiagnostics("https://SECRET").client_connection_id is None
    monkeypatch.setattr("tui_gateway.connection_diagnostics._log.log", lambda *args: (_ for _ in ()).throw(OSError()))
    diag.log("health")
    assert diag.errors == 1


def test_real_loopback_two_clients_stream_recovery_and_heartbeat(monkeypatch):
    import uvicorn
    from fastapi import FastAPI
    from websockets.asyncio.client import connect
    from tui_gateway import ws as ws_mod

    peers = []
    for name in ("_ensure_skin_watcher", "_ensure_lease_watcher", "_start_backend_heartbeat_refresher",
                 "_schedule_startup_orphan_sweep", "_release_wake_for_transport"):
        monkeypatch.setattr(server, name, lambda *args: None)
    monkeypatch.setattr(server, "resolve_skin", lambda: {})
    monkeypatch.setattr(server, "register_live_transport", peers.append)
    monkeypatch.setattr(server, "_close_sessions_for_transport", lambda *args, **kwargs: (0, 0))
    monkeypatch.setattr(ws_mod, "_note_dashboard_client_activity", lambda **kwargs: None)
    monkeypatch.setattr(server, "dispatch", lambda req, transport: {
        "jsonrpc": "2.0", "id": req["id"], "result": {"recovered": "x" * (256 * 1024)}})
    app = FastAPI()

    @app.websocket("/api/ws")
    async def route(ws: WebSocket):
        await ws_mod.handle_ws(ws)

    async def run():
        listener = socket.socket()
        listener.bind(("127.0.0.1", 0))
        listener.listen(16)
        port = listener.getsockname()[1]
        service = uvicorn.Server(uvicorn.Config(app, log_level="error", lifespan="off", ws_ping_interval=None))
        service.install_signal_handlers = lambda: None
        serving = asyncio.create_task(service.serve(sockets=[listener]))
        try:
            while not service.started:
                await asyncio.sleep(.001)
            async with connect(f"ws://127.0.0.1:{port}/api/ws?client_connection_id={'a' * 32}", max_size=None) as one, \
                    connect(f"ws://127.0.0.1:{port}/api/ws", max_size=None) as two:
                ready = [json.loads(await client.recv())["params"]["payload"] for client in (one, two)]
                assert ready[0]["client_connection_id"] == "a" * 32
                assert ready[1]["client_connection_id"] is None
                assert ready[0]["connection_id"] != ready[1]["connection_id"]
                fan = FanoutTransport(*peers)
                count = 1200

                async def receive(client):
                    seq, replies = [], set()
                    ping_elapsed = None
                    async with asyncio.timeout(10):
                        while len(seq) < count or len(replies) < 2:
                            item = json.loads(await client.recv())
                            if "id" in item:
                                replies.add(item["id"])
                                if item["id"] == "ping":
                                    ping_elapsed = time.monotonic() - started
                            else:
                                seq.append(item["params"]["seq"])
                    return seq, replies, ping_elapsed

                readers = [asyncio.create_task(receive(client)) for client in (one, two)]
                started = time.monotonic()
                for client in (one, two):
                    await client.send(json.dumps({"id": "recover", "method": "audit.recover", "params": {}}))
                    await client.send(json.dumps({"id": "ping", "method": "gateway.ping", "params": {}}))

                def burst(lo, hi):
                    for n in range(lo, hi):
                        assert fan.write(event(n, "reasoning.delta" if n % 2 == 0 else "message.output_delta"))

                await asyncio.to_thread(burst, 0, 1000)
                # A subsequent paced stream runs without per-frame receipts.
                for lo in range(1000, count, 2):
                    await asyncio.to_thread(burst, lo, lo + 2)
                    await asyncio.sleep(.025)  # ~40 logical chunks / 80 wire frames per second.
                results = await asyncio.gather(*readers)
                for sequence, replies, ping_elapsed in results:
                    assert sequence == list(range(count))
                    assert replies == {"recover", "ping"}
                    assert ping_elapsed < 2
                print("loopback_metrics", json.dumps({"events_per_client": count,
                      "elapsed_seconds": time.monotonic() - started,
                      "ping_seconds": [result[2] for result in results]}))
                assert time.monotonic() - started < 6
                assert all(not peer.closed for peer in peers)
                fan.close()
        finally:
            service.should_exit = True
            await asyncio.wait_for(serving, 5)
            listener.close()
    asyncio.run(run())
