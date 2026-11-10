"""Real native stream/Steer and transport admission share the replay sequence order."""
from __future__ import annotations

import asyncio
import copy
import io
import json
import threading
import time
import socket
from types import SimpleNamespace

import pytest
from openai.types.chat import ChatCompletionChunk
from fastapi import WebSocket

from tests.tui_gateway.test_pending_native_turn import live as live
from tui_gateway import event_replay, inflight_output, server, transport
from tui_gateway.ws import WSTransport

_NATIVE_EMIT = server._emit


class Peer:
    def __init__(self):
        self.frames = []

    def write(self, obj):
        self.frames.append(copy.deepcopy(obj))
        return True

    def close(self):
        pass


def _drain(fan):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        with fan._lock:
            if not any(p.pending_frames or p.writing for p in fan._peers):
                return
        time.sleep(.001)
    raise AssertionError('fanout did not drain')


def _assert_order(frames, sid='runtime'):
    events = [f['params'] for f in frames if f.get('method') == 'event' and f['params'].get('session_id') == sid]
    seqs = [e['seq'] for e in events]
    assert seqs == sorted(set(seqs)), seqs
    by_seq = {e['seq']: e for e in events}
    for event in events:
        if event['type'] == 'message.output_delta':
            payload = event['payload']
            legacy = by_seq[payload['source_event_seq']]
            assert legacy['type'] == payload['native_type']
            assert legacy['payload'] == payload['native_payload']
    return events


def _rpc(method, **params):
    return server.handle_request({'id': method, 'method': method, 'params': {'session_id': 'runtime', **params}})


def test_native_stream_steer_and_internal_notice_preserve_fanout_order(live, monkeypatch):
    """The D-S01 barrier is after real stamping, before real Fanout queue admission."""
    rt = live
    record = server._deferred_session_record('stored', cols=80, cwd=str(rt.home), history=[], lease=None,
                                            profile_home=rt.home)
    record.update(agent=rt.agent, _sid='runtime', show_reasoning=True)
    record['agent_ready'].set()
    rt.session.clear()
    rt.session.update(record)
    assert type(rt.session['history_lock']) is type(threading.Lock())
    (rt.home / 'config.yaml').write_text((rt.home / 'config.yaml').read_text() + f'terminal:\n  cwd: {rt.home}\n')
    peers = [Peer(), Peer()]
    fan = transport.FanoutTransport(*peers)
    rt.session['transport'] = fan
    monkeypatch.setattr(server, '_emit', _NATIVE_EMIT)
    for name, callback in server._agent_cbs('runtime').items():
        monkeypatch.setattr(rt.agent, name, callback, raising=False)
    event_replay.reset_replay_state()
    blocked, release, finish, steer_done = (threading.Event() for _ in range(4))
    rt.releases.extend([release, finish])
    original_serialize = transport.serialize_frame
    held = []
    def serialize(obj, peer, log):
        params = obj.get('params') or {}
        if peer == 'fanout' and params.get('type') == 'message.delta' and not held:
            held.append(params['seq'])
            blocked.set()
            assert release.wait(5)
        return original_serialize(obj, peer, log)
    monkeypatch.setattr(transport, 'serialize_frame', serialize)
    def chunk(**delta):
        reason = delta.pop('finish_reason', None)
        return ChatCompletionChunk(id='synthetic', created=1, model='test/model', object='chat.completion.chunk',
            choices=[{'index': 0, 'delta': delta, 'finish_reason': reason}])
    def provider(**kwargs):
        def stream():
            yield chunk(role='assistant', reasoning_content='Synthetic reasoning.')
            yield chunk(content='Synthetic live text.')
            assert finish.wait(5)
            yield chunk(finish_reason='stop')
        return stream()
    monkeypatch.setattr(rt.agent, '_create_request_openai_client', lambda **kwargs:
        SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=provider)), close=lambda: None))
    rt.agent._disable_streaming = False
    workers = []
    original_work = server._start_session_work
    def work(*args, **kwargs):
        worker = original_work(*args, **kwargs)
        if worker is not None:
            workers.append(worker)
        return worker
    monkeypatch.setattr(server, '_start_session_work', work)
    responses = []
    def steer():
        responses.append(_rpc('session.steer_pending', turn_id=rt.agent._current_turn_id,
                              operation_id='ordered-steer', text='Synthetic correction'))
        steer_done.set()
    steering = threading.Thread(target=steer)
    notice = threading.Thread(target=lambda: server._emit('status.update', 'runtime', {'kind': 'heartbeat', 'text': 'Synthetic notice'}))
    try:
        assert _rpc('prompt.submit', text='Synthetic user')['result']['status'] == 'streaming'
        assert blocked.wait(5)
        steering.start()
        notice.start()
        # Old code admits the higher-seq Steer while this lower-seq delta is paused.
        steer_done.wait(.05)
    finally:
        release.set()
        if steering.ident is not None:
            steering.join(5)
        if notice.ident is not None:
            notice.join(5)
        finish.set()
        for worker in workers:
            worker.join(10)
        _drain(fan)
        fan.close()
    assert not steering.is_alive() and not notice.is_alive()
    assert responses[0]['result']['accepted']
    assert all(not worker.is_alive() for worker in workers)
    replay = event_replay.events_since('runtime', 0)
    for peer in peers:
        events = _assert_order(peer.frames)
        assert [e['seq'] for e in events] == [e['seq'] for e in replay]
    assert peers[0].frames == peers[1].frames
    assert any(e['type'] == 'steer.pending_changed' for e in replay)
    assert any(e['type'] == 'status.update' and e['payload']['kind'] == 'heartbeat' for e in replay)


