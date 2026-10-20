"""Human reply delivery brackets, kept separate from model history."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from agent.i18n import t
from gateway.platforms.event import MessageEvent
from gateway.voice_reply_echo import event_echo, reply_metadata, reply_payload

logger = logging.getLogger("gateway.platforms.base")


async def send_final_reply(
    self, event: MessageEvent, session_key: str, text_content: str, metadata: Dict[str, Any], *,
    reply_to: Optional[str], is_ephemeral_response: bool = False,
) -> tuple[Any, Any]:
    """The delivery-ledger bracket every final text goes through, on the CURRENT transport
    (a reconnect may have replaced this adapter): record the obligation before the send,
    send with retry, finalize from the result — so a refused final (flood control, a dead
    transport) leaves a ledger row the boot sweep / runtime redelivery can act on. ``event``
    supplies the source and the ledger identity (``ledger_message_id`` or ``message_id``).
    Returns the result with the adapter that sent it: that adapter owns ``result.message_id``
    (an ephemeral delete must go to the same transport)."""
    from gateway.platforms.base import stop_reply_clock

    delivery_adapter = self._final_delivery_adapter(event.source)
    metadata = reply_metadata(metadata, event_echo(event))
    async with reply_payload(delivery_adapter, event.source.chat_id, text_content, metadata) as payload:
        logger.info("[%s] Sending response (%d chars) to %s", delivery_adapter.name,
                    len(text_content), event.source.chat_id)
        obligation_id = await self._record_delivery_obligation(
            event, session_key, payload.content, delivery_adapter, is_ephemeral_response)
        if obligation_id is not None:
            await self._release_turn_marker(event)  # the ledger now owns the crash recovery
        result = await delivery_adapter._send_with_retry(
            chat_id=event.source.chat_id, content=payload.content, reply_to=reply_to, metadata=payload.metadata)
        payload.acknowledge(result)
        stop_reply_clock(delivery_adapter, event.source.chat_id, result)
        if obligation_id is not None:
            await self._finalize_delivery_obligation(obligation_id, result, event, delivery_adapter)
        return result, delivery_adapter


async def notify_turn_error(self, event: MessageEvent, e: BaseException) -> Optional[dict]:
    """Tell the user a turn failed rather than leaving radio silence (last resort:
    a failing notice is logged, never raised). Returns the thread metadata used."""
    from gateway.platforms.base import _thread_metadata_for_event, diagnostic_wake_muted

    _thread_metadata = None
    try:
        _thread_metadata = _thread_metadata_for_event(event)
        error_detail = str(e)[:300] if str(e) else t("gateway.notify.turn_error_no_details")
        # Only the policy reads bind the routed profile; the send stays in the launch scope
        # as before, so delivery bookkeeping keeps landing where boot-time recovery reads it.
        with self._media_delivery_scope(event.source):
            content = None if diagnostic_wake_muted(event) else self.warning_text(
                t("gateway.notify.turn_error_detailed", error_type=type(e).__name__, error_detail=error_detail),
                t("gateway.notify.turn_error"),
                logical_platform=event.source.platform, chat_id=event.source.chat_id, metadata=_thread_metadata)
        if content is None:
            return _thread_metadata
        await self.send(chat_id=event.source.chat_id, content=content, metadata=reply_metadata(_thread_metadata, event_echo(event)))
    except Exception as notify_err:
        logger.error(
            "[%s] Failed to send error notification to user: %s", self.name, notify_err, exc_info=True)
    return _thread_metadata
