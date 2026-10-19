"""Model-facing inbound provenance and timestamp application for gateway turns.

The ``<timestamp>`` marker is identical on every surface (Web UI included), so it cannot
identify the messaging channel. ``wrap_inbound_origin`` adds an explicit XML envelope around
the model-facing copy only — the durable transcript and the UI stay clean. The wrapper is
read back from the ``api_content`` sidecar on replay, so the model keeps seeing it.

``apply_message_timestamp`` keeps the platform time as metadata, strips legacy timestamp
prefixes and the Discord triggering note; only in-context rendering is gated by
``gateway.message_timestamps.enabled`` (default OFF).
"""

from __future__ import annotations

import logging
from typing import Any, Optional, Tuple

logger = logging.getLogger(__name__)

# Messaging channels whose model-facing body gets an explicit XML source envelope.
# Extend this mapping for another gateway platform; Web UI never passes through here.
_INBOUND_ORIGIN_LABELS = {"weixin": "微信"}


def wrap_inbound_origin(event: Any, text: str) -> str:
    """Wrap one messaging-channel inbound body in ``<gateway-message from="…">``.

    Web UI turns never pass through this module. Internal/synthetic events keep their own
    carriers and are not user messages, so they are never wrapped.
    """
    if not text or getattr(event, "internal", False):
        return text
    metadata = getattr(event, "metadata", None)
    if isinstance(metadata, dict) and metadata.get("synthetic_prompt"):
        return text
    source = getattr(event, "source", None)
    platform = getattr(source, "platform", None)
    name = getattr(platform, "value", None) or str(platform or "")
    label = _INBOUND_ORIGIN_LABELS.get(name)
    if not label:
        return text
    return f'<gateway-message from="{label}">\n{text}\n</gateway-message>'


def apply_message_timestamp(event: Any, message_text: Any) -> Tuple[Any, Optional[str], Optional[float]]:
    """Return ``(model_text, persist_text, persist_timestamp)`` for one inbound turn."""
    from gateway.run import _load_gateway_config, _message_timestamps_enabled
    from gateway.run_inbound import strip_discord_triggering_note

    persist_user_message = None
    persist_user_timestamp = None
    try:
        from hermes_time import get_timezone as _get_evt_tz
        from gateway.message_timestamps import (
            coerce_message_timestamp as _coerce_msg_ts,
            render_user_content_with_timestamp as _render_msg_ts,
            strip_leading_message_timestamps as _strip_msg_ts,
        )
        _evt_tz = _get_evt_tz()
        if message_text and isinstance(message_text, str):
            _clean_message_text, _embedded_ts = _strip_msg_ts(message_text, tz=_evt_tz)
            persist_user_message = strip_discord_triggering_note(event, _clean_message_text)
            _event_epoch = _coerce_msg_ts(getattr(event, "timestamp", None), tz=_evt_tz)
            persist_user_timestamp = _event_epoch if _event_epoch is not None else _embedded_ts
            if _message_timestamps_enabled(_load_gateway_config()):
                message_text = _render_msg_ts(_clean_message_text, persist_user_timestamp, tz=_evt_tz)
            else:
                # Toggle off: the model sees the clean message; timestamp stored for later opt-in.
                message_text = _clean_message_text
    except Exception as _ts_err:
        logger.debug("Message timestamp injection failed (non-fatal): %s", _ts_err, exc_info=True)
    # Channel provenance for the model only: the timestamp marker is identical on every
    # surface, so it cannot identify the channel. The durable content stays clean.
    message_text = wrap_inbound_origin(event, message_text)
    from agent.message_metadata import preserve_user_input_origin
    message_text = preserve_user_input_origin(event.text, message_text)
    return message_text, persist_user_message, persist_user_timestamp
