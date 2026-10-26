"""Durable message provenance and content-digest helpers for Conversation History.

The stored ``role`` is the native provider role.  It is not, by itself, proof
that a user-role row contains something the person actually said: Notebook
results, reminders and framework carriers are durable user-role rows too.
This module is the one pure classifier used by the History projection so the
tool and its tests agree on that distinction.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from typing import Any

HUMAN = "human"
ASSISTANT = "assistant"
TOOL = "tool"
SYSTEM = "system"
FRAMEWORK = "framework"
NOTEBOOK = "notebook"

KINDS = frozenset({HUMAN, ASSISTANT, TOOL, SYSTEM, FRAMEWORK, NOTEBOOK})

# A physical role may carry more than one provenance kind (``user`` can be a
# real human turn, a framework carrier, or a Notebook result).  This mapping is
# only the *default* used when the caller does not supply kinds explicitly.
ROLE_TO_KINDS = {
    "user": frozenset({HUMAN}),
    "assistant": frozenset({ASSISTANT}),
    "tool": frozenset({TOOL}),
    "system": frozenset({SYSTEM}),
}

KIND_TO_ROLES = {
    HUMAN: frozenset({"user"}),
    ASSISTANT: frozenset({"assistant"}),
    TOOL: frozenset({"tool"}),
    SYSTEM: frozenset({"system"}),
    FRAMEWORK: frozenset({"user"}),
    NOTEBOOK: frozenset({"user"}),
}

# Display kinds produced by runtime-owned carriers.  Anything non-empty that is
# not an explicit human kind is classified as framework (fail closed): a search
# must never mistake an unknown synthetic carrier for the person's own words.
_SYNTHETIC_DISPLAY_KINDS = frozenset({
    "process_complete",
    "model_switch",
    "skill_invocation",
    "auto_continue",
    "async_delegation_complete",
    "system_reminder",
    "instant_reminder",
    "deferred_reminder",
    "noting_task",
    "compaction",
})
_HUMAN_DISPLAY_KINDS = frozenset({"", "steer"})
SYNTHETIC_DISPLAY_KINDS = _SYNTHETIC_DISPLAY_KINDS

# Legacy text by itself is not a provenance stamp: people may quote any
# wrapper. Persisted admission receipts or exact native producer framing can
# enrich the source before this pure classifier is called.
_NOTEBOOK_TEXT_MARKERS = ("CURRENT NOTEBOOK SNAPSHOT", "NOTING RESULT")


def _tool_name(row: Any) -> str:
    name = row.get("tool_name") if isinstance(row, dict) else None
    return name if isinstance(name, str) and name.strip() else "unknown"


def _notebook_body(row: Any, metadata: dict) -> bool:
    if metadata.get("noting_run_output") is True or metadata.get("noting_snapshot_id"):
        return True
    text = row.get("content")
    if not isinstance(text, str):
        text = metadata.get("display_text")
    if not isinstance(text, str):
        return False
    return any(marker in text for marker in _NOTEBOOK_TEXT_MARKERS)


def message_provenance(row: Any) -> tuple[str, str]:
    """Return ``(kind, source)`` for one durable message/projection row.

    ``kind`` is the coarse evidence category (human/assistant/tool/system/
    framework/notebook); ``source`` is a stable human-readable detail string.
    The function never infers a human source from a user-role carrier whose
    runtime provenance says otherwise.
    """
    if not isinstance(row, dict):
        return FRAMEWORK, "framework:unknown"
    role = row.get("role")
    if row.get("is_compaction") and row.get("projection_kind") in {"compaction", "system_context"}:
        return FRAMEWORK, "framework:compaction"
    metadata = row.get("display_metadata")
    if not isinstance(metadata, dict):
        metadata = {}
    origin = metadata.get("origin")
    display_kind = row.get("display_kind")
    # Runtime provenance outranks the native provider role, including assistant
    # and user carriers. Plain user text mentioning Notebook is never a stamp.
    if origin or metadata.get("noting_run_output") or metadata.get("noting_snapshot_id"):
        if origin == NOTEBOOK or metadata.get("noting_run_output") or metadata.get("noting_snapshot_id"):
            return NOTEBOOK, "notebook:noting_result"
        return FRAMEWORK, "framework:" + str(metadata.get("producer") or origin)
    if display_kind and display_kind not in _HUMAN_DISPLAY_KINDS:
        if _notebook_body(row, metadata):
            return NOTEBOOK, "notebook:noting_result"
        detail = metadata.get("producer") or display_kind
        if display_kind not in _SYNTHETIC_DISPLAY_KINDS:
            detail = "unknown:" + str(display_kind)
        return FRAMEWORK, "framework:" + str(detail)
    if role == "tool":
        return TOOL, f"tool:{_tool_name(row)}"
    if role == "assistant":
        return ASSISTANT, "assistant"
    if role == "system":
        return SYSTEM, "system"
    if role != "user":
        return FRAMEWORK, "framework:" + str(role or "unknown")
    return HUMAN, "human"


def instant_carrier(conn, row):
    """Exact native admission proof, bound to the physical source's owner.

    Never look up a receipt by UID alone or by the caller's Conversation. A
    branch keeps the original row/session owner; a foreign identical UID/body
    or a changed same-owner body cannot borrow this proof.
    """
    if not isinstance(row.get("content"), str):
        return False
    return conn.execute(
        "SELECT 1 FROM secretary_pending_reminders p "
        "JOIN secretary_session_bindings b ON b.conversation_ref=p.conversation_ref "
        "JOIN messages m ON m.session_id=b.session_id "
        "WHERE m.id=? AND m.session_id=? AND m.message_uid=? AND m.content=? AND m.role='user' "
        "AND p.carrier_message_uid=m.message_uid AND p.carrier_content=m.content "
        "AND (p.origin_instant=1 OR p.delivery_semantics='user_reminder') LIMIT 1",
        (row.get("id"), row.get("session_id"), row.get("message_uid"), row.get("content")),
    ).fetchone() is not None


# Exact secretary/heartbeat.py producer before 351770eaeb1bdbfb7d4761ec1afbc84cbb91713c.
# Keep the complete historical instruction, rather than matching its keywords.
_LEGACY_HEARTBEAT_INSTRUCTION = (
    "Check what you can do: attend to the user's current state, remind the user of relevant matters, "
    "delegate agent tasks and verify their results, register schedules (do not rely on heartbeat), "
    "and follow up on anything else that needs attention.\n"
    "Finish by replying with HEARTBEAT_OVER."
)


def _legacy_heartbeat(content, timestamp):
    """Recognize the complete native producer, never arbitrary heartbeat words."""
    from secretary.heartbeat import HEARTBEAT_INSTRUCTION

    if not isinstance(content, str):
        return False
    opening, closing = "<heartbeat>\n", "\n</heartbeat>"
    if not content.startswith(opening) or not content.endswith(closing):
        return False
    stamp, separator, body = content[len(opening):-len(closing)].partition("\n")
    if not separator or not stamp.startswith("<timestamp>") or not stamp.endswith("</timestamp>"):
        return False
    try:
        instant = datetime.fromisoformat(stamp[len("<timestamp>"):-len("</timestamp>")].replace("Z", "+00:00"))
        if instant.tzinfo is None or abs(instant.timestamp() - float(timestamp)) >= 1:
            return False
    except (TypeError, ValueError, OverflowError, OSError):
        return False
    instructions = (HEARTBEAT_INSTRUCTION, _LEGACY_HEARTBEAT_INSTRUCTION)
    return any(body == instruction or body.startswith(instruction + "\n\nAdditional prompt:\n")
               for instruction in instructions)


def _native_reminder_origin(conn, row):
    if not isinstance(row.get("content"), str):
        return None
    if instant_carrier(conn, row):
        return "instant_reminder"
    found = conn.execute(
        "SELECT 1 FROM secretary_pending_reminders p "
        "JOIN secretary_session_bindings b ON b.conversation_ref=p.conversation_ref "
        "JOIN messages m ON m.session_id=b.session_id "
        "WHERE m.id=? AND m.session_id=? AND m.message_uid=? AND m.content=? AND m.role='user' "
        "AND p.carrier_message_uid=m.message_uid AND p.carrier_content=m.content LIMIT 1",
        (row.get("id"), row.get("session_id"), row.get("message_uid"), row.get("content")),
    ).fetchone()
    return "deferred_reminder" if found is not None else None


def enrich_message_source(db, conn, row, *, content_decoded=False):
    """Decode a real source and add read-only runtime provenance evidence.

    Existing trusted metadata wins. Steer is the native human-source witness,
    so its quoted wrapper is never reinterpreted as an autonomous admission.
    """
    result = dict(row)
    if not content_decoded and isinstance(result.get("content"), str):
        result["content"] = db._decode_content(result["content"])
    metadata = result.get("display_metadata")
    if isinstance(metadata, str):
        metadata = json.loads(metadata)
    result["display_metadata"] = dict(metadata) if isinstance(metadata, dict) else {}
    if message_provenance(result)[0] != HUMAN or result.get("display_kind") == "steer":
        return result
    # Query against the exact raw source bytes, not the decoded/projected view.
    origin = _native_reminder_origin(conn, row)
    if origin is None and _legacy_heartbeat(result.get("content"), result.get("timestamp")):
        origin = "heartbeat"
    if origin is not None:
        result["display_metadata"].update(origin="framework", producer=origin)
    return result


def semantic_role(row: Any) -> str:
    """Public role of the evidence, independent of the provider storage role."""
    kind, _ = message_provenance(row)
    if kind == HUMAN:
        return "user"
    if kind == ASSISTANT:
        if normalize_tool_calls(row.get("tool_calls")) and not content_text(row.get("content")).strip():
            return "tools"
        return "assistant"
    if kind == TOOL:
        return "tools"
    return "system"


def content_text(content: Any) -> str:
    """Stable text used for length/digest calculations, never for display."""
    if isinstance(content, str):
        return content
    if content is None:
        return ""
    try:
        return json.dumps(content, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    except (TypeError, ValueError):
        return str(content)


def content_chars(content: Any) -> int:
    return len(content_text(content))


def content_digest(content: Any) -> str:
    return "sha256:" + hashlib.sha256(content_text(content).encode("utf-8")).hexdigest()[:16]


def _canonical_args(arguments: Any) -> str:
    if isinstance(arguments, str):
        try:
            parsed = json.loads(arguments)
        except (TypeError, ValueError):
            return arguments
        return json.dumps(parsed, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if arguments is None:
        return ""
    try:
        return json.dumps(arguments, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=str)
    except (TypeError, ValueError):
        return str(arguments)


def argument_digest(arguments: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical_args(arguments).encode("utf-8")).hexdigest()[:16]


def normalize_tool_calls(raw: Any) -> list | None:
    """Parse the stored tool_calls column; ``None`` means malformed."""
    if raw is None:
        return []
    calls = raw
    if isinstance(raw, str):
        try:
            calls = json.loads(raw)
        except (TypeError, ValueError):
            return None
    if not isinstance(calls, list):
        return None
    return [call for call in calls if isinstance(call, dict)]


def tool_call_digests(raw: Any) -> list | None:
    calls = normalize_tool_calls(raw)
    if calls is None:
        return None
    result = []
    for call in calls:
        function = call.get("function")
        if not isinstance(function, dict):
            function = {}
        name = function.get("name")
        if not isinstance(name, str) or not name.strip():
            name = call.get("name")
        if not isinstance(name, str) or not name.strip():
            name = "unknown"
        arguments = function.get("arguments", call.get("arguments"))
        result.append({"name": name, "args_digest": argument_digest(arguments)})
    return result


def tool_call_names(raw: Any) -> list[str]:
    calls = normalize_tool_calls(raw) or []
    names = []
    for call in calls:
        function = call.get("function")
        if not isinstance(function, dict):
            function = {}
        name = function.get("name")
        if not isinstance(name, str) or not name.strip():
            name = call.get("name")
        if isinstance(name, str) and name.strip():
            names.append(name)
    return names
