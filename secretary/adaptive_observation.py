"""Conservative server-ingress observation spans on existing host ticks.

No new scheduler. Gaps beyond the existing polling cadence break coverage;
unsaved tails are lost on crashes, never invented as observed idle time.
"""
from __future__ import annotations

import json
import logging
import threading
import time
import uuid

from secretary import adaptive_config, adaptive_store

logger = logging.getLogger(__name__)
_lock = threading.RLock()
_segments = {}
MAX_TRACKED_OWNERS = 512


def touch_gateway_session(db, session_id):
    """The caller has verified this session's live adapter handler."""
    try:
        if db is None or not adaptive_config.for_db(db):
            return
        ref = db.resolve_conversation_ref(session_id)
        if ref:
            touch(db, ref, scope='gateway_adapter', at=time.time(),
                  monotonic=time.monotonic(), maximum_gap=20.0)
    except Exception:
        logger.debug('Adaptive gateway coverage unavailable', exc_info=True)


def touch_profile(db, *, scope, at=None, monotonic=None, maximum_gap=20.0):
    """Only the process owning an instrumented ingress may certify its scope."""
    try:
        config = adaptive_config.for_db(db)
        if not config or scope not in ('web_submit', 'gateway_adapter'):
            return
        now = time.time() if at is None else at
        clock = time.monotonic() if monotonic is None else monotonic
        with db._read_ctx() as conn:
            refs = [row[0] for row in conn.execute(
                "SELECT conversation_ref FROM secretary_heartbeats WHERE status='active' LIMIT 512")]
        for ref in refs:
            touch(db, ref, scope=scope, at=now, monotonic=clock, maximum_gap=maximum_gap)
    except Exception:
        logger.debug('Adaptive observation coverage unavailable', exc_info=True)


def touch(db, ref, *, scope, at, monotonic, maximum_gap):
    key = (str(getattr(db, 'db_path', id(db))), ref, scope)
    with _lock:
        state = _segments.get(key)
        if state and (monotonic <= state['clock'] or monotonic - state['clock'] > maximum_gap
                      or abs((at - state['at']) - (monotonic - state['clock'])) > 2):
            state = None
        if state is None:
            if len(_segments) >= MAX_TRACKED_OWNERS:
                _segments.pop(next(iter(_segments)))
            state = dict(start=at, at=at, clock=monotonic, flushed=at,
                         identity='coverage:' + uuid.uuid4().hex)
            _segments[key] = state
            return
        state['at'], state['clock'] = at, monotonic
        if at - state['flushed'] < 60:
            return
        event = dict(event_id=state['identity'], at=at, kind='coverage', source='user',
                     verified=True, scope=scope, start_at=state['start'], end_at=at)
        def write(conn):
            payload = json.dumps(event, allow_nan=False, separators=(',', ':'))
            updated = conn.execute('UPDATE secretary_adaptive_events SET at=?,payload=? '
                                   'WHERE conversation_ref=? AND event_id=?',
                                   (at, payload, ref, state['identity'])).rowcount
            if not updated:
                adaptive_store.event_conn(conn, ref, event)
        db._execute_write(write)
        state['flushed'] = at
