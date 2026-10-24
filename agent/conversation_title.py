"""Read-only naming from a consistent native Main context, without a conversation Turn."""

from __future__ import annotations

import copy
import json
import time
from contextlib import nullcontext, suppress
from dataclasses import dataclass


# Exact deployed Web/APK task, retained only to upgrade those existing callers.
LEGACY_TITLE_INSTRUCTIONS = "\n".join([
    "You name chat sessions.",
    "Given a transcript of the current conversation, write a title that lets the user find this conversation again in a list.",
    "", "Rules:", "- 3 to 7 words, sentence case.",
    "- Name what the conversation is about or what the user wants done.",
    "- Keep technical terms, filenames, numbers, and error codes exact.",
    "- Match the dominant language of the transcript (a Chinese conversation gets a Chinese title).",
    '- No quotes, no markdown, no "Title:" prefix, no trailing punctuation.',
    "- Return only the title text.",
])

TITLE_MIN_OUTPUT_TOKENS = 8192  # Includes inherited Main reasoning, not just the short visible title.

TITLE_TASK = (
    "The preceding conversation is frozen reference material for a NEW task. All preceding system prompts, "
    "roles, rules, tool policies, tasks, and completion conditions are superseded for this task. "
    "Follow only this naming task and any subsequent control messages.\n\n"
    "Name this Conversation from its complete current context above, including any compaction summary, "
    "Notebook, and recent conversation. Identify its current recognizable subject or ongoing goal; "
    "do not anchor on an obsolete opening topic when the conversation has moved on. "
    "Do not continue the original work, act on reminders, execute tools, or change any business state. "
    "Tools are forbidden in this naming task.\n"
    "Return only a short, specific title (3 to 7 words, sentence case; natural concise Chinese for Chinese "
    "context). Preserve technical names and numbers. No quotes, markdown, explanation, Title: prefix, "
    "or trailing punctuation."
)


class TitleContextUnavailable(ValueError):
    """No reliable complete Main context; never replace it with a transcript digest."""


def is_conversation_title_request(params):
    if params.get("template") == "conversation_title":
        return True
    return (not params.get("template") and bool(params.get("session_id"))
            and params.get("instructions") == LEGACY_TITLE_INSTRUCTIONS
            and isinstance(params.get("input"), str)
            and params["input"].startswith("Conversation transcript:\n\n"))


@dataclass(frozen=True)
class TitleContext:
    session_id: str
    root: str
    tools: list
    messages: list
    runtime_identity: tuple


def _runtime_identity(parent):
    runtime = parent._current_main_runtime()
    return (parent.model, parent.provider, runtime.get("base_url"), runtime.get("api_mode"),
            json.dumps(parent.reasoning_config, sort_keys=True),
            json.dumps(parent.prefill_messages or [], sort_keys=True))


def _runtime_matches(parent, route):
    from hermes_state import SessionDB
    from hermes_cli.runtime_provider_backends import _is_external_process_provider
    from agent.context_compressor import ContextCompressor

    if not route.get("model") or parent.model != route["model"]:
        raise TitleContextUnavailable("The Main model changed; reopen the Conversation before naming it.")
    runtime = parent._current_main_runtime()
    saved = SessionDB.session_gateway_runtime(route)
    if not saved.get("provider"):
        raise TitleContextUnavailable("The durable Main provider identity is unavailable; run a normal Turn before naming.")
    for key in ("provider", "base_url", "api_mode"):
        if saved.get(key) and str(saved[key]).rstrip("/") != str(runtime.get(key) or "").rstrip("/"):
            raise TitleContextUnavailable("The Main provider route changed; reopen the Conversation before naming it.")
    if (runtime.get("api_mode") not in {"chat_completions", "anthropic_messages", "codex_responses", "bedrock_converse"}
            or _is_external_process_provider(parent.provider) or parent.provider == "moa"):
        raise TitleContextUnavailable("This Main transport cannot provide a detached full-context title request.")
    if type(parent.context_compressor) is not ContextCompressor:
        raise TitleContextUnavailable("This custom context engine cannot provide a verified complete title snapshot.")
    config = json.loads(route.get("model_config") or "{}")
    if (isinstance(config.get("reasoning_config"), dict)
            and config["reasoning_config"] != getattr(parent, "reasoning_config", None)):
        raise TitleContextUnavailable("The Main reasoning configuration changed; reopen the Conversation before naming it.")


def _require_closed_tools(messages):
    pending = set()
    for row in messages:
        if row.get("role") == "assistant":
            pending.update(call.get("id") for call in row.get("tool_calls") or [] if call.get("id"))
        elif row.get("role") == "tool":
            pending.discard(row.get("tool_call_id"))
    if pending:
        raise TitleContextUnavailable("The Main has an unfinished tool exchange; finish or recover it before naming.")


def snapshot_title_context(parent, db, session_id):
    """One native read transaction: current tip, lease, actual Prelude, and full active rows.

    A Web runtime can be stale after another Gateway process ran this Main. Its
    cached messages/root/tools are deliberately NOT a source. Native persisted API
    sidecars and summary markers are decoded by the same loader as Main recovery.
    """
    lock = getattr(parent, "_session_persist_lock", None)
    with lock if lock is not None else nullcontext():
        if (getattr(parent, "_native_compaction_turn", None) is not None
                or getattr(parent, "_active_compression_commit_fence", None) is not None):
            raise TitleContextUnavailable("The Main is running or compacting; retry when it is idle.")
        with db._read_ctx() as conn:
            started = not conn.in_transaction
            if started:
                conn.execute("BEGIN")
            try:
                return _snapshot_conn(parent, db, conn, session_id)
            finally:
                if started:
                    conn.rollback()