@pytest.mark.parametrize('kind', ['fanout', 'stdio', 'ws'])
def test_parallel_emit_stamping_matches_each_transport_admission(monkeypatch, tmp_path, kind):
    """A scheduling pause in serialization cannot let a later event overtake its seq."""
    async def run():
        peer = Peer()
        class Socket:
            async def send_text(self, text):
                peer.frames.append(json.loads(text))
        output = io.StringIO()
        target = (transport.FanoutTransport(peer) if kind == 'fanout' else
                  transport.StdioTransport(lambda: output, threading.Lock()) if kind == 'stdio' else
                  WSTransport(Socket(), asyncio.get_running_loop()))
        event_replay.reset_replay_state()
        session = server._deferred_session_record('ordered', cols=80, cwd=str(tmp_path), history=[], lease=None)
        session['transport'] = target
        monkeypatch.setattr(server, '_sessions', {'runtime': session})
        blocked, release, attempted = (threading.Event() for _ in range(3))
        serial = transport.serialize_frame
        def pause(obj, label, log):
            if (obj.get('params') or {}).get('type') == 'message.delta':
                blocked.set()
                assert release.wait(5)
            return serial(obj, label, log)
        monkeypatch.setattr(transport, 'serialize_frame', pause)
        monkeypatch.setattr('tui_gateway.ws.serialize_frame', pause)
        def emit(kind):
            return server._emit(kind, 'runtime', {'text': 'Synthetic'} if kind == 'message.delta' else {'kind': 'heartbeat', 'text': 'Synthetic'})
        def later():
            attempted.set()
            emit('status.update')
        first = asyncio.create_task(asyncio.to_thread(emit, 'message.delta'))
        assert await asyncio.to_thread(blocked.wait, 5)
        second = asyncio.create_task(asyncio.to_thread(later))
        assert await asyncio.to_thread(attempted.wait, 5)
        await asyncio.sleep(.03)
        release.set()
        await asyncio.gather(first, second)
        if kind == 'fanout':
            await asyncio.to_thread(_drain, target)
            target.close()
        elif kind == 'stdio':
            peer.frames = [json.loads(line) for line in output.getvalue().splitlines()]
        else:
            async with asyncio.timeout(5):
                while len(peer.frames) < 2:
                    await asyncio.sleep(.001)
            target.close()
        assert [e['seq'] for e in _assert_order(peer.frames)] == [1, 2]
    asyncio.run(run())


