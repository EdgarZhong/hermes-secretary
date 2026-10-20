"""P1-06: real idle admission/SQLite/worker/native Loop, controlled provider only.

Ports the original mobile investigation's image receipt reproduction with the
fixed expectations; no production data, external provider or UI automation.
"""
import base64
import errno
import threading
from contextlib import contextmanager

import pytest

from agent.context_references import format_reference_value
from hermes_state import SessionDB
from tests.tui_gateway.test_pending_native_turn import live as live
from tests.tui_gateway.test_submit_idle import image_file, native_vision, provider_gate, rpc, wait_all
from tui_gateway import inflight_output, server

_native_emit = server._emit


@pytest.fixture(autouse=True)
def outside_repo_profile(live, monkeypatch):
    # Profile cwd must not load this checkout's AGENTS into any native tooling.
    config = live.home / "config.yaml"
    config.write_text(config.read_text() + f"terminal:\n  cwd: {live.home}\n")
    monkeypatch.chdir(live.home)


def pause_worker(live, monkeypatch):
    original = server._run_after_agent_ready
    entered, release = threading.Event(), threading.Event()
    live.releases.append(release)

    def delayed(*args, **kwargs):
        entered.set()
        assert release.wait(5)
        return original(*args, **kwargs)

    monkeypatch.setattr(server, "_run_after_agent_ready", delayed)
    return entered, release


def users(live, owner="stored"):
    return [row for row in live.db.get_messages(owner) if row["role"] == "user"]


def durable_user_facts(rows):
    return [{key: row[key] for key in ("id", "session_id", "role", "content", "message_uid", "timestamp", "active")}
            for row in rows]


@pytest.mark.parametrize("mode", ["native", "text"])
@pytest.mark.parametrize("caption", ["", "caption", " \t ", "\x1b[200~line caption\x1b[201~"])
def test_receipt_before_worker_then_same_row_uid_and_original_model_input(live, monkeypatch, mode, caption):
    from hermes_cli.input_sanitize import sanitize_user_prompt_text

    photo = image_file(live, "photo with spaces.png")
    other = image_file(live, "second.png")
    # Canonical resolution, order and repeated occurrence must survive the handoff.
    alias = live.home / "alias.png"
    alias.symlink_to(photo)
    paths = [str(alias), str(other), str(photo)]
    canonical = [str(photo.resolve()), str(other.resolve()), str(photo.resolve())]
    live.session["attached_images"] = ["another client draft.png"]
    if mode == "native":
        native_vision(live, monkeypatch)
    else:
        monkeypatch.setattr("agent.image_routing.decide_image_input_mode", lambda *a, **k: "text")
    encoded = []
    original_encode = base64.b64encode

    def encode(value, *args, **kwargs):
        encoded.append(len(value))
        return original_encode(value, *args, **kwargs)

    monkeypatch.setattr(base64, "b64encode", encode)
    entered, release = pause_worker(live, monkeypatch)
    gate = provider_gate(live, monkeypatch)
    updates = []
    original_update = SessionDB.set_user_message_content

    def update(db, owner, row_id, content, **kwargs):
        updates.append((str(db.db_path), owner, row_id, kwargs))
        return original_update(db, owner, row_id, content, **kwargs)

    monkeypatch.setattr(SessionDB, "set_user_message_content", update)
    result = rpc(text=caption, image_paths=paths)["result"]
    assert entered.wait(5)
    clean = sanitize_user_prompt_text(caption)
    refs = "\n".join(f"@image:{format_reference_value(path)}" for path in canonical)
    expected = f"{clean}\n{refs}" if clean else refs
    before = users(live)
    assert len(before) == 1 and before[0]["content"] == expected
    row_id, uid = before[0]["id"], before[0]["message_uid"]
    receipt = result["accepted_user"]
    assert receipt == {"stored_session_id": "stored", "message": {
        "role": "user", "content": expected, "row_id": row_id,
        "message_uid": uid, "timestamp": before[0]["timestamp"]}}
    assert result["user_row_id"] == row_id
    assert [payload for kind, _, payload in live.frames if kind == "message.user_committed"] == [receipt]
    assert not any(kind == "message.start" for kind, _, _ in live.frames)
    assert not encoded and not gate.calls
    staged = live.session["_submit_user_row"]
    assert staged["_submit_input_text"] == clean and staged["_submit_image_paths"] == tuple(canonical)
    assert staged["_submit_row_db_path"] == str((live.home / "state.db").resolve())
    assert staged["_submit_row_session_id"] == "stored"
    release.set()
    assert gate.entered.wait(5)
    during = users(live)
    assert [(row["id"], row["message_uid"]) for row in during] == [(row_id, uid)]
    assert "_submit_user_row" not in live.session
    # Native early flush consumes pending_cli, but keeps the adopted dict's marker.
    assert staged["_row_id"] == row_id and staged["message_uid"] == uid and staged["_db_persisted"]
    model_user = gate.calls[0]["messages"][-1]["content"]
    assert "@image:" not in str(model_user)
    assert "_submit_" not in str(gate.calls[0]["messages"]) and "<timestamp>" in str(model_user)
    if mode == "native":
        assert isinstance(model_user, list)
        images = [part for part in model_user if part["type"] == "image_url"]
        assert len(images) == 3 and all("data:image/png;base64," in str(part) for part in images)
        assert "Examine it with the vision_analyze" not in str(model_user)
    else:
        assert isinstance(model_user, str) and "Examine it with the vision_analyze tool" in model_user
        assert "data:image/" not in model_user and not encoded
        assert during[0]["api_content"] == model_user
    assert updates == [(str(live.home / "state.db"), "stored", row_id, {"expected_message_uid": uid})]
    if clean.strip():
        model_text = "\n".join(part.get("text", "") for part in model_user) if isinstance(model_user, list) else model_user
        assert clean.strip() in model_text
    gate.release.set()
    wait_all(live)
    after = users(live)
    assert [(row["id"], row["message_uid"]) for row in after] == [(row_id, uid)]
    assert live.session["attached_images"] == ["another client draft.png"]
    assert [kind for kind, _, _ in live.frames].count("message.user_committed") == 1
    complete = [payload for kind, _, payload in live.frames if kind == "message.complete"][-1]
    assert complete["persisted_turn"]["user_row_id"] == row_id
    assert live.db.get_messages_as_conversation("stored", include_row_ids=True)[0]["_row_id"] == row_id


