"""Instant driving sources publish from real admission/commit/Agent Loop before provider work."""

import json
from pathlib import Path
import threading
import time
from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from secretary import reminders, schedules
from tests.agent.test_run_agent import _mock_response
from tests.secretary.reminder_runtime import arm_native_reminder
from tests.tui_gateway.test_pending_native_turn import rpc, settled
from tui_gateway import server
from tui_gateway.contracts.registry import check_payload

pytest_plugins = ("tests.tui_gateway.test_pending_native_turn",)
_NATIVE_EMIT = server._emit


@pytest.fixture
def source_live(live):
    from secretary.noting_scope import bind_main_runtime
    config = live.home / "config.yaml"
    config.write_text(config.read_text().replace("enabled: false", "enabled: true", 1))
    live.agent._secretary_conversation_ref = live.db.resolve_conversation_ref(live.agent.session_id)
    assert bind_main_runtime(live.agent)
    live.agent.thinking_callback = lambda text: server._agent_thinking_update("runtime", text)
    return live


def arm(live, text="actual instant source"):
    ref = live.agent._secretary_conversation_ref
    schedule = arm_native_reminder(live.db, ref, {"kind": "once", "run_at": datetime.fromtimestamp(
        time.time() - 30, timezone.utc).isoformat()}, text)
    history = live.db.get_messages_as_conversation(live.agent.session_id, include_row_ids=True)
    live.session["history"] = history
    live.agent._session_messages = list(history)
    claim = schedules.claim_due(live.db, schedule["schedule_id"], owner="native-source-test")
    assert claim is not None
    return claim


def source_frames(live):
    return [payload for kind, _sid, payload in live.frames if kind == "message.source_committed"]


