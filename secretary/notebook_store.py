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
            snapshot = self._db.notebook_current_conn(conn, self.conversation_ref)
            on_path = {row["message_uid"] for row in self._db.get_full_foreground_conn(conn, self.conversation_ref)}
        payload = snapshot["payload"] if snapshot else None
        # New evidence must be an Anchor-eligible Message of the current Full Foreground;
        # provenance already committed stays auditable after Hermes supersedes the citation.
        persisted = _persisted_source_identities(payload)

        def valid_source(source):
            if not isinstance(source, dict):
                return False
            return (source.get("message_uid") in on_path
                    or (source.get("conversation_ref"), source.get("message_uid")) in persisted)

        self._state = NotebookWorkingState(self.conversation_ref, payload,
                                           validate_source_identity=valid_source,
                                           parse_schedule=self._parse_schedule)
        return self._state.show()

    def show(self) -> dict:
        """The complete task-local state; the next commit persists exactly this."""
        return self._state.show()

    def create(self, entry_type, fields, *, status=None, source_message_identities=None) -> dict:
        return self._state.create(entry_type, fields, status=status,
                                  source_message_identities=source_message_identities)

    def edit(self, entry_id, fields, *, source_message_identities=None) -> dict:
        return self._state.edit(entry_id, fields, source_message_identities=source_message_identities)

    def archive(self, entry_id) -> dict:
        return self._state.archive(entry_id)

    def restore(self, entry_id) -> dict:
        return self._state.restore(entry_id)

    def transition_status(self, entry_id, status) -> dict:
        return self._state.transition_status(entry_id, status)

    def schedule_create(self, entry_id, expression) -> dict:
        return self._state.schedule_create(entry_id, expression)

    def schedule_update(self, entry_id, expression) -> dict:
        return self._state.schedule_update(entry_id, expression)

    def schedule_cancel(self, entry_id) -> dict:
        return self._state.schedule_cancel(entry_id)

    def commit(self, anchor_message_uid) -> str:
        """Commit this task's complete state as one Snapshot; a refusal keeps state and pointer."""
        return self._db.notebook_commit_snapshot(
            self.conversation_ref, self._state.show(), anchor_message_uid=anchor_message_uid,
            trigger_type=self.trigger_type, runtime_profile=self.runtime_profile)
