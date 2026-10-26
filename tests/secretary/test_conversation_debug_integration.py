"""Formal debug RPCs with real native Agents, SQLite and loopback model HTTP.

Only auxiliary metadata/title lookups are disabled. Recovery runner, tool
dispatch, leases, Snapshot commit and Framework publication remain native.
"""

from copy import deepcopy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import socket
import threading
import time
from types import SimpleNamespace

import pytest
import hermes_yaml as yaml

from hermes_state import SessionDB


@pytest.fixture
def model_endpoint():
    endpoint = SimpleNamespace(requests=[], replies=[], finish_responses=[], entered=threading.Event(),
                               release=threading.Event(), pause=False)

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            endpoint.requests.append({"path": self.path, "body": payload,
                                      "authorization": self.headers.get("Authorization")})
            if endpoint.pause and len(endpoint.requests) == 1:
                endpoint.entered.set()
                if not endpoint.release.wait(20):
                    self.send_error(504)
                    return
            message = endpoint.replies.pop(0)
            if any(call.get("function", {}).get("name") == "finish_noting"
                   for call in message.get("tool_calls", [])):
                endpoint.finish_responses.append(len(endpoint.requests))
            body = json.dumps({"id": "fixture-completion", "object": "chat.completion",
                               "created": int(time.time()), "model": "deepseek-chat",
                               "choices": [{"index": 0, "message": message,
                                            "finish_reason": "tool_calls" if message.get("tool_calls") else "stop"}],
                               "usage": {"prompt_tokens": 50, "completion_tokens": 10, "total_tokens": 60}}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *_args):
            pass

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    worker = threading.Thread(target=http.serve_forever, daemon=True)
    worker.start()
    endpoint.url = f"http://127.0.0.1:{http.server_port}/v1"
    try:
        yield endpoint
    finally:
        endpoint.release.set()
        http.shutdown()
        worker.join(timeout=3)
        http.server_close()


@pytest.fixture
def debug_runtime(tmp_path, monkeypatch, model_endpoint):
    from hermes_cli import profiles
    from tui_gateway import server

    root = tmp_path / "hermes"
    target = root / "profiles" / "target"
    target.mkdir(parents=True)
    cwd = tmp_path / "workspace"
    cwd.mkdir()
    assert not cwd.is_relative_to(Path(__file__).resolve().parents[2])
    for home, key in ((root, "fixture-launch-key"), (target, "fixture-target-key")):
        (home / "logs").mkdir(exist_ok=True)
        (home / ".env").write_text(f"DEEPSEEK_API_KEY={key}\n", encoding="utf-8")
        (home / "config.yaml").write_text(yaml.safe_dump({
            "model": {"default": "deepseek-chat", "provider": "deepseek", "base_url": model_endpoint.url,
                      "api_mode": "chat_completions", "streaming": False, "context_length": 262144},
            "compression": {"enabled": True, "threshold": .8, "idle_compact_after_seconds": 0},
            "noting": {"enabled": True, "idle": {"enabled": False}},
            "scheduler": {"enabled": True}, "agent": {"disabled_toolsets": ["vision"]},
            "platform_toolsets": {"cli": []}, "terminal": {"cwd": str(cwd)},
            "memory": {"memory_enabled": False, "user_profile_enabled": False},
        }), encoding="utf-8")
    monkeypatch.setenv("HERMES_HOME", str(root))
    monkeypatch.setenv("HERMES_IGNORE_RULES", "1")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "fixture-launch-ambient-key")
    monkeypatch.setenv("HERMES_SESSION_ID", "integration-caller-main")
    monkeypatch.setattr(profiles, "_get_default_hermes_home", lambda: root)
    monkeypatch.setattr(server, "_hermes_home", root)
    monkeypatch.setattr("run_agent._hermes_home", root)
    monkeypatch.setattr("agent.model_metadata.fetch_model_metadata", lambda *_a, **_kw: {})
    monkeypatch.setattr("agent.title_generator.maybe_auto_title", lambda *_a, **_kw: None)
    original_connect = socket.socket.connect

    def local_only(sock, address):
        if isinstance(address, tuple) and address[0] not in {"127.0.0.1", "::1"}:
            raise AssertionError(f"Unexpected external network request: {address[0]}")
        return original_connect(sock, address)

    monkeypatch.setattr(socket.socket, "connect", local_only)
    stores = {"launch": SessionDB(root / "state.db"), "target": SessionDB(target / "state.db")}
    for name, db in stores.items():
        db.create_session("parent", source="cli", model="deepseek-chat", cwd=str(cwd),
                          system_prompt=f"{name} original root",
                          model_config={"provider": "deepseek", "base_url": model_endpoint.url,
                                        "api_mode": "chat_completions"})
    value = SimpleNamespace(server=server, stores=stores, home=target, endpoint=model_endpoint,
                            cwd=cwd, ref=stores["target"].resolve_conversation_ref("parent"))
    try:
        yield value
    finally:
        from secretary.noting_recovery import _WORKERS
        model_endpoint.release.set()
        for worker in list(_WORKERS.values()):
            worker.join(timeout=5)
        for db in stores.values():
            db.close()


