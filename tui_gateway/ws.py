"""WebSocket transport for the tui_gateway JSON-RPC server: reuses :func:`tui_gateway.server.dispatch`
verbatim so every RPC, slash command, approval flow and agent event takes the same handlers as Ink over
stdio. Wire protocol is identical to stdio (newline-delimited JSON-RPC both ways; ``gateway.ready`` right
after accept). Mount as ``@app.websocket("/api/ws") async def ws(ws): await handle_ws(ws)``."""

from __future__ import annotations

import asyncio
import contextlib
import concurrent.futures
import json
import logging
import socket
import threading
import time
from typing import Any

from tui_gateway import server
from agent.message_sanitization import _sanitize_surrogates
from tui_gateway.event_replay import replay_epoch
from tui_gateway.transport import serialize_frame
from tui_gateway.connection_diagnostics import ConnectionDiagnostics, close_initiator, ensure_loop_probe, peer_reported_initiator

_log = logging.getLogger(__name__)

# Scale-to-zero: tell the (separate) gateway process a dashboard/desktop/TUI client is attached via
# the mtime of a marker file it reads in its idle predicate (gateway/scale_to_zero.py). Clients ping
# every 15s; one write per 5s per process is plenty.
_DASHBOARD_CLIENT_TOUCH_MIN_INTERVAL_S = 5.0
_dashboard_client_touched_at = 0.0
_dashboard_client_touch_lock = threading.Lock()


def _note_dashboard_client_activity(*, force: bool = False) -> None:
    """Refresh the dashboard-client liveness marker (throttled, best-effort)."""
    global _dashboard_client_touched_at
    now = time.monotonic()
    with _dashboard_client_touch_lock:
        if not force and now - _dashboard_client_touched_at < _DASHBOARD_CLIENT_TOUCH_MIN_INTERVAL_S:
            return
        _dashboard_client_touched_at = now
    try:
        from gateway.scale_to_zero import touch_dashboard_client_heartbeat
        touch_dashboard_client_heartbeat()
    except Exception:  # noqa: BLE001 - liveness garnish must never break the WS
        _log.debug("dashboard client heartbeat touch failed", exc_info=True)


def _sanitize_ws_text(text: str) -> str:
    """Return *text* that can be UTF-8 encoded for a WebSocket frame.

    ``json.dumps(..., ensure_ascii=False)`` happily emits lone UTF-16 surrogates; Starlette's
    ``send_text`` then raises ``UnicodeEncodeError``, which used to latch the whole connection
    closed. Same U+FFFD replacement every other Hermes transport applies.

    See #97288.
    """
    return _sanitize_surrogates(text) if text else text


# Max seconds a pool-dispatched handler blocks waiting for the loop to flush a WS frame before we
# give up waiting (the transport is NOT marked dead).
_WS_WRITE_TIMEOUT_S = 10.0
# Max seconds one send_text may await the socket once it is actually running on the loop. A healthy
# socket usually returns immediately. This bounds elapsed send time, which can include loop lag;
# diagnostics record loop scheduling separately rather than asserting the network is at fault. 3x the worker wait
# above and under the client's 45s heartbeat deadline (apps/shared json-rpc-gateway): a peer that
# cannot drain ~48 KiB in 30s is gone, and closing here starts its reconnect instead of leaving every
# later frame and RPC reply parked behind the writer lock (#106369).
_WS_SEND_DEADLINE_S = 30.0
# Frames read ahead of a busy dispatcher. RPCs still dispatch one at a time in arrival order, but on a
# per-connection task so the read loop keeps answering gateway.ping while a handler blocks (a lock held
# by a long compaction, a GIL-heavy turn): the client's heartbeat deadline measures the transport, not
# handler latency (#108325). A full queue parks the reader — the old serial behaviour.
_WS_DISPATCH_QUEUE_MAX = 256

