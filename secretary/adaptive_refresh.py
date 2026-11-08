"""Reevaluate committed evidence at existing owner and host-tick boundaries."""
from __future__ import annotations

import json
import logging
import time

from secretary import adaptive_config as settings, adaptive_store as store

logger = logging.getLogger(__name__)


def _facts(conn, db, ref, parent, now):
    from secretary.heartbeat_route import heartbeat_route_conn
    from secretary.noting_scope import is_current_main_runtime
    from secretary.noting_timers import main_turn_running
    route = heartbeat_route_conn(db, conn, ref)
    hb = conn.execute('SELECT * FROM secretary_heartbeats WHERE conversation_ref=?', (ref,)).fetchone()
    if not route or not hb or hb['status'] != 'active':
        return None
    if parent is not None and (not is_current_main_runtime(parent) or parent.session_id != route['id']
                               or main_turn_running(parent)):
        return None
    lease_key = db._session_turn_lease_key_on_conn(conn, route['id'])
    if conn.execute('SELECT 1 FROM session_turn_leases WHERE conversation_id=? AND expires_at>?',
                    (lease_key, now)).fetchone():
        return None
    if conn.execute('SELECT 1 FROM compression_locks WHERE session_id=? AND expires_at>?',
                    (route['id'], now)).fetchone():
        return None
    epoch = conn.execute('SELECT interval_id FROM secretary_noting_compaction_state WHERE conversation_ref=?',
                         (ref,)).fetchone()
    events = conn.execute('SELECT MAX(id) FROM secretary_adaptive_events WHERE conversation_ref=?', (ref,)).fetchone()[0]
    return dict(route=dict(route), heartbeat=dict(hb), period=db.noting_idle_state_conn(conn, ref),
                epoch=epoch[0] if epoch else None, events=events, refresh=store.refresh_conn(conn, ref),
                mode=store.heartbeat_conn(conn, ref), plan=store.plan_conn(conn, ref))


def _needed(facts, mode, config):
    request = facts['refresh']
    pending = json.loads(mode['pending']) if mode and mode.get('pending') else {}
    current_version = pending.get('config_version') or (mode['config_version'] if mode else None)
    return bool(current_version != config['config_version']
                or request and request['revision'] > request['evaluated_revision'])


def _cold_snapshot(db, ref, config, facts, now):
    """No runtime construction, model call, or inferred current context/cache."""
    from secretary.adaptive_runtime import _next_reminder
    from secretary.adaptive_bootstrap import read
    from secretary.noting_scope import settings_for_db
    from secretary.noting_runtime import noting_local_enabled
    from secretary.adaptive_model_config import digest
    from secretary.adaptive_features import clean_events
    history = store.history(db, ref, now)
    events = clean_events(history, now)
    contract = config['model_contract']
    model_key = digest(contract)
    context_contract = [contract['context_length'], contract['threshold_tokens']]
    observations = [e for e in events if e['kind'] in ('context_read', 'turn_end')
                    and e.get('model_key') == model_key and e.get('context_epoch') == facts['epoch']
                    and e.get('context_contract') == context_contract
                    and e.get('context_path') == [facts['route']['id'], facts['route']['rewind_count']]]
    usage = observations[-1].get('context_tokens') if observations else None
    users = [e['at'] for e in events if e['kind'] == 'user_activity' and e.get('source') == 'user']
    maintenance = [e['at'] for e in events if e['kind'] == 'maintenance_end']
    hb = facts['heartbeat']
    with db._read_ctx() as conn:
        mode = store.heartbeat_conn(conn, ref)
    valid = bool(mode and mode['config_version'] == config['config_version'])
    anchor = hb['last_fired_at'] or hb['created_at'] or (mode['fallback_anchor'] if valid else 0)
    interval = mode['interval_seconds'] if valid else hb['interval_seconds']
    current = settings_for_db(db, ref)
    reminder, known = _next_reminder(db, ref, now)
    return dict(now=now, conversation_ref=ref, context_tokens=usage, context_limit=contract['context_length'],
                native_threshold_tokens=contract['threshold_tokens'], last_user_at=max(users) if users else None,
                last_maintenance_at=max(maintenance) if maintenance else None,
                heartbeat_mode=mode['mode'] if valid else 'business', heartbeat_interval_seconds=interval,
                current_mode_native=not valid, heartbeat_anchor=anchor,
                heartbeat_next_due=anchor + interval if interval is not None else None,
                heartbeat_status=hb['status'], next_reminder_at=reminder, next_reminder_known=known,
                idle_enabled=current.idle_enabled and noting_local_enabled(db, ref), maintenance_running=False,
                idle_period=facts['period'], timezone=config.get('timezone'), model=contract['model'],
                provider=contract['provider'], model_key=model_key, context_epoch=facts['epoch'],
                context_path=[facts['route']['id'], facts['route']['rewind_count']],
                idle_config=[current.idle_enabled, current.idle_delay_seconds, current.idle_threshold_tokens],
                historical_cohorts=store.imported_history(db, ref, now), bootstrap_priors=read(db, ref, now)), history


