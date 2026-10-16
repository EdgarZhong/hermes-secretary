"""Round-three Notebook contracts; no persistence, scheduling or model calls.

The schema is 07 sections 4 and 7. Evidence support/approval is a model duty;
these validators enforce structure, current references and provenance addresses.
"""

from copy import deepcopy
from datetime import datetime

SECTIONS = ("work", "situations", "discussion", "candidates")
TYPE_SECTIONS = {
    "matter": "work", "action": "work",
    "situation": "situations", "implicit_gap": "situations",
    "question": "discussion", "insight": "discussion", "decision": "discussion",
    "candidate": "candidates",
}
REQUIRED_FIELDS = {
    "matter": ("description", "completion_condition"),
    "action": ("description", "owner", "completion_condition"),
    "situation": ("description", "subjects", "time_context"),
    "implicit_gap": ("description", "situation_ref", "missing_information", "impact", "resolution_condition"),
    "question": ("description", "unresolved_points"),
    "insight": ("description", "certainty", "qualification"),
    "decision": ("description", "scope", "valid_when", "ends_when"),
    "candidate": ("description", "targets", "notebook_refs", "source_types"),
}
OPTIONAL_FIELDS = {
    "matter": ("blocker", "last_progress_time"),
    "action": ("blocker", "last_progress_time"),
    "situation": (), "implicit_gap": (),
    "question": ("current_answer", "last_discussion_time"),
    "insight": (), "decision": ("rationale",), "candidate": ("stage_evidence",),
}
COMMON_FIELDS = {"domains", "external_refs", "evidence_time", "processing_note"}
ARRAY_FIELDS = {"domains", "external_refs", "subjects", "targets", "notebook_refs", "source_types"}
EVIDENCE_TIMES = {"evidence_time", "last_progress_time", "last_discussion_time"}
STATUSES = {
    "matter": ("in_progress", "paused", "completed", "terminated"),
    "action": ("pending", "in_progress", "waiting", "paused", "completed", "terminated"),
    "situation": ("current", "expired"),
    "implicit_gap": ("missing", "resolved", "invalid"),
    "question": ("open", "answered", "withdrawn"),
    "insight": ("current", "revised", "withdrawn"),
    "decision": ("active", "superseded", "revoked", "expired"),
    "candidate": ("proposed", "awaiting_approval", "approved", "awaiting_result"),
}
RELATION_KINDS = {"part_of", "depends_on", "based_on", "supersedes", "related_to"}
SOURCE_TYPES = {"matter", "action", "situation", "question", "insight", "decision"}
ENTRY_KEYS = {
    "entry_id", "version_id", "entry_type", "fields", "status", "relations",
    "source_message_identities", "source_time_range", "created_at", "updated_at",
    "last_processed_at", "archived",
}
CHANGE_KEYS = {"fields", "status", "relations", "source_message_identities", "source_time_range"}


class NotebookValidationError(ValueError):
    """A refused operation, with 07's model-facing error and correction guidance."""

    def __init__(self, message, *, code="invalid_argument", field=None,
                 next_action="Correct the named input; other fields remain unchanged.", details=None):
        super().__init__(message)
        self.code = code
        self.field = field
        self.next_action = next_action
        self.details = deepcopy(details)

    def as_result(self):
        error = {"code": self.code, "message": str(self), "next_action": self.next_action}
        if self.field is not None:
            error["field"] = self.field
        if self.details is not None:
            error["details"] = deepcopy(self.details)
        return {"success": False, "error": error}


def require_text(value, field):
    if not isinstance(value, str) or not value.strip():
        raise NotebookValidationError(f"Invalid {field}: expected nonempty text.", field=field)


def section_for_type(entry_type):
    if not isinstance(entry_type, str) or entry_type not in TYPE_SECTIONS:
        raise NotebookValidationError("Unknown Notebook entry type.", field="entry_type")
    return TYPE_SECTIONS[entry_type]


def parse_time(value, field):
    try:
        if not isinstance(value, str):
            raise ValueError("not text")
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            raise ValueError("no timezone")
        return parsed
    except (TypeError, ValueError, OverflowError) as exc:
        raise NotebookValidationError(
            f"Invalid {field}: expected a timezone-aware ISO 8601 timestamp.", field=field,
            next_action="Supply the evidenced time with its timezone, or null when unknown.",
        ) from exc


def validate_source_range(value):
    if not isinstance(value, dict) or set(value) != {"start_time", "end_time"}:
        raise NotebookValidationError(
            "Source time range requires both bounds.", field="source_time_range",
            next_action="Supply start_time and end_time together, or null when another source remains.",
        )
    start, end = (parse_time(value[key], f"source_time_range.{key}")
                  for key in ("start_time", "end_time"))
    if start > end:
        raise NotebookValidationError("Source time range is reversed.", field="source_time_range")
    return start, end


