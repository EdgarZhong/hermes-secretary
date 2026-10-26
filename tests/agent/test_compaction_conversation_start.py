"""Compaction footer starts at persisted History Foreground, never the RAM window."""
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from agent.context_compressor import ContextCompressor, _format_instant
from hermes_state import SessionDB


START = 1_790_000_000.0


def compressor(db, session_id):
    with patch('agent.context_compressor.get_model_context_length', return_value=100_000):
        result = ContextCompressor(model='test/model', quiet_mode=True, tail_mode='lean')
    result.bind_session_state(db, session_id)
    result._secretary_history_recovery = True
    return result


def summarize_window(c, memory):
    def generate(turns, **kwargs):
        return c._augment_summary_lean('## Goal\nContinue the conversation.', turns)
    with patch.object(c, '_generate_summary', side_effect=generate):
        return c._summarize_window(memory, memory, SimpleNamespace(), None, '', False)


@pytest.mark.parametrize('rotation', [False, True], ids=['in-place', 'session-rotation'])
def test_foreground_start_survives_repeated_compaction_and_cold_restore(tmp_path, rotation):
    path = tmp_path / 'state.db'
    (tmp_path / 'config.yaml').write_text('timezone: Asia/Shanghai\n')
    db = SessionDB(path)
    sid = 'original'
    db.create_session(sid, source='cli')
    db.append_message(sid, 'user', 'The first Conversation message.', timestamp=START, message_uid='first')
    ref = db.resolve_conversation_ref(sid)
    try:
        for step in range(3):
            stamp = START + (step + 1) * 86400
            db.append_message(sid, 'user', f'Later question {step}', timestamp=stamp, message_uid=f'user-{step}')
            db.append_message(sid, 'assistant', f'Later answer {step}', timestamp=stamp+1, message_uid=f'answer-{step}')
            memory = db.get_messages(sid)[-2:]
            assert all(row['message_uid'] != 'first' for row in memory)
            c = compressor(db, sid)
            summary = summarize_window(c, memory)
            expected = _format_instant(START, str(tmp_path))
            assert f'since this Conversation began ({expected})' in summary
            assert f'({_format_instant(stamp, str(tmp_path))}–{_format_instant(stamp+1, str(tmp_path))}) compacted' in summary
            handoff = [{'role': 'user', 'content': summary, '_compressed_summary': True, 'timestamp': stamp+2}]
            if rotation:
                child = f'rotated-{step}'
                db.publish_compression_child(parent_session_id=sid, child_session_id=child, source='cli', messages=handoff, require_compression_lease=False)
                sid = child
            else:
                db.archive_and_compact(sid, handoff)
            db.close()
            db = SessionDB(path)
            assert db.resolve_conversation_ref(sid) == ref
            first = db.get_history_foreground(sid)[0]
            assert (first['message_uid'], first['timestamp']) == ('first', START)
    finally:
        db.close()


def test_footer_uses_first_foreground_row_not_min_timestamp_or_stale_memory(tmp_path):
    db = SessionDB(tmp_path / 'state.db')
    try:
        db.create_session('owner', source='cli')
        db.append_message('owner', 'user', 'First in the path', timestamp=START, message_uid='first')
        db.append_message('owner', 'assistant', 'Imported older clock', timestamp=START-100, message_uid='later')
        db.create_session('foreign', source='cli')
        db.append_message('foreign', 'user', 'Other Conversation', timestamp=START-1000)
        c = compressor(db, 'owner')
        c._conversation_started_at = START-9999  # obsolete RAM state must have no authority
        memory = [{'role': 'user', 'content': 'Only current tail', 'timestamp': START+86400}]
        summary = summarize_window(c, memory)
        assert f'since this Conversation began ({_format_instant(START, str(tmp_path))})' in summary
        # The deterministic summary path also reads Foreground; it never ran the RAM summary hook.
        restored = compressor(db, 'owner')
        fallback = restored._augment_summary_lean('Deterministic handoff', memory)
        assert f'since this Conversation began ({_format_instant(START, str(tmp_path))})' in fallback
    finally:
        db.close()
