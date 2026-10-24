"""Normal Idle uses a real Noting child, built-in summary engine and durable publication."""

import pytest

from tests.secretary.test_idle_noting_commit_order import finish_responses, result_rows, start_idle

pytest_plugins = ["tests.secretary.test_idle_noting_commit_order"]


@pytest.mark.parametrize("in_place", [True, False])
def test_idle_normal_commit_then_full_summary_then_framework(idle_runtime, monkeypatch, in_place):
    parent, db, client, workers = idle_runtime
    parent.compression_in_place = in_place
    parent.context_compressor.protect_first_n = 4
    parent.context_compressor.protect_last_n = 20
    parent.context_compressor.min_tail_user_messages = 3
    finish_responses(client)
    before = list(parent._session_messages)
    ref = parent._secretary_conversation_ref
    observed = []

    def summarize(prompt, started):
        current = db.notebook_current(ref)
        assert current is not None
        assert db.notebook_snapshot_audit(current["snapshot_id"])["termination"]["type"] == "finish_noting"
        assert not result_rows(parent)
        assert db.get_compression_lock_holder(parent.session_id)
        observed.append(prompt)
        return "## Progress\nPrior work was reviewed and completed."

    monkeypatch.setattr(parent.context_compressor, "_call_summary_llm", summarize)
    assert start_idle(parent, db) == "admitted"
    workers[0].join(15)
    assert not workers[0].is_alive()
    assert observed and all(row["content"][:25] in observed[0] for row in before)
    live = parent._session_messages
    assert len(live) == 2
    from agent.context_compressor import is_compaction_summary_message
    assert is_compaction_summary_message(live[0])
    assert "Original dialogue " not in live[0]["content"]
    assert result_rows(parent) == [live[1]]
    assert "Termination: finish_noting" in live[1]["content"]
    durable = db.get_messages_as_conversation(parent.session_id)
    assert [(row["role"], row["content"]) for row in live] == [(row["role"], row["content"]) for row in durable]
    assert parent._native_compaction_request.durable_commit_succeeded
