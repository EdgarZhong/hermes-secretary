"""One Noting task's complete Notebook; publication belongs to the Snapshot gate.

All operations are serialized by ``lock``. A proposed full state is validated
before allocating an immutable version or replacing the working view.
"""

from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock

from secretary.notebook_contract import (
    ARRAY_FIELDS, CHANGE_KEYS, COMMON_FIELDS, ENTRY_KEYS, OPTIONAL_FIELDS,
    RELATION_KINDS, REQUIRED_FIELDS, STATUSES, NotebookValidationError,
    outgoing_references, parse_time, public_state, require_text,
    validate_candidate_provenance, validate_fields, validate_references, validate_source_range,
)
from secretary.notebook_contract import SECTIONS as SECTIONS
from secretary.notebook_contract import TYPE_SECTIONS as TYPE_SECTIONS
from secretary.notebook_contract import section_for_type as section_for_type


def _utc_now():
    return datetime.now(timezone.utc)


class NotebookWorkingState:
    """Internal state includes archive final versions; no Agent archive lookup exists."""

    def __init__(self, conversation_ref, payload=None, *, validate_source_identity=None,
                 validate_source_range=None, validate_inherited_sources=None,
                 insert_version=None, lock=None, clock=None):
        require_text(conversation_ref, "conversation_ref")
        self.conversation_ref = conversation_ref
        self.lock = lock if lock is not None else RLock()
        self._clock = clock if clock is not None else _utc_now
        self._validate_source_identity = validate_source_identity
        self._validate_source_range = validate_source_range
        self._validate_inherited_sources = validate_inherited_sources
        self._insert_version = insert_version
        self._frozen = False
        state = deepcopy(payload) if payload is not None else {section: [] for section in SECTIONS}
        self._validate_state(state)
        self._state = state
        numbers = [int(entry[key]) for entries in state.values() for entry in entries
                   for key in ("entry_id", "version_id")
                   if entry[key].isascii() and entry[key].isdecimal()]
        self._next_id = max(numbers, default=0) + 1

    def _now(self):
        value = self._clock()
        if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
            raise NotebookValidationError("The runtime clock is unavailable.", code="temporarily_unavailable")
        return value.isoformat()

    def _validate_sources(self, entry, *, fresh=False):
        sources = entry["source_message_identities"]
        if not isinstance(sources, list):
            raise NotebookValidationError("Expected a Message Identity array.", field="source_message_identities")
        seen = set()
        for source in sources:
            if not isinstance(source, dict) or set(source) != {"conversation_ref", "message_uid"}:
                raise NotebookValidationError("Expected a canonical Message Identity.", field="source_message_identities")
            for key in ("conversation_ref", "message_uid"):
                require_text(source[key], f"source_message_identities.{key}")
            if source["conversation_ref"] != self.conversation_ref:
                raise NotebookValidationError(
                    "Notebook sources must belong to the bound Conversation.", code="scope_denied",
                    next_action="Use the supplied parent Conversation; do not retry in another scope.",
                )
            identity = (source["conversation_ref"], source["message_uid"])
            if identity in seen:
                raise NotebookValidationError("Duplicate source Message Identity.", field="source_message_identities")
            seen.add(identity)
        source_range = entry["source_time_range"]
        if source_range is not None:
            validate_source_range(source_range)
        inherited = (not fresh and self._validate_inherited_sources is not None
                     and self._validate_inherited_sources(deepcopy(entry)))
        if inherited:
            return
        if entry["entry_type"] == "candidate":
            if validate_candidate_provenance(entry) == "refs":
                # Referenced entries carry their own provenance; validate_references checks them.
                return
        elif not sources and source_range is None:
            raise NotebookValidationError(
                "Every entry requires at least one provenance form.", field="source_message_identities",
                next_action="Supply supporting Message Identities or a bounded source_time_range.",
            )
        valid_messages = all(self._validate_source_identity is not None
                             and self._validate_source_identity(deepcopy(source)) for source in sources)
        valid_range = (source_range is None or (self._validate_source_range is not None
                       and self._validate_source_range(deepcopy(source_range))))
        if not valid_messages or not valid_range:
            raise NotebookValidationError(
                "The requested source is not available on the authorized current path.", code="source_unavailable",
                next_action="Search for the specific evidence in the allowed scope; keep it unknown if unavailable.",
            )

    def _validate_entry(self, entry, *, fresh=False):
        if not isinstance(entry, dict) or set(entry) != ENTRY_KEYS:
            raise NotebookValidationError("Invalid internal Notebook entry shape.", field="entry")
        entry_type = entry["entry_type"]
        section_for_type(entry_type)
        require_text(entry["entry_id"], "entry_id")
        require_text(entry["version_id"], "version_id")
        if not isinstance(entry["archived"], bool):
            raise NotebookValidationError("Invalid archive marker.", field="archived")
        validate_fields(entry_type, entry["fields"])
        if not isinstance(entry["status"], str) or entry["status"] not in STATUSES[entry_type]:
            raise NotebookValidationError("Invalid status for this entry type.", field="status")
        relations = entry["relations"]
        if not isinstance(relations, list):
            raise NotebookValidationError("Expected a complete relations array.", field="relations")
        seen = set()
        for relation in relations:
            if not isinstance(relation, dict) or set(relation) != {"kind", "entry_id"}:
                raise NotebookValidationError("Invalid relation fields.", field="relations")
            require_text(relation["kind"], "relations.kind")
            require_text(relation["entry_id"], "relations.entry_id")
            key = (relation["kind"], relation["entry_id"])
            if relation["kind"] not in RELATION_KINDS or key in seen:
                raise NotebookValidationError("Unknown or duplicate relation.", field="relations")
            seen.add(key)
        for key in ("created_at", "updated_at", "last_processed_at"):
            if entry[key] is not None:
                parse_time(entry[key], key)
        self._validate_sources(entry, fresh=fresh)

    def _validate_state(self, state, *, fresh_id=None):
        if not isinstance(state, dict) or set(state) != set(SECTIONS):
            raise NotebookValidationError("Notebook requires work, situations, discussion and candidates arrays.")
        ids, versions = set(), set()
        for section in SECTIONS:
            if not isinstance(state[section], list):
                raise NotebookValidationError("Notebook sections must be arrays.", field=section)
            for entry in state[section]:
                self._validate_entry(entry, fresh=isinstance(entry, dict) and entry.get("entry_id") == fresh_id)
                if (section_for_type(entry["entry_type"]) != section or entry["entry_id"] in ids
                        or entry["version_id"] in versions):
                    raise NotebookValidationError("Wrong section or duplicate entry/version identity.", field=section)
                ids.add(entry["entry_id"])
                versions.add(entry["version_id"])
        validate_references(state)

    def _require_writable(self):
        if self._frozen:
            raise NotebookValidationError(
                "The working Notebook is frozen; maintenance cannot be applied.", code="state_conflict",
                next_action="Use notebook_show to inspect the fixed view; let the runtime finish the task.",
            )

    def freeze(self):
        """C5 calls this under the same task lock when finish_noting is accepted."""
        with self.lock:
            self._frozen = True
            return self.snapshot_state()

    def _locate(self, entry_id):
        require_text(entry_id, "entry_id")
        for section in SECTIONS:
            for index, entry in enumerate(self._state[section]):
                if entry["entry_id"] == entry_id and not entry["archived"]:
                    return section, index
        raise NotebookValidationError(
            "No current entry has that ID.", code="entry_not_found", field="entry_id",
            next_action="Use an entry_id from the supplied or current working Notebook; do not guess IDs.",
        )

    def snapshot_state(self):
        with self.lock:
            return deepcopy(self._state)

    def show(self):
        with self.lock:
            return public_state(self._state)

    def get(self, entry_id):
        with self.lock:
            section, _index = self._locate(entry_id)
            return next(entry for entry in self.show()[section] if entry["entry_id"] == entry_id)

    def _persist(self, entry, previous_version_id):
        if self._insert_version is not None:
            return self._insert_version(deepcopy(entry), previous_version_id)
        entry = deepcopy(entry)
        version_id = str(self._next_id)
        self._next_id += 1
        if previous_version_id is None:
            entry["entry_id"] = version_id
        entry["version_id"] = version_id
        return entry

    def create(self, entry_type, fields, *, status=None, relations=None,
               source_message_identities=None, source_time_range=None):
        with self.lock:
            self._require_writable()
            section = section_for_type(entry_type)
            validate_fields(entry_type, fields)
            # A cleared optional singleton has one representation: absent. Required
            # text/arrays were checked above, so null cannot hide a missing value.
            fields = {key: deepcopy(value) for key, value in fields.items() if value is not None}
            entry = {"entry_id": "__new__", "version_id": "__new__", "entry_type": entry_type,
                     "fields": fields, "status": STATUSES[entry_type][0] if status is None else status,
                     "relations": deepcopy(relations) if relations is not None else [],
                     "source_message_identities": deepcopy(source_message_identities)
                     if source_message_identities is not None else [],
                     "source_time_range": deepcopy(source_time_range), "archived": False,
                     "created_at": None, "updated_at": None, "last_processed_at": None}
            draft = self.snapshot_state()
            draft[section].append(entry)
            self._validate_state(draft, fresh_id="__new__")
            now = self._now()
            entry["created_at"] = entry["updated_at"] = now
            note = entry["fields"].get("processing_note")
            if isinstance(note, str) and note.strip():
                entry["last_processed_at"] = now
            saved = self._persist(entry, None)
            draft[section][-1] = saved
            self._state = draft
            return {"success": True, "changed": True, "entry": self.get(saved["entry_id"])}

    def update(self, entry_id, changes):
        with self.lock:
            self._require_writable()
            section, index = self._locate(entry_id)
            if not isinstance(changes, dict) or not changes or changes.keys() - CHANGE_KEYS:
                raise NotebookValidationError("Expected nonempty changes with only editable properties.", field="changes")
            old = self._state[section][index]
            entry = deepcopy(old)
            field_changes = changes.get("fields", {})
            if not isinstance(field_changes, dict):
                raise NotebookValidationError("Expected a fields patch object.", field="changes.fields")
            for key, value in changes.items():
                if key != "fields":
                    entry[key] = deepcopy(value)
            allowed = (set(REQUIRED_FIELDS[entry["entry_type"]])
                       | set(OPTIONAL_FIELDS[entry["entry_type"]]) | COMMON_FIELDS)
            for key, value in field_changes.items():
                if key not in allowed:
                    raise NotebookValidationError("Field does not belong to this type.", field=f"changes.fields.{key}")
                if value is None and key not in REQUIRED_FIELDS[entry["entry_type"]] and key not in ARRAY_FIELDS:
                    entry["fields"].pop(key, None)
                elif key in ARRAY_FIELDS and value == [] and key not in entry["fields"]:
                    # Clearing an already absent optional array is a no-op.
                    continue
                else:
                    entry["fields"][key] = deepcopy(value)
            draft = self.snapshot_state()
            draft[section][index] = entry
            self._validate_state(draft)
            if entry == old:
                return {"success": True, "changed": False, "entry": self.get(entry_id)}
            now = self._now()
            entry["updated_at"] = now
            note = field_changes.get("processing_note")
            if isinstance(note, str) and note.strip():
                entry["last_processed_at"] = now
            saved = self._persist(entry, old["version_id"])
            draft[section][index] = saved
            self._state = draft
            return {"success": True, "changed": True, "entry": self.get(entry_id)}

    def archive(self, entry_id, reason):
        with self.lock:
            self._require_writable()
            require_text(reason, "reason")
            section, index = self._locate(entry_id)
            referrers = []
            for entries in self._state.values():
                for entry in entries:
                    if entry["archived"]:
                        continue
                    fields = [field for target, field, _kind in outgoing_references(entry) if target == entry_id]
                    if fields:
                        referrers.append({"entry_id": entry["entry_id"], "version_id": entry["version_id"],
                                          "fields": fields})
            if referrers:
                raise NotebookValidationError(
                    f"Entry {entry_id} is still referenced by {[row['entry_id'] for row in referrers]}.",
                    code="invalid_reference", field="entry_id", details={"referrers": referrers},
                    next_action="Preserve needed content and update those references before archiving.",
                )
            old = self._state[section][index]
            entry = deepcopy(old)
            entry["archived"] = True
            entry["fields"]["processing_note"] = reason
            draft = self.snapshot_state()
            draft[section][index] = entry
            self._validate_state(draft)
            now = self._now()
            entry["updated_at"] = entry["last_processed_at"] = now
            draft[section][index] = self._persist(entry, old["version_id"])
            self._state = draft
            return {"success": True, "changed": True, "entry_id": entry_id, "archived": True}

    def maintain(self, args):
        """Strict action router for C5; does not grant Main mutation authority."""
        if not isinstance(args, dict) or not isinstance(args.get("action"), str):
            raise NotebookValidationError("Expected a Notebook action object.", field="action")
        action = args["action"]
        required = {"create": {"entry_type", "fields"}, "update": {"entry_id", "changes"},
                    "archive": {"entry_id", "reason"}}
        optional = {"create": {"status", "relations", "source_message_identities", "source_time_range"},
                    "update": set(), "archive": set()}
        if action not in required:
            raise NotebookValidationError("Expected create, update or archive.", field="action")
        supplied = set(args) - {"action"}
        if supplied - required[action] - optional[action] or required[action] - supplied:
            raise NotebookValidationError("Missing required or mixed-action parameters.", field="action",
                                          next_action="Supply only the parameters for the selected action.")
        for key in ("status", "relations", "source_message_identities"):
            if key in args and args[key] is None:
                raise NotebookValidationError("Null is not allowed for this parameter.", field=key)
        kwargs = {key: value for key, value in args.items() if key != "action"}
        return getattr(self, action)(**kwargs)
