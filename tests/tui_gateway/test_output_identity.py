"""Native output object -> real batch commit -> gateway identity/replay, with legacy fallback."""
import contextlib
import copy
import json
import threading
from types import SimpleNamespace

import pytest

from agent.output_identity import observe_outputs, accept_response
from agent.turn_context import _bind_turn_identity, build_api_messages
from hermes_state import SessionDB
from run_agent import AIAgent
from tui_gateway import server
from tui_gateway import output_identity as gateway_identity


def provider_wire(kwargs):
    """Capture the actual SDK serialized HTTP body without a network/model call."""
    import httpx
    from openai import OpenAI
    bodies = []

    def respond(request):
        bodies.append(request.content.decode())
        return httpx.Response(200, json={"id": "controlled", "object": "chat.completion",
            "created": 0, "model": "fixture/model", "choices": []})

    with OpenAI(api_key="fixture-key", base_url="https://example.invalid/v1",
                http_client=httpx.Client(transport=httpx.MockTransport(respond))) as client:
        response = client.chat.completions.create(**kwargs)
        if callable(getattr(response, "close", None)):
            response.close()
    assert len(bodies) == 1
    return bodies[0]


class Recorder:
    def __init__(self, typed_failure=False):
        self.frames = []
        self.typed_failure = typed_failure

    def write(self, frame):
        if self.typed_failure and frame.get("params", {}).get("type") in {"message.output_delta", "tool.output"}:
            raise RuntimeError("additive delivery unavailable")
        self.frames.append(copy.deepcopy(frame))
        return True


