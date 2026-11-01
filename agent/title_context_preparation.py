"""Temporarily prepare a detached Main through its native prompt owners.

The exact object is recognized only inside this scope. It remains persistence
disabled, cannot register as a live Main, and loses Main eligibility on exit.
"""

import copy
import json
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass


_preparing_main = ContextVar("detached_main_context_preparation", default=None)


def is_detached_main_preparation(agent):
    return _preparing_main.get() is agent and getattr(agent, "_persist_disabled", False) is True


@contextmanager
def detached_main_preparation(agent):
    if not getattr(agent, "_persist_disabled", False):
        raise ValueError("Main context preparation requires a persistence-disabled fork")
    token = _preparing_main.set(agent)
    try:
        yield
    finally:
        _preparing_main.reset(token)


def finish_detached_context(agent, ignore_rules, side_agent=False):
    """Detach a native cold runtime without starting external memory providers."""
    agent._persist_disabled = True
    agent._end_session_on_close = False
    from agent.prompt_cache_scope import resolve_prompt_cache_scope_safe
    agent._inherited_cache_scope = resolve_prompt_cache_scope_safe(agent)
    agent._cached_conversation_root = agent._conversation_root_id()
    agent._session_db = None
    agent.side_agent = side_agent
    if not ignore_rules and agent._memory_store is None:
        from tools.memory_tool import load_on_disk_store
        agent._memory_store = load_on_disk_store()
        agent._memory_enabled = agent._memory_store.memory_enabled
        agent._user_profile_enabled = agent._memory_store.user_profile_enabled
    return agent


@dataclass(frozen=True)
class MainContextReader:
    """Only the native preparation reads, captured in the transcript transaction.

    No writer handle, flush-on-read SessionDB API or mutator is exposed. The
    profile path still lets the native owners read the correct configuration.
    """

    db_path: str
    row: dict
    conversation_ref: str
    conversation_root: str
    compression_lineage: tuple

    def get_session(self, session_id):
        return copy.deepcopy(self.row) if session_id == self.row["id"] else None

    def get_session_title(self, session_id):
        row = self.get_session(session_id)
        return row.get("title") if row else None

    def get_session_title_source(self, session_id):
        row = self.get_session(session_id)
        return row.get("title_source") if row else None

    def get_conversation_root(self, session_id):
        return self.conversation_root if session_id == self.row["id"] else session_id

    def get_compression_lineage(self, session_id):
        return list(self.compression_lineage) if session_id == self.row["id"] else []

    def resolve_conversation_ref(self, session_id, trusted_declared_locator=None):
        return self.conversation_ref if session_id == self.row["id"] else None


def prepare_title_prefix(fork, context):
    """Replay a valid effective capture verbatim, otherwise use native restore/build."""
    from agent.conversation_loop import _restore_or_build_system_prompt, _stored_prompt_matches_runtime
    from agent.conversation_prefix import freeze_request_prefix, restore_request_prefix
    from secretary.noting_surface import apply_main_read_surface, synchronize_main_read_prompt

    fork.session_id = context.session_id
    fork._session_db = context.reader
    try:
        with detached_main_preparation(fork):
            apply_main_read_surface(fork)
            native_root = context.reader.row.get("system_prompt") or context.root
            if context.root is not None and _stored_prompt_matches_runtime(fork, native_root):
                try:
                    saved = json.loads(context.reader.row.get("tool_names") or "null")
                except (TypeError, ValueError):
                    saved = None
                restore_request_prefix(fork, saved)
                freeze_request_prefix(fork)
                fork._cached_system_prompt = context.root
                fork.tools = copy.deepcopy(context.tools)
                # The effective capture already includes the pinned ephemeral addition.
                fork.ephemeral_system_prompt = None
            else:
                # A parity fork initially inherits its Parent's old declaration bytes.
                # At a native clear boundary fresh definitions precede restore/build.
                from secretary.conversation_cache import _refresh_current_tools
                fork._tool_snapshot_generation = -1
                _refresh_current_tools(fork)
                fork._cached_system_prompt = None
                _restore_or_build_system_prompt(fork, None, context.messages)
                synchronize_main_read_prompt(fork)
                freeze_request_prefix(fork)
    finally:
        fork._session_db = None
