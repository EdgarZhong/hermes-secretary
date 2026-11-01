"""Optional session response projection; native runtime and recovery facts stay untouched."""


def project_session_info(payload, params):
    """Only an explicit opt-out removes the unused prompt from this response copy."""
    if params.get("include_system_prompt", True) is not False or "system_prompt" not in payload.get("info", {}):
        return payload
    return {**payload, "info": {key: value for key, value in payload["info"].items() if key != "system_prompt"}}


def resume_response(
    namespace, ctx, sid: str, record: dict, *, info: dict, display: list = (), count_source: list | None = None,
    messages: list | None = None, message_count: int | None = None, running: bool = False,
    status: str = "idle", hydrating: bool | None = None, started_at=None, auto_continue=None,
) -> dict:
    """Common resume payload; omit_messages counts ``count_source`` (client still learns the stored size)."""
    if messages is None:
        messages = ctx.messages(display)
    if message_count is None:
        message_count = len(count_source) if ctx.omit_messages else len(messages)
    if not info.get("usage") and (usage := namespace["_session_usage_snapshot"](record)):
        info = {**info, "usage": usage}
    payload = {"recovery_view_version": 1, "session_id": sid, "resumed": ctx.target, "message_count": message_count, "messages": messages,
               **({"messages_omitted": ctx.omit_messages} if hydrating is None else {"hydrating": hydrating}),
               "info": info, "inflight": None, "running": running, "session_key": ctx.target,
               "started_at": record["created_at"] if started_at is None else started_at, "status": status}
    if auto_continue is not None:
        payload["auto_continue"] = auto_continue
    return namespace["_ok"](ctx.rid, project_session_info(namespace["_attach_todo_state"](payload, record), getattr(ctx, "params", {})))
