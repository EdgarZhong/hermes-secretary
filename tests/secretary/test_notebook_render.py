"""AI JSON and normal human slash text keep different 02 §3.5/3.6 contracts."""

from secretary.notebook_model import NotebookWorkingState
from secretary.notebook_render import render_notebook, show_notebook


def test_null_is_explicit_and_not_an_empty_snapshot():
    assert show_notebook(None) is None
    assert "no Notebook Snapshot yet" in render_notebook(None)


def test_human_view_shows_timestamp_and_complete_semantics_without_anchor_or_pointer():
    model = NotebookWorkingState("conv_source", validate_source_identity=lambda source: True)
    commitment = model.create("user_commitment", {"what": "send report", "intent": "request approval"})
    model.schedule_create(commitment["entry_id"], "2030-10-07T12:00:00Z")
    model.create("agent_task", {"task": "draft slides", "purpose": "team review"})
    decision = model.create("decision", {"decision": "ship Friday", "rationale": "test runway"})
    model.archive(decision["entry_id"])
    model.create("skill_candidate", {"capability": "triage", "workflow_draft": ["logs", "isolate"]},
                 source_message_identities=[{"conversation_ref": "conv_source", "message_uid": "hidden_anchor"}])
    snapshot = {"snapshot_id": "hidden_pointer", "conversation_ref": "conv_source",
                "anchor_message_uid": "hidden_anchor", "created_at": "2026-10-07T17:23:45+08:00",
                "trigger_type": "idle", "runtime_profile": "NOTING", "payload": model.show()}
    rendered = render_notebook(snapshot)
    for text in (snapshot["created_at"], "user", "assistant", "consultation", "persistence",
                 "send report", "request approval", "draft slides", "team review", "ship Friday",
                 "test runway", "archived", "triage", "logs", "isolate", "Schedule", "2030-10-07"):
        assert text in rendered
    assert "hidden_anchor" not in rendered
    assert "hidden_pointer" not in rendered
    structured = show_notebook(snapshot)
    assert structured == snapshot
    assert structured["anchor_message_uid"] == "hidden_anchor"
    structured["payload"]["user"].clear()
    assert snapshot["payload"]["user"]


def test_committed_empty_snapshot_still_has_created_at_and_four_sections():
    snapshot = {"created_at": "2026-10-07T09:00:00Z", "payload": NotebookWorkingState("conv_a").show()}
    rendered = render_notebook(snapshot)
    assert snapshot["created_at"] in rendered
    assert rendered.count("(no entries)") == 4
    assert "no Notebook Snapshot yet" not in rendered