def test_captured_direct_peer_rechecks_route_after_fanout_attachment(monkeypatch, tmp_path):
    async def run():
        delivered = Peer()
        class Socket:
            async def send_text(self, text):
                delivered.frames.append(json.loads(text))
        peer = WSTransport(Socket(), asyncio.get_running_loop())
        newcomer = Peer()
        session = server._deferred_session_record('ordered', cols=80, cwd=str(tmp_path), history=[], lease=None)
        session['transport'] = peer
        monkeypatch.setattr(server, '_sessions', {'runtime': session})
        event_replay.reset_replay_state()
        captured, release = threading.Event(), threading.Event()
        entry = 'write_ordered' if hasattr(peer, 'write_ordered') else 'write'
        original = getattr(peer, entry)
        def pause(*args, **kwargs):
            captured.set()
            assert release.wait(5)
            return original(*args, **kwargs)
        monkeypatch.setattr(peer, entry, pause)
        def emit(text):
            return server._emit('status.update', 'runtime', {'kind': 'heartbeat', 'text': text})
        first = asyncio.create_task(asyncio.to_thread(emit, 'first caller'))
        assert await asyncio.to_thread(captured.wait, 5)
        assert server._attach_session_transport(session, newcomer)
        fan = session['transport']
        assert isinstance(fan, transport.FanoutTransport)
        try:
            await asyncio.to_thread(emit, 'later caller admitted first')
            async with asyncio.timeout(5):
                while not delivered.frames:
                    await asyncio.sleep(.001)
            release.set()
            await first
            await asyncio.to_thread(_drain, fan)
            assert [e['seq'] for e in _assert_order(delivered.frames)] == [1, 2]
            assert [e['seq'] for e in _assert_order(newcomer.frames)] == [1, 2]
        finally:
            release.set()
            fan.close()
            peer.close()
    asyncio.run(run())


def test_hook_keeps_stamped_seq_and_can_emit_recursively_after_admission(monkeypatch, tmp_path):
    output = io.StringIO()
    primary = transport.StdioTransport(lambda: output, threading.Lock())
    sidecar = Peer()
    tee = transport.TeeTransport(primary, sidecar)
    session = server._deferred_session_record('ordered', cols=80, cwd=str(tmp_path), history=[], lease=None)
    session['transport'] = tee
    monkeypatch.setattr(server, '_sessions', {'runtime': session})
    event_replay.reset_replay_state()
    hooks = []
    def project(frame, _sessions):
        hooks.append(frame['params']['seq'])
        assert event_replay._replay_lock.acquire(timeout=.1)
        event_replay._replay_lock.release()
        if frame['params']['seq'] == 1:
            server._emit('status.update', 'runtime', {'kind': 'heartbeat', 'text': 'recursive synthetic hook'})
    monkeypatch.setattr('tui_gateway.hosted_room_member_activity.project_room_member_activity', project)
    thread = threading.Thread(target=lambda: server._emit('message.delta', 'runtime', {'text': 'synthetic'}), daemon=True)
    thread.start()
    thread.join(5)
    assert not thread.is_alive(), 'hook ran inside the non-reentrant output lock'
    assert hooks == [1, 2]
    main = [json.loads(line) for line in output.getvalue().splitlines()]
    assert main == sidecar.frames
    assert [e['seq'] for e in _assert_order(main)] == [1, 2]


