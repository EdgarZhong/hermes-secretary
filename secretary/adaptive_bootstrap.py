"""Explicit same-Conversation conditional persisted-stream training bootstrap.

The source is an audited numeric package, not continuous live ingress coverage.
Only original occurrence/knowledge times and bounded provenance are retained.
"""
from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from secretary import adaptive_store as store
from secretary.adaptive_features import number
from secretary.adaptive_import import _existing_receipt, _freeze, _json, _profile, _text

KIND = 'same_conversation_bootstrap'
SCHEMA = 'adaptive-persisted-bootstrap-v1'


def _stamp(value):
    result = number(value)
    if result is None:
        raise ValueError('invalid numeric bootstrap timestamp')
    return result


def _dataset(package):
    raw = package.get('dataset', {})
    if (raw.get('runtime_monitoring_coverage') is not False or raw.get('work_complete') is not False
            or raw.get('work') or raw.get('label_scope') != 'conditional_persisted_submission_sequence'):
        raise ValueError('bootstrap must be conditional timing evidence without model work or live coverage')
    cutoff = _stamp(package.get('cutoff'))
    result = dict(users=[], checkpoints=[], spans=[], excluded=[], work=[], work_complete=False, work_features_unknown=True)
    for key in ('users', 'checkpoints'):
        seen = set()
        for row in raw.get(key, []):
            identity = _text(row.get('id'), 'numeric observation id')
            at, known = _stamp(row.get('at')), _stamp(row.get('available_at'))
            if identity in seen or at > cutoff or known > cutoff or known < at:
                raise ValueError('duplicate, future or invalid bootstrap observation')
            seen.add(identity)
            result[key].append(dict(id=identity, at=at, available_at=known))
    for key in ('spans', 'excluded'):
        for pair in raw.get(key, []):
            if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                raise ValueError('invalid conditional interval')
            lo, hi = map(_stamp, pair)
            if lo >= hi or hi > cutoff:
                raise ValueError('invalid conditional interval boundary')
            result[key].append([lo, hi])
    if sum(len(result[key]) for key in ('users', 'checkpoints', 'spans', 'excluded')) > 2048:
        raise ValueError('bootstrap numeric observation capacity exceeded')
    return result


def _declaration(package, ref, identity):
    if (package.get('schema') != SCHEMA or package.get('schema_version') != 1
            or package.get('runtime_monitoring_coverage') is not False):
        raise ValueError('unsupported bootstrap schema or online coverage claim')
    source = package.get('source', {})
    if source.get('conversation_ref') != ref or package.get('target_conversation') != ref:
        raise ValueError('bootstrap requires the exact same source and target Conversation')
    sid = _text(source.get('original_session_id'), 'source session')
    session_hash = hashlib.sha256(sid.encode()).hexdigest()[:12]
    if source.get('session_hash') != session_hash:
        raise ValueError('source session hash mismatch')
    return dict(id=_text(identity, 'bootstrap id'), kind=KIND, schema=SCHEMA,
                source_session=sid, source_session_hash=session_hash,
                profile=_text(source.get('profile'), 'source Profile'), conversation_ref=ref,
                source_input_sha256=_text(package.get('source_input_sha256'), 'source input digest'),
                package_sha256=hashlib.sha256(_json(package).encode()).hexdigest(),
                source_provider=_text(source['provider'], 'source provider') if source.get('provider') else None,
                source_model=_text(source['model'], 'source model') if source.get('model') else None,
                source_model_work_transferred=False,
                cutoff=_stamp(package.get('cutoff')))


def _validate_owner(conn, db, ref, declaration):
    from hermes_cli.profiles import profile_matches_home
    if not profile_matches_home(declaration['profile'], Path(db.db_path).resolve().parent):
        raise ValueError('bootstrap source Profile differs from the owning Profile')
    row = conn.execute('SELECT conversation_ref FROM secretary_session_bindings WHERE session_id=?',
                       (declaration['source_session'],)).fetchone()
    if row is None or row[0] != ref:
        raise ValueError('source session is not bound to this Conversation in the owning database')


