"""Optional first-paint history projection; durable rows remain the only source."""
from __future__ import annotations

import json
import re

from hermes_state_messages import _DISPLAY_ACTIVE_CLAUSE, DISPLAY_VISIBLE_SQL

_REASONING = ("reasoning", "reasoning_content", "reasoning_details", "display_reasoning")
_CANCELLED = re.compile(
    r"^\[Tool execution cancelled — [\w.-]+ was (?:abandoned:|skipped\.) [\s\S]+\]$")


def detail_row_ids(value: str | None) -> list[int] | None:
    """Small exact-row requests, never an unbounded alternate history scan."""
    if value is None:
        return None
    parts = value.split(",")
    if not 1 <= len(parts) <= 12 or any(not part.isascii() or not part.isdecimal() for part in parts):
        raise ValueError("detail_row_ids requires 1 to 12 positive integer row ids")
    ids = list(dict.fromkeys(int(part) for part in parts))
    if any(not 0 < row_id <= 9223372036854775807 for row_id in ids):
        raise ValueError("detail_row_ids requires positive SQLite row ids")
    return ids


def read_detail_rows(db, session_id: str, row_ids: list[int], *, include_compacted: bool = False) -> list[dict]:
    """Fetch only requested visible rows on this verified compression spine.

    Inactive rewind generations cannot be resurrected by a delayed disclosure read.
    Physical ids deliberately do not follow aliases into a different row or branch.
    ``include_compacted`` mirrors the page read: a caller that never asked for
    archived display history cannot fetch one row of it by id.
    """
    spine = db._resume_lineage_ids(session_id)
    marks = ",".join("?" for _ in spine)
    ids = ",".join("?" for _ in row_ids)
    visible = _DISPLAY_ACTIVE_CLAUSE if include_compacted else " AND active = 1"
    with db._read_ctx() as conn:
        columns = set(db._message_column_names(conn))
        generation = ""
        if "message_uid" in columns:
            generation = f""" AND (NULLIF(messages.message_uid, '') IS NULL OR (
                SELECT generation.active = 1 OR generation.compacted = 1 FROM messages AS generation
                WHERE generation.session_id IN ({marks}) AND generation.message_uid = messages.message_uid
                ORDER BY generation.id DESC LIMIT 1))"""
        rows = conn.execute(
            f"SELECT * FROM messages WHERE session_id IN ({marks}) AND id IN ({ids})"
            f"{visible}{DISPLAY_VISIBLE_SQL}{generation} ORDER BY id",
            (*spine, *row_ids, *(spine if generation else []))).fetchall()
    return [db._row_to_message_dict(row, warn_context="disclosure detail", summary_flag=True) for row in rows]


def _reject_json_constant(value):
    """``json`` accepts NaN/Infinity; the browser's JSON.parse does not."""
    raise ValueError(f"non-standard JSON constant {value}")


def _exit_code_failure(code) -> bool:
    if isinstance(code, bool):
        return False
    if isinstance(code, int):
        return code != 0
    # JSON has one number type and the client's Number.isInteger(2.0) is true, so an
    # integral float must classify the same way here or the status flips on hydration.
    if isinstance(code, float):
        return code.is_integer() and code != 0
    return False


def _failed(result: dict) -> bool:
    return bool(result.get("is_error") or result.get("success") is False or result.get("ok") is False
                or (isinstance(result.get("error"), str) and result["error"].strip())
                or _exit_code_failure(result.get("exit_code"))
                or result.get("status") in ("failed", "error"))


def tool_status(content, metadata: dict) -> str:
    """Same displayed result facts as the existing client, before omitting the body."""
    result = content if isinstance(content, dict) else {}
    if isinstance(content, str):
        try:
            parsed = json.loads(content, parse_constant=_reject_json_constant)
            result = parsed if isinstance(parsed, dict) else {}
        except (ValueError, TypeError):
            pass
    if (metadata.get("status") in ("interrupted", "cancelled")
            or result.get("status") in ("interrupted", "cancelled")
            or (isinstance(content, str) and _CANCELLED.fullmatch(content.strip()))):
        return "interrupted"
    if _failed(metadata) or _failed(result):
        return "failed"
    # Parity with the client's ``toolResultState``: a tool row always carries the
    # ``content`` key, so a stored NULL is that row's empty result (null lands as
    # "complete" there), and only an ABSENT field may claim "unknown" — the
    # terminal-output call site guards that by requiring the key.
    return metadata.get("status") or "complete"


def _tool_calls(calls: list) -> tuple[list, bool]:
    deferred = False
    result = []
    for original in calls:
        if not isinstance(original, dict):
            result.append(original)
            continue
        call = dict(original)
        if "arguments" in call:
            call.pop("arguments")
            deferred = True
        if isinstance(call.get("function"), dict):
            function = dict(call["function"])
            if "arguments" in function:
                function.pop("arguments")
                deferred = True
            call["function"] = function
        result.append(call)
    return result, deferred


def _terminal_metadata(metadata: dict) -> tuple[dict, bool]:
    terminal = metadata.get("turn_terminal")
    if not isinstance(terminal, dict) or not isinstance(terminal.get("outputs"), list):
        return metadata, False
    outputs, deferred = [], False
    for original in terminal["outputs"]:
        if not isinstance(original, dict) or original.get("kind") not in ("reasoning", "tool"):
            outputs.append(original)
            continue
        output = dict(original)
        fields = []
        for field in ("text", "args", "result"):
            if field in output:
                output.pop(field)
                fields.append(field)
        if fields:
            # Only an existing ``result`` field may be judged; an absent one is the
            # client's "unknown" fallback, which must not be replaced by a marker.
            if original.get("kind") == "tool" and original.get("state") == "complete" and "result" in original:
                output["display_tool_status"] = tool_status(original["result"], {})
            output["deferred_details"] = fields
            deferred = True
        outputs.append(output)
    return {**metadata, "turn_terminal": {**terminal, "outputs": outputs}}, deferred


def history_cards(messages: list[dict]) -> list[dict]:
    """Omit disclosure bodies AFTER all normal display/security projections.

    No placeholder text is invented. Explicit markers let the client render the
    existing cards and distinguish unavailable bodies from truly empty results.
    """
    projected = []
    for original in messages:
        message, fields = dict(original), []
        if original.get("role") == "assistant":
            if any(original.get(field) for field in _REASONING):
                fields.append("reasoning")
            for field in _REASONING:
                message.pop(field, None)
            if isinstance(message.get("tool_calls"), list):
                message["tool_calls"], deferred = _tool_calls(message["tool_calls"])
                if deferred:
                    fields.append("tool_arguments")
        if original.get("role") == "tool" and "content" in original:
            message["display_tool_status"] = tool_status(original["content"], original)
            message.pop("content", None)
            fields.append("tool_result")
        metadata = original.get("display_metadata")
        if isinstance(metadata, dict):
            message["display_metadata"], deferred = _terminal_metadata(metadata)
            if deferred:
                fields.append("terminal_outputs")
        for field in ("api_content", "codex_reasoning_items", "codex_message_items"):
            message.pop(field, None)
        if fields:
            message["deferred_details"] = fields
        projected.append(message)
    return projected
