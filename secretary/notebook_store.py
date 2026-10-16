"""Task-bound Notebook service; each task keeps its own base and complete view."""

from copy import deepcopy
from datetime import datetime, timezone
from threading import RLock

from secretary.notebook_contract import NotebookValidationError, parse_time, require_text, validate_source_range
from secretary.notebook_model import NotebookWorkingState


_UNBOUND_BASE = object()


def _source_checks_conn(db, conn, conversation_ref):
    """Use the native legal History path, not a separate Notebook evidence index."""
    history = list(db.get_history_foreground_conn(conn, conversation_ref))
    on_path = {row["message_identity"]["message_uid"] for row in history if row.get("message_identity")}
    timestamps = []
    for row in history:
        if not row.get("message_identity"):
            continue
        value = row.get("timestamp")
        try:
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                timestamps.append(datetime.fromtimestamp(value, timezone.utc))
            elif isinstance(value, str):
                timestamps.append(parse_time(value, "timestamp"))
        except (ValueError, OverflowError, OSError):
            # Unknown evidence time is not manufactured from operation time.
            continue

    def valid_identity(source):
        return (isinstance(source, dict) and source.get("conversation_ref") == conversation_ref
                and source.get("message_uid") in on_path)

    def valid_range(source_range):
        start, end = validate_source_range(source_range)
        return any(start <= timestamp <= end for timestamp in timestamps)

    return valid_identity, valid_range


def _source_validator_conn(db, conn, conversation_ref):
    return _source_checks_conn(db, conn, conversation_ref)[0]


def _inherited_sources_conn(conn, conversation_ref, entry, *, exact_version=False):
    from secretary.notebook_items import item_entry, item_row_conn, source_basis_conn

    row = item_row_conn(conn, entry["version_id"])
    if exact_version and entry != item_entry(row, conversation_ref):
        raise ValueError("Notebook entry differs from its immutable version")
    return source_basis_conn(conn, conversation_ref, row, entry) is not None


def validate_snapshot_state_conn(db, conn, conversation_ref, payload):
    """Revalidate versions, provenance and references in the commit transaction."""
    valid_identity, valid_range = _source_checks_conn(db, conn, conversation_ref)
    state = NotebookWorkingState(
        conversation_ref, payload, validate_source_identity=valid_identity, validate_source_range=valid_range,
        validate_inherited_sources=lambda entry: _inherited_sources_conn(
            conn, conversation_ref, entry, exact_version=True),
    ).snapshot_state()
    from secretary.notebook_items import snapshot_item_ids_conn
    snapshot_item_ids_conn(conn, conversation_ref, state)
    return state