def _frontier(conn, package, declaration, now):
    value = package.get('current_frontier')
    if value is None:
        return None
    ref, sid = declaration['conversation_ref'], declaration['source_session']
    if (value.get('same_conversation_verified') is not True or value.get('query_only') != 1
            or value.get('original_session_id') != sid
            or value.get('original_session_hash') != declaration['source_session_hash']
            or value.get('source_conversation_ref') != ref or value.get('target_conversation_ref') != ref):
        raise ValueError('current frontier identity is not proven for the target')
    known = _stamp(value.get('queried_at'))
    user = value.get('latest_proven_user')
    if user is None:
        return None
    at = _stamp(user.get('at'))
    if (known > now or at > known or user.get('verified') is not True or user.get('source') != 'user'
            or user.get('session_id') != sid or user.get('conversation_ref') != ref):
        raise ValueError('invalid frontier occurrence/knowledge or owner')
    fields = ('client_submission_id', 'gateway_input_owner', 'is_bot', 'internal', 'synthetic_prompt',
              'hermes_plugin_injection', 'replay', 'retry', 'human_only')
    scalars = ','.join("json_extract(CASE WHEN json_valid(display_metadata) THEN display_metadata ELSE '{}' END,'$."
                       + key + "') AS " + key for key in fields)
    row = conn.execute('SELECT session_id,timestamp,message_uid,role,display_kind,active,compacted,'
                       + scalars + ' FROM messages WHERE id=?', (user.get('row_id'),)).fetchone()
    uid = user.get('message_uid_hash')
    if (row is None or row['session_id'] != sid or row['timestamp'] != at
            or hashlib.sha256(str(row['message_uid']).encode()).hexdigest()[:12] != uid):
        raise ValueError('current frontier no longer matches its native numeric message identity')
    client = row['client_submission_id']
    if (row['role'] != 'user' or row['display_kind'] == 'process_complete'
            or row['active'] != 1 or row['compacted'] != 0 or row['gateway_input_owner']
            or any(bool(row[key]) for key in fields[2:])
            or not isinstance(client, str) or not client.strip() or len(client) > 128
            or user.get('ingress') != 'web_submit'
            or user.get('event_id') != 'web:' + hashlib.sha256(client.encode()).hexdigest()[:12]):
        raise ValueError('current frontier lacks native initial-writer user provenance')
    original_known = user.get('available_at')
    if original_known is not None:
        known = max(known, _stamp(original_known))
    if known > now:
        raise ValueError('frontier evidence is not yet known')
    return dict(event_id='recovered:' + _text(uid, 'frontier UID hash'), at=at, available_at=known,
                original_available_at=original_known, kind='user_activity', source='user', verified=True,
                ingress=_text(user.get('ingress'), 'frontier ingress'),
                bootstrap_receipt=declaration['id'], message_uid_hash=uid,
                proof='native_closed_submit_schema_and_client_submission_initial_writer')


def _events(data, declaration):
    rows = []
    for key in ('users', 'checkpoints', 'spans', 'excluded'):
        for index, value in enumerate(data[key]):
            at = value['at'] if isinstance(value, dict) else value[1]
            known = value['available_at'] if isinstance(value, dict) else declaration['cutoff']
            rows.append(dict(origin_profile=declaration['origin_profile'],
                             origin_conversation=declaration['conversation_ref'],
                             origin_event_id=f"bootstrap:{declaration['package_sha256']}:{key}:{index}",
                             at=at, available_at=known, kind='bootstrap_' + key, value=value,
                             bootstrap_schema=SCHEMA, bootstrap_cutoff=declaration['cutoff'],
                             bootstrap_source_session=declaration['source_session'],
                             bootstrap_profile=declaration['profile']))
    return rows


def _prepare(conn, db, ref, package, identity, now):
    declaration = _declaration(package, ref, identity)
    _validate_owner(conn, db, ref, declaration)
    declaration['origin_profile'] = _profile(db)
    if declaration['cutoff'] > now:
        raise ValueError('bootstrap cutoff is not yet known')
    data = _dataset(package)
    frontier = _frontier(conn, package, declaration, now)
    from secretary.adaptive_forecast import training_examples
    windows = len(training_examples(data, min(now, declaration['cutoff']), 1800))
    receipt = dict(declaration=declaration, target_conversation=ref, imported_at=now,
                   grade='conditional_persisted_submission_sequence', runtime_monitoring_coverage=False,
                   counts={key: len(data[key]) for key in ('users', 'checkpoints', 'spans', 'excluded')},
                   mature_training_windows=windows, qualified=windows >= 8,
                   unknown_submissions=[dict(id=_text(row.get('event_id', row.get('id')), 'unknown id'),
                                             at=_stamp(row.get('at')), available_at=None)
                                        for row in package.get('unknown_submissions', [])],
                   recovered_last_user_at=frontier['at'] if frontier else None,
                   recovered_event_id=frontier['event_id'] if frontier else None,
                   work_compatibility='timing_only_no_transferred_model_work')
    if len(receipt['unknown_submissions']) > 2048:
        raise ValueError('unknown observation capacity exceeded')
    return declaration, data, frontier, receipt


def _prior_receipt(conn, db, ref, package, identity):
    declaration = _declaration(package, ref, identity)
    _validate_owner(conn, db, ref, declaration)
    declaration['origin_profile'] = _profile(db)
    return _existing_receipt(conn, ref, declaration)


def preview(db, ref, package, *, bootstrap_id, now=None):
    """Validate and preview numeric readiness without changing any runtime state."""
    from secretary.adaptive_config import enabled_for_db
    if not enabled_for_db(db, ref):
        raise ValueError('target adaptive Conversation is not explicitly enabled')
    now = _stamp(time.time() if now is None else now)
    with db._read_ctx() as conn:
        prior = _prior_receipt(conn, db, ref, package, bootstrap_id)
        receipt = prior or _prepare(conn, db, ref, package, bootstrap_id, now)[3]
    return {**(prior or receipt), 'already_applied': prior is not None,
            'adoption': 'next_natural_turn_boundary_only'}


