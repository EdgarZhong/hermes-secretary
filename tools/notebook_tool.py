"""Read-only AI-facing Notebook show for the main Assistant's current Conversation.

The runtime supplies a proven Main + global read gate, independently of local background
participation. The handler fails closed without it and returns complete structured Snapshot JSON.
"""

import json

from secretary.notebook_render import show_notebook
from tools.registry import registry


NOTEBOOK_SHOW_SCHEMA = {
    "name": "notebook_show",
    "description": "Read the current Conversation's committed Notebook Snapshot as complete structured JSON. Read-only.",
    "parameters": {"type": "object", "properties": {}, "additionalProperties": False},
}


def notebook_show(args=None, *, db=None, conversation_ref=None, effective_enabled=None, **kwargs):
    """``effective_enabled`` is the explicit Main + global read gate; missing proof fails closed."""
    args = dict(args or {})
    args.update(kwargs)
    try:
        if args:
            raise ValueError("Unsupported Notebook arguments: " + ", ".join(sorted(args)))
        if db is None or not conversation_ref:
            raise ValueError("Current Conversation state is unavailable")
        enabled = effective_enabled is True
        if not enabled:
            raise ValueError("Notebook is not enabled for this Conversation")
        return json.dumps({"success": True, "snapshot": show_notebook(db.notebook_current(conversation_ref))},
                          ensure_ascii=False)
    except (ValueError, TypeError) as exc:
        return json.dumps({"success": False, "error": str(exc)}, ensure_ascii=False)


registry.register(
    name="notebook_show", toolset="notebook", schema=NOTEBOOK_SHOW_SCHEMA,
    handler=lambda args, **kw: notebook_show(args, db=kw.get("db"), conversation_ref=kw.get("conversation_ref"),
                                             effective_enabled=kw.get("effective_enabled")),
    emoji="📓",
)
