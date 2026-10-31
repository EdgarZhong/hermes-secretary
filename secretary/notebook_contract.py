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
    "situation": ("description", "subjects"),
    "implicit_gap": ("description", "situation_ref", "missing_information", "impact"),
    "question": ("description",),
    "insight": ("description", "certainty"),
    "decision": ("description", "scope"),
    "candidate": ("description", "targets", "notebook_refs", "source_types"),
}
OPTIONAL_FIELDS = {
    "matter": ("blocker", "last_progress_time"),
    "action": ("blocker", "last_progress_time"),
    "situation": ("time_context",), "implicit_gap": ("resolution_condition",),
    "question": ("unresolved_points", "current_answer", "last_discussion_time"),
    "insight": ("qualification",), "decision": ("valid_when", "ends_when", "rationale"), "candidate": ("stage_evidence",),
}
COMMON_FIELDS = {"domains", "processing_note"}
ARRAY_FIELDS = {"domains", "subjects", "targets", "notebook_refs", "source_types"}
EVIDENCE_TIMES = {"last_progress_time", "last_discussion_time"}
LEGACY_STATUSES = {
    "matter": ("in_progress", "paused", "completed", "terminated"),
    "action": ("pending", "in_progress", "waiting", "paused", "completed", "terminated"),
    "situation": ("current", "expired"),
    "implicit_gap": ("missing", "resolved", "invalid"),
    "question": ("open", "answered", "withdrawn"),
    "insight": ("current", "revised", "withdrawn"),
    "decision": ("active", "superseded", "revoked", "expired"),
    "candidate": ("proposed", "awaiting_approval", "approved", "awaiting_result"),
}
LEGACY_DONE_STATUSES = {
    "completed", "terminated", "expired", "resolved", "invalid", "answered",
    "withdrawn", "superseded", "revoked",
}
RELATION_KINDS = {"part_of", "depends_on", "based_on", "supersedes", "related_to"}
SOURCE_TYPES = {"matter", "action", "situation", "question", "insight", "decision"}
CANDIDATE_TARGETS = {"memory", "skill", "rule", "conversation"}
PERSISTENCE_TARGETS = CANDIDATE_TARGETS - {"conversation"}
ENTRY_KEYS = {
    "entry_id", "version_id", "entry_type", "fields", "done", "relations",
    "provenance", "provenance_descriptions", "provenance_tasks", "write_task_id", "evidence_time", "created_at", "updated_at",
    "last_processed_at", "archived",
}
CHANGE_KEYS = {"fields", "done", "relations", "schedule_suggestion", "source_message_identities", "source_message_uids", "source_description"}
SOURCE_NOT_PROVIDED = object()


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


def validate_source_range(value, field="evidence_time"):
    if not isinstance(value, dict) or set(value) != {"start_time", "end_time"}:
        raise NotebookValidationError(
            "Derived evidence time requires both bounds.", field=field,
            next_action="Evidence time is runtime-derived; supply valid source Message UIDs instead.",
        )
    start, end = (parse_time(value[key], f"{field}.{key}")
                  for key in ("start_time", "end_time"))
    if start > end:
        raise NotebookValidationError("Source time range is reversed.", field=field)
    return start, end


def canonical_range_fields(values):
    """Keep the old singleton only as a trusted internal/read compatibility form."""
    result = deepcopy(values)
    if "source_time_range" in result:
        if "source_time_ranges" in result:
            raise NotebookValidationError(
                "Do not mix legacy and current range parameters.", field="source_time_ranges",
                next_action="Use only source_time_ranges with the complete replacement array.",
            )
        interval = result.pop("source_time_range")
        result["source_time_ranges"] = [] if interval is None else [interval]
    return result


