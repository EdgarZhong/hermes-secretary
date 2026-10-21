"""Explicit Conversation context-prefix cache maintenance."""

from typing import Literal

from pydantic import Field

from .base import Params, Result
from .registry import method


class ConversationCacheClearParams(Params):
    profile: str = Field(min_length=1)
    conversation_ref: str = Field(min_length=1)


class ConversationCacheClearResult(Result):
    profile: str
    conversation_ref: str
    stored_session_id: str
    status: Literal["cleared", "already_clear"]


method("conversation.context_cache_clear", params=ConversationCacheClearParams,
       result=ConversationCacheClearResult,
       doc="Clear the current Conversation root and tools pin; rebuild on its next normal turn.")
