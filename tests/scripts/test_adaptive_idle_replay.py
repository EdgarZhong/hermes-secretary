"""Numeric replay keeps observed facts and unavailable historical state separate."""
from copy import deepcopy
from datetime import datetime, timezone
import importlib.util
from pathlib import Path

import pytest

_SPEC = importlib.util.spec_from_file_location(
    'adaptive_idle_replay', Path(__file__).resolve().parents[2] / 'scripts/adaptive_idle_replay.py')
replay = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(replay)


def test_historical_audit_does_not_backdate_updated_coverage():
    now = datetime(2026, 11, 3, 23, tzinfo=timezone.utc).timestamp()
    at = now - 3600
    history = [
        dict(event_id='decision', kind='decision', at=at, stage='proposed', decision={'mode': 'hot'}),
        dict(event_id='coverage', kind='coverage', at=now, start_at=at - 7200, end_at=now),
        dict(event_id='late-proof', kind='user_activity', at=at - 120, available_at=now),
        dict(event_id='turn', kind='turn_end', at=at, context_tokens=419138, source='heartbeat'),
    ]
    original = deepcopy(history)
    rows = replay.historical_audit({'now': now}, history, {'timezone': 'UTC'})
    assert rows[0]['visible_coverage_ids'] == []
    assert rows[0]['visible_event_count'] == 2
    assert rows[0]['replay_status'] == 'not_replayed_incomplete_decision_snapshot'
    assert rows[0]['recorded_stage'] == 'proposed'
    assert rows[0]['recovered_turn_fields'][0]['context_tokens'] == 419138
    assert history == original


def test_usage_total_prompt_includes_cache_and_keeps_sources_separate():
    history = [dict(kind='request', at=100, source=source, input_tokens=1000,
                    cache_read_tokens=800, output_tokens=10)
               for source in ('heartbeat', 'reminder', 'unknown')]
    result = replay.observed_usage({'now': 101}, history,
                                  {'cache_ratio': .05, 'output_ratio': 5})
    for source in ('heartbeat', 'reminder', 'unknown'):
        assert result['by_explicit_source'][source]['input_equivalent'] == 290
        assert result['by_explicit_source'][source]['requests'] == 1


@pytest.mark.parametrize('usage', [
    {'input_tokens': 100, 'cache_read_tokens': 101, 'output_tokens': 0},
    {'input_tokens': 100, 'cache_read_tokens': None, 'output_tokens': 0},
    {'input_tokens': 100, 'cache_read_tokens': 0, 'output_tokens': 0, 'cache_write_tokens': 1},
])
def test_missing_or_unpriced_usage_never_becomes_zero_cost_observation(usage):
    row = dict(kind='request', at=100, source='heartbeat', **usage)
    result = replay.observed_usage({'now': 101}, [row], {'cache_ratio': .05, 'output_ratio': 5})
    assert result['by_explicit_source']['heartbeat']['missing_usage'] == 1
    assert result['by_explicit_source']['heartbeat']['requests'] == 1


def test_day_boundary_uses_declared_local_timezone():
    now = datetime(2026, 11, 3, 1, tzinfo=timezone.utc).timestamp()
    before_local_midnight = datetime(2026, 11, 2, 15, 59, tzinfo=timezone.utc).timestamp()
    rows = [dict(kind='request', at=at, source='heartbeat', input_tokens=100,
                 cache_read_tokens=0, output_tokens=0) for at in (before_local_midnight, now - 60)]
    result = replay.observed_usage({'now': now}, rows,
        {'timezone': 'Asia/Shanghai', 'cache_ratio': .05, 'output_ratio': 5})
    assert result['by_explicit_source']['heartbeat']['requests'] == 1


def test_usage_excludes_not_yet_visible_and_future_requests():
    rows = [dict(kind='request', at=at, available_at=available, source='heartbeat',
                 input_tokens=100, cache_read_tokens=0, output_tokens=0)
            for at, available in ((90, 100), (90, 110), (110, 110))]
    result = replay.observed_usage({'now': 100}, rows, {'cache_ratio': .05, 'output_ratio': 5})
    assert result['by_explicit_source']['heartbeat']['requests'] == 1