def produce(home, monkeypatch, observer=True, fault=None, repeat=False, retry=False, rotate=False, worker=False, nonstream=False, ambiguous=False):
    home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HERMES_HOME", str(home))
    (home / "config.yaml").write_text("noting:\n  enabled: false\nmodel:\n  context_length: 262144\ncompression:\n  threshold_tokens: null\n")
    db = SessionDB(home / "state.db")
    agent = AIAgent(api_key="fixture-key", base_url="https://example.invalid/v1", model="fixture/model",
                    quiet_mode=True, skip_memory=True, skip_context_files=True, session_db=db,
                    session_id="fixture-session", enabled_toolsets=[])
    agent.api_mode = "chat_completions"
    agent._current_turn_timestamp = 1700000000.0
    if db.get_session(agent.session_id) is None:
        db.create_session(agent.session_id, source="tui")
    agent._secretary_conversation_ref = db.resolve_conversation_ref(agent.session_id)
    sid = "fixture-runtime"
    recorder = Recorder(typed_failure=fault == "delivery")
    session = {"agent": agent, "transport": recorder, "history_lock": threading.RLock(),
               "session_key": agent.session_id, "tool_progress_mode": "all", "running": True}
    monkeypatch.setitem(server._sessions, sid, session)
    submitted = []
    native_write = server.write_json

    def capture(frame):
        params = frame.get("params") or {}
        if params.get("type") not in {"message.output_state", "message.output_delta", "message.output_committed", "tool.output"}:
            submitted.append((params.get("type"), copy.deepcopy(params.get("payload"))))
        return native_write(frame)
    monkeypatch.setattr(server, "write_json", capture)
    emit = lambda kind, payload: server._emit(kind, sid, payload)
    _bind_turn_identity(agent, "fixture-task", lambda text: emit("message.delta", {"text": text}), None, None, None)
    agent.stream_delta_callback = None
    if nonstream:
        agent._stream_callback = None
    agent.reasoning_callback = lambda text: emit("reasoning.delta", {"text": text})
    agent.interim_assistant_callback = lambda text, *, already_streamed=False: emit("message.interim", {"text": text, "already_streamed": already_streamed})
    agent._current_api_request_id = agent._current_turn_id + ":api:1"
    messages = [{"role": "user", "content": "Calculate the budget.", "timestamp": 1700000000.0}]
    # The controlled native Turn has one actual user at index zero.
    agent._persist_user_message_idx = 0
    starting_compressions = agent.context_compressor.compression_count
    emit("message.start", {})
    context = observe_outputs(agent, emit) if observer else contextlib.nullcontext()
    with context as owner:
        if fault == "observer":
            monkeypatch.setattr(owner, "source", lambda *args: (_ for _ in ()).throw(RuntimeError("observation failed")))
        token = None if nonstream else agent._claim_stream_writer()
        if retry:
            agent._fire_reasoning_delta("An abandoned stream attempt.")
            token = agent._claim_stream_writer()
        if not nonstream:
            agent._fire_reasoning_delta("Compute the budget.")
        raw = SimpleNamespace(content="Preparing the calculation.", reasoning="Compute the budget.", tool_calls=[SimpleNamespace(
            id="reused-provider-id", type="function", function=SimpleNamespace(name="terminal", arguments='{"command":"print(2000)"}'))])
        if ambiguous:
            raw.tool_calls.append(copy.deepcopy(raw.tool_calls[0]))
        accept_response(agent, raw, token)
        assistant = agent._build_assistant_message(raw, "tool_calls")
        messages.append(assistant)
        assert agent._flush_messages_to_session_db(messages, []) is True
        agent._emit_interim_assistant_message(assistant)
        start = lambda: emit("tool.start", {"tool_id": "reused-provider-id", "name": "terminal", "args": {"command": "print(2000)"}})
        if worker:
            from tools.thread_context import propagate_context_to_thread
            thread = threading.Thread(target=propagate_context_to_thread(start))
            thread.start()
            thread.join()
        else:
            start()
        messages.append({"role": "tool", "name": "terminal", "tool_call_id": "reused-provider-id", "content": '{"output":"2000","exit_code":0}'})
        assert agent._flush_messages_to_session_db(messages, []) is True
        emit("tool.complete", {"tool_id": "reused-provider-id", "name": "terminal", "result": {"output": "2000", "exit_code": 0}})
        if repeat:
            agent._current_api_request_id = agent._current_turn_id + ":api:repeat"
            token = agent._claim_stream_writer()
            accept_response(agent, raw, token)
            messages.append(agent._build_assistant_message(raw, "tool_calls"))
            assert agent._flush_messages_to_session_db(messages, []) is True
            emit("tool.start", {"tool_id": "reused-provider-id", "name": "terminal", "args": {"command": "print(2000)"}})
            messages.append({"role": "tool", "name": "terminal", "tool_call_id": "reused-provider-id", "content": '{"output":"2000","exit_code":0}'})
            assert agent._flush_messages_to_session_db(messages, []) is True
            emit("tool.complete", {"tool_id": "reused-provider-id", "name": "terminal", "result": {"output": "2000", "exit_code": 0}})
        agent._current_api_request_id = agent._current_turn_id + ":api:2"
        if rotate:
            original_ref = db.resolve_conversation_ref(agent.session_id)
            db.publish_compression_child(parent_session_id=agent.session_id, child_session_id="fixture-child",
                source="tui", messages=messages, require_compression_lease=False)
            agent.session_id = "fixture-child"
            assert db.resolve_conversation_ref(agent.session_id) == original_ref
            messages = db.get_messages_as_conversation(agent.session_id, include_row_ids=True)
        token = None if nonstream else agent._claim_stream_writer()
        if not nonstream:
            agent._fire_stream_delta("The total is 2000.")
        raw = SimpleNamespace(content="The total is 2000.", reasoning=None, tool_calls=None)
        accept_response(agent, raw, token)
        final = agent._build_assistant_message(raw, "stop")
        messages.append(final)
        if fault == "commit":
            monkeypatch.setattr(db, "append_messages_batch", lambda **kwargs: (_ for _ in ()).throw(RuntimeError("commit failed")))
        assert agent._flush_messages_to_session_db(messages, []) is (fault != "commit")
        api_messages, _ = build_api_messages(agent, messages, current_turn_user_idx=0,
            ext_prefetch_cache=None, plugin_user_context=None, moa_config=None,
            active_system_prompt="Frozen root. Keep the existing tool boundary.")
        wire = agent._build_api_kwargs(api_messages, tools_for_api=[{"type": "function", "function": {"name": "terminal", "parameters": {"type": "object"}}}])
    status, text = ("error", "") if fault == "commit" else ("complete", "The total is 2000.")
    st = server._TurnRun(agent=agent, one_turn_restore=None, terminal_callback=None,
        receipt_committed=False, history=[], compression_count=starting_compressions,
        result={"messages": messages})
    receipt = server._persisted_turn_receipt(st, text, status)
    emit("message.complete", {"text": text, "status": status, "persisted_turn": receipt})
    rows = db.get_messages(agent.session_id)
    result = {"events": [f["params"] for f in recorder.frames if f.get("method") == "event"],
              "messages": [{**row, "row_id": row["id"]} for row in rows],
              "wire": provider_wire(wire), "legacy_input": submitted}
    actual_legacy = [(e["type"], e.get("payload")) for e in result["events"] if e["type"] not in {"message.output_state", "message.output_delta", "message.output_committed", "tool.output"}]
    assert actual_legacy == submitted
    from agent.agent_runtime_helpers import note_turn_persisted
    note_turn_persisted(agent)
    agent.close()
    db.close()
    return result


