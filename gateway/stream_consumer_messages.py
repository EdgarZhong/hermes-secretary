"""Identity-scoped complete messages on the existing stream consumer FIFO."""

from dataclasses import dataclass
import logging

from gateway.response_filters import is_intentional_silence_response

logger = logging.getLogger(__name__)


@dataclass
class OrderedMessage:
    identity: str
    text: object


def finish_native_message(ctx, result, consumer):
    """Bind an opted-in gateway final to the existing identity-scoped FIFO."""
    if (not isinstance(result, dict) or result.get("failed") or result.get("interrupted")
            or not isinstance(result.get("final_response"), str)
            or not callable(getattr(type(consumer), "bind_final_message", None))):
        return False

    def confirm_native_delivery():
        # The FIFO can succeed before result construction. Replay only that real
        # receipt, while its original turn and consumer still own the result.
        holder = ctx.stream_consumer_holder
        if ctx._run_still_current() and holder and holder[0] is consumer:
            result["already_sent"] = True

    identity = result.get("final_message_uid")
    consumer.bind_final_message(identity, result["final_response"], on_delivered=confirm_native_delivery)
    if (getattr(consumer, "native_message_delivery", False) is not True
            or result.get("completed") is False or not isinstance(identity, str) or not identity):
        return False
    # A successful send skips this UID; failure retries on the same FIFO. If
    # that also fails, the ordinary gateway final send remains responsible.
    # Never add a competing text-only final to the native-message consumer.
    consumer.on_message(identity, result["final_response"])
    consumer.finish()
    return True


class OrderedMessagesMixin:
    def bind_final_message(self, identity, text, *, on_delivered=None):
        self._ordered_final_message = OrderedMessage(identity, text)
        self._ordered_final_on_delivered = on_delivered

    def _confirm_ordered_final(self):
        final = getattr(self, "_ordered_final_message", None)
        receipts = getattr(self, "_delivered_message_payloads", {})
        if (final is None or not final.identity or final.identity not in receipts
                or not self._run_still_current()):
            return False
        # A successful native message UID is the receipt. Cleanup can append a footer
        # after that message completed; it neither creates a new message nor revokes
        # delivery. Record what was actually sent, never the later tail payload.
        self._mark_final_delivered(record=receipts[final.identity])
        callback = getattr(self, "_ordered_final_on_delivered", None)
        if callback is not None:
            callback()
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
        if self.native_message_delivery and (
            text == "(empty)" or is_intentional_silence_response(self._clean_for_display(str(text)))
        ):
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
