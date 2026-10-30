"""Formal activate handler over real SQLite, native snapshot and replay seams."""
from __future__ import annotations

import contextlib
import json
import subprocess
import sys
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest

from hermes_state import SessionDB
from hermes_state_recovery_view import project_view, read_view, selector
from tui_gateway import event_replay, inflight_output, recovery_view, server
from tui_gateway.contracts.sessions import LiveSessionSnapshot, SessionActivateParams


class Peer:
    def write(self, _frame):
        return True


@pytest.fixture
def native(tmp_path, monkeypatch, request):
    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    profile = getattr(request, "param", "default")
    home = tmp_path if profile == "default" else tmp_path / "profiles" / profile
    home.mkdir(parents=True, exist_ok=True)
    db = SessionDB(db_path=home / "state.db")
    db.create_session("stored", source="pi-import" if profile != "default" else "desktop", profile_name="default")
    db.append_messages_batch("stored", [{"role":"user","content":"Question","timestamp":1},
                                        {"role":"assistant","content":"Answer","timestamp":2}])
    agent = SimpleNamespace(model="controlled", session_id="stored", _current_turn_id="native-turn",
                            _active_session_turn_lease_holder=None)
    session = {"_sid":"runtime", "agent":agent, "session_key":"stored", "profile_home":str(home),
               "history":[], "history_lock":threading.Lock(), "created_at":1., "running":False,
               "transport":Peer()}
    monkeypatch.setattr(server,"_sessions",{"runtime":session})
    monkeypatch.setattr(server,"_fallback_session_info",lambda _session:{"model":"controlled"})
    monkeypatch.setattr(server,"profile_name_for_home",lambda home:profile)
    monkeypatch.setattr(server,"_launch_home",lambda:str(home))
    monkeypatch.setattr(server,"_current_profile_name",lambda:profile)
    @contextlib.contextmanager
    def owner(_session):
        yield db
    monkeypatch.setattr(server,"_session_db",owner)
    event_replay.reset_replay_state()
    yield db, session, home
    db.close()


def request(db, selections=None, details=(), *, profile="default"):
    selections = selections or [selector()]
    projected = project_view(read_view(db,"stored",profile,selections))
    return {"version":1,"profile":profile,"stored_id":"stored",
            "windows":[{"selector":item["selector"],"receipt":item["coverage"]} for item in projected["windows"]],
            "details":list(details)}


def activate(req):
    params = {"session_id":"runtime","omit_messages":True,"recovery_view":req}
    SessionActivateParams.model_validate(params)
    reply = server._methods["session.activate"]("activate",params)
    assert "error" not in reply, reply
    LiveSessionSnapshot.model_validate(reply["result"])
    return reply["result"]["recovery_view"]


def begin(db, session, holder="pid=123:turn=native-turn:platform=desktop"):
    assert db.try_acquire_session_turn_lease("stored",holder)
    session["agent"]._active_session_turn_lease_holder = holder
    with session["history_lock"]:
        session["running"] = True
        server._start_inflight_turn(session,"Question")
    user = db.get_messages("stored")[0]
    server._emit("message.source_committed","runtime",{
        "turn_id":"native-turn","stored_session_id":"stored","conversation_ref":"controlled",
        "message":{"role":"user","content":"Question","timestamp":1,"row_id":user["id"],"message_uid":user["message_uid"]},
        "source_messages":[],"source_boundary":{"user_message_uid":user["message_uid"],
         "after_message_uid":None,"prefix_unchanged":True,"compression_unchanged":True,"all_rows_committed":True}})
    return holder


def test_formal_idle_envelope_matches_and_full_replacement_after_append(native):
    db, _session, _home = native
    req = request(db)
    view = activate(req)
    assert view["complete"] and view["windows"][0]["matched"]
    assert "messages" not in view["windows"][0]
    db.append_message("stored","assistant","Later")
    changed = activate(req)
    assert changed["complete"] and not changed["windows"][0]["matched"]
    assert [row["content"] for row in changed["windows"][0]["messages"]] == ["Question","Answer","Later"]
    assert changed["stream_cut"]["latest_seq"] >= changed["stream_cut"]["snapshot_seq"]


