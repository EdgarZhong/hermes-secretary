"""A saved native stream partial keeps its observed occurrence through real SQLite commit."""
import contextlib
import copy
import threading
import time
from types import SimpleNamespace

import pytest

from agent.output_identity import accept_response, bind_stream_partial, observe_outputs
from agent.turn_api_call import handle_api_interrupt
from agent.turn_context import _bind_turn_identity
from agent.turn_retry_state import TurnRetryState
from hermes_state import SessionDB
from hermes_state_turn_terminal import persist_terminal_metadata
from run_agent import AIAgent
from tui_gateway import server
from tui_gateway.turn_terminal import observed_output_events


@pytest.fixture
def runtime(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.chdir(tmp_path)
    (home / "config.yaml").write_text("noting:\n  enabled: false\nmodel:\n  context_length: 262144\n")
    db = SessionDB(home / "state.db")
    agent = AIAgent(api_key="fixture-key", base_url="https://example.invalid/v1", model="fixture/model",
                    quiet_mode=True, skip_memory=True, skip_context_files=True, session_db=db,
                    session_id="interrupt-session", enabled_toolsets=[])
    if db.get_session(agent.session_id) is None:
        db.create_session(agent.session_id, source="tui")
    frames = []

    class Recorder:
        def write(self, frame):
            frames.append(copy.deepcopy(frame))
            return True

    sid = "interrupt-runtime"
    session = {"agent": agent, "transport": Recorder(), "history_lock": threading.RLock(),
               "session_key": agent.session_id, "running": True}
    monkeypatch.setitem(server._sessions, sid, session)
    emit = lambda kind, payload: server._emit(kind, sid, payload)
    _bind_turn_identity(agent, "interrupt-test", lambda text: emit("message.delta", {"text": text}), None, None, None)
    agent.stream_delta_callback = None
    agent._current_api_request_id = "controlled-request"
    agent._persist_user_message_idx = 0
    messages = [{"role": "user", "content": "Synthetic interrupt source."}]
    assert agent._flush_messages_to_session_db(messages, [])
    yield SimpleNamespace(agent=agent, db=db, frames=frames, emit=emit, messages=messages)
    from agent.agent_runtime_helpers import note_turn_persisted
    note_turn_persisted(agent)
    agent.close()
    db.close()


def interrupt(runtime):
    return handle_api_interrupt(runtime.agent, _retry=TurnRetryState(), thinking_spinner=None,
        messages=runtime.messages, conversation_history=[], api_start_time=time.time(),
        interrupted=False, final_response=None)


def events(runtime):
    return [frame["params"] for frame in runtime.frames if frame.get("method") == "event"]


@pytest.mark.parametrize("finalizer_fallback", [False, True])
def test_codex_completion_commits_the_streamed_identity(runtime, monkeypatch, finalizer_fallback):
    from agent import codex_runtime, relay_llm
    from agent.codex_responses_adapter import _normalize_codex_response

    text = "One complete synthetic Codex reply."
    chunks = [SimpleNamespace(type="response.output_text.delta", delta=text),
              SimpleNamespace(type="response.completed", response=SimpleNamespace(
                  id="controlled-response", status="completed", usage=None, output=[],
                  incomplete_details=None, error=None))]
    client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: iter(chunks)))
    if finalizer_fallback:
        consume = codex_runtime._consume_codex_event_stream

        def terminal_missing(stream, **kwargs):
            final = consume(stream, **kwargs)
            # Relay has the assembled response even when the consumer reports no terminal.
            stream.final_response = final
            raise RuntimeError("controlled missing terminal")

        monkeypatch.setattr(codex_runtime, "_consume_codex_event_stream", terminal_missing)
        # The controlled fallback must not recurse through Relay's own finalizer.
        monkeypatch.setattr(relay_llm, "stream", lambda kwargs, opener, **hooks: _fallback_stream(kwargs, opener, hooks))

    with observe_outputs(runtime.agent, runtime.emit) as owner:
        response = codex_runtime.run_codex_stream(runtime.agent, {"model": "fixture/model"}, client=client)
        uid = owner.current.message["message_uid"]
        message, finish_reason = _normalize_codex_response(response)
        runtime.messages.append(runtime.agent._build_assistant_message(message, finish_reason))
        assert runtime.agent._flush_messages_to_session_db(runtime.messages, [])
        assert runtime.messages[-1]["message_uid"] == uid
    assistants = [row for row in runtime.db.get_messages(runtime.agent.session_id) if row["role"] == "assistant"]
    assert [(row["message_uid"], row["content"]) for row in assistants] == [(uid, text)]
    typed = [event for event in events(runtime) if event["type"] == "message.output_delta"]
    assert typed and all(event["payload"]["message_uid"] == uid for event in typed)
    commits = [event for event in events(runtime) if event["type"] == "message.output_committed"]
    assert len(commits) == 1 and commits[0]["payload"]["source_message"]["message_uid"] == uid
    assert [event["payload"]["state"] for event in events(runtime)
            if event["type"] == "message.output_state"] == ["open", "closed"]


