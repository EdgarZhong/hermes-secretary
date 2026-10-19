"""Additive idle-only Web Send; native PromptSubmit wire remains unchanged."""
from typing import Literal

from pydantic import Field

from .base import Result
from .common import SessionParams
from .events import MessageUserCommittedPayload
from .registry import method


class SubmitIdleParams(SessionParams):
    session_id: str = Field(min_length=1)
    text: str = ""
    image_paths: list[str] = Field(default_factory=list)
    title_preview: str | None = None
    truncate_before_user_ordinal: int | None = None
    truncate_before_row_id: int | None = None
    truncate_before_message_id: str | None = None
    confirm_truncate: bool | None = None
    confirm_empty_truncate: bool | None = None
    rebind_survivor_row_ids: list[int] | None = None


class SubmitIdleResult(Result):
    status: Literal["streaming"]
    user_row_id: int | None = None
    survivor_user_row_ids: list[int | None] | None = None
    survivor_row_id_map: dict[str, int | None] | None = None
    turn_isolation: bool | None = None
    accepted_user: MessageUserCommittedPayload | None = None


method("prompt.submit_idle", params=SubmitIdleParams, result=SubmitIdleResult,
       doc="Submit only if the native running claim is idle; competing turns refuse with 4009, never busy fallback.")