@pytest.mark.parametrize("native", ["alex"], indirect=True)
def test_imported_profile_label_does_not_override_actual_runtime_owner(native):
    db, _session, _home = native
    req = request(db, profile="alex")
    result = activate(req)
    assert result["complete"] and result["owner"]["profile"] == "alex"
    assert result["windows"][0]["matched"]
    assert db.get_session("stored")["profile_name"] == "default"
    wrong = json.loads(json.dumps(req))
    wrong["profile"] = "study"
    for window in wrong["windows"]:
        window["receipt"]["profile"] = "study"
    denied = activate(wrong)
    assert not denied["complete"] and denied["reason"] == "owner_mismatch"


def test_d0_s_d1_external_append_and_finite_delta_suffix(native, monkeypatch):
    db, session, home = native
    req = request(db)
    begin(db,session)
    original = recovery_view.snapshot
    def capture(*args, **kwargs):
        state = original(*args,**kwargs)
        with SessionDB(db_path=home/"state.db") as writer:
            writer.append_message("stored","assistant","external append")
        server._emit("message.delta","runtime",{"text":"continued"})
        return state
    monkeypatch.setattr(recovery_view,"snapshot",capture)
    view = activate(req)
    assert view["complete"] and view["running"]
    assert view["windows"][0]["messages"][-1]["content"] == "external append"
    assert view["stream_cut"]["events"][-1]["payload"]["text"] == "continued"
    assert session["running"]  # recovery did not wait for settlement


@pytest.mark.parametrize("mutation",["replace","rewind","compression","delete"])
def test_independent_process_destructive_change_between_d0_and_s(native, monkeypatch, mutation):
    db, _session, home = native
    req = request(db)
    original = recovery_view.snapshot
    calls = []
    def capture(*args,**kwargs):
        state = original(*args,**kwargs)
        if not calls:
            script = '''import sys
from pathlib import Path
from hermes_state import SessionDB
with SessionDB(db_path=Path(sys.argv[1])) as db:
    kind=sys.argv[2]
    if kind=='replace': db.replace_messages('stored',[{'role':'user','content':'replacement'},{'role':'assistant','content':'new'}])
    elif kind=='rewind': db.rewind_to_message('stored',db.get_messages('stored')[0]['id'])
    elif kind=='compression': db.archive_and_compact('stored',[{'role':'user','content':'summary','_compressed_summary':True}])
    else: db.delete_session('stored')
'''
            subprocess.run([sys.executable,"-c",script,str(home/"state.db"),mutation],check=True,timeout=15)
            calls.append(True)
        return state
    monkeypatch.setattr(recovery_view,"snapshot",capture)
    view = activate(req)
    if mutation == "delete":
        assert not view["complete"] and view["reason"] == "not_found"
    else:
        assert view["complete"] and not view["windows"][0]["matched"]
        messages = view["windows"][0]["messages"]
        if mutation == "replace":
            assert [row["content"] for row in messages] == ["replacement","new"]
        elif mutation == "rewind":
            assert "Answer" not in [row.get("content") for row in messages]


def test_repeated_rewrite_is_bounded_failure(native,monkeypatch):
    db, _session, _home = native
    req = request(db)
    original, attempts = recovery_view.snapshot, []
    def capture(*args,**kwargs):
        state=original(*args,**kwargs)
        attempts.append(1)
        db.replace_messages("stored",[{"role":"assistant","content":str(len(attempts))}])
        return state
    monkeypatch.setattr(recovery_view,"snapshot",capture)
    result=activate(req)
    assert not result["complete"] and result["reason"] == "view_changed" and len(attempts)==2


def test_external_lease_is_normal_but_missing_local_snapshot_is_not(native):
    db, session, _home=native
    req=request(db)
    db.try_acquire_session_turn_lease("stored","external-owner")
    external = activate(req)
    assert external["complete"] and external["running"] and external["live_output_available"] is False
    db.release_session_turn_lease("stored","external-owner")
    session["running"]=True
    session["inflight_turn"]={"assistant":"unproved text"}
    assert activate(req)["reason"] == "runtime_unavailable"


def test_native_current_lease_handoff_rejects_stale_complete_snapshot(native,monkeypatch):
    db,session,_home=native
    req=request(db)
    holder=begin(db,session)
    original=recovery_view.snapshot
    def handoff(*args,**kwargs):
        state=original(*args,**kwargs)
        db.release_session_turn_lease("stored",holder)
        assert db.try_acquire_session_turn_lease("stored","pid=123:turn=other:platform=desktop")
        return state
    monkeypatch.setattr(recovery_view,"snapshot",handoff)
    result=activate(req)
    assert not result["complete"] and result["reason"] in ("view_changed","runtime_unavailable")


