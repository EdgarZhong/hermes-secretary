"""Notebook semantics from 02 §2.5/3.7/3.8; durable service wiring is separate."""

from copy import deepcopy

import pytest

from secretary.notebook_model import NotebookValidationError, NotebookWorkingState
from secretary.notebook_schedule import schedule_delivery_semantics


REF = "conv_owner"
SOURCE = {"conversation_ref": REF, "message_uid": "ordinary_source"}
HORIZON = "2030-10-07T12:00:00+00:00"
FIELDS = {
    "user_commitment": {"what": "send proposal", "intent": "get review"},
    "user_reminder": {"message": "submit report"},
    "agent_task": {"task": "draft plan", "purpose": "prepare launch"},
    "watchpoint": {"subject": "release", "what_to_watch": "errors", "why": "reliability", "until": HORIZON},
    "decision": {"decision": "use sqlite", "rationale": "local atomic writes"},
    "open_question": {"question": "which port?", "why_it_matters": "deployment"},
    "formulating_insight": {"insight": "retries hide failures", "basis": "three incidents"},
    "memory_candidate": {"draft": "user prefers mornings", "why_persist": "repeated preference"},
    "rule_candidate": {"draft_rule": "review before publish", "reason": "user request", "scope": "reports"},
    "skill_candidate": {"capability": "triage", "workflow_draft": ["read logs", "isolate cause"], "why_reusable": "weekly"},
}
TYPES_AND_SECTIONS = [
    ("user_commitment", "user"), ("user_reminder", "user"),
    ("agent_task", "assistant"), ("watchpoint", "assistant"),
    ("decision", "consultation"), ("open_question", "consultation"),
    ("formulating_insight", "consultation"),
    ("memory_candidate", "persistence"), ("rule_candidate", "persistence"),
    ("skill_candidate", "persistence"),
]


@pytest.fixture
def notebook():
    # A task's callback is supplied by the later DB service, not syntax recognition.
    return NotebookWorkingState(REF, validate_source_identity=lambda source: source == SOURCE)


def create(notebook, entry_type, **kwargs):
    sources = [SOURCE] if entry_type.endswith("_candidate") else None
    return notebook.create(entry_type, FIELDS[entry_type], source_message_identities=sources, **kwargs)


@pytest.mark.parametrize("entry_type,section", TYPES_AND_SECTIONS)
def test_ten_types_complete_mutations_and_isolation(notebook, entry_type, section):
    original = create(notebook, entry_type)
    assert notebook.show()[section] == [original]
    assert "section" not in original
    original["fields"].clear()
    entry = notebook.get(original["entry_id"])
    assert entry["fields"] == FIELDS[entry_type]
    key = next(iter(FIELDS[entry_type]))
    edited = notebook.edit(entry["entry_id"], {key: "updated semantic text"})
    assert edited["fields"][key] == "updated semantic text"
    assert edited == notebook.get(entry["entry_id"])
    archived = notebook.archive(entry["entry_id"])
    assert archived["archived"] is True
    assert archived["fields"] == edited["fields"]
    restored = notebook.restore(entry["entry_id"])
    assert restored == edited


REQUIRED = [
    ("user_commitment", "what"), ("user_commitment", "intent"),
    ("user_reminder", "message"), ("agent_task", "task"), ("agent_task", "purpose"),
    ("watchpoint", "subject"), ("watchpoint", "what_to_watch"),
    ("watchpoint", "why"), ("watchpoint", "until"),
    ("decision", "decision"), ("decision", "rationale"),
    ("open_question", "question"), ("open_question", "why_it_matters"),
    ("formulating_insight", "insight"), ("formulating_insight", "basis"),
]


@pytest.mark.parametrize("entry_type,key", REQUIRED)
@pytest.mark.parametrize("value", [None, "", "   "])
def test_required_fields_reject_without_partial_creation(notebook, entry_type, key, value):
    fields = {**FIELDS[entry_type], key: value}
    before = notebook.show()
    with pytest.raises(ValueError):
        notebook.create(entry_type, fields)
    assert notebook.show() == before
    entry = create(notebook, entry_type)
    before = notebook.show()
    with pytest.raises(ValueError):
        notebook.edit(entry["entry_id"], {key: value})
    assert notebook.show() == before


