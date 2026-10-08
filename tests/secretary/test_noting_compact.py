"""``compact_parent`` against native state: verdict, refusal, cooldown and admission proof.

The Parent here is a real ``AIAgent`` with a real ``ContextCompressor`` bound to a real
profile ``state.db``, so "below threshold", the cooldown ladder and the durable compression
lock are the native ones. The native compression entry itself is replaced only where this
module's own admission classification is the contract under test (the full compression body
is covered by the compression suite); its absence must never be reported as success.
"""

from __future__ import annotations

import threading
import time
from unittest.mock import MagicMock

import pytest

from hermes_state import SessionDB
from secretary.noting_compact import compact_parent, compact_parent_from_child


def make_parent(tmp_path, monkeypatch, session_id="S17"):
    from run_agent import AIAgent

    monkeypatch.setattr("model_tools.get_tool_definitions", lambda **kwargs: [])
    monkeypatch.setattr("model_tools.check_toolset_requirements", lambda *a, **k: {})
    monkeypatch.setattr("agent.process_bootstrap.OpenAI", lambda **kwargs: MagicMock())
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *a, **k: {})
    monkeypatch.setattr("agent.title_generator.maybe_auto_title", lambda *a, **k: None)
    monkeypatch.setattr("run_agent._hermes_home", tmp_path / "hermes-home")
    (tmp_path / "hermes-home" / "logs").mkdir(parents=True, exist_ok=True)
    db = SessionDB(db_path=tmp_path / "state.db")
    db.create_session(session_id, source="test")
    agent = AIAgent(
        api_key="test-key", base_url="https://openrouter.ai/api/v1", quiet_mode=True,
        skip_context_files=True, skip_memory=True, session_db=db, session_id=session_id,
    )
    agent._cached_system_prompt = "You are helpful."
    agent._session_messages = [{"role": "user", "content": "hello", "timestamp": 1.0}]
    return agent, db


def _never_compress(monkeypatch, parent) -> dict:
    calls = {"n": 0}

    def _fail(*args, **kwargs):
        calls["n"] += 1
        raise AssertionError("native compaction must not be requested on this path")

    monkeypatch.setattr(parent, "_compress_context", _fail, raising=False)
    return calls


def test_below_threshold_is_success_without_requesting_compaction(tmp_path, monkeypatch):
    parent, db = make_parent(tmp_path, monkeypatch)
    try:
        parent.context_compressor.last_prompt_tokens = 10
        parent.context_compressor.threshold_tokens = 100_000
        calls = _never_compress(monkeypatch, parent)
        result = compact_parent(parent)
        assert (result.ok, result.status) == (True, "already_below_threshold")
        assert calls["n"] == 0
    finally:
        db.close()


def test_cooldown_refuses_without_forcing_and_without_starting_an_attempt(tmp_path, monkeypatch):
    parent, db = make_parent(tmp_path, monkeypatch)
    try:
        parent.context_compressor.last_prompt_tokens = 500_000
        parent.context_compressor.threshold_tokens = 100_000
        parent.context_compressor.record_timeout_failure("stalled", failure_kind="stalled")
        calls = _never_compress(monkeypatch, parent)
        result = compact_parent(parent)
        assert result.ok is False
        assert result.status.startswith("blocked:cooldown")
        assert calls["n"] == 0
    finally:
        db.close()


def test_early_durable_compression_lock_is_not_safe_admission(tmp_path, monkeypatch):
    parent, db = make_parent(tmp_path, monkeypatch)
    try:
        parent.context_compressor.last_prompt_tokens = 500_000
        parent.context_compressor.threshold_tokens = 100_000
        assert db.try_acquire_compression_lock("S17", "pid=99999:turn=other", ttl_seconds=300.0) is True
        calls = _never_compress(monkeypatch, parent)
        result = compact_parent(parent)
        assert result.ok is False
        assert calls["n"] == 1
    finally:
        db.close()