# Per-token streaming frames are coalesced: buffered and flushed as a batch on a short timer instead
# of waking the loop once per token (each wakeup competes with the agent turn for the GIL). Keep this
# set to genuinely high-frequency, display-only events — anything a client must see promptly
# (tool/approval/status/completion) is non-streaming and flushes the buffer ahead of itself, so
# ordering is preserved. _TOKEN_COALESCE_S: max buffer wait (~30 fps; imperceptible).
_STREAMING_EVENT_TYPES = frozenset({"message.delta", "reasoning.delta", "thinking.delta"})
_TOKEN_COALESCE_S = 0.033

# starlette stays optional at import time; fall back to a generic sentinel.
try:
    from starlette.websockets import WebSocketDisconnect as _WebSocketDisconnect
except ImportError:  # pragma: no cover - starlette is a required install path
    _WebSocketDisconnect = Exception  # type: ignore[assignment]


class WSTransport:
    """Per-connection WS transport. ``write`` is safe from any thread *other than* the loop thread owning the
    socket (pool workers marshal onto the loop and block on the future); from the loop thread itself it would
    deadlock, so it detects that and fires-and-forgets. Loop-thread callers needing completion use ``write_async``."""

    def __init__(self, ws: Any, loop: asyncio.AbstractEventLoop, *, peer: str = "unknown",
                 auth_identity: dict | None = None, client_connection_id=None) -> None:
        self._ws = ws
        self._loop = loop
        self._peer = peer
        self.diagnostics = ConnectionDiagnostics(client_connection_id)
        ensure_loop_probe(loop)
        self._close_reason = None
        self._close_code = None
        #: Server-verified identity from the WS-upgrade credential, stamped by ``web_server_chat._ws_auth_reason``; None
        #: for legacy-token/stdio. RPC params can never populate it: sole identity authority for browser controllers
        #: and for the ``user_id`` the agent is built with (``server._session_auth_user_id``).
        self.auth_identity = auth_identity
        self._closed = False
        # Token-coalescing buffer. The lock guards the buffer + "armed" flag against worker threads
        # calling write(); the timer handle is only ever touched on the loop thread.
        self._token_lock = threading.Lock()
        self._pending_tokens: list[str] = []
        self._token_flush_handle: asyncio.TimerHandle | None = None
        self._token_flush_armed = False
        # Socket writes need an async boundary: several batches can queue on the loop during a stall.
        self._send_lock = asyncio.Lock()
        self._abort_requested = False

    def _on_loop(self) -> bool:
        try:
            return asyncio.get_running_loop() is self._loop
        except RuntimeError:
            return False

    def write(self, obj: dict) -> bool:
        return self.write_ordered(obj)

    def write_ordered(self, obj: dict, prepare=None) -> bool:
        """Commit seq/projection and token/batch admission under the existing token owner.

        Preparation only records replay/inflight metadata; all socket waiting stays outside.
        """
        on_loop = self._on_loop()
        # Streamed token: buffer it and arm the flush timer; the worker returns immediately.
        # call_soon_threadsafe is safe from a worker or the loop.
        with self._token_lock:
            if prepare is not None:
                prepare()
            # A closed peer still records the native event for recovery through prepare.
            if self._closed:
                return False
            line = serialize_frame(obj, self._peer, _log)
            params = obj.get("params") if isinstance(obj, dict) else None
            if isinstance(params, dict) and params.get("type") in _STREAMING_EVENT_TYPES:
                self._pending_tokens.append(line)
                if not self._token_flush_armed:
                    self._token_flush_armed = True
                    self._loop.call_soon_threadsafe(self._arm_token_flush)
                return not self._closed
            # Non-streaming frames flush the buffered prefix in the same admission order.
            # Schedule inside the lock so the timer cannot overtake this batch.
            self._pending_tokens.append(line)
            batch, self._pending_tokens = self._pending_tokens, []
            fut = self._schedule_send_many(batch)
            if fut is None:
                return False
            if on_loop:
                return True
        try:
            fut.result(timeout=_WS_WRITE_TIMEOUT_S)
            return not self._closed
        except concurrent.futures.TimeoutError:  # builtin TimeoutError on 3.11+
            # Waiting on the loop/send lock is not proof of a dead socket. Leave
            # the scheduled frame in flight; actual send failures own closure.
            self.diagnostics.log("write_wait", queue_wait_ms=_WS_WRITE_TIMEOUT_S * 1000)
            return not self._closed
        except (OSError, RuntimeError, concurrent.futures.CancelledError):
            self._closed = True
            self.diagnostics.log("send_error", reason="send_error")
            return False

    def _arm_token_flush(self) -> None:  # loop thread
        if not self._closed:
            self._token_flush_handle = self._loop.call_later(_TOKEN_COALESCE_S, self._flush_tokens)

    def _schedule_send_many(self, lines, **kwargs):
        """Called under the token lock: one FIFO callback path for workers and loop callers.

        Creating a task directly on the loop could overtake a worker callback that has been
        admitted but has not yet created its task. No network IO or waiting happens here.
        """
        from agent.async_utils import safe_schedule_threadsafe
        future = safe_schedule_threadsafe(self._safe_send_many(lines, **kwargs), self._loop)
        if future is None:
            self._closed = True
        return future

    def _flush_tokens(self) -> None:
        """Timer callback (loop thread): send buffered tokens as one batch, scheduled under the lock so
        wire order is fixed relative to a concurrent ``write``."""
        with self._token_lock:
            self._token_flush_handle = None
            self._token_flush_armed = False
            batch, self._pending_tokens = self._pending_tokens, []
            if batch and not self._closed:
                self._schedule_send_many(batch)

    @property
    def closed(self) -> bool:
        return self._closed

    async def write_async(self, obj: dict) -> bool:
        """Send from the owning loop; awaits until the frame is on the wire. Buffered tokens are flushed
        ahead of it in the SAME batch so nothing slips between."""
        if self._closed:
            return False
        with self._token_lock:
            batch, self._pending_tokens = self._pending_tokens, []
            batch.append(serialize_frame(obj, self._peer, _log))
            future = self._schedule_send_many(batch)
        if future is not None:
            await asyncio.wrap_future(future)
        return not self._closed

    async def write_lines_async(self, lines: list[str], *, queued_at: float, is_current=None) -> bool:
        """Flush one bounded fanout batch with one worker→loop handoff; each wire event stays intact."""
        if self._closed:
            return False
        with self._token_lock:
            prefix, self._pending_tokens = self._pending_tokens, []
            # The first batch shares direct writes' FIFO scheduling boundary, including
            # an old direct write already stamped when its session became a fanout.
            first = prefix or lines[:16]
            future = (self._schedule_send_many(first, queued_at=None if prefix else queued_at,
                                              is_current=None if prefix else is_current) if first else None)
        # Other direct-session owners have already admitted this prefix. Flush
        # it atomically under one lock tenure, with no fanout membership fence:
        # releasing midway lets their later non-token write overtake its tail.
        if future is not None:
            await asyncio.wrap_future(future)
        if self._closed:
            return False
        if not prefix and first:
            await asyncio.sleep(0)
        # The fanout owner has only one in-flight batch per session/peer. Slice
        # its lock tenure so unrelated RPC/heartbeat replies get a fair turn,
        # without another worker↔loop handoff or reordering that session's events.
        for offset in range(0 if prefix else 16, len(lines), 16):
            await self._safe_send_many(lines[offset:offset + 16], queued_at=queued_at, is_current=is_current)
            if self._closed:
                return False
            await asyncio.sleep(0)
        return not self._closed

    async def _safe_send_many(self, lines: list[str], *, queued_at: float | None = None, is_current=None) -> None:
        """Send one indivisible batch of pre-serialized frames in wire order."""
        async with self._send_lock:
            if self._closed:
                return
            for line in lines:
                if self._closed or (is_current is not None and not is_current()):
                    return
                payload = _sanitize_ws_text(line)
                started = time.monotonic()
                wait_ms = (started - queued_at) * 1000 if queued_at is not None else 0.0
                try:
                    await asyncio.wait_for(self._ws.send_text(payload), timeout=_WS_SEND_DEADLINE_S)
                except asyncio.TimeoutError:
                    # Bound this send without attributing it to the network:
                    # elapsed time may include loop starvation. Close/replay
                    # remains necessary; separate loop diagnostics retain the distinction.
                    self.diagnostics.log("send_timeout", reason="send_deadline", frame_bytes=len(payload.encode("utf-8")),
                                         send_ms=(time.monotonic() - started) * 1000,
                                         queue_wait_ms=wait_ms, loop_lag_ms=self._loop_lag_ms())
                    self.abort(reason="send_deadline")
                    return
                except UnicodeEncodeError:
                    # A single illegal UTF-8 frame (lone surrogate) must not tear down the socket.
                    self.diagnostics.log("send_error", reason="send_error")
                    continue
                except (OSError, RuntimeError, ValueError, _WebSocketDisconnect):
                    # Latch while holding the writer lock so queued batches observe the failure first.
                    self.diagnostics.log("send_error", reason="send_error")
                    self.abort(reason="send_error")
                    return
                self.diagnostics.sent(len(payload.encode("utf-8")), wait_ms,
                                      (time.monotonic() - started) * 1000, self._loop_lag_ms())
                self.diagnostics.health()

    def _loop_lag_ms(self) -> float:
        return getattr(self._loop, "_hermes_connection_lag_ms", 0.0)

    def close(self) -> None:  # loop thread (handle_ws finally), so the TimerHandle is safe
        self._closed = True
        if self._token_flush_handle is not None:
            self._token_flush_handle.cancel()
            self._token_flush_handle = None

    def abort(self, *, reason="fanout_overflow") -> None:
        """Close from any thread and drop the socket with 1011 so the client reconnects and replays
        (fanout overflow). One-shot: N mirrored sessions overflowing on this socket schedule one close."""
        self._closed = True
        with self._token_lock:
            if self._abort_requested:
                return
            self._abort_requested = True
            self._close_reason, self._close_code = reason, 1011
        self.diagnostics.log("close_requested", initiator="server", reason=reason, code=1011)
        if self._on_loop():
            self._finish_abort()
            return
        # A loop that already shut down has nothing left to cancel or close.
        with contextlib.suppress(RuntimeError):
            self._loop.call_soon_threadsafe(self._finish_abort)

    def _finish_abort(self) -> None:  # loop thread
        self.close()
        self._loop.create_task(self._close_socket(1011, self._close_reason or "unknown"))

    async def _close_socket(self, code: int, reason: str) -> None:
        """Close the peer socket so ``handle_ws``'s ``receive_text`` unblocks and its disconnect teardown
        runs. The server library bounds this (websockets ``close_timeout`` → abort)."""
        try:
            await self._ws.close(code=code, reason=reason)
        except Exception as exc:  # noqa: BLE001 - the peer is already gone; teardown is what matters
            _log.debug("ws close after %s failed peer=%s error=%s", reason, self._peer, exc)


