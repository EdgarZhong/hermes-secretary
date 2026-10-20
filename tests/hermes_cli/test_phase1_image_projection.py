"""Phase-one read-only image refs through real HTTP, SQLite and file downloads."""

import base64
import copy
import gzip
import json
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+aX1sAAAAASUVORK5CYII="
)


def image_content(paths, caption="", *, hints=False):
    from agent.context_references import format_reference_value

    if hints:
        text = caption + "\n\n" + "\n".join(f"[Image attached at: {path}]" for path in paths)
    else:
        text = (caption + "\n\n" if caption else "") + "\n".join(
            f"@image:{format_reference_value(str(path))}" for path in paths)
    return [{"type": "text", "text": text}] + [
        {"type": "image_url", "image_url": {"url": "data:image/png;base64," +
         base64.b64encode(PNG).decode("ascii")}} for _ in paths]


@pytest.fixture
def endpoint(tmp_path, monkeypatch):
    from hermes_cli import profiles, web_server
    from hermes_cli.config import atomic_config_write
    from hermes_state import SessionDB

    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    home = tmp_path / "hermes"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setenv("HERMES_DASHBOARD_FILES_ROOT", str(tmp_path / "managed"))
    monkeypatch.setattr(profiles, "_get_default_hermes_home", lambda: home)
    monkeypatch.setattr("hermes_state.DEFAULT_DB_PATH", home / "state.db")
    homes = {"default": home, "study": home / "profiles" / "study"}
    dbs = {}
    for name, profile_home in homes.items():
        profile_home.mkdir(parents=True, exist_ok=True)
        atomic_config_write(profile_home / "config.yaml", {"terminal": {"cwd": str(tmp_path)}})
        db = SessionDB(profile_home / "state.db")
        db.create_session("chat", source="desktop", profile_name=name, cwd=str(tmp_path))
        dbs[name] = db
    root = tmp_path / "managed"
    root.mkdir()
    image = root / "my image.png"
    image.write_bytes(PNG)
    monkeypatch.setattr(web_server.app.state, "auth_required", False, raising=False)
    monkeypatch.setattr(web_server.app.state, "bound_host", None, raising=False)
    client = TestClient(web_server.app)
    client.headers[web_server._SESSION_HEADER_NAME] = web_server._SESSION_TOKEN
    yield client, dbs, image
    client.close()
    for db in dbs.values():
        db.close()


@pytest.mark.parametrize("view", [None, "cards", "details"])
@pytest.mark.parametrize("caption,hints,duplicates", [
    ("", False, False), ("caption", True, False), ("two images", False, True),
])
def test_verified_refs_preserve_identity_and_download_all_images(endpoint, view, caption, hints, duplicates):
    client, dbs, image = endpoint
    paths = [image, image] if duplicates else [image]
    content = image_content(paths, caption, hints=hints)
    row_id = dbs["study"].append_message("chat", "user", content, message_uid="image-uid")
    params = {"profile": "study", "limit": 200}
    if view == "details":
        params.pop("limit")
        params["detail_row_ids"] = str(row_id)
    elif view:
        params["view"] = view
    path = "/api/sessions/chat/messages"
    original = client.get(path, params=params)
    optimized = client.get(path, params={**params, "prefer_image_refs": "true", "inline_images": "true"})
    assert original.status_code == optimized.status_code == 200
    before, after = original.json(), optimized.json()
    assert after["profile"] == before["profile"] == "study"
    assert after["pagination"] == before["pagination"]
    old_row, new_row = before["messages"][0], after["messages"][0]
    assert old_row["content"] == content
    assert {k: v for k, v in old_row.items() if k != "content"} == {
        k: v for k, v in new_row.items() if k != "content"}
    assert new_row["message_uid"] == "image-uid"
    assert new_row["id"] == row_id
    assert new_row["content"].count("@image:") == len(paths)
    if caption:
        assert new_row["content"].startswith(caption + "\n\n")
    for target in paths:
        downloaded = client.get("/api/fs/download", params={"path": str(target), "profile": "study"})
        assert downloaded.status_code == 200
        assert downloaded.headers["content-type"].startswith("image/png")
        assert downloaded.content == PNG
    assert dbs["study"].get_messages("chat")[0]["content"] == content
    assert client.get(path, params={**params, "prefer_image_refs": "false"}).json() == before


