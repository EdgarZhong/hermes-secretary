"""Task-local semantic Notebook mutations, independent of durable Snapshot storage.

Only the Noting runtime's service may expose these operations. This pure model
does not confer permissions, move pointers, or mutate Schedule runtime rows.
"""

from copy import deepcopy
from datetime import datetime
from typing import Callable
from uuid import uuid4

from secretary.notebook_schedule import (
    SCHEDULE_TYPES,
    canonical_schedule,
    parse_schedule_expression,
    validate_schedule_intent,
)


SECTIONS = ("user", "assistant", "consultation", "persistence")
TYPE_SECTIONS = {
    "user_commitment": "user", "user_reminder": "user",
    "agent_task": "assistant", "watchpoint": "assistant",
    "decision": "consultation", "open_question": "consultation",
    "formulating_insight": "consultation",
    "memory_candidate": "persistence", "rule_candidate": "persistence",
    "skill_candidate": "persistence",
}
REQUIRED_FIELDS = {
    "user_commitment": ("what", "intent"), "user_reminder": ("message",),
    "agent_task": ("task", "purpose"),
    "watchpoint": ("subject", "what_to_watch", "why", "until"),
    "decision": ("decision", "rationale"),
    "open_question": ("question", "why_it_matters"),
    "formulating_insight": ("insight", "basis"),
    # The specification suggests candidate semantic fields, but only requires provenance.
    "memory_candidate": (), "rule_candidate": (), "skill_candidate": (),
}
OPTIONAL_FIELDS = {
    "open_question": ("needed_information",),
    "formulating_insight": ("uncertainty", "what_would_confirm", "what_would_refute"),
    "memory_candidate": ("draft", "why_persist"),
    "rule_candidate": ("draft_rule", "reason", "scope"),
    "skill_candidate": ("capability", "workflow_draft", "why_reusable"),
}
STATUS_TRANSITIONS = {
    "user_commitment": {"pending": ("in_progress", "dropped"),
                        "in_progress": ("done", "dropped"), "done": (), "dropped": ()},
    "user_reminder": {"active": ("delivered", "cancelled"), "delivered": (), "cancelled": ()},
    "agent_task": {"pending": ("running", "failed", "dropped"),
                   "running": ("done", "failed", "dropped"),
                   "done": (), "failed": (), "dropped": ()},
    "watchpoint": {"watching": ("resolved", "dropped"), "resolved": (), "dropped": ()},
    "decision": {"active": ("superseded", "revoked"), "superseded": (), "revoked": ()},
    "open_question": {"open": ("resolved", "dropped"), "resolved": (), "dropped": ()},
    "formulating_insight": {"forming": ("validated", "rejected", "superseded"),
                            "validated": (), "rejected": (), "superseded": ()},
}
ENTRY_KEYS = {"entry_id", "type", "archived", "fields", "status",
              "source_message_identities", "schedule"}


class NotebookValidationError(ValueError):
    """A semantic operation was rejected without changing the working state."""


def section_for_type(entry_type: str) -> str:
    try:
        return TYPE_SECTIONS[entry_type]
    except (KeyError, TypeError) as exc:
        raise NotebookValidationError(f"Unknown Notebook entry type: {entry_type}") from exc


def _validate_fields(entry_type: str, fields: dict) -> None:
    if not isinstance(fields, dict):
        raise NotebookValidationError("Semantic fields must be an object")
    allowed = set(REQUIRED_FIELDS[entry_type]) | set(OPTIONAL_FIELDS.get(entry_type, ()))
    if fields.keys() - allowed:
        raise NotebookValidationError("Unknown semantic fields")
    for key in REQUIRED_FIELDS[entry_type]:
        value = fields.get(key)
        if not isinstance(value, str) or not value.strip():
            raise NotebookValidationError(f"{entry_type} requires non-empty {key}")
    for value in fields.values():
        if not isinstance(value, (str, list)) or isinstance(value, list) and not all(
            isinstance(item, str) for item in value
        ):
            raise NotebookValidationError("Semantic values must be text or lists of text")


