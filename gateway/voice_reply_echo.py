"""Event-owned voice transcript echoes, carried only on human reply delivery.

There is deliberately no chat/session registry: a pending event owns its state and
only the TurnContext executing that event may put it on model reply metadata.
"""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from typing import Any

from agent.i18n import t
from gateway.config import Platform

_STATE = "_gateway_voice_reply_echo"
_PAYLOAD = "_gateway_voice_reply_payload"
_RESULT = "_gateway_terminal_voice_reply_echo"


@dataclass
class VoiceReplyEcho:
    chat_id: str
    transcripts: list[str] = field(default_factory=list)
    delivered: int = 0
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


def event_echo(event: Any) -> VoiceReplyEcho | None:
    state = getattr(event, _STATE, None)
    return state if isinstance(state, VoiceReplyEcho) else None


def defer_voice_echo(runner, event, source, transcripts: list[str]) -> bool:
    """Opt-in Weixin only; retain ordered clips, including identical spoken text."""
    if (not getattr(runner.config, "stt_echo_transcripts_with_reply", False)
            or getattr(source, "platform", None) != Platform.WEIXIN or getattr(event, "internal", False)
            or not runner._should_echo_stt_transcripts()):
        return False
    if transcripts:
        state = event_echo(event) or VoiceReplyEcho(str(source.chat_id))
        state.transcripts = list(transcripts)
        setattr(event, _STATE, state)
    return True


def reply_metadata(metadata, state: VoiceReplyEcho | None):
    """Clone only for an eligible model reply; never mutate progress/typing metadata."""
    return {**(metadata or {}), _STATE: state} if isinstance(state, VoiceReplyEcho) else metadata


def carry_terminal_echo(result, state, *, previous=None):
    """A recursive queued turn, including one with no echo, owns the outer final."""
    if state is not None or previous is not None:
        if isinstance(result, dict) and _RESULT not in result:
            return {**result, _RESULT: state}
        if isinstance(result, BaseException) and not hasattr(result, _RESULT):
            setattr(result, _RESULT, state)
    return result


def adopt_terminal_echo(event, result) -> None:
    if isinstance(result, dict) and _RESULT in result:
        setattr(event, _STATE, result[_RESULT])
    elif isinstance(result, BaseException) and hasattr(result, _RESULT):
        setattr(event, _STATE, getattr(result, _RESULT))


@dataclass
class ReplyPayload:
    content: str
    metadata: Any
    state: VoiceReplyEcho | None = None
    through: int = 0

    def acknowledge(self, result) -> None:
        # Refused/failed sends leave the clips available for the actual retry/final.
        if self.state is not None and getattr(result, "success", False):
            self.state.delivered = max(self.state.delivered, self.through)


def _has_reply_text(adapter, chat_id, content: str) -> bool:
    """An attachment-only reply must not turn into a standalone transcript notice."""
    with adapter._media_delivery_scope(adapter.build_source(chat_id=chat_id)):
        _, text = adapter.extract_media(content)
        _, text = adapter.extract_images(text)
        _, text = adapter.extract_local_files(text)
    return bool(text.strip())


@asynccontextmanager
async def reply_payload(adapter, chat_id, content, metadata):
    """Serialize replies for ONE event through send ACK, including native retries.

    The prepared flag is wire-invisible and only disables chatty/line splitting;
    Weixin still applies its canonical maximum-length packing to the whole payload.
    """
    state = (metadata or {}).get(_STATE)
    if (getattr(adapter, "platform", None) != Platform.WEIXIN
            or not isinstance(state, VoiceReplyEcho) or state.chat_id != str(chat_id)
            or not content or not _has_reply_text(adapter, chat_id, content)):
        yield ReplyPayload(content, metadata)
        return
    async with state.lock:
        prepared = {key: value for key, value in (metadata or {}).items() if key != _STATE}
        through = len(state.transcripts)
        tail = state.transcripts[state.delivered:through]
        if tail:
            echoes = "\n".join(t("gateway.voice.transcript_echo_short", text=text) for text in tail)
            content = f"{echoes}\n\n{content}"
            prepared[_PAYLOAD] = True
        yield ReplyPayload(content, prepared, state, through)


def is_echo_payload(metadata) -> bool:
    return bool((metadata or {}).get(_PAYLOAD))