def _fallback_stream(kwargs, opener, hooks):
    raw = opener(kwargs)
    hooks["on_stream_created"](raw)

    class Stream:
        final_response = None

        def __iter__(self):
            return raw

        def close(self):
            pass

    return Stream()


@pytest.mark.parametrize("with_final", [False, True])
def test_codex_commentary_keeps_public_facet_through_stream_commit_and_history(runtime, with_final):
    from agent.codex_runtime import run_codex_stream
    from agent.codex_responses_adapter import _chat_messages_to_responses_input, _normalize_codex_response
    from hermes_cli.web_routers.sessions import _project_for_display

    commentary, reasoning, analysis, final = "I will check that first.", "Checking scope.", "Private analysis.", "The final answer."
    def message(text, phase, item_id):
        return SimpleNamespace(type="message", role="assistant", id=item_id, phase=phase,
                               status="completed", content=[SimpleNamespace(type="output_text", text=text)])
    items = [SimpleNamespace(type="reasoning", id="rs_test", status="completed",
                summary=[SimpleNamespace(type="summary_text", text=reasoning)], encrypted_content="opaque"),
             message(analysis, "analysis", "analysis_test"), message(commentary, "commentary", "commentary_test")]
    if with_final:
        items.append(message(final, "final_answer", "final_test"))
    else:
        items.append(SimpleNamespace(type="function_call", id="fc_test", call_id="call_test",
                                    name="terminal", arguments="{}", status="completed"))
    chunks = []
    for item in items:
        chunks.append(SimpleNamespace(type="response.output_item.added", item=item))
        if item.type == "message":
            chunks.append(SimpleNamespace(type="response.output_text.delta", delta=item.content[0].text))
        chunks.append(SimpleNamespace(type="response.output_item.done", item=item))
    chunks.append(SimpleNamespace(type="response.completed", response=SimpleNamespace(status="completed")))
    client = SimpleNamespace(responses=SimpleNamespace(create=lambda **kwargs: iter(chunks)))
    delivered = []
    runtime.agent.interim_assistant_callback = lambda text, **kwargs: (
        delivered.append(text), runtime.emit("message.interim", {"text": text, "already_streamed": False}))
    with observe_outputs(runtime.agent, runtime.emit) as owner:
        response = run_codex_stream(runtime.agent, {"model": "fixture/model"}, client=client)
        uid = owner.current.message["message_uid"]
        normalized, finish = _normalize_codex_response(response, issuer_kind="codex_backend")
        assert normalized.reasoning == f"{reasoning}\n\n{analysis}"
        assert normalized.content == (final if with_final else "")
        assert finish == ("stop" if with_final else "tool_calls")
        built = runtime.agent._build_assistant_message(normalized, finish)
        runtime.messages.append(built)
        assert runtime.agent._flush_messages_to_session_db(runtime.messages, [])
        runtime.agent._emit_interim_assistant_message(built)
    assert delivered == [commentary]
    committed = [event["payload"]["source_message"] for event in events(runtime)
                 if event["type"] == "message.output_committed"]
    assert len(committed) == 1 and committed[0]["message_uid"] == uid
    assert committed[0]["has_content"] is True and committed[0]["has_reasoning"] is True
    rows = runtime.db.get_messages_as_conversation(runtime.agent.session_id)
    row = next(message for message in rows if message["role"] == "assistant")
    assert row["message_uid"] == uid
    projected = _project_for_display([row])[0]
    assert projected["display_commentary"] == [commentary]
    assert projected["display_reasoning"] == f"{reasoning}\n\n{analysis}"
    # Model replay preserves the exact phase item, separate from final content.
    replay = _chat_messages_to_responses_input([row], current_issuer_kind="codex_backend")
    public = [item for item in replay if item.get("phase") == "commentary"]
    assert len(public) == 1 and public[0]["content"] == [{"type": "output_text", "text": commentary}]


@pytest.mark.parametrize("phase,role,expected", [
    ("commentary", "assistant", True), ("analysis", "assistant", False),
    ("commentary", "user", False), ("final_answer", "assistant", False),
])
def test_public_source_facet_requires_the_typed_assistant_commentary(phase, role, expected):
    from agent.pending_steer import native_source_message

    message = {"role": role, "content": "", "codex_message_items": [{
        "type": "message", "role": role, "phase": phase,
        "content": [{"type": "output_text", "text": "Synthetic text."}],
    }]}
    assert native_source_message(message)["has_content"] is expected