class NotebookWorkingState:
    """One Noting task's complete four-section state, never a mutable DB master row."""

    def __init__(
        self, conversation_ref: str, payload: dict | None = None, *,
        validate_source_identity: Callable[[dict], bool] | None = None,
        parse_schedule: Callable[[str], dict] = parse_schedule_expression,
    ):
        if not isinstance(conversation_ref, str) or not conversation_ref:
            raise NotebookValidationError("An owning Conversation Ref is required")
        self.conversation_ref = conversation_ref
        self._validate_source_identity = validate_source_identity
        self._parse_schedule = parse_schedule
        state = deepcopy(payload) if payload is not None else {section: [] for section in SECTIONS}
        self._validate_state(state)
        self._state = state

    def _validate_sources(self, entry: dict) -> None:
        sources = entry.get("source_message_identities", [])
        is_candidate = section_for_type(entry["type"]) == "persistence"
        if not isinstance(sources, list) or is_candidate and not sources:
            raise NotebookValidationError("Candidates require at least one valid source Message Identity")
        for source in sources:
            if not isinstance(source, dict) or set(source) != {"conversation_ref", "message_uid"}:
                raise NotebookValidationError("Source must be a canonical Message Identity")
            if source["conversation_ref"] != self.conversation_ref:
                raise NotebookValidationError("Source must belong to this Conversation")
            if not isinstance(source["message_uid"], str) or not source["message_uid"]:
                raise NotebookValidationError("Source Message UID is required")
            if self._validate_source_identity is None or not self._validate_source_identity(deepcopy(source)):
                raise NotebookValidationError("Source Message Identity is not valid on the current path")

    def _validate_entry(self, entry: dict) -> None:
        if not isinstance(entry, dict) or entry.keys() - ENTRY_KEYS:
            raise NotebookValidationError("Invalid Notebook entry fields")
        entry_type = entry.get("type")
        section_for_type(entry_type)
        if not isinstance(entry.get("entry_id"), str) or not entry["entry_id"]:
            raise NotebookValidationError("Entry ID is required")
        if not isinstance(entry.get("archived"), bool):
            raise NotebookValidationError("Archived must be a boolean")
        _validate_fields(entry_type, entry.get("fields"))
        if entry_type in STATUS_TRANSITIONS:
            if not isinstance(entry.get("status"), str) or entry["status"] not in STATUS_TRANSITIONS[entry_type]:
                raise NotebookValidationError("Invalid status for this entry type")
        elif "status" in entry:
            raise NotebookValidationError("Persistence candidates have no defined status graph")
        self._validate_sources(entry)
        self._validate_entry_schedule(entry)

    def _validate_entry_schedule(self, entry: dict) -> None:
        intent = entry.get("schedule")
        if intent is not None:
            if entry["type"] not in SCHEDULE_TYPES:
                raise NotebookValidationError("This entry type cannot carry a Schedule")
            validate_schedule_intent(intent)
            canonical = intent["canonical_schedule"]
            if canonical["kind"] == "cron":
                parsed = canonical_schedule(canonical["expr"], self._parse_schedule)
                if parsed["kind"] != "cron":
                    raise NotebookValidationError("Canonical cron intent requires a cron expression")
        if entry["type"] == "watchpoint":
            if intent is None or intent["canonical_schedule"]["kind"] != "once":
                raise NotebookValidationError("Watchpoint until requires a one-shot Schedule")
            # Compare absolute horizons, allowing equivalent offsets and descriptive text.
            horizon = canonical_schedule(entry["fields"]["until"], self._parse_schedule)
            if horizon["kind"] != "once" or datetime.fromisoformat(horizon["run_at"]) != datetime.fromisoformat(
                intent["canonical_schedule"]["run_at"].replace("Z", "+00:00")
            ):
                raise NotebookValidationError("Watchpoint Schedule must correspond to until")

    def _validate_state(self, state: dict) -> None:
        if not isinstance(state, dict) or set(state) != set(SECTIONS):
            raise NotebookValidationError("Notebook requires all four semantic sections")
        ids = set()
        for section, entries in state.items():
            if not isinstance(entries, list):
                raise NotebookValidationError("Notebook sections must be entry lists")
            for entry in entries:
                self._validate_entry(entry)
                if section_for_type(entry["type"]) != section or entry["entry_id"] in ids:
                    raise NotebookValidationError("Wrong section or duplicate Notebook entry ID")
                ids.add(entry["entry_id"])

    def show(self) -> dict:
        return deepcopy(self._state)

    def get(self, entry_id: str) -> dict:
        section, index = self._locate(entry_id)
        return deepcopy(self._state[section][index])

    def _locate(self, entry_id: str) -> tuple[str, int]:
        for section, entries in self._state.items():
            for index, entry in enumerate(entries):
                if entry["entry_id"] == entry_id:
                    return section, index
        raise NotebookValidationError(f"Unknown Notebook entry: {entry_id}")

    def _replace(self, entry: dict) -> dict:
        self._validate_entry(entry)
        section, index = self._locate(entry["entry_id"])
        self._state[section][index] = deepcopy(entry)
        return deepcopy(entry)

    def create(
        self, entry_type: str, fields: dict, *, status: str | None = None,
        source_message_identities: list[dict] | None = None,
    ) -> dict:
        section = section_for_type(entry_type)
        entry = {"entry_id": f"entry_{uuid4().hex}", "type": entry_type,
                 "archived": False, "fields": deepcopy(fields)}
        if entry_type in STATUS_TRANSITIONS:
            entry["status"] = status if status is not None else next(iter(STATUS_TRANSITIONS[entry_type]))
        elif status is not None:
            raise NotebookValidationError("Persistence candidates have no defined status graph")
        if source_message_identities is not None:
            entry["source_message_identities"] = deepcopy(source_message_identities)
        if entry_type == "watchpoint" and isinstance(fields, dict) and fields.get("until"):
            entry["schedule"] = self._new_intent(fields["until"])
            if entry["schedule"]["canonical_schedule"]["kind"] == "once":
                entry["fields"]["until"] = entry["schedule"]["canonical_schedule"]["run_at"]
        self._validate_entry(entry)
        self._state[section].append(deepcopy(entry))
        return deepcopy(entry)

    def edit(
        self, entry_id: str, fields: dict, *, source_message_identities: list[dict] | None = None,
    ) -> dict:
        entry = self.get(entry_id)
        if not isinstance(fields, dict):
            raise NotebookValidationError("Semantic edits must be an object")
        entry["fields"].update(deepcopy(fields))
        if source_message_identities is not None:
            entry["source_message_identities"] = deepcopy(source_message_identities)
        if entry["type"] == "watchpoint" and "until" in fields:
            entry["schedule"] = self._new_intent(fields["until"])
            if entry["schedule"]["canonical_schedule"]["kind"] == "once":
                entry["fields"]["until"] = entry["schedule"]["canonical_schedule"]["run_at"]
        return self._replace(entry)

    def archive(self, entry_id: str) -> dict:
        entry = self.get(entry_id)
        entry["archived"] = True
        return self._replace(entry)

    def restore(self, entry_id: str) -> dict:
        entry = self.get(entry_id)
        entry["archived"] = False
        return self._replace(entry)

    def transition_status(self, entry_id: str, status: str) -> dict:
        entry = self.get(entry_id)
        transitions = STATUS_TRANSITIONS.get(entry["type"], {})
        if status not in transitions.get(entry.get("status"), ()):
            raise NotebookValidationError("Illegal Notebook status transition")
        entry["status"] = status
        return self._replace(entry)

    def _new_intent(self, expression: str) -> dict:
        return {"canonical_schedule": canonical_schedule(expression, self._parse_schedule), "cancelled": False}

    def _set_schedule(self, entry_id: str, expression: str, *, update: bool) -> dict:
        entry = self.get(entry_id)
        if entry["type"] not in SCHEDULE_TYPES:
            raise NotebookValidationError("This entry type cannot carry a Schedule")
        existing = entry.get("schedule")
        if update and existing is None or not update and existing is not None and not existing["cancelled"]:
            raise NotebookValidationError("Schedule intent does not match create/update operation")
        entry["schedule"] = self._new_intent(expression)
        if entry["type"] == "watchpoint":
            if entry["schedule"]["canonical_schedule"]["kind"] != "once":
                raise NotebookValidationError("Watchpoint until requires a one-shot Schedule")
            entry["fields"]["until"] = entry["schedule"]["canonical_schedule"]["run_at"]
        return self._replace(entry)

    def schedule_create(self, entry_id: str, expression: str) -> dict:
        return self._set_schedule(entry_id, expression, update=False)

    def schedule_update(self, entry_id: str, expression: str) -> dict:
        return self._set_schedule(entry_id, expression, update=True)

    def schedule_cancel(self, entry_id: str) -> dict:
        entry = self.get(entry_id)
        if entry.get("schedule") is None:
            raise NotebookValidationError("Entry has no Schedule intent")
        entry["schedule"]["cancelled"] = True
        return self._replace(entry)