TRANSITIONS = [
    ("user_commitment", "pending", "in_progress"), ("user_commitment", "in_progress", "done"),
    ("user_commitment", "pending", "dropped"), ("user_commitment", "in_progress", "dropped"),
    ("user_reminder", "active", "delivered"), ("user_reminder", "active", "cancelled"),
    ("agent_task", "pending", "running"), ("agent_task", "running", "done"),
    ("agent_task", "pending", "failed"), ("agent_task", "running", "failed"),
    ("agent_task", "pending", "dropped"), ("agent_task", "running", "dropped"),
    ("watchpoint", "watching", "resolved"), ("watchpoint", "watching", "dropped"),
    ("decision", "active", "superseded"), ("decision", "active", "revoked"),
    ("open_question", "open", "resolved"), ("open_question", "open", "dropped"),
    ("formulating_insight", "forming", "validated"),
    ("formulating_insight", "forming", "rejected"),
    ("formulating_insight", "forming", "superseded"),
]


@pytest.mark.parametrize("entry_type,start,end", TRANSITIONS)
def test_all_defined_status_edges(notebook, entry_type, start, end):
    entry = create(notebook, entry_type, status=start)
    result = notebook.transition_status(entry["entry_id"], end)
    assert result["status"] == end
    assert result == notebook.get(entry["entry_id"])
    before = notebook.show()
    with pytest.raises(NotebookValidationError):
        notebook.transition_status(entry["entry_id"], start)
    assert notebook.show() == before


@pytest.mark.parametrize("entry_type,section", TYPES_AND_SECTIONS)
def test_invalid_status_and_reserved_edits_atomic(notebook, entry_type, section):
    entry = create(notebook, entry_type)
    before = notebook.show()
    with pytest.raises(ValueError):
        notebook.transition_status(entry["entry_id"], "invented_status")
    for key in ("entry_id", "type", "section", "status", "archived", "next_run_at", "claim"):
        with pytest.raises(ValueError):
            notebook.edit(entry["entry_id"], {key: "forged"})
        assert notebook.show() == before


@pytest.mark.parametrize("entry_type", ["memory_candidate", "rule_candidate", "skill_candidate"])
def test_candidate_sources_require_real_owner_and_path(notebook, entry_type):
    for sources in ([], [dict(SOURCE, message_uid="syntactically_valid_but_missing")],
                    [SOURCE, dict(SOURCE, message_uid="missing_second_source")],
                    [dict(SOURCE, conversation_ref="conv_other")],
                    [{"session_id": "physical", "message_uid": "ordinary_source"}]):
        before = notebook.show()
        with pytest.raises(ValueError):
            notebook.create(entry_type, {}, source_message_identities=sources)
        assert notebook.show() == before
    candidate = notebook.create(entry_type, {}, source_message_identities=[SOURCE])
    assert candidate["source_message_identities"] == [SOURCE]
    with pytest.raises(ValueError):
        NotebookWorkingState(REF).create(entry_type, {}, source_message_identities=[SOURCE])
    before = notebook.show()
    with pytest.raises(ValueError):
        notebook.edit(candidate["entry_id"], {}, source_message_identities=[])
    assert notebook.show() == before


def test_cross_owner_is_rejected_even_by_permissive_validator():
    notebook = NotebookWorkingState(REF, validate_source_identity=lambda source: True)
    with pytest.raises(ValueError):
        notebook.create("memory_candidate", {}, source_message_identities=[dict(SOURCE, conversation_ref="other")])


@pytest.mark.parametrize("entry_type,end", [
    ("user_commitment", "done"), ("agent_task", "done"), ("watchpoint", "active"),
])
def test_status_shortcuts_are_not_legal_transitions(notebook, entry_type, end):
    entry = create(notebook, entry_type)
    before = notebook.show()
    with pytest.raises(ValueError):
        notebook.transition_status(entry["entry_id"], end)
    assert notebook.show() == before


@pytest.mark.parametrize("entry_type,delivery", [
    ("user_commitment", "system_reminder"), ("agent_task", "system_reminder"),
    ("user_reminder", "user_reminder"), ("watchpoint", "system_reminder"),
])
def test_schedule_lifecycle_and_delivery_class(notebook, entry_type, delivery):
    entry = create(notebook, entry_type)
    if entry_type != "watchpoint":
        entry = notebook.schedule_create(entry["entry_id"], "every 30m")
    assert schedule_delivery_semantics(entry) == delivery
    changed = notebook.schedule_update(entry["entry_id"], HORIZON)
    assert changed["schedule"]["canonical_schedule"]["run_at"] == HORIZON
    assert changed == notebook.get(entry["entry_id"])
    assert schedule_delivery_semantics(notebook.archive(entry["entry_id"])) is None
    assert schedule_delivery_semantics(notebook.restore(entry["entry_id"])) == delivery
    cancelled = notebook.schedule_cancel(entry["entry_id"])
    assert cancelled["schedule"]["cancelled"] is True
    assert schedule_delivery_semantics(cancelled) is None
    recreated = notebook.schedule_create(entry["entry_id"], HORIZON)
    assert schedule_delivery_semantics(recreated) == delivery


