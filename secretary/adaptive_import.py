"""Explicit, same-profile frozen numeric evidence imports; no live-state transfer."""
from __future__ import annotations

from collections import Counter
from datetime import datetime
import json
from pathlib import Path
import time

from secretary import adaptive_store as store
from secretary.adaptive_features import number

MAX_IMPORT_EVENTS = 2048
MAX_IMPORT_RECEIPTS = 32
KINDS = frozenset(('user_activity', 'turn_end', 'request', 'coverage', 'maintenance_start',
                   'maintenance_end', 'cancel', 'blocked_send', 'gap', 'coverage_gap',
                   'maintenance_exclusion', 'exclusion', 'maintenance_sample'))
NUMBER_FIELDS = frozenset(('at', 'available_at', 'start_at', 'end_at', 'input_tokens',
                          'cache_read_tokens', 'cache_write_tokens', 'output_tokens',
                          'context_tokens', 'context_before', 'context_after', 'duration_seconds',
                          'context_limit', 'context_length', 'threshold_tokens'))
LABEL_FIELDS = frozenset(('event_id', 'kind', 'model_key', 'provider', 'model', 'model_option',
                         'provider_slug', 'model_item', 'api_mode', 'reasoning_effort',
                         'config_version', 'context_epoch', 'turn_id', 'operation_id',
                         'ingress', 'activity', 'scope', 'outcome', 'trigger', 'input_semantics',
                         'duration_scope', 'reason', 'quality'))
BOOL_FIELDS = frozenset(('verified', 'usage_complete', 'idle', 'cancel_requested', 'conflict'))