def test_ring_gap_restarts_once_without_chasing_turn_end(native,monkeypatch):
    db,session,_home=native
    req=request(db)
    begin(db,session)
    original=recovery_view.project_view
    projected=[]
    def backlog(*args,**kwargs):
        result=original(*args,**kwargs)
        if not projected:
            for _ in range(550):
                server._emit("message.delta","runtime",{"text":"x"})
            projected.append(True)
        return result
    monkeypatch.setattr(recovery_view,"project_view",backlog)
    view=activate(req)
    assert view["complete"] and view["running"]
    assert view["stream_cut"]["snapshot_seq"] >= 550
    assert view["state_snapshot"]["events"][-1]["payload"]["text"] == "x"*550


def test_old_activate_and_history_lock_timeout(native):
    db,session,_home=native
    old=server._methods["session.activate"]("old",{"session_id":"runtime","omit_messages":True})["result"]
    assert "recovery_view" not in old and old["recovery_view_version"] == 1
    req=request(db)
    session["history_lock"].acquire()
    try:
        view=activate(req)
    finally:
        session["history_lock"].release()
    assert not view["complete"] and view["reason"] == "history_busy"


def native_output(session, uid="output-uid", tool_uid=None):
    """Actual paired native/relay frames; the snapshot and seq use production seams."""
    scope={"turn_id":"native-turn","stored_session_id":"stored","conversation_ref":"controlled","message_uid":uid}
    server._emit("message.output_state","runtime",{**scope,"state":"open","api_request_id":"request","stream_writer_token":1})
    legacy={"jsonrpc":"2.0","method":"event","params":{"type":"message.delta","session_id":"runtime","payload":{"text":"old live answer"}}}
    server.write_json(legacy)
    server._emit("message.output_delta","runtime",{**scope,"native_type":"message.delta","native_payload":{"text":"old live answer"},
                                                   "source_event_seq":legacy["params"]["seq"]})
    if tool_uid:
        legacy={"jsonrpc":"2.0","method":"event","params":{"type":"tool.start","session_id":"runtime",
            "payload":{"tool_id":"provider-call","name":"terminal","args":{"cmd":"controlled"}}}}
        server.write_json(legacy)
        tool_scope={key:value for key,value in scope.items() if key != "message_uid"}
        server._emit("tool.output","runtime",{**tool_scope,"assistant_message_uid":uid,"tool_call_uid":tool_uid,"phase":"start",
            "native_payload":legacy["params"]["payload"],"source_event_seq":legacy["params"]["seq"]})


def begin_web(db, session):
    """Ordinary Web uses the real persisted-source observer, no Reminder event."""
    from tui_gateway import turn_terminal
    holder = "pid=123:turn=native-turn:platform=desktop"
    assert db.try_acquire_session_turn_lease("stored", holder)
    session["agent"]._active_session_turn_lease_holder = holder
    session["agent"]._session_db = db
    with session["history_lock"]:
        session["running"] = True
        server._start_inflight_turn(session, "Question")
    row = dict(db.get_messages("stored")[0])
    row["_row_id"] = row["id"]
    observe = turn_terminal.source_observer("runtime", session, session["agent"], turn_terminal.token(session), None)
    observe([row], 0)
    assert session["inflight_turn"]["_terminal_source"]["message_uid"] == row["message_uid"]
    native_output(session)
    return holder


def test_ordinary_web_native_source_recovers_without_reminder_event(native):
    db, session, _home = native
    req = request(db)
    begin_web(db, session)
    session["inflight_turn"]["_terminal_source"]["message"] = {"content": "untrusted cached text"}
    view = activate(req)
    assert view["complete"] and view["running"]
    events = view["state_snapshot"]["events"]
    assert not any(event["type"] == "message.source_committed" for event in events)
    assert any(event["type"] == "message.delta" for event in events)