def legacy(result):
    # Native receipt UUIDs differ between independent runs. Its entire original
    # payload is checked unchanged at the actual write seam by produce().
    names = {"message.delta", "reasoning.delta", "message.interim", "tool.start", "tool.complete"}
    return [(e["type"], e.get("payload")) for e in result["events"] if e["type"] in names]


def test_actual_uid_commit_and_wire_legacy_parity(tmp_path, monkeypatch):
    plain = produce(tmp_path / "plain", monkeypatch, observer=False)
    typed = produce(tmp_path / "typed", monkeypatch)
    assert typed["wire"] == plain["wire"]
    assert legacy(typed) == legacy(plain)
    assert "message_uid" not in typed["wire"] and "tool_call_uid" not in typed["wire"]
    by_seq = {e["seq"]: e for e in typed["events"]}
    deltas = [e for e in typed["events"] if e["type"] in {"message.output_delta", "tool.output"}]
    assert {e["type"] for e in deltas} == {"message.output_delta", "tool.output"}
    for event in deltas:
        original = by_seq[event["payload"]["source_event_seq"]]
        assert original["payload"] == event["payload"]["native_payload"]
    committed = [e["payload"]["source_message"] for e in typed["events"] if e["type"] == "message.output_committed"]
    assert {r["message_uid"] for r in committed} == {r["message_uid"] for r in typed["messages"] if r["role"] != "user"}
    thinking = next(e for e in deltas if e["payload"].get("native_type") == "reasoning.delta")
    first_assistant = next(r for r in typed["messages"] if r["role"] == "assistant")
    assert thinking["payload"]["message_uid"] == first_assistant["message_uid"]
    calls = [e["payload"] for e in deltas if e["type"] == "tool.output"]
    assert calls[0]["tool_call_uid"] == calls[1]["tool_call_uid"]
    assert calls[0]["tool_call_uid"] == next(r for r in typed["messages"] if r["role"] == "tool")["tool_call_uid"]


@pytest.mark.parametrize("fault", ["observer", "delivery"])
def test_observer_failure_preserves_last_legacy_and_wire(tmp_path, monkeypatch, fault):
    plain = produce(tmp_path / "plain", monkeypatch, observer=False)
    broken = produce(tmp_path / "broken", monkeypatch, fault=fault)
    assert legacy(broken) == legacy(plain)
    assert broken["wire"] == plain["wire"]
    assert next(e for e in broken["events"] if e["type"] == "message.delta")["payload"]["text"] == "The total is 2000."


def test_actual_child_reference_projects_parent_sequence_with_interleave(tmp_path, monkeypatch):
    child = produce(tmp_path / "child", monkeypatch)
    recorder = Recorder()
    sid = "fixture-runtime"
    mirror = {"agent": None, "transport": recorder, "history_lock": threading.RLock()}
    monkeypatch.setitem(server._sessions, sid, mirror)
    origin_to_parent = {}
    for event in child["events"]:
        frame = {"jsonrpc": "2.0", "method": "event", "params": copy.deepcopy(event)}
        if event["type"] in {"message.output_delta", "tool.output"}:
            server._emit("status.update", sid, {"kind": "info", "text": "Concurrent source update"})
        assert server._relay_compute_host_rpc(frame) is True
        if event["type"] in {"message.delta", "reasoning.delta", "message.interim", "tool.start", "tool.complete"}:
            origin_to_parent[event["seq"]] = frame["params"]["seq"]
    paired = [f["params"] for f in recorder.frames if f["params"]["type"] in {"message.output_delta", "tool.output"}]
    source_pairs = [e for e in child["events"] if e["type"] in {"message.output_delta", "tool.output"}]
    assert len(paired) == len(source_pairs)
    for parent, original in zip(paired, source_pairs):
        assert parent["payload"]["source_event_seq"] == origin_to_parent[original["payload"]["source_event_seq"]]
        assert parent["payload"]["native_payload"] == original["payload"]["native_payload"]


