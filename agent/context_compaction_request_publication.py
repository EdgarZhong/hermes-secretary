"""Native committed-result publication and request-specific durable handoff.

The marker is manufactured at the native summary commit site, never on requests or
Framework messages. Its summary UID changes on each successor compaction.
"""
from __future__ import annotations

import copy
import logging

logger = logging.getLogger(__name__)
PUBLICATION_KEY = 'native_compaction_request_publication'


def _marker(message):
    metadata = message.get('display_metadata') or {}
    return metadata.get(PUBLICATION_KEY) if isinstance(metadata, dict) else None


def stamp_native_publication(agent, messages, compressed, request=None):
    """Mark only the native-generated summary which the same transaction stores."""
    from agent.context_compaction_request import _ref
    if request is not None:
        ref, origin = str(_ref(agent)), request.publication_id
    else:
        # A caller/Framework can carry arbitrary display metadata. Only the
        # current durable native summary can originate an inherited publication.
        db = getattr(agent, '_session_db', None)
        reader = getattr(type(db), 'get_native_request_publication', None)
        if not callable(reader):
            return
        try:
            previous = reader(db, agent.session_id)
            ref = str(_ref(agent)) if previous else None
        except Exception:
            logger.debug('Could not inherit a native request publication', exc_info=True)
            return
        if not previous or previous['marker'].get('conversation_ref') != ref:
            return
        origin = previous['marker'].get('origin_request')
    if not origin:
        return
    for row in compressed:
        if isinstance(row, dict) and row.get('_compressed_summary') is True:
            metadata = dict(row.get('display_metadata') or {})
            metadata[PUBLICATION_KEY] = {'origin_request': origin, 'conversation_ref': ref}
            row['display_metadata'] = metadata
            return


def _overlay_runtime_fields(durable, runtime):
    """Keep API-local fields on UID twins; the loader owns durable identity/order."""
    from agent.session_persistence import _EPHEMERAL_SCAFFOLDING_FLAGS
    from hermes_state_messages import SessionMessagesMixin
    by_uid = {row.get('message_uid'): row for row in runtime
              if isinstance(row, dict) and row.get('message_uid')}
    for row in durable:
        original = by_uid.get(row.get('message_uid'))
        if original is None or original.get('role') != row.get('role'):
            continue
        role = row.get('role')
        loaded = SessionMessagesMixin._loaded_view_content
        if (loaded(role, original.get('content')) != loaded(role, row.get('content'))
                or original.get('tool_calls') != row.get('tool_calls')
                or original.get('tool_call_id') != row.get('tool_call_id')):
            continue
        for key, value in original.items():
            if key == 'api_content' or key in _EPHEMERAL_SCAFFOLDING_FLAGS:
                row[key] = copy.deepcopy(value)
    return durable


def publish_native_commit(agent, commit, prompt, request=None, *, restore_complete_context=False):
    """Called inside the existing native commit fence, before it is released."""
    if (request is None and not restore_complete_context) or not commit.session_commit_succeeded:
        return commit.compressed
    from agent.context_compaction_request import _lock
    with _lock(agent):
        if request is not None:
            request.durable_commit_succeeded = True
            if not request.current():
                raise RuntimeError('Native request owner changed after compression commit')
        durable = agent._session_db.get_messages_as_conversation(agent.session_id, include_row_ids=True)
        durable = _overlay_runtime_fields(durable, commit.compressed)
        live = getattr(agent, '_session_messages', None)
        if isinstance(live, list):
            live[:] = durable
        else:
            agent._session_messages = durable
        agent._cached_system_prompt = prompt
        agent._last_flushed_db_idx = len(durable)
        agent._flushed_db_message_ids = set()
        agent._db_flush_scan_prefix = None
        if request is not None:
            request.committed = True
            request.result = (durable, prompt)
        return durable


def refresh_request_history(agent, history, *, task_context=None):
    """Lease-held native entry: reload ONLY an unconsumed committed request summary."""
    db = getattr(agent, '_session_db', None)
    reader = getattr(type(db), 'get_native_request_publication', None)
    if not callable(reader):
        return history
    try:
        publication = reader(db, agent.session_id)
    except Exception:
        # No new failure surface for databases/runtimes which never had a request.
        logger.debug('Could not inspect native request publication', exc_info=True)
        return history
    if not publication:
        return history
    from agent.context_compaction_request import _ref
    if publication['marker'].get('conversation_ref') != str(_ref(agent)):
        return history
    uid = publication['message_uid']
    target_session = publication.get('session_id', agent.session_id)
    if any(isinstance(row, dict) and row.get('message_uid') == uid
           and _marker(row) == publication['marker'] for row in (history or [])) and target_session == agent.session_id:
        return history
    durable = db.get_messages_as_conversation(target_session, include_row_ids=True)
    if target_session != agent.session_id:
        agent.session_id = target_session
        if task_context is not None:
            task_context['session_id'] = target_session
        from agent.compression_facade import _rebind_caller_session_context
        _rebind_caller_session_context(agent)
    durable = _overlay_runtime_fields(durable, history or [])
    # Carried input was admitted by native code but never persisted in the old Turn.
    from agent.session_persistence import _PERSIST_AFTER_ADMISSION_INTERRUPT
    from agent.context_compressor import _DB_PERSISTED_MARKER
    durable_uids = {row.get('message_uid') for row in durable}
    durable.extend(row for row in (history or []) if isinstance(row, dict)
                   and not row.get('_row_id') and (row.get(_PERSIST_AFTER_ADMISSION_INTERRUPT)
                   or (not row.get(_DB_PERSISTED_MARKER) and row.get('message_uid') not in durable_uids)))
    live = getattr(agent, '_session_messages', None)
    if isinstance(live, list):
        live[:] = durable
    else:
        agent._session_messages = durable
    root = (db.get_session(agent.session_id) or {}).get('system_prompt')
    if root is not None:
        agent._cached_system_prompt = root
    agent._last_flushed_db_idx = len(durable)
    agent._flushed_db_message_ids = set()
    agent._db_flush_scan_prefix = None
    return durable


def observe_request_admission(agent, fence, receipt, request=None):
    """Keep existing receipt semantics for all ordinary native callers."""
    if request is not None:
        request.admit(fence)
    else:
        from secretary.noting_admission_receipt import observe_native_admission
        observe_native_admission(agent, fence, receipt)
