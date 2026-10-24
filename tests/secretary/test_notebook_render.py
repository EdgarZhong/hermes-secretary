"""Complete Snapshot projections retain public identity and exclude audit/archive."""

from copy import deepcopy
from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from secretary.notebook_model import NotebookWorkingState
from secretary.notebook_render import render_notebook, show_notebook

REF = "conv_source"
RANGE = {"start_time": "2026-10-07T12:00:00.123456+08:00", "end_time": "2026-10-07T12:00:00.654321+08:00"}
DISPLAY_RANGE = {"start_time": "2026-10-07T12:00:00+08:00", "end_time": "2026-10-07T12:00:00+08:00"}


@pytest.fixture
def profile(tmp_path):
    (tmp_path / "config.yaml").write_text("timezone: Asia/Shanghai\n")
    return tmp_path


def snapshot():
    model = NotebookWorkingState(REF, validate_source_range=lambda value: value == RANGE)
    entry = model.create("matter", {"description": "send report", "completion_condition": "reviewed"}, source_time_range=RANGE)["entry"]
    model.create("candidate", {"description": "precise evidence", "targets": ["memory"], "notebook_refs": [entry["entry_id"]], "source_types": ["matter"]})
    return {"snapshot_id": "pointer", "conversation_ref": REF, "created_at": "2026-10-07T17:23:45.999999+08:00", "anchor_message_uid": "source", "payload": model.show()}


def test_display_time_does_not_rewrite_source_range_or_snapshot(profile):
    saved = snapshot()
    # Preserve the historical single-range payload as immutable input evidence.
    source = saved["payload"]["work"][0]
    source["source_time_range"] = source.pop("source_time_ranges")[0]
    before = deepcopy(saved)
    view = show_notebook(saved, profile_home=profile)
    assert view["created_at"] == "2026-10-07T17:23:45+08:00"
    assert view["payload"]["work"][0]["source_time_ranges"] == [DISPLAY_RANGE]
    assert "source_time_range" not in view["payload"]["work"][0]
    assert saved == before


def test_empty_view_is_success_with_bound_owner_and_explicit_null_snapshot():
    view = show_notebook(None, conversation_ref=REF)
    assert view == {"success": True, "conversation_ref": REF, "view_kind": "snapshot", "snapshot_id": None,
                    "coverage": None, "payload": {section: [] for section in ("work", "situations", "discussion", "candidates")}}
    assert "no Notebook Snapshot yet" in render_notebook(None)


def test_human_and_model_views_are_complete_and_exclude_termination_audit(profile):
    saved = snapshot()
    saved["termination"] = {"type": "forced"}; saved["future_internal_audit"] = "never_expose"
    text = render_notebook(saved, profile_home=profile)
    for value in ("work", "situations", "discussion", "candidates", "send report", "reviewed", "precise evidence", "candidate_refs", "entry_id", "version_id"):
        assert value in text
    assert "forced" not in text and "never_expose" not in text
    assert saved["snapshot_id"] not in text
    assert "Coverage anchor:" not in text and "Snapshot:" not in text
    assert "source_time_ranges" in text and DISPLAY_RANGE["start_time"] in text
    view = show_notebook(saved, profile_home=profile)
    assert view["coverage"] == {"anchor_message_uid": "source"}
    assert view["snapshot_id"] == "pointer"
    times = {"created_at", "updated_at", "last_processed_at", "source_time_ranges", "evidence_time"}
    sources = {"source_message_identities", "source_message_uids"}
    for section, entries in saved["payload"].items():
        for original, projected in zip(entries, view["payload"][section], strict=True):
            assert {key: value for key, value in projected.items() if key not in times | sources} == {
                key: value for key, value in original.items() if key not in times | sources}
            assert projected["source_message_uids"] == [source["message_uid"] for source in original["source_message_identities"]]
            assert "source_message_identities" not in projected
            assert projected["source_time_ranges"] == [DISPLAY_RANGE for _interval in original["source_time_ranges"]]
            assert projected["evidence_time"] == [DISPLAY_RANGE]
            for key in times - {"source_time_ranges", "evidence_time"}:
                assert projected[key] == (None if original[key] is None else
                    datetime.fromisoformat(original[key]).astimezone(ZoneInfo("Asia/Shanghai")).replace(microsecond=0).isoformat())
    assert "termination" not in view and "future_internal_audit" not in view
    view["payload"]["work"].clear()
    assert saved["payload"]["work"]


def test_committed_empty_snapshot_has_created_time_and_four_sections():
    saved = snapshot(); saved["payload"] = NotebookWorkingState(REF).show()
    text = render_notebook(saved)
    assert "2026-10-07T17:23:45+08:00" in text and text.count("(no entries)") == 4
    assert "no Notebook Snapshot yet" not in text