def test_slow_ws_send_does_not_hold_admission_or_replay(monkeypatch, tmp_path):
    async def run():
        started, release = asyncio.Event(), asyncio.Event()
        delivered = Peer()
        class Socket:
            async def send_text(self, text):
                started.set()
                await release.wait()
                delivered.frames.append(json.loads(text))
        peer = WSTransport(Socket(), asyncio.get_running_loop())
        session = server._deferred_session_record('ordered', cols=80, cwd=str(tmp_path), history=[], lease=None)
        session['transport'] = peer
        monkeypatch.setattr(server, '_sessions', {'runtime': session})
        event_replay.reset_replay_state()
        first = asyncio.create_task(asyncio.to_thread(server._emit, 'status.update', 'runtime',
                                                      {'kind': 'heartbeat', 'text': 'blocked socket'}))
        await asyncio.wait_for(started.wait(), 5)
        try:
            assert await asyncio.wait_for(asyncio.to_thread(server._emit, 'message.delta', 'runtime', {'text': 'later'}), 1)
            assert not first.done()
            assert [e['seq'] for e in event_replay.events_since('runtime', 0)] == [1, 2]
        finally:
            release.set()
            await first
            await peer.write_async({'id': 'flush', 'result': {}})
            peer.close()
        assert [e['seq'] for e in _assert_order(delivered.frames)] == [1, 2]
    asyncio.run(run())


def test_relay_rewrites_exact_legacy_reference_after_ordered_admission(monkeypatch, tmp_path):
    peer = Peer()
    fan = transport.FanoutTransport(peer)
    session = server._deferred_session_record('ordered', cols=80, cwd=str(tmp_path), history=[], lease=None)
    session['transport'] = fan
    monkeypatch.setattr(server, '_sessions', {'runtime': session})
    event_replay.reset_replay_state()
    scope = {'turn_id': 'synthetic-turn', 'stored_session_id': 'stored',
             'conversation_ref': 'synthetic-conversation', 'message_uid': 'synthetic-uid'}
    def relay(kind, sequence, payload):
        return server.write_json({'jsonrpc': '2.0', 'method': 'event', 'params': {
            'type': kind, 'session_id': 'runtime', 'seq': sequence, 'payload': payload}})
    relay('message.output_state', 100, {**scope, 'state': 'open'})
    relay('reasoning.delta', 101, {'text': 'synthetic relay'})
    server._emit('status.update', 'runtime', {'kind': 'heartbeat', 'text': 'parent notice'})
    relay('message.output_delta', 102, {**scope, 'native_type': 'reasoning.delta',
        'native_payload': {'text': 'synthetic relay'}, 'source_event_seq': 101})
    _drain(fan)
    fan.close()
    events = _assert_order(peer.frames)
    assert [e['seq'] for e in events] == [1, 2, 3, 4]
    assert events[-1]['payload']['source_event_seq'] == 2


def test_real_loopback_two_ws_clients_receive_stamp_order(monkeypatch, tmp_path):
    import uvicorn
    from fastapi import FastAPI
    from websockets.asyncio.client import connect
    peers = []
    app = FastAPI()
    @app.websocket('/order')
    async def route(ws: WebSocket):
        await ws.accept()
        peer = WSTransport(ws, asyncio.get_running_loop())
        peers.append(peer)
        try:
            await ws.receive_text()
        except Exception:
            pass
        finally:
            peer.close()
    async def run():
        listener = socket.socket()
        listener.bind(('127.0.0.1', 0))
        listener.listen(16)
        port = listener.getsockname()[1]
        service = uvicorn.Server(uvicorn.Config(app, log_level='error', lifespan='off', ws_ping_interval=None))
        service.install_signal_handlers = lambda: None
        serving = asyncio.create_task(service.serve(sockets=[listener]))
        try:
            while not service.started:
                await asyncio.sleep(.001)
            async with connect(f'ws://127.0.0.1:{port}/order') as one, connect(f'ws://127.0.0.1:{port}/order') as two:
                fan = transport.FanoutTransport(*peers)
                session = server._deferred_session_record('ordered', cols=80, cwd=str(tmp_path), history=[], lease=None)
                session['transport'] = fan
                monkeypatch.setattr(server, '_sessions', {'runtime': session})
                event_replay.reset_replay_state()
                blocked, release = threading.Event(), threading.Event()
                serial = transport.serialize_frame
                def pause(obj, label, log):
                    if (obj.get('params') or {}).get('type') == 'message.delta':
                        blocked.set()
                        assert release.wait(5)
                    return serial(obj, label, log)
                monkeypatch.setattr(transport, 'serialize_frame', pause)
                first = asyncio.create_task(asyncio.to_thread(server._emit, 'message.delta', 'runtime', {'text': 'synthetic'}))
                assert await asyncio.to_thread(blocked.wait, 5)
                second = asyncio.create_task(asyncio.to_thread(server._emit, 'status.update', 'runtime', {'kind': 'heartbeat', 'text': 'synthetic'}))
                await asyncio.sleep(.03)
                release.set()
                await asyncio.gather(first, second)
                for client in (one, two):
                    frames = [json.loads(await asyncio.wait_for(client.recv(), 5)) for _ in range(2)]
                    assert [e['seq'] for e in _assert_order(frames)] == [1, 2]
                fan.close()
        finally:
            service.should_exit = True
            await asyncio.wait_for(serving, 5)
            listener.close()
    asyncio.run(run())