@pytest.mark.parametrize("failure", ["disk_full", "write_error"])
def test_image_write_failure_has_no_forged_receipt_or_event(live, monkeypatch, failure):
    photo = image_file(live)
    original = SessionDB.append_message

    def append(db, owner, role, *args, **kwargs):
        if role == "user":
            if failure == "disk_full":
                raise OSError(errno.ENOSPC, "controlled full disk")
            raise OSError("controlled write failure")
        return original(db, owner, role, *args, **kwargs)

    monkeypatch.setattr(SessionDB, "append_message", append)
    monkeypatch.setattr(server, "_run_after_agent_ready", lambda *a, **k: None)
    result = rpc(image_paths=[str(photo)])
    wait_all(live)
    assert "accepted_user" not in result.get("result", {})
    assert users(live) == []
    assert not any(kind == "message.user_committed" for kind, _, _ in live.frames)
    if failure == "disk_full":
        assert result["error"]["code"] == 5070 and not live.session["running"]


@pytest.mark.parametrize("failure", ["build", "cancel"])
def test_durable_image_survives_worker_build_failure_or_cancel_without_resend(live, monkeypatch, failure):
    photo = image_file(live)
    entered, release = pause_worker(live, monkeypatch)
    gate = provider_gate(live, monkeypatch)
    result = rpc(image_paths=[str(photo)])["result"]
    assert entered.wait(5)
    receipt = result["accepted_user"]
    before = users(live)
    if failure == "build":
        monkeypatch.setattr(server, "_wait_agent_for_prompt", lambda *a: {"error": {"message": "controlled build failed"}})
    else:
        cancelled = rpc("session.interrupt")
        assert "result" in cancelled
    release.set()
    wait_all(live)
    assert durable_user_facts(users(live)) == durable_user_facts(before)
    assert not live.session["running"] and not gate.calls
    assert not live.session.get("queued_prompt")
    assert [payload for kind, _, payload in live.frames if kind == "message.user_committed"] == [receipt]
    if failure == "build":
        assert any(kind == "message.complete" and payload.get("status") == "error" for kind, _, payload in live.frames)
        assert users(live)[0]["display_metadata"]["turn_terminal"]["status"] == "error"
    else:
        assert any(kind in {"error", "session.interrupted"} for kind, _, _ in live.frames)


