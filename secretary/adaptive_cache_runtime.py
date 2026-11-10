"""Cache-policy wiring at existing reads, claims and Main boundaries; no scheduler."""
from __future__ import annotations

import json
import time

from secretary import adaptive_config as settings, adaptive_store as store


def inspect_conn(db, conn, ref, heartbeat, *, now=None, at=None, config=None, initialize_epoch=False):
    from secretary.adaptive_cache import assess
    from secretary.adaptive_model_config import digest, _target
    moment = time.time() if now is None else now
    config = config or settings.heartbeat_for_db(db, ref, conn=conn)
    if config is None or config.get('shadow_only') is True:
        return None
    if config.get('hot_interval_seconds') is None:
        return config, dict(mode='standby', status='configuration_unavailable',
                            reason='missing_target_hot_interval', source_ids=[], evaluated_at=moment)
    route = _target(db, ref, None, conn)
    epoch = conn.execute('SELECT interval_id FROM secretary_noting_compaction_state WHERE conversation_ref=?',
                         (ref,)).fetchone()
    mode = store.heartbeat_conn(conn, ref)
    anchor = heartbeat['last_fired_at'] or heartbeat['created_at'] or (
        mode['fallback_anchor'] if mode else config.get('_configured_at'))
    epoch = epoch[0] if epoch else (db.noting_compaction_interval_conn(conn, ref) if initialize_epoch else None)
    snapshot = dict(now=moment, heartbeat_anchor=anchor, model_key=digest(config['model_contract']),
                    cache_contract=config.get('cache_contract'), context_epoch=epoch,
                    context_path=[route['id'], route['rewind_count']] if route else None)
    # Cache evidence is only physical Main requests, their legacy identity
    # ends, and successful native maintenance. Do not parse coverage/decision
    # payloads on every load or due scan.
    rows = conn.execute("SELECT payload FROM secretary_adaptive_events WHERE conversation_ref=? AND at<=? "
                        "AND kind IN ('request','request_start','turn_end','maintenance_end') "
                        "ORDER BY at DESC,id DESC LIMIT ?", (ref, moment, store.MAX_HISTORY_EVENTS))
    history = [json.loads(row[0]) for row in reversed(rows.fetchall())]
    evidence = assess(snapshot, history, config, at=at)
    evidence['context_signature'] = digest([snapshot['context_epoch'], snapshot['context_path'], snapshot['cache_contract']])
    return config, evidence


def interval(result):
    config, evidence = result
    return config.get('hot_interval_seconds') if evidence['mode'] == 'hot' else None


def heartbeat_only_decision(snapshot, history, config):
    """An unpriced model can preserve cache; it cannot invent maintenance costs."""
    from secretary.adaptive_cache import assess
    if config.get('hot_interval_seconds') is None:
        evidence = dict(mode='standby', reason='missing_target_hot_interval', status='configuration_unavailable')
    else:
        evidence = assess(snapshot, history, config)
    return dict(mode=evidence['mode'], threshold_tokens=None, delay_seconds=None, fallback=False,
                reason=evidence['reason'], diagnostics=dict(cache=evidence,
                maintenance_deferred=('missing_target_hot_interval' if config.get('hot_interval_seconds') is None
                                      else 'missing_priced_model_configuration')))


def refresh_unpriced(db, ref, parent, now):
    """Existing owner/tick boundary for targets whose maintenance model is unpriced."""
    from secretary.adaptive_refresh import _facts
    from secretary.noting_scope import settings_for_db
    with db._read_ctx() as conn:
        config = settings.heartbeat_for_db(db, ref, parent=parent, conn=conn)
        facts = _facts(conn, db, ref, parent, now) if config else None
        hb = conn.execute('SELECT * FROM secretary_heartbeats WHERE conversation_ref=?', (ref,)).fetchone()
        result = inspect_conn(db, conn, ref, hb, config=config, now=now) if facts else None
    if not facts or config.get('shadow_only') is True or not config.get('_heartbeat_only'):
        return False
    if not settings_for_db(db, ref).enabled:
        return False
    evidence = result[1]
    old = facts['mode']
    request = facts['refresh']
    if (old and old['config_version'] == config['config_version'] and old['mode'] == evidence['mode']
            and (not request or request['revision'] == request['evaluated_revision'])):
        return False
    def write(conn):
        from secretary.adaptive_model_config import selection_is_current
        current = settings.heartbeat_for_db(db, ref, parent=parent, conn=conn)
        if (not current or current['config_version'] != config['config_version']
                or not selection_is_current(db, ref, parent, conn=conn)
                or _facts(conn, db, ref, parent, now) != facts):
            return False
        store.adopt_mode_conn(conn, ref, evidence['mode'], config)
        if request:
            store.acknowledge_refresh_conn(conn, ref, request['revision'])
        return True
    return db._execute_write(write)


def block_first_heartbeat_dispatch(parent, db, ref, config):
    """Only the admitted HB's first physical call can become a new cold probe."""
    if (getattr(parent, '_adaptive_turn_source', None) != 'heartbeat'
            or getattr(parent, '_adaptive_turn_dispatched', False)):
        return False
    moment = time.time()
    with db._read_ctx() as conn:
        heartbeat = conn.execute('SELECT * FROM secretary_heartbeats WHERE conversation_ref=?', (ref,)).fetchone()
        if heartbeat is None or heartbeat['status'] != 'active':
            return False
        result = inspect_conn(db, conn, ref, heartbeat, config=config, now=moment, at=moment)
    return bool(result and result[1]['mode'] == 'standby')