def test_direct_nonstream_admitted_before_fanout_attachment_keeps_wire_order(monkeypatch, tmp_path):
    async def run():
        delivered = Peer()
        class Socket:
            async def send_text(self, text):
                delivered.frames.append(json.loads(text))
        peer = WSTransport(Socket(), asyncio.get_running_loop())
        newcomer = Peer()
        session = server._deferred_session_record('ordered', cols=80, cwd=str(tmp_path), history=[], lease=None)
        session['transport'] = peer
        monkeypatch.setattr(server, '_sessions', {'runtime': session})
        event_replay.reset_replay_state()
        blocked, release, fan_entered = (threading.Event() for _ in range(3))
        serial = transport.serialize_frame
        def pause(obj, label, log):
            if (obj.get('params') or {}).get('seq') == 1:
                blocked.set()
                assert release.wait(5)
            return serial(obj, label, log)
        monkeypatch.setattr('tui_gateway.ws.serialize_frame', pause)
        original = peer.write_lines_async
        async def entering(*args, **kwargs):
            fan_entered.set()
            return await original(*args, **kwargs)
        monkeypatch.setattr(peer, 'write_lines_async', entering)
        def unblock():
            assert fan_entered.wait(5)
            release.set()
        unblocker = threading.Thread(target=unblock, daemon=True)
        first = asyncio.create_task(asyncio.to_thread(server._emit, 'status.update', 'runtime',
                                                      {'kind': 'heartbeat', 'text': 'before attachment'}))
        assert await asyncio.to_thread(blocked.wait, 5)
        assert server._attach_session_transport(session, newcomer)
        fan = session['transport']
        unblocker.start()
        try:
            await asyncio.to_thread(server._emit, 'status.update', 'runtime',
                                    {'kind': 'heartbeat', 'text': 'after attachment'})
            await first
            await asyncio.to_thread(_drain, fan)
            assert [e['seq'] for e in _assert_order(delivered.frames)] == [1, 2]
            assert [e['seq'] for e in _assert_order(newcomer.frames)] == [2]
        finally:
            release.set()
            unblocker.join(5)
            fan.close()
            peer.close()
    asyncio.run(run())