def canonical_notebook_entry(entry):
    """Project old fields without rewriting any immutable version's stored JSON."""
    if not isinstance(entry, dict):
        return deepcopy(entry)
    result = canonical_range_fields(entry)
    if "provenance_descriptions" not in result and isinstance(result.get("provenance"), list):
        # Missing legacy descriptions stay explicitly unknown. Never rewrite or
        # infer historical wording from UIDs, times or the current entry text.
        result["provenance_descriptions"] = [None] * len(result["provenance"])
    if "status" in result:
        status = result.pop("status")
        entry_type = result.get("entry_type")
        if ("done" in result or not isinstance(status, str) or not isinstance(entry_type, str)
                or status not in LEGACY_STATUSES.get(entry_type, ())):
            raise NotebookValidationError("Invalid legacy Notebook status representation.", field="status")
        result["done"] = status in LEGACY_DONE_STATUSES
        fields = result.get("fields")
        if (isinstance(fields, dict) and isinstance(fields.get("description"), str)
                and fields["description"].strip()):
            # Preserve the old record's meaning without inventing a new fact,
            # approval or disposition. This is a read projection, not a write.
            meaning = f"Earlier record marked this {entry_type.replace('_', ' ')} as {status.replace('_', ' ')}."
            if status == "pending":
                meaning += " That marker does not establish whether work had started."
            if entry_type == "candidate":
                meaning += " That stage alone does not establish authorization or an actual write."
            fields["description"] = fields["description"] + "\n" + meaning
    if isinstance(result.get("fields"), dict):
        for key in ("external_refs", "evidence_time"):
            result["fields"].pop(key, None)
    return result


def reject_legacy_status(values):
    if isinstance(values, dict) and "status" in values:
        raise NotebookValidationError(
            "status is no longer editable; use the top-level done boolean.", field="status",
            next_action="Omit status; set done to true or false and record progress or outcomes in fields.description.",
        )


def validate_done(value):
    if not isinstance(value, bool):
        raise NotebookValidationError(
            "done requires a boolean; null, numbers and strings are not accepted.", field="done",
            next_action="Supply true or false; omit done on update to keep its current value.",
        )


def unique_strings(value, field):
    if not isinstance(value, list):
        raise NotebookValidationError("Expected a complete replacement array.", field=field,
                                      next_action="Include all values to retain; use [] to clear an optional array.")
    for item in value:
        require_text(item, field)
    if len(value) != len(set(value)):
        raise NotebookValidationError("Duplicate array values are not allowed.", field=field)


def canonical_source_fields(values, conversation_ref):
    """Bind internal canonical identity input to the one editable local UID slot."""
    result = deepcopy(values)
    if "source_message_identities" in result:
        if "source_message_uids" in result:
            raise NotebookValidationError("Supply only one source representation.", field="source_message_uids")
        sources = result.pop("source_message_identities")
        if not isinstance(sources, list):
            raise NotebookValidationError("Expected Message identities.", field="source_message_uids")
        for source in sources:
            if (not isinstance(source, dict) or set(source) != {"conversation_ref", "message_uid"}
                    or source["conversation_ref"] != conversation_ref):
                raise NotebookValidationError("Source belongs to another Conversation.", code="scope_denied",
                                              field="source_message_uids")
        result["source_message_uids"] = [source["message_uid"] for source in sources]
    if "source_message_uids" in result:
        unique_strings(result["source_message_uids"], "source_message_uids")
    return result


def provenance_prefix(left, right):
    """Count identical licensed nodes, including descriptions and derived times."""
    left, right = canonical_notebook_entry(left), canonical_notebook_entry(right)
    count = 0
    keys = ("provenance_tasks", "provenance", "provenance_descriptions", "evidence_time")
    for old, new in zip(zip(*(left[key] for key in keys)), zip(*(right[key] for key in keys))):
        if old != new:
            break
        count += 1
    return count


def validate_provenance_transition(previous, entry, *, mutable_task_id=None, allow_tail_replacement=True):
    """A task can replace its tail slot; earlier tasks' nodes never change."""
    old_tasks, tasks = previous["provenance_tasks"], entry["provenance_tasks"]
    count = provenance_prefix(previous, entry)
    append = len(tasks) == len(old_tasks) + 1 and count == len(old_tasks)
    replace = (allow_tail_replacement and bool(tasks) and tasks == old_tasks and count >= len(tasks) - 1)
    unchanged = count == len(old_tasks) == len(tasks)
    clear_current = (mutable_task_id is not None and old_tasks == [mutable_task_id]
                     and previous["write_task_id"] == mutable_task_id and not tasks
                     and entry["entry_type"] == "candidate" and bool(entry["fields"]["notebook_refs"])
                     and not entry["provenance"] and not entry["provenance_descriptions"] and not entry["evidence_time"])
    if not (append or replace or unchanged or clear_current):
        raise NotebookValidationError("Earlier Task provenance nodes are immutable.", field="source_message_uids")


