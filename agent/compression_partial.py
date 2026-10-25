"""Attempt-owned partial summaries; only native compression installs these scopes."""

from __future__ import annotations

import contextlib
import contextvars
import copy
import logging
import threading
from types import SimpleNamespace

_CAPTURE = contextvars.ContextVar('compression_partial_capture', default=None)
_ADOPTED = contextvars.ContextVar('compression_adopted_partial', default=None)
logger = logging.getLogger(__name__)
TRUNCATION_NOTICE = (
    '[System notice: The compression summary was truncated by a context/output limit or timeout. '
    'The available summary was retained; some details may be incomplete.]'
)


def field(value, name, default=None):
    result = value.get(name, default) if isinstance(value, dict) else getattr(value, name, default)
    return default if result is None else result


def response_finish_reason(response):
    choices = field(response, 'choices', [])
    reason = field(choices[0], 'finish_reason') if choices else None
    return str(reason or field(response, 'stop_reason', '')).strip().lower()


def response_truncated(response):
    reason = response_finish_reason(response)
    details = field(response, 'incomplete_details', {})
    incomplete = str(field(details, 'reason', '')).lower()
    return reason in {'length', 'max_tokens', 'max_output_tokens', 'model_context_window_exceeded', 'timeout'} or (
        field(response, 'status') == 'incomplete' and incomplete in {
            'max_output_tokens', 'max_tokens', 'context_length_exceeded', 'model_context_window_exceeded'})


class PartialSummary(str):
    """Immutable text carrying a display notice until summary augmentation finishes."""


def annotate_summary(summary, partial):
    return summary.rstrip() + '\n\n' + TRUNCATION_NOTICE if partial else summary


def normalized_response(content='', reasoning='', refusal=''):
    return SimpleNamespace(choices=[SimpleNamespace(finish_reason='timeout', message=SimpleNamespace(
        content=content, reasoning_content=reasoning, refusal=refusal))])


class PartialCapture:
    """Freeze the last accepted stream prefix under its accumulator's own lock."""

    def __init__(self):
        self._lock = threading.Lock()
        self._reader = None
        self.adopted = False
        self._text, self._reasoning, self._refusal = [], [], []

    def register(self, reader):
        with self._lock:
            self._reader = reader
            self._text, self._reasoning, self._refusal = [], [], []

    def observe(self, event):
        kind, delta = field(event, 'type', ''), field(event, 'delta')
        with self._lock:
            if kind in {'response.output_text.delta', 'response.refusal.delta', 'response.reasoning_summary_text.delta'}:
                target = self._refusal if 'refusal' in kind else self._reasoning if 'reasoning' in kind else self._text
                if isinstance(delta, str):
                    target.append(delta)
            elif kind == 'content_block_delta':
                for key, target in (('text', self._text), ('thinking', self._reasoning)):
                    value = field(delta, key)
                    if isinstance(value, str):
                        target.append(value)

    def freeze(self):
        with self._lock:
            response = self._reader() if self._reader else normalized_response(
                ''.join(self._text), ''.join(self._reasoning), ''.join(self._refusal))
            response = copy.deepcopy(response)
        try:
            from agent.context_compressor import _is_refusal_response
            from agent.auxiliary_client import extract_content_or_reasoning
            text = extract_content_or_reasoning(response, max_reasoning_chars=8000)
            if not text.strip() or _is_refusal_response(response, text):
                return None
            return PartialSummary(text)
        except Exception:
            logger.debug('Unable to freeze partial compression summary', exc_info=True)
            return None


@contextlib.contextmanager
def capture_scope(capture):
    token = _CAPTURE.set(capture)
    try:
        yield
    finally:
        _CAPTURE.reset(token)


def register_stream(reader):
    capture = _CAPTURE.get()
    if capture is not None:
        capture.register(reader)


def observe_stream_event(event):
    capture = _CAPTURE.get()
    if capture is not None:
        capture.observe(event)


def response_after_timeout(exc):
    from agent.auxiliary_client import _is_timeout_error, _aux_interrupt_cancel_requested
    capture = _CAPTURE.get()
    if capture is None or _aux_interrupt_cancel_requested():
        return None
    from agent.error_classifier import FailoverReason, classify_api_error
    if not _is_timeout_error(exc) and classify_api_error(exc).reason != FailoverReason.context_overflow:
        return None
    text = capture.freeze()
    return normalized_response(content=text) if text else None


def adopted_summary():
    return _ADOPTED.get()


def recover_partial(fence, *, worker, messages, telemetry_agent, new_fence):
    """Poisoned original stays poisoned; the normal worker publishes a frozen candidate on a fresh fence."""
    stop = getattr(telemetry_agent, '_hard_interrupt_requested', None)
    if callable(getattr(stop, 'is_set', None)) and stop.is_set():
        return None
    text = fence.partial.freeze()
    if text is None:
        return None
    fence.partial.adopted = True
    from agent.conversation_compression import CompressionCommitFence
    retry_fence = new_fence() if callable(new_fence) else CompressionCommitFence()
    token = _ADOPTED.set(text)
    try:
        result = worker(retry_fence)
        return result
    finally:
        _ADOPTED.reset(token)


def call_with_partial(call):
    """A compression-only timeout response bypasses transport/model retries; other calls raise unchanged."""
    try:
        return call()
    except Exception as exc:
        partial = response_after_timeout(exc)
        if partial is None:
            raise
        return partial