def _rpc(runtime, method, **params):
    response = runtime.server.handle_request({"jsonrpc": "2.0", "id": 701, "method": method,
                                              "params": {"profile": "target", **params}})
    assert "error" not in response, response
    return response["result"]


def _schedule(db, ref):
    from secretary.scheduler_table import apply_schedule_action_conn
    db._execute_write(lambda conn: apply_schedule_action_conn(conn, ref, {
        "action": "create", "content": "Preserve existing schedule", "schedule": "every 2h",
        "delivery_mode": "instant"}, now=1792200000))


def _rows(db, table, where="", args=()):
    with db._read_ctx() as conn:
        return [tuple(row) for row in conn.execute(f"SELECT * FROM {table} {where} ORDER BY rowid", args)]


def _tool(name, args, call_id):
    return {"role": "assistant", "content": None, "tool_calls": [
        {"id": call_id, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]}


def test_clear_rpc_waits_for_normal_native_turn_and_rebuilds_full_surface(debug_runtime):
    runtime = debug_runtime
    db = runtime.stores["target"]
    old_tools = [{"type": "function", "function": {"name": "obsolete_pin", "description": "old schema",
                  "parameters": {"type": "object", "properties": {}}}},
                 {"type": "function", "function": {"name": "scheduler", "description": "obsolete scheduler schema",
                  "parameters": {"type": "object", "properties": {}}}}]
    db.update_session_tool_names("parent", {"version": "old", "tools": old_tools})
    db.append_message("parent", "user", "Retain prior history", message_uid="prior")
    _schedule(db, runtime.ref)
    messages = _rows(db, "messages")
    schedules = _rows(db, "secretary_schedule_registry")
    launch = runtime.stores["launch"].get_session("parent")
    with runtime.server._session_profile_runtime_scope({"profile_home": str(runtime.home)}):
        agent = runtime.server._make_agent("integration-main", "parent", session_db=db,
                                           platform_override="cli", cwd_override=str(runtime.cwd))
        agent._cached_system_prompt = "target original root"
        agent.tools = deepcopy(old_tools)
        agent.valid_tool_names = {"obsolete_pin", "scheduler"}
        agent.save_trajectories = False
        try:
            result = _rpc(runtime, "conversation.context_cache_clear", conversation_ref=runtime.ref)
            assert result["status"] == "cleared"
            assert not runtime.endpoint.requests
            assert agent._cached_system_prompt == "target original root"
            assert db.get_session("parent")["system_prompt"] is None
            assert db.get_session("parent")["tool_names"] is None
            assert _rows(db, "messages") == messages
            assert _rows(db, "secretary_schedule_registry") == schedules
            assert _rpc(runtime, "conversation.context_cache_clear", conversation_ref=runtime.ref)["status"] == "already_clear"
            runtime.endpoint.replies = [{"role": "assistant", "content": "Normal turn completed"}]
            outcome = agent.run_conversation(user_message="Next normal active turn",
                                             conversation_history=db.get_messages_as_conversation("parent"),
                                             title_user_message="")
            assert outcome["completed"] is True, outcome
            assert len(runtime.endpoint.requests) == 1
            wire = runtime.endpoint.requests[0]
            assert wire["authorization"] == "Bearer fixture-target-key"
            names = {tool["function"]["name"] for tool in wire["body"]["tools"]}
            assert {"scheduler", "notebook_show", "conversation_history"} <= names
            assert names.isdisjoint({"obsolete_pin", "vision_analyze"})
            scheduler = next(tool["function"] for tool in wire["body"]["tools"]
                             if tool["function"]["name"] == "scheduler")
            assert scheduler["description"] != "obsolete scheduler schema"
            assert "action" in scheduler["parameters"]["properties"]
            persisted = db.get_session("parent")
            assert persisted["system_prompt"] != "target original root"
            assert "obsolete_pin" not in {tool["function"]["name"] for tool in json.loads(persisted["tool_names"])["tools"]}
            assert _rows(db, "messages")[:len(messages)] == messages
            assert _rows(db, "secretary_schedule_registry") == schedules
            assert runtime.stores["launch"].get_session("parent") == launch
        finally:
            agent._end_session_on_close = False
            agent.close()


def _failed_child(runtime):
    from agent.message_metadata import build_noting_task_wrapper
    from secretary.notebook_store import NotebookStore
    from secretary.noting_tools import noting_tool_control_message, noting_tool_schemas

    db, ref = runtime.stores["target"], runtime.ref
    db.append_message("parent", "user", "Pre-compaction source", message_uid="pre")
    db.archive_and_compact("parent", [{"role": "user", "content": "Admitted compacted boundary",
                                     "_compressed_summary": True, "message_uid": "boundary"}])
    db.append_message("parent", "user", "Frozen local evidence", message_uid="evidence")
    db.append_message("parent", "assistant", "Frozen local response", message_uid="anchor")
    tools = [{"type": "function", "function": {"name": "terminal", "description": "Frozen tool schema",
              "parameters": {"type": "object", "properties": {"command": {"type": "string"}}}}}]
    tools.extend({"type": "function", "function": schema} for schema in noting_tool_schemas())
    store = NotebookStore(db, ref, anchor_message_uid="anchor", trigger_type="manual")
    initial = store.create("matter", {"description": "Initial responsibility", "completion_condition": "Done"},
                           source_message_identities=[{"conversation_ref": ref, "message_uid": "evidence"}])["entry"]
    base = store.commit(termination={"type": "finish_noting", "reason": "Existing baseline"})
    admission = db.noting_admit(ref, "anchor", kind="manual")
    working = NotebookStore(db, ref, anchor_message_uid="anchor", trigger_type="manual", task_id=str(admission))
    control = noting_tool_control_message(notebook_state=working.show(), conversation_ref=ref,
                                          coverage=working.coverage, db=db)
    maintained = working.update(initial["entry_id"], {"fields": {"description": "Successfully maintained before failure"},
                                                       "source_message_uids": ["evidence"]})
    db.create_session("failed-child", source="subagent", parent_session_id="parent", model="deepseek-chat",
                      system_prompt="Frozen failed child root", cwd=str(runtime.cwd),
                      model_config={"_delegate_from": "parent", "provider": "deepseek",
                                    "base_url": runtime.endpoint.url, "api_mode": "chat_completions"})
    db.update_session_tool_names("failed-child", {"version": "old", "tools": tools})
    db.append_message("failed-child", "user", build_noting_task_wrapper(control))
    call = _tool("notebook_update", {"entry_id": initial["entry_id"],
                                      "fields": {"description": "Successfully maintained before failure"},
                                      "source_message_uids": ["evidence"]}, "prior-update")
    db.append_message("failed-child", "assistant", "", tool_calls=call["tool_calls"])
    from secretary.notebook_render import model_notebook_data, readable_notebook_entry
    receipt = {**maintained, "entry": readable_notebook_entry(
        maintained["entry"], db=db, conversation_ref=ref, state=working.snapshot_state())}
    db.append_message("failed-child", "tool", json.dumps(model_notebook_data(receipt)),
                      tool_call_id="prior-update", tool_name="notebook_update")
    db.noting_child_register(admission, child_session_id="failed-child", profile="target")
    db.noting_child_finish(admission, status="failed")
    db.end_session("failed-child", "fixture_interrupted")
    return admission, tools, maintained["entry"], base


def test_recovery_rpc_native_http_commit_preserves_failed_records_and_appends_current_tail(debug_runtime):
    runtime = debug_runtime
    db = runtime.stores["target"]
    admission, tools, entry, base = _failed_child(runtime)
    old_child = db.get_session("failed-child")
    old_messages = _rows(db, "messages", "WHERE session_id=?", ("failed-child",))
    registry = db.noting_child(admission)
    db.update_system_prompt("parent", "Current root must not replace historical root")
    db.update_session_tool_names("parent", {"version": "new", "tools": []})
    db.append_message("parent", "user", "Current tail before recovery", message_uid="current")
    _schedule(db, runtime.ref)
    schedules = _rows(db, "secretary_schedule_registry")
    before = _rows(db, "messages", "WHERE session_id=?", ("parent",))
    launch = runtime.stores["launch"].get_session("parent")
    endpoint = runtime.endpoint
    endpoint.pause = True
    endpoint.replies = [_tool("notebook_show", {}, "recovered-show"),
                        _tool("finish_noting", {"reason": "Recovered legal working view"}, "recovered-finish"),
                        {"role": "assistant", "content": "Recovery complete"}]
    params = {"conversation_ref": runtime.ref, "failed_child_session_id": "failed-child", "request_id": "integration-r1"}
    environment = dict(os.environ)
    ack = _rpc(runtime, "secretary.noting_recover", **params)
    assert endpoint.entered.wait(15), _rpc(runtime, "secretary.noting_recovery_state", **params)
    assert db.try_acquire_session_turn_lease("parent", "integration-late-main")
    try:
        db.append_message("parent", "assistant", "Main wrote while recovery model was running", message_uid="late-main",
                          turn_lease_holder="integration-late-main")
    finally:
        db.release_session_turn_lease("parent", "integration-late-main")
    late = _rows(db, "messages", "WHERE session_id=?", ("parent",))[-1]
    endpoint.release.set()
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        state = _rpc(runtime, "secretary.noting_recovery_state", **params)
        if state["status"] not in {"queued", "running"}:
            break
        time.sleep(.02)
    assert state["status"] == "completed" and state["committed"], state
    from secretary.noting_recovery import _WORKERS
    worker = _WORKERS.get((str(db.db_path.resolve()), state["operation_id"]))
    if worker is not None:
        worker.join(timeout=3)
        assert not worker.is_alive()
    assert state["operation_id"] == ack["operation_id"]
    assert endpoint.finish_responses == [len(endpoint.requests)]
    assert all(request["authorization"] == "Bearer fixture-target-key" for request in endpoint.requests)
    first = endpoint.requests[0]["body"]
    assert first["tools"] == tools
    assert first["messages"][0]["content"] == "Frozen failed child root"
    wire_text = json.dumps(first["messages"])
    assert "Admitted compacted boundary" in wire_text and "Frozen local evidence" in wire_text
    assert "Successfully maintained before failure" in wire_text
    assert "Current tail before recovery" not in wire_text and "Current root must" not in wire_text
    shown = [json.loads(message["content"]) for message in endpoint.requests[1]["body"]["messages"]
             if message.get("role") == "tool" and message.get("tool_call_id") == "recovered-show"]
    assert shown[0]["payload"]["work"][0]["fields"]["description"] == entry["fields"]["description"]
    snapshot = db.notebook_current(runtime.ref)
    assert snapshot["snapshot_id"] == state["snapshot_id"] != base["snapshot_id"]
    assert snapshot["payload"]["work"][0] == entry
    after = _rows(db, "messages", "WHERE session_id=?", ("parent",))
    assert after[:len(before)] == before and after[-2] == late
    messages = db.get_messages_as_conversation("parent")
    assert messages[-1]["display_metadata"]["noting_snapshot_id"] == state["snapshot_id"]
    assert db.get_session("failed-child") == old_child
    assert _rows(db, "messages", "WHERE session_id=?", ("failed-child",)) == old_messages
    assert db.noting_child(admission) == registry
    assert _rows(db, "secretary_schedule_registry") == schedules
    assert runtime.stores["launch"].get_session("parent") == launch
    assert dict(os.environ) == environment
    assert _rpc(runtime, "secretary.noting_recover", **params) == state
    assert endpoint.finish_responses == [len(endpoint.requests)]
    assert not _rows(db, "session_turn_leases")
    assert db.get_session(state["child_session_id"])["end_reason"]


def test_recovery_preserves_existing_native_main_and_uses_its_framework_queue(debug_runtime):
    from secretary.framework_messages import mark_framework_turn
    from secretary.noting_scope import _main_runtimes, _runtime_key

    runtime = debug_runtime
    db = runtime.stores["target"]
    _failed_child(runtime)
    with runtime.server._session_profile_runtime_scope({"profile_home": str(runtime.home)}):
        live = runtime.server._make_agent("integration-existing-main", "parent", session_db=db,
                                          platform_override="cli", cwd_override=str(runtime.cwd))
        live._session_messages = db.get_messages_as_conversation("parent", include_row_ids=True)
        assert _main_runtimes.get(_runtime_key(db, runtime.ref)) is live
        mark_framework_turn(live, running=True)
        before = _rows(db, "messages", "WHERE session_id=?", ("parent",))
        endpoint = runtime.endpoint
        endpoint.pause = True
        endpoint.replies = [_tool("finish_noting", {"reason": "Retained recovered work"}, "live-finish"),
                            {"role": "assistant", "content": "Recovery complete"}]
        params = {"conversation_ref": runtime.ref, "failed_child_session_id": "failed-child", "request_id": "live-owner-r1"}
        try:
            _rpc(runtime, "secretary.noting_recover", **params)
            assert endpoint.entered.wait(15), _rpc(runtime, "secretary.noting_recovery_state", **params)
            assert _main_runtimes.get(_runtime_key(db, runtime.ref)) is live
            endpoint.release.set()
            deadline = time.monotonic() + 20
            while time.monotonic() < deadline:
                state = _rpc(runtime, "secretary.noting_recovery_state", **params)
                if state["status"] not in {"queued", "running"}:
                    break
                time.sleep(.02)
            assert state["status"] == "completed" and state["committed"], state
            assert _rows(db, "messages", "WHERE session_id=?", ("parent",)) == before
            assert len(live._secretary_framework_messages) == 1
            mark_framework_turn(live, running=False)
            after = db.get_messages_as_conversation("parent")
            assert after[-1]["display_metadata"]["noting_snapshot_id"] == state["snapshot_id"]
            assert _rows(db, "messages", "WHERE session_id=?", ("parent",))[:len(before)] == before
            assert endpoint.finish_responses == [len(endpoint.requests)]
        finally:
            endpoint.release.set()
            mark_framework_turn(live, running=False)
            live._end_session_on_close = False
            live.close()