@pytest.mark.parametrize("failure", ["exception", "zero_rows"])
def test_image_adoption_update_failure_ends_turn_without_second_user_row(live, monkeypatch, failure):
    native_vision(live, monkeypatch)
    photo = image_file(live)
    entered, release = pause_worker(live, monkeypatch)
    gate = provider_gate(live, monkeypatch)
    result = rpc(image_paths=[str(photo)])["result"]
    assert entered.wait(5)
    before = users(live)

    def update(*args, **kwargs):
        if failure == "exception":
            raise OSError("controlled row update failure")
        return 0

    monkeypatch.setattr(SessionDB, "set_user_message_content", update)
    release.set()
    wait_all(live)
    assert durable_user_facts(users(live)) == durable_user_facts(before)
    assert not gate.calls and not live.session["running"]
    assert users(live)[0]["display_metadata"]["turn_terminal"]["status"] == "error"
    assert [payload for kind, _, payload in live.frames if kind == "message.user_committed"] == [result["accepted_user"]]
    assert any(kind == "message.complete" and payload.get("status") == "error" for kind, _, payload in live.frames)


@pytest.mark.parametrize("store", ["unavailable", "different_database"])
@pytest.mark.parametrize("mode", ["native", "text"])
def test_image_adoption_does_not_switch_away_from_accepted_store(live, monkeypatch, store, mode):
    if mode == "native":
        native_vision(live, monkeypatch)
    else:
        monkeypatch.setattr("agent.image_routing.decide_image_input_mode", lambda *a, **k: "text")
    photo = image_file(live)
    entered, release = pause_worker(live, monkeypatch)
    gate = provider_gate(live, monkeypatch)
    gate.release.set()  # A broken bypass must finish so its real provider call can be observed.
    result = rpc(image_paths=[str(photo)])["result"]
    assert entered.wait(5)
    before = users(live)
    foreign = SessionDB(live.home / "foreign.db")
    try:
        foreign.create_session("stored", source="tui")
        foreign.append_message("stored", "user", content="foreign store sentinel")

        @contextmanager
        def wrong_store(session):
            yield None if store == "unavailable" else foreign

        monkeypatch.setattr(server, "_session_db", wrong_store)
        release.set()
        wait_all(live)
        assert durable_user_facts(users(live)) == durable_user_facts(before)
        assert not gate.calls and not live.session["running"]
        assert [row["content"] for row in foreign.get_messages("stored")] == ["foreign store sentinel"]
        assert [payload for kind, _, payload in live.frames if kind == "message.user_committed"] == [result["accepted_user"]]
        assert any(kind == "message.complete" and payload.get("status") == "error"
                   and "Accepted image message store" in payload.get("error", "") for kind, _, payload in live.frames)
    finally:
        foreign.close()


@pytest.mark.parametrize("mode", ["native", "text"])
@pytest.mark.parametrize("mutation", ["deleted", "inactive", "changed_uid"])
def test_image_adoption_requires_same_live_row_and_uid(live, monkeypatch, mode, mutation):
    if mode == "native":
        native_vision(live, monkeypatch)
    else:
        monkeypatch.setattr("agent.image_routing.decide_image_input_mode", lambda *a, **k: "text")
    entered, release = pause_worker(live, monkeypatch)
    gate = provider_gate(live, monkeypatch)
    gate.release.set()
    result = rpc(image_paths=[str(image_file(live))])["result"]
    assert entered.wait(5)
    receipt = result["accepted_user"]
    row_id = receipt["message"]["row_id"]
    if mutation == "deleted":
        live.db._write_rowcount("DELETE FROM messages WHERE id=?", (row_id,))
    elif mutation == "inactive":
        live.db.deactivate_message("stored", row_id)
    else:
        live.db._write_rowcount("UPDATE messages SET message_uid=? WHERE id=?", ("changed-uid", row_id))

    def rows():
        return [dict(row) for row in live.db._read_all(
            "SELECT id,session_id,role,content,message_uid,active,timestamp FROM messages WHERE role='user'")]

    before = rows()
    release.set()
    wait_all(live)
    assert not gate.calls and not live.session["running"]
    assert rows() == before  # No replacement, duplicate append or rewrite of another identity.
    assert [payload for kind, _, payload in live.frames if kind == "message.user_committed"] == [receipt]
    assert any(kind == "message.complete" and payload.get("status") == "error"
               and "Accepted image message" in payload.get("error", "") for kind, _, payload in live.frames)


