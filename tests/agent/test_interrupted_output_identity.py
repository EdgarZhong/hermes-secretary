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