@pytest.mark.parametrize("failure", [
    "missing", "changed", "directory", "non-image-mime", "too-large", "sensitive",
    "outside-root", "symlink-outside", "extra-part", "bad-base64", "part-count", "mixed-valid-invalid",
])
def test_any_failed_validation_keeps_the_whole_inline_row(endpoint, failure):
    from hermes_cli.web_server import _FS_DATA_URL_MAX_BYTES

    client, dbs, image = endpoint
    root = image.parent
    directory = root / "directory.png"
    directory.mkdir()
    changed = root / "changed.png"
    changed.write_bytes(b"changed")
    text_file = root / "image.txt"
    text_file.write_bytes(PNG)
    large = root / "large.png"
    with large.open("wb") as stream:
        stream.truncate(_FS_DATA_URL_MAX_BYTES + 1)
    sensitive = root / "pairing" / "image.png"
    sensitive.parent.mkdir()
    sensitive.write_bytes(PNG)
    outside = root.parent / "outside.png"
    outside.write_bytes(PNG)
    link = root / "link.png"
    link.symlink_to(outside)
    valid = image_content([image], "keep caption")
    bad_base64 = copy.deepcopy(valid)
    bad_base64[1]["image_url"]["url"] = "data:image/png;base64,broken!"
    cases = {name: image_content([target], "keep caption") for name, target in {
        "missing": root / "absent.png", "changed": changed, "directory": directory,
        "non-image-mime": text_file, "too-large": large, "sensitive": sensitive,
        "outside-root": outside, "symlink-outside": link,
    }.items()}
    cases.update({
        "extra-part": valid + [{"type": "text", "text": "must not be discarded"}],
        "bad-base64": bad_base64, "part-count": valid[:1],
        "mixed-valid-invalid": image_content([image, root / "absent.png"], "keep caption"),
    })
    content = cases[failure]
    row_id = dbs["default"].append_message("chat", "user", content)
    params = {"profile": "default", "prefer_image_refs": "true", "inline_images": "true"}
    for projection in ({"view": "cards"}, {"detail_row_ids": str(row_id)}):
        response = client.get("/api/sessions/chat/messages", params={**params, **projection})
        assert response.status_code == 200
        assert response.json()["messages"][0]["content"] == content
    assert dbs["default"].get_messages("chat")[0]["content"] == content


def test_text_assistant_inline_false_and_profile_owner_remain_compatible(endpoint):
    client, dbs, image = endpoint
    structured = image_content([image], "caption")
    dbs["default"].append_message("chat", "user", "plain", message_uid="plain")
    dbs["default"].append_message("chat", "assistant", structured, message_uid="assistant")
    dbs["default"].append_message("chat", "user", structured, message_uid="image")
    foreign_id = dbs["study"].append_message("chat", "user", "study only", message_uid="study")
    path = "/api/sessions/chat/messages"
    params = {"profile": "default", "inline_images": "false"}
    original = client.get(path, params=params).json()
    projected = client.get(path, params={**params, "prefer_image_refs": "true"}).json()
    assert projected == original
    rows = client.get(path, params={"profile": "default", "prefer_image_refs": "true"}).json()["messages"]
    assert rows[0]["content"] == "plain"
    assert rows[1]["content"] == structured
    study = client.get(path, params={"profile": "study", "prefer_image_refs": "true"}).json()
    assert [(r["id"], r["message_uid"], r["content"]) for r in study["messages"]] == [
        (foreign_id, "study", "study only")]
    dbs["study"].create_session("only-study", source="desktop", profile_name="study")
    assert client.get("/api/sessions/only-study/messages", params={
        "profile": "default", "prefer_image_refs": "true"}).status_code == 404


def test_only_queried_page_and_details_are_validated(endpoint, monkeypatch):
    import tui_gateway.session_history as history

    client, dbs, image = endpoint
    content = image_content([image])
    first = dbs["default"].append_message("chat", "user", content, message_uid="first")
    second = dbs["default"].append_message("chat", "user", content, message_uid="second")
    calls = []
    real = history._user_image_display_text

    def tracked(value):
        calls.append(copy.deepcopy(value))
        return real(value)

    monkeypatch.setattr(history, "_user_image_display_text", tracked)
    path = "/api/sessions/chat/messages"
    params = {"profile": "default", "prefer_image_refs": "true"}
    page = client.get(path, params={**params, "limit": 1, "offset": 1, "order": "oldest"}).json()
    assert [r["id"] for r in page["messages"]] == [second]
    assert calls == [content]
    calls.clear()
    detail = client.get(path, params={**params, "detail_row_ids": str(first)}).json()
    assert [r["id"] for r in detail["messages"]] == [first]
    assert calls == [content]