@pytest.mark.parametrize("native", ["default", "alex"], indirect=True)
def test_other_profile_actual_source_db_cannot_prove_same_stored_locator(native):
    from tui_gateway import turn_terminal
    db, session, home = native
    begin_web(db, session)
    with SessionDB(db_path=home / "other-profile.db") as other:
        other.create_session("stored", source="desktop")
        other.append_message("stored", "user", "other profile source")
        session["agent"]._session_db = other
        row = dict(other.get_messages("stored")[0])
        row["_row_id"] = row["id"]
        turn_terminal.source_observer("runtime", session, session["agent"], turn_terminal.token(session), None)([row], 0)
    view = activate(request(db, profile=server.profile_name_for_home(home)))
    assert not view["complete"] and view["reason"] == "owner_mismatch"


def test_native_source_must_be_a_user_row(native):
    db, session, _home = native
    begin_web(db, session)
    assistant = db.get_messages("stored")[1]
    session["inflight_turn"]["_terminal_source"].update(row_id=assistant["id"], message_uid=assistant["message_uid"])
    view = activate(request(db))
    assert not view["complete"] and view["reason"] == "view_changed"


def test_settled_alias_never_rebinds_a_real_active_turn_source(native):
    db, session, _ = native
    holder = begin_web(db, session)
    source = dict(session["inflight_turn"]["_terminal_source"])
    db.release_session_turn_lease("stored", holder)
    db.archive_and_compact("stored", db.get_messages_as_conversation("stored", include_row_ids=True))
    assert db.try_acquire_session_turn_lease("stored", holder)
    try:
        raw = read_view(db, "stored", "default", [selector()], identities=[source])
        assert any(row["id"] != source["row_id"] for row in raw["identities"])
        view = activate(request(db))
        assert not view["complete"] and view["reason"] == "view_changed"
    finally:
        db.release_session_turn_lease("stored", holder)


@pytest.mark.parametrize("field,value,reason", [
    ("db_path", "/different-profile/state.db", "owner_mismatch"),
    ("session_id", "other-conversation", "view_changed"),
    ("row_id", 999999, "view_changed"),
    ("message_uid", "unknown-user", "view_changed"),
])
def test_web_native_source_requires_exact_durable_owner_and_row(native, field, value, reason):
    db, session, _home = native
    begin_web(db, session)
    session["inflight_turn"]["_terminal_source"][field] = value
    view = activate(request(db))
    assert not view["complete"] and view["reason"] == reason


@pytest.mark.parametrize("mutation", ["replace", "rewind", "compression"])
def test_web_native_source_retired_by_formal_writer_cannot_lend_live_output(native, mutation):
    db, session, _home = native
    begin_web(db, session)
    if mutation == "replace":
        db.replace_messages("stored", [{"role": "user", "content": "different source"}])
    elif mutation == "rewind":
        db.rewind_to_message("stored", db.get_messages("stored")[0]["id"])
    else:
        db.archive_and_compact("stored", [{"role": "user", "content": "summary", "_compressed_summary": True}])
    view = activate(request(db))
    # Rewind also revokes the real lease; either missing ownership or a retired
    # source is an explicit refusal, never an active recovery success.
    assert not view["complete"] and view["reason"] in {"view_changed", "runtime_unavailable"}


@pytest.mark.parametrize("mutation", ["token", "turn", "holder", "missing_holder", "missing_source"])
def test_web_source_cannot_cross_turn_or_lease_capture(native, monkeypatch, mutation):
    db, session, _home = native
    holder = begin_web(db, session)
    original = recovery_view.snapshot
    def takeover():
        db.release_session_turn_lease("stored", holder)
        assert db.try_acquire_session_turn_lease("stored", "pid=456:turn=native-turn:platform=desktop")
    changes = {
        "token": lambda: session["inflight_turn"].__setitem__("_terminal_token", object()),
        "turn": lambda: setattr(session["agent"], "_current_turn_id", "other-turn"),
        "holder": takeover,
        "missing_holder": lambda: setattr(session["agent"], "_active_session_turn_lease_holder", None),
        "missing_source": lambda: session["inflight_turn"].pop("_terminal_source", None),
    }
    def change(*args, **kwargs):
        state = original(*args, **kwargs)
        changes[mutation]()
        return state
    monkeypatch.setattr(recovery_view, "snapshot", change)
    view = activate(request(db))
    assert not view["complete"] and view["reason"] in {"view_changed", "runtime_unavailable"}


