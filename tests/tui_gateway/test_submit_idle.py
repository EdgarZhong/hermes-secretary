"""Real native prompt RPC/admission/SQLite/Loop with only provider returns controlled."""
import copy
import threading
import errno
from types import SimpleNamespace

import pytest

from tests.agent.test_run_agent import _mock_response
from tests.tui_gateway.test_pending_native_turn import live as live, settled
from tui_gateway import server


def rpc(method="prompt.submit_idle", **params):
    return server.handle_request({"jsonrpc": "2.0", "id": method, "method": method,
                                  "params": {"session_id": "runtime", **params}})


def provider_gate(live, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    calls = []
    def provider(kwargs):
        calls.append(kwargs)
        if len(calls) == 1:
            entered.set()
            assert release.wait(5)
        return _mock_response(content="finished", finish_reason="stop")
    monkeypatch.setattr(live.agent, "_interruptible_api_call", provider)
    return SimpleNamespace(entered=entered, release=release, calls=calls)


def wait_all(live):
    for _ in range(3):
        settled(live)


def busy_error(result):
    assert result["error"] == {"code": 4009, "message": "session busy",
                               "data": {"accepted": False, "reason": "session_busy"}}


def claim_pause(live, monkeypatch, name="first-request"):
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    original = server._lock_in_submit_turn
    def claim(*args, **kwargs):
        if threading.current_thread().name == name:
            entered.set()
            assert release.wait(5)
        return original(*args, **kwargs)
    monkeypatch.setattr(server, "_lock_in_submit_turn", claim)
    return entered, release


def start_rpc(name="first-request", method="prompt.submit_idle", **params):
    results = []
    thread = threading.Thread(target=lambda: results.append(rpc(method, **params)), name=name)
    thread.start()
    return thread, results


def join_rpc(thread, results):
    thread.join(5)
    assert not thread.is_alive() and len(results) == 1
    return results[0]


def test_idle_submit_native_row_loop_and_no_legacy_marker(live, monkeypatch):
    gate = provider_gate(live, monkeypatch)
    result = rpc(text="native @file:notes.md")
    assert result["result"]["status"] == "streaming"
    assert gate.entered.wait(5)
    rows = [r for r in live.db.get_messages("stored") if r["role"] == "user"]
    assert len(rows) == 1 and rows[0]["id"] == result["result"]["user_row_id"]
    assert "@file:notes.md" in rows[0]["content"]
    assert live.session["_idle_only_running_claim"] is True
    gate.release.set()
    wait_all(live)
    legacy = rpc("prompt.submit", text="legacy ordinary")
    assert legacy["result"]["status"] == "streaming"
    wait_all(live)
    assert "_idle_only_running_claim" not in live.session
    assert len(gate.calls) == 2


def test_already_busy_refuses_at_native_claim_without_busy_handler_or_mutation(live, monkeypatch):
    gate = provider_gate(live, monkeypatch)
    assert rpc("prompt.submit", text="legacy active")["result"]["status"] == "streaming"
    assert gate.entered.wait(5)
    assert "_idle_only_running_claim" not in live.session
    live.session["attached_images"] = ["unsent.png"]
    before = (copy.deepcopy(live.db.get_messages("stored")), copy.deepcopy(live.session["inflight_turn"]))
    live.session.update(client_surface="voice-live", voice_live_context="keep current context", voice_turn=True)
    def forbidden(*a, **k):
        raise AssertionError("idle-only must never enter native busy handler")
    monkeypatch.setattr(server, "_handle_busy_submit", forbidden)
    busy_error(rpc(text="must stay draft", truncate_before_user_ordinal=0, confirm_truncate=True))
    assert before == (live.db.get_messages("stored"), live.session["inflight_turn"])
    assert live.session["attached_images"] == ["unsent.png"]
    assert live.session["client_surface"] == "voice-live" and live.session["voice_turn"] is True
    assert live.session["voice_live_context"] == "keep current context"
    assert not live.session.get("queued_prompt") and live.agent._pending_steer is None
    gate.release.set()
    wait_all(live)


@pytest.mark.parametrize("winner", ["prompt.submit_idle", "prompt.submit"])
def test_new_request_before_claim_loses_to_other_client_without_mutation(live, monkeypatch, winner):
    gate = provider_gate(live, monkeypatch)
    entered, release = claim_pause(live, monkeypatch)
    thread, results = start_rpc(text="losing web")
    assert entered.wait(5)
    winning = rpc(winner, text="winning client")
    assert winning["result"]["status"] == "streaming" and gate.entered.wait(5)
    live.session["attached_images"] = ["new-staging.png"]
    before = copy.deepcopy(live.db.get_messages("stored")), copy.deepcopy(live.session["inflight_turn"])
    release.set()
    busy_error(join_rpc(thread, results))
    assert before == (live.db.get_messages("stored"), live.session["inflight_turn"])
    assert live.session["attached_images"] == ["new-staging.png"] and len(gate.calls) == 1
    gate.release.set()
    wait_all(live)


@pytest.mark.parametrize("mode,status", [("queue", "queued"), ("steer", "steered"), ("interrupt", "redirected")])
def test_legacy_past_idle_observation_retries_its_native_busy_policy(live, monkeypatch, mode, status):
    gate = provider_gate(live, monkeypatch)
    monkeypatch.setattr(server, "_load_busy_input_mode", lambda: mode)
    entered, release = claim_pause(live, monkeypatch)
    thread, results = start_rpc(method="prompt.submit", text="legacy after gap")
    assert entered.wait(5)
    assert rpc(text="web owns claim")["result"]["status"] == "streaming" and gate.entered.wait(5)
    first_inflight = copy.deepcopy(live.session["inflight_turn"])
    release.set()
    result = join_rpc(thread, results)
    assert result["result"]["status"] == status
    assert live.session["inflight_turn"]["user"] == first_inflight["user"]
    assert len(gate.calls) == 1
    gate.release.set()
    wait_all(live)
    assert len(gate.calls) == 2


def test_contextvar_finally_reset_preserves_later_legacy_rpc(live, monkeypatch):
    gate = provider_gate(live, monkeypatch)
    original = server._native_prompt_submit_handler
    def failed(*a, **k):
        raise RuntimeError("controlled pre-admission failure")
    monkeypatch.setattr(server, "_native_prompt_submit_handler", failed)
    with pytest.raises(RuntimeError, match="controlled pre-admission failure"):
        rpc(text="never accepted")
    assert server._idle_submit_requested() is False
    monkeypatch.setattr(server, "_native_prompt_submit_handler", original)
    assert rpc("prompt.submit", text="legacy active")["result"]["status"] == "streaming"
    assert gate.entered.wait(5)
    assert rpc("prompt.submit", text="legacy queue", queued=True)["result"]["status"] == "queued"
    assert "_idle_only_running_claim" not in live.session
    gate.release.set()
    wait_all(live)


def test_long_preflight_keeps_native_resume_history_lock_order(live, monkeypatch):
    gate = provider_gate(live, monkeypatch)
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    original = server._ensure_active_session_slot
    def slow(*a, **k):
        if threading.current_thread().name == "first-request":
            entered.set()
            assert release.wait(5)
        return original(*a, **k)
    monkeypatch.setattr(server, "_ensure_active_session_slot", slow)
    thread, results = start_rpc(text="long preflight")
    assert entered.wait(5)
    # Same native ordering as resume: resume lock before history. No outer history lock may be held here.
    with server._session_resume_lock:
        assert live.session["history_lock"].acquire(timeout=1)
        live.session["history_lock"].release()
    release.set()
    assert join_rpc(thread, results)["result"]["status"] == "streaming" and gate.entered.wait(5)
    gate.release.set()
    wait_all(live)


def test_schema_profile_errors_and_unknown_ack_are_not_safe_resend(live, monkeypatch):
    assert rpc(text="invalid fallback", queued=True)["error"]["code"] == 4000
    monkeypatch.setattr(server, "_profile_home", lambda profile: live.home / "different")
    assert rpc(text="wrong profile", profile="other")["error"]["code"] == 4003
    assert not live.db.get_messages("stored")
    gate = provider_gate(live, monkeypatch)
    # Discard the genuine ACK: existing server state proves a turn, not a reusable send op_id.
    rpc(text="lost ACK")
    assert gate.entered.wait(5)
    assert len([r for r in live.db.get_messages("stored") if r["role"] == "user"]) == 1
    assert live.session["running"] and live.session["inflight_turn"]["user"]
    busy_error(rpc(text="blind retry"))
    assert len([r for r in live.db.get_messages("stored") if r["role"] == "user"]) == 1
    gate.release.set()
    wait_all(live)


def test_rewind_native_confirmation_and_busy_never_mutate_history(live, monkeypatch):
    gate = provider_gate(live, monkeypatch)
    assert rpc(text="first")["result"]["status"] == "streaming" and gate.entered.wait(5)
    gate.release.set()
    wait_all(live)
    before = copy.deepcopy(live.db.get_messages("stored"))
    live.session["history"] = live.db.get_messages_as_conversation("stored", include_row_ids=True)
    target = next(r["id"] for r in before if r["role"] == "user")
    assert rpc(text="edited", truncate_before_row_id=target)["error"]["code"] == 4029
    assert live.db.get_messages("stored") == before
    assert rpc(text="edited", truncate_before_row_id=target, confirm_truncate=True)["error"]["code"] == 4028
    assert live.db.get_messages("stored") == before
    result = rpc(text="edited", truncate_before_row_id=target, confirm_truncate=True, confirm_empty_truncate=True)
    assert result["result"]["status"] == "streaming"
    wait_all(live)
    rows = live.db.get_messages("stored")
    assert [r["content"] for r in rows if r["role"] == "user"] == ["edited"]


def test_explicit_images_keep_foreign_staging_and_update_unique_native_row(live, monkeypatch):
    from PIL import Image
    photo = live.home / "photo.png"
    Image.new("RGB", (8, 8), (10, 20, 30)).save(photo)
    live.session["attached_images"] = ["foreign.png"]
    # Controlled external model capability; native loading/parts/persistence is untouched.
    monkeypatch.setattr("agent.image_routing.decide_image_input_mode", lambda *a, **k: "native")
    monkeypatch.setattr(live.agent, "_model_supports_vision", lambda *a, **k: True)
    gate = provider_gate(live, monkeypatch)
    result = rpc(text="picture", image_paths=[str(photo)])
    assert result["result"]["status"] == "streaming" and gate.entered.wait(5)
    assert live.session["attached_images"] == ["foreign.png"]
    assert "data:image/png;base64," in str(gate.calls[0]["messages"])
    rows = live.db.get_messages("stored")
    users = [r for r in rows if r["role"] == "user"]
    assert len(users) == 1 and users[0]["id"] == result["result"]["user_row_id"]
    uid = live.db._conn.execute("SELECT message_uid FROM messages WHERE id = ?", (users[0]["id"],)).fetchone()[0]
    assert str(photo) in str(users[0]) and uid
    gate.release.set()
    wait_all(live)


def test_native_retirement_refusal_preserves_staging_and_db(live, monkeypatch):
    from hermes_cli.backend_retirement import RetirementFence
    fence = RetirementFence()
    monkeypatch.setattr("hermes_cli.web_server_idle_proof.idle_proof", lambda: {"idle": True})
    permit = fence.prepare()
    assert permit["ok"] and fence.commit(permit["token"])["ok"]
    monkeypatch.setattr("hermes_cli.backend_retirement.retirement", fence)
    live.session["attached_images"] = ["not claimed.png"]
    before = copy.deepcopy(live.db.get_messages("stored"))
    assert rpc(text="retiring")["error"]["code"] == 5035
    assert live.db.get_messages("stored") == before and not live.session["running"]
    assert live.session["attached_images"] == ["not claimed.png"]
    assert "_idle_only_running_claim" not in live.session


def test_native_storage_failure_releases_running_without_claiming_images(live, monkeypatch):
    from hermes_state import SessionDB
    original = SessionDB.append_message
    def write(db, sid, role, content=None, *args, **kwargs):
        if role == "user" and content == "disk failure":
            raise OSError(errno.ENOSPC, "controlled full test disk")
        return original(db, sid, role, content, *args, **kwargs)
    monkeypatch.setattr(SessionDB, "append_message", write)
    live.session["attached_images"] = ["not claimed.png"]
    result = rpc(text="disk failure")
    assert result["error"]["code"] == 5070
    assert not live.session["running"] and live.session["inflight_turn"] is None
    assert live.session["attached_images"] == ["not claimed.png"] and not live.db.get_messages("stored")
    assert server._idle_submit_requested() is False


def test_images_deferred_native_build_preserves_accept_uid_and_captured_list(live, monkeypatch):
    native_vision(live, monkeypatch)
    photo = image_file(live)
    live.session["attached_images"] = ["foreign.png"]
    gate = provider_gate(live, monkeypatch)
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    ready = threading.Event()
    live.session.update(agent=None, agent_ready=ready)
    constructor_arguments = []
    def construct(sid, key, **kwargs):
        constructor_arguments.append((sid, key, kwargs))
        entered.set()
        assert release.wait(5)
        return live.agent  # controlled external constructor; real build/attach/ready machinery remains
    monkeypatch.setattr(server, "_make_agent", construct)
    monkeypatch.setattr(server, "_wire_session_agent", lambda *a, **k: False)
    monkeypatch.setattr(server, "_announce_built_agent", lambda *a, **k: None)
    monkeypatch.setattr("tui_gateway.entry.ensure_mcp_discovery_started", lambda: None)
    result = rpc(text="build first turn", image_paths=[photo.as_uri()])
    assert result["result"]["status"] == "streaming" and entered.wait(5)
    assert not ready.is_set() and live.session["agent"] is None
    row_id = result["result"]["user_row_id"]
    assert live.db.get_messages("stored")[0]["id"] == row_id
    uid = live.db._conn.execute("SELECT message_uid FROM messages WHERE id = ?", (row_id,)).fetchone()[0]
    assert constructor_arguments[0][0:2] == ("runtime", "stored")
    assert str(constructor_arguments[0][2]["session_db"].db_path).startswith(str(live.home))
    release.set()
    assert ready.wait(5) and gate.entered.wait(5)
    assert live.session["agent"] is live.agent
    assert live.session["attached_images"] == ["foreign.png"]
    assert "data:image/png;base64," in str(gate.calls[0]["messages"])
    assert str(photo) in str(live.db.get_messages("stored")[0])
    assert uid == live.db._conn.execute("SELECT message_uid FROM messages WHERE id = ?", (row_id,)).fetchone()[0]
    gate.release.set()
    wait_all(live)
    assert len(gate.calls) == 1 and len([r for r in live.db.get_messages("stored") if r["role"] == "user"]) == 1


def image_file(live, name="owned.png"):
    from PIL import Image
    photo = live.home / name
    Image.new("RGB", (8, 8), (10, 20, 30)).save(photo)
    return photo


def native_vision(live, monkeypatch):
    monkeypatch.setattr("agent.image_routing.decide_image_input_mode", lambda *a, **k: "native")
    monkeypatch.setattr(live.agent, "_model_supports_vision", lambda *a, **k: True)


def test_uploaded_images_order_duplicates_and_unique_db_row(live, monkeypatch):
    import base64
    native_vision(live, monkeypatch)
    photo = image_file(live)
    uploaded = rpc("file.attach", name="browser.png", data_url="data:image/png;base64," +
                   base64.b64encode(photo.read_bytes()).decode())["result"]
    assert uploaded["uploaded"] and live.session["attached_images"] == []
    second = image_file(live, "second.png")
    live.session["attached_images"] = ["foreign.png"]
    gate = provider_gate(live, monkeypatch)
    paths = [uploaded["path"], str(second), uploaded["path"]]
    result = rpc(text="ordered pictures", image_paths=paths)
    assert result["result"]["status"] == "streaming" and gate.entered.wait(5)
    user = next(m for m in gate.calls[0]["messages"] if m["role"] == "user")
    assert len([p for p in user["content"] if p.get("type") == "image_url"]) == 3
    rows = [r for r in live.db.get_messages("stored") if r["role"] == "user"]
    assert len(rows) == 1 and rows[0]["id"] == result["result"]["user_row_id"]
    assert str(rows[0]["content"]).index(uploaded["path"]) < str(rows[0]["content"]).index(str(second))
    assert live.session["attached_images"] == ["foreign.png"]
    gate.release.set()
    wait_all(live)


@pytest.mark.parametrize("explicit", [False, True])
def test_images_late_legacy_attach_after_detach_cannot_leak_into_idle_send(live, monkeypatch, explicit):
    import asyncio
    import cli
    from tui_gateway.transport import bind_transport, reset_transport
    from tui_gateway.ws import WSTransport
    loop = asyncio.new_event_loop()
    old_ws, new_ws = WSTransport(None, loop, peer="old"), WSTransport(None, loop, peer="new")
    photo = image_file(live)
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)
    original = cli._resolve_attachment_path
    def resolve(raw):
        if threading.current_thread().name == "old-ws":
            entered.set()
            assert release.wait(5)
        return original(raw)
    monkeypatch.setattr(cli, "_resolve_attachment_path", resolve)
    results = []
    def old_attach():
        token = bind_transport(old_ws)
        try:
            results.append(rpc("image.attach", path=str(photo)))
        finally:
            reset_transport(token)
    thread = threading.Thread(target=old_attach, name="old-ws")
    thread.start()
    assert entered.wait(5)
    old_ws.close()
    token = bind_transport(new_ws)
    try:
        assert rpc("image.detach", path=str(photo))["result"]["detached"] is False
    finally:
        reset_transport(token)
    release.set()
    assert join_rpc(thread, results)["result"]["attached"] is True
    assert live.session["attached_images"] == [str(photo)]
    gate = provider_gate(live, monkeypatch)
    token = bind_transport(new_ws)
    try:
        result = rpc(text="new socket owns no image", **({"image_paths": []} if explicit else {}))
    finally:
        reset_transport(token)
    assert result["result"]["status"] == "streaming" and gate.entered.wait(5)
    assert "image_url" not in str(gate.calls[0]["messages"]) and str(photo) not in str(gate.calls[0]["messages"])
    assert live.session["attached_images"] == [str(photo)]
    assert old_ws.closed and not new_ws.closed
    assert new_ws in live.session["viewers"]
    gate.release.set()
    wait_all(live)
    new_ws.close()
    loop.close()