def unique_strings(value, field):
    if not isinstance(value, list):
        raise NotebookValidationError("Expected a complete replacement array.", field=field,
                                      next_action="Include all values to retain; use [] to clear an optional array.")
    for item in value:
        require_text(item, field)
    if len(value) != len(set(value)):
        raise NotebookValidationError("Duplicate array values are not allowed.", field=field)


def validate_fields(entry_type, fields):
    section_for_type(entry_type)
    if not isinstance(fields, dict):
        raise NotebookValidationError("Expected a fields object.", field="fields")
    required = set(REQUIRED_FIELDS[entry_type])
    allowed = required | set(OPTIONAL_FIELDS[entry_type]) | COMMON_FIELDS
    if fields.keys() - allowed:
        raise NotebookValidationError("Fields do not belong to this entry type.", field="fields",
                                      details={"unknown_fields": sorted(fields.keys() - allowed)})
    for key in required:
        if key not in fields:
            raise NotebookValidationError(f"Missing required field {key}.", field=f"fields.{key}")
    for key, value in fields.items():
        field = f"fields.{key}"
        if key in ARRAY_FIELDS:
            unique_strings(value, field)
            if key in {"subjects", "targets"} and not value:
                raise NotebookValidationError("This required array cannot be empty.", field=field)
            if key == "targets" and set(value) - {"memory", "skill", "rule"}:
                raise NotebookValidationError("Unknown persistence target.", field=field)
            if key == "source_types" and set(value) - SOURCE_TYPES:
                raise NotebookValidationError("Invalid source label; implicit_gap maps to situation.", field=field)
        elif key in EVIDENCE_TIMES:
            if value is not None:
                parse_time(value, field)
        elif key in required:
            require_text(value, field)
        elif value is not None and not isinstance(value, str):
            raise NotebookValidationError("Expected optional text or null.", field=field)


def same_source_claim(left, right):
    """An inherited citation license is not transferable to a different claim.

    Administrative processing and archiving do not change the supported claim.
    Any content/status/relationship/provenance change must use current sources.
    This is a structural safeguard, not an attempt to infer semantic entailment.
    """
    def claim(entry):
        fields = deepcopy(entry["fields"])
        fields.pop("processing_note", None)
        return {"entry_id": entry["entry_id"], "entry_type": entry["entry_type"],
                "fields": fields, "status": entry["status"], "relations": entry["relations"],
                "source_message_identities": entry["source_message_identities"],
                "source_time_range": entry["source_time_range"]}
    return claim(left) == claim(right)


def outgoing_references(entry):
    """Yield exact editable paths; derived candidate_refs are deliberately absent."""
    for index, relation in enumerate(entry["relations"]):
        yield relation["entry_id"], f"relations[{index}].entry_id", None
    if entry["entry_type"] == "implicit_gap":
        yield entry["fields"]["situation_ref"], "fields.situation_ref", "situation"
    if entry["entry_type"] == "candidate":
        for index, target in enumerate(entry["fields"]["notebook_refs"]):
            yield target, f"fields.notebook_refs[{index}]", "non_candidate"


def validate_references(state):
    entries = {entry["entry_id"]: entry for section in SECTIONS
               for entry in state[section] if not entry["archived"]}
    for entry in entries.values():
        for target_id, field, required_type in outgoing_references(entry):
            target = entries.get(target_id)
            invalid = target is None or target_id == entry["entry_id"]
            if target is not None:
                invalid = invalid or (required_type == "situation" and target["entry_type"] != "situation")
                invalid = invalid or (required_type == "non_candidate" and target["entry_type"] == "candidate")
                invalid = invalid or (entry["entry_type"] == "candidate" and target["entry_type"] == "candidate")
            if invalid:
                raise NotebookValidationError(
                    "The reference has no eligible current target.", code="invalid_reference", field=field,
                    next_action="Use an existing eligible entry from the current working Notebook.",
                    details={"entry_id": entry["entry_id"], "target_entry_id": target_id},
                )
        if entry["entry_type"] == "candidate":
            required_labels = {"situation" if entries[ref]["entry_type"] == "implicit_gap"
                               else entries[ref]["entry_type"] for ref in entry["fields"]["notebook_refs"]}
            if not required_labels.issubset(set(entry["fields"]["source_types"])):
                raise NotebookValidationError(
                    "Candidate source_types omits a referenced content type.", field="fields.source_types",
                    next_action="Include the union of source labels, mapping implicit_gap to situation.",
                    details={"required_source_types": sorted(required_labels)},
                )


def public_state(state):
    """Complete current bodies with reverse Candidate links computed from this view."""
    result = {section: [deepcopy(entry) for entry in state[section] if not entry.get("archived", False)]
              for section in SECTIONS}
    entries = {entry["entry_id"]: entry for section in SECTIONS for entry in result[section]}
    for entry in entries.values():
        entry.pop("archived", None)
        entry["candidate_refs"] = []
    for candidate in result["candidates"]:
        for target in candidate["fields"]["notebook_refs"]:
            if target in entries:
                entries[target]["candidate_refs"].append(candidate["entry_id"])
    return result