def local_source_error(error):
    """Keep diagnostic fields consistent with the caller's local UID input."""
    if error.field and error.field.startswith("source_message_identities"):
        error.field = error.field.replace("source_message_identities", "source_message_uids", 1)
        error.next_action = error.next_action.replace("Message Identities", "Message UIDs")
    return error


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
            if key == "targets":
                if set(value) - CANDIDATE_TARGETS:
                    raise NotebookValidationError("Unknown Candidate target.", field=field)
                if "conversation" in value and len(set(value)) != 1:
                    raise NotebookValidationError(
                        "A Conversation Candidate cannot mix persistence targets.", field=field,
                        next_action="Create a separate Memory, Skill or Rule Candidate for persistence.",
                    )
            if key == "source_types" and set(value) - SOURCE_TYPES:
                raise NotebookValidationError("Invalid source label; implicit_gap maps to situation.", field=field)
        elif key in EVIDENCE_TIMES:
            if value is not None:
                parse_time(value, field)
        elif key in required:
            require_text(value, field)
        elif value is not None and not isinstance(value, str):
            raise NotebookValidationError("Expected optional text or null.", field=field)


def validate_schedule_suggestion(value):
    """One semantic suggestion, never Scheduler input or an executable time."""
    if value is None:
        return
    if not isinstance(value, dict) or set(value) != {"content", "schedule"}:
        raise NotebookValidationError(
            "Expected one object containing content and schedule.", field="schedule_suggestion",
            next_action="Supply both semantic strings in one object, or null to clear the suggestion.",
        )
    for key in ("content", "schedule"):
        require_text(value[key], f"schedule_suggestion.{key}")


def validate_candidate_provenance(entry):
    """Direct UID chains and current Notebook references are exclusive."""
    fields = entry["fields"]
    refs, sources = fields["notebook_refs"], entry["provenance"]
    if refs:
        if sources:
            raise NotebookValidationError(
                "A Candidate cites either Notebook entries or direct Message UIDs, not both.",
                field="source_message_uids", next_action="Keep one source form; prior Task nodes cannot be removed.")
        return "refs"
    if fields["source_types"]:
        raise NotebookValidationError("source_types requires notebook_refs.", field="fields.source_types")
    if not sources:
        raise NotebookValidationError("Direct Candidates require Message UIDs.", field="source_message_uids")
    return "messages"


def same_source_claim(left, right, *, allow_relation_removal=False):
    """An inherited citation license is not transferable to a different claim.

    Administrative processing and archiving do not change the supported claim.
    Any content/done/relationship/provenance change must use current sources.
    This is a structural safeguard, not an attempt to infer semantic entailment.
    """
    def claim(entry):
        entry = canonical_notebook_entry(entry)
        fields = deepcopy(entry["fields"])
        fields.pop("processing_note", None)
        return {"entry_id": entry["entry_id"], "entry_type": entry["entry_type"],
                "fields": fields, "done": entry["done"], "relations": entry["relations"],
                "provenance": entry["provenance"], "provenance_tasks": entry["provenance_tasks"],
                "provenance_descriptions": entry["provenance_descriptions"],
                "evidence_time": entry["evidence_time"]}
    left_claim, right_claim = claim(left), claim(right)
    if allow_relation_removal:
        # Runtime archive cleanup can only remove existing auxiliary relations;
        # it cannot add a relationship or alter any supported content/provenance.
        old_relations = left_claim["relations"]
        new_relations = right_claim["relations"]
        if any(relation not in old_relations for relation in new_relations):
            return False
        left_claim["relations"] = new_relations
    left_claim["schedule_suggestion"] = left.get("schedule_suggestion")
    right_claim["schedule_suggestion"] = right.get("schedule_suggestion")
    return left_claim == right_claim


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
    result = {section: [canonical_notebook_entry(entry) for entry in state[section] if not entry.get("archived", False)]
              for section in SECTIONS}
    entries = {entry["entry_id"]: entry for section in SECTIONS for entry in result[section]}
    for entry in entries.values():
        entry.pop("archived", None)
        entry.pop("provenance_tasks", None)
        entry.pop("write_task_id", None)
        entry["candidate_refs"] = []
    for candidate in result["candidates"]:
        for target in candidate["fields"]["notebook_refs"]:
            if target in entries:
                entries[target]["candidate_refs"].append(candidate["entry_id"])
    return result