@pytest.mark.parametrize("kind,code", [("null", 4000), ("scalar", 4000), ("item", 4000), ("blank", 4015), ("missing", 4016),
                                       ("extension", 4016), ("read", 5027)])
def test_images_validation_precedes_claim_and_confirmed_rewind(live, monkeypatch, kind, code):
    from pathlib import Path
    gate = provider_gate(live, monkeypatch)
    assert rpc(text="original")["result"]["status"] == "streaming" and gate.entered.wait(5)
    gate.release.set()
    wait_all(live)
    before = copy.deepcopy(live.db.get_messages("stored"))
    live.session["history"] = live.db.get_messages_as_conversation("stored", include_row_ids=True)
    target = next(r["id"] for r in before if r["role"] == "user")
    photo = image_file(live)
    unsupported = live.home / "not-image.txt"
    unsupported.write_text("text")
    paths = {"null": None, "scalar": str(photo), "item": [1], "blank": [" "], "missing": [str(live.home / "missing.png")],
             "extension": [str(unsupported)], "read": [str(photo)]}[kind]
    if kind == "read":
        original = Path.open
        def denied(path, *a, **k):
            if path == photo and a == ("rb",):
                raise PermissionError("controlled unreadable image")
            return original(path, *a, **k)
        monkeypatch.setattr(Path, "open", denied)
    live.session["attached_images"] = ["foreign.png"]
    history = copy.deepcopy(live.session["history"])
    result = rpc(text="invalid rewrite", image_paths=paths, truncate_before_row_id=target,
                 confirm_truncate=True, confirm_empty_truncate=True)
    assert result["error"]["code"] == code
    assert live.db.get_messages("stored") == before and live.session["history"] == history
    assert live.session["attached_images"] == ["foreign.png"] and not live.session["running"]