def test_missing_child_reference_never_uses_last_sequence(monkeypatch):
    recorder = Recorder()
    sid = "unproven-runtime"
    monkeypatch.setitem(server._sessions, sid, {"agent": None, "transport": recorder})
    server._emit("message.delta", sid, {"text": "Visible unknown output"})
    fields = {"turn_id": "turn", "stored_session_id": "stored", "conversation_ref": "ref", "message_uid": "uid",
              "native_type": "message.delta", "native_payload": {"text": "Visible unknown output"}, "source_event_seq": 999}
    frame = {"jsonrpc": "2.0", "method": "event", "params": {"type": "message.output_delta", "session_id": sid, "seq": 1000, "payload": fields}}
    assert server.write_json(frame) is True
    assert len(recorder.frames) == 1
    assert recorder.frames[0]["params"]["type"] == "message.delta"


def test_retry_closes_uncommitted_attempt_and_never_adopts_its_uid(tmp_path, monkeypatch):
    result = produce(tmp_path, monkeypatch, retry=True)
    states = [e["payload"] for e in result["events"] if e["type"] == "message.output_state"]
    abandoned = next(s["message_uid"] for s in states if s["state"] == "uncommitted")
    assert abandoned not in {r["message_uid"] for r in result["messages"]}
    assert any(s["state"] == "closed" for s in states)
    assert any(e["payload"].get("native_type") == "message.interim" for e in result["events"] if e["type"] == "message.output_delta")


def test_repeated_provider_id_remains_two_native_occurrences(tmp_path, monkeypatch):
    result = produce(tmp_path, monkeypatch, repeat=True)
    starts = [e["payload"]["tool_call_uid"] for e in result["events"] if e["type"] == "tool.output" and e["payload"]["phase"] == "start"]
    assert len(starts) == 2 and len(set(starts)) == 2
    assert starts == [r["tool_call_uid"] for r in result["messages"] if r["role"] == "tool"]


def test_failed_commit_never_emits_committed_row(tmp_path, monkeypatch):
    result = produce(tmp_path, monkeypatch, fault="commit")
    final = next(e["payload"]["message_uid"] for e in result["events"] if e["type"] == "message.output_delta" and e["payload"]["native_type"] == "message.delta")
    assert final not in {e["payload"]["source_message"]["message_uid"] for e in result["events"] if e["type"] == "message.output_committed"}
    assert any(e["payload"]["message_uid"] == final and e["payload"]["state"] == "uncommitted" for e in result["events"] if e["type"] == "message.output_state")


def test_rotation_preserves_native_scope_and_commit_uid(tmp_path, monkeypatch):
    result = produce(tmp_path, monkeypatch, rotate=True)
    outputs = [e["payload"] for e in result["events"] if e["type"] == "message.output_delta"]
    assert {p["stored_session_id"] for p in outputs} == {"fixture-session", "fixture-child"}
    assert len({p["conversation_ref"] for p in outputs}) == 1
    final = next(p for p in outputs if p["native_type"] == "message.delta")
    assert final["message_uid"] == result["messages"][-1]["message_uid"]


def test_native_tool_worker_context_carries_actual_dispatch_owner(tmp_path, monkeypatch):
    result = produce(tmp_path, monkeypatch, worker=True)
    start = next(e["payload"] for e in result["events"] if e["type"] == "tool.output" and e["payload"]["phase"] == "start")
    assert start["tool_call_uid"] == next(r["tool_call_uid"] for r in result["messages"] if r["role"] == "tool")


