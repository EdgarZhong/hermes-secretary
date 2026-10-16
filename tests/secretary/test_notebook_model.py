"""Retired ontology boundaries; current type/status matrix lives in test_r3_notebook."""

from copy import deepcopy

import pytest

from secretary.notebook_model import NotebookValidationError, NotebookWorkingState


@pytest.mark.parametrize("entry_type", ["user_reminder", "user_commitment", "secretary_task", "watchpoint", "open_question", "memory_candidate", "skill_candidate", "rule_candidate"])
def test_retired_types_cannot_be_created_or_restored(entry_type):
    model = NotebookWorkingState("conv_source", validate_source_identity=lambda value: True)
    before = model.snapshot_state()
    with pytest.raises(NotebookValidationError):
        model.create(entry_type, {"description": "old shape"}, source_message_identities=[{"conversation_ref": "conv_source", "message_uid": "m"}])
    assert model.snapshot_state() == before
    with pytest.raises(NotebookValidationError):
        NotebookWorkingState("conv_source", {"user": [], "assistant": [], "consultation": [], "persistence": []})


def test_cross_owner_is_rejected_even_by_permissive_validator():
    model = NotebookWorkingState("conv_owner", validate_source_identity=lambda source: True)
    with pytest.raises(NotebookValidationError):
        model.create("matter", {"description": "report", "completion_condition": "done"},
                     source_message_identities=[{"conversation_ref": "conv_other", "message_uid": "m"}])
    assert model.show()["work"] == []


def test_complete_state_loading_is_detached_and_rejects_invalid_sections():
    model = NotebookWorkingState("conv_owner", validate_source_identity=lambda source: True)
    model.create("matter", {"description": "report", "completion_condition": "done"},
                 source_message_identities=[{"conversation_ref": "conv_owner", "message_uid": "m"}])
    saved = model.snapshot_state(); before = deepcopy(saved)
    restored = NotebookWorkingState("conv_owner", saved, validate_source_identity=lambda source: True)
    saved["work"][0]["fields"]["description"] = "mutated"
    assert restored.snapshot_state() == before
    for payload in ({"work": []}, {**before, "persistence": []}, {**before, "work": [1]}):
        with pytest.raises(NotebookValidationError):
            NotebookWorkingState("conv_owner", payload, validate_source_identity=lambda source: True)