@pytest.mark.parametrize("failed", [False, True])
def test_images_compute_host_frame_and_native_inline_fallback(live, monkeypatch, failed):
    native_vision(live, monkeypatch)
    photo = image_file(live)
    live.session["attached_images"] = ["foreign.png"]
    gate = provider_gate(live, monkeypatch)
    frames = []
    class Supervisor:
        def submit_turn(self, frame, on_complete):
            frames.append(frame)
            if failed:
                on_complete({"reason": "send_failed"})
                raise OSError("controlled pipe failure")
    monkeypatch.setattr(server, "_session_uses_compute_host", lambda *a, **k: True)
    monkeypatch.setattr(server, "_get_compute_host_supervisor", lambda *a, **k: Supervisor())
    result = rpc(text="isolated images", image_paths=[str(photo)])
    assert result["result"]["status"] == "streaming"
    assert frames[0]["attached_images"] == [str(photo)] and frames[0]["profile_home"] == str(live.home)
    assert live.session["attached_images"] == ["foreign.png"]
    if failed:
        assert gate.entered.wait(5) and "data:image/png;base64," in str(gate.calls[0]["messages"])
        rows = [r for r in live.db.get_messages("stored") if r["role"] == "user"]
        assert len(rows) == 1 and str(photo) in str(rows[0])
        gate.release.set()
        wait_all(live)
    else:
        assert result["result"]["turn_isolation"] is True and not gate.calls
        # Controlled supervisor performs no child execution; do not claim child DB/Loop evidence.
        live.session["running"] = False


