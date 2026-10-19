"""The sidebar projection preserves native list ownership, flags and pagination."""
from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from hermes_state import SessionDB


@pytest.mark.parametrize("full", [False, True])
def test_summary_omits_only_origin_and_preserves_native_pages(tmp_path, monkeypatch, full):
    from hermes_cli.web_routers import sessions

    home = tmp_path / "profile"
    home.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(sessions, "_cron_profile_home", lambda profile: ("work", home))
    monkeypatch.setattr(sessions, "_maybe_auto_archive_for_profile", lambda profile: None)
    monkeypatch.setattr(sessions, "_open_session_db_for_profile",
                        lambda profile, read_only: SessionDB(home / "state.db", read_only=read_only))
    db = SessionDB(home / "state.db")
    try:
        for index in range(5):
            sid = f"session-{index}"
            db.create_session(sid, source="tui",
                              origin_json='{"payload":"' + "x" * 10000 + '"}',
                              system_prompt="stable system prompt", model="test/model")
            db.set_session_title(sid, sid)
            db.append_message(sid, "user", content=f"question {index}")
        db.set_session_pinned("session-0", True)
        db.set_session_archived("session-1", True)
        app = FastAPI()
        app.include_router(sessions.list_router)
        with TestClient(app) as client:
            for archived in ("exclude", "only", "include"):
                for offset in (0, 2):
                    query = {"profile": "work", "full": str(full).lower(), "limit": 2,
                             "offset": offset, "order": "recent", "archived": archived}
                    default = client.get("/api/sessions", params=query)
                    explicit = client.get("/api/sessions", params={**query, "summary": "false"})
                    summary = client.get("/api/sessions", params={**query, "summary": "true"})
                    assert default.status_code == explicit.status_code == summary.status_code == 200
                    expected = default.json()
                    assert explicit.json() == expected
                    for row in expected["sessions"]:
                        assert row.pop("origin_json")
                        assert row["profile"] == "work" and not row["is_default_profile"]
                        assert isinstance(row["pinned"], bool) and isinstance(row["archived"], bool)
                        assert ("system_prompt" in row) == full
                    assert summary.json() == expected
                    assert summary.json()["offset"] == offset and summary.json()["limit"] == 2
                    assert summary.json()["total"] == {"exclude": 4, "only": 1, "include": 5}[archived]
    finally:
        db.close()


def test_detail_summary_keeps_metadata_default_and_not_found(tmp_path, monkeypatch):
    from hermes_cli.web_routers import sessions

    monkeypatch.setenv("HERMES_HOME", str(tmp_path))
    monkeypatch.setattr(sessions, "_open_session_db_for_profile",
                        lambda profile, read_only: SessionDB(tmp_path / "state.db", read_only=read_only))
    monkeypatch.setattr(sessions, "_serving_profile", lambda profile: "work")
    db = SessionDB(tmp_path / "state.db")
    try:
        db.create_session("stored", source="tui", system_prompt="prompt", model="test/model",
                          model_config={"context_length": 32000}, origin_json='{"origin":"large"}')
        db.set_session_title("stored", "Real title")
        db.append_message("stored", "user", content="question")
        app = FastAPI()
        app.include_router(sessions.manage_router)
        with TestClient(app) as client:
            default = client.get("/api/sessions/stored").json()
            explicit = client.get("/api/sessions/stored?summary=false").json()
            summary = client.get("/api/sessions/stored?summary=true").json()
            assert default == explicit
            assert all(default[field] for field in ("origin_json", "system_prompt", "model_config"))
            assert summary == {key: value for key, value in default.items()
                               if key not in ("origin_json", "system_prompt", "model_config")}
            assert summary["title"] == "Real title" and summary["model"] == "test/model"
            assert summary["profile"] == "work" and summary["message_count"] == 1
            assert "input_tokens" in summary and "output_tokens" in summary
            for query in ("", "?summary=false", "?summary=true"):
                missing = client.get("/api/sessions/missing" + query)
                assert missing.status_code == 404 and missing.json() == {"detail": "Session not found"}
    finally:
        db.close()
