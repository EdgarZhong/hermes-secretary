"""Native iteration-summary message assembly, shared by all provider modes.

The public helper remains in chat_completion_helpers; its established sanitizer
patch points are resolved there lazily to preserve compatibility.
"""

from __future__ import annotations


def build_iteration_summary_messages(agent, messages: list) -> list:
    """Wire-ready messages for the summary call, mirroring the main loop's api_messages build
    (sidecar substitution, tool-call repair, thinking-only drop, underscore-key sweep).

    ``reasoning_details`` is kept: the anthropic_messages converter rebuilds signed thinking
    blocks from it, and the chat-completions transport already drops it on the wire for routes
    that do not replay it (``_chat_summary_attempt`` -> ``_build_api_kwargs``)."""
    from agent import chat_completion_helpers as helpers

    needs_sanitize = agent._should_sanitize_tool_calls()
    sanitize_model = agent.model
    if needs_sanitize and agent.provider == "moa":
        # MoA: agent.model is the virtual preset; use the real aggregator so Gemini keeps thought_signature.
        agg_slot = getattr(getattr(agent, "client", None), "last_aggregator_slot", None)
        sanitize_model = (agg_slot or {}).get("model") or sanitize_model
    api_messages = []
    for msg in messages:
        api_msg = msg.copy()
        agent._copy_reasoning_content_for_api(msg, api_msg)
        for key in helpers._SUMMARY_FOREIGN_MESSAGE_KEYS:
            api_msg.pop(key, None)
        # Mirror of the transport's role-qualified strip: ``name`` is
        # schema-foreign on tool results only (strict providers reject with
        # "contains item with unknown key name"); it stays on user/assistant.
        if api_msg.get("role") == "tool":
            api_msg.pop("name", None)
        # api_content holds the exact bytes the main loop sent; substituting (not popping)
        # keeps the summary's prefix identical instead of re-prefilling the largest context.
        # Strict OpenAI-compatible gateways (Fireworks-backed OpenCode Go, Mistral, Moonshot/Kimi) reject
        # any message key outside the Chat Completions schema. The main loop drops these via
        # ChatCompletionsTransport.convert_messages(), but the summary path hand-builds messages and calls
        # chat.completions.create() directly, bypassing the transport — so mirror that sanitization here:
        # tool_name (SQLite FTS bookkeeping), the codex_* reasoning carriers, timestamp (preserved on
        # gateway user replay entries for the stale-confirmation expiry check — #47868 rejection class), and
        # every Hermes-internal underscore-prefixed scaffolding key.
        helpers.substitute_api_content(api_msg)
        if needs_sanitize:
            agent._sanitize_tool_calls_for_strict_api(api_msg, model=sanitize_model)
        api_messages.append(api_msg)

    effective_system = agent._cached_system_prompt or ""
    if agent.ephemeral_system_prompt:
        effective_system = (effective_system + "\n\n" + agent.ephemeral_system_prompt).strip()
    if effective_system:
        api_messages = [{"role": "system", "content": effective_system}] + api_messages
    for idx, pfm in enumerate(agent.prefill_messages or ()):
        api_messages.insert((1 if effective_system else 0) + idx, pfm.copy())

    from secretary.noting_request import prepare_noting_request, normalize_noting_request, uses_dynamic_noting_tools
    _noting_declaration = prepare_noting_request(agent, api_messages)

    # Compression/resume can orphan a tool result whose parent tool_call was summarized away.
    api_messages = agent._sanitize_api_messages(api_messages)
    # Same send-path vision eviction as the main loop (#89296).
    from agent.context_compressor import evict_stale_outbound_tool_images
    evict_stale_outbound_tool_images(api_messages)
    # Same per-model image strip as turn_api_request.build_api_request: this path builds
    # api_messages by hand and calls _build_api_kwargs directly, so a model recorded in
    # agent._image_rejecting_models would otherwise get images here → 4xx → no summary.
    # Safe on the shallow row copies: the strip rebinds the row's ``content``, never the
    # nested list shared with history.
    helpers.strip_images_for_rejecting_model(agent, api_messages)
    # Thinking-only assistant turns 400 on Anthropic-family providers; _thinking_prefill must
    # survive until here so the drop pass recognizes stubs after reasoning is stripped.
    if _noting_declaration is not None or uses_dynamic_noting_tools(agent):
        from agent.conversation_loop import _CODEX_INCOMPLETE_NUDGE
        api_messages = normalize_noting_request(
            agent, api_messages, _noting_declaration, drop_nudge_marker=_CODEX_INCOMPLETE_NUDGE)
    else:
        api_messages = agent._drop_thinking_only_and_merge_users(api_messages)
    for api_msg in api_messages:  # underscore scaffolding: the transport's sweeper is bypassed here
        if isinstance(api_msg, dict):
            for internal_key in [k for k in api_msg if isinstance(k, str) and k.startswith("_")]:
                del api_msg[internal_key]
    # Same closing normalization as assemble_api_request so the summary's prefix stays
    # bit-identical to the main loop's (a diverging early row defeats prefix caching).
    for api_msg in api_messages:
        if isinstance(api_msg.get("content"), str):
            api_msg["content"] = api_msg["content"].strip()
    from agent.conversation_loop import _canonicalize_api_tool_calls, _clone_message_for_send
    _canonicalize_api_tool_calls(api_messages)
    # Third closing pass of the main path: lone surrogates -> U+FFFD (else the SDK's utf-8
    # wire encode raises and burns the summary retries). The sanitizer is in-place and these
    # rows still share nested dicts with history, so clone first like the main path does.
    api_messages = [_clone_message_for_send(m) for m in api_messages]
    helpers._sanitize_messages_surrogates(api_messages)
    return api_messages
