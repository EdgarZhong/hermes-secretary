"""Proposal thresholds count the same current Notebook bodies that Main receives."""

from copy import deepcopy
from types import SimpleNamespace

import pytest

from secretary.notebook_model import NotebookWorkingState
from secretary.notebook_render import render_notebook
from secretary.noting_notifications import completion_body


@pytest.fixture
def committed(tmp_path):
    (tmp_path / "config.yaml").write_text("timezone: UTC\n", encoding="utf-8")
    state = NotebookWorkingState("conv_count", validate_source_identity=lambda source: True)
    for kind, fields in (
        ("matter", {"description": "Current matter", "completion_condition": "Delivered"}),
        ("situation", {"description": "Current situation", "subjects": ["visit"]}),
        ("question", {"description": "Current question"}),
        ("candidate", {"description": "Current candidate", "targets": ["memory"],
                       "notebook_refs": [], "source_types": []}),
    ):
        state.create(kind, fields, source_message_uids=["source"])
    for index in range(2):
        entry = state.create("matter", {"description": f"Retired audit item {index}", "completion_condition": "Done"},
                             source_message_uids=["source"])["entry"]
        state.archive(entry["entry_id"], "Already handled")
    return {"snapshot_id": "synthetic-snapshot", "conversation_ref": "conv_count", "anchor_message_uid": "source",
            "created_at": "2026-11-08T12:00:00+00:00", "payload": state.snapshot_state()}


def render_completion(snapshot, profile, *, char_threshold=1000000, entry_threshold=100):
    settings = SimpleNamespace(persistence_proposal_char_threshold=char_threshold,
                               persistence_proposal_entry_threshold=entry_threshold)
    before = deepcopy(snapshot)
    result = completion_body(snapshot, termination={"type": "finish_noting", "reason": "Reviewed"},
                             summary="Reviewed", settings=settings, profile_home=profile)
    assert snapshot == before
    assert "Retired audit item" not in result
    return result


@pytest.mark.parametrize("threshold,expected", [(5, False), (4, False), (3, True)])
def test_entry_threshold_excludes_archived_audit_bodies(committed, tmp_path, threshold, expected):
    assert sum(map(len, committed["payload"].values())) == 6
    body = render_completion(committed, tmp_path, entry_threshold=threshold)
    assert ("PERSISTENCE PROPOSAL REQUEST" in body) is expected
    if expected:
        assert "and 4 current entries;" in body


@pytest.mark.parametrize("exceeds", [False, True])
def test_character_threshold_remains_independent_of_current_entry_threshold(committed, tmp_path, exceeds):
    rendered = render_notebook(committed, profile_home=tmp_path, model_visible=True)
    body = render_completion(committed, tmp_path, char_threshold=len(rendered) - int(exceeds))
    assert ("PERSISTENCE PROPOSAL REQUEST" in body) is exceeds
    if exceeds:
        assert f"contains {len(rendered)} characters and 4 current entries;" in body


def test_large_current_notebook_still_triggers_character_limit(committed, tmp_path):
    committed["payload"]["work"][0]["fields"]["description"] = "x" * 75096
    body = render_completion(committed, tmp_path, char_threshold=12000, entry_threshold=80)
    assert "PERSISTENCE PROPOSAL REQUEST" in body
    assert "and 4 current entries;" in body
