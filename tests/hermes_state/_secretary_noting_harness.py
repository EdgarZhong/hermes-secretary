"""Shared real-SessionDB harness for Noting admission / child-registry / Idle-timer tests.

The Noting mixin and its schema wiring are part of SessionDB's bases centrally; these tests use
the real class directly. The Notebook sibling is composed in for the same reason it always was:
the runtime reads its conversation-local gate and the §4.9 derivation reads its Snapshot table.
"""

from hermes_state import SessionDB
from hermes_state_secretary_notebook import init_secretary_notebook_schema
from hermes_state_secretary_noting import init_secretary_noting_schema
from secretary.notebook_model import SECTIONS


class NotingSessionDB(SessionDB):
    """SessionDB with the centrally wired Secretary Noting and Notebook mixins."""


def open_noting_db(path):
    db = NotingSessionDB(path)

    def _init(conn):
        init_secretary_noting_schema(conn.cursor())
        init_secretary_notebook_schema(conn.cursor())

    db._execute_write(_init)
    return db


def make(db, sid, parent=None, marker=None, source="test", key=None):
    db.create_session(sid, source=source, parent_session_id=parent,
                      model_config={marker: parent} if marker else {}, session_key=key)


def add(db, sid, text, uid, role="user", timestamp=100, **kwargs):
    return db.append_message(sid, role, text, message_uid=uid, timestamp=timestamp, **kwargs)


def ref_of(db, sid):
    return db.resolve_conversation_ref(sid)


def empty_state():
    return {section: [] for section in SECTIONS}
