"""Real Noting task lifecycle emits invalidation and exposes only its true owner."""
import copy
from pathlib import Path

from secretary.noting_child import run_noting_task
from secretary.web_events import subscribe, unsubscribe
from secretary.web_read import secretary_state
from tests.secretary.test_noting_child import _tool_response, mock_response

pytest_plugins = ('tests.secretary.test_noting_child',)


def test_real_task_start_finish_snapshot_memo_events(parent, db, stub_client):
    ref = parent._secretary_conversation_ref
    (Path(db.db_path).parent / 'config.yaml').write_text('noting:\n  enabled: true\n')
    db.noting_memo_mutate(ref, {'operation': 'add', 'content': 'cover in Notebook'})
    observed, hints = [], []
    prefix = copy.deepcopy(parent._session_messages)
    def provider(**kwargs):
        with db._read_ctx() as conn:
            before = tuple(conn.iterdump())
        status = secretary_state(db, parent.session_id)
        with db._read_ctx() as conn:
            assert tuple(conn.iterdump()) == before
        assert parent._session_messages == prefix
        observed.append(status)
        return _tool_response('finish_noting', {'reason': 'review complete'}, 'finish') if len(observed) == 1 else mock_response('done')
    stub_client.chat.completions.create.side_effect = provider
    subscribe('test-web-child', lambda home, owner, reason: hints.append((home, owner, reason)))
    try:
        admission = db.noting_admit(ref, 'm2', kind='idle')
        outcome = run_noting_task(parent, admission_id=admission, conversation_ref=ref, anchor_message_uid='m2',
                                trigger_type='idle', runtime_profile='NOTING', task_instruction='review')
        assert outcome.committed, outcome
        assert observed and all(state['task_state'] == 'active' for state in observed)
        assert all(state['tasks'] == [{'task_id': outcome.child_session_id}] for state in observed)
        assert all(state['memo_count'] == 1 for state in observed)
        final = secretary_state(db, parent.session_id)
        assert final['task_state'] == 'idle' and final['memo_count'] == 0
        reasons = [reason for home, owner, reason in hints]
        assert reasons[0] == 'task_started' and reasons[-1] == 'task_finished'
        assert 'notebook_changed' in reasons
        assert all(home == Path(db.db_path).parent.resolve() and owner == ref for home, owner, reason in hints)
    finally:
        unsubscribe('test-web-child')
        parent.close()