def block_provider(live, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    calls = []

    def provider(kwargs):
        calls.append(kwargs)
        entered.set()
        assert release.wait(timeout=10)
        return _mock_response(content="native finished", finish_reason="stop")

    monkeypatch.setattr(live.agent, "_interruptible_api_call", provider)
    return entered, release, calls


def finish(live, release):
    release.set()
    settled(live)
    assert live.session["running"] is False


def deliver(live, claim):
    server._secretary_deliver_claim("runtime", live.session, live.db, claim, reminders)


def test_committed_instant_source_precedes_thinking_and_matches_exact_row(source_live, monkeypatch):
    live = source_live
    claim = arm(live)
    predecessor = live.session["history"][-1]["message_uid"]
    entered, release, calls = block_provider(live, monkeypatch)
    deliver(live, claim)
    assert entered.wait(timeout=5)
    assert len(source_frames(live)) == 1
    payload = source_frames(live)[0]
    check_payload("message.source_committed", payload)
    row = live.db.get_messages_around(payload["stored_session_id"], payload["message"]["row_id"], 0)["window"][0]
    assert payload["message"] == {"message_uid": row["message_uid"], "row_id": row["id"],
                                  "role": "user", "content": row["content"], "timestamp": row["timestamp"]}
    assert payload["conversation_ref"] == claim["conversation_ref"]
    assert payload["turn_id"] == live.agent._current_turn_id
    assert payload["source_messages"][0]["message_uid"] == row["message_uid"]
    assert payload["source_messages"][0]["row_id"] == row["id"]
    assert payload["source_boundary"] == {
        "user_message_uid": row["message_uid"], "after_message_uid": predecessor,
        "prefix_unchanged": True, "compression_unchanged": True, "all_rows_committed": True}
    kinds = [kind for kind, _sid, _payload in live.frames]
    assert kinds.index("message.source_committed") < kinds.index("thinking.delta")
    assert "message.complete" not in kinds
    assert all(payload is None for kind, _sid, payload in live.frames if kind == "message.start")
    assert len(calls) == 1
    active_root = live.agent._cached_system_prompt
    assert "<instant-reminder>" in row["content"] and "<timestamp>" in row["content"]
    finish(live, release)
    assert len(source_frames(live)) == 1
    assert "_on_turn_user_persisted" not in vars(live.agent)
    assert len([r for r in live.db.get_messages(live.agent.session_id)
                if r["message_uid"] == row["message_uid"]]) == 1
    assert live.agent._cached_system_prompt == active_root


@pytest.mark.parametrize("failure", ["rollback", "write", "local_off", "claim_reclaimed", "lease_reclaimed"])
def test_uncommitted_active_source_never_publishes_or_calls_provider(source_live, monkeypatch, failure):
    live = source_live
    claim = arm(live)
    append = live.db.append_messages_batch

    def fail(*args, **kwargs):
        if failure == "write":
            raise OSError("controlled native write failure")
        if failure == "local_off":
            live.db.notebook_set_local_enabled(claim["conversation_ref"], False)
        elif failure == "claim_reclaimed":
            live.db._execute_write(lambda conn: conn.execute(
                "UPDATE secretary_schedule_registry SET claim_token='new-owner' WHERE schedule_id=?",
                (claim["schedule_id"],)))
        elif failure == "lease_reclaimed":
            assert kwargs["turn_lease_holder"]
            live.db._execute_write(lambda conn: conn.execute(
                "UPDATE session_turn_leases SET holder='new-owner' WHERE session_id=?",
                (live.agent.session_id,)))
        callback = kwargs["before_commit"]

        def reject(conn, sid, inserted):
            callback(conn, sid, inserted)
            if failure == "rollback":
                raise OSError("controlled rollback after active settlement")

        return append(*args, **{**kwargs, "before_commit": reject})

    monkeypatch.setattr(live.db, "append_messages_batch", fail)
    entered, release, calls = block_provider(live, monkeypatch)
    deliver(live, claim)
    settled(live)
    assert calls == [] and not entered.is_set()
    assert source_frames(live) == []
    assert not any(r["role"] == "user" for r in live.db.get_messages(live.agent.session_id))
    assert "_on_turn_user_persisted" not in vars(live.agent)
    state = live.db._read_one("SELECT state FROM secretary_schedule_registry WHERE schedule_id=?",
                             (claim["schedule_id"],))[0]
    assert state == "pending"


def test_unknown_commit_reuses_native_row_proof_and_publishes_once(source_live, monkeypatch):
    live = source_live
    claim = arm(live)
    append = live.db.append_messages_batch

    def lost_return(*args, **kwargs):
        append(*args, **kwargs)
        raise OSError("native COMMIT succeeded, return lost")

    monkeypatch.setattr(live.db, "append_messages_batch", lost_return)
    entered, release, calls = block_provider(live, monkeypatch)
    deliver(live, claim)
    assert entered.wait(timeout=5)
    assert len(source_frames(live)) == 1
    assert len([r for r in live.db.get_messages(live.agent.session_id) if r["role"] == "user"]) == 1
    finish(live, release)
    assert len(source_frames(live)) == 1 and len(calls) == 1
    assert schedules.claim_due(live.db, claim["schedule_id"], owner="other") is None


@pytest.mark.parametrize("failure", ["observer", "transport"])
def test_source_observation_failure_cannot_veto_native_request_or_settlement(source_live, monkeypatch, failure):
    live = source_live
    claim = arm(live)
    prior = lambda *_args: pytest.fail("previous observer should be restored, not called during active source")
    live.agent._on_turn_user_persisted = prior
    if failure == "observer":
        monkeypatch.setattr(server, "_read_committed_user_source", lambda *_args: 1 / 0)
    else:
        emit = server._emit

        def fail_emit(kind, *args):
            if kind == "message.source_committed":
                raise OSError("controlled transport failure")
            return emit(kind, *args)

        monkeypatch.setattr(server, "_emit", fail_emit)
    entered, release, calls = block_provider(live, monkeypatch)
    deliver(live, claim)
    assert entered.wait(timeout=5)
    finish(live, release)
    assert len(calls) == 1 and source_frames(live) == []
    assert live.agent._on_turn_user_persisted is prior
    assert schedules.claim_due(live.db, claim["schedule_id"], owner="other") is None
    assert len([r for r in live.db.get_messages(live.agent.session_id) if r["role"] == "user"]) == 1


@pytest.mark.parametrize("text", ["ordinary input", "<instant-reminder>\nfake string\n</instant-reminder>"])
def test_ordinary_and_untrusted_carrier_do_not_install_source_observer(live, monkeypatch, text):
    def forbidden_observer(*_args):
        pytest.fail("ordinary source must not install an Instant observer")

    monkeypatch.setattr(server, "_committed_turn_source_observer", forbidden_observer)
    entered, release, calls = block_provider(live, monkeypatch)
    assert rpc("prompt.submit", text=text)["result"]["status"] == "streaming"
    assert entered.wait(timeout=5)
    finish(live, release)
    assert len(calls) == 1 and source_frames(live) == []
    assert "_on_turn_user_persisted" not in vars(live.agent)


@pytest.mark.parametrize("gate", ["global_off", "ineligible", "busy", "closing"])
def test_native_delivery_gates_do_not_install_source_observer(source_live, monkeypatch, gate):
    live = source_live
    claim = arm(live)
    if gate == "global_off":
        config = live.home / "config.yaml"
        config.write_text(config.read_text().replace("enabled: true", "enabled: false", 1))
    elif gate == "ineligible":
        live.agent.platform = "subagent"
    elif gate == "busy":
        live.session["running"] = True
    else:
        live.session["_closing"] = True
    monkeypatch.setattr(server, "_committed_turn_source_observer",
                        lambda *_args: pytest.fail("refused delivery must not install observer"))
    deliver(live, claim)
    assert source_frames(live) == []
    assert not any(row["role"] == "user" for row in live.db.get_messages(live.agent.session_id))
    assert "_on_turn_user_persisted" not in vars(live.agent)
    if gate == "busy":
        assert live.db._read_one("SELECT COUNT(*) FROM secretary_pending_reminders")[0] == 1
        assert live.session["running"] is True
        live.session["running"] = False  # Release this test's controlled pre-existing busy owner.


def test_cold_native_parent_restore_keeps_committed_source_before_first_request(source_live, monkeypatch):
    from run_agent import AIAgent
    from tui_gateway.session_agent_context import prepare_resumed_parent_context, attach_recovered_agent

    live = source_live
    entered, release, _calls = block_provider(live, monkeypatch)
    assert rpc("prompt.submit", text="warm authentic conversation")["result"]["status"] == "streaming"
    assert entered.wait(timeout=5)
    finish(live, release)
    claim = arm(live, "cold restored instant")
    warm = live.agent
    history = live.session["history"]
    with patch("agent.process_bootstrap.OpenAI"), patch("agent.model_metadata.fetch_model_metadata", return_value={}):
        cold = AIAgent(api_key="test-key", base_url="http://invalid.local/v1", model="test/model",
                       session_db=live.db, session_id=warm.session_id, quiet_mode=True,
                       skip_context_files=True, skip_memory=True, enabled_toolsets=[])
    cold._disable_streaming = True
    cold.compression_enabled = False
    cold.save_trajectories = False
    cold._skip_mcp_refresh = True
    monkeypatch.setattr(cold, "_cleanup_task_resources", lambda *_args, **_kwargs: None)
    monkeypatch.setattr(cold, "_save_trajectory", lambda *_args, **_kwargs: None)
    cold.thinking_callback = lambda text: server._agent_thinking_update("runtime", text)
    assert prepare_resumed_parent_context(cold, history) is True
    root = cold._cached_system_prompt  # Preserve the root the native cold identity check actually accepted.
    assert attach_recovered_agent(server.__dict__, "runtime", live.session, cold)
    live.agent = cold
    frame_start = len(live.frames)
    entered, release, calls = block_provider(live, monkeypatch)
    try:
        deliver(live, claim)
        assert entered.wait(timeout=5)
        payload = source_frames(live)[0]
        assert payload["message"]["content"].endswith("cold restored instant\n</instant-reminder>")
        assert payload["source_boundary"]["after_message_uid"] == history[-1]["message_uid"]
        assert payload["source_boundary"]["prefix_unchanged"] is True
        assert payload["conversation_ref"] == claim["conversation_ref"]
        kinds = [kind for kind, _sid, _payload in live.frames[frame_start:]]
        assert kinds.index("message.source_committed") < kinds.index("thinking.delta")
        assert "message.complete" not in kinds and len(calls) == 1
        assert cold._cached_system_prompt == root
        finish(live, release)
        assert len(source_frames(live)) == 1
    finally:
        release.set()
        settled(live)
        cold.close()
        warm.close()


def test_same_uid_in_foreign_profile_cannot_satisfy_source_commit_proof(source_live, monkeypatch, tmp_path):
    from hermes_state import SessionDB

    live = source_live
    claim = arm(live)
    entered, release, _calls = block_provider(live, monkeypatch)
    deliver(live, claim)
    assert entered.wait(timeout=5)
    message = live.agent._session_messages[live.agent._persist_user_message_idx]
    witness = reminders.active_admission_witness(message["content"])
    assert witness.committed
    other = SessionDB(tmp_path / "foreign-profile" / "state.db")
    try:
        other.create_session(live.agent.session_id, source="cli")
        for row in live.db.get_messages(live.agent.session_id):
            other.append_message(live.agent.session_id, row["role"], content=row["content"],
                                 timestamp=row["timestamp"], message_uid=row["message_uid"])
        duplicate = other.get_messages_around(live.agent.session_id, message["_row_id"], 0)["window"][0]
        assert duplicate["message_uid"] == message["message_uid"]
        assert server._read_committed_user_source(SimpleNamespace(_session_db=other), live.agent._session_messages,
                                                  live.agent._persist_user_message_idx, witness) is None
        assert len(source_frames(live)) == 1
    finally:
        other.close()
        finish(live, release)


def test_rotated_native_tip_keeps_conversation_identity_and_real_physical_source(source_live, monkeypatch):
    from agent.prompt_cache_scope import initialize_conversation_identity
    from secretary.noting_scope import bind_main_runtime

    live = source_live
    config = live.home / "config.yaml"
    enabled = config.read_text()
    # Hold background Noting through its real config gate while preparing a real compression tip.
    config.write_text(enabled.replace("enabled: true", "enabled: false", 1))
    for index in range(8):
        live.db.append_message("stored", "user", f"past user {index} " + "old words " * 120)
        live.db.append_message("stored", "assistant", f"past response {index} " + "old response " * 120)
    live.session["history"] = live.db.get_messages_as_conversation("stored", include_row_ids=True)
    live.agent._session_messages = live.session["history"]
    initialize_conversation_identity(live.agent)
    live.agent._compression_feasibility_checked = True
    live.agent.compression_in_place = False
    compressor = live.agent.context_compressor
    compressor.context_length, compressor.threshold_tokens = 130000, 75000
    compressor.protect_first_n, compressor.protect_last_n = 2, 4
    monkeypatch.setattr(compressor, "_call_summary_llm", lambda *_a, **_k: "## Progress\nPrevious work done.\n## Open\nContinue.")
    live.agent.compression_enabled = True
    live.agent._compress_context(live.agent._session_messages, "Test fixed root", approx_tokens=100000,
                                 force=True, trigger="mid_turn")
    live.agent.compression_enabled = False
    tip = live.db.get_compression_tip("stored")
    assert tip != "stored" and live.agent.session_id == tip
    assert live.db.resolve_conversation_ref(tip) == live.agent._secretary_conversation_ref
    config.write_text(enabled)
    assert bind_main_runtime(live.agent)
    claim = arm(live, "true continuation instant")
    entered, release, _calls = block_provider(live, monkeypatch)
    deliver(live, claim)
    assert entered.wait(timeout=5)
    payload = source_frames(live)[0]
    assert payload["stored_session_id"] == tip
    assert payload["conversation_ref"] == live.db.resolve_conversation_ref("stored")
    assert payload["message"]["message_uid"] == payload["source_boundary"]["user_message_uid"]
    assert live.db.get_messages_around(tip, payload["message"]["row_id"], 0)["window"][0]["content"] == payload["message"]["content"]
    finish(live, release)
    assert len(source_frames(live)) == 1


def test_native_event_frame_routing_and_replay_keep_committed_source_order(source_live, monkeypatch):
    live = source_live
    frames = []

    class RecordingTransport:
        def write(self, frame):
            frames.append(frame)
            return True

    live.session["transport"] = RecordingTransport()
    monkeypatch.setattr(server, "_emit", _NATIVE_EMIT)
    claim = arm(live)
    entered, release, _calls = block_provider(live, monkeypatch)
    deliver(live, claim)
    assert entered.wait(timeout=5)
    events = [frame["params"] for frame in frames if frame.get("method") == "event"]
    source = next(event for event in events if event["type"] == "message.source_committed")
    thinking = next(event for event in events if event["type"] == "thinking.delta")
    assert source["session_id"] == "runtime" and source["seq"] < thinking["seq"]
    assert source["payload"]["stored_session_id"] == live.agent.session_id
    assert all("payload" not in event for event in events if event["type"] == "message.start")
    replay = rpc("session.events.since", last_seen=source["seq"] - 1)["result"]["events"]
    assert replay[0] == source
    assert [event["type"] for event in replay[:2]] == ["message.source_committed", "thinking.delta"]
    proof_dir = Path(__file__).resolve().parents[2] / ".hermes-dev" / "round2-verification" / "instant-source"
    proof_dir.mkdir(parents=True, exist_ok=True)
    persisted = live.db.get_messages_around(source["payload"]["stored_session_id"],
                                           source["payload"]["message"]["row_id"], 0)["window"][0]
    (proof_dir / "native-event-frame-proof.json").write_text(json.dumps({
        "controlled_dependency": "provider response held; real Gateway routing/replay, Agent Loop and SQLite commit",
        "source_event": source, "first_thinking_event": thinking, "replay_prefix": replay[:2],
        "persisted_row": persisted, "complete_before_source_observed": any(
            event["type"] == "message.complete" for event in events)}, ensure_ascii=False, indent=2) + "\n")
    finish(live, release)
    assert len([frame for frame in frames if (frame.get("params") or {}).get("type") == "message.source_committed"]) == 1


def test_copied_uid_in_different_conversation_cannot_admit_original_instant_source(source_live, monkeypatch):
    from run_agent import AIAgent

    live = source_live
    claim = arm(live)
    original = live.db.get_messages("stored")[-1]
    live.db.create_session("branch", source="cli", parent_session_id="stored")
    live.db.append_message("branch", original["role"], content=original["content"],
                           timestamp=original["timestamp"], message_uid=original["message_uid"])
    branch_ref = live.db.resolve_conversation_ref("branch")
    assert branch_ref != claim["conversation_ref"]
    assert live.db.get_messages("branch")[0]["message_uid"] == original["message_uid"]
    with patch("agent.process_bootstrap.OpenAI"), patch("agent.model_metadata.fetch_model_metadata", return_value={}):
        branch = AIAgent(api_key="test-key", base_url="http://invalid.local/v1", model="test/model",
                         session_db=live.db, session_id="branch", quiet_mode=True,
                         skip_context_files=True, skip_memory=True, enabled_toolsets=[])
    live.session["agent"] = branch
    monkeypatch.setattr(server, "_committed_turn_source_observer",
                        lambda *_args: pytest.fail("foreign Conversation must not install source observer"))
    try:
        deliver(live, claim)
        assert source_frames(live) == [] and live.session["running"] is False
        assert not any(row["role"] == "user" for row in live.db.get_messages("branch"))
        assert "_on_turn_user_persisted" not in vars(branch)
        assert live.db._read_one("SELECT state FROM secretary_schedule_registry WHERE schedule_id=?",
                                 (claim["schedule_id"],))[0] == "pending"
    finally:
        live.session["agent"] = live.agent
        branch.close()


def test_changed_row_address_cannot_publish_unproved_source_or_veto_native_turn(source_live, monkeypatch):
    live = source_live
    claim = arm(live)
    read = live.db.get_messages_around

    def wrong_address(*args, **kwargs):
        result = read(*args, **kwargs)
        return {**result, "window": [{**row, "id": row["id"] + 1000} for row in result["window"]]}

    monkeypatch.setattr(live.db, "get_messages_around", wrong_address)
    entered, release, calls = block_provider(live, monkeypatch)
    deliver(live, claim)
    assert entered.wait(timeout=5)
    assert source_frames(live) == []
    finish(live, release)
    assert len(calls) == 1 and source_frames(live) == []
    assert len([row for row in live.db.get_messages(live.agent.session_id) if row["role"] == "user"]) == 1
    assert schedules.claim_due(live.db, claim["schedule_id"], owner="other") is None
