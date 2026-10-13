"""New RPCs registered at production seams, real AIAgent loop and SessionDB.

Only the provider return and irrelevant host/UI side effects are controlled.
All databases and temporary profiles live under the canonical runner basetemp.
"""
import threading
import socket
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from hermes_state import SessionDB
from run_agent import AIAgent
from tests.agent.test_run_agent import _mock_response
from tools.registry import registry
from tui_gateway import server
from tui_gateway.contracts import pending as pending_contract  # noqa: F401 -- actual new wire registry

TOOL = "pending_native_probe"
registry.register(name=TOOL, toolset="utility", schema={"name": TOOL, "description": "probe",
                  "parameters": {"type": "object", "properties": {}, "required": []}},
                  handler=lambda args, **kwargs: "probe done", override=True)


@pytest.fixture
def live(monkeypatch, tmp_path):
    network_attempts = []
    def forbidden_connect(sock, address):
        network_attempts.append(address)
        raise AssertionError("provider traffic forbidden in native mechanism tests")
    monkeypatch.setattr(socket.socket, "connect", forbidden_connect)
    monkeypatch.setattr(socket.socket, "connect_ex", forbidden_connect)
    monkeypatch.setattr("agent.model_metadata._is_ollama_server", lambda *a, **k: False)
    home = tmp_path / "profile"
    home.mkdir()
    (home / "config.yaml").write_text("noting:\n  enabled: false\ncompression:\n  enabled: false\n"
                                     "model:\n  default: test/model\n  base_url: http://invalid.local/v1\n  context_length: 256000\n")
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(server, "_hermes_home", home)
    db = SessionDB(home / "state.db")
    schema = {"type": "function", "function": {"name": TOOL, "description": "probe",
              "parameters": {"type": "object", "properties": {}}}}
    with (patch("model_tools.get_tool_definitions", return_value=[schema]),
          patch("model_tools.check_toolset_requirements", return_value={}),
          patch("agent.process_bootstrap.OpenAI"),
          patch("agent.model_metadata.fetch_model_metadata", return_value={})):
        agent = AIAgent(api_key="test-key", base_url="http://invalid.local/v1", model="test/model",
                        session_db=db, session_id="stored", quiet_mode=True,
                        skip_context_files=True, skip_memory=True)
    agent._disable_streaming = True
    agent._cached_system_prompt = "Test fixed root"
    agent._use_prompt_caching = False
    agent.compression_enabled = False
    agent.save_trajectories = False
    agent.tool_delay = 0
    session = {"agent": agent, "session_key": "stored", "source": "tui", "profile_home": str(home),
               "history": [], "history_lock": threading.RLock(), "history_version": 0, "running": False,
               "attached_images": [], "image_counter": 0, "cols": 80, "slash_worker": None,
               "show_reasoning": False, "tool_progress_mode": "all", "inflight_turn": None,
               "transport": None, "created_at": 1, "close_on_disconnect": False}
    monkeypatch.setattr(server, "_sessions", {"runtime": session})
    frames = []
    monkeypatch.setattr(server, "_emit", lambda kind, sid, payload=None: frames.append((kind, sid, payload)))
    # No model/transport/profile logic is replaced; disable host-only audio/status/cleanup utilities.
    for name in ("_wire_callbacks", "_sync_agent_model_with_config", "_register_session_cwd",
                 "_tts_stream_begin", "_tts_stream_end", "_publish_session_control_snapshot",
                 "_emit_settled_session_info", "_post_turn_housekeeping", "_after_complete_turn"):
        monkeypatch.setattr(server, name, lambda *a, **k: None, raising=False)
    monkeypatch.setattr(server, "_session_cwd", lambda value: str(home))
    monkeypatch.setattr(server, "_get_usage", lambda value: {})
    monkeypatch.setattr(agent, "_cleanup_task_resources", lambda *a, **k: None)
    monkeypatch.setattr(agent, "_save_trajectory", lambda *a, **k: None)
    monkeypatch.setattr("hermes_cli.plugins.discover_plugins", lambda: None)
    monkeypatch.setattr("agent.title_generator.maybe_auto_title", lambda *a, **k: None)
    agent._ensure_db_session()
    releases = []
    yield SimpleNamespace(agent=agent, session=session, db=db, frames=frames, home=home, releases=releases)
    for release in releases:
        release.set()
    session["_closing"] = True
    from agent.pending_steer import reject_native_pending
    reject_native_pending(agent, "test_closed", include_reserved=True)
    thread = session.get("_run_thread")
    if thread:
        thread.join(5)
        assert not thread.is_alive()
    db.close()
    assert network_attempts == []


