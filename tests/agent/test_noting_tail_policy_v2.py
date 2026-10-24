"""Attempt-local tail policy through the built-in engine and real SQLite publication."""
from copy import deepcopy

import pytest

from agent.context_compaction_tail_policy import NATIVE_THRESHOLD_TRIGGER, no_default_tail
from agent.conversation_compression import CompressionCommitFence
from agent.conversation_compression_manual import compress_now, parse_compress_args
from hermes_state import SessionDB
from secretary.noting_scope import owning_db_scope
from tests.agent.test_context_compaction_request import _agent, _seed


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    (tmp_path / "config.yaml").write_text("noting:\n  enabled: true\n  idle:\n    enabled: false\n")
    db = SessionDB(tmp_path / "state.db")
    _seed(db)
    parent = _agent(db, monkeypatch, tmp_path)
    parent.compression_enabled = parent.compression_in_place = True
    parent.context_compressor.context_length = 130_000
    parent.context_compressor.tail_token_budget = 1800
    parent.context_compressor.min_tail_user_messages = 3
    parent.context_compressor.protect_first_n = 2
    parent.context_compressor.protect_last_n = 8
    prompts = []

    def summarize(prompt, started):
        prompts.append(prompt)
        return "## Progress\nHistorical questions were answered; no further action is owed."

    monkeypatch.setattr(parent.context_compressor, "_call_summary_llm", summarize)
    with owning_db_scope(db):
        yield parent, db, prompts
    db.close()


def compress(parent, *, trigger=None, force=True, fence=None):
    output, _ = parent._compress_context(
        parent._session_messages, "", approx_tokens=50000, force=force,
        trigger=trigger, commit_fence=fence or CompressionCommitFence(),
    )
    return output


def visible(rows):
    return [(row["role"], row.get("content"), row.get("tool_calls"), row.get("tool_call_id")) for row in rows]


@pytest.mark.parametrize("trigger,force", [(None, True), (None, False), ("auto", False),
                                           ("overflow", False), ("noting_joint_idle", False),
                                           ("engine_maintenance", False)])
def test_non_threshold_full_summarizes_completed_tail_and_never_reinserts(runtime, trigger, force):
    parent, db, prompts = runtime
    before = deepcopy(parent._session_messages)
    settings = (parent.context_compressor.protect_last_n, parent.context_compressor.tail_token_budget,
                parent.context_compressor.min_tail_user_messages, parent.context_compressor.protect_first_n)
    result = compress(parent, trigger=trigger, force=force)
    assert prompts and all(row["content"][:30] in prompts[0] for row in before)
    assert len(result) == 1
    assert "old question" not in str(result) and "old answer" not in str(result)
    assert visible(result) == visible(db.get_messages_as_conversation(parent.session_id))
    assert len(db.get_messages(parent.session_id, include_compacted=True)) > len(result)
    assert settings == (parent.context_compressor.protect_last_n, parent.context_compressor.tail_token_budget,
                        parent.context_compressor.min_tail_user_messages, parent.context_compressor.protect_first_n)
    assert no_default_tail() is False


@pytest.mark.parametrize("mode", ["threshold", "off", "noting-child", "non-main"])
def test_native_policy_is_unchanged_for_excluded_paths(runtime, tmp_path, mode):
    parent, db, prompts = runtime
    trigger = NATIVE_THRESHOLD_TRIGGER if mode == "threshold" else None
    if mode == "off":
        (tmp_path / "config.yaml").write_text("noting:\n  enabled: false\n")
    elif mode == "noting-child":
        parent._secretary_noting_child = True
    elif mode == "non-main":
        parent.side_agent = True
    parent.context_compressor.protect_first_n = 0
    result = compress(parent, trigger=trigger)
    assert len(result) > 1
    assert any("old answer 3" in str(row.get("content")) for row in result)
    assert "old answer 3" not in str(prompts)
    assert visible(result) == visible(db.get_messages_as_conversation(parent.session_id))
    assert no_default_tail() is False


