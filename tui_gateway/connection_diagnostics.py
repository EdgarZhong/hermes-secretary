"""Bounded, content-free connection diagnostics on the existing backend logger."""
from __future__ import annotations

import json
import logging
import re
import threading
import time
import uuid
from datetime import datetime, timezone

_log = logging.getLogger("hermes_cli.web_server")
_INSTANCE = uuid.uuid4().hex
_ID = re.compile(r"[0-9a-fA-F]{32}\Z")
_PEER_INITIATORS = frozenset({"ping_timeout", "ping_error", "connect_timeout", "socket_error",
                              "bootstrap_error", "authentication", "stop"})
_PEER_CLOSE_REASONS = {f"hermes:{value}": value for value in _PEER_INITIATORS}
_FIELDS = frozenset({
    "code", "initiator", "reason", "event_type", "frame_bytes", "pending_frames", "pending_bytes",
    "pending_batches", "queue_wait_ms", "send_ms", "loop_lag_ms", "sent_frames", "sent_bytes",
    "max_queue_wait_ms", "max_send_ms", "max_loop_lag_ms", "messages", "parse_errors",
    "dispatch_crashes", "send_failures", "duration_ms", "client_id_valid", "errors",
    "max_pending_frames", "max_pending_bytes", "max_pending_batches",
    "normal_pending_bytes", "large_pending_bytes", "large_pending_frames",
})
_EVENTS = frozenset({"accepted", "ready", "health", "queue_overflow", "frame_too_large",
                     "send_timeout", "send_error", "write_wait", "close_requested", "closed"})
_REASONS = frozenset({"fanout_overflow", "frame_too_large", "send_deadline", "send_error",
                      "disconnect_observed", "receive_failed", "ready_send_failed", "server_shutdown",
                      "handler_send_failed", "normal", "unknown"})


def valid_connection_id(value) -> str | None:
    return value.lower() if isinstance(value, str) and _ID.fullmatch(value) else None


def peer_reported_initiator(code, reason) -> str | None:
    """Untrusted close metadata only; never an authorization or recovery decision."""
    return _PEER_CLOSE_REASONS.get(reason) if code == 4100 and isinstance(reason, str) else None


def close_initiator(server_requested: bool, peer_reported: str | None) -> str:
    if server_requested:
        return "server"
    return "peer" if peer_reported else "unknown"


def event_type(obj: dict) -> str:
    from tui_gateway.contracts.registry import EVENTS
    params = obj.get("params")
    kind = params.get("type") if isinstance(params, dict) else None
    return kind if isinstance(kind, str) and kind in EVENTS else "rpc_or_other"


def backend_revision() -> str:
    # The native startup fingerprint identifies executing code, not a later checkout.
    from gateway import code_skew
    fingerprint = code_skew._boot_fingerprint or ""
    revision = fingerprint.rsplit(":", 1)[-1]
    return revision if re.fullmatch(r"[0-9a-fA-F]{7,64}", revision) else "unknown"


def ensure_loop_probe(loop) -> None:
    if getattr(loop, "_hermes_connection_probe", False):
        return
    loop._hermes_connection_probe = True
    loop._hermes_connection_lag_ms = 0.0

    def tick(expected):
        now = loop.time()
        loop._hermes_connection_lag_ms = max(0.0, (now - expected) * 1000)
        loop.call_later(1.0, tick, now + 1.0)

    loop.call_later(1.0, tick, loop.time() + 1.0)


class ConnectionDiagnostics:
    def __init__(self, client_connection_id=None):
        self.connection_id = uuid.uuid4().hex
        self.client_connection_id = valid_connection_id(client_connection_id)
        try:
            self.revision = backend_revision()
        except (ImportError, AttributeError):
            self.revision = "unknown"
        self.started = time.monotonic()
        self._lock = threading.Lock()
        self._next_health = self.started + 60.0
        self._metrics = dict(sent_frames=0, sent_bytes=0, max_queue_wait_ms=0.0,
                             max_send_ms=0.0, max_loop_lag_ms=0.0, max_pending_frames=0,
                             max_pending_bytes=0, max_pending_batches=0)
        self.errors = 0

    def log(self, event: str, **fields) -> None:
        try:
            if event not in _EVENTS:
                return
            safe = {key: value for key, value in fields.items() if key in _FIELDS
                    and isinstance(value, (int, float, bool))}
            if fields.get("reason") in _REASONS:
                safe["reason"] = fields["reason"]
            if fields.get("initiator") in {"server", "peer", "unknown"}:
                safe["initiator"] = fields["initiator"]
            if fields.get("peer_reported_initiator") in _PEER_INITIATORS:
                safe["peer_reported_initiator"] = fields["peer_reported_initiator"]
            if "event_type" in fields:
                from tui_gateway.contracts.registry import EVENTS
                kind = fields["event_type"]
                safe["event_type"] = kind if kind in EVENTS else "rpc_or_other"
            record = dict(event=event, connection_id=self.connection_id,
                          client_connection_id=self.client_connection_id, backend_instance=_INSTANCE,
                          backend_revision=self.revision, monotonic_ms=round(time.monotonic() * 1000, 3),
                          timestamp=datetime.now(timezone.utc).isoformat(),
                          **safe)
            level = logging.WARNING if event in {"queue_overflow", "frame_too_large", "send_timeout", "send_error"} else logging.INFO
            _log.log(level, "connection_diagnostic %s", json.dumps(record, separators=(",", ":")))
        except (OSError, ValueError, TypeError, RuntimeError):
            self.errors += 1  # Diagnostics never prevent a send/close.

    def sent(self, size: int, wait_ms: float, send_ms: float, loop_lag_ms: float) -> None:
        with self._lock:
            values = self._metrics
            values["sent_frames"] += 1
            values["sent_bytes"] += size
            for key, value in (("max_queue_wait_ms", wait_ms), ("max_send_ms", send_ms),
                               ("max_loop_lag_ms", loop_lag_ms)):
                values[key] = max(values[key], round(value, 3))

    def queued(self, frames: int, size: int, batches: int) -> None:
        with self._lock:
            for key, value in (("max_pending_frames", frames), ("max_pending_bytes", size),
                               ("max_pending_batches", batches)):
                self._metrics[key] = max(self._metrics[key], value)

    def health(self, *, force=False) -> None:
        now = time.monotonic()
        with self._lock:
            if not force and now < self._next_health:
                return
            values, self._next_health = dict(self._metrics), now + 60.0
        self.log("health", **values, errors=self.errors, duration_ms=round((now - self.started) * 1000, 3))
