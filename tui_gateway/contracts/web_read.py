"""Additive browser-only compression controls and Secretary human read projections."""
from typing import Literal

from pydantic import Field

from .base import Params, Payload, Result
from .registry import event, method


class CompactionStateParams(Params):
    session_id: str = Field(min_length=1)
    profile: str | None = None


class CompactionStateResult(Result):
    active: bool
    operation_id: str | None
    phase: Literal["idle", "computing", "committing", "committed", "cancelled", "finished", "unknown"]
    cancelable: bool
    state: Literal["idle", "running", "completed", "cancelled", "no_change", "error", "unknown"]


class CompactionCancelParams(CompactionStateParams):
    operation_id: str = Field(min_length=1)


class CompactionCancelResult(Result):
    operation_id: str
    outcome: Literal["cancelled", "too_late", "no_active", "already_finished"]


class SecretaryReadParams(Params):
    stored_session_id: str = Field(min_length=1)
    profile: str


class IdleEstimate(Result):
    state: Literal["scheduled", "absent", "unknown"]
    at: str | None


class ActiveTask(Result):
    task_id: str


class MemoEntry(Result):
    index: int
    content: str


class SecretaryStateResult(Result):
    stored_session_id: str
    profile: str
    profile_home: str
    conversation_ref: str | None
    availability: Literal["available", "unavailable"]
    global_enabled: bool | None
    local_enabled: bool | None
    task_state: Literal["active", "idle", "unknown"]
    tasks: list[ActiveTask]
    next_idle: IdleEstimate
    observed_at: str
    memo_count: int
    memo_entries: list[MemoEntry]


class NotebookReadResult(Result):
    stored_session_id: str
    profile: str
    profile_home: str
    availability: Literal["available", "unavailable"]
    exists: bool
    output: str
    created_at: str | None


class SecretaryChangedPayload(Payload):
    profile_home: str
    conversation_ref: str | None
    reason: Literal["task_started", "task_finished", "memo_changed", "notebook_changed", "local_changed", "idle_changed", "global_changed"]


method("session.compaction_state", params=CompactionStateParams, result=CompactionStateResult)
method("session.compaction_cancel", params=CompactionCancelParams, result=CompactionCancelResult)
method("secretary.state", params=SecretaryReadParams, result=SecretaryStateResult)
method("secretary.notebook_read", params=SecretaryReadParams, result=NotebookReadResult)
event("secretary.changed", SecretaryChangedPayload)
