"""Task-local Notebook semantics with immutable, item-bound provenance inheritance."""

from secretary.notebook_model import NotebookValidationError, NotebookWorkingState
from secretary.notebook_schedule import parse_schedule_expression


def _source_validator_conn(db, conn, conversation_ref):
    """New citations must exist in the current History Foreground, including archived raw rows."""
    on_path = {row["message_identity"]["message_uid"]
               for row in db.get_history_foreground_conn(conn, conversation_ref)
               if row.get("message_identity")}

    def valid_source(source):
        return (isinstance(source, dict) and source.get("conversation_ref") == conversation_ref
                and source.get("message_uid") in on_path)

    return valid_source


def _inherited_sources_conn(conn, conversation_ref, entry, *, exact_version=False):
    from secretary.notebook_items import item_entry, item_row_conn, source_basis_conn

    row = item_row_conn(conn, entry["entry_id"])
    if exact_version and entry != item_entry(row, conversation_ref):
        raise ValueError(f"Notebook entry differs from immutable version: {entry['entry_id']}")
    return source_basis_conn(conn, conversation_ref, row, entry) is not None


def validate_snapshot_state_conn(db, conn, conversation_ref, payload):
    """Recheck new citations in the commit transaction; inherited citations stay item-bound."""
    return NotebookWorkingState(
        conversation_ref, payload,
        validate_source_identity=_source_validator_conn(db, conn, conversation_ref),
        validate_inherited_sources=lambda entry: _inherited_sources_conn(
            conn, conversation_ref, entry, exact_version=True),
    ).snapshot_state()


class NotebookStore:
    """The Noting runtime's semantic control surface; never a raw JSON or SQL replacement."""

    def __init__(self, db, conversation_ref, *, trigger_type="idle", runtime_profile="NOTING",
                 parse_schedule=parse_schedule_expression):
        if db is None or not isinstance(conversation_ref, str) or not conversation_ref:
            raise NotebookValidationError("A Notebook Store requires an owning DB and Conversation Ref")
        self._db = db
        self.conversation_ref = conversation_ref
        self.trigger_type = trigger_type
        self.runtime_profile = runtime_profile
        self._parse_schedule = parse_schedule
        self._state = None
        self.load()

    def load(self):
        """(Re)build the working state from the current committed Snapshot; none starts empty."""
        with self._db._read_ctx() as conn:
            payload = self._db.notebook_snapshot_state_conn(conn, self.conversation_ref)

        self._state = NotebookWorkingState(
            self.conversation_ref, payload, validate_source_identity=self._valid_source,
            validate_inherited_sources=self._inherited_sources,
            parse_schedule=self._parse_schedule, insert_version=self._insert_version)
        return self._state.show()

    def _valid_source(self, source):
        # Source input is checked when the operation runs, not against the task-load path.
        with self._db._read_ctx() as conn:
            return _source_validator_conn(self._db, conn, self.conversation_ref)(source)

    def _inherited_sources(self, entry):
        with self._db._read_ctx() as conn:
            return _inherited_sources_conn(conn, self.conversation_ref, entry)

    def _insert_version(self, entry, previous_id, inherit_sources):
        from secretary.notebook_items import insert_item_conn, item_row_conn, source_basis_conn

        def insert(conn):
            basis = None
            if inherit_sources and previous_id is not None:
                basis = source_basis_conn(conn, self.conversation_ref, item_row_conn(conn, previous_id), entry)
            if basis is None:
                valid = _source_validator_conn(self._db, conn, self.conversation_ref)
                if not all(valid(source) for source in entry.get("source_message_identities", [])):
                    raise NotebookValidationError("Source Message Identity is not valid on the current path")
            return insert_item_conn(conn, self.conversation_ref, entry, previous_id, source_basis_id=basis)

        return self._db._execute_write(insert)

    def snapshot_state(self) -> dict:
        return self._state.snapshot_state()

    def show(self) -> dict:
        """The active task-local four-section Agent view; archive versions stay internal."""
        return self._state.show()

    def create(self, entry_type, fields, *, status=None, source_message_identities=None,
               source_time_range=None, expression=None, delivery_mode=None) -> dict:
        return self._state.create(entry_type, fields, status=status,
                                  source_message_identities=source_message_identities,
                                  source_time_range=source_time_range, expression=expression,
                                  delivery_mode=delivery_mode)

    def edit(self, entry_id, fields, *, source_message_identities=None, source_time_range=None) -> dict:
        return self._state.edit(entry_id, fields, source_message_identities=source_message_identities,
                                source_time_range=source_time_range)

    def get(self, entry_id) -> dict:
        return self._state.get(entry_id)

    def archive(self, entry_id) -> dict:
        return self._state.archive(entry_id)

    def transition_status(self, entry_id, status) -> dict:
        return self._state.transition_status(entry_id, status)

    def schedule_update(self, entry_id, expression, *, delivery_mode=None) -> dict:
        return self._state.schedule_update(entry_id, expression, delivery_mode=delivery_mode)

    def schedule_cancel(self, entry_id) -> dict:
        return self._state.schedule_cancel(entry_id)

    def commit(self, anchor_message_uid) -> str:
        """Commit this task's complete state as one Snapshot; a refusal keeps state and pointer."""
        return self._db.notebook_commit_snapshot(
            self.conversation_ref, self._state.snapshot_state(), anchor_message_uid=anchor_message_uid,
            trigger_type=self.trigger_type, runtime_profile=self.runtime_profile)
