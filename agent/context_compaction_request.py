"""Native, compression-specific handoff between idle maintenance and a Turn.

Requests reserve no successful admission: only the existing compressor's post-safety
receipt can do that. Network work never holds the session publication lock.
"""
from __future__ import annotations

import logging
import os
import threading
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)
_UNKNOWN = object()


@dataclass
class NativeCompactionResult:
    ok: bool
    status: str
    usage_tokens: int = 0
    threshold_tokens: int = 0
    detail: str = ""


def _lock(agent):
    return vars(agent).setdefault('_session_persist_lock', threading.RLock())


def _epoch(agent):
    return vars(agent).setdefault('_native_compaction_owner', object())


def _ref(agent):
    db = getattr(agent, '_session_db', None)
    return db.resolve_conversation_ref(agent.session_id) if db is not None else None


def trust_default_system_message(agent):
    """Official host factories invoke native Turns with their default None parameter."""
    agent._native_compaction_default_system_message = True


@dataclass
class NativeCompactionRequest:
    agent: Any
    deadline: float
    usage: int
    threshold: int
    owner: Any
    db: Any
    conversation_ref: Any
    session_id: str
    publication_id: str = field(default_factory=lambda: uuid.uuid4().hex)
    state: str = 'waiting'
    fence: Any = None
    admitted: threading.Event = field(default_factory=threading.Event)
    completed: threading.Event = field(default_factory=threading.Event)
    result: Any = None
    error: str = ''
    committed: bool = False
    durable_commit_succeeded: bool = False
    was_admitted: bool = False

    def current(self):
        return (self.owner is _epoch(self.agent) and self.db is getattr(self.agent, '_session_db', None)
                and self.conversation_ref == _ref(self.agent))

    def bind_fence(self, fence):
        with _lock(self.agent):
            self.fence = fence
            if self.state in {'expired', 'cancelled'} or not self.current():
                fence.revoke_commit_admission()

    def admit(self, fence):
        """Called AFTER native safety checks; deadline and receipt have one winner."""
        with _lock(self.agent):
            stop = getattr(self.agent, '_hard_interrupt_requested', None)
            if (not self.current() or self.state in {'expired', 'cancelled'}
                    or (not self.admitted.is_set() and time.monotonic() >= self.deadline)
                    or (stop is not None and stop.is_set()) or fence.is_cancelled):
                self.state = 'expired'
                fence.revoke_commit_admission()
                return False
            self.state = 'admitted'
            self.was_admitted = True
            fence._secretary_native_admitted = True
            self.admitted.set()
            return True

    def cancel(self, state='cancelled'):
        with _lock(self.agent):
            unclaimed = self.state == 'waiting'
            self.state = state
            fence = self.fence
            if unclaimed:
                self.completed.set()
                self.admitted.set()
        if fence is not None:
            fence.revoke_commit_admission()
            fence.cancel_before_commit()


def _usage(agent):
    c = getattr(agent, 'context_compressor', None)
    usage = max(int(getattr(c, 'last_real_prompt_tokens', 0) or 0),
                int(getattr(c, 'last_prompt_tokens', 0) or 0))
    return usage, int(getattr(c, 'threshold_tokens', 0) or 0)


class _NativeAdmissionReceipt:
    """RPC-owned native routes report their real dispatch ACK through this adapter."""
    def __init__(self, request):
        self.request = request

    def set(self):
        fence = self.request.fence
        if fence is not None:
            self.request.admit(fence)


