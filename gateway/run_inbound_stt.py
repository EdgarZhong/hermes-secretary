"""Inbound STT preparation and human transcript echo policy."""

from __future__ import annotations

import asyncio
import logging
from typing import List, Optional

from agent.i18n import t
from gateway.platforms.event import MessageEvent
from gateway.run_common import _UNSET
from gateway.session import SessionSource
from gateway.voice_reply_echo import defer_voice_echo

logger = logging.getLogger("gateway.run")


class GatewayInboundSTTMixin:
    async def _echo_stt_transcripts(
        self, adapter, source: SessionSource, transcripts: List[str], *, metadata=None, log_context: str = "Transcript"
    ) -> None:
        """Send each transcript back as ``🎙️ "…"`` (best-effort; failures are logged, never raised)."""
        for tx in transcripts:
            try:
                await adapter.send(source.chat_id, t("gateway.voice.transcript_echo_short", text=tx), metadata=metadata)
            except Exception as echo_exc:
                logger.debug("%s echo failed (non-fatal): %s", log_context, echo_exc)

    async def _enrich_inbound_voice(
        self, event: MessageEvent, source: SessionSource, message_text: str, audio_paths: list[str]
    ) -> str:
        message_text, _successful_transcripts = await self._enrich_message_with_transcription(
            message_text, audio_paths,
        )
        # The opt-in Weixin lane carries a human-only sidecar until a model reply.
        # Other platforms retain immediate echoes. STT failures only add a neutral model marker.
        if defer_voice_echo(self, event, source, _successful_transcripts):
            return message_text
        if _successful_transcripts and self._should_echo_stt_transcripts():
            _echo_adapter = self._delivery_adapter_for(source)
            if _echo_adapter:
                _echo_meta = self._thread_metadata_for_source(source, self._reply_anchor_for_event(event))
                await self._echo_stt_transcripts(_echo_adapter, source, _successful_transcripts, metadata=_echo_meta)
        return message_text

    def _pending_event_audio_paths(self, event) -> List[str]:
        """Return STT-eligible paths from a pending voice message."""
        from gateway.run import _event_media_is_stt_input
        return [
            path for i, path in enumerate(getattr(event, "media_urls", None) or [])
            if _event_media_is_stt_input(event, i)
        ]

    async def _transcribe_pending_audio_event_once(self, event, user_text=None):
        # Keep the legacy path unchanged unless this Weixin feature is opted in.
        if not defer_voice_echo(self, event, getattr(event, "source", None), []):
            return await self._transcribe_pending_audio_event(event, user_text)
        lock = getattr(event, "_gateway_pending_stt_lock", None)
        if lock is None:
            event._gateway_pending_stt_lock = lock = asyncio.Lock()
        async with lock:
            while True:
                snapshot = (self._pending_event_audio_paths(event), getattr(event, "text", ""))
                result = await self._transcribe_pending_audio_event(event, user_text)
                if snapshot == (self._pending_event_audio_paths(event), getattr(event, "text", "")):
                    return result
                # Input merged during STT; the old in-flight result is stale.
                user_text = getattr(event, "text", "")
                for attr in ("_gateway_pending_stt_text", "_gateway_pending_stt_transcripts"):
                    if hasattr(event, attr):
                        delattr(event, attr)

    async def _transcribe_pending_audio_event(
        self, event, user_text: Optional[str] = None
    ) -> tuple[str | None, List[str]]:
        """Transcribe a pending audio event once and cache the result on the event: the interrupt
        monitor and the pending-drain path both need it — one STT call and one echo per message."""
        if hasattr(event, "_gateway_pending_stt_text"):
            return event._gateway_pending_stt_text, list(getattr(event, "_gateway_pending_stt_transcripts", []) or [])
        audio_paths = self._pending_event_audio_paths(event)
        if not audio_paths:
            return user_text if user_text is not None else (getattr(event, "text", None) or None), []
        text = user_text if user_text is not None else (getattr(event, "text", "") or "")
        enriched_text, successful_transcripts = await self._enrich_message_with_transcription(text, audio_paths)
        event._gateway_pending_stt_text = enriched_text
        event._gateway_pending_stt_transcripts = list(successful_transcripts)
        return enriched_text, successful_transcripts

    async def _echo_pending_stt_transcripts_once(
        self, event, adapter, source, transcripts: List[str], *, metadata=None,
        log_context: str = "Transcript",
    ) -> None:
        """Echo pending-event STT transcripts to the chat at most once. Tracked as a COUNT (not a
        set — identical transcripts are distinct deliveries): ``merge_pending_message_event`` can
        append a second voice note and invalidate the cache; the re-run returns earlier transcripts
        as a prefix, so only the unsent tail is echoed."""
        if not transcripts or not self._should_echo_stt_transcripts() or adapter is None:
            return
        if defer_voice_echo(self, event, source, transcripts):
            return
        already_echoed = int(getattr(event, "_gateway_pending_stt_echoed", 0) or 0)
        event._gateway_pending_stt_echoed = max(already_echoed, len(transcripts))
        await self._echo_stt_transcripts(
            adapter, source, transcripts[already_echoed:], metadata=metadata, log_context=log_context,
        )

    async def _transcribe_and_echo_pending_voice(
        self, event, adapter, source, text: str, *, log_context: str, metadata=_UNSET
    ) -> tuple[str, List[str]]:
        """Transcribe a pending voice event and echo transcripts once → ``(enriched_text,
        transcripts)`` for ``agent.interrupt()`` or the pending-drain flow; ``(text, [])`` when there
        is no STT-eligible media (caller owns the ``_build_media_placeholder`` fallback)."""
        if not self._pending_event_audio_paths(event):
            return text, []
        try:
            enriched_text, transcripts = await self._transcribe_pending_audio_event_once(event, text)
            if metadata is _UNSET:
                metadata = self._thread_metadata_for_source(source, self._reply_anchor_for_event(event))
            await self._echo_pending_stt_transcripts_once(
                event, adapter, source, transcripts, metadata=metadata, log_context=log_context
            )
            return enriched_text or text, transcripts
        except Exception as trans_exc:
            logger.warning("%s transcription failed: %s", log_context, trans_exc)
            return text, []