def test_nonstream_builder_reasoning_callback_adopts_its_actual_uid(tmp_path, monkeypatch):
    result = produce(tmp_path, monkeypatch, nonstream=True)
    states = [e["payload"] for e in result["events"] if e["type"] == "message.output_state"]
    assert states and all(s["stream_writer_token"] is None for s in states)
    reasoning = next(e["payload"] for e in result["events"] if e["type"] == "message.output_delta" and e["payload"]["native_type"] == "reasoning.delta")
    assert reasoning["message_uid"] == next(r["message_uid"] for r in result["messages"] if r["role"] == "assistant")


def test_one_response_duplicate_provider_id_preserves_native_shared_uid(tmp_path, monkeypatch):
    result = produce(tmp_path, monkeypatch, ambiguous=True)
    calls = [e["payload"]["tool_call_uid"] for e in result["events"] if e["type"] == "tool.output"]
    assert len(calls) == 2 and len(set(calls)) == 1
    assert calls[0] == next(r["tool_call_uid"] for r in result["messages"] if r["role"] == "tool")
    source = next(e["payload"]["source_message"] for e in result["events"] if e["type"] == "message.output_committed" and e["payload"]["source_message"].get("tool_calls"))
    assert all(call.get("tool_call_uid") == calls[0] for call in source["tool_calls"])
    assert source["message_uid"] == next(r["message_uid"] for r in result["messages"] if r["role"] == "assistant")


def test_native_owner_fixture(tmp_path, monkeypatch):
    scenarios = []
    for name, options in [("normal", {}), ("observer_failure", {"fault": "observer"}),
                          ("typed_delivery_failure", {"fault": "delivery"}), ("repeated_provider_id", {"repeat": True})]:
        result = produce(tmp_path / name, monkeypatch, **options)
        scenarios.append({"name": name, "events": result["events"], "messages": result["messages"]})
    fixture = {"provenance": "Controlled SDK response objects; actual native writer/builder, SessionDB commit/History, gateway envelopes. No model call; no grafted historical frames.", "scenarios": scenarios}
    (tmp_path / "typed-native-fixture.json").write_text(json.dumps(fixture, ensure_ascii=False, indent=2))
    assert len(scenarios) == 4


@pytest.mark.parametrize("failure", ["install", "teardown"])
def test_observer_lifecycle_failure_never_changes_native_body(monkeypatch, failure):
    @contextlib.contextmanager
    def unavailable(*args):
        if failure == "install":
            raise RuntimeError("observer installation unavailable")
        try:
            yield
        finally:
            raise RuntimeError("observer teardown unavailable")
    monkeypatch.setattr(gateway_identity, "observe_outputs", unavailable)
    with gateway_identity.observe_session_outputs(object(), "runtime", lambda *args: None):
        result = "Native result is delivered"
    assert result == "Native result is delivered"


def test_old_turn_reference_is_not_rebound_to_new_turn(monkeypatch):
    sid = "turn-scope-runtime"
    recorder = Recorder()
    session = {"agent": None, "transport": recorder}
    monkeypatch.setitem(server._sessions, sid, session)
    base = {"stored_session_id": "stored", "conversation_ref": "ref", "message_uid": "uid",
            "api_request_id": "request", "stream_writer_token": 1}
    for turn, sequence in [("old-turn", 10), ("new-turn", 20)]:
        server.write_json({"method": "event", "params": {"session_id": sid, "seq": sequence,
            "type": "message.output_state", "payload": {**base, "turn_id": turn, "state": "open"}}})
        server.write_json({"method": "event", "params": {"session_id": sid, "seq": sequence + 1,
            "type": "message.delta", "payload": {"text": "Same text"}}})
    payload = {"turn_id": "old-turn", **{k: v for k, v in base.items() if k not in {"api_request_id", "stream_writer_token"}},
               "native_type": "message.delta", "native_payload": {"text": "Same text"}, "source_event_seq": 11}
    server.write_json({"method": "event", "params": {"session_id": sid, "seq": 30,
        "type": "message.output_delta", "payload": payload}})
    assert [f["params"]["type"] for f in recorder.frames].count("message.delta") == 2
    assert not any(f["params"]["type"] == "message.output_delta" for f in recorder.frames)
