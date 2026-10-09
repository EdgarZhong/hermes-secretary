"""Read-only current Conversation History Foreground; shared by main and Noting."""

import json
import re

from hermes_cli.timefmt import coerce_epoch
from tools.registry import registry


SESSION_HISTORY_SCHEMA = {
    "name": "session_history",
    "description": "Search/read authentic history of the current Conversation across compaction. Read-only; no other Conversations.",
    "parameters": {
        "type": "object",
        "properties": {
            "mode": {"type": "string", "enum": ["search", "read"]},
            "query": {"type": "string"}, "match": {"type": "string", "enum": ["keyword", "regex"]},
            "roles": {"type": "array", "items": {"type": "string", "enum": ["user", "assistant", "tool", "system"]}},
            "limit": {"type": "integer", "minimum": 1, "maximum": 200},
            "message_id": {"type": "integer"},
            "message_identity": {
                "type": "object", "description": "Read a canonical Candidate source identity in the current Conversation.",
                "properties": {"conversation_ref": {"type": "string"}, "message_uid": {"type": "string"}},
                "required": ["conversation_ref", "message_uid"], "additionalProperties": False,
            },
            "before": {"type": "integer", "minimum": 0, "maximum": 100},
            "after": {"type": "integer", "minimum": 0, "maximum": 100},
            "start_time": {"type": "string", "description": "Inclusive ISO timestamp or epoch seconds"},
            "end_time": {"type": "string", "description": "Inclusive ISO timestamp or epoch seconds"},
        },
        "required": ["mode"], "additionalProperties": False,
    },
}


def _bounded_int(value, default, minimum, maximum):
    result = default if value is None else value
    if isinstance(result, bool) or not isinstance(result, int) or not minimum <= result <= maximum:
        raise ValueError(f"Integer must be between {minimum} and {maximum}")
    return result


def _time_bound(value):
    if value is None:
        return None
    result = coerce_epoch(value)
    if result is None:
        raise ValueError("Invalid time bound")
    return result


def _select_history(db, session_id, conversation_ref, args):
    ref = conversation_ref or db.resolve_conversation_ref(session_id)
    with db._read_ctx() as conn:
        rows = db.get_history_foreground_conn(conn, ref)
        message_id = args.get("message_id")
        identity = args.get("message_identity")
        if args.get("mode") == "read" and (message_id is not None or identity is not None):
            if message_id is not None:
                if isinstance(message_id, bool) or not isinstance(message_id, int):
                    raise ValueError("message_id must be an integer")
                physical_identity = db.normalize_message_identity_conn(conn, ref, message_id)
                if identity is not None and identity != physical_identity:
                    raise ValueError("message_id and message_identity differ")
                identity = physical_identity
            if (not isinstance(identity, dict) or set(identity) != {"conversation_ref", "message_uid"}
                    or identity["conversation_ref"] != ref or not isinstance(identity["message_uid"], str)
                    or not identity["message_uid"]):
                raise ValueError("message_identity must belong to the current Conversation")
            index = next((i for i, row in enumerate(rows) if row["message_identity"] == identity), None)
            if index is None:
                raise ValueError("Message Identity is missing or outside the current Conversation path")
            before = _bounded_int(args.get("before"), 2, 0, 100)
            after = _bounded_int(args.get("after"), 3, 0, 100)
            rows = rows[max(0, index - before):index + after + 1]
    roles = args.get("roles")
    if roles is not None and (not isinstance(roles, list) or any(role not in {"user", "assistant", "tool", "system"} for role in roles)):
        raise ValueError("Invalid roles")
    start, end = _time_bound(args.get("start_time")), _time_bound(args.get("end_time"))
    if start is not None and end is not None and start > end:
        raise ValueError("start_time is after end_time")
    rows = [row for row in rows if (roles is None or row["role"] in roles)
            and (start is None or row["timestamp"] >= start) and (end is None or row["timestamp"] <= end)]
    if args["mode"] == "search":
        query, match = args.get("query", ""), args.get("match", "keyword")
        if not isinstance(query, str) or not query:
            raise ValueError("Search requires a nonempty query")
        if match not in {"keyword", "regex"}:
            raise ValueError("Invalid match mode")
        pattern = re.compile(query, re.IGNORECASE) if match == "regex" else None
        def matches(row):
            content = row["content"] if isinstance(row["content"], str) else json.dumps(row["content"], ensure_ascii=False)
            return bool(pattern.search(content)) if pattern else query.casefold() in content.casefold()
        rows = [row for row in rows if matches(row)]
    return rows[:_bounded_int(args.get("limit"), 20, 1, 200)]


def session_history(args=None, *, db=None, current_session_id=None, conversation_ref=None, **kwargs):
    """The caller, never model arguments, supplies the owning DB/Conversation."""
    args = dict(args or {})
    args.update(kwargs)
    try:
        unknown = set(args) - set(SESSION_HISTORY_SCHEMA["parameters"]["properties"])
        if unknown:
            raise ValueError("Unsupported History arguments: " + ", ".join(sorted(unknown)))
        if args.get("mode") not in {"search", "read"}:
            raise ValueError("mode must be search or read")
        if db is None or not (current_session_id or conversation_ref):
            raise ValueError("Current Conversation state is unavailable")
        rows = _select_history(db, current_session_id, conversation_ref, args)
        public = [{key: row[key] for key in ("message_id", "message_identity", "message_uid", "timestamp", "role", "content")} for row in rows]
        return json.dumps({"success": True, "messages": public, "count": len(public)}, ensure_ascii=False)
    except (ValueError, TypeError, re.error) as exc:
        return json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False)


registry.register(
    name="session_history", toolset="session_history", schema=SESSION_HISTORY_SCHEMA,
    handler=lambda args, **kw: session_history(args, db=kw.get("db"), current_session_id=kw.get("current_session_id"),
                                             conversation_ref=kw.get("conversation_ref")),
    emoji="📖",
)