def rpc(name, **params):
    return server.handle_request({"jsonrpc": "2.0", "id": name, "method": name,
                                  "params": {"session_id": "runtime", **params}})


def begin(live, monkeypatch, *, tools=False, on_first=None, activate=True, pause_second=False):
    entered, release, completed = threading.Event(), threading.Event(), threading.Event()
    calls = []
    live.releases.append(release)
    second_entered, second_release = threading.Event(), threading.Event()
    live.releases.append(second_release)

    def provider(kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            entered.set()
            assert release.wait(5)
            if on_first:
                on_first()
            if tools:
                call = SimpleNamespace(id="call_probe", type="function",
                                       function=SimpleNamespace(name=TOOL, arguments="{}"))
                return _mock_response(content=None, finish_reason="tool_calls", tool_calls=[call])
        if len(calls) == 2 and pause_second:
            second_entered.set()
            assert second_release.wait(5)
        completed.set()
        return _mock_response(content="finished", finish_reason="stop")

    monkeypatch.setattr(live.agent, "_interruptible_api_call", provider)
    accepted = rpc("prompt.submit", text="original")
    assert accepted["result"]["status"] == "streaming"
    assert entered.wait(5)
    turn = (rpc("session.steer_pending_snapshot")["result"]["turn_id"] if activate
            else live.agent._current_turn_id)
    assert turn
    return SimpleNamespace(entered=entered, release=release, completed=completed, calls=calls, turn=turn,
                           second_entered=second_entered, second_release=second_release)


def submit(turn, operation, text):
    return rpc("session.steer_pending", turn_id=turn, operation_id=operation, text=text)["result"]


def settled(live):
    thread = live.session.get("_run_thread")
    if thread:
        thread.join(5)
        assert not thread.is_alive()


def test_rpc_consume_withdraw_and_one_real_persisted_row(live, monkeypatch):
    gate = begin(live, monkeypatch, tools=True)
    one = submit(gate.turn, "a", "same")
    two = submit(gate.turn, "b", "same")
    assert one["pending_id"] != two["pending_id"]
    removed = rpc("session.steer_withdraw", turn_id=gate.turn, pending_id=two["pending_id"])["result"]
    assert removed["state"] == "withdrawn" and removed["text"] == "same"
    gate.release.set()
    settled(live)
    rows = live.db.get_messages("stored")
    steers = [r for r in rows if r.get("display_kind") == "steer"]
    assert len(steers) == 1 and "same\nsame" not in steers[0]["content"]
    receipt = rpc("session.steer_withdraw", turn_id=gate.turn, pending_id=one["pending_id"])["result"]
    assert receipt["state"] == "already_consumed"
    assert receipt["message_uid"] == steers[0]["message_uid"]
    assert one == submit(gate.turn, "a", "same") or submit(gate.turn, "a", "same")["state"] == "consumed"
    assert any(kind == "steer.consumed" for kind, _, _ in live.frames)


def test_consumed_event_exposes_real_preflush_insertion_and_completion_sources(live, monkeypatch):
    from tui_gateway.contracts.registry import check_payload

    gate = begin(live, monkeypatch, tools=True, pause_second=True)
    one = submit(gate.turn, "first", "one")
    two = submit(gate.turn, "second", "two")
    gate.release.set()
    assert gate.second_entered.wait(5)
    consumed = [payload for kind, _, payload in live.frames if kind == "steer.consumed"]
    assert len(consumed) == 1
    payload = consumed[0]
    check_payload("steer.consumed", payload)
    message = payload["message"]
    assert payload["pending_ids"] == [one["pending_id"], two["pending_id"]]
    assert message["role"] == "user" and message["display_kind"] == "steer"
    assert message["message_uid"] == payload["message_uid"]
    assert message["display_content"] == "one\ntwo"
    assert "one\ntwo" in message["content"] and "timestamp" not in message
    prefix = payload["source_messages"]
    predecessor = payload["predecessor"]
    assert predecessor["role"] == "tool" and predecessor["tool_call_id"] == "call_probe"
    assert predecessor["message_uid"] == payload["after_message_uid"] == prefix[-1]["message_uid"]
    assert prefix[-1]["row_id"] and all("content" not in row for row in prefix)
    assert message["message_uid"] not in [row["message_uid"] for row in prefix]
    assert payload["source_boundary"] == {
        "user_message_uid": prefix[0]["message_uid"], "after_message_uid": None,
        "prefix_unchanged": True, "compression_unchanged": True,
        "all_rows_committed": True, "insertion_at_tail": True}
    assert all(row["message_uid"] != message["message_uid"] for row in live.db.get_messages("stored"))
    gate.second_release.set()
    settled(live)
    durable = live.db.get_messages("stored")
    steer = next(row for row in durable if row["message_uid"] == message["message_uid"])
    assert steer["content"] == message["content"] and steer["display_kind"] == "steer"
    assert "_row_id" not in message and "_db_persisted" not in message
    complete = [payload for kind, _, payload in live.frames if kind == "message.complete"][-1]
    check_payload("message.complete", complete)
    receipt = complete["persisted_turn"]
    assert receipt["complete"] is False  # preserve conservative one-User condition
    assert receipt["source_boundary"]["all_rows_committed"] is True
    assert receipt["source_boundary"]["prefix_unchanged"] is True
    assert receipt["source_boundary"]["compression_unchanged"] is True
    assert [(row["message_uid"], row["row_id"]) for row in receipt["source_messages"]] == [
        (row["message_uid"], row["id"]) for row in durable]
    assert "_pending_steer_source_boundary" not in vars(live.agent)


def test_natural_finish_uses_one_followup_and_late_ack_rejected(live, monkeypatch):
    gate = begin(live, monkeypatch)
    receipt = submit(gate.turn, "a", "a\nb")
    gate.release.set()
    # Followup owns a replacement run thread. Wait via final persisted response rather than first worker only.
    for _ in range(2):
        settled(live)
    assert len(gate.calls) == 2
    users = [r for r in live.db.get_messages("stored") if r["role"] == "user"]
    assert len(users) == 2 and "a\nb" in users[1]["content"]
    retry = submit(gate.turn, "a", "a\nb")
    assert retry["accepted"] and retry["pending_id"] == receipt["pending_id"]
    assert submit(gate.turn, "late", "late")["accepted"] is False


def test_interrupt_is_queryable_pending_only_one_admission(live, monkeypatch):
    gate = begin(live, monkeypatch)
    first = submit(gate.turn, "a", "one")
    second = submit(gate.turn, "b", "two")
    live.session["attached_images"] = ["not-submitted-image"]
    result = rpc("session.interrupt_pending", turn_id=gate.turn, operation_id="cut")["result"]
    assert result["state"] == "stopping"
    assert result["selected_ids"] == [first["pending_id"], second["pending_id"]]
    assert rpc("session.steer_withdraw", turn_id=gate.turn, pending_id=first["pending_id"])["result"]["state"] == "handoff_reserved"
    assert rpc("session.interrupt_pending", turn_id=gate.turn, operation_id="cut")["result"] == result
    gate.release.set()
    for _ in range(2):
        settled(live)
    status = rpc("session.interrupt_pending_status", turn_id=gate.turn, operation_id="cut")["result"]
    assert status["state"] == "followup_accepted" and status["followup"]["turn_id"] != gate.turn
    assert len(gate.calls) == 2
    assert live.session["attached_images"] == ["not-submitted-image"]
    users = [r for r in live.db.get_messages("stored") if r["role"] == "user"]
    assert len(users) == 2 and "one\ntwo" in users[-1]["content"]
    assert "not-submitted-image" not in str(gate.calls[1]["messages"])


def test_profile_and_hosted_rejection_do_not_accept(live, monkeypatch):
    gate = begin(live, monkeypatch)
    monkeypatch.setattr(server, "_profile_home", lambda profile: live.home / "another")
    mismatch = rpc("session.steer_pending", turn_id=gate.turn, operation_id="a", text="wrong", profile="other")
    assert mismatch["error"]["code"] == 4003
    live.session["_hosted_room_task"] = {"task_id": "hosted"}
    assert rpc("session.steer_pending_snapshot")["error"]["code"] == 4010
    live.session.pop("_hosted_room_task")
    gate.release.set()
    settled(live)


def test_true_tool_insertion_revalidates_withdrawn_claim(live, monkeypatch):
    from agent import pending_steer
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    original = pending_steer.append_claimed_batch
    def insert(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return original(*args, **kwargs)
    monkeypatch.setattr(pending_steer, "append_claimed_batch", insert)
    gate = begin(live, monkeypatch, tools=True)
    old = submit(gate.turn, "old", "multiline\ncorrection")
    keep = submit(gate.turn, "keep", "keep")
    gate.release.set()
    assert entered.wait(5)
    assert rpc("session.steer_withdraw", turn_id=gate.turn, pending_id=old["pending_id"])["result"]["state"] == "withdrawn"
    release.set()
    settled(live)
    rows = [r for r in live.db.get_messages("stored") if r.get("display_kind") == "steer"]
    assert len(rows) == 1 and "multiline" not in rows[0]["content"] and "keep" in rows[0]["content"]
    assert rpc("session.steer_withdraw", turn_id=gate.turn, pending_id=keep["pending_id"])["result"]["state"] == "already_consumed"


def test_finalizer_late_ack_and_interrupt_cannot_duplicate_natural_followup(live, monkeypatch):
    from agent import pending_steer
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    original = pending_steer.finish_native_turn
    def finish(agent, **kwargs):
        result = original(agent, **kwargs)
        if result:
            entered.set()
            assert release.wait(5)
        return result
    monkeypatch.setattr(pending_steer, "finish_native_turn", finish)
    gate = begin(live, monkeypatch)
    pending = submit(gate.turn, "one", "natural")
    gate.release.set()
    assert entered.wait(5)
    late = submit(gate.turn, "late", "late")
    assert not late["accepted"] and late["state"] == "terminal_conflict"
    cut = rpc("session.interrupt_pending", turn_id=gate.turn, operation_id="late-cut")["result"]
    assert cut["state"] == "already_transitioned" and not cut["selected_ids"]
    assert rpc("session.steer_withdraw", turn_id=gate.turn, pending_id=pending["pending_id"])["result"]["state"] == "handoff_reserved"
    release.set()
    for _ in range(2):
        settled(live)
    assert len(gate.calls) == 2
    assert len([r for r in live.db.get_messages("stored") if r["role"] == "user"]) == 2


@pytest.mark.parametrize("explicit", [True, False], ids=["interrupt", "natural-finalizer"])
def test_stop_before_handoff_admission_wins_native_generation_gate(live, monkeypatch, explicit):
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    original = server._run_prompt_submit
    def dispatch(rid, *args, **kwargs):
        if rid == "__pending_handoff__":
            entered.set()
            assert release.wait(5)
        return original(rid, *args, **kwargs)
    monkeypatch.setattr(server, "_run_prompt_submit", dispatch)
    gate = begin(live, monkeypatch)
    pending = submit(gate.turn, "one", "stop me")
    operation_id = "cut"
    if explicit:
        result = rpc("session.interrupt_pending", turn_id=gate.turn, operation_id=operation_id)["result"]
        assert result["state"] == "stopping"
    gate.release.set()
    assert entered.wait(5)
    if not explicit:
        operation_id = rpc("session.steer_pending_snapshot")["result"]["operation"]["operation_id"]
    assert rpc("session.interrupt")["result"] == {"status": "interrupted"}
    release.set()
    settled(live)
    status = rpc("session.interrupt_pending_status", turn_id=gate.turn, operation_id=operation_id)["result"]
    assert status["state"] == "rejected" and len(gate.calls) == 1
    assert rpc("session.steer_withdraw", turn_id=gate.turn, pending_id=pending["pending_id"])["result"]["state"] == "rejected"
    assert len([r for r in live.db.get_messages("stored") if r["role"] == "user"]) == 1


def test_nonretryable_provider_failure_terminates_accepted_pending(live, monkeypatch):
    def failed():
        raise ValueError("invalid local request")
    gate = begin(live, monkeypatch, on_first=failed)
    pending = submit(gate.turn, "one", "cannot survive failure")
    gate.release.set()
    settled(live)
    receipt = rpc("session.steer_withdraw", turn_id=gate.turn, pending_id=pending["pending_id"])["result"]
    assert receipt["state"] == "rejected" and receipt["reason"] == "turn_failed"
    assert len(gate.calls) == 1 and not live.session["running"]


def test_reconnect_snapshot_compression_gate_and_mixed_legacy(live, monkeypatch):
    gate = begin(live, monkeypatch, tools=True)
    first = submit(gate.turn, "a", "web")
    assert rpc("session.steer", text="legacy")["result"] == {"status": "queued", "text": "legacy"}
    live.session["_manual_compress_active"] = True
    rejected = submit(gate.turn, "b", "not accepted during summary")
    assert not rejected["accepted"] and rejected["state"] == "compressing"
    snap = rpc("session.steer_pending_snapshot")["result"]
    assert [r["text"] for r in snap["pending"]] == ["web", "legacy"]
    assert snap == rpc("session.steer_pending_snapshot")["result"]
    assert submit(gate.turn, "a", "web")["pending_id"] == first["pending_id"]
    live.session["_manual_compress_active"] = False
    gate.release.set()
    settled(live)
    rows = [r for r in live.db.get_messages("stored") if r.get("display_kind") == "steer"]
    assert len(rows) == 1 and "web\nlegacy" in rows[0]["content"]


def test_natural_handoff_uses_rotated_native_tip(live, monkeypatch):
    from agent.prompt_cache_scope import initialize_conversation_identity
    for index in range(30):
        live.db.append_message("stored", "user", f"question {index} " + "old words " * 120)
        live.db.append_message("stored", "assistant", f"answer {index} " + "old response " * 120)
    live.session["history"] = live.db.get_messages_as_conversation("stored", include_row_ids=True)
    live.agent._session_messages = live.session["history"]
    initialize_conversation_identity(live.agent)
    live.agent._compression_feasibility_checked = True
    live.agent.compression_in_place = False
    compressor = live.agent.context_compressor
    compressor.context_length, compressor.threshold_tokens = 130000, 75000
    compressor.protect_first_n, compressor.protect_last_n = 2, 4
    monkeypatch.setattr(compressor, "_call_summary_llm", lambda *a, **k: "## Progress\nPrevious questions answered.\n## Open\nRetain current request.")
    def rotate():
        live.agent.compression_enabled = True
        live.agent._compress_context(live.agent._session_messages, "Test fixed root", approx_tokens=100000,
                                    force=True, trigger="mid_turn")
        live.agent.compression_enabled = False
    gate = begin(live, monkeypatch, on_first=rotate)
    pending = submit(gate.turn, "one", "continue on tip")
    gate.release.set()
    for _ in range(2):
        settled(live)
    tip = live.db.get_compression_tip("stored")
    assert tip != "stored" and live.agent.session_id == tip
    op = rpc("session.steer_pending_snapshot")["result"]["operation"]
    assert op["state"] == "followup_accepted" and op["followup"]["stored_session_id"] == tip
    assert "continue on tip" in str(live.db.get_messages(tip))
    assert rpc("session.steer_withdraw", turn_id=gate.turn, pending_id=pending["pending_id"])["result"]["state"] == "already_consumed"


def test_real_admission_ownership_refusal_never_reports_accepted(live, monkeypatch):
    gate = begin(live, monkeypatch)
    pending = submit(gate.turn, "one", "refused followup")
    assert rpc("session.interrupt_pending", turn_id=gate.turn, operation_id="cut")["result"]["state"] == "stopping"
    # The actual admission method remains intact; its external ownership dependency refuses the slot.
    monkeypatch.setattr(server, "_ensure_active_session_slot", lambda *a, **k: SimpleNamespace(reason="owned_elsewhere"))
    gate.release.set()
    settled(live)
    status = rpc("session.interrupt_pending_status", turn_id=gate.turn, operation_id="cut")["result"]
    assert status["state"] == "rejected" and status["reason"] == "followup_admission_refused"
    assert len(gate.calls) == 1
    assert rpc("session.steer_withdraw", turn_id=gate.turn, pending_id=pending["pending_id"])["result"]["state"] == "rejected"
    assert not any(kind == "steer.consumed" for kind, _, _ in live.frames)


def test_finalize_session_marks_every_accepted_occurrence_terminal(live, monkeypatch):
    gate = begin(live, monkeypatch)
    one = submit(gate.turn, "one", "first")
    two = submit(gate.turn, "two", "second")
    live.session["_closing"] = True
    gate.release.set()
    settled(live)
    # Actual lifecycle finalizer is the close/shutdown backstop, independently of Loop success.
    server._finalize_session(live.session, end_reason="test_shutdown")
    owner = live.agent._pending_steer
    with live.agent._pending_steer_lock:
        assert all(owner.withdraw(gate.turn, receipt["pending_id"])["state"] == "rejected" for receipt in (one, two))
    assert len(gate.calls) == 1


def test_unused_new_path_global_off_keeps_native_string_and_old_return(live, monkeypatch):
    gate = begin(live, monkeypatch, tools=True, activate=False)
    assert rpc("session.steer", text="legacy only")["result"] == {"status": "queued", "text": "legacy only"}
    assert live.agent._pending_steer == "legacy only"
    gate.release.set()
    settled(live)
    assert live.agent._pending_steer is None
    assert not any(kind.startswith("steer.") for kind, _, _ in live.frames)
    rows = [r for r in live.db.get_messages("stored") if r.get("display_kind") == "steer"]
    assert len(rows) == 1 and "legacy only" in rows[0]["content"]


def test_rpc_capacity_retries_do_not_mutate_occurrence_inventory(live, monkeypatch):
    gate = begin(live, monkeypatch)
    ids = [submit(gate.turn, str(index), "same")["pending_id"] for index in range(256)]
    before = rpc("session.steer_pending_snapshot")["result"]
    assert len(set(ids)) == 256
    assert submit(gate.turn, "overflow", "no mutation")["state"] == "capacity"
    assert submit(gate.turn, "0", "same")["pending_id"] == ids[0]
    assert submit(gate.turn, "0", "different")["reason"] == "operation_conflict"
    assert before == rpc("session.steer_pending_snapshot")["result"]
    assert rpc("session.interrupt")["result"] == {"status": "interrupted"}
    gate.release.set()
    settled(live)
    assert len(gate.calls) == 1


def test_interrupt_reserves_only_still_pending_after_real_consumption(live, monkeypatch):
    gate = begin(live, monkeypatch, tools=True, pause_second=True)
    consumed = submit(gate.turn, "consumed", "already in tool context")
    gate.release.set()
    assert gate.second_entered.wait(5)
    assert rpc("session.steer_withdraw", turn_id=gate.turn, pending_id=consumed["pending_id"])["result"]["state"] == "already_consumed"
    remaining = submit(gate.turn, "remaining", "pending\nonly")
    result = rpc("session.interrupt_pending", turn_id=gate.turn, operation_id="cut")["result"]
    assert result["selected_ids"] == [remaining["pending_id"]]
    assert rpc("session.interrupt_pending_status", turn_id=gate.turn, operation_id="unseen")["result"]["state"] == "unknown"
    gate.second_release.set()
    for _ in range(2):
        settled(live)
    assert len(gate.calls) == 3
    users = [r for r in live.db.get_messages("stored") if r["role"] == "user"]
    assert len(users) == 3 and "pending\nonly" in users[-1]["content"]
    assert "already in tool context" not in users[-1]["content"]


@pytest.mark.parametrize("explicit", [True, False], ids=["interrupt", "natural-finalizer"])
def test_fast_followup_keeps_existing_ordinary_queue(live, monkeypatch, explicit):
    original = server._run_prompt_submit
    def dispatch(rid, *args, **kwargs):
        accepted = original(rid, *args, **kwargs)
        if rid == "__pending_handoff__":
            # Force the new native worker to finish before the outer dispatch ACK is returned.
            for _ in range(2):
                settled(live)
        return accepted
    monkeypatch.setattr(server, "_run_prompt_submit", dispatch)
    gate = begin(live, monkeypatch)
    pending = submit(gate.turn, "pending", "pending followup")
    assert rpc("prompt.submit", text="ordinary queue", queued=True)["result"]["status"] == "queued"
    if explicit:
        assert rpc("session.interrupt_pending", turn_id=gate.turn, operation_id="cut")["result"]["state"] == "stopping"
    gate.release.set()
    for _ in range(3):
        settled(live)
    assert len(gate.calls) == 3
    assert not live.session.get("queued_prompt") and not live.session.get("queued_prompts")
    users = [r for r in live.db.get_messages("stored") if r["role"] == "user"]
    assert len(users) == 3 and "pending followup" in users[1]["content"] and "ordinary queue" in users[2]["content"]
    assert rpc("session.steer_withdraw", turn_id=gate.turn, pending_id=pending["pending_id"])["result"]["state"] == "already_consumed"


def test_simultaneous_interrupt_retry_has_one_stop_and_followup(live, monkeypatch):
    gate = begin(live, monkeypatch)
    pending = submit(gate.turn, "one", "exactly once")
    stops, results = [], []
    original = server._interrupt_session_turn
    def stop(*args, **kwargs):
        stops.append(True)
        return original(*args, **kwargs)
    monkeypatch.setattr(server, "_interrupt_session_turn", stop)
    barrier = threading.Barrier(3)
    def cut():
        barrier.wait()
        results.append(rpc("session.interrupt_pending", turn_id=gate.turn, operation_id="same-op")["result"])
    workers = [threading.Thread(target=cut) for _ in range(2)]
    for worker in workers:
        worker.start()
    barrier.wait()
    for worker in workers:
        worker.join(5)
        assert not worker.is_alive()
    assert len(stops) == 1 and results[0] == results[1]
    assert results[0]["selected_ids"] == [pending["pending_id"]]
    gate.release.set()
    for _ in range(2):
        settled(live)
    assert len(gate.calls) == 2
    assert rpc("session.interrupt_pending_status", turn_id=gate.turn, operation_id="same-op")["result"]["state"] == "followup_accepted"


def test_opt_in_between_legacy_drain_and_requeue_preserves_one_owner(live, monkeypatch):
    from agent import turn_iteration_prep
    from agent.pending_steer import SteerBatch
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    original = turn_iteration_prep._inject_steer_after_newest_tool_result
    def insert(agent, messages, text, *args):
        if not isinstance(text, SteerBatch):
            entered.set()
            assert release.wait(5)
        return original(agent, messages, text, *args)
    monkeypatch.setattr(turn_iteration_prep, "_inject_steer_after_newest_tool_result", insert)
    calls = []
    def provider(kwargs):
        calls.append(kwargs)
        return _mock_response(content="finished", finish_reason="stop")
    monkeypatch.setattr(live.agent, "_interruptible_api_call", provider)
    live.agent.steer("old drained legacy")
    assert rpc("prompt.submit", text="original")["result"]["status"] == "streaming"
    assert entered.wait(5)
    turn = rpc("session.steer_pending_snapshot")["result"]["turn_id"]
    new = submit(turn, "new", "new web")
    owner = live.agent._pending_steer
    release.set()
    for _ in range(2):
        settled(live)
    assert live.agent._pending_steer is owner and len(calls) == 2
    users = [r for r in live.db.get_messages("stored") if r["role"] == "user"]
    assert len(users) == 2 and "old drained legacy\nnew web" in users[-1]["content"]
    assert rpc("session.steer_withdraw", turn_id=turn, pending_id=new["pending_id"])["result"]["state"] == "already_consumed"
