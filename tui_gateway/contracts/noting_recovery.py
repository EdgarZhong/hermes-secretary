"""Explicit failed Noting recovery; operation audit lives on the native child."""
from typing import Literal

from pydantic import Field

from .base import Params, Result
from .registry import method


class NotingRecoveryParams(Params):
    profile: str | None = None
    conversation_ref: str = Field(min_length=1)
    failed_child_session_id: str = Field(min_length=1)
    request_id: str = Field(min_length=1, max_length=128)


class NotingRecoverySources(Result):
    parent: str
    root: str
    tools: str
    notebook: str


class NotingRecoveryResult(Result):
    operation_id: str
    child_session_id: str | None
    status: Literal["not_found", "queued", "running", "completed", "failed", "abandoned", "incomplete", "interrupted"]
    committed: bool
    snapshot_id: str | None
    error: str | None
    sources: NotingRecoverySources | None


method("secretary.noting_recover", params=NotingRecoveryParams, result=NotingRecoveryResult)
method("secretary.noting_recovery_state", params=NotingRecoveryParams, result=NotingRecoveryResult)
