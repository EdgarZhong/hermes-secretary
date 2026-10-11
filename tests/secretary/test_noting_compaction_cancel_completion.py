"""C09: real native receipt/cancel followed by normal Child CommitGate/Finish."""
import json

from tests.secretary.test_noting_child import _tool_response, mock_response

pytest_plugins = ['tests.secretary.test_noting_child']


def test_receipt_success_then_native_cancel_still_commits_snapshot_and_finish(parent, db, stub_client, monkeypatch):
    from agent.context_compaction_request import NativeCompactionRequest, trust_default_system_message
    from secretary.noting_child import spawn_noting_task, active_noting_task_count
    from secretary.noting_runtime import try_admit_idle
    from secretary.noting_policy import ContextMeasurement, NotingSettings
    from secretary.noting_scope import bind_main_runtime
    from secretary.framework_messages import flush_framework_messages

    parent._compression_feasibility_checked = True
    parent.context_compressor.context_length = 196000
    parent.context_compressor.threshold_tokens = 147000
    parent.context_compressor.last_real_prompt_tokens = 110000
    trust_default_system_message(parent)
    assert bind_main_runtime(parent)
    receipts = []
    original = NativeCompactionRequest.admit
    def receipt_then_cancel(request, fence):
        admitted = original(request, fence)
        assert admitted
        receipts.append(request)
        request.cancel()
        return admitted
    monkeypatch.setattr(NativeCompactionRequest, 'admit', receipt_then_cancel)
    def forbidden_summary(*args, **kwargs):
        raise AssertionError('The real cancelled native fence must prevent summary dispatch')
    monkeypatch.setattr(parent.context_compressor, 'compress', forbidden_summary)
    stub_client.chat.completions.create.side_effect = [
        _tool_response('notebook_show', {}, 'read'),
        _tool_response('compact_parent', {}, 'compact'),
        mock_response('Finished.'),
    ]
    ref = parent._secretary_conversation_ref
    db.noting_idle_turn_finished(ref, 1000.0)
    settings = NotingSettings(True, 500, True, 100000, False)
    decision = try_admit_idle(db, ref, now=2000.0, settings=settings,
                              measurement=ContextMeasurement(110000, 196000, 147000))
    assert decision.action == 'admit' and decision.admission.task_profile == 'NOTING_WITH_COMPACTION'
    worker = spawn_noting_task(parent, decision.admission)
    worker.join(15)
    assert not worker.is_alive()
    if hasattr(parent, '_native_compaction_worker'):
        parent._native_compaction_worker.join(15)
        assert not parent._native_compaction_worker.is_alive()
    assert len(receipts) == 1
    request = receipts[0]
    assert request.was_admitted and request.fence.is_cancelled and not request.committed
    assert db.get_native_request_publication(parent.session_id) is None
    record = db.noting_child(decision.admission.admission_id)
    assert record['status'] == 'completed'
    rows = db.get_messages(record['child_session_id'])
    result = next(row for row in rows if row['role'] == 'tool' and row.get('tool_name') == 'compact_parent')
    payload = json.loads(result['content'])
    assert payload['success'] and payload['status'] == 'admitted'
    current = db.notebook_current(ref)
    assert current['anchor_message_uid'] == 'm2'
    audit = db.notebook_snapshot_audit(current['snapshot_id'])
    assert audit['termination'] == {'type': 'compact_parent'}
    flush_framework_messages(parent)
    live = [row for row in parent._session_messages if (row.get('display_metadata') or {}).get('noting_run_output')]
    durable = [row for row in db.get_messages(parent.session_id)
               if (row.get('display_metadata') or {}).get('noting_run_output')]
    assert len(live) == len(durable) == 1
    assert live[0]['message_uid'] == durable[0]['message_uid']
    assert live[0]['content'] == durable[0]['content']
    assert 'Processed memo entries have been cleared.' in live[0]['content']
    assert active_noting_task_count() == 0
