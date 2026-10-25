"""Imported session labels do not override the requested profile's real store."""

from pathlib import Path

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from hermes_state import SessionDB


@pytest.fixture
def profiles(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    root = tmp_path / ".hermes"
    root.mkdir()
    monkeypatch.setenv("HERMES_HOME", str(root))
    monkeypatch.setattr("hermes_state.DEFAULT_DB_PATH", root / "state.db")
    stores = {}
    for name in ("default", "alex", "study"):
        home = root if name == "default" else root / "profiles" / name
        home.mkdir(parents=True, exist_ok=True)
        stores[name] = SessionDB(db_path=home / "state.db")
    from hermes_cli.web_routers.sessions import manage_router
    app = FastAPI()
    app.include_router(manage_router)
    with TestClient(app) as client:
        yield stores, client
    for db in stores.values():
        db.close()


def imported(db, sid="pi-imported", content="Imported prompt"):
    db.create_session(sid, source="pi-import", profile_name="default")
    db.append_message(sid, "user", content, message_uid=f"{content}-uid", timestamp=100)
    db.append_message(sid, "assistant", f"Answer to {content}", reasoning="Imported reasoning", timestamp=101)
    return db.get_messages(sid)


def get(client, sid, suffix="", *, profile="alex", **params):
    return client.get(f"/api/sessions/{sid}{suffix}", params={"profile": profile, **params})


def test_imported_default_label_has_matching_metadata_history_recovery_timeline_and_details(profiles):
    stores, client = profiles
    db = stores["alex"]
    messages = imported(db)
    before = db.get_session("pi-imported")
    responses = {
        "metadata": get(client, "pi-imported"),
        "ordinary": get(client, "pi-imported", "/messages", view="cards", limit=200),
        "recovery": get(client, "pi-imported", "/messages", recovery_view=1, view="cards", limit=200),
        "anchor": get(client, "pi-imported", "/messages", recovery_view=1,
                      anchor_uid=messages[0]["message_uid"], before=0, after=1),
        "timeline": get(client, "pi-imported", "/timeline"),
        "around": get(client, "pi-imported", "/messages/around", row_id=messages[0]["id"]),
        "details": get(client, "pi-imported", "/messages", detail_row_ids=str(messages[1]["id"])),
    }
    statuses = {name: response.status_code for name, response in responses.items()}
    print("Formal imported-profile REST statuses:", statuses)
    assert statuses == dict.fromkeys(responses, 200)
    assert responses["metadata"].json()["profile"] == "alex"
    assert responses["ordinary"].json()["messages"] == responses["recovery"].json()["messages"]
    assert responses["recovery"].json()["coverage"]["profile"] == "alex"
    assert responses["anchor"].json()["messages"][0]["message_uid"] == messages[0]["message_uid"]
    assert responses["timeline"].json()["entries"][0]["row_id"] == messages[0]["id"]
    assert responses["around"].json()["messages"][0]["content"] == "Imported prompt"
    assert responses["details"].json()["messages"][0]["reasoning"] == "Imported reasoning"
    assert db.get_session("pi-imported") == before
    assert before["source"] == "pi-import" and before["profile_name"] == "default"


@pytest.mark.parametrize("requested", ["pi-imported", "imported-tip"])
def test_imported_labels_work_across_real_compression_chain(profiles, requested):
    stores, client = profiles
    db = stores["alex"]
    original = imported(db)
    db.end_session("pi-imported", end_reason="compression")
    db.create_session("imported-tip", source="desktop", profile_name="default", parent_session_id="pi-imported")
    db.append_messages_batch("imported-tip", original)
    db.append_message("imported-tip", "user", "Continued prompt", message_uid="continued", timestamp=102)
    recovery = get(client, requested, "/messages", recovery_view=1)
    assert recovery.status_code == 200, recovery.text
    page = recovery.json()
    assert page["session_id"] == db.resolve_resume_session_id(requested) == "imported-tip"
    assert page["coverage"]["lineage"] == ["pi-imported", "imported-tip"]
    assert [row["content"] for row in page["messages"]] == ["Imported prompt", "Answer to Imported prompt", "Continued prompt"]
    timeline = get(client, requested, "/timeline").json()
    assert [entry["preview"] for entry in timeline["entries"]] == ["Imported prompt", "Continued prompt"]
    old_anchor = get(client, requested, "/messages", recovery_view=1,
                     anchor_row_id=original[0]["id"], before=0, after=1)
    assert old_anchor.status_code == 200 and old_anchor.json()["session_id"] == "imported-tip"
    prompt_id = timeline["entries"][0]["row_id"]
    assert get(client, requested, "/messages/around", row_id=prompt_id).json()["messages"][0]["id"] == prompt_id
    answer_id = page["messages"][1]["id"]
    assert get(client, requested, "/messages", detail_row_ids=str(answer_id)).json()["messages"][0]["reasoning"]
    assert all(db.get_session(sid)["profile_name"] == "default" for sid in ("pi-imported", "imported-tip"))


@pytest.mark.parametrize("profile", ["default", "alex", "study"])
def test_identical_session_and_row_ids_only_read_selected_database(profiles, profile):
    stores, client = profiles
    for owner, db in stores.items():
        imported(db, content=f"{owner} private prompt")
    for suffix, params in (("/messages", {"recovery_view": 1}), ("/messages", {}),
                           ("/messages/around", {"row_id": 1}), ("/messages", {"detail_row_ids": "1"})):
        response = get(client, "pi-imported", suffix, profile=profile, **params)
        assert response.status_code == 200, response.text
        assert response.json()["profile"] == profile
        assert response.json()["messages"][0]["content"] == f"{profile} private prompt"
    timeline = get(client, "pi-imported", "/timeline", profile=profile)
    assert timeline.status_code == 200
    assert timeline.json()["entries"][0]["preview"] == f"{profile} private prompt"


def test_missing_scope_and_foreign_anchors_keep_real_not_found_semantics(profiles):
    stores, client = profiles
    own = imported(stores["alex"])
    foreign = imported(stores["study"], sid="only-study", content="Study-only prompt")
    stores["study"].append_messages_batch("only-study", [{"role": "user", "content": f"Study {i}"} for i in range(5)])
    foreign_row = stores["study"].get_messages("only-study")[-1]
    for sid, profile in (("only-study", "alex"), ("pi-imported", "default"), ("absent", "alex")):
        for suffix, params in (("", {}), ("/messages", {}), ("/messages", {"recovery_view": 1}),
                               ("/timeline", {}), ("/messages/around", {"row_id": own[0]["id"]})):
            assert get(client, sid, suffix, profile=profile, **params).status_code == 404
    for anchor in ({"anchor_uid": foreign[0]["message_uid"]}, {"anchor_row_id": foreign_row["id"]}):
        response = get(client, "pi-imported", "/messages", recovery_view=1, **anchor)
        assert response.status_code == 404 and response.json()["detail"] == "anchor_not_found"
    response = get(client, "pi-imported", "/messages/around", row_id=foreign_row["id"])
    assert response.status_code == 404 and response.json()["detail"] == "Prompt not found"
    details = get(client, "pi-imported", "/messages", detail_row_ids=str(foreign_row["id"]))
    assert details.status_code == 200 and details.json()["messages"] == []
