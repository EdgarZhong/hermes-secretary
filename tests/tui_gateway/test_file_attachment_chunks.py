"""Bounded native file.attach uploads: ownership, publication and ACK retry semantics."""

import base64
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import threading
import uuid

import pytest

from tui_gateway import server
from tui_gateway.contracts.registry import METHODS, check_result


@pytest.fixture
def sessions(tmp_path, monkeypatch):
    records = {
        sid: {"profile_home": str(tmp_path / sid), "cwd": str(tmp_path / sid / "workspace"),
              "running": False, "history_lock": threading.Lock()}
        for sid in ("first", "second")
    }
    monkeypatch.setattr(server, "_sessions", records)
    monkeypatch.setattr(server, "_cwd_is_remote", lambda home: False)
    return records


def request(sid="first", **params):
    response = server._methods["file.attach"](1, {"session_id": sid, **params})
    if "result" in response:
        check_result(METHODS["file.attach"], response["result"])
    return response


def chunk(upload_id, offset, payload, total=10, sid="first", name="same.bin"):
    return request(sid, upload_id=upload_id, offset=offset, total_bytes=total, name=name,
                   data_url="data:application/octet-stream;base64," + base64.b64encode(payload).decode())


def test_chunks_publish_only_complete_bytes_and_retry_same_ack(sessions):
    key = str(uuid.uuid4())
    first = chunk(key, 0, b"first")
    assert first["result"]["attached"] is False
    assert first["result"]["ref_text"] == ""
    assert chunk(key, 0, b"first") == first
    assert chunk(key, 0, b"other")["error"]["code"] == 5028
    assert chunk(key, 7, b"end")["error"]["code"] == 5028
    last = chunk(key, 5, b" last")
    assert last["result"]["attached"] is True
    assert last["result"]["size_bytes"] == 10
    assert Path(last["result"]["path"]).read_bytes() == b"first last"
    assert chunk(key, 5, b" last") == last
    assert chunk(key, 0, b"first")["error"]["code"] == 5028
    assert list(Path(sessions["first"]["profile_home"]).joinpath("attachments").iterdir()) == [Path(last["result"]["path"])]


def test_same_upload_id_isolated_by_owner_and_names_allocate_independently(sessions):
    key = str(uuid.uuid4())
    first = chunk(key, 0, b"first", total=5)
    second = chunk(key, 0, b"other", total=5, sid="second")
    third = chunk(str(uuid.uuid4()), 0, b"third", total=5)
    paths = [Path(item["result"]["path"]) for item in (first, second, third)]
    assert len(set(paths)) == 3
    assert [path.read_bytes() for path in paths] == [b"first", b"other", b"third"]
    assert paths[0].parent != paths[1].parent
    assert paths[2].name == "same-2.bin"


def test_concurrent_same_chunk_appends_once(sessions):
    key = str(uuid.uuid4())
    with ThreadPoolExecutor(max_workers=2) as pool:
        responses = list(pool.map(lambda _: chunk(key, 0, b"first"), range(2)))
    assert responses[0] == responses[1]
    assert sessions["first"]["file_uploads"][key]["offset"] == 5
    result = chunk(key, 5, b" last")["result"]
    assert Path(result["path"]).read_bytes() == b"first last"


def test_abort_removes_partial_and_does_not_revoke_complete_upload(sessions):
    key = str(uuid.uuid4())
    chunk(key, 0, b"first")
    temporary = sessions["first"]["file_uploads"][key]["temporary"]
    assert request(upload_id=key, abort_upload=True)["result"]["attached"] is False
    assert not temporary.exists()
    assert key not in sessions["first"]["file_uploads"]
    assert chunk(key, 5, b" last")["error"]["code"] == 5028
    result = chunk(key, 0, b"done", total=4)["result"]
    request(upload_id=key, abort_upload=True)
    assert Path(result["path"]).read_bytes() == b"done"


@pytest.mark.parametrize("total", [0, -1, 500_000_001])
def test_invalid_total_rejected_without_partial_file(sessions, total):
    assert "error" in chunk(str(uuid.uuid4()), 0, b"x", total=total)
    assert not Path(sessions["first"]["profile_home"]).joinpath("attachments").exists()


def test_full_budget_total_admitted_and_chunk_overflow_keeps_existing_bytes(sessions):
    key = str(uuid.uuid4())
    assert chunk(key, 0, b"x", total=500_000_000)["result"]["received_bytes"] == 1
    request(upload_id=key, abort_upload=True)
    chunk(key, 0, b"first", total=6)
    assert "error" in chunk(key, 5, b"xx", total=6)
    assert sessions["first"]["file_uploads"][key]["temporary"].read_bytes() == b"first"


def test_read_only_metadata_uses_real_size_without_staging_and_enforces_roots(sessions, tmp_path):
    workspace = Path(sessions["first"]["cwd"])
    workspace.mkdir(parents=True)
    source = workspace / "real.bin"
    source.write_bytes(b"real bytes")
    before = set(tmp_path.rglob("*"))
    result = request(path="real.bin", metadata_only=True)["result"]
    assert result["attached"] is False
    assert result["size_bytes"] == 10
    assert set(tmp_path.rglob("*")) == before
    assert source.read_bytes() == b"real bytes"
    assert "error" in request("second", path=str(source), metadata_only=True)
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"outside")
    (workspace / "link.bin").symlink_to(outside)
    assert "error" in request(path="link.bin", metadata_only=True)


def test_remote_cwd_does_not_stat_same_named_local_path(sessions, monkeypatch):
    local = Path(sessions["first"]["cwd"])
    local.mkdir(parents=True)
    (local / "not-remote.bin").write_bytes(b"host bytes")
    monkeypatch.setattr(server, "_cwd_is_remote", lambda home: True)
    assert "error" in request(path="not-remote.bin", metadata_only=True)
    result = chunk(str(uuid.uuid4()), 0, b"local staged", total=12)["result"]
    assert request(path=result["path"], metadata_only=True)["result"]["size_bytes"] == 12


def test_upload_id_cannot_inject_path(sessions):
    assert "error" in chunk("../../outside", 0, b"x", total=1)
    assert not Path(sessions["first"]["profile_home"]).exists()


def test_chunk_controls_without_upload_id_cannot_fall_back_to_legacy_write(sessions):
    response = request(offset=0, total_bytes=1, name="not-staged.bin", data_url="eA==")
    assert response["error"]["code"] == 5028
    assert "upload_id" in response["error"]["message"]
    assert not Path(sessions["first"]["profile_home"]).exists()