@pytest.mark.parametrize("entry_type,status", [
    ("user_commitment", "dropped"), ("agent_task", "failed"),
    ("user_reminder", "delivered"), ("watchpoint", "resolved"),
])
def test_terminal_status_cancels_runtime_action_but_preserves_intent(notebook, entry_type, status):
    entry = create(notebook, entry_type)
    if entry_type != "watchpoint":
        entry = notebook.schedule_create(entry["entry_id"], HORIZON)
    terminal = notebook.transition_status(entry["entry_id"], status)
    assert terminal["schedule"] == entry["schedule"]
    assert schedule_delivery_semantics(terminal) is None


@pytest.mark.parametrize("entry_type", ["decision", "open_question", "formulating_insight",
                                      "memory_candidate", "rule_candidate", "skill_candidate"])
def test_unsupported_schedule_types_rejected(notebook, entry_type):
    entry = create(notebook, entry_type)
    before = notebook.show()
    with pytest.raises(ValueError):
        notebook.schedule_create(entry["entry_id"], HORIZON)
    assert notebook.show() == before


def test_watchpoint_horizon_rejects_recurring_and_tracks_edits(notebook):
    entry = create(notebook, "watchpoint")
    for mutation in (lambda: notebook.schedule_update(entry["entry_id"], "every 1h"),
                     lambda: notebook.edit(entry["entry_id"], {"until": "every 1h"})):
        before = notebook.show()
        with pytest.raises(ValueError):
            mutation()
        assert notebook.show() == before
    edited = notebook.edit(entry["entry_id"], {"until": "2031-01-01T09:00:00Z"})
    assert edited["fields"]["until"] == edited["schedule"]["canonical_schedule"]["run_at"]
    assert edited["schedule"]["canonical_schedule"]["kind"] == "once"


def test_relative_watchpoint_horizon_is_frozen(notebook):
    entry = notebook.create("watchpoint", {**FIELDS["watchpoint"], "until": "in 30m"})
    assert entry["fields"]["until"] == entry["schedule"]["canonical_schedule"]["run_at"]
    assert notebook.archive(entry["entry_id"])["schedule"] == entry["schedule"]


def test_illegal_schedule_operation_and_runtime_forgery_are_atomic(notebook):
    entry = create(notebook, "user_reminder")
    with pytest.raises(ValueError):
        notebook.schedule_update(entry["entry_id"], HORIZON)
    with pytest.raises(ValueError):
        notebook.schedule_cancel(entry["entry_id"])
    scheduled = notebook.schedule_create(entry["entry_id"], "0 9 * * *")
    assert scheduled["schedule"]["canonical_schedule"]["kind"] == "cron"
    before = notebook.show()
    for expression in ("not a schedule", {"kind": "once", "next_run_at": HORIZON}):
        with pytest.raises(ValueError):
            notebook.schedule_update(entry["entry_id"], expression)
        assert notebook.show() == before
    with pytest.raises(ValueError):
        notebook.schedule_create(entry["entry_id"], HORIZON)
    payload = notebook.show()
    payload["user"][0]["schedule"]["claim"] = "forged"
    with pytest.raises(ValueError):
        NotebookWorkingState(REF, payload)


@pytest.mark.parametrize("schedule", [
    {"kind": "cron", "expr": "bad expression"},
    {"kind": "cron", "expr": "every 30m"},
    {"kind": "once", "run_at": "2030-10-07T12:00:00"},
    {"kind": "interval", "minutes": 0},
    {"kind": "interval", "minutes": True},
    {"kind": "once", "run_at": HORIZON, "delivery_semantics": "forged"},
])
def test_invalid_stored_canonical_schedule_rejected(notebook, schedule):
    create(notebook, "user_reminder")
    payload = notebook.show()
    payload["user"][0]["schedule"] = {"canonical_schedule": schedule, "cancelled": False}
    with pytest.raises(ValueError):
        NotebookWorkingState(REF, payload)


def test_complete_state_loading_is_detached_and_rejects_invalid_sections(notebook):
    entry = create(notebook, "user_commitment")
    payload = notebook.show()
    second = NotebookWorkingState(REF, payload)
    payload["user"][0]["fields"]["what"] = "caller mutation"
    second.edit(entry["entry_id"], {"what": "second task"})
    assert notebook.get(entry["entry_id"])["fields"]["what"] == "send proposal"
    wrong = deepcopy(notebook.show())
    wrong["assistant"] = wrong.pop("user")
    with pytest.raises(ValueError):
        NotebookWorkingState(REF, wrong)
    duplicate = notebook.show()
    duplicate["user"].append(entry)
    with pytest.raises(ValueError):
        NotebookWorkingState(REF, duplicate)
