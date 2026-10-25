"""Native retained-tail compaction publishes usable truncated/timeout summaries without another model call."""

import threading
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from agent import auxiliary_client as aux
from agent.compression_partial import TRUNCATION_NOTICE, response_truncated
from agent.context_compressor import _SUMMARY_END_MARKER
from agent.usage_anchor import capture_usage_anchor, set_usage_anchor
from hermes_state import SessionDB
from tests.agent.test_context_compaction_request import _agent, _seed


def chunk(text='', reason=None, reasoning=None):
    return SimpleNamespace(choices=[SimpleNamespace(finish_reason=reason,
        delta=SimpleNamespace(content=text, reasoning_content=reasoning))], usage=None)


def complete_response():
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(
        content='Continued successfully', tool_calls=None, reasoning=None), finish_reason='stop')], usage=None)


@pytest.fixture(params=["legacy", "lean"])
def native(tmp_path, monkeypatch, request):
    (tmp_path / 'config.yaml').write_text('noting:\n  enabled: false\n')
    db = SessionDB(tmp_path / 'state.db')
    _seed(db)
    parent = _agent(db, monkeypatch, tmp_path)
    parent.compression_in_place = True
    compressor = parent.context_compressor
    compressor.protect_first_n, compressor.protect_last_n = 0, 2
    compressor.tail_mode = request.param
    compressor.threshold_tokens = 10000
    compressor.last_prompt_tokens = compressor.last_real_prompt_tokens = 20000
    set_usage_anchor(parent, capture_usage_anchor(20000, 0, parent._session_messages, model=parent.model))
    parent.client = MagicMock()
    parent.client.chat.completions.create.return_value = complete_response()
    parent._disable_streaming = True
    parent._use_prompt_caching = False
    parent.tool_delay = 0
    monkeypatch.setattr('agent.conversation_compression.resolve_context_compression_timeouts', lambda: (.15, .15))
    yield parent, db
    db.close()


@pytest.mark.parametrize('termination', ['length', 'timeout', 'stream-timeout', 'context-limit', 'stop', 'anthropic-timeout', 'responses-timeout'])
def test_native_auto_partial_summary_commits_retained_tail_and_continues(native, monkeypatch, termination):
    parent, db = native
    calls, release = [], threading.Event()
    from agent import conversation_compression as cc
    pool, futures = cc._get_compress_timeout_executor(), []
    submit = pool.submit
    def tracked_submit(*args, **kwargs):
        future = submit(*args, **kwargs)
        futures.append(future)
        return future
    monkeypatch.setattr(pool, "submit", tracked_submit)
    summary = '## Goal\nPreserve the task.\n## Progress\nAvailable partial summary'

    def stream():
        yield chunk(summary)
        if termination == 'timeout':
            release.wait(2)
        if termination == 'stream-timeout':
            raise TimeoutError('read timed out')
        if termination == 'context-limit':
            raise limit_error()
        yield chunk(reason=termination if termination != 'timeout' else 'stop')

    client = MagicMock()
    client.chat.completions.create.side_effect = lambda **kw: stream()

    def summarize(**kwargs):
        calls.append(kwargs)
        if termination == 'anthropic-timeout':
            return anthropic_timeout_summary(summary)
        if termination == 'responses-timeout':
            return responses_timeout_summary(summary)
        return aux._run_protected_sync_provider_call(lambda request: aux._create_with_progress_once(
            client, request, 'compression'), {'model': 'test/model', 'messages': kwargs['messages']})

    monkeypatch.setattr('agent.context_compressor.call_llm', summarize)
    try:
        result = parent.run_conversation('Continue the task', conversation_history=parent._session_messages,
                                         task_id=parent.session_id, persist_user_message='Continue the task')
        checkpoint = parent.context_compressor._previous_summary
        durable_checkpoint = [(r['id'], r['content']) for r in db.get_messages(parent.session_id)]
        context_boundary = db.get_session_model_config_value(parent.session_id, '_usage_context')['transcript_boundary']
    finally:
        release.set()
    for future in futures:
        future.result(timeout=3)
    assert parent.context_compressor._previous_summary == checkpoint
    assert [(r['id'], r['content']) for r in db.get_messages(parent.session_id)] == durable_checkpoint
    assert db.get_session_model_config_value(parent.session_id, '_usage_context')['transcript_boundary'] == context_boundary
    assert parent.context_compressor._summary_failure_cooldown_until == 0
    from agent.compression_read import compression_state
    assert compression_state(parent)['state'] == 'completed'
    assert compression_state(parent)['active'] is False
    assert result['final_response'] == 'Continued successfully'
    assert len(calls) == 1
    if termination not in {'anthropic-timeout', 'responses-timeout'}:
        assert client.chat.completions.create.call_count == 1
    durable = db.get_messages(parent.session_id)
    summaries = [m for m in durable if m.get('_compressed_summary')]
    assert len(summaries) == 1
    text = summaries[0]['content']
    assert summary in text
    assert text.split(_SUMMARY_END_MARKER, 1)[0].rstrip().endswith(TRUNCATION_NOTICE) is (termination != 'stop')
    assert any('old answer 3' in m.get('content', '') for m in durable if not m.get('_compressed_summary'))
    assert any(m.get('content') == 'Continued successfully' for m in durable)
    assert not any(TRUNCATION_NOTICE in m.get('content', '') for m in durable if not m.get('_compressed_summary'))
    assert parent.context_compressor.compression_count >= 1
    assert parent.client.chat.completions.create.call_count == 1


