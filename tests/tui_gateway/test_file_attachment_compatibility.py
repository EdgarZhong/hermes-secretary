"""Original file.attach wire semantics and additive upload RPC boundaries."""

import base64
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading
import uuid

import pytest

from tui_gateway import server


@pytest.fixture
def session(tmp_path, monkeypatch):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    record = {"profile_home": str(tmp_path / "served-profile"), "cwd": str(workspace),
              "history_lock": threading.Lock(), "running": False, "attached_images": []}
    monkeypatch.setattr(server, "_sessions", {"runtime": record})
    monkeypatch.setattr(server, "_hermes_home", tmp_path / "launch-profile")
    monkeypatch.setattr(server, "_cwd_is_remote", lambda home: False)
    monkeypatch.setattr(server, "_start_agent_build", lambda *args: None)
    return record


def rpc(method="file.attach", **params):
    return server.dispatch({"jsonrpc": "2.0", "id": 1, "method": method,
                            "params": {"session_id": "runtime", **params}})


def chunk(upload_id, payload, offset=0, total=10):
    return rpc("file.upload_chunk", upload_id=upload_id, offset=offset, total_bytes=total,
               name="same.bin", data_url=base64.b64encode(payload).decode())


@pytest.mark.parametrize("data_url", ["aGVsbG8=", "data:text/plain;base64,aGVsbG8="])
def test_legacy_upload_returns_exact_six_field_result(session, data_url):
    result = rpc(data_url=data_url, name=" hello.txt ")["result"]
    target = Path(session["profile_home"]) / "attachments" / "hello.txt"
    assert result == {"attached": True, "name": "hello.txt", "path": str(target),
                      "ref_path": str(target), "ref_text": f"@file:{target}", "uploaded": True}
    assert target.read_bytes() == b"hello"


def test_legacy_visible_path_is_not_reuploaded(session):
    source = Path(session["cwd"]) / "on disk.txt"
    source.write_text("real local bytes")
    result = rpc(path=str(source))["result"]
    assert result == {"attached": True, "name": source.name, "path": str(source),
                      "ref_path": source.name, "ref_text": "@file:`on disk.txt`", "uploaded": False}
    assert not Path(session["profile_home"]).exists()


@pytest.mark.parametrize("params,code,message", [
    ({}, 4015, "path or data_url required"),
    ({"path": "  ", "data_url": " "}, 4015, "path or data_url required"),
    ({"data_url": "%%%"}, 5028, "invalid data_url payload"),
    ({"path": "/unavailable/attachment.bin"}, 5028, "file not found on gateway and no data_url provided"),
])
def test_legacy_domain_errors_remain_exact(session, params, code, message):
    assert rpc(**params)["error"] == {"code": code, "message": message}
    assert not Path(session["profile_home"]).exists()


@pytest.mark.parametrize("key,value", [
    ("upload_id", str(uuid.uuid4())), ("offset", 0), ("total_bytes", 1),
    ("abort_upload", True), ("metadata_only", True), ("unknown", None),
])
def test_legacy_extra_keys_rejected_before_staging(session, key, value):
    response = rpc(data_url="eA==", name="never.bin", **{key: value})
    assert response["error"]["code"] == 4000
    assert f"{key}: Extra inputs are not permitted" in response["error"]["message"]
    assert not Path(session["profile_home"]).exists()


@pytest.mark.parametrize("method,params", [
    ("file.attach", {"data_url": "eA=="}),
    ("file.upload_chunk", {"upload_id": str(uuid.uuid4()), "offset": 0,
                           "total_bytes": 1, "data_url": "eA=="}),
    ("file.upload_abort", {"upload_id": str(uuid.uuid4())}),
    ("file.attachment_info", {"path": "x.bin"}),
])
def test_all_methods_require_live_runtime_session(session, method, params):
    assert rpc(method, session_id="stored-locator", **params)["error"]["code"] == 4001
    assert not Path(session["profile_home"]).exists()


def test_metadata_and_abort_do_not_warm_agent_or_mutate_turn(session, monkeypatch):
    source = Path(session["cwd"]) / "real.txt"
    source.write_bytes(b"read-only")
    session.update(running=True, inflight_turn={"text": "ongoing"}, pending=["keep"])
    before = dict(session)
    monkeypatch.setattr(server, "_start_agent_build", lambda *args: pytest.fail("read/abort warmed agent"))
    result = rpc("file.attachment_info", path=str(source))["result"]
    assert result["size_bytes"] == len(b"read-only")
    assert result["attached"] is False and result["uploaded"] is False
    assert session == before
    assert not Path(session["profile_home"]).exists()
    rpc("file.upload_abort", upload_id=str(uuid.uuid4()))
    assert session["running"] is True
    assert session["inflight_turn"] == before["inflight_turn"]
    assert session["pending"] == before["pending"]


