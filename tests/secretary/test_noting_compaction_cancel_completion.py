"""A cancelled native parent request cannot invalidate an independent Noting commit."""

from tests.secretary.test_noting_child import _tool_response, mock_response

pytest_plugins = ['tests.secretary.test_noting_child']


def test_receipt_success_then_native_cancel_still_commits_snapshot_and_finish(parent, db, stub_client, monkeypatch):
    from agent.context_compaction_request import NativeCompactionRequest, trust_default_system_message
    from secretary.noting_child import run_noting_task, active_noting_task_count
    from secretary.noting_scope import bind_main_runtime
    from secretary.framework_messages import flush_framework_messages

    parent._compression_feasibility_checked = True
    parent.context_compressor.context_length = 196000
    parent.context_compressor.threshold_tokens = 147000
    parent.context_compressor.last_prompt_tokens = 110000
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
        raise AssertionError('The cancelled native fence must prevent summary dispatch')
    monkeypatch.setattr(parent.context_compressor, 'compress', forbidden_summary)
    result = parent.request_context_compaction(relevant_threshold_tokens=100000, wait_seconds=2)
    assert result.ok and result.status == 'admitted'
    parent._native_compaction_worker.join(5)
    assert not parent._native_compaction_worker.is_alive() and len(receipts) == 1
    request = receipts[0]
    assert request.was_admitted and request.fence.is_cancelled and not request.committed
    assert db.get_native_request_publication(parent.session_id) is None
    stub_client.chat.completions.create.side_effect = [
        _tool_response('finish_noting', {'reason': 'Reviewed the frozen context.'}, 'finish'), mock_response('Finished.')]
    ref = parent._secretary_conversation_ref
    admission = db.noting_admit(ref, 'm2', kind='manual')
    outcome = run_noting_task(parent, admission_id=admission, conversation_ref=ref, anchor_message_uid='m2',
                             trigger_type='manual', runtime_profile='NOTING', task_instruction='Maintain the Notebook.')
    assert outcome.committed and db.noting_child(admission)['status'] == 'completed'
    current = db.notebook_current(ref)
    assert current['anchor_message_uid'] == 'm2'
    assert db.notebook_snapshot_audit(current['snapshot_id'])['termination']['type'] == 'finish_noting'
    flush_framework_messages(parent)
    live = [row for row in parent._session_messages if (row.get('display_metadata') or {}).get('noting_run_output')]
    durable = [row for row in db.get_messages(parent.session_id) if (row.get('display_metadata') or {}).get('noting_run_output')]
    assert len(live) == len(durable) == 1
    assert live[0]['message_uid'] == durable[0]['message_uid'] and live[0]['content'] == durable[0]['content']
    assert live[0]['display_metadata']['noting_snapshot_id'] == current['snapshot_id']
    assert current['snapshot_id'] not in live[0]['content'] and 'CURRENT NOTEBOOK SNAPSHOT' in live[0]['content']
    assert active_noting_task_count() == 0