@pytest.mark.parametrize("style", ["guarded_equal", "guarded_change", "wrong_uid", "legacy_equal"])
def test_image_guard_reuses_native_setter_and_preserves_branch_semantics(live, style):
    row_id = live.db.append_message("stored", "user", content="original", message_uid="accepted-uid")
    live.db.create_session("branch", source="tui", parent_session_id="stored",
                           model_config={"_branched_from": "stored"})
    before = [(row["message_uid"], row["content"]) for row in live.db.get_history_foreground("branch")]
    content = "changed" if style == "guarded_change" else "original"
    if style == "legacy_equal":
        result = live.db.set_user_message_content("stored", row_id, content)
    else:
        result = live.db.set_user_message_content(
            "stored", row_id, content, expected_message_uid="wrong-uid" if style == "wrong_uid" else "accepted-uid")
    assert result == (0 if style == "wrong_uid" else 1)
    assert live.db.get_messages("stored")[0]["content"] == content
    assert [(row["message_uid"], row["content"]) for row in live.db.get_history_foreground("branch")] == before
    count = live.db._read_one("SELECT COUNT(*) FROM messages")[0]
    # The guarded equal path proves identity without cloning frozen branch sources;
    # omitting the new option preserves the native setter's existing rewrite behavior.
    assert count == (2 if style in {"guarded_change", "legacy_equal"} else 1)


def test_rotated_owner_uses_profile_database_and_rewrites_same_row(live, monkeypatch, tmp_path):
    native_vision(live, monkeypatch)
    photo = image_file(live)
    launch = SessionDB(tmp_path / "launch" / "state.db")
    try:
        launch.create_session("rotated", source="tui")
        launch.append_message("rotated", "user", content="other profile sentinel")
        live.db.publish_compression_child(
            parent_session_id="stored", child_session_id="rotated", source="tui",
            messages=[{"role": "assistant", "content": "compressed context"}],
            require_compression_lease=False)
        live.agent.session_id = "rotated"
        monkeypatch.setattr(server, "_get_db", lambda: launch)
        entered, release = pause_worker(live, monkeypatch)
        gate = provider_gate(live, monkeypatch)
        result = rpc(image_paths=[str(photo)])["result"]
        assert entered.wait(5)
        assert result["accepted_user"]["stored_session_id"] == "rotated"
        before = users(live, "rotated")
        assert len(before) == 1 and users(live) == []
        release.set()
        assert gate.entered.wait(5)
        gate.release.set()
        wait_all(live)
        assert [(row["id"], row["message_uid"]) for row in users(live, "rotated")] == [
            (before[0]["id"], before[0]["message_uid"])]
        assert users(live) == []
        assert [row["content"] for row in launch.get_messages("rotated")] == ["other profile sentinel"]
    finally:
        launch.close()


@pytest.mark.parametrize("mismatch", ["text", "paths", "order"])
def test_staged_input_match_rejects_changed_text_or_images(live, monkeypatch, mismatch):
    first, second = image_file(live), image_file(live, "second.png")
    entered, release = pause_worker(live, monkeypatch)
    result = rpc(text="original", image_paths=[str(first), str(second)])["result"]
    assert entered.wait(5)
    before = users(live)
    text = "changed" if mismatch == "text" else "original"
    paths = {"text": [str(first), str(second)], "paths": [str(first)], "order": [str(second), str(first)]}[mismatch]
    server._adopt_submit_user_row(live.session, live.agent, "must not replace accepted row", text, image_paths=paths)
    assert users(live) == before and live.agent._pending_cli_user_message is None
    assert result["accepted_user"]["message"]["row_id"] == before[0]["id"]
    # Stop the accepted worker after this direct handoff-boundary probe.
    rpc("session.interrupt")
    release.set()
    wait_all(live)


def test_pure_text_receipt_retains_original_content_and_single_row(live, monkeypatch):
    gate = provider_gate(live, monkeypatch)
    result = rpc(text="plain text")["result"]
    assert gate.entered.wait(5)
    assert result["accepted_user"]["message"]["content"] == "plain text"
    assert "plain text" in gate.calls[0]["messages"][-1]["content"]
    gate.release.set()
    wait_all(live)
    assert len(users(live)) == 1


def test_image_committed_event_retained_in_native_snapshot_and_replay(live, monkeypatch):
    from tui_gateway import event_replay
    from tui_gateway.contracts.registry import check_payload

    event_replay.reset_replay_state()
    monkeypatch.setattr(server, "_emit", _native_emit)
    entered, release = pause_worker(live, monkeypatch)
    result = rpc(image_paths=[str(image_file(live))])["result"]
    assert entered.wait(5)
    snapshot = inflight_output.snapshot(live.session, "runtime")
    committed = [event for event in snapshot["events"] if event["type"] == "message.user_committed"]
    assert len(committed) == 1 and committed[0]["payload"] == result["accepted_user"]
    check_payload("message.user_committed", committed[0]["payload"])
    replay = rpc("session.events.since", last_seen=0)["result"]
    assert [event["payload"] for event in replay["events"] if event["type"] == "message.user_committed"] == [result["accepted_user"]]
    rpc("session.interrupt")
    release.set()
    wait_all(live)