def test_metadata_resolves_profile_roots_and_workspace_storage(session):
    profile = Path(session["profile_home"])
    profile.mkdir()
    (profile / "config.yaml").write_text("attachments:\n  storage: workspace\n")
    result = chunk(str(uuid.uuid4()), b"workspace!", total=10)["result"]
    target = Path(result["path"])
    assert target.parent == Path(session["cwd"]) / ".hermes" / "attachments"
    assert rpc("file.attachment_info", path=result["ref_path"])["result"]["size_bytes"] == 10
    assert not (profile / "attachments").exists()
    assert not (profile.parent / "launch-profile").exists()


def test_abort_waits_for_chunk_owner_then_drops_only_partial(session, monkeypatch):
    upload_id = str(uuid.uuid4())
    entered, release = threading.Event(), threading.Event()
    real_append = server._append_file_attachment_chunk

    def blocked_append(*args):
        entered.set()
        assert release.wait(timeout=10)
        return real_append(*args)

    monkeypatch.setattr(server, "_append_file_attachment_chunk", blocked_append)
    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = pool.submit(chunk, upload_id, b"first")
        assert entered.wait(timeout=5)
        abort = pool.submit(rpc, "file.upload_abort", upload_id=upload_id)
        release.set()
        late_ack = pending.result(timeout=5)
        aborted = abort.result(timeout=5)
    assert late_ack["result"]["attached"] is False
    assert aborted["result"]["attached"] is False
    assert upload_id not in session["file_uploads"]
    assert list(Path(session["profile_home"]).joinpath("attachments").iterdir()) == []
    assert chunk(upload_id, b" last", offset=5)["error"]["code"] == 5028


def test_completed_ack_retry_after_cancel_does_not_revoke_or_duplicate_file(session):
    upload_id = str(uuid.uuid4())
    first = chunk(upload_id, b"first")
    assert first["result"]["path"] == "" and first["result"]["ref_text"] == ""
    completed = chunk(upload_id, b" last", offset=5)
    cancelled = rpc("file.upload_abort", upload_id=upload_id)
    assert cancelled["result"]["attached"] is False
    assert cancelled["result"]["ref_text"] == ""
    assert chunk(upload_id, b" last", offset=5) == completed
    target = Path(completed["result"]["path"])
    assert target.read_bytes() == b"first last"
    assert list(target.parent.iterdir()) == [target]


@pytest.mark.parametrize("method,params", [
    ("file.upload_chunk", {"upload_id": str(uuid.uuid4()), "offset": 0,
                           "total_bytes": 1, "data_url": "eA==", "abort_upload": True}),
    ("file.upload_abort", {"upload_id": str(uuid.uuid4()), "data_url": "eA=="}),
    ("file.attachment_info", {"path": "x.bin", "data_url": "eA=="}),
])
def test_new_methods_do_not_mix_control_and_write_contracts(session, method, params):
    assert rpc(method, **params)["error"]["code"] == 4000
    assert not Path(session["profile_home"]).exists()


@pytest.mark.parametrize("method,params,message", [
    ("file.upload_chunk", {}, "upload_id must be a canonical UUID"),
    ("file.upload_abort", {}, "upload_id must be a canonical UUID"),
    ("file.attachment_info", {}, "path is required for attachment metadata"),
])
def test_missing_new_method_inputs_fail_without_write(session, method, params, message):
    assert rpc(method, **params)["error"] == {"code": 5028, "message": message}
    assert not Path(session["profile_home"]).exists()


def test_abort_does_not_touch_another_runtime_with_the_same_upload_id(session, monkeypatch):
    upload_id = str(uuid.uuid4())
    other = {**session, "history_lock": threading.Lock()}
    monkeypatch.setattr(server, "_sessions", {"runtime": session, "other": other})
    chunk(upload_id, b"first")
    chunk(upload_id, b"first")  # ACK replay does not allocate another temporary.
    response = rpc("file.upload_chunk", session_id="other", upload_id=upload_id, offset=0,
                   total_bytes=10, name="same.bin", data_url="b3RoZXI=")
    assert response["result"]["received_bytes"] == 5
    survivor = other["file_uploads"][upload_id]["temporary"]
    rpc("file.upload_abort", upload_id=upload_id)
    assert survivor.read_bytes() == b"other"
    assert list(survivor.parent.iterdir()) == [survivor]


def test_failed_chunk_write_removes_only_its_unpublished_upload(session, monkeypatch):
    completed = chunk(str(uuid.uuid4()), b"completed!", total=10)["result"]
    upload_id = str(uuid.uuid4())
    chunk(upload_id, b"first")
    temporary = session["file_uploads"][upload_id]["temporary"]
    real_open = Path.open

    def fail_write(path, mode="r", *args, **kwargs):
        if path == temporary and mode == "r+b":
            raise OSError("write failed")
        return real_open(path, mode, *args, **kwargs)

    monkeypatch.setattr(Path, "open", fail_write)
    assert chunk(upload_id, b" last", offset=5)["error"] == {"code": 5028, "message": "write failed"}
    assert upload_id not in session["file_uploads"]
    assert not temporary.exists()
    survivor = Path(completed["path"])
    assert survivor.read_bytes() == b"completed!"
    assert list(survivor.parent.iterdir()) == [survivor]