def test_download_admission_error_or_remote_backend_preserves_inline(endpoint, monkeypatch):
    from hermes_cli.web_routers import files

    client, dbs, image = endpoint
    content = image_content([image])
    dbs["default"].append_message("chat", "user", content)
    path = "/api/sessions/chat/messages"
    params = {"profile": "default", "prefer_image_refs": "true"}
    with monkeypatch.context() as patch:
        patch.setattr(files, "_fs_backend", lambda profile: object())
        assert client.get(path, params=params).json()["messages"][0]["content"] == content
    with monkeypatch.context() as patch:
        def fail(_target):
            raise OSError("read admission unavailable")

        patch.setattr(files, "_refuse_live_database", fail)
        assert client.get(path, params=params).json()["messages"][0]["content"] == content


def test_same_200_row_window_keeps_order_caption_and_reports_bytes(endpoint, record_property):
    client, dbs, image = endpoint
    db = dbs["default"]
    expected_contents = {}
    for index in range(205):
        if index % 20 == 0:
            content = image_content([image, image], f"caption {index}")
            expected_contents[f"row-{index}"] = f"caption {index}"
        elif index % 20 == 1:
            content = image_content([image.parent / "missing.png"], f"fallback {index}")
        else:
            content = f"text {index}"
        db.append_message("chat", "user", content, message_uid=f"row-{index}")
    path = "/api/sessions/chat/messages"
    params = {"profile": "default", "view": "cards", "limit": 200, "offset": 3, "order": "oldest"}
    started = time.perf_counter()
    original = client.get(path, params=params)
    original_seconds = time.perf_counter() - started
    started = time.perf_counter()
    optimized = client.get(path, params={**params, "prefer_image_refs": "true", "inline_images": "true"})
    optimized_seconds = time.perf_counter() - started
    before, after = original.json(), optimized.json()
    assert len(before["messages"]) == len(after["messages"]) == 200
    assert before["pagination"] == after["pagination"]
    assert [(r["id"], r["message_uid"], r["role"]) for r in before["messages"]] == [
        (r["id"], r["message_uid"], r["role"]) for r in after["messages"]]
    converted = fallback = 0
    for old, new in zip(before["messages"], after["messages"]):
        if old["message_uid"] in expected_contents:
            converted += 1
            assert new["content"].startswith(expected_contents[old["message_uid"]] + "\n\n")
            assert new["content"].count("@image:") == 2
        else:
            fallback += isinstance(old["content"], list)
            assert old["content"] == new["content"]
    assert converted == 10 and fallback == 10
    record_property("window_metrics", json.dumps({
        "environment": "synthetic SQLite + HTTP; not production", "rows": 200,
        "converted_rows": converted, "converted_images": 2 * converted,
        "fallback_rows": fallback, "fallback_reasons": {"missing_file": fallback},
        "original_json_bytes": len(original.content), "optimized_json_bytes": len(optimized.content),
        "original_gzip_bytes": len(gzip.compress(original.content)),
        "optimized_gzip_bytes": len(gzip.compress(optimized.content)),
        "original_seconds": original_seconds, "optimized_seconds": optimized_seconds,
    }))


def test_messages_and_download_still_require_existing_session_auth(endpoint):
    from hermes_cli import web_server

    client, dbs, image = endpoint
    dbs["default"].append_message("chat", "user", image_content([image]))
    token = client.headers.pop(web_server._SESSION_HEADER_NAME)
    try:
        assert client.get("/api/sessions/chat/messages", params={
            "prefer_image_refs": "true", "profile": "default"}).status_code == 401
        assert client.get("/api/fs/download", params={
            "path": str(image), "profile": "default"}).status_code == 401
    finally:
        client.headers[web_server._SESSION_HEADER_NAME] = token