def apply(db, ref, package, *, bootstrap_id, now=None):
    """Freeze numbers and one proven current activity; never finish/reanchor a Turn."""
    from secretary.adaptive_config import enabled_for_db
    if not enabled_for_db(db, ref):
        raise ValueError('target adaptive Conversation is not explicitly enabled')
    now = _stamp(time.time() if now is None else now)

    def write(conn):
        prior = _prior_receipt(conn, db, ref, package, bootstrap_id)
        if prior:
            return prior
        declaration, data, frontier, receipt = _prepare(conn, db, ref, package, bootstrap_id, now)
        _freeze(conn, ref, declaration, _events(data, declaration), receipt, now)
        if frontier:
            _recover_frontier(conn, ref, frontier)
        return receipt
    return db._execute_write(write)


def _recover_frontier(conn, ref, event):
    prior = conn.execute('SELECT payload FROM secretary_adaptive_events WHERE conversation_ref=? AND event_id=?',
                         (ref, event['event_id'])).fetchone()
    if prior:
        value = json.loads(prior[0])
        keys = ('at', 'message_uid_hash', 'kind', 'source', 'verified', 'proof')
        if any(value.get(key) != event.get(key) for key in keys):
            raise ValueError('recovered activity conflicts with existing evidence')
        return  # The first receipt already proves when this same fact became known.
    store.event_conn(conn, ref, event)


def _records(conn, ref, now):
    return conn.execute(
        'SELECT e.*,i.import_id,i.imported_at FROM secretary_adaptive_import_events e '
        'JOIN secretary_adaptive_import_members m USING '
        '(conversation_ref,origin_profile,origin_conversation,origin_event_id) '
        'JOIN secretary_adaptive_imports i USING (conversation_ref,import_id) '
        'WHERE e.conversation_ref=? AND e.at<=? AND e.available_at<=? AND i.imported_at<=? '
        "AND i.replaced_by IS NULL AND json_extract(e.payload,'$.bootstrap_schema')=? "
        "ORDER BY json_extract(e.payload,'$.bootstrap_cutoff') DESC,i.imported_at DESC,i.import_id DESC,e.at",
        (ref, now, now, now, SCHEMA)).fetchall()


def _selected_records(conn, db, ref, now):
    records = _records(conn, ref, now)
    if not records:
        return []
    first = records[0]
    tag = json.loads(first['payload'])
    # Membership/receipt freezes the source proof. Deleting its live Session
    # must not revoke an already imported training snapshot.
    if first['origin_profile'] != _profile(db):
        raise ValueError('bootstrap cannot cross owning Profiles')
    return [r for r in records if (r['import_id'], r['origin_profile'], r['origin_conversation'])
            == (first['import_id'], first['origin_profile'], first['origin_conversation'])
            and json.loads(r['payload'])['bootstrap_cutoff'] == tag['bootstrap_cutoff']]


def read(db, ref, now):
    """Same-owner explicit priors only; duplicates never multiply training evidence."""
    with db._read_ctx() as conn:
        records = _selected_records(conn, db, ref, now)
    if not records:
        return []
    data = dict(users=[], checkpoints=[], spans=[], excluded=[], work=[], work_complete=False, work_features_unknown=True)
    for record in records:
        event = json.loads(record['payload'])
        data[event['kind'].removeprefix('bootstrap_')].append(event['value'])
    return [dict(dataset=data, cutoff=json.loads(records[0]['payload'])['bootstrap_cutoff'],
                 imported_at=records[0]['imported_at'], receipt=records[0]['import_id'],
                 conversation_ref=ref, grade='conditional_persisted_submission_sequence',
                 runtime_monitoring_coverage=False)]


def export_conn(conn, db, ref, now):
    """Standard explicit imports carry training rows, never the recovered live frontier."""
    rows = []
    for record in _selected_records(conn, db, ref, now):
        event = json.loads(record['payload'])
        event['available_at'] = max(event['available_at'], record['imported_at'])
        rows.append({**event, **{key: record[key] for key in
                                ('origin_profile', 'origin_conversation', 'origin_event_id')}})
    return rows


def project_transfer(event):
    """Numeric allowlist for the existing explicit Conversation import projector."""
    if event.get('bootstrap_schema') != SCHEMA or event.get('kind') not in {
            'bootstrap_users', 'bootstrap_checkpoints', 'bootstrap_spans', 'bootstrap_excluded'}:
        return None
    cutoff = _stamp(event.get('bootstrap_cutoff'))
    key = event['kind'].removeprefix('bootstrap_')
    raw = dict(runtime_monitoring_coverage=False, work_complete=False, work=[],
               label_scope='conditional_persisted_submission_sequence', **{key: [event.get('value')]})
    value = _dataset(dict(dataset=raw, cutoff=cutoff))[key][0]
    return dict(event_id=_text(event.get('origin_event_id'), 'training origin id'),
                kind=event['kind'], source='unknown', verified=False, at=_stamp(event.get('at')),
                available_at=_stamp(event.get('available_at')), value=value,
                bootstrap_schema=SCHEMA, bootstrap_cutoff=cutoff,
                bootstrap_source_session=_text(event.get('bootstrap_source_session'), 'source session'),
                bootstrap_profile=_text(event.get('bootstrap_profile'), 'source Profile'))