@pytest.mark.parametrize("worker", [False, True])
def test_partial_commits_observed_uid_once_and_terminal_has_no_durable_residual(runtime, worker):
    with observe_outputs(runtime.agent, runtime.emit) as owner:
        def stream():
            runtime.agent._claim_stream_writer()
            runtime.agent._fire_stream_delta("Visible synthetic partial.")
        if worker:
            thread = threading.Thread(target=stream)
            thread.start()
            thread.join()
        else:
            stream()
        uid = owner.current.message["message_uid"]
        verdict = interrupt(runtime)
        partial = runtime.messages[-1]
        assert partial["message_uid"] == uid
        assert owner.current.message is partial
        assert sum(message is partial for message in owner.messages) == 1
        assert runtime.agent._flush_messages_to_session_db(runtime.messages, [])
        commits = [event for event in events(runtime) if event["type"] == "message.output_committed"]
        assert len(commits) == 1
        assert commits[0]["payload"]["source_message"]["message_uid"] == uid
    rows = runtime.db.get_messages(runtime.agent.session_id)
    assert [(row["message_uid"], row["content"]) for row in rows if row["role"] == "assistant"] == [
        (uid, "Visible synthetic partial.")]
    observed = observed_output_events(events(runtime))
    assert len(observed) == 1 and observed[0]["message_uid"] == uid
    assert observed[0]["_before_commit"] is True
    source = rows[0]
    terminal = persist_terminal_metadata(runtime.db, runtime.agent.session_id,
        {"session_id": source["session_id"], "row_id": source["id"], "message_uid": source["message_uid"]},
        {"source_message_uid": source["message_uid"], "status": "interrupted",
         "text": verdict.final_response, "outputs": observed})
    assert "outputs" not in terminal
    saved = runtime.db.get_messages(runtime.agent.session_id)[0]["display_metadata"]["turn_terminal"]
    assert "outputs" not in saved
    assert [event["payload"]["state"] for event in events(runtime)
            if event["type"] == "message.output_state"] == ["open", "closed"]


@pytest.mark.parametrize("fault", ["writer", "request", "turn", "bound", "tool", "closed", "unclaimed"])
def test_ineligible_candidate_keeps_native_append_and_distinct_identity(runtime, fault):
    with observe_outputs(runtime.agent, runtime.emit) as owner:
        token = runtime.agent._claim_stream_writer()
        runtime.agent._fire_stream_delta("Same synthetic text.")
        candidate = owner.current

        def bind_existing(tool=False):
            raw = SimpleNamespace(content="Same synthetic text.", reasoning=None, tool_calls=None)
            if tool:
                raw.tool_calls = [SimpleNamespace(id="controlled-call", type="function",
                    function=SimpleNamespace(name="terminal", arguments="{}"))]
            accept_response(runtime.agent, raw, token)
            owned = runtime.agent._build_assistant_message(raw, "tool_calls" if tool else "stop")
            runtime.messages.append(owned)
            assert runtime.agent._flush_messages_to_session_db(runtime.messages, [])

        faults = {
            "writer": lambda: setattr(runtime.agent, "_stream_writer_token", token + 1),
            "request": lambda: setattr(runtime.agent, "_current_api_request_id", "next-request"),
            "turn": lambda: setattr(runtime.agent, "_current_turn_id", "next-turn"),
            "bound": bind_existing,
            "tool": lambda: bind_existing(tool=True),
            "closed": owner.close,
            "unclaimed": lambda: owner.candidate(token),
        }
        candidate = faults[fault]() or candidate
        uid = candidate.message["message_uid"]
        verdict = interrupt(runtime)
        assert verdict.final_response == "Same synthetic text."
        assert runtime.messages[-1]["message_uid"] != uid
        assert runtime.messages[-1]["display_metadata"] == {"interrupted": True}
        assert runtime.messages[-1] is not candidate.message
        if fault in {"bound", "tool"}:
            assistants = [row for row in runtime.db.get_messages(runtime.agent.session_id) if row["role"] == "assistant"]
            assert len(assistants) == 2
            assert assistants[0]["message_uid"] != assistants[1]["message_uid"]


@pytest.mark.parametrize("extra", [{"message_uid": "unrelated-identity"}, {"message_uid": None},
    {"tool_calls": []}, {"_row_id": 123}, {"_db_persisted": True}, {"role": "tool"}])
def test_partial_target_with_existing_identity_or_nonplain_shape_is_not_adopted(runtime, extra):
    with observe_outputs(runtime.agent, runtime.emit) as owner:
        runtime.agent._claim_stream_writer()
        original = owner.current.message
        message = {"role": "assistant", "content": "Synthetic partial.", **extra}
        before = copy.deepcopy(message)
        assert bind_stream_partial(runtime.agent, message) is message
        assert message == before
        assert owner.current.message is original
        assert owner.messages == []


def test_partial_observer_failure_cannot_block_native_append(runtime, monkeypatch):
    with observe_outputs(runtime.agent, runtime.emit) as owner:
        runtime.agent._claim_stream_writer()
        runtime.agent._fire_stream_delta("Fail-open synthetic partial.")
        def unavailable(message):
            raise RuntimeError("controlled observer unavailable")
        monkeypatch.setattr(owner, "bind_stream_partial", unavailable)
        assert interrupt(runtime).final_response == "Fail-open synthetic partial."
        assert runtime.db.get_messages(runtime.agent.session_id)[-1]["content"] == "Fail-open synthetic partial."


def test_without_observer_keeps_native_partial(runtime):
    with contextlib.nullcontext():
        runtime.agent._claim_stream_writer()
        runtime.agent._fire_stream_delta("Native partial without observer.")
        assert interrupt(runtime).final_response == "Native partial without observer."
    assert runtime.messages[-1]["display_metadata"] == {"interrupted": True}
    assert not any(event["type"] == "message.output_committed" for event in events(runtime))