def test_admission_requires_receipt_not_early_lock_publication(tmp_path, monkeypatch):
    parent, db = make_parent(tmp_path, monkeypatch)
    try:
        parent.context_compressor.last_prompt_tokens = 500_000
        parent.context_compressor.threshold_tokens = 100_000
        release = threading.Event()
        entered = threading.Event()

        def _native_entry(messages, prompt, **kwargs):
            entered.set()
            parent._active_compression_lock_holder = "test-holder"  # native admission publication
            kwargs["admission_receipt"].set()
            release.wait(timeout=10)
            parent._active_compression_lock_holder = None
            return messages, prompt

        monkeypatch.setattr(parent, "_compress_context", _native_entry, raising=False)
        result = compact_parent(parent, wait_seconds=5.0)
        assert entered.is_set()
        assert (result.ok, result.status) == (True, "admitted")
        release.set()
        time.sleep(0.05)

        # A native entry that ends without ever publishing admission is a FAILURE, not a success.
        parent._active_compression_lock_holder = None

        def _no_admission(messages, prompt, **kwargs):
            return messages, prompt

        monkeypatch.setattr(parent, "_compress_context", _no_admission, raising=False)
        refused = compact_parent(parent, wait_seconds=5.0)
        assert refused.ok is False
        assert refused.status in {"not_admitted", "blocked:ineffective"}
    finally:
        db.close()


def test_native_error_is_a_typed_failure(tmp_path, monkeypatch):
    parent, db = make_parent(tmp_path, monkeypatch)
    try:
        parent.context_compressor.last_prompt_tokens = 500_000
        parent.context_compressor.threshold_tokens = 100_000

        def _boom(messages, prompt, **kwargs):
            raise RuntimeError("summary route unavailable")

        monkeypatch.setattr(parent, "_compress_context", _boom, raising=False)
        result = compact_parent(parent, wait_seconds=5.0)
        assert result.ok is False
        assert result.status in {"native_error", "blocked:ineffective"}
    finally:
        db.close()


def test_missing_compressor_fails_clearly(tmp_path, monkeypatch):
    parent, db = make_parent(tmp_path, monkeypatch)
    try:
        result = compact_parent(object())
        assert (result.ok, result.status) == (False, "no_compressor")
    finally:
        db.close()


def test_tool_entry_requires_the_parent_binding(tmp_path, monkeypatch):
    payload = compact_parent_from_child(object())
    assert '"success": false' in payload and "permission_denied" in payload


def test_real_native_safety_checks_precede_receipt(tmp_path, monkeypatch):
    from agent.conversation_compression import CompressionCommitFence, compress_context

    parent, db = make_parent(tmp_path, monkeypatch)
    try:
        parent._compression_feasibility_checked = True
        parent.context_compressor.last_prompt_tokens = 500_000
        parent.context_compressor.threshold_tokens = 100_000
        receipt = threading.Event()
        messages = parent._session_messages
        unchanged, _ = compress_context(parent, messages, "prompt", commit_fence=CompressionCommitFence(),
                                         snapshot_is_current=lambda: False, admission_receipt=receipt)
        assert unchanged is messages and not receipt.is_set()
        assert db.get_compression_lock_holder(parent.session_id) is None
        monkeypatch.setattr("agent.conversation_compression._capture_authoritative_cooldown_under_lease", lambda *a: (False, {}))
        unchanged, _ = compress_context(parent, messages, "prompt", commit_fence=CompressionCommitFence(),
                                         admission_receipt=receipt)
        assert unchanged is messages and not receipt.is_set()
        assert db.get_compression_lock_holder(parent.session_id) is None
    finally:
        db.close()


def test_real_native_admission_returns_before_summary_finishes(tmp_path, monkeypatch):
    parent, db = make_parent(tmp_path, monkeypatch)
    release = threading.Event()
    entered = threading.Event()
    try:
        parent._compression_feasibility_checked = True
        parent.context_compressor.last_prompt_tokens = 500_000
        parent.context_compressor.threshold_tokens = 100_000
        def summary(*args, **kwargs):
            entered.set()
            release.wait(timeout=10)
            raise RuntimeError("ultimate summary failure")
        monkeypatch.setattr("agent.conversation_compression._run_summary_phase", summary)
        result = compact_parent(parent, wait_seconds=2)
        assert entered.is_set()
        assert result.ok and result.status == "admitted"
        # Native safe admission also supports a different concurrent Noting task.
        assert compact_parent(parent).status == "already_in_flight"
    finally:
        release.set()
        deadline = time.monotonic() + 3
        while db.get_compression_lock_holder(parent.session_id) and time.monotonic() < deadline:
            time.sleep(0.01)
        db.close()