def test_images_legacy_submit_still_consumes_shared_staging(live, monkeypatch):
    native_vision(live, monkeypatch)
    photo = image_file(live)
    live.session["attached_images"] = [str(photo)]
    gate = provider_gate(live, monkeypatch)
    assert rpc("prompt.submit", text="legacy picture")["result"]["status"] == "streaming"
    assert gate.entered.wait(5) and live.session["attached_images"] == []
    assert "data:image/png;base64," in str(gate.calls[0]["messages"])
    gate.release.set()
    wait_all(live)


def test_images_rewind_two_confirmations_then_update_single_durable_row(live, monkeypatch):
    native_vision(live, monkeypatch)
    gate = provider_gate(live, monkeypatch)
    assert rpc(text="original")["result"]["status"] == "streaming" and gate.entered.wait(5)
    gate.release.set()
    wait_all(live)
    before = copy.deepcopy(live.db.get_messages("stored"))
    target = next(r["id"] for r in before if r["role"] == "user")
    live.session["history"] = live.db.get_messages_as_conversation("stored", include_row_ids=True)
    photo = image_file(live)
    live.session["attached_images"] = ["foreign.png"]
    params = dict(text="edited image", image_paths=[str(photo)], truncate_before_row_id=target)
    assert rpc(**params)["error"]["code"] == 4029
    assert rpc(**params, confirm_truncate=True)["error"]["code"] == 4028
    assert live.db.get_messages("stored") == before
    result = rpc(**params, confirm_truncate=True, confirm_empty_truncate=True)
    assert result["result"]["status"] == "streaming"
    wait_all(live)
    users = [r for r in live.db.get_messages("stored") if r["role"] == "user"]
    assert len(users) == 1 and users[0]["id"] == result["result"]["user_row_id"] and str(photo) in str(users[0])
    assert live.session["attached_images"] == ["foreign.png"]
    assert "data:image/png;base64," in str(gate.calls[-1]["messages"])