def _ws_peer_label(ws: Any) -> str:
    """``host:port`` when available, else a stable placeholder."""
    client = getattr(ws, "client", None)
    if client is None:
        return "unknown"
    host, port = getattr(client, "host", None) or "unknown", getattr(client, "port", None)
    return f"{host}:{port}" if port is not None else host


def _disable_nagle(ws: Any) -> None:
    """Disable Nagle + enable TCP keepalive on the raw socket (best-effort). Without TCP_NODELAY the kernel
    coalesces small per-token frames, so a burst after the model's think-pause lands in one tick and no
    client-side smoothing can recover the cadence. Without keepalive a silently-dropped client (SSH tunnel
    reset, sleep) leaves the leg half-open forever: receive_text() blocks and the disconnect teardown never runs."""
    try:
        scope = getattr(ws, "scope", None) or {}
        transport = (scope.get("extensions") or {}).get("transport") or getattr(ws, "transport", None)
        sock = transport.get_extra_info("socket") if transport is not None else None
        if sock is not None:
            sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_KEEPALIVE, 1)
            if hasattr(socket, "TCP_KEEPIDLE"):  # Linux
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPIDLE, 30)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPINTVL, 10)
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPCNT, 3)
            elif hasattr(socket, "TCP_KEEPALIVE"):  # macOS idle seconds
                sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_KEEPALIVE, 30)
    except Exception as exc:  # pragma: no cover - best-effort tuning
        _log.debug("ws TCP_NODELAY skip: %s", exc)