def request_context_compaction(agent, *, relevant_threshold_tokens=None, wait_seconds=5.0):
    """Machine result for one native request; successful receipt is not completion."""
    from agent.conversation_compression import _automatic_compression_gate_blocks
    usage, native_threshold = _usage(agent)
    threshold = native_threshold if relevant_threshold_tokens is None else relevant_threshold_tokens
    if getattr(agent, 'context_compressor', None) is None:
        return NativeCompactionResult(False, 'no_compressor')
    if usage < threshold:
        return NativeCompactionResult(True, 'already_below_threshold', usage, threshold)
    fence = getattr(agent, '_active_compression_commit_fence', None)
    if fence is not None and getattr(fence, '_secretary_native_admitted', False) is True and not fence.is_cancelled:
        return NativeCompactionResult(True, 'already_in_flight', usage, threshold)
    if _automatic_compression_gate_blocks(agent, False):
        reason = getattr(agent.context_compressor, '_compression_block_reason', lambda: None)() or 'native_guard'
        return NativeCompactionResult(False, f'blocked:{reason}', usage, threshold)
    with _lock(agent):
        request = vars(agent).get('_native_compaction_request')
        if request is None or request.completed.is_set():
            active = vars(agent).get('_native_compaction_turn') is not None
            custom = vars(agent).get('_native_compaction_custom', _UNKNOWN)
            if custom is _UNKNOWN and not active:
                if vars(agent).get('_native_compaction_default_system_message') is not True:
                    return NativeCompactionResult(False, 'unknown_system_message', usage, threshold)
                custom = None
            messages = getattr(agent, '_session_messages', None)
            if not isinstance(messages, list) or getattr(agent, '_session_db', None) is None:
                return NativeCompactionResult(False, 'no_parent_transcript', usage, threshold)
            request = NativeCompactionRequest(agent, time.monotonic() + max(0.0, wait_seconds), usage,
                                              threshold, _epoch(agent), agent._session_db, _ref(agent), agent.session_id)
            agent._native_compaction_request = request
            if not active:
                request.state = 'claimed'
                _start_idle_request(request, custom)
    timeout = max(0.0, request.deadline - time.monotonic())
    # Completion without admission wakes the same event (with no successful state).
    request.admitted.wait(timeout)
    with _lock(agent):
        if request.was_admitted or request.committed:
            return NativeCompactionResult(True, 'admitted', usage, threshold, 'native_safe_admission')
        if request.completed.is_set():
            return NativeCompactionResult(False, 'native_error' if request.error else 'not_admitted', usage, threshold, request.error)
        request.state = 'expired'
    request.cancel('expired')
    return NativeCompactionResult(False, 'admission_timeout', usage, threshold)


def _start_idle_request(request, custom):
    from agent.memory_provider import spawn_context_thread
    worker = spawn_context_thread(lambda: _run_idle_request(request, custom), name='native-compaction-request')
    request.agent._native_compaction_worker = worker
    worker.start()


def _run_idle_request(request, custom):
    from agent.periodic_scheduler import schedule
    from hermes_state_pidns import holder_namespace_token
    agent, db = request.agent, request.db
    holder = f'pid={os.getpid()}{holder_namespace_token()}:turn=compaction:{request.publication_id}'
    handle = None
    acquired = False
    try:
        acquired = db.acquire_session_turn_lease(request.session_id, holder,
            wait_seconds=max(0.0, request.deadline-time.monotonic()), poll_interval_seconds=0.05,
            should_abort=lambda: not request.current() or request.state in {'expired', 'cancelled'})
        if not acquired:
            return
        agent._active_session_turn_lease_holder = holder
        def refresh():
            if not db.refresh_session_turn_lease(request.session_id, holder):
                request.cancel()
        handle = schedule(refresh, 60.0)
        from agent.context_compaction_request_publication import refresh_request_history
        messages = refresh_request_history(agent, agent._session_messages)
        _execute_request(request, messages, custom, idle=True)
    except BaseException as exc:
        request.error = str(exc)
        logger.debug('Idle native compaction request failed', exc_info=True)
    finally:
        if handle is not None:
            handle.cancel(wait=1.0)
        if acquired:
            db.release_session_turn_lease(request.session_id, holder)
            if getattr(agent, '_active_session_turn_lease_holder', None) == holder:
                agent._active_session_turn_lease_holder = None
        request.completed.set()
        request.admitted.set()


def _execute_request(request, messages, custom, *, idle=False):
    agent = request.agent
    try:
        from hermes_constants import reset_hermes_home_override, set_hermes_home_override
        from pathlib import Path
        token = set_hermes_home_override(Path(request.db.db_path).parent)
        try:
            request.result = agent._compress_context(messages, custom, approx_tokens=request.usage,
                trigger='noting_compact_parent', snapshot_is_current=request.current, native_request=request,
                admission_receipt=_NativeAdmissionReceipt(request))
        finally:
            reset_hermes_home_override(token)
        return request.result
    except BaseException as exc:
        request.error = str(exc)
        raise
    finally:
        if not idle:
            request.completed.set()
            request.admitted.set()