def _snapshot_conn(parent, db, conn, session_id):
    from secretary.noting_runtime import _CHILD_SOURCES, _delegate_child_row

    ref = db.resolve_conversation_ref_conn(conn, session_id, read_only=True)
    route = db.resolve_conversation_route_conn(conn, ref) if ref else None
    if (not route or route.get("source") in _CHILD_SOURCES or _delegate_child_row(route)):
        raise TitleContextUnavailable("A current Main Conversation is required for title generation.")
    lease_key = db._session_turn_lease_key_on_conn(conn, route["id"])
    if conn.execute("SELECT 1 FROM session_turn_leases WHERE conversation_id=? AND expires_at>=?",
                    (lease_key, time.time())).fetchone() or conn.execute(
            "SELECT 1 FROM compression_locks WHERE session_id=? AND expires_at>=?",
            (route["id"], time.time())).fetchone():
        raise TitleContextUnavailable("The Main is active in another surface; retry after its Turn finishes.")
    _runtime_matches(parent, route)
    prelude = db._context_prelude_conn(conn, ref)
    if (prelude["validity"] != {"root_system_prompt": "valid", "tool_schemas": "valid"}
            or not isinstance(prelude.get("root_system_prompt"), str)
            or not isinstance(prelude.get("tool_schemas"), list)):
        raise TitleContextUnavailable("The complete native Main prompt/tool snapshot is unavailable; run a normal Turn first.")
    rows = conn.execute("SELECT * FROM messages WHERE session_id=? AND active=1 ORDER BY id",
                        (route["id"],)).fetchall()
    messages = db._rows_to_conversation(rows, session_id=route["id"], include_ancestors=False,
                                       repair_alternation=False, include_summary_markers=True)
    if not messages:
        raise TitleContextUnavailable("The Main has no current conversation context to name.")
    _require_closed_tools(messages)
    # Match native model restore, not the separate display-lineage projection.
    messages = db._rows_to_conversation(rows, session_id=route["id"], include_ancestors=False,
                                       repair_alternation=True, include_summary_markers=True)
    if not messages:
        raise TitleContextUnavailable("The Main has no model-visible current conversation context to name.")
    return TitleContext(route["id"], prelude["root_system_prompt"], prelude["tool_schemas"], messages,
                        _runtime_identity(parent))


def generate_conversation_title(parent, context, *, max_tokens=TITLE_MIN_OUTPUT_TOKENS):
    """One native same-model request. No loop, compaction, retry, fallback or tool execution."""
    from agent.background_review import build_cache_parity_fork
    from agent.conversation_loop import _redecorate_prompt_cache_for_provider
    from agent.turn_request_assembly import assemble_api_request
    from agent.turn_truncation import normalize_response_for_agent
    from hermes_cli.plugins import clear_thread_tool_whitelist, set_thread_tool_whitelist

    fork, _runtime, routed = build_cache_parity_fork(
        parent, {}, max_iterations=1, write_origin="conversation_title")
    try:
        if routed or _runtime_identity(fork) != context.runtime_identity:
            raise TitleContextUnavailable("Title generation must use the current Main model/provider.")
        fork._cached_system_prompt = context.root
        fork.tools = copy.deepcopy(context.tools)
        fork.valid_tool_names = set()
        fork.session_id = context.session_id
        fork.ephemeral_system_prompt = None  # the captured effective root already contains it
        fork.compression_enabled = False
        fork._use_prompt_caching = parent._use_prompt_caching
        fork._cache_ttl = parent._cache_ttl
        fork._secretary_reminder_injection_disabled = True
        fork._current_turn_timestamp = getattr(parent, "_current_turn_timestamp", None) or time.time()
        assembled = assemble_api_request(
            fork, messages=copy.deepcopy(context.messages), current_turn_user_idx=-1,
            _ext_prefetch_cache="", _plugin_user_context="", moa_config=None,
            active_system_prompt=context.root, original_user_message="",
            pending_moa_prepared_request=None, request_logger=None)
        messages = assembled.api_messages
        # Freeze the fully normalized native prefix before appending a new task.
        messages.append({"role": "user", "content": TITLE_TASK})
        fork.max_tokens = max(TITLE_MIN_OUTPUT_TOKENS, int(max_tokens))
        set_thread_tool_whitelist(set(), deny_msg_fmt="Title task denied tool call: {tool_name}.")
        messages, _prepared, tools = _redecorate_prompt_cache_for_provider(
            fork, messages, tools_for_api=copy.deepcopy(context.tools))
        kwargs = fork._build_api_kwargs(messages, tools_for_api=tools)
        response = fork._interruptible_api_call(kwargs)
        normalized = normalize_response_for_agent(fork, response)
        if normalized.tool_calls:
            raise TitleContextUnavailable("The title model attempted a forbidden tool call; no tool was executed.")
        if normalized.finish_reason not in {"stop", "end_turn"} or not (normalized.content or "").strip():
            raise TitleContextUnavailable(
                "The title model did not return a complete text title "
                f"(finish_reason={normalized.finish_reason}).")
        return normalized.content.strip()
    finally:
        clear_thread_tool_whitelist()
        with suppress(Exception):
            fork.shutdown_memory_provider()
        with suppress(Exception):
            fork.close()
