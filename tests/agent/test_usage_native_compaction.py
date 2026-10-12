"""Actual compression facade + SessionDB do not enter Main dispatch accounting."""
from agent.usage_read import begin_main_turn_usage, finish_main_turn_usage, main_usage_detail

pytest_plugins = ("tests.agent.test_web_compaction_control",)


def test_native_summary_and_publication_do_not_count_as_main_model_calls(runtime, monkeypatch):
    agent, db = runtime
    agent.compression_in_place = True
    begin_main_turn_usage(agent, "real-main-owner", has_prior_history=False)
    summaries = []
    def summary(prompt, started):
        summaries.append(prompt)
        return "## Progress\nPrior history summarized.\n## Open\nContinue the active request."
    monkeypatch.setattr(agent.context_compressor, "_call_summary_llm", summary)
    agent._compress_context(agent._session_messages, "Native probe root", approx_tokens=100000,
                            force=True, trigger="manual")
    assert summaries and agent.context_compressor.compression_count == 1
    assert db.get_messages(agent.session_id)
    finish_main_turn_usage(agent, "real-main-owner", {})
    latest = main_usage_detail(agent)["latest_completed_turn"]
    assert latest["model_calls"] == 0 and latest["input_tokens"] == 0
    assert agent.session_input_tokens == 0
