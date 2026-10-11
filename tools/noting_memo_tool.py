"""Main-only scratch pad toward the next background Noting consolidation."""

import json

from tools.registry import registry

NOTING_MEMO_SCHEMA = {
    "name": "noting_memo",
    "description": "Maintain this Conversation's Noting Memo with add, replace, delete, or list. Write a brief one-sentence memo for what the next background consolidation must cover; a non-empty memo keeps local Noting on and does not trigger a run.",
    "parameters": {
        "type": "object", "properties": {
            "operation": {"type": "string", "enum": ["add", "replace", "delete", "list"]},
            "content": {"type": "string"},
            "index": {"type": "integer", "minimum": 1},
        }, "required": ["operation"], "additionalProperties": False,
    },
}


def noting_memo(args=None, *, db=None, conversation_ref=None, effective_enabled=None):
    try:
        if effective_enabled is not True:
            raise ValueError("Noting Memo is unavailable for this runtime")
        if db is None or not conversation_ref:
            raise ValueError("Current Conversation state is unavailable")
        if not isinstance(args, dict):
            raise ValueError("Noting Memo arguments must be an object")
        return db.noting_memo_mutate(conversation_ref, args)
    except (ValueError, TypeError) as exc:
        return json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False)


registry.register(name="noting_memo", toolset="notebook", schema=NOTING_MEMO_SCHEMA,
                  handler=lambda args, **kw: noting_memo(args, db=kw.get("db"),
                      conversation_ref=kw.get("conversation_ref"), effective_enabled=kw.get("effective_enabled")),
                  emoji="📝")