def test_images_only_send_persists_one_native_user_row(live, monkeypatch):
    native_vision(live, monkeypatch)
    gate = provider_gate(live, monkeypatch)
    photo = image_file(live)
    live.session["attached_images"] = ["foreign.png"]
    assert rpc(image_paths=[str(photo)])["result"]["status"] == "streaming" and gate.entered.wait(5)
    users = [r for r in live.db.get_messages("stored") if r["role"] == "user"]
    assert len(users) == 1 and str(photo) in str(users[0])
    assert live.session["attached_images"] == ["foreign.png"]
    gate.release.set()
    wait_all(live)


def test_images_busy_refusal_preserves_list_staging_and_current_native_row(live, monkeypatch):
    gate = provider_gate(live, monkeypatch)
    assert rpc(text="other client active")["result"]["status"] == "streaming" and gate.entered.wait(5)
    photo = image_file(live)
    live.session["attached_images"] = ["other client draft.png"]
    before = copy.deepcopy(live.db.get_messages("stored")), copy.deepcopy(live.session["inflight_turn"])
    busy_error(rpc(text="image draft must survive", image_paths=[str(photo)]))
    assert before == (live.db.get_messages("stored"), live.session["inflight_turn"])
    assert photo.is_file() and live.session["attached_images"] == ["other client draft.png"]
    assert len(gate.calls) == 1 and not live.session.get("queued_prompt")
    gate.release.set()
    wait_all(live)