def test_explicit_here_preserves_user_selected_exchange(runtime):
    parent, db, prompts = runtime
    before = deepcopy(parent._session_messages)
    parent.context_compressor.protect_first_n = 0
    result = compress_now(parent, before, parse_compress_args("here 1"), system_message="")
    assert visible(result.after_messages[-2:]) == visible(before[-2:])
    assert "old answer 3" not in str(prompts)
    assert visible(result.after_messages) == visible(db.get_messages_as_conversation(parent.session_id))


def _active_rows():
    return [
        {"role": "user", "content": "First still-unanswered request"},
        {"role": "user", "content": [{"type": "text", "text": "Inspect both inputs"},
                                     {"type": "image_url", "image_url": {"url": "data:image/png;base64,AAAA"}}]},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": "unread", "type": "function", "function": {"name": "terminal", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": "unread", "content": "UNREAD_TOOL_RESULT " * 10000},
        {"role": "user", "display_kind": "steer", "content": "Also retain this legal steer"},
    ]


def test_unanswered_requests_multimodal_unread_round_and_steer_stay_lossless(runtime):
    parent, db, prompts = runtime
    rows = _active_rows()
    db.append_messages_batch(parent.session_id, rows)
    parent._session_messages = db.get_messages_as_conversation(parent.session_id, include_row_ids=True)
    result = compress(parent)
    text = str(result)
    assert "old answer" not in text
    assert "First still-unanswered request" in text
    assert "Inspect both inputs" in text and "data:image/png;base64,AAAA" in text
    assert rows[-2]["content"] in [row.get("content") for row in result]
    assert rows[-1]["content"] in text
    assert sum(row.get("tool_call_id") == "unread" for row in result) == 1
    assert sum(bool(row.get("tool_calls")) for row in result) == 1
    assert "UNREAD_TOOL_RESULT" not in str(prompts)
    assert visible(result) == visible(db.get_messages_as_conversation(parent.session_id))


@pytest.mark.parametrize("in_place", [True, False])
def test_new_input_beyond_compression_watermark_survives_live_and_durable(runtime, monkeypatch, in_place):
    parent, db, prompts = runtime
    parent.compression_in_place = in_place
    original = parent.context_compressor._call_summary_llm
    arrival = {"role": "user", "content": "Arrived after the compression snapshot"}

    def summarize(*args):
        db.append_messages_batch(parent.session_id, [arrival])
        return original(*args)

    monkeypatch.setattr(parent.context_compressor, "_call_summary_llm", summarize)
    result = compress(parent)
    assert arrival["content"] in str(result)
    assert visible(result) == visible(db.get_messages_as_conversation(parent.session_id))
    assert arrival["content"] not in str(prompts)


@pytest.mark.parametrize("failure", ["summary", "cancel", "commit", "lease", "no-op"])
def test_failure_never_clears_tail(runtime, monkeypatch, failure):
    parent, db, prompts = runtime
    before = deepcopy(parent._session_messages)
    before_ids = [row["_row_id"] for row in before]
    fence = CompressionCommitFence()
    original = parent.context_compressor._call_summary_llm
    if failure == "summary":
        parent.context_compressor.abort_on_summary_failure = True
        monkeypatch.setattr(parent.context_compressor, "_call_summary_llm", lambda *a: None)
    elif failure == "cancel":
        def cancel(*args):
            fence.cancel_before_commit()
            return original(*args)
        monkeypatch.setattr(parent.context_compressor, "_call_summary_llm", cancel)
    elif failure == "no-op":
        # Every input is unfinished: no completed source exists to summarize.
        db.append_message(parent.session_id, "user", "pending")
        parent._session_messages = db.get_messages_as_conversation(parent.session_id, include_row_ids=True)[-1:]
        before = deepcopy(parent._session_messages)
    else:
        original_archive = db.archive_and_compact
        def refuse(*args, **kwargs):
            if failure == "lease":
                db.release_compression_lock(parent.session_id, kwargs["lock_holder"])
                return original_archive(*args, **kwargs)
            raise RuntimeError("controlled atomic commit failure")
        monkeypatch.setattr(db, "archive_and_compact", refuse)
    result = compress(parent, fence=fence)
    assert visible(result) == visible(before)
    if failure != "no-op":
        assert [row["_row_id"] for row in db.get_messages_as_conversation(parent.session_id, include_row_ids=True)] == before_ids
    assert no_default_tail() is False


