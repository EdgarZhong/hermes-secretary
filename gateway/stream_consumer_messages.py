"""Identity-scoped complete messages on the existing stream consumer FIFO."""

from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class OrderedMessage:
    identity: str
    text: object


class OrderedMessagesMixin:
    def bind_final_message(self, identity, text):
        self._ordered_final_message = OrderedMessage(identity, text)

    def _confirm_ordered_final(self):
        final = getattr(self, "_ordered_final_message", None)
        receipts = getattr(self, "_delivered_message_payloads", {})
        if final is None or not final.identity or final.identity not in receipts:
            return False
        if self._display_payload(receipts[final.identity]) != self._display_payload(final.text):
            return False
        self._mark_final_delivered(record=final.text)
        return True

    def on_message(self, identity, text):
        self._enqueue(OrderedMessage(identity, text))

    async def _deliver_message(self, message):
        import asyncio
        import concurrent.futures

        delivered = vars(self).setdefault("_delivered_message_ids", set())
        if message.identity in delivered or not self._run_still_current():
            return
        text = message.text
        if isinstance(text, concurrent.futures.Future):
            text = await asyncio.wrap_future(text)
        if not text or not self._run_still_current():
            return
        try:
            metadata = dict(self.metadata or {})
            metadata["_interim_send"] = True
            result = await self.adapter.send(self.chat_id, str(text), metadata=metadata)
            if result.success and self._run_still_current():
                delivered.add(message.identity)
                vars(self).setdefault("_delivered_message_payloads", {})[message.identity] = str(text)
                self._notify_new_message()
            elif not result.success:
                logger.warning("Ordered assistant message delivery not confirmed: %s",
                               getattr(result, "error", None) or "adapter declined")
        except Exception:
            logger.warning("Ordered assistant message send failed", exc_info=True)
