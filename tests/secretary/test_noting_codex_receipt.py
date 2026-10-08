"""Noting observes actual app-server transport ACKs, not early native fences."""

import threading
import time

import pytest

from agent.transports.codex_app_server import CodexAppServerError
from tests.agent.transports.test_codex_app_server_session import FakeClient, make_session
from tests.secretary.test_noting_compact import make_parent
from secretary.noting_compact import compact_parent


def _codex_parent(tmp_path, monkeypatch):
    parent, db = make_parent(tmp_path, monkeypatch)
    client = FakeClient()
    session = make_session(client)
    parent.api_mode = "codex_app_server"
    parent.codex_app_server_auto_compaction = "hermes"
    parent._codex_session = session
    parent.context_compressor.last_prompt_tokens = 500_000
    parent.context_compressor.threshold_tokens = 100_000
    return parent, db, client, session


def _wait_finished(parent):
    deadline = time.monotonic() + 3
    while getattr(parent, "_active_compression_commit_fence", None) and time.monotonic() < deadline:
        time.sleep(0.01)
    assert getattr(parent, "_active_compression_commit_fence", None) is None


@pytest.mark.parametrize("terminal", ["completed", "failed", "timeout"])
def test_transport_ack_receipt_precedes_native_completion(tmp_path, monkeypatch, terminal):
    parent, db, client, session = _codex_parent(tmp_path, monkeypatch)
    original = session.compact_thread
    session.compact_thread = lambda **kwargs: original(turn_timeout=0.3, **kwargs)
    try:
        result = compact_parent(parent, wait_seconds=1)
        assert result.ok and result.status == "admitted"
        assert ("thread/compact/start", {"threadId": "thread-fake-001"}) in client.requests
        assert parent._active_compression_commit_fence is not None
        assert compact_parent(parent).status == "already_in_flight"
        if terminal != "timeout":
            client.queue_notification("turn/started", threadId="thread-fake-001", turn={"id": "compact-1"})
            client.queue_notification("turn/completed", threadId="thread-fake-001",
                                      turn={"id": "compact-1", "status": terminal})
        _wait_finished(parent)
        # A later failed turn or timeout cannot erase a successful provider admission ACK.
        assert result.ok and result.status == "admitted"
        if terminal != "completed":
            assert parent.context_compressor._last_summary_error
    finally:
        session.close()
        _wait_finished(parent)
        db.close()


@pytest.mark.parametrize("reason", ["rpc_error", "mode_native", "mode_off", "cooldown", "snapshot_stale", "cancelled"])
def test_transport_refusal_and_native_skip_never_publish_receipt(tmp_path, monkeypatch, reason):
    from agent.conversation_compression import CompressionCommitFence, compress_context
    parent, db, client, session = _codex_parent(tmp_path, monkeypatch)
    receipt = threading.Event()
    fence = CompressionCommitFence()
    try:
        if reason == "rpc_error":
            def rpc(method, params):
                if method == "thread/start":
                    return {"thread": {"id": "thread-fake-001"}}
                raise CodexAppServerError(code=-32000, message="compaction rejected")
            client._request_handler = rpc
        elif reason.startswith("mode_"):
            parent.codex_app_server_auto_compaction = reason.removeprefix("mode_")
        elif reason == "cooldown":
            parent.context_compressor.record_timeout_failure("original native cooldown", failure_kind="stalled")
        elif reason == "cancelled":
            fence.cancel_before_commit()
        if reason == "snapshot_stale":
            with pytest.raises(RuntimeError, match="snapshot stale"):
                compress_context(parent, parent._session_messages, "prompt", commit_fence=fence,
                                 admission_receipt=receipt, snapshot_is_current=lambda: False)
        else:
            unchanged, _ = compress_context(parent, parent._session_messages, "prompt", commit_fence=fence,
                                            admission_receipt=receipt)
            assert unchanged is parent._session_messages
        assert not receipt.is_set()
        if reason != "rpc_error":
            assert not any(method == "thread/compact/start" for method, _ in client.requests)
    finally:
        session.close()
        db.close()
