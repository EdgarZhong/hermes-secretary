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

# Wrapper tags emitted by the runtime before a carrier is persisted.  The
# durable wrapper is the fallback witness for historical rows that predate the
# explicit display_metadata origin stamp.
_WRAPPER_SOURCES = (
    ("<framework-message>", "framework:framework_message"),
    ("<instant-reminder>", "framework:instant_reminder"),
    ("<deferred-reminder>", "framework:deferred_reminder"),
    ("<noting-task>", "framework:noting_task"),
    ("[CONTEXT COMPACTION", "framework:compaction"),
)
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
    if role == "tool":
        return TOOL, f"tool:{_tool_name(row)}"
    if role == "assistant":
        return ASSISTANT, "assistant"
    if role == "system":
        return SYSTEM, "system"
    if role != "user":
        label = role if isinstance(role, str) and role else "unknown"
        return FRAMEWORK, f"framework:{label}"

    metadata = row.get("display_metadata")
    if not isinstance(metadata, dict):
        metadata = {}

    if _notebook_body(row, metadata):
        return NOTEBOOK, "notebook:noting_result"

    origin = metadata.get("origin")
    if isinstance(origin, str) and origin.strip():
        producer = metadata.get("producer")
        detail = producer if isinstance(producer, str) and producer.strip() else origin.strip()
        if origin.strip() == NOTEBOOK:
            return NOTEBOOK, f"notebook:{detail}"
        return FRAMEWORK, f"framework:{detail}"

    display_kind = row.get("display_kind")
    if isinstance(display_kind, str) and display_kind.strip():
        kind = display_kind.strip()
        if kind in _HUMAN_DISPLAY_KINDS:
            return HUMAN, "human"
        producer = metadata.get("producer")
        detail = producer if isinstance(producer, str) and producer.strip() else kind
        if kind == "process_complete":
            # The body marker above already caught Notebook results; this is a
            # framework carrier such as a reminder or an external notice.
            return FRAMEWORK, f"framework:{detail}"
        if kind in _SYNTHETIC_DISPLAY_KINDS:
            return FRAMEWORK, f"framework:{detail}"
        return FRAMEWORK, f"framework:unknown:{kind}"

    content = row.get("content")
    if isinstance(content, str):
        for prefix, source in _WRAPPER_SOURCES:
            if content.startswith(prefix):
                return FRAMEWORK, source
    return HUMAN, "human"


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