def enter_native_turn(agent, system_message, conversation_history):
    """Handoff before host history is copied by build_turn_context; no network lock."""
    while True:
        with _lock(agent):
            request = vars(agent).get('_native_compaction_request')
            waiting = (request is not None and request.state != 'waiting' and not request.completed.is_set())
            if not waiting:
                token = object()
                agent._native_compaction_turn = token
                if request is not None and request.committed and request.current():
                    conversation_history = list(agent._session_messages)
                    agent._native_compaction_request = None
                return token, conversation_history
        request.completed.wait(0.1)


def capture_native_turn_custom(agent, system_message):
    """Capture only after native admission, immediately before executing its loop."""
    with _lock(agent):
        agent._native_compaction_custom = system_message


def consume_native_request(agent, messages, system_message):
    """One safe-point consumer, after the whole preceding response/tool batch."""
    with _lock(agent):
        request = vars(agent).get('_native_compaction_request')
        if request is None or request.state != 'waiting':
            return None
        if not request.current() or time.monotonic() >= request.deadline:
            request.state = 'expired'
            request.completed.set()
            request.admitted.set()
            return None
        request.state = 'claimed'
    try:
        result = _execute_request(request, messages, system_message)
    except Exception:
        if request.durable_commit_succeeded:
            # The old context has been retired. A failed publication cannot
            # safely fall back to it, even though no live result was adopted.
            raise
        logger.debug('Native request failed at Turn safe point; keeping its context', exc_info=True)
        return None
    with _lock(agent):
        if request.committed and request.current():
            agent._native_compaction_request = None
            return result
    return None


def consume_iteration_request(agent, messages, system_message, active_system_prompt,
                              conversation_history, user_message, current_turn_user_idx):
    result = consume_native_request(agent, messages, system_message)
    if result is None:
        return messages, active_system_prompt, conversation_history, current_turn_user_idx
    from agent.turn_context_compaction import _reanchor, _reset_retry_state_after_compaction
    from agent.conversation_compression import conversation_history_after_compression
    messages, active_system_prompt = result
    conversation_history = conversation_history_after_compression(agent, messages, conversation_history)
    _reset_retry_state_after_compaction(agent)
    return messages, active_system_prompt, conversation_history, _reanchor(agent, messages, user_message)


def finish_native_turn(agent, token, result, system_message, user_message):
    """The final native consumer must update the actual host result envelope."""
    if not isinstance(result, dict) or not isinstance(result.get('messages'), list):
        return result
    stop = getattr(agent, '_hard_interrupt_requested', None)
    if stop is not None and stop.is_set():
        cancel_native_request(agent)
        return result
    consumed = consume_native_request(agent, result['messages'], system_message)
    if consumed is not None:
        result['messages'] = consumed[0]
        from agent.turn_context import export_current_turn_boundary
        result.pop('current_turn_user_idx', None)
        result = export_current_turn_boundary(agent, result, user_message)
    return result


def leave_native_turn(agent, token):
    with _lock(agent):
        if vars(agent).get('_native_compaction_turn') is token:
            agent._native_compaction_turn = None
        request = vars(agent).get('_native_compaction_request')
        if request is not None and request.state == 'waiting':
            request.state = 'cancelled'
            request.completed.set()
            request.admitted.set()


def cancel_native_request(agent, *, boundary=False, enabled=True):
    if not enabled:
        return
    request = vars(agent).get('_native_compaction_request')
    if request is not None:
        request.cancel()
    if boundary:
        with _lock(agent):
            agent._native_compaction_owner = object()
            agent._native_compaction_request = None
            vars(agent).pop('_native_compaction_custom', None)


def settle_native_boundary_history(agent, history):
    """Settle its real fence, then consume committed history BEFORE a host flush/copy."""
    cancel_native_request(agent)
    from agent.context_compaction_request_publication import refresh_request_history
    fresh = refresh_request_history(agent, history)
    if fresh is not history:
        from agent.compression_facade import _rebind_caller_session_context
        _rebind_caller_session_context(agent)
    return fresh
