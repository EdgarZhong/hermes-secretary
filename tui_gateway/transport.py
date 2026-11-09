"""Transport abstraction for the tui_gateway JSON-RPC server.

A :class:`Transport` forwards a JSON-serialisable dict to its peer, so one dispatcher runs over stdio
(``tui_gateway.entry``) or WebSocket (``tui_gateway.ws``). The request's transport lives in a
``ContextVar`` so pool-dispatched handlers write to the right peer; with nothing bound
``server.write_json`` falls back to the module-level :class:`StdioTransport`, which resolves
``_real_stdout`` lazily so tests that monkey-patch it keep working.
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
import contextlib
import contextvars
import errno
import json
import logging
import os
import threading
import time
from itertools import chain
from typing import Any, Callable, Optional, Protocol, runtime_checkable

# Errno values that mean "the peer is gone" rather than "the host has a real I/O problem". Anything
# outside this set re-raises so it surfaces in the crash log instead of looking like a clean disconnect.
_PEER_GONE_ERRNOS = frozenset({
    errno.EPIPE, errno.ECONNRESET, errno.EBADF, errno.ESHUTDOWN,
    getattr(errno, "WSAECONNRESET", -1), getattr(errno, "WSAESHUTDOWN", -1),  # win32 (no-op on POSIX)
} - {-1})

logger = logging.getLogger(__name__)

# When true, StdioTransport skips ``stream.flush`` after writing: on a half-closed pipe (TUI Node parent quit
# while the gateway still emits) flush can block long enough to starve the worker pool. Python text stdout is
# fully buffered on a pipe, so this ONLY makes sense with ``-u``/``PYTHONUNBUFFERED=1``; otherwise the TUI hangs.
_DISABLE_FLUSH = (os.environ.get("HERMES_TUI_GATEWAY_NO_FLUSH", "") or "").strip().lower() in {"1", "true", "yes", "on"}

@runtime_checkable
class Transport(Protocol):
    """Minimal interface every transport implements."""

    def write(self, obj: dict) -> bool:
        """Emit one JSON frame. Return ``False`` when the peer is gone."""

    def close(self) -> None:
        """Release any resources owned by this transport."""


_current_transport: contextvars.ContextVar[Optional[Transport]] = contextvars.ContextVar(
    "hermes_gateway_transport", default=None
)


def current_transport() -> Optional[Transport]:
    return _current_transport.get()


def bind_transport(transport: Optional[Transport]):
    """Bind *transport* for the current context; returns a token for :func:`reset_transport`."""
    return _current_transport.set(transport)


def reset_transport(token) -> None:
    _current_transport.reset(token)


def _raise_unless_peer_gone(exc: Exception, what: str) -> None:
    """Return when *exc* from a stream write/flush means the peer is gone; re-raise anything else.
    ``False`` from :meth:`StdioTransport.write` is the dispatcher's "broken stdout pipe" signal (``entry.py``
    exits cleanly on it), so programming errors and real host I/O bugs (UnicodeEncodeError from a misconfigured
    locale, ENOSPC, EACCES, ...) MUST re-raise so the crash log records them instead of masquerading as a clean
    disconnect. Peer-gone: BrokenPipeError, ValueError("...closed file..."), OSError errno in _PEER_GONE_ERRNOS."""
    if isinstance(exc, BrokenPipeError):
        return
    if isinstance(exc, ValueError):
        if isinstance(exc, UnicodeEncodeError) or "closed file" not in str(exc):
            raise exc
        return
    if not isinstance(exc, OSError) or exc.errno not in _PEER_GONE_ERRNOS:
        raise exc
    logger.debug("StdioTransport %s peer gone: %s", what, exc)


def serialize_frame(obj: dict, peer: str, log: logging.Logger) -> str:
    """``json.dumps`` the frame; an unserializable payload becomes a JSON-RPC error frame carrying
    the original id. Shared by every transport: without it the TypeError escaped from a pool
    worker (the executor swallows it), so the client waited forever with no log line (#92506)."""
    try:
        return json.dumps(obj, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        rid = obj.get("id") if isinstance(obj, dict) else None
        log.error("frame serialization failed peer=%s id=%s error_type=%s error=%s",
                  peer, rid, type(exc).__name__, exc)
        fallback = {"jsonrpc": "2.0", "id": rid,
                    "error": {"code": -32603, "message": f"response serialization error: {exc}"}}
        return json.dumps(fallback, ensure_ascii=False)


class StdioTransport:
    """Writes JSON frames to a stream (usually ``sys.stdout``) resolved via a callable, so runtime
    monkey-patches of the stream keep working."""

    __slots__ = ("_stream_getter", "_lock")

    def __init__(self, stream_getter: Callable[[], Any], lock: threading.Lock) -> None:
        self._stream_getter = stream_getter
        self._lock = lock

    def write(self, obj: dict) -> bool:
        """Return ``True`` on success, ``False`` ONLY when the peer is gone (see :func:`_raise_unless_peer_gone`)."""
        # Serialization is OUTSIDE the lock so a large payload can't block other threads' frames.
        line = serialize_frame(obj, "stdio", logger) + "\n"
        with self._lock:
            stream = self._stream_getter()
            try:
                stream.write(line)
            except Exception as e:
                _raise_unless_peer_gone(e, "write")
                return False
            # A flush that *raises* peer-gone means the dispatcher should exit cleanly; one that *hangs*
            # on a half-closed pipe holds the lock until it returns — ``_DISABLE_FLUSH`` skips it entirely.
            if not _DISABLE_FLUSH:
                try:
                    stream.flush()
                except Exception as e:
                    _raise_unless_peer_gone(e, "flush")
                    return False
        return True

    def close(self) -> None:
        return None


@dataclass(eq=False)
class _FanoutPeer:
    transport: Transport
    pending: deque = field(default_factory=deque)
    inflight: list = field(default_factory=list)
    pending_bytes: int = 0
    pending_frames: int = 0
    oldest_at: float = 0.0
    large_key: tuple | None = None
    large_frames: int = 0
    large_bytes: int = 0
    writing: bool = False
    attached: bool = True
    generation: int = 0


class FanoutTransport:
    """Ordered, bounded session-event mailboxes; RPC replies remain request-local.

    One slow socket must not stop the emitting turn or any healthy subscriber.
    Each peer has at most one daemon writer and a bounded backlog. On overflow
    it loses its subscription and that peer's transport is closed so the client
    notices, reconnects and replays history. Closing the socket also drops any
    other sessions multiplexed on it; the same reconnect + replay recovers them.
    Other sockets are unaffected. A write already in the OS cannot be revoked.
    """

    # Capacity counts encoded batches, not individual token notifications. The
    # original byte budget stays unchanged; descriptor count is independently bounded.
    _MAX_PENDING_BATCHES = 256
    _BATCH_FRAMES = 64
    _BATCH_BYTES = 64 * 1024
    _MAX_PENDING_BYTES = 4 * 1024 * 1024

    def __init__(self, *transports: Transport) -> None:
        self._lock = threading.Lock()
        self._peers: list[_FanoutPeer] = []
        for transport in transports:
            self.attach(transport)

    def attach(self, transport: Transport) -> bool:
        if transport is None or transport is self:
            return False
        with self._lock:
            for peer in self._peers:
                if peer.transport is transport:
                    if peer.attached:
                        return False
                    # Reuse the in-flight writer: reconnect cannot spawn more
                    # threads or overtake a write already inside this socket.
                    peer.attached = True
                    peer.generation += 1
                    return True
            self._peers.append(_FanoutPeer(transport))
            return True

    def _remove(self, peer: _FanoutPeer) -> None:
        # Membership lock held; identity fences a stale writer from removing
        # a later attachment of the same transport.
        peer.attached = False
        peer.pending.clear()
        peer.inflight = []
        peer.pending_bytes = 0
        peer.pending_frames = 0
        peer.oldest_at = 0.0
        peer.large_key, peer.large_frames, peer.large_bytes = None, 0, 0
        if not peer.writing and peer in self._peers:
            self._peers.remove(peer)

    def detach(self, transport: Transport) -> bool:
        with self._lock:
            for peer in self._peers:
                if peer.attached and peer.transport is transport:
                    self._remove(peer)
                    return True
        return False

    def contains(self, transport: Transport) -> bool:
        with self._lock:
            return any(peer.attached and peer.transport is transport for peer in self._peers)

    def transports(self) -> list[Transport]:
        with self._lock:
            return [peer.transport for peer in self._peers if peer.attached]

    def has_transports(self, *, excluding: Transport | None = None) -> bool:
        return any(peer is not excluding for peer in self.transports())

    def _drain(self, peer: _FanoutPeer) -> None:
        while True:
            with self._lock:
                if not peer.attached or not peer.pending:
                    peer.writing = False
                    if not peer.attached:
                        self._remove(peer)
                    return
                generation = peer.generation
                batch = peer.pending.popleft()
                peer.inflight = batch
            try:
                from tui_gateway.ws import WSTransport
                if isinstance(peer.transport, WSTransport):
                    from agent.async_utils import safe_schedule_threadsafe
                    future = safe_schedule_threadsafe(
                        peer.transport.write_lines_async([item[0] for item in batch],
                                                         queued_at=batch[0][3],
                                                         is_current=lambda: peer.attached and peer.generation == generation),
                        peer.transport._loop)
                    ok = future is not None and future.result()
                else:
                    ok = True
                    for item in batch:
                        if not peer.attached or peer.generation != generation:
                            break
                        if not peer.transport.write(json.loads(item[0])):
                            ok = False
                            break
            except Exception:
                logger.debug("fanout write failed; pruning peer", exc_info=True)
                ok = False
            with self._lock:
                if peer.generation != generation:
                    continue
                if not peer.attached or not ok:
                    peer.writing = False
                    self._remove(peer)
                    return
                # Include in-flight bytes until the actual socket send completes.
                peer.pending_bytes -= sum(item[1] for item in batch)
                peer.pending_frames -= len(batch)
                peer.oldest_at = peer.pending[0][0][3] if peer.pending else 0.0
                for item in batch:
                    if item[4] == peer.large_key:
                        peer.large_frames -= 1
                        peer.large_bytes -= item[1]
                peer.inflight = []
                if not peer.large_frames:
                    peer.large_key = None

    def _signal_overflow_detach(self, transport: Transport, details: dict) -> None:
        # Outside the fanout lock: abort()/close() may re-enter contains/detach, and
        # a WS close must not stall the emit turn or other subscribers. WSTransport
        # aborts (1011 socket close, off-loop safe); other transports just close.
        try:
            diagnostics = getattr(transport, "diagnostics", None)
            if diagnostics is not None:
                diagnostics.log("queue_overflow", **details, reason="fanout_overflow")
            abort = getattr(transport, "abort", None)
            (abort or transport.close)()
        except Exception:
            logger.debug("fanout overflow close failed; membership already dropped", exc_info=True)

    def write(self, obj: dict) -> bool:
        # Freeze the queued frame so a caller cannot mutate it after admission. Same serialization
        # guard as the single-peer transports: an unserializable frame reaches every peer as -32603.
        encoded = serialize_frame(obj, "fanout", logger)
        size = len(encoded.encode("utf-8", errors="surrogatepass"))
        from tui_gateway.connection_diagnostics import event_type
        now = time.monotonic()
        large_key = self._large_group(obj)
        item = (encoded, size, event_type(obj), now, large_key)
        overflowed = []
        with self._lock:
            for peer in list(self._peers):
                if not peer.attached:
                    continue
                if not self._can_enqueue(peer, item, large_key):
                    oldest = peer.oldest_at or now
                    details = dict(event_type=item[2], frame_bytes=size, pending_frames=peer.pending_frames,
                                   pending_bytes=peer.pending_bytes, pending_batches=len(peer.pending),
                                   normal_pending_bytes=peer.pending_bytes - peer.large_bytes,
                                   large_pending_bytes=peer.large_bytes, large_pending_frames=peer.large_frames,
                                   queue_wait_ms=round((now - oldest) * 1000, 3))
                    logger.warning("fanout subscriber backlog full; detaching peer")
                    overflowed.append((peer.transport, details))
                    self._remove(peer)
                    continue
                self._append_batch(peer, item)
                if not peer.pending_frames:
                    peer.oldest_at = now
                peer.pending_bytes += size
                peer.pending_frames += 1
                if peer.large_key == large_key:
                    peer.large_frames += 1
                    peer.large_bytes += size
                diagnostics = getattr(peer.transport, "diagnostics", None)
                if diagnostics is not None:
                    diagnostics.queued(peer.pending_frames, peer.pending_bytes, len(peer.pending))
                if not peer.writing:
                    peer.writing = True
                    threading.Thread(target=self._drain, args=(peer,),
                                     name="tui-fanout", daemon=True).start()
            remaining = any(peer.attached for peer in self._peers)
        for transport, details in overflowed:
            self._signal_overflow_detach(transport, details)
        return remaining

    @staticmethod
    def _large_group(obj):
        # One existing large logical event may have its additive typed twin.
        # Neither is copied per subscriber, truncated, or assigned a new size limit.
        params = obj.get("params")
        params = params if isinstance(params, dict) else {}
        payload = params.get("payload")
        payload = payload if isinstance(payload, dict) else {}
        sequence = payload.get("source_event_seq") if params.get("type") in {
            "message.output_delta", "tool.output"} else params.get("seq")
        return (params.get("session_id"), sequence) if type(sequence) is int else (object(),)

    def _can_enqueue(self, peer, item, large_key):
        size = item[1]
        normal_full = peer.pending_bytes - peer.large_bytes + size > self._MAX_PENDING_BYTES
        if normal_full and not peer.large_frames:
            self._reserve_large_event(peer, item, large_key)
        in_large_slot = peer.large_key == large_key
        if in_large_slot and peer.large_frames >= 2:
            return False
        if not in_large_slot and normal_full:
            return False
        needs_batch = (not peer.pending or len(peer.pending[-1]) >= self._BATCH_FRAMES
                       or sum(entry[1] for entry in peer.pending[-1]) + size > self._BATCH_BYTES)
        return not needs_batch or len(peer.pending) < self._MAX_PENDING_BATCHES

    def _reserve_large_event(self, peer, item, key):
        if item[1] > self._MAX_PENDING_BYTES:
            peer.large_key = key
            return
        # A 2.5MiB legacy + 2.5MiB typed twin is one logical large event too.
        # Promote its existing first frame rather than letting the duplicate
        # payload poison every healthy subscriber at the 4MiB ordinary budget.
        pairs = {"message.output_delta": {"message.delta", "reasoning.delta", "message.interim"},
                 "tool.output": {"tool.start", "tool.complete", "tool.generating"}}
        expected = pairs.get(item[2], ())
        if not expected:
            return
        for prior in chain(peer.inflight, chain.from_iterable(peer.pending)):
            if prior[4] == key and prior[2] in expected:
                peer.large_key, peer.large_frames, peer.large_bytes = key, 1, prior[1]
                return

    def _append_batch(self, peer, item):
        if (peer.pending and len(peer.pending[-1]) < self._BATCH_FRAMES
                and sum(entry[1] for entry in peer.pending[-1]) + item[1] <= self._BATCH_BYTES):
            peer.pending[-1].append(item)
        else:
            peer.pending.append([item])

    def close(self) -> None:
        """Detach without closing sockets owned by the connection handlers."""
        with self._lock:
            for peer in list(self._peers):
                self._remove(peer)


class TeeTransport:
    """Mirrors writes to one primary plus N best-effort secondaries. The primary's return value (and
    exceptions) determine the result; secondaries swallow failures so a wedged sidecar never stalls the
    main IO path. Used by the PTY child: every emit lands on stdio (Ink) AND a back-WS for the dashboard."""

    __slots__ = ("_primary", "_secondaries")

    def __init__(self, primary: "Transport", *secondaries: "Transport") -> None:
        self._primary = primary
        self._secondaries = secondaries

    def write(self, obj: dict) -> bool:
        # Primary first so a slow sidecar (WS publisher) never delays Ink/stdio.
        ok = self._primary.write(obj)
        for sec in self._secondaries:
            with contextlib.suppress(Exception):
                sec.write(obj)
        return ok

    def close(self) -> None:
        try:
            self._primary.close()
        finally:
            for sec in self._secondaries:
                with contextlib.suppress(Exception):
                    sec.close()