class NotebookStore:
    """C5's task-local service, not a Main tool or an editable global Notebook.

    Lock order: caller's task lock (pass it as ``lock``) -> SessionDB transaction.
    No conn helper reacquires a task lock. Host capability/global switch and
    admission checks remain runner responsibilities; commit rechecks local state
    and Anchor. There is no reload/whole-view replacement or old edit/schedule API.
    """

    def __init__(self, db, conversation_ref, *, anchor_message_uid, trigger_type="idle",
                 runtime_profile="NOTING", lock=None, clock=None, base_snapshot_id=_UNBOUND_BASE):
        if db is None:
            raise NotebookValidationError("An owning SessionDB is required.")
        require_text(conversation_ref, "conversation_ref")
        require_text(anchor_message_uid, "anchor_message_uid")
        from hermes_state_secretary_notebook import TRIGGER_TYPES, RUNTIME_PROFILES
        if trigger_type not in TRIGGER_TYPES or runtime_profile not in RUNTIME_PROFILES:
            raise NotebookValidationError("Invalid Noting trigger or runtime profile.")
        self._db = db
        self.conversation_ref = conversation_ref
        self.trigger_type = trigger_type
        self.runtime_profile = runtime_profile
        self.lock = lock if lock is not None else RLock()
        self._anchor_message_uid = anchor_message_uid
        self._commit_result = None
        with self.lock, db._read_ctx() as conn:
            current = (db.notebook_current_conn(conn, conversation_ref)
                       if base_snapshot_id is _UNBOUND_BASE else None)
            if anchor_message_uid not in db._notebook_anchor_positions_conn(conn, conversation_ref):
                raise NotebookValidationError("The frozen Anchor is unavailable.", code="source_unavailable")
            self._base_snapshot_id = (current["snapshot_id"] if current is not None else None)
            if base_snapshot_id is not _UNBOUND_BASE:
                if base_snapshot_id is not None:
                    require_text(base_snapshot_id, "base_snapshot_id")
                self._base_snapshot_id = base_snapshot_id
            # Hydrate by the captured immutable ID. A second pointer read could
            # combine A's base_snapshot_id with B's payload under concurrency.
            snapshot = (None if self._base_snapshot_id is None else
                        db.notebook_snapshot_audit_conn(conn, self._base_snapshot_id))
            if self._base_snapshot_id is not None and snapshot is None:
                raise NotebookValidationError("The bound base Snapshot is unavailable.", code="source_unavailable")
            if snapshot is not None and snapshot["conversation_ref"] != conversation_ref:
                raise NotebookValidationError("The base Snapshot belongs to another Conversation.", code="scope_denied")
            payload = None if snapshot is None else snapshot["payload"]
            valid_identity, valid_range = _source_checks_conn(db, conn, conversation_ref)
            self._state = NotebookWorkingState(
                conversation_ref, payload, lock=self.lock, clock=clock,
                validate_source_identity=valid_identity, validate_source_range=valid_range,
                validate_inherited_sources=lambda entry: _inherited_sources_conn(
                    conn, conversation_ref, entry, exact_version=True),
            )
        # Subsequent operations check the current legal path, not a startup cache.
        self._state._validate_source_identity = self._valid_source
        self._state._validate_source_range = self._valid_range
        self._state._validate_inherited_sources = self._inherited_sources
        self._state._insert_version = self._insert_version

    @property
    def base_snapshot_id(self):
        return self._base_snapshot_id

    @property
    def coverage(self):
        return {"anchor_message_uid": self._anchor_message_uid}

    def _valid_source(self, source):
        with self._db._read_ctx() as conn:
            return _source_checks_conn(self._db, conn, self.conversation_ref)[0](source)

    def _valid_range(self, source_range):
        with self._db._read_ctx() as conn:
            return _source_checks_conn(self._db, conn, self.conversation_ref)[1](source_range)

    def _inherited_sources(self, entry):
        with self._db._read_ctx() as conn:
            return _inherited_sources_conn(conn, self.conversation_ref, entry)

    def _insert_version(self, entry, previous_version_id):
        from secretary.notebook_items import insert_item_conn, item_row_conn, source_basis_conn

        def insert(conn):
            basis = None
            if previous_version_id is not None:
                basis = source_basis_conn(conn, self.conversation_ref,
                                          item_row_conn(conn, previous_version_id), entry)
            if basis is None:
                valid_identity, valid_range = _source_checks_conn(self._db, conn, self.conversation_ref)
                if (not all(valid_identity(source) for source in entry["source_message_identities"])
                        or (entry["source_time_range"] is not None and not valid_range(entry["source_time_range"]))):
                    raise NotebookValidationError(
                        "The source left the authorized current path before the write.", code="source_unavailable",
                        next_action="Locate current evidence; this operation did not change the working Notebook.",
                    )
            return insert_item_conn(conn, self.conversation_ref, entry, previous_version_id, source_basis_id=basis)

        return self._db._execute_write(insert)

    def snapshot_state(self):
        return self._state.snapshot_state()

    def show(self):
        """Complete current payload only; no base reload, publication or time renewal."""
        return self._state.show()

    def working_view(self):
        with self.lock:
            return {"success": True, "conversation_ref": self.conversation_ref, "view_kind": "working",
                    "base_snapshot_id": self._base_snapshot_id, "coverage": self.coverage, "payload": self.show()}

    def get(self, entry_id):
        return self._state.get(entry_id)

    def create(self, entry_type, fields, *, status=None, relations=None,
               source_message_identities=None, source_time_range=None):
        return self._state.create(entry_type, fields, status=status, relations=relations,
                                  source_message_identities=source_message_identities, source_time_range=source_time_range)

    def update(self, entry_id, changes):
        return self._state.update(entry_id, changes)

    def archive(self, entry_id, reason):
        return self._state.archive(entry_id, reason)

    def maintain(self, args):
        return self._state.maintain(args)

    def freeze(self):
        return self._state.freeze()

    def commit(self, *, termination):
        """Return I-N's transaction result; the runner calls after the native Turn.

        The Anchor is bound at startup, never a model-selected/latest UID. Failed
        commit keeps the complete work. Successful repeated calls return the same
        receipt, without publishing another Snapshot or emitting another event.
        """
        with self.lock:
            if self._commit_result is not None:
                return deepcopy(self._commit_result)
            result = self._db.notebook_commit_snapshot_result(
                self.conversation_ref, self.snapshot_state(), anchor_message_uid=self._anchor_message_uid,
                trigger_type=self.trigger_type, runtime_profile=self.runtime_profile, termination=termination,
            )
            self._state.freeze()
            self._commit_result = deepcopy(result)
            return deepcopy(result)
