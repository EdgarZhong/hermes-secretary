"""Shared real-SessionDB harness for Notebook persistence tests.

The Notebook mixin and its schema wiring are part of SessionDB's bases centrally; these tests
use the real class directly. Each test module owns its isolated ``db`` fixture (the
foundation-test pattern), so no fixture name crosses module boundaries.
"""

from hermes_state import SessionDB
from hermes_state_secretary_notebook import init_secretary_notebook_schema
from secretary.notebook_model import SECTIONS


class NotebookSessionDB(SessionDB):
    """SessionDB with the centrally wired Secretary Notebook mixin."""


def open_notebook_db(path):
    db = NotebookSessionDB(path)
    db._execute_write(lambda conn: init_secretary_notebook_schema(conn.cursor()))
    return db


def make(db, sid, parent=None, marker=None, source="test", key=None):
    db.create_session(sid, source=source, parent_session_id=parent,
                      model_config={marker: parent} if marker else {}, session_key=key)


def add(db, sid, text, uid, role="user", timestamp=100):
    return db.append_message(sid, role, text, message_uid=uid, timestamp=timestamp)


def ref_of(db, sid):
    return db.resolve_conversation_ref(sid)


def empty_state():
    return {section: [] for section in SECTIONS}
