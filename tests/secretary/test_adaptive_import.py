"""Frozen history uses real owner transactions and never transfers live state."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path

import pytest
import hermes_yaml as yaml

from hermes_state import SessionDB
from secretary import adaptive_import as imports, adaptive_store as store


@pytest.fixture
def owned(tmp_path):
    home = tmp_path / 'owner'
    home.mkdir()
    db = SessionDB(home / 'state.db')
    refs = {}
    for name in ('source', 'target', 'third'):
        db.create_session(name, source='test')
        refs[name] = db.resolve_conversation_ref(name)
    yield db, refs
    db.close()


def configure(db, target, source, identity='first', through=900):
    value = dict(id=identity, from_conversation=source,
                 through=datetime.fromtimestamp(through, timezone.utc).isoformat())
    block = dict(enabled=True, conversations={target: dict(enabled=True, history_import=value)})
    path = Path(db.db_path).parent / 'config.yaml'
    path.write_text(yaml.safe_dump(dict(noting=dict(enabled=True, adaptive_idle_token_saving=block))))
    return value


def record(db, ref, identity, at, kind='user_activity', **values):
    event = dict(event_id=identity, at=at, kind=kind, source='user', verified=True, **values)
    db._execute_write(lambda conn: store.event_conn(conn, ref, event))
    return event


def imported(db, target, now=2000):
    return [event for cohort in store.imported_history(db, target, now) for event in cohort['events']]


def tables(db, names):
    with db._read_ctx() as conn:
        return {name: [tuple(row) for row in conn.execute(f'SELECT * FROM {name}')]
                for name in names}


def test_preview_freeze_idempotence_and_source_changes(owned):
    db, refs = owned
    source, target = refs['source'], refs['target']
    record(db, source, 'original', 100, body='must not transfer', credentials={'secret': 'never'})
    record(db, source, 'later', 950)
    configure(db, target, source)
    before = tables(db, ['secretary_adaptive_imports', 'secretary_adaptive_import_events'])
    preview = imports.preview(db, target, now=1000)
    assert preview['event_count'] == 1
    assert preview['available_range'] == [100, 100]
    assert preview['excluded']['after_cutoff_or_not_yet_known'] == 1
    assert tables(db, list(before)) == before
    receipt = imports.apply(db, target, now=1000)
    assert imported(db, target, now=999) == []
    event = imported(db, target)[0]
    assert event['at'] == 100 and event['available_at'] == 100 and event['imported_at'] == 1000
    assert 'body' not in event and 'credentials' not in event
    assert store.history(db, target, 2000) == []
    record(db, source, 'new', 200)
    db._execute_write(lambda conn: conn.execute('DELETE FROM secretary_adaptive_events WHERE conversation_ref=?', (source,)))
    assert imports.apply(db, target, now=1500) == receipt
    assert imports.preview(db, target, now=1500)['already_applied'] is True
    assert imported(db, target)[0] == event
    db.close()
    reopened = SessionDB(db.db_path)
    try:
        assert imported(reopened, target)[0] == event
    finally:
        reopened.close()


def test_conflicting_id_and_explicit_replacement_preserve_local_state(owned):
    db, refs = owned
    source, target = refs['source'], refs['target']
    record(db, source, 'original', 100)
    local = record(db, target, 'target-local', 120)
    db._execute_write(lambda conn: conn.execute(
        'INSERT INTO secretary_adaptive_plans VALUES (?,?,?,?,?,?)', (target, 1, 'pending', 130, 'cfg', '{}')))
    db._execute_write(lambda conn: conn.execute(
        'INSERT INTO secretary_adaptive_heartbeats VALUES (?,?,?,?,?,?,?)',
        (target, 'hot', 60, 'cfg', 2, None, 140)))
    live_names = ['secretary_adaptive_events', 'secretary_adaptive_plans', 'secretary_adaptive_heartbeats']
    configure(db, target, source)
    imports.apply(db, target, now=1000)
    original_state = tables(db, live_names)
    configure(db, target, source, through=500)
    with pytest.raises(ValueError, match='conflicting declaration'):
        imports.apply(db, target, now=1100)
    configure(db, target, source, identity='replacement', through=500)
    receipt = imports.apply(db, target, replace_import_id='first', now=1200)
    assert receipt['replaces'] == 'first'
    assert tables(db, live_names) == original_state
    assert store.history(db, target, 2000) == [local]
    assert len(imported(db, target)) == 1
    assert imports.apply(db, target, replace_import_id='first', now=1300) == receipt
    with pytest.raises(ValueError, match='conflicting replacement'):
        imports.apply(db, target, now=1300)
    configure(db, target, source)
    assert imports.apply(db, target, now=1350)['replaced_by'] == 'replacement'
    assert len(imported(db, target)) == 1
    configure(db, target, source, through=500)
    with pytest.raises(ValueError, match='conflicting declaration'):
        imports.apply(db, target, now=1350)
    configure(db, target, source, identity='bad-replace')
    with pytest.raises(ValueError, match='does not exist'):
        imports.apply(db, target, replace_import_id='foreign-id', now=1400)
    assert tables(db, live_names) == original_state


def test_original_identity_deduplicates_chains_and_rejects_target_cycles(owned):
    db, refs = owned
    source, target, third = (refs[name] for name in ('source', 'target', 'third'))
    record(db, source, 'same-id', 100)
    configure(db, target, source)
    imports.apply(db, target, now=1000)
    record(db, target, 'same-id', 200)
    configure(db, third, target, through=1100)
    imports.apply(db, third, now=1200)
    assert len(imported(db, third)) == 2  # The two Conversations' IDs are distinct origins.
    configure(db, third, source, identity='direct', through=1100)
    imports.apply(db, third, now=1300)
    assert len(imported(db, third)) == 2
    first = next(event for event in imported(db, third) if event['origin_conversation'] == source)
    assert first['origin_event_id'] == 'same-id' and first['at'] == 100
    assert first['imported_at'] == 1200  # Additional receipt does not make it appear newer.
    configure(db, source, third, identity='return', through=1400)
    result = imports.apply(db, source, now=1500)
    assert result['excluded']['target_origin_cycle'] == 1
    assert [event['origin_conversation'] for event in imported(db, source)] == [target]
    cohorts = store.imported_history(db, third, 2000)
    assert len(cohorts) == 2 and all(cohort['retained_start_at'] in (100, 200) for cohort in cohorts)


def test_unknown_identity_coverage_gaps_and_model_labels_survive(owned):
    db, refs = owned
    source, target = refs['source'], refs['target']
    db._execute_write(lambda conn: store.event_conn(conn, source,
        dict(event_id='unknown', at=100, available_at=150, kind='request', verified=True,
             model_key='long-model', provider='provider', model_option='model-900k',
             context_contract=[900000, 800000], reasoning={'effort': 'high'}, input_tokens=99,
             output_tokens=None, body='do not copy',
             model_identity=dict(provider='provider', model='model-900k'),
             model_contract=dict(provider='provider', model='model-900k', context_length=900000,
                 threshold_tokens=800000, api_mode='responses', reasoning_config={'effort': 'high'},
                 fast_mode=True, service_tier='priority', capabilities={'vision': True},
                 body='do not copy'))))
    record(db, source, 'coverage', 200, kind='coverage', start_at=50, end_at=200, scope='web_submit')
    record(db, source, 'gap', 220, kind='coverage_gap', start_at=200, end_at=220, reason='disconnected')
    record(db, source, 'maintenance', 300, kind='maintenance_start', operation_id='operation')
    configure(db, target, source)
    report = imports.preview(db, target, now=1000)
    assert report['unknown_source_events'] == 1
    assert report['model_distribution'] == {'provider / model-900k': 1}
    cohort = report['cohorts'][0]
    assert cohort['retained_start_at'] == 100
    assert cohort['coverage_intervals'][0]['start_at'] == 50
    assert len(cohort['exclusions']) == 2
    imports.apply(db, target, now=1000)
    event = next(event for event in imported(db, target) if event['event_id'] == 'unknown')
    assert event['source'] == 'unknown' and event['available_at'] == 150
    assert event['model_option'] == 'model-900k' and event['context_contract'] == [900000, 800000]
    assert event['output_tokens'] is None and 'body' not in event
    assert event['model_identity'] == dict(provider='provider', model='model-900k')
    assert event['model_contract']['context_length'] == 900000
    assert event['model_contract']['capabilities'] == {'vision': True}
    assert event['model_contract']['reasoning_config'] == {'effort': 'high'}
    assert 'body' not in event['model_contract']


def test_source_without_coverage_does_not_invent_it_and_known_time_is_fenced(owned):
    db, refs = owned
    source, target = refs['source'], refs['target']
    record(db, source, 'known-later', 100, available_at=950)
    record(db, source, 'known', 200, available_at=300)
    configure(db, target, source, through=900)
    report = imports.preview(db, target, now=1000)
    assert report['event_count'] == 1
    assert report['cohorts'][0]['coverage_intervals'] == []
    imports.apply(db, target, now=1000)
    assert [event['event_id'] for event in imported(db, target)] == ['known']
    assert store.imported_history(db, target, 999) == []
    configure(db, refs['third'], target, through=2000)
    assert imports.preview(db, refs['third'], now=999)['event_count'] == 0


def test_config_owner_exact_refs_and_opt_in_fail_closed(owned, tmp_path, monkeypatch):
    db, refs = owned
    source, target = refs['source'], refs['target']
    alien = tmp_path / 'alien'
    alien.mkdir()
    monkeypatch.setenv('HERMES_HOME', str(alien))
    configure(db, target, source)
    assert imports.preview(db, target, now=1000)['event_count'] == 0
    for bad_source in (target, 'source', 'missing'):
        configure(db, target, bad_source)
        with pytest.raises(ValueError):
            imports.apply(db, target, now=1000)
    configure(db, target, source)
    with pytest.raises(ValueError, match='not explicitly enabled'):
        imports.apply(db, refs['third'], now=1000)
    value = json.loads(json.dumps(yaml.safe_load((Path(db.db_path).parent / 'config.yaml').read_text())))
    value['noting']['adaptive_idle_token_saving']['conversations'][target]['history_import']['from_profile'] = 'alien'
    (Path(db.db_path).parent / 'config.yaml').write_text(yaml.safe_dump(value))
    with pytest.raises(ValueError, match='requires only'):
        imports.preview(db, target, now=1000)


@pytest.mark.parametrize('through', ['2026-01-01T00:00:00', 'invalid', 900, None])
def test_cutoff_requires_explicit_timezone(owned, through):
    db, refs = owned
    configure(db, refs['target'], refs['source'])
    path = Path(db.db_path).parent / 'config.yaml'
    value = yaml.safe_load(path.read_text())
    value['noting']['adaptive_idle_token_saving']['conversations'][refs['target']]['history_import']['through'] = through
    path.write_text(yaml.safe_dump(value))
    with pytest.raises(ValueError, match='ISO timestamp with timezone'):
        imports.preview(db, refs['target'], now=1000)


def test_capacity_replacement_failure_rolls_back_whole_transaction(owned, monkeypatch):
    db, refs = owned
    source, target = refs['source'], refs['target']
    record(db, source, 'original', 100)
    configure(db, target, source)
    imports.apply(db, target, now=1000)
    names = ['secretary_adaptive_imports', 'secretary_adaptive_import_events', 'secretary_adaptive_import_members']
    before = tables(db, names)
    record(db, source, 'second', 200)
    configure(db, target, source, identity='replacement')
    monkeypatch.setattr(imports, 'MAX_IMPORT_EVENTS', 1)
    # Force an event insertion failure after deletion, rather than candidate truncation.
    original = imports._freeze
    def fail_after_freeze(conn, *args):
        original(conn, *args)
        raise ValueError('injected transaction failure')
    monkeypatch.setattr(imports, '_freeze', fail_after_freeze)
    with pytest.raises(ValueError):
        imports.apply(db, target, replace_import_id='first', now=1200)
    assert tables(db, names) == before


def test_receipt_and_unique_event_bounds_are_separate_from_local(owned, monkeypatch):
    db, refs = owned
    source, target = refs['source'], refs['target']
    record(db, source, 'first', 100)
    configure(db, target, source)
    imports.apply(db, target, now=1000)
    monkeypatch.setattr(imports, 'MAX_IMPORT_RECEIPTS', 1)
    configure(db, target, source, identity='second')
    with pytest.raises(ValueError, match='receipt capacity'):
        imports.apply(db, target, now=1100)
    monkeypatch.setattr(imports, 'MAX_IMPORT_RECEIPTS', 32)
    monkeypatch.setattr(imports, 'MAX_IMPORT_EVENTS', 1)
    record(db, refs['third'], 'other', 200)
    configure(db, target, refs['third'], identity='other')
    with pytest.raises(ValueError, match='event capacity'):
        imports.apply(db, target, now=1100)
    assert len(imported(db, target)) == 1
    assert len(store.history(db, source, 2000)) == 1


def test_existing_origin_conflict_is_not_silently_rewritten(owned):
    db, refs = owned
    source, target = refs['source'], refs['target']
    record(db, source, 'coverage', 100, kind='coverage', start_at=50, end_at=100)
    configure(db, target, source)
    imports.apply(db, target, now=1000)
    event = dict(event_id='coverage', at=200, kind='coverage', source='user', verified=True, start_at=50, end_at=200)
    db._execute_write(lambda conn: conn.execute('UPDATE secretary_adaptive_events SET at=?,payload=? '
        'WHERE conversation_ref=? AND event_id=?', (200, json.dumps(event), source, 'coverage')))
    configure(db, target, source, identity='second')
    with pytest.raises(ValueError, match='conflicts with an existing frozen'):
        imports.apply(db, target, now=1100)
    assert imported(db, target)[0]['end_at'] == 100
    imports.apply(db, target, replace_import_id='first', now=1200)
    assert imported(db, target)[0]['end_at'] == 200


def test_cli_uses_native_profile_and_only_explicit_apply(owned, monkeypatch, capsys):
    db, refs = owned
    configure(db, refs['target'], refs['source'])
    record(db, refs['source'], 'first', 100)
    spec = importlib.util.spec_from_file_location('adaptive_history_import_cli',
            Path(__file__).resolve().parents[2] / 'scripts/adaptive_history_import.py')
    cli = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cli)
    monkeypatch.setattr('hermes_cli.profiles.profile_exists', lambda name: name == 'owner')
    monkeypatch.setattr('hermes_cli.profiles.get_profile_dir', lambda name: Path(db.db_path).parent)
    cli.main(['preview', '--profile', 'owner', '--target', refs['target']])
    assert json.loads(capsys.readouterr().out)['event_count'] == 1
    assert imported(db, refs['target']) == []
    cli.main(['apply', '--profile', 'owner', '--target', refs['target']])
    receipt = json.loads(capsys.readouterr().out)
    assert len(imported(db, refs['target'], now=receipt['imported_at'])) == 1


def test_source_live_plan_claim_and_idle_are_never_transferred(owned):
    from hermes_state_secretary_noting import init_secretary_noting_schema
    db, refs = owned
    source, target = refs['source'], refs['target']
    db._execute_write(lambda conn: init_secretary_noting_schema(conn.cursor()))
    db.noting_idle_turn_finished(source, 100, due_at=500)
    db._execute_write(lambda conn: conn.execute(
        'INSERT INTO secretary_adaptive_plans VALUES (?,?,?,?,?,?)',
        (source, 9, 'pending', 100, 'cfg', '{"mode":"hot","delay_seconds":400}')))
    db._execute_write(lambda conn: conn.execute(
        'INSERT INTO secretary_adaptive_heartbeats VALUES (?,?,?,?,?,?,?)',
        (source, 'hot', 60, 'cfg', 9, '{"mode":"business"}', 100)))
    record(db, source, 'historical-end', 100, kind='turn_end', context_tokens=900000)
    configure(db, target, source)
    names = ['secretary_adaptive_plans', 'secretary_adaptive_heartbeats', 'secretary_noting_idle_state']
    before = tables(db, names)
    imports.apply(db, target, now=1000)
    assert tables(db, names) == before
    assert db.noting_idle_state(target) is None
    assert store.history(db, target, 2000) == []


def test_actual_retention_and_import_selection_disclose_missing_old_history(owned):
    db, refs = owned
    source, target, third = (refs[name] for name in ('source', 'target', 'third'))
    record(db, third, 'old-prior', 0)
    configure(db, source, third, identity='prior', through=3000)
    imports.apply(db, source, now=3500)
    def write(conn):
        for index in range(1, 2051):
            store.event_conn(conn, source, dict(event_id=f'event-{index}', at=index,
                kind='user_activity', source='user', verified=True))
    db._execute_write(write)
    configure(db, target, source, through=4000)
    report = imports.preview(db, target, now=4500)
    assert report['source_local_retained'] == 2050
    assert report['source_local_limit'] == 65536
    assert report['event_count'] <= 2048 and report['available_range'] == [0, 2050]
    assert report['excluded']['snapshot_event_bound'] == 3
    assert report['cohorts'][0]['coverage_missing'] is True
    imports.apply(db, target, now=4500)
    assert len(imported(db, target, now=5000)) == report['event_count']
    assert any(e['kind'] == 'coverage_gap' for e in imported(db, target, now=5000))
    assert len(store.history(db, source, 5000)) == 2050
    assert len(imported(db, source, now=5000)) == 1