def test_gateway_precheck_does_not_apply_native_tail_floor_to_full_policy(runtime):
    parent, db, prompts = runtime
    parent.context_compressor.protect_first_n = 100
    assert parent.context_compressor.has_content_to_compress(parent._session_messages) is False
    result = compress_now(parent, parent._session_messages, parse_compress_args(""),
                          system_message="", skip_without_window=True)
    assert result.status == "compressed" and len(result.after_messages) == 1 and prompts


def test_attempt_does_not_leak_policy_to_following_native_threshold(runtime):
    parent, db, prompts = runtime
    compress(parent)
    for number in range(4):
        db.append_message(parent.session_id, "user", f"new q{number} " + "u" * 2000)
        db.append_message(parent.session_id, "assistant", f"new a{number} " + "a" * 2000)
    parent._session_messages = db.get_messages_as_conversation(parent.session_id, include_row_ids=True)
    result = compress(parent, trigger=NATIVE_THRESHOLD_TRIGGER)
    assert any("new a3" in str(row.get("content")) for row in result)
    assert no_default_tail() is False


def test_following_real_main_request_uses_durable_full_context(runtime):
    from tests.agent.test_post_tool_compression_attempt_cap import _stop_response
    parent, db, prompts = runtime
    result = compress(parent)
    wires = []
    parent.client.chat.completions.create.side_effect = lambda **kw: wires.append(deepcopy(kw)) or _stop_response()
    parent.compression_enabled = False
    parent._disable_streaming = True
    parent._use_prompt_caching = False
    next_turn = parent.run_conversation("Continue from the compacted state.", conversation_history=result,
                                         title_user_message="")
    assert next_turn["completed"] and wires
    wire = wires[0]["messages"]
    assert "Historical questions were answered" in str(wire)
    assert "old question 3" not in str(wire) and "old answer 3" not in str(wire)
    assert "Continue from the compacted state" in str(wire)


@pytest.mark.parametrize("site", ["turn-start", "pre-api", "post-tool", "pre-api-overflow", "engine-maintenance"])
def test_actual_native_threshold_seams_keep_tail(runtime, monkeypatch, site):
    from agent.turn_context_compaction import CompactionOutcome, _run_preflight_passes
    from agent.turn_preflight import PreflightGateVerdict, run_preflight_compression, compress_after_tool_results
    parent, db, prompts = runtime
    compressor = parent.context_compressor
    compressor.protect_first_n = 0
    compressor.threshold_tokens = 2000
    compressor.last_prompt_tokens = compressor.last_real_prompt_tokens = 50000
    parent.max_compression_attempts = 1
    messages = parent._session_messages
    if site == "turn-start":
        outcome = CompactionOutcome(messages, "root", [], 0)
        _run_preflight_passes(parent, outcome, compressor, 50000, "", "test")
        result = outcome.messages
    elif site in {"pre-api", "pre-api-overflow"}:
        verdict = PreflightGateVerdict(action="fallthrough", pending_moa_prepared_request=None,
            messages=messages, conversation_history=[], active_system_prompt="root",
            compression_attempts=0, api_call_count=1, final_response=None, failed=False,
            _turn_exit_reason="", _compression_timeout_exhausted=False, _preflight_compression_blocked=False,
            _provider_overflow_recovery_pending=False, _last_preflight_pressure=0)
        outcome = run_preflight_compression(parent, verdict, compressor=compressor, request_pressure_tokens=50000,
            provider_overflow_preflight=site == "pre-api-overflow", defer_preflight=lambda n: False, moa_prepared_request=None,
            system_message="", user_message="old question 3", max_compression_attempts=1, effective_task_id="test")
        result = outcome.messages
    elif site == "engine-maintenance":
        from agent.turn_context_compaction import _engine_preflight_maintenance
        monkeypatch.setattr(compressor, "should_compress_preflight", lambda *a, **kw: True)
        outcome = CompactionOutcome(messages, "root", [], 0)
        _engine_preflight_maintenance(parent, outcome, compressor, 1000, "", "test")
        result = outcome.messages
    else:
        outcome = compress_after_tool_results(parent, messages=messages, system_message="", user_message="old question 3",
            active_system_prompt="root", conversation_history=[], compression_attempts=0, max_compression_attempts=1,
            effective_task_id="test", final_response=None, turn_exit_reason="", current_turn_user_idx=0)
        result = outcome.messages
    assert prompts
    if site in {"pre-api-overflow", "engine-maintenance"}:
        assert "old answer 3" in str(prompts) and "old answer 3" not in str(result)
    else:
        assert any("old answer 3" in str(row.get("content")) for row in result)
        assert "old answer 3" not in str(prompts)


