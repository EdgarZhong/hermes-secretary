"""Read the Main Conversation's complete effective Notebook Snapshot."""

import json
from pathlib import Path

from secretary.notebook_render import show_notebook
from secretary.noting_contract import NOTEBOOK_SHOW_SCHEMA
from tools.registry import registry


def notebook_show(args=None, *, db=None, conversation_ref=None, effective_enabled=None, **kwargs):
    try:
        if not isinstance(args if args is not None else {}, dict) or args or kwargs:
            raise ValueError("notebook_show accepts only an empty argument object")
        if db is None or not conversation_ref or effective_enabled is not True:
            return json.dumps({"success": False, "error": {
                "code": "scope_denied", "message": "Notebook is unavailable for this Main Conversation.",
                "next_action": "Continue with visible evidence and authorized conversation_history.",
            }})
        return json.dumps(show_notebook(db.notebook_current(conversation_ref), conversation_ref=conversation_ref,
                                       profile_home=Path(db.db_path).parent),
                          ensure_ascii=False)
    except (ValueError, TypeError) as exc:
        return json.dumps({"success": False, "error": {"code": "invalid_argument", "message": str(exc),
                           "next_action": "Call notebook_show with an empty object."}}, ensure_ascii=False)


registry.register(name="notebook_show", toolset="notebook", schema=NOTEBOOK_SHOW_SCHEMA,
                  handler=lambda args, **kw: notebook_show(args, db=kw.get("db"),
                      conversation_ref=kw.get("conversation_ref"), effective_enabled=kw.get("effective_enabled")),
                  emoji="📓")