@pytest.mark.parametrize('response,expected', [
    ({'choices': [{'finish_reason': 'length'}]}, True),
    (SimpleNamespace(stop_reason='max_tokens'), True),
    ({'status': 'incomplete', 'incomplete_details': {'reason': 'max_output_tokens'}}, True),
    ({'status': 'incomplete', 'incomplete_details': {'reason': 'content_filter'}}, False),
    ({'choices': [{'finish_reason': 'stop'}]}, False),
    ({}, False),
])
def test_termination_fields_are_compatible(response, expected):
    assert response_truncated(response) is expected


@pytest.mark.parametrize('mode', ['empty', 'refusal', 'user-stop'])
def test_unusable_timeout_and_explicit_stop_do_not_publish_summary(native, monkeypatch, mode):
    parent, db = native
    release, entered = threading.Event(), threading.Event()
    before = db.get_messages(parent.session_id)
    text = '' if mode == 'empty' else "I cannot provide this summary." if mode == 'refusal' else 'Available summary'

    def stream():
        yield chunk(text)
        entered.set()
        release.wait(2)
        yield chunk(reason='stop')

    client = MagicMock()
    client.chat.completions.create.side_effect = lambda **kw: stream()
    monkeypatch.setattr('agent.context_compressor.call_llm', lambda **kw: aux._create_with_progress_once(
        client, {'model': 'test/model', 'messages': kw['messages']}, 'compression'))
    stop = None
    if mode == 'user-stop':
        def interrupt():
            assert entered.wait(2)
            parent.hard_interrupt()
        stop = threading.Thread(target=interrupt)
        stop.start()
    try:
        result, _ = parent._compress_context(parent._session_messages, '', approx_tokens=20000,
                                             trigger='native_context_threshold')
    finally:
        release.set()
        if stop:
            stop.join(2)
    assert not any(m.get('_compressed_summary') for m in db.get_messages(parent.session_id))
    assert [r['content'] for r in db.get_messages(parent.session_id)] == [r['content'] for r in before]
    assert not any(TRUNCATION_NOTICE in m.get('content', '') for m in result)


def test_aux_transport_timeout_adopts_available_text_only_in_compression_scope():
    from agent.compression_partial import PartialCapture, capture_scope

    def stream():
        yield chunk('Received before socket timeout')
        raise TimeoutError('read timed out')

    with pytest.raises(TimeoutError):
        aux._aggregate_chat_stream(stream())
    with capture_scope(PartialCapture()):
        response = aux._aggregate_chat_stream(stream())
    assert aux.extract_content_or_reasoning(response) == 'Received before socket timeout'
    assert response.choices[0].finish_reason == 'timeout'


def test_partial_capture_keeps_refusal_fields_out():
    from agent.compression_partial import PartialCapture, capture_scope
    capture = PartialCapture()
    with capture_scope(capture):
        accumulator = aux._ChatStreamAccumulator()
        accumulator.feed(SimpleNamespace(choices=[SimpleNamespace(finish_reason=None,
            delta=SimpleNamespace(content='Plausible summary', refusal='policy refusal'))]))
        assert capture.freeze() is None


def limit_error():
    import httpx
    from openai import BadRequestError
    return BadRequestError('context window exceeded', response=httpx.Response(400,
        request=httpx.Request('POST', 'https://example.invalid/v1')), body={
            'error': {'code': 'context_length_exceeded', 'message': 'context window exceeded'}})


@pytest.mark.parametrize('error', [limit_error(), RuntimeError('HTTP 400 invalid parameter')])
def test_empty_limit_error_and_unrelated_error_cannot_become_partial(error):
    from agent.compression_partial import PartialCapture, capture_scope
    def stream():
        if False:
            yield chunk()
        raise error
    with capture_scope(PartialCapture()), pytest.raises(type(error)):
        aux._aggregate_chat_stream(stream())


def anthropic_timeout_summary(text):
    class Stream:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            return False
        def __iter__(self):
            yield SimpleNamespace(type='content_block_delta', delta=SimpleNamespace(text=text))
            raise TimeoutError('stream read timed out')
        def get_final_message(self):
            raise AssertionError('the stream did not complete')
    client = SimpleNamespace(messages=SimpleNamespace(stream=lambda **kw: Stream()))
    return aux._AnthropicCompletionsAdapter(client, 'test/model').create(
        model='test/model', messages=[{'role': 'user', 'content': 'Summarize'}])


def responses_timeout_summary(text):
    def stream():
        yield SimpleNamespace(type='response.output_text.delta', delta=text,
                              output_index=0, content_index=0, item_id='item-one')
        raise TimeoutError('stream read timed out')
    client = SimpleNamespace(base_url='https://example.invalid/v1',
                             responses=SimpleNamespace(create=lambda **kw: stream()))
    return aux._CodexCompletionsAdapter(client, 'test/model').create(
        model='test/model', messages=[{'role': 'user', 'content': 'Summarize'}])


def test_reasoning_fallback_survives_partial_timeout():
    from agent.compression_partial import PartialCapture, capture_scope
    def stream():
        yield chunk(reasoning='Available reasoning handoff')
        raise TimeoutError('read timed out')
    with capture_scope(PartialCapture()):
        response = aux._aggregate_chat_stream(stream())
    assert aux.extract_content_or_reasoning(response) == 'Available reasoning handoff'
    assert response.choices[0].finish_reason == 'timeout'
