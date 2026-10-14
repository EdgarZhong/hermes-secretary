"""AI JSON and normal human slash text keep different 02 §3.5/3.6 contracts."""

from secretary.notebook_model import NotebookWorkingState
from secretary.notebook_render import render_notebook, show_notebook


def test_display_times_hide_fraction_without_mutating_schedule_or_source_range():
    from copy import deepcopy

    exact = "2030-10-07T12:00:00.987654+08:00"
    source_range = {"start_time": "2026-10-07T12:00:00.123456+08:00",
                    "end_time": "2026-10-07T12:00:00.654321+08:00"}
    model = NotebookWorkingState("conv_source")
    model.create("watchpoint", {"subject": "report", "what_to_watch": "response", "why": "deadline", "until": exact})
    model.create("memory_candidate", {"draft": "precise evidence"}, source_time_range=source_range)
    snapshot = {"created_at": "2026-10-07T17:23:45.999999+08:00", "anchor_message_uid": "source", "payload": model.show()}
    before = deepcopy(snapshot)
    view = show_notebook(snapshot)
    watchpoint = view["assistant"][0]
    assert view["last_update_time"] == "2026-10-07T17:23:45+08:00"
    assert watchpoint["schedule"]["canonical_schedule"]["run_at"] == "2030-10-07T12:00:00+08:00"
    assert watchpoint["fields"]["until"] == "2030-10-07T12:00:00+08:00"
    assert view["persistence"][0]["source_time_range"] == source_range
    assert snapshot == before


def test_null_is_explicit_and_not_an_empty_snapshot():
    assert show_notebook(None) is None
    assert "no Notebook Snapshot yet" in render_notebook(None)


def test_human_view_shows_timestamp_and_complete_semantics_without_anchor_or_pointer():
    model = NotebookWorkingState("conv_source", validate_source_identity=lambda source: True)
    commitment = model.create("user_commitment", {"what": "send report", "intent": "request approval"})
    model.schedule_update(commitment["entry_id"], "2030-10-07T12:00:00Z")
    model.create("secretary_task", {"task": "draft slides", "purpose": "team review"},
                 expression="2030-10-07T12:00:00+00:00", delivery_mode="deferred")
    decision = model.create("decision", {"decision": "ship Friday", "rationale": "test runway"})
    model.archive(decision["entry_id"])
    model.create("skill_candidate", {"capability": "triage", "workflow_draft": ["logs", "isolate"]},
                 source_message_identities=[{"conversation_ref": "conv_source", "message_uid": "hidden_anchor"}])
    snapshot = {"snapshot_id": "hidden_pointer", "conversation_ref": "conv_source",
                "anchor_message_uid": "hidden_anchor", "created_at": "2026-10-07T17:23:45+08:00",
                "trigger_type": "idle", "runtime_profile": "NOTING", "future_internal_audit": "never_expose",
                "termination": {"type": "forced"}, "payload": model.show()}
    rendered = render_notebook(snapshot)
    for text in (snapshot["created_at"], "user", "assistant", "consultation", "persistence",
                 "send report", "request approval", "draft slides", "team review", "triage", "logs", "isolate", "Schedule", "2030-10-07"):
        assert text in rendered
    assert "ship Friday" not in rendered
    assert "archived" not in rendered
    assert "hidden_anchor" not in rendered
    assert "hidden_pointer" not in rendered
    structured = show_notebook(snapshot)
    assert set(structured) == {"last_update_time", "anchor_message_uid", "user", "assistant", "consultation", "persistence"}
    assert structured["last_update_time"] == snapshot["created_at"]
    assert structured["anchor_message_uid"] == snapshot["anchor_message_uid"]
    assert structured["user"][0]["schedule"]["canonical_schedule"]["display"] == "once at 2030-10-07T12:00:00+00:00"
    assert structured["user"][0]["fields"] == snapshot["payload"]["user"][0]["fields"]
    assert structured["persistence"] == snapshot["payload"]["persistence"]
    structured["user"].clear()
    assert snapshot["payload"]["user"]


def test_committed_empty_snapshot_still_has_created_at_and_four_sections():
    snapshot = {"created_at": "2026-10-07T09:00:00Z", "payload": NotebookWorkingState("conv_a").show()}
    rendered = render_notebook(snapshot)
    assert snapshot["created_at"] in rendered
    assert rendered.count("(no entries)") == 4
    assert "no Notebook Snapshot yet" not in rendered