def test_image_only_unanswered_request_is_not_summarized(runtime):
    parent, db, prompts = runtime
    image = {"type": "image_url", "image_url": {"url": "data:image/png;base64,BBBB"}}
    db.append_messages_batch(parent.session_id, [{"role": "user", "content": [image]}])
    parent._session_messages = db.get_messages_as_conversation(parent.session_id, include_row_ids=True)
    result = compress(parent)
    assert "data:image/png;base64,BBBB" in str(result)
    assert "BBBB" not in str(prompts)
    assert visible(result) == visible(db.get_messages_as_conversation(parent.session_id))


def test_repeated_full_compaction_does_not_fold_a_merged_pending_request(runtime):
    parent, db, prompts = runtime
    db.append_message(parent.session_id, "user", "Unanswered request must survive both compactions")
    parent._session_messages = db.get_messages_as_conversation(parent.session_id, include_row_ids=True)
    first = compress(parent)
    assert "Unanswered request must survive both compactions" in str(first)
    call = {"role": "assistant", "content": None, "tool_calls": [
        {"id": "repeat", "type": "function", "function": {"name": "terminal", "arguments": "{}"}}]}
    db.append_messages_batch(parent.session_id, [call, {"role": "tool", "tool_call_id": "repeat", "content": "Pending answer"}])
    parent._session_messages = db.get_messages_as_conversation(parent.session_id, include_row_ids=True)
    before = deepcopy(parent._session_messages)
    second = compress(parent)
    assert visible(second) == visible(before)
    assert len(prompts) == 1


def test_covered_framework_is_summarized_without_becoming_an_unanswered_user(runtime):
    from secretary.framework_messages import publish_framework_message
    parent, db, prompts = runtime
    assert publish_framework_message(parent, "Previous background work completed.",
                                     display_metadata={"noting_run_output": True})
    result = compress(parent)
    assert len(result) == 1
    assert "Previous background work completed" in str(prompts)
    assert "Previous background work completed" not in str(result)


def test_growth_refusal_cannot_salvage_away_unanswered_input_or_unread_tools(runtime, monkeypatch):
    parent, db, prompts = runtime
    db.append_messages_batch(parent.session_id, _active_rows())
    parent._session_messages = db.get_messages_as_conversation(parent.session_id, include_row_ids=True)
    before = deepcopy(parent._session_messages)
    monkeypatch.setattr(parent.context_compressor, "_call_summary_llm", lambda *a: "oversized summary " * 20000)
    result = compress(parent)
    assert visible(result) == visible(before)
    assert visible(result) == visible(db.get_messages_as_conversation(parent.session_id))