def settled_web_output(db, session):
    """The same native frames and durable receipt as the real UI trace."""
    holder = begin_web(db, session)
    user = db.get_messages("stored")[0]
    source = {"role": "user", "row_id": user["id"], "message_uid": user["message_uid"],
              "has_content": True, "has_reasoning": False}
    server._emit("message.user_committed", "runtime", {"stored_session_id": "stored", "message": {
        "role": "user", "row_id": user["id"], "message_uid": user["message_uid"],
        "content": user["content"], "timestamp": user["timestamp"]}})
    db.append_message("stored", "assistant", "old live answer", message_uid="output-uid")
    assistant = db.get_messages("stored")[-1]
    output = {"role": "assistant", "row_id": assistant["id"], "message_uid": assistant["message_uid"],
              "has_content": True, "has_reasoning": False}
    server._emit("reasoning.available", "runtime", {"text": "old live answer"})
    server._emit("message.output_committed", "runtime", {
        "turn_id": "native-turn", "stored_session_id": "stored", "conversation_ref": "controlled", "source_message": output})
    receipt = {"complete": True, "row_ids": [source["row_id"], output["row_id"]], "source_messages": [source, output]}
    server._emit("message.complete", "runtime", {"text": "old live answer", "persisted_turn": receipt})
    with session["history_lock"]:
        session["running"] = False
        server._clear_inflight_turn(session)
    db.release_session_turn_lease("stored", holder)
    return receipt


@pytest.mark.parametrize("receipt_state", ["valid", "compacted", "missing", "wrong_row", "retired"])
def test_settled_web_notifications_use_existing_durable_receipt(native, receipt_state):
    db, session, _home = native
    receipt = settled_web_output(db, session)
    completed = session["_inflight_output"]["events"][-1]["payload"]
    mutate = {
        "valid": lambda: None,
        "missing": lambda: completed.pop("persisted_turn"),
        "wrong_row": lambda: completed["persisted_turn"]["source_messages"][-1].update(row_id=999999),
        "retired": lambda: db.rewind_to_message("stored", receipt["source_messages"][0]["row_id"]),
        "compacted": lambda: db.archive_and_compact("stored", [{"role": "user", "content": "summary", "_compressed_summary": True}]),
    }
    mutate[receipt_state]()
    view = activate(request(db))
    if receipt_state in {"valid", "compacted"}:
        assert view["complete"] and not view["running"] and not view["state_snapshot"]["events"]
    else:
        assert not view["complete"] and view["reason"] == "runtime_unavailable"


@pytest.mark.parametrize("event_type", ["message.delta", "reasoning.delta"])
def test_settled_receipt_never_accepts_unknown_output(native, event_type):
    db, session, _home = native
    settled_web_output(db, session)
    server._emit(event_type, "runtime", {"text": "unaccounted output"})
    view = activate(request(db))
    assert not view["complete"] and view["reason"] == "runtime_unavailable"


def test_active_reasoning_notice_keeps_its_existing_display(native):
    db, session, _home = native
    begin_web(db, session)
    server._emit("reasoning.available", "runtime", {"text": "active reasoning"})
    view = activate(request(db))
    assert view["complete"] and view["running"]
    assert any(event["type"] == "reasoning.available" for event in view["state_snapshot"]["events"])


@pytest.mark.parametrize("mutation",["replace","rewind","delete"])
def test_settled_old_snapshot_never_revives_after_stable_formal_rewrite(native,mutation):
    db,session,_home=native
    req=request(db)
    holder=begin(db,session)
    native_output(session)
    with session["history_lock"]:
        server._clear_inflight_turn(session)
        session["running"]=False
    db.release_session_turn_lease("stored",holder)
    if mutation=="replace":
        db.replace_messages("stored",[{"role":"user","content":"new question"},{"role":"assistant","content":"new answer"}])
    elif mutation=="rewind":
        db.rewind_to_message("stored",db.get_messages("stored")[0]["id"])
    else:
        db.delete_session("stored")
    result=activate(req)
    if mutation != "delete":
        assert result["complete"] and not result["state_snapshot"]["events"]
        assert "old live answer" not in json.dumps(result)
    else:
        assert not result["complete"] and result["reason"] == "not_found"


