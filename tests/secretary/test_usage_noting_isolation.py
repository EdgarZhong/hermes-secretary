"""Actual persistent Noting child loop preserves parent Main usage ownership."""
import copy

from agent.message_metadata import build_noting_task_wrapper
from agent.usage_read import begin_main_turn_usage, main_usage_detail
from secretary.noting_child import build_noting_child, freeze_parent_active_prefix
from tests.agent.test_run_agent import _mock_response

pytest_plugins = ("tests.secretary.test_noting_child",)


def test_persistent_noting_child_accounting_is_not_parent_main_usage(parent, db, stub_client):
    begin_main_turn_usage(parent, "main-current", has_prior_history=True)
    before = copy.deepcopy(main_usage_detail(parent))
    prefix = freeze_parent_active_prefix(parent, "m2")
    child = build_noting_child(parent, runtime_profile="NOTING", parent_conversation_ref=parent._secretary_conversation_ref)
    child._disable_streaming = True
    stub_client.chat.completions.create.return_value = _mock_response(usage={
        "prompt_tokens": 400, "completion_tokens": 30, "prompt_tokens_details": {"cached_tokens": 200}})
    try:
        result = child.run_conversation(build_noting_task_wrapper("Review only.", timestamp=1791370458),
                                        conversation_history=prefix, title_user_message="")
        assert result["completed"], result
        assert child.session_input_tokens == 200 and child.session_api_calls == 1
        assert not hasattr(child, "_main_usage_read")
        assert parent.session_input_tokens == 0
        after = main_usage_detail(parent)
        assert after["session_total"] == before["session_total"]
        assert after["latest_completed_turn"] == before["latest_completed_turn"]
        assert db.get_messages(child.session_id)
    finally:
        child.close()
        parent.close()