def _text(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 512:
        raise ValueError(f'invalid {label}')
    return value


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def _profile(db):
    return str(Path(db.db_path).resolve().parent)


def declaration_for_db(db, target_ref):
    """Only the owning Profile's existing config.yaml may declare an import."""
    from hermes_cli.config import load_config_readonly
    from secretary.noting_scope import owning_db_scope

    _text(target_ref, 'target conversation_ref')
    with owning_db_scope(db):
        config = load_config_readonly()
    noting = config.get('noting', {})
    block = noting.get('adaptive_idle_token_saving', {}) if isinstance(noting, dict) else {}
    if not isinstance(block, dict) or block.get('enabled') is not True or noting.get('enabled', True) is not True:
        raise ValueError('adaptive_idle_token_saving is not enabled for this Profile')
    conversations = block.get('conversations', {})
    target = conversations.get(target_ref, {}) if isinstance(conversations, dict) else {}
    if not isinstance(target, dict) or target.get('enabled') is not True:
        raise ValueError('target Conversation is not explicitly enabled')
    value = target.get('history_import')
    if not isinstance(value, dict) or set(value) != {'id', 'from_conversation', 'through'}:
        raise ValueError('history_import requires only id, from_conversation and through')
    identity = _text(value['id'], 'import id')
    source = _text(value['from_conversation'], 'source conversation_ref')
    if source == target_ref:
        raise ValueError('source and target must be different Conversations')
    through = value['through']
    # YAML timestamp scalars may be parsed by the native YAML loader as datetime.
    try:
        stamp = through if isinstance(through, datetime) else datetime.fromisoformat(through)
        if stamp.tzinfo is None or stamp.utcoffset() is None:
            raise ValueError('timezone required')
        cutoff = stamp.timestamp()
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError('history_import.through must be an ISO timestamp with timezone') from exc
    if number(cutoff) is None:
        raise ValueError('invalid history_import cutoff')
    return dict(id=identity, from_conversation=source, through=cutoff)


def _validate_refs(conn, target, source):
    for ref in (target, source):
        if not conn.execute('SELECT 1 FROM secretary_conversations WHERE conversation_ref=?', (ref,)).fetchone():
            raise ValueError(f'unknown Conversation reference in owning Profile: {ref}')


def _model_tags(event):
    result = {}
    identity = event.get('model_identity')
    if isinstance(identity, dict):
        result['model_identity'] = {key: identity[key] for key in ('provider', 'model')
                                    if isinstance(identity.get(key), str) and len(identity[key]) <= 512}
    contract = event.get('model_contract')
    if not isinstance(contract, dict):
        return result
    tags = {key: contract[key] for key in ('provider', 'model', 'api_mode', 'reasoning_effort', 'service_tier')
            if isinstance(contract.get(key), str) and len(contract[key]) <= 512}
    for key in ('context_length', 'threshold_tokens'):
        if key in contract:
            tags[key] = number(contract[key])
    if isinstance(contract.get('fast_mode'), bool):
        tags['fast_mode'] = contract['fast_mode']
    reasoning = contract.get('reasoning_config')
    if reasoning is None:
        tags['reasoning_config'] = None
    elif isinstance(reasoning, dict):
        tags['reasoning_config'] = {key: reasoning[key] for key in ('enabled', 'effort', 'max_tokens')
                                    if isinstance(reasoning.get(key), (str, bool, int))
                                    and len(str(reasoning[key])) <= 128}
    capabilities = contract.get('capabilities')
    if isinstance(capabilities, dict):
        tags['capabilities'] = {key: value for key, value in sorted(capabilities.items())[:32]
                                if isinstance(key, str) and len(key) <= 128 and isinstance(value, bool)}
    result['model_contract'] = tags
    return result


def _project(event):
    """Whitelist native numeric measurements and bounded provenance labels, never text blobs."""
    if not isinstance(event, dict):
        return None
    if event.get('kind') == 'maintenance_sample':
        from secretary.adaptive_samples import normalize_sample
        try:
            return normalize_sample(event)
        except ValueError:
            return None
    if event.get('bootstrap_schema'):
        from secretary.adaptive_bootstrap import project_transfer
        return project_transfer(event)
    if event.get('kind') not in KINDS:
        return None
    if number(event.get('at')) is None:
        return None
    try:
        _text(event.get('event_id'), 'event id')
    except ValueError:
        return None
    result = {key: event[key] for key in LABEL_FIELDS
              if isinstance(event.get(key), str) and 0 < len(event[key]) <= 512}
    for key in NUMBER_FIELDS:
        if key in event:
            result[key] = number(event[key])
    for key in BOOL_FIELDS:
        if isinstance(event.get(key), bool):
            result[key] = event[key]
    result['verified'] = event.get('verified') is True
    source = event.get('source')
    result['source'] = source if source in ('user', 'heartbeat', 'reminder', 'framework') else 'unknown'
    # Absence means the native observation was known at its original receipt time.
    result['available_at'] = number(event.get('available_at', event['at']))
    if result['available_at'] is None:
        return None
    contract = event.get('context_contract')
    if isinstance(contract, (list, tuple)) and len(contract) == 2:
        result['context_contract'] = [number(value) for value in contract]
    reasoning = event.get('reasoning')
    if isinstance(reasoning, str) and len(reasoning) <= 128:
        result['reasoning'] = reasoning
    elif isinstance(reasoning, dict):
        result['reasoning'] = {key: reasoning[key] for key in ('enabled', 'effort', 'max_tokens')
                               if isinstance(reasoning.get(key), (str, bool, int))
                               and len(str(reasoning[key])) <= 128}
    result.update(_model_tags(event))
    return result


def _identity(event):
    return event['origin_profile'], event['origin_conversation'], event['origin_event_id']


def _payload(event):
    return {key: value for key, value in event.items()
            if key not in ('origin_profile', 'origin_conversation', 'origin_event_id', 'imported_at')}


def _candidates(conn, db, target, declaration, now):
    source, cutoff = declaration['from_conversation'], declaration['through']
    excluded, candidates = Counter(), {}
    local = conn.execute('SELECT payload FROM secretary_adaptive_events WHERE conversation_ref=? '
                         'ORDER BY at,id', (source,)).fetchall()
    rows = [{**json.loads(row[0]), 'origin_profile': _profile(db),
             'origin_conversation': source, 'origin_event_id': json.loads(row[0]).get('event_id')}
            for row in local]
    for cohort in store.imported_history_conn(conn, source, now):
        rows.extend(cohort['events'])
    from secretary.adaptive_bootstrap import export_conn
    rows.extend(export_conn(conn, db, source, now))
    conflicts = set()
    for raw in rows:
        if raw.get('bootstrap_receipt'):
            excluded['bootstrap_frontier_is_local_state'] += 1
            continue
        event = _project(raw)
        if event is None:
            excluded['unsupported_or_invalid_numeric_event'] += 1
            continue
        if (event['kind'] == 'maintenance_sample' and event.get('source_kind') == 'conversation'
                and event.get('source_conversation_ref') != target
                and event.get('ownership') in ('verified_native_owner', 'same_target_verified')):
            event['ownership'] = 'other_conversation_verified'
        if max(event['at'], event['available_at']) > min(cutoff, now):
            excluded['after_cutoff_or_not_yet_known'] += 1
            continue
        origin = {key: raw[key] for key in ('origin_profile', 'origin_conversation', 'origin_event_id')}
        if origin['origin_profile'] != _profile(db):
            excluded['cross_profile_origin'] += 1
            continue
        if origin['origin_conversation'] == target:
            excluded['target_origin_cycle'] += 1
            continue
        event.update(origin)
        key = _identity(event)
        if key in candidates and candidates[key] != event:
            conflicts.add(key)
        candidates[key] = event
    for key in conflicts:
        del candidates[key]
        excluded['conflicting_origin'] += 1
    ordered = sorted(candidates.values(), key=lambda event: (event['at'], _identity(event)))
    if len(ordered) > MAX_IMPORT_EVENTS and any(event.get('bootstrap_schema') for event in ordered):
        raise ValueError('source snapshot capacity would truncate a bootstrap training group')
    excluded['snapshot_event_bound'] += max(0, len(ordered) - MAX_IMPORT_EVENTS)
    return ordered[-MAX_IMPORT_EVENTS:], dict(excluded), len(local)


def _model_label(event):
    identity = event.get('model_identity', {})
    if identity.get('provider') and identity.get('model'):
        return f"{identity['provider']} / {identity['model']}"
    model = event.get('model_option') or event.get('model_item') or event.get('model')
    if event.get('provider') and model:
        return f"{event['provider']} / {model}"
    return 'unknown option: ' + event.get('model_key', 'unknown')


def _summary(events, excluded, local_count):
    times = [event['at'] for event in events]
    model_counts = Counter(_model_label(event) for event in events
                           if event['kind'] in ('request', 'turn_end', 'maintenance_end', 'maintenance_sample'))
    cohorts = {}
    for event in events:
        key = event['origin_profile'], event['origin_conversation']
        cohort = cohorts.setdefault(key, dict(origin_profile=key[0], origin_conversation=key[1],
                                               event_count=0, retained_start_at=event['at'],
                                               coverage_intervals=[], exclusions=[]))
        cohort['event_count'] += 1
        cohort['retained_start_at'] = min(cohort['retained_start_at'], event['at'])
        if event['kind'] == 'coverage':
            start, end = number(event.get('start_at')), number(event.get('end_at'))
            if start is not None and end is not None and start < end:
                cohort['coverage_intervals'].append(dict(start_at=start, end_at=end,
                                                         scope=event.get('scope', 'unknown'),
                                                         verified=event['verified'], source=event['source']))
        elif event['kind'] in ('gap', 'coverage_gap', 'maintenance_start', 'maintenance_end',
                              'maintenance_exclusion', 'exclusion'):
            cohort['exclusions'].append(dict(kind=event['kind'], at=event['at'],
                                             start_at=event.get('start_at'), end_at=event.get('end_at')))
    for cohort in cohorts.values():
        cohort['coverage_missing'] = not any(item['verified'] and item['source'] == 'user'
                                             for item in cohort['coverage_intervals'])
    return dict(event_count=len(events), available_range=[min(times), max(times)] if times else None,
                source_local_retained=local_count, source_local_limit=2048,
                target_import_event_limit=MAX_IMPORT_EVENTS, target_receipt_limit=MAX_IMPORT_RECEIPTS,
                verified_events=sum(event['verified'] for event in events),
                unknown_source_events=sum(event['source'] == 'unknown' for event in events),
                quality='numeric_observations_only_no_inferred_identity_or_coverage',
                model_distribution=dict(model_counts.most_common(32)),
                model_distribution_other=sum(count for _, count in model_counts.most_common()[32:]),
                cohorts=list(cohorts.values()), excluded=excluded,
                limitations=['Only retained observations collected while enabled are available.',
                             'Evicted and pre-collection history cannot be recovered.',
                             'No coverage is inferred from silence or message roles.',
                             'Source cohorts are separate; overlapping exposure must not be added twice.'])


def _existing_receipt(conn, target, declaration):
    row = conn.execute('SELECT declaration,receipt,replaced_by FROM secretary_adaptive_imports '
                       'WHERE conversation_ref=? AND import_id=?', (target, declaration['id'])).fetchone()
    if row is None:
        return None
    if row['declaration'] != _json(declaration):
        raise ValueError('import id already exists with a conflicting declaration')
    receipt = json.loads(row['receipt'])
    return {**receipt, 'replaced_by': row['replaced_by']} if row['replaced_by'] else receipt


def preview(db, target_ref, *, now=None):
    """Read-only preview from the current explicit owning-Profile declaration."""
    now = time.time() if now is None else now
    declaration = declaration_for_db(db, target_ref)
    with db._read_ctx() as conn:
        _validate_refs(conn, target_ref, declaration['from_conversation'])
        receipt = _existing_receipt(conn, target_ref, declaration)
        if receipt:
            return {**receipt, 'already_applied': True}
        events, excluded, retained = _candidates(conn, db, target_ref, declaration, now)
    return dict(target_conversation=target_ref, declaration=declaration, already_applied=False,
                **_summary(events, excluded, retained))


def _remove_import(conn, target, identity, replacement):
    row = conn.execute('SELECT replaced_by FROM secretary_adaptive_imports WHERE conversation_ref=? AND import_id=?',
                       (target, identity)).fetchone()
    if row is None or row['replaced_by'] is not None:
        raise ValueError('replace import id does not exist for target Conversation')
    conn.execute('DELETE FROM secretary_adaptive_import_members WHERE conversation_ref=? AND import_id=?',
                 (target, identity))
    conn.execute('UPDATE secretary_adaptive_imports SET replaced_by=? WHERE conversation_ref=? AND import_id=?',
                 (replacement, target, identity))
    conn.execute('DELETE FROM secretary_adaptive_import_events AS e WHERE conversation_ref=? AND NOT EXISTS '
                 '(SELECT 1 FROM secretary_adaptive_import_members m WHERE m.conversation_ref=e.conversation_ref '
                 'AND m.origin_profile=e.origin_profile AND m.origin_conversation=e.origin_conversation '
                 'AND m.origin_event_id=e.origin_event_id)', (target,))


def _freeze(conn, target, declaration, events, receipt, now):
    count = conn.execute('SELECT COUNT(*) FROM secretary_adaptive_imports WHERE conversation_ref=?',
                         (target,)).fetchone()[0]
    if count >= MAX_IMPORT_RECEIPTS:
        raise ValueError('target import receipt capacity exceeded (including replaced receipts)')
    for event in events:
        key = (target, *_identity(event))
        payload = _json(_payload(event))
        previous = conn.execute('SELECT payload FROM secretary_adaptive_import_events WHERE conversation_ref=? '
                                'AND origin_profile=? AND origin_conversation=? AND origin_event_id=?', key).fetchone()
        if previous and previous[0] != payload:
            raise ValueError('original event conflicts with an existing frozen snapshot')
        conn.execute('INSERT OR IGNORE INTO secretary_adaptive_import_events VALUES (?,?,?,?,?,?,?)',
                     (*key, event['at'], event['available_at'], payload))
        conn.execute('INSERT INTO secretary_adaptive_import_members VALUES (?,?,?,?,?)',
                     (target, declaration['id'], *_identity(event)))
    total = conn.execute('SELECT COUNT(*) FROM secretary_adaptive_import_events WHERE conversation_ref=?',
                         (target,)).fetchone()[0]
    if total > MAX_IMPORT_EVENTS:
        raise ValueError('target imported event capacity exceeded; explicitly replace an import')
    conn.execute('INSERT INTO secretary_adaptive_imports '
                 '(conversation_ref,import_id,declaration,imported_at,receipt) VALUES (?,?,?,?,?)',
                 (target, declaration['id'], _json(declaration), now, _json(receipt)))


def apply(db, target_ref, *, replace_import_id=None, now=None):
    """Explicit one-transaction freeze; local events/plans/HB/Idle are never written."""
    now = time.time() if now is None else now
    if number(now) is None:
        raise ValueError('invalid import time')
    declaration = declaration_for_db(db, target_ref)
    if replace_import_id is not None:
        _text(replace_import_id, 'replace import id')
        if replace_import_id == declaration['id']:
            raise ValueError('replacement requires a new import id')

    def write(conn):
        _validate_refs(conn, target_ref, declaration['from_conversation'])
        prior = _existing_receipt(conn, target_ref, declaration)
        if prior:
            if prior.get('replaces') != replace_import_id:
                raise ValueError('repeated import has a conflicting replacement declaration')
            return prior
        events, excluded, retained = _candidates(conn, db, target_ref, declaration, now)
        receipt = dict(target_conversation=target_ref, declaration=declaration, imported_at=now,
                       replaces=replace_import_id, **_summary(events, excluded, retained))
        if replace_import_id:
            _remove_import(conn, target_ref, replace_import_id, declaration['id'])
        _freeze(conn, target_ref, declaration, events, receipt, now)
        return receipt
    return db._execute_write(write)


def _sample_source(target_ref, events, source_kind, source_conversation, source_sha256):
    if source_kind == 'component_pool':
        if source_conversation is not None or any(row.get('origin_conversation') is not None for row in events):
            raise ValueError('component pool cannot claim Conversation ownership')
        return dict(source_kind='component_pool', ownership='unproven_historical_component_pool',
                    source_conversation=None, origin_key='numeric-package:' + source_sha256)
    if source_kind != 'conversation':
        raise ValueError('source_kind must be component_pool or conversation')
    _text(source_conversation, 'explicit source Conversation')
    for row in events:
        proof = row.get('proof', {})
        if (not isinstance(proof, dict) or proof.get('owner_verified') is not True
                or proof.get('owner_conversation_ref') != source_conversation):
            raise ValueError('Conversation source requires explicit matching owner proof for every sample')
        if row.get('origin_conversation', source_conversation) != source_conversation:
            raise ValueError('source Conversation conflicts with the explicit declaration')
        if row.get('source_conversation_ref', source_conversation) != source_conversation:
            raise ValueError('sample owner conflicts with the explicit source declaration')
    return dict(source_kind='conversation', ownership=('same_target_verified' if source_conversation == target_ref
                                                      else 'other_conversation_verified'),
                source_conversation=source_conversation, origin_key=source_conversation)


def import_samples(db, target_ref, events, *, import_id, source_sha256, now=None, apply=False,
                   source_kind='component_pool', source_conversation=None):
    """Explicit same-owner numeric maintenance freeze; preview is read-only.

    The source package remains untouched. This writes only existing import sidecars,
    never native usage, Conversation state, Idle clocks, or the live event buffer.
    """
    from hashlib import sha256
    from secretary.adaptive_config import enabled_for_db
    from secretary.adaptive_samples import normalize_sample
    _text(import_id, 'import id')
    _text(target_ref, 'target conversation_ref')
    if (not isinstance(source_sha256, str) or len(source_sha256) != 64
            or any(char not in '0123456789abcdef' for char in source_sha256)):
        raise ValueError('source_sha256 must be an explicit SHA256 digest')
    now = time.time() if now is None else number(now)
    if now is None or not enabled_for_db(db, target_ref):
        raise ValueError('target Conversation is not explicitly enabled in its owning Profile')
    if not isinstance(events, list) or not 0 < len(events) <= MAX_IMPORT_EVENTS:
        raise ValueError('bounded nonempty maintenance sample list required')
    if any(not isinstance(event, dict) for event in events):
        raise ValueError('invalid sample')
    source = _sample_source(target_ref, events, source_kind, source_conversation, source_sha256)
    projected, identities = [], set()
    for raw in events:
        if raw.get('origin_profile', _profile(db)) != _profile(db):
            raise ValueError('cross-Profile maintenance import denied')
        sample = normalize_sample(raw)
        if not sample['verified'] or max(sample['at'], sample['available_at']) > now:
            raise ValueError('unverified or not-yet-known maintenance sample')
        if sample['event_id'] in identities:
            raise ValueError('duplicate sample identity in package')
        identities.add(sample['event_id'])
        sample.update(source_kind=source['source_kind'], ownership=source['ownership'])
        if source_conversation is not None:
            sample['source_conversation_ref'] = source_conversation
        else:
            sample.pop('source_conversation_ref', None)
        projected.append({**sample, 'origin_profile': _profile(db), 'origin_conversation': source['origin_key'],
                          'origin_event_id': sample['event_id']})
    declaration = dict(id=import_id, kind='empirical_maintenance', from_conversation=target_ref,
                       source_sha256=source_sha256, source=source,
                       payload_sha256=sha256(_json(projected).encode()).hexdigest())

    def run(conn):
        _validate_refs(conn, target_ref, target_ref)
        if source['source_kind'] == 'conversation':
            _validate_refs(conn, target_ref, source_conversation)
        # Recheck opt-in before the transaction writes; no route/network resolution.
        if not enabled_for_db(db, target_ref):
            raise ValueError('target Conversation was disabled')
        prior = _existing_receipt(conn, target_ref, declaration)
        if prior:
            return {**prior, 'already_applied': True}
        receipt = dict(target_conversation=target_ref, declaration=declaration, imported_at=now,
                       already_applied=False, **_summary(projected, {}, 0))
        receipt.update(quality='explicit_numeric_maintenance_samples_no_live_state_transfer',
                       source_kind=source['source_kind'], ownership=source['ownership'],
                       limitations=['Import binding is to this local Profile; historical source ownership follows the explicit source declaration.',
                                    'Component-pool samples do not prove target Conversation experience or a linked joint invoice.',
                                    'Event knowability and import receipt time are both required before training.',
                                    'No coverage, current activity, native usage, or scheduling state is transferred.'])
        if apply:
            _freeze(conn, target_ref, declaration, projected, receipt, now)
        return {**receipt, 'applied': apply}
    if apply:
        return db._execute_write(run)
    with db._read_ctx() as conn:
        return run(conn)