def test_settled_proven_durable_output_uses_authoritative_row_and_no_live_tail(native):
    db,session,_home=native
    holder=begin(db,session)
    native_output(session)
    db.append_message("stored","assistant","durable authoritative text",message_uid="output-uid")
    with session["history_lock"]:
        server._clear_inflight_turn(session)
        session["running"]=False
    db.release_session_turn_lease("stored",holder)
    result=activate(request(db))
    assert result["complete"] and result["state_snapshot"]["events"] == []


def test_active_durable_tool_parent_keeps_unpersisted_exact_occurrence(native):
    db,session,_home=native
    begin(db,session)
    db.append_messages_batch("stored",[{"role":"assistant","content":None,"message_uid":"output-uid","tool_calls":[{
        "id":"provider-call","function":{"name":"terminal","arguments":"{}"}}],
        "_tool_call_uids":{"provider-call":"tool-occurrence"}}])
    native_output(session,tool_uid="tool-occurrence")
    result=activate(request(db))
    assert result["complete"]
    assert any(event["type"]=="tool.start" for event in result["state_snapshot"]["events"])
    db.append_messages_batch("stored",[{"role":"tool","content":"durable result","tool_call_id":"provider-call","_tool_call_uid":"tool-occurrence"}])
    result=activate(request(db))
    assert result["complete"]
    assert not any(event["type"]=="tool.start" for event in result["state_snapshot"]["events"])


def test_anchor_alias_retired_and_large_append_gap(native,monkeypatch):
    db,_session,_home=native
    req=request(db,[selector({"kind":"latest","limit":1})])
    original=recovery_view.snapshot
    def append_many(*args,**kwargs):
        state=original(*args,**kwargs)
        db.append_messages_batch("stored",[{"role":"assistant","content":f"append-{i}"} for i in range(3)])
        return state
    monkeypatch.setattr(recovery_view,"snapshot",append_many)
    result=activate(req)
    assert not result["complete"] and result["reason"] == "coverage_gap"


def test_projection_does_not_hold_history_database_replay_or_global_resume_lock(native,monkeypatch):
    db,session,_home=native
    req=request(db)
    original_read,original_project=recovery_view.read_view,recovery_view.project_view
    observed=[]
    def read(*args,**kwargs):
        assert server._session_resume_lock.acquire(blocking=False)
        server._session_resume_lock.release()
        assert event_replay._replay_lock.acquire(blocking=False)
        event_replay._replay_lock.release()
        observed.append("read")
        return original_read(*args,**kwargs)
    def project(*args,**kwargs):
        assert session["history_lock"].acquire(blocking=False)
        session["history_lock"].release()
        assert event_replay._replay_lock.acquire(blocking=False)
        event_replay._replay_lock.release()
        with db._read_ctx() as conn:
            assert not conn.in_transaction
        observed.append("project")
        return original_project(*args,**kwargs)
    monkeypatch.setattr(recovery_view,"read_view",read)
    monkeypatch.setattr(recovery_view,"project_view",project)
    assert activate(req)["complete"]
    assert observed == ["read","read","project","project"]


def test_idle_unknown_output_without_committed_source_refuses_ready(native):
    db,session,_home=native
    inflight_output.start(session)
    native_output(session)
    result=activate(request(db))
    assert not result["complete"] and result["reason"] == "runtime_unavailable"


def test_deep_visible_anchor_latest_and_expanded_details_are_independently_bounded(native):
    db,_session,_home=native
    db.append_messages_batch("stored",[{"role":"assistant","content":f"step-{i}","reasoning":f"detail-{i}"} for i in range(1100)])
    anchor=db._read_one("SELECT id,message_uid FROM messages WHERE session_id='stored' ORDER BY id LIMIT 1 OFFSET 30")
    selections=[selector(),selector({"kind":"anchor","anchor_uid":anchor["message_uid"],"before":2,"after":2})]
    req=request(db,selections,[{"row_id":anchor["id"],"message_uid":anchor["message_uid"]}])
    result=activate(req)
    assert result["complete"] and len(result["windows"]) == 2
    assert result["windows"][0]["coverage"]["window"]["returned"] == 200
    assert result["windows"][1]["coverage"]["window"]["returned"] == 5
    assert result["windows"][0]["coverage"]["window"]["start"] > result["windows"][1]["coverage"]["window"]["end"]+1
    assert result["details"][0]["reasoning"] == "detail-28"