def test_multiple_producers_share_each_healthy_subscription_order(monkeypatch, tmp_path):
    peers = [Peer() for _ in range(3)]
    fan = transport.FanoutTransport(*peers)
    session = server._deferred_session_record('ordered', cols=80, cwd=str(tmp_path), history=[], lease=None)
    session['transport'] = fan
    monkeypatch.setattr(server, '_sessions', {'runtime': session})
    event_replay.reset_replay_state()
    start = threading.Barrier(4)
    failures = []
    def produce():
        try:
            start.wait(5)
            for _ in range(80):
                assert server._emit('status.update', 'runtime', {'kind': 'heartbeat', 'text': 'synthetic'})
        except Exception as exc:
            failures.append(exc)
    workers = [threading.Thread(target=produce) for _ in range(4)]
    try:
        for worker in workers:
            worker.start()
        for worker in workers:
            worker.join(10)
        assert not failures
        assert all(not worker.is_alive() for worker in workers)
        _drain(fan)
        for peer in peers:
            assert [e['seq'] for e in _assert_order(peer.frames)] == list(range(1, 321))
        assert peers[0].frames == peers[1].frames == peers[2].frames
    finally:
        fan.close()


@pytest.mark.parametrize('outcome', ['gone', 'error'])
@pytest.mark.parametrize('kind', ['plain', 'ws_subclass', 'tee_primary_subclass'])
def test_legacy_custom_transport_retains_result_and_hook_on_failed_io(monkeypatch, tmp_path, outcome, kind):
    error = OSError('synthetic disk full')
    base = WSTransport if kind == 'ws_subclass' else transport.StdioTransport if kind == 'tee_primary_subclass' else object
    class Legacy(base):
        def __init__(self):
            pass
        def write(self, obj):
            if outcome == 'error':
                raise error
            return False
    peer = Legacy()
    if kind == 'tee_primary_subclass':
        peer = transport.TeeTransport(peer, Peer())
    session = server._deferred_session_record('ordered', cols=80, cwd=str(tmp_path), history=[], lease=None)
    session['transport'] = peer
    monkeypatch.setattr(server, '_sessions', {'runtime': session})
    event_replay.reset_replay_state()
    hooks = []
    monkeypatch.setattr('tui_gateway.hosted_room_member_activity.project_room_member_activity',
                        lambda obj, _sessions: hooks.append(obj['params']['seq']))
    if outcome == 'error':
        with pytest.raises(OSError) as caught:
            server._emit('status.update', 'runtime', {'kind': 'heartbeat', 'text': 'synthetic'})
        assert caught.value is error
    else:
        assert server._emit('status.update', 'runtime', {'kind': 'heartbeat', 'text': 'synthetic'}) is False
    assert hooks == [1]
    assert [e['seq'] for e in event_replay.events_since('runtime', 0)] == [1]


def test_overflow_close_hook_can_emit_after_both_fanout_locks_release(monkeypatch, tmp_path):
    healthy = Peer()
    started, release, closed = (threading.Event() for _ in range(3))
    class Slow(Peer):
        def write(self, obj):
            started.set()
            assert release.wait(5)
            return True
        def close(self):
            assert fan._lock.acquire(timeout=2)
            fan._lock.release()
            assert fan._admission_lock.acquire(timeout=2)
            fan._admission_lock.release()
            server._emit('status.update', 'runtime', {'kind': 'heartbeat', 'text': 'overflow hook'})
            release.set()
            closed.set()
    slow = Slow()
    fan = transport.FanoutTransport(healthy, slow)
    session = server._deferred_session_record('ordered', cols=80, cwd=str(tmp_path), history=[], lease=None)
    session['transport'] = fan
    monkeypatch.setattr(server, '_sessions', {'runtime': session})
    event_replay.reset_replay_state()
    try:
        assert server._emit('message.delta', 'runtime', {'text': 'x' * (5 * 1024 * 1024)})
        assert started.wait(5)
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            with fan._lock:
                healthy_peer = next(p for p in fan._peers if p.transport is healthy)
                if not healthy_peer.pending_frames:
                    break
            time.sleep(.001)
        else:
            raise AssertionError('healthy large frame did not drain')
        assert server._emit('message.delta', 'runtime', {'text': 'y' * (5 * 1024 * 1024)})
        assert closed.wait(5)
        _drain(fan)
        assert fan.contains(healthy) and not fan.contains(slow)
        assert [e['seq'] for e in _assert_order(healthy.frames)] == [1, 2, 3]
    finally:
        release.set()
        fan.close()