class _SendFailed(Exception):
    """Raised by handle_ws._reply when a reply could not be written: ends the read loop."""


async def _close_ws_after_disconnect(ws, shutting_down: bool, peer: str) -> None:
    try:
        if shutting_down:
            await ws.close(code=1001, reason="server_shutdown")
        else:
            await ws.close()
    except (OSError, RuntimeError, TypeError, _WebSocketDisconnect):
        _log.debug("ws final close failed peer=%s", peer)


async def handle_ws(ws: Any, *, auth_identity: dict | None = None, subprotocol: str | None = None) -> None:
    """Run one WebSocket session. Wire-compatible with ``tui_gateway.entry``. *auth_identity* is the server-minted
    ``{user_id, provider}`` recorded at WS-upgrade auth, stored as ``WSTransport.auth_identity`` (the only identity
    authority for browser-controller registration); callers that omit it (harnesses, embedded TUI child) get None."""
    peer, transport = _ws_peer_label(ws), None
    messages = parse_errors = dispatch_crashes = send_failures = 0
    disconnect_reason = "not_connected"
    disconnect_code = None
    peer_initiator = None

    async def _reply(frame: dict, reason: str, msg: str, *args: Any) -> None:
        """write_async; on failure record *reason*, log *msg* and end the read loop."""
        nonlocal disconnect_reason, send_failures
        if not await transport.write_async(frame):
            disconnect_reason = reason
            send_failures += 1
            _log.warning("ws reply failed peer=%s reason=%s", peer, reason)
            raise _SendFailed

    def _error(code: int, message: str, req_id: Any) -> dict:
        return {"jsonrpc": "2.0", "error": {"code": code, "message": message}, "id": req_id}

    pending: asyncio.Queue = asyncio.Queue(maxsize=_WS_DISPATCH_QUEUE_MAX)
    dispatcher: asyncio.Task | None = None
    stop = object()  # queue sentinel; a JSON ``null`` frame parses to None, so None can't be it

    async def _dispatch_loop() -> None:
        """Dispatch queued requests one at a time in arrival order until the ``stop`` sentinel."""
        nonlocal dispatch_crashes
        while (req := await pending.get()) is not stop:
            req_id = req.get("id") if isinstance(req, dict) else None
            req_method = req.get("method") if isinstance(req, dict) else None
            # dispatch() may schedule long handlers on the pool; it returns None then and the worker
            # writes the response itself via transport.write (a separate thread, so that is the safe
            # path). Inline handlers return the response dict, written here from the loop.
            try:
                resp = await asyncio.to_thread(server.dispatch, req, transport)
            except Exception:
                dispatch_crashes += 1
                _log.error("ws dispatch crash peer=%s", peer)
                await _reply(_error(-32603, "internal error", req_id), "send_failed_after_dispatch_crash",
                             "ws dispatch-crash reply send failed peer=%s id=%s method=%s", peer, req_id, req_method)
                continue
            if resp is not None:
                await _reply(resp, "send_failed_after_response",
                             "ws response send failed peer=%s id=%s method=%s", peer, req_id, req_method)

    async def _unless_dispatch_failed(aw: Any) -> Any:
        """Await *aw*, or raise _SendFailed once the dispatcher has ended on a reply it could not send."""
        assert dispatcher is not None
        step = asyncio.ensure_future(aw)
        try:
            await asyncio.wait({step, dispatcher}, return_when=asyncio.FIRST_COMPLETED)
            if step.done():
                return step.result()
            raise _SendFailed
        finally:
            step.cancel()  # no-op once done

    try:
        await (ws.accept(subprotocol=subprotocol) if subprotocol else ws.accept())
        disconnect_reason = "connected"
        # Mark the client attached before the (possibly slow) ready/skin setup so scale-to-zero sees it.
        _note_dashboard_client_activity(force=True)
        _disable_nagle(ws)
        _log.info("ws accepted peer=%s", peer)
        client_id = getattr(ws, "query_params", {}).get("client_connection_id")
        transport = WSTransport(ws, asyncio.get_running_loop(), peer=peer, auth_identity=auth_identity,
                                client_connection_id=client_id)
        transport.diagnostics.log("accepted", client_id_valid=transport.diagnostics.client_connection_id is not None)
        # resolve_skin() is sync I/O + CPU; pooled so the read loop can drain the frontend's initial RPC burst.
        skin_payload = await asyncio.to_thread(server.resolve_skin)
        # change_events: this backend broadcasts pet/cron/sessions.changed, so clients can demote legacy
        # polls to backstops. replay_epoch lets reconnecting clients detect a backend restart and reset
        # their per-session seq watermarks (event_replay).
        ready_ok = await transport.write_async({
            "jsonrpc": "2.0", "method": "event",
            "params": {"type": "gateway.ready", "payload": {
                "skin": skin_payload, "change_events": True, "heartbeat": True, "replay_epoch": replay_epoch(),
                "connection_id": transport.diagnostics.connection_id,
                "client_connection_id": transport.diagnostics.client_connection_id,
                "web_controlled_input": 1,
            }},
        })
        if ready_ok:
            transport.diagnostics.log("ready")
            # Live-apply skins Hermes activates mid-conversation, and track this peer for session-less
            # global broadcasts write_json can't route.
            server._ensure_skin_watcher()
            server._ensure_lease_watcher()  # cross-process lease moves → display.lease
            server.register_live_transport(transport)
        # Cross-backend liveness: a heartbeat row lets the startup orphan sweep tell "live but idle
        # backend" from "truly orphaned". Idempotent and once-per-process, like the orphan sweep (the
        # desktop app and web dashboard reach the agent via this sidecar, not entry.main()).
        for start, what in (
            (server._start_backend_heartbeat_refresher, "backend heartbeat refresher start"),
            (server._schedule_startup_orphan_sweep, "startup orphan sweep scheduling"),
        ):
            try:
                start()
            except Exception:
                _log.warning("%s failed", what, exc_info=True)
        if not ready_ok:
            disconnect_reason = "ready_send_failed"
            send_failures += 1
            _log.error("ws ready frame send failed peer=%s", peer)
            return

        dispatcher = asyncio.create_task(_dispatch_loop())
        while True:
            try:
                raw = await _unless_dispatch_failed(ws.receive_text())
                _note_dashboard_client_activity()
            except _SendFailed:
                raise
            except _WebSocketDisconnect as exc:
                disconnect_code = getattr(exc, "code", None)
                peer_initiator = peer_reported_initiator(disconnect_code, getattr(exc, "reason", None))
                disconnect_reason = f"client_disconnect(code={disconnect_code})"
                break
            except Exception:
                disconnect_reason = "receive_failed"
                _log.exception("ws receive failed peer=%s", peer)
                break
            line = raw.strip()
            if not line:
                continue
            messages += 1
            try:
                req = json.loads(line)
            except json.JSONDecodeError:
                parse_errors += 1
                _log.warning("ws parse error peer=%s index=%d", peer, messages)
                await _reply(_error(-32700, "parse error", None), "send_failed_after_parse_error",
                             "ws parse-error reply send failed peer=%s", peer)
                continue
            if isinstance(req, dict) and req.get("method") == "gateway.ping":
                req_id = req.get("id")
                await _reply({"jsonrpc": "2.0", "result": {"ok": True}, "id": req_id}, "send_failed_after_heartbeat",
                             "ws heartbeat reply send failed peer=%s id=%s", peer, req_id)
                continue
            await _unless_dispatch_failed(pending.put(req))
    except _SendFailed:
        pass
    finally:
        shutting_down = asyncio.current_task().cancelling() > 0
        if dispatcher is not None:
            # Finish the in-flight handler and the frames read before the disconnect (as the serial read loop
            # did) before the teardown below parks this transport's sessions. A cancelled connection (server
            # shutdown) stops at once instead, as the read loop's cancelled await did.
            task = asyncio.current_task()
            if task is not None and task.cancelling():
                dispatcher.cancel()
            else:
                with contextlib.suppress(_SendFailed):
                    await _unless_dispatch_failed(pending.put(stop))
            await asyncio.wait({dispatcher})
            failure = None if dispatcher.cancelled() else dispatcher.exception()
            if failure is not None and not isinstance(failure, _SendFailed):
                _log.error("ws dispatcher failed peer=%s", peer, exc_info=failure)
        reaped_sessions = detached_sessions = 0
        if transport is not None:
            transport.diagnostics.health(force=True)
            reason = transport._close_reason or ("server_shutdown" if shutting_down else "disconnect_observed")
            transport.diagnostics.log("closed", reason=reason,
                                      initiator=close_initiator(bool(transport._close_reason or shutting_down), peer_initiator),
                                      peer_reported_initiator=peer_initiator,
                                      code=transport._close_code or disconnect_code or (1001 if shutting_down else None), messages=messages,
                                      parse_errors=parse_errors, dispatch_crashes=dispatch_crashes,
                                      send_failures=send_failures)
            server.unregister_live_transport(transport)
            # Owner-safely park browser controllers this transport registered (a same-identity reconnect may
            # deliver a terminal result for in-flight work). Offloaded: disconnect takes the controller's
            # send_lock, which a worker-thread dispatch may hold while blocking on THIS loop to transmit.
            try:
                from gateway.browser_control_broker import get_browser_control_broker
                await asyncio.to_thread(get_browser_control_broker().disconnect_owner, transport)
            except Exception:
                _log.exception("ws browser-controller disconnect failed peer=%s", peer)
            transport.close()
            try:
                await asyncio.to_thread(server._release_wake_for_transport, transport)
            except Exception:
                _log.exception("ws wake-word teardown failed peer=%s", peer)
            # The single WS-disconnect teardown path: reap sessions this transport owned (close_on_disconnect
            # sidecars) or detach the rest to the drop sentinel so later emits don't hit a closed socket; detached
            # ones go to the grace-windowed orphan reaper (a quick resume cancels it). Offloaded: worker.close()
            # blocks (terminate + waits) plus a sync DB write, which inline would freeze the loop for every peer.
            try:
                reaped_sessions, detached_sessions = await asyncio.to_thread(
                    server._close_sessions_for_transport, transport, end_reason="ws_disconnect"
                )
            except Exception:
                _log.exception("ws transport teardown failed peer=%s", peer)
        await _close_ws_after_disconnect(ws, shutting_down, peer)
        _log.info(
            "ws closed peer=%s reason=%s messages=%d parse_errors=%d "
            "dispatch_crashes=%d send_failures=%d reaped_sessions=%d detached_sessions=%d",
            peer, disconnect_reason, messages, parse_errors, dispatch_crashes, send_failures, reaped_sessions, detached_sessions,
        )