def test_continuous_native_delta_finishes_at_finite_cut_without_settling(native):
    db,session,_home=native
    begin(db,session)
    req=request(db)
    stop,started=threading.Event(),threading.Event()
    def stream():
        while not stop.is_set():
            server._emit("message.delta","runtime",{"text":"x"})
            started.set()
            stop.wait(0.001)
    writer=threading.Thread(target=stream)
    writer.start()
    try:
        assert started.wait(5)
        result=activate(req)
        assert result["complete"] and result["running"]
        cut=result["stream_cut"]
        assert [event["seq"] for event in cut["events"]] == list(range(cut["snapshot_seq"]+1,cut["latest_seq"]+1))
        assert session["running"]
    finally:
        stop.set();writer.join(5)
    assert not writer.is_alive()


def test_epoch_change_between_snapshot_and_suffix_never_crosses_cut(native,monkeypatch):
    db,_session,_home=native
    original=recovery_view.project_view
    epochs=[]
    def changed(*args,**kwargs):
        result=original(*args,**kwargs)
        epochs.append(str(len(epochs)))
        monkeypatch.setattr(event_replay,"_REPLAY_EPOCH","changed-"+epochs[-1])
        return result
    monkeypatch.setattr(recovery_view,"project_view",changed)
    result=activate(request(db))
    assert not result["complete"] and result["reason"] == "replay_gap"
    assert len(epochs) == 4  # at most one restart


def test_idle_native_exceptional_terminal_sidecar_accounts_for_unpersisted_output(native):
    db,session,home=native
    holder=begin(db,session)
    user=db.get_messages("stored")[0]
    from tui_gateway import turn_terminal
    token=turn_terminal.token(session)
    turn_terminal.remember_source(session,{"db_path":str((home/"state.db").resolve()),"session_id":"stored",
                                          "row_id":user["id"],"message_uid":user["message_uid"],"message":user},token)
    native_output(session)
    turn_terminal.persist("runtime",session,{"status":"error","text":"old live answer","error":"controlled"},token)
    with session["history_lock"]:
        server._clear_inflight_turn(session)
        session["running"]=False
    db.release_session_turn_lease("stored",holder)
    req=request(db)
    result=activate(req)
    assert result["complete"] and result["state_snapshot"]["events"] == []
    assert db.get_messages("stored")[0]["display_metadata"]["turn_terminal"]["status"] == "error"


def test_tool_occurrence_identity_uses_exact_uid_not_substring(native):
    db,session,_home=native
    begin(db,session)
    db.append_messages_batch("stored",[{"role":"assistant","content":None,"message_uid":"output-uid","tool_calls":[{
        "id":"provider-call","function":{"name":"terminal","arguments":"{}"}}],
        "_tool_call_uids":{"provider-call":"long-tool-occurrence"}}])
    native_output(session,tool_uid="tool-occurrence")
    result=activate(request(db))
    assert not result["complete"] and result["reason"] == "view_changed"


@pytest.mark.parametrize('holder', ['opaque lease identity', 'owner/v2:worker:any',
                                         'pid=123:turn=external-native-turn:platform=weixin'])
def test_external_turn_recovers_from_authoritative_opaque_lease_identity(native, holder):
    db, session, _home = native
    # A previous local Turn's unpersisted output cannot stand for this Gateway Turn.
    inflight_output.start(session)
    native_output(session)
    db.append_message('stored', 'user', 'New external question')
    req = request(db)
    assert db.try_acquire_session_turn_lease('stored', holder)
    result = activate(req)
    assert result['complete'] and result['running'] and result['status'] == 'working'
    assert result['live_output_available'] is False
    assert result['state_snapshot']['events'] == []
    assert 'inflight' not in result
    db.append_message('stored', 'assistant', 'External result persisted while still running')
    result = activate(req)
    assert result['complete'] and result['running']
    assert result['windows'][0]['messages'][-1]['content'] == 'External result persisted while still running'
    db.release_session_turn_lease('stored', holder)


def test_local_turn_proof_uses_opaque_holder_equality_and_committed_source(native):
    db, session, _home = native
    begin(db, session, holder='opaque-local-lease')
    native_output(session)
    result = activate(request(db))
    assert result['complete'] and result['running']
    assert result.get('live_output_available') is not False
    assert result['state_snapshot']['events']