def _refresh(db, ref, parent, now):
    from secretary.adaptive_policy import decide
    from secretary.adaptive_runtime import context_contract, snapshot
    from secretary.noting_scope import settings_for_db
    with db._read_ctx() as conn:
        config = settings.for_db(db, ref, parent=parent, conn=conn)
        facts = _facts(conn, db, ref, parent, now) if config else None
        mode = store.heartbeat_conn(conn, ref)
    if not facts or config.get('shadow_only') is True or not _needed(facts, mode, config):
        return False
    if not settings_for_db(db, ref).enabled:
        return False
    if parent is not None:
        from agent.compression_read import compression_state
        if compression_state(parent)['active']:
            return False
        measured, history = snapshot(parent, db, ref, config, now)
        # Creating the existing interval is allowed; capture that fact for CAS.
        with db._read_ctx() as conn:
            current = _facts(conn, db, ref, parent, now)
        if current is None:
            return False
        if facts['epoch'] is None:
            facts['epoch'] = current['epoch']
        if facts != current:
            return False
    else:
        measured, history = _cold_snapshot(db, ref, config, facts, now)
    decision = settings.validate_decision(decide(measured, history, config))
    if config.get('shadow_only') is True or decision.get('fallback') is True:
        return False
    decision.update(model_key=measured['model_key'], context_path=measured['context_path'],
                    context_contract=context_contract(parent) if parent is not None else
                    [config['model_contract']['context_length'], config['model_contract']['threshold_tokens']],
                    idle_config=measured['idle_config'])
    revision = facts['refresh']['revision'] if facts['refresh'] else 0

    def guard(conn):
        current = settings.for_db(db, ref, parent=parent, conn=conn)
        idle = settings_for_db(db, ref)
        return bool(idle.enabled and [idle.idle_enabled, idle.idle_delay_seconds, idle.idle_threshold_tokens]
                    == measured['idle_config'] and current and current['config_version'] == config['config_version']
                    and _facts(conn, db, ref, parent, now) == facts)

    adopted = store.refresh_plan(db, ref, at=now, expected_period=facts['period'], decision=decision,
                                 config=config, context_epoch=measured['context_epoch'], revision=revision, guard=guard)
    if adopted and parent is not None:
        from secretary.noting_timers import arm_idle_timer, cancel_idle_timer
        with db._read_ctx() as conn:
            plan, period = store.plan_conn(conn, ref), db.noting_idle_state_conn(conn, ref)
        if period != facts['period']:
            cancel_idle_timer(db, ref, parent=parent)
            if plan and plan['status'] == 'pending' and period['trigger_produced_at'] is None:
                arm_idle_timer(parent, db, ref, period['due_at'])
    return adopted


def refresh(db, ref, *, parent=None, now=None):
    """Best effort notification/recovery. Busy and failed revisions remain pending."""
    from secretary.noting_scope import current_main_runtime
    from secretary.noting_timers import conversation_timer_lock
    try:
        if parent is None:
            candidate = current_main_runtime(db, ref)
            from secretary.noting_scope import is_current_main_runtime
            parent = candidate if candidate is not None and is_current_main_runtime(candidate) else None
        with conversation_timer_lock(db, ref):
            return _refresh(db, ref, parent, time.time() if now is None else now)
    except Exception:
        logger.debug('Adaptive evidence refresh deferred to the next native boundary', exc_info=True)
        return False
