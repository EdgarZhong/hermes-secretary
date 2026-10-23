"""Attach a Weixin acknowledgement to the native redirect checkpoint, never guessed deltas."""

import concurrent.futures
import logging
import os
import time
import uuid

from agent.interrupt_compat import _accepts_keyword
from gateway.config import Platform

logger = logging.getLogger(__name__)


def redirect_with_receipt(runner, agent, text, session_key, event):
    """Return None for the native legacy path, otherwise the redirect acceptance result."""
    if event.source.platform != Platform.WEIXIN:
        return None
    state = runner._peek_session_state(session_key)
    ctx = state.turn.ctx if state is not None else None
    consumer = ctx.stream_consumer_holder[0] if ctx is not None else None
    if (consumer is None or state.turn.agent is not agent
            or not callable(ctx._run_still_current) or not ctx._run_still_current()
            or getattr(agent, "_executing_tools", False)
            or getattr(agent, "api_mode", None) == "codex_app_server"
            or not _accepts_keyword(agent.redirect, "on_applied")):
        return None
    ready = concurrent.futures.Future()
    identity = "redirect:" + uuid.uuid4().hex
    now = time.time()
    show_empty = (os.environ.get("HERMES_GATEWAY_BUSY_ACK_ENABLED", "true").lower() == "true"
                  and now - state.turn.busy_ack_ts >= 30)

    def applied(partial):
        payload = concurrent.futures.Future()
        # Enqueue at the checkpoint before any following Assistant Message.
        consumer.on_message(identity, payload)
        def prepare(done):
            ack = done.result()
            payload.set_result(f"{partial}\n\n{ack}" if partial else ack if show_empty else "")
        ready.add_done_callback(prepare)

    try:
        accepted = agent.redirect(runner._steer_text_with_origin(text, event), on_applied=applied)
    except Exception:
        logger.warning("Weixin redirect failed", exc_info=True)
        return False
    if accepted:
        event._weixin_redirect_ack_deferred = True
        try:
            message = runner._compose_busy_ack_message(
                event, now, state, agent, is_steer_mode=False, is_queue_mode=False,
                is_redirect_mode=True, demoted_for_subagents=False, demoted_for_compression=False)
        except Exception:
            logger.warning("Weixin redirect acknowledgement rendering failed", exc_info=True)
            from agent.i18n import t
            message = t("gateway.busy.ack", head=t("gateway.busy.redirected_head"), detail="",
                        tail=t("gateway.busy.redirected_tail"))
        ready.set_result(message)
        if show_empty:
            state.turn.busy_ack_ts = now
    return accepted
