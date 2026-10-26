"""Source-preserving public previews and same-invocation tool projections."""

import re
from datetime import datetime

from hermes_cli.timefmt import coerce_epoch
from agent.message_metadata import strip_user_timestamp_marker
from hermes_state_message_provenance import content_text, normalize_tool_calls, semantic_role

# Only runtime-owned outer wrappers; never strip arbitrary HTML or date strings.
_WRAPPER = re.compile(
    r"\A<(framework-message|instant-reminder|deferred-reminder|noting-task|"
    r"system-reminder|user-reminder|heartbeat)>\s*\n?(.*?)\n?</\1>\s*\Z", re.S)


def head_tail(content):
    text = content_text(content)
    return text if len(text) <= 200 else text[:100] + text[-100:]


def _strip_stamp(content, row, *, trusted_carrier=False):
    text = content
    if isinstance(content, list) and content and isinstance(content[0], dict):
        text = content[0].get("text")
    if not isinstance(text, str):
        return content
    match = re.match(r"\A<timestamp>([^<]+)</timestamp>(?:\n|$)", text)
    if match is None:
        return content
    try:
        instant = datetime.fromisoformat(match.group(1).replace("Z", "+00:00"))
        epoch = coerce_epoch(row.get("timestamp"))
        if instant.tzinfo is None:
            return content
        if not trusted_carrier and (epoch is None or abs(instant.timestamp() - epoch) >= 1):
            return content
    except (ValueError, OverflowError, OSError):
        return content
    return strip_user_timestamp_marker(content)


def _cleaned_content(row):
    if row.get("projection_kind") == "system_context":
        return "\n\n".join(_cleaned_content(part) for part in row["_history_preview_parts"])
    content = _strip_stamp(row.get("content"), row)
    text = content_text(content)
    if row.get("display_kind") == "steer" and semantic_role(row) == "user":
        from agent.prompt_builder import STEER_MARKER_CLOSE, STEER_MARKER_OPEN
        opening, closing = STEER_MARKER_OPEN + "\n", "\n" + STEER_MARKER_CLOSE
        if text.startswith(opening) and text.endswith(closing):
            text = content_text(_strip_stamp(text[len(opening):-len(closing)], row))
    if row.get("is_compaction") and row.get("projection_kind") == "compaction":
        from agent.context_compressor import ContextCompressor, _content_text_for_contains
        text = ContextCompressor._strip_summary_prefix(_content_text_for_contains(content))
    if semantic_role(row) == "system":
        match = _WRAPPER.fullmatch(text)
        while match:
            text = content_text(_strip_stamp(match.group(2), row, trusted_carrier=True))
            match = _WRAPPER.fullmatch(text)
    return text


def cleaned_preview(row):
    return head_tail(_cleaned_content(row))


def _call(call):
    function = call.get("function")
    function = function if isinstance(function, dict) else call
    return {"tool_call_id": call.get("id"), "name": function.get("name") or "unknown",
            "arguments": function.get("arguments"), "result": None}


class ToolInvocations:
    """Pair by call ID within its actual assistant batch on this legal path.

    The latest assistant batch replaces previous pending IDs. A result consumes
    its ID once; duplicate IDs within a batch are ambiguous and remain unknown.
    No pairing follows hidden/rewound rows or reaches into another Conversation.
    """

    def __init__(self, rows, visible_uids=None):
        self.by_uid = {}
        pending = {}
        for row in rows:
            if row.get("is_compaction"):
                continue
            if row["role"] == "assistant" or semantic_role(row) == "user":
                pending = {}
            if visible_uids is not None and row["message_uid"] not in visible_uids:
                if row["role"] in {"user", "system"}:
                    pending = {}
                if row["role"] == "tool":
                    pending.pop(row.get("tool_call_id"), None)
                continue
            if row["role"] == "assistant":
                calls = [_call(call) for call in (normalize_tool_calls(row.get("tool_calls")) or [])]
                if calls:
                    self.by_uid[row["message_uid"]] = calls
                for call in calls:
                    key = call["tool_call_id"]
                    if key:
                        pending[key] = call if key not in pending else None
            elif row["role"] == "tool":
                call = pending.pop(row.get("tool_call_id"), None)
                if call is None:
                    call = {"tool_call_id": row.get("tool_call_id"),
                            "name": row.get("tool_name") or "unknown", "arguments": None,
                            "result": row.get("content")}
                else:
                    call["result"] = row.get("content")
                self.by_uid[row["message_uid"]] = [call]

    def content(self, row, *, preview=False):
        calls = self.by_uid.get(row["message_uid"], [])
        projected = []
        for call in calls:
            item = dict(call)
            if preview:
                for key in ("arguments", "result"):
                    if item[key] is not None:
                        item[key] = head_tail(item[key])
            projected.append(item)
        if row["role"] == "tool":
            call = projected[0]
            return {"arguments": call["arguments"], "result": call["result"]}
        return {"content": row.get("content"), "tool_calls": projected}
