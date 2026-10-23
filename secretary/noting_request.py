"""Request-only audit for the bound Noting child's fixed tool surface."""

from __future__ import annotations

import hashlib
import json


def audit_noting_request(agent, kwargs):
    """Record hashes and pressure from the transport-built request, never schemas in messages."""
    if not getattr(agent, "_secretary_noting_child", False):
        return
    from agent.model_metadata import estimate_request_tokens_rough
    from agent.message_content import flatten_message_text

    messages = kwargs.get("messages") or kwargs.get("input") or []
    system = kwargs.get("system") or kwargs.get("instructions") or ""

    def digest(value):
        encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(encoded.encode()).hexdigest()

    audit = {
        "top_level_tools_sha256": digest(kwargs.get("tools") or []),
        "request_sha256": digest({"messages": messages, "system": system, "tools": kwargs.get("tools") or []}),
        "estimated_request_tokens": estimate_request_tokens_rough(
            messages, system_prompt=flatten_message_text(system), tools=kwargs.get("tools")),
    }
    history = getattr(agent, "_secretary_noting_request_history", None)
    if not isinstance(history, list):
        history = agent._secretary_noting_request_history = []
    history.append(audit)