@pytest.mark.parametrize('later', ['on_loop', 'flush', 'async'])
def test_loop_send_paths_cannot_overtake_admitted_worker_callback(monkeypatch, later):
    """Keep the event loop occupied until worker admission; its callback is still pending."""
    from agent import async_utils
    async def run():
        delivered = Peer()
        class Socket:
            async def send_text(self, text):
                delivered.frames.append(json.loads(text))
        peer = WSTransport(Socket(), asyncio.get_running_loop())
        admitted = threading.Event()
        schedule = async_utils.safe_schedule_threadsafe
        def scheduled(*args, **kwargs):
            future = schedule(*args, **kwargs)
            admitted.set()
            return future
        monkeypatch.setattr(async_utils, 'safe_schedule_threadsafe', scheduled)
        def frame(seq, kind='status.update'):
            return {'jsonrpc': '2.0', 'method': 'event', 'params': {
                'session_id': 'runtime', 'type': kind, 'seq': seq,
                'payload': {'kind': 'heartbeat', 'text': 'synthetic'}}}
        results = []
        worker = threading.Thread(target=lambda: results.append(peer.write(frame(1))))
        worker.start()
        try:
            # This synchronous barrier intentionally prevents the loop from running the
            # worker's callback before the competing on-loop path is admitted.
            assert admitted.wait(5)
            if later == 'on_loop':
                assert peer.write(frame(2))
            elif later == 'flush':
                assert peer.write(frame(2, 'reasoning.delta'))
                peer._flush_tokens()
            else:
                assert await peer.write_async(frame(2))
            await asyncio.to_thread(worker.join, 5)
            assert not worker.is_alive() and results == [True]
            async with asyncio.timeout(5):
                while len(delivered.frames) < 2:
                    await asyncio.sleep(.001)
            assert [e['seq'] for e in _assert_order(delivered.frames)] == [1, 2]
        finally:
            peer.close()
    asyncio.run(run())


def test_large_frame_serialization_does_not_block_completed_send_credit(monkeypatch):
    sending, sent, serializing, release = (threading.Event() for _ in range(4))
    class Controlled(Peer):
        def write(self, obj):
            if obj['params']['seq'] == 1:
                sending.set()
                assert sent.wait(5)
            return super().write(obj)
    peer = Controlled()
    fan = transport.FanoutTransport(peer)
    serial = transport.serialize_frame
    def pause(obj, label, log):
        if obj['params']['seq'] == 2:
            serializing.set()
            assert release.wait(5)
        return serial(obj, label, log)
    monkeypatch.setattr(transport, 'serialize_frame', pause)
    def frame(seq):
        return {'jsonrpc': '2.0', 'method': 'event', 'params': {
            'session_id': 'runtime', 'type': 'message.delta', 'seq': seq,
            'payload': {'text': 'x' * (5 * 1024 * 1024)}}}
    results = []
    second = threading.Thread(target=lambda: results.append(fan.write(frame(2))))
    try:
        assert fan.write(frame(1))
        assert sending.wait(5)
        second.start()
        assert serializing.wait(5)
        sent.set()
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            assert fan._lock.acquire(timeout=2), 'serialization held the drain membership lock'
            try:
                assert fan._peers and fan._peers[0].attached
                pending = fan._peers[0].pending_frames
            finally:
                fan._lock.release()
            if not pending:
                break
            time.sleep(.001)
        else:
            raise AssertionError('completed send credit waited for unrelated serialization')
        release.set()
        second.join(5)
        assert not second.is_alive() and results == [True]
        _drain(fan)
        assert [e['seq'] for e in _assert_order(peer.frames)] == [1, 2]
    finally:
        sent.set()
        release.set()
        if second.ident is not None:
            second.join(5)
        fan.close()
