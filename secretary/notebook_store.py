"""One Noting task's semantic Notebook operations over the committed Snapshot.

Semantic mutations reuse the task-local model in ``secretary.notebook_model``; the durable
effect of a task is one immutable Snapshot committed in the same transaction as its pointer
move (02 §3.3, §3.7). A refused operation — the frozen Anchor having left the current Full
Foreground included — changes neither the committed state nor this working state. Only the
Noting runtime's service may expose this control surface.
"""

from secretary.notebook_model import NotebookValidationError, NotebookWorkingState
from secretary.notebook_schedule import parse_schedule_expression


def _persisted_source_identities(payload):
    """Provenance already committed, so a later supersession does not make it unreadable."""
    if not isinstance(payload, dict):
        return set()
    return {(source.get("conversation_ref"), source.get("message_uid"))
            for entries in payload.values() if isinstance(entries, list)
            for entry in entries if isinstance(entry, dict)
            for source in entry.get("source_message_identities") or [] if isinstance(source, dict)}


def _source_validator_conn(db, conn, conversation_ref):
    """New citations use the current path; already committed provenance remains auditable.

    Include older immutable Snapshots because a concurrently admitted task may have loaded
    an earlier base Snapshot before a newer task committed. Supersession does not turn
    those existing citations into newly invented evidence.
    """
    import json

    on_path = set(db._notebook_anchor_positions_conn(conn, conversation_ref))
    persisted = set()
    for row in conn.execute(
        "SELECT payload_json FROM secretary_notebook_snapshots WHERE conversation_ref = ?",
        (conversation_ref,),
    ):
        from secretary.notebook_items import hydrate_snapshot_conn
        persisted.update(_persisted_source_identities(hydrate_snapshot_conn(
            conn, conversation_ref, json.loads(row[0]), include_archived=True)))

    def valid_source(source):
        return (isinstance(source, dict) and source.get("conversation_ref") == conversation_ref
                and (source.get("message_uid") in on_path
                     or (conversation_ref, source.get("message_uid")) in persisted))

    return valid_source


def validate_snapshot_state_conn(db, conn, conversation_ref, payload):
    """Apply the same full semantic/provenance/intent validation at the durable DB gate."""
    return NotebookWorkingState(
        conversation_ref, payload,
        validate_source_identity=_source_validator_conn(db, conn, conversation_ref),
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
            valid_source = _source_validator_conn(self._db, conn, self.conversation_ref)

        self._state = NotebookWorkingState(self.conversation_ref, payload,
                                           validate_source_identity=valid_source,
                                           parse_schedule=self._parse_schedule, insert_version=self._insert_version)
        return self._state.show()

    def _insert_version(self, entry, previous_id):
        from secretary.notebook_items import insert_item_conn
        return self._db._execute_write(lambda conn: insert_item_conn(
            conn, self.conversation_ref, entry, previous_id))

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
