"""The real Main Turn end is the only Force trigger."""

import logging

logger = logging.getLogger(__name__)


def check_force_at_turn_end(parent):
    from secretary import noting_runtime as rt
    if not rt.is_main_conversation_agent(parent):
        return
    try:
        from agent.context_compaction_request import _lock
        from secretary.framework_messages import _lock as framework_lock
        from agent.usage_anchor import anchored_context_tokens
        from secretary.noting_policy import measurement_from_agent
        from agent.model_metadata import estimate_request_tokens_rough
        from agent.conversation_loop import _midturn_request_pressure_tokens
        with framework_lock(parent), _lock(parent):
            if getattr(parent, "_secretary_main_turn_running", False):
                return
            messages = getattr(parent, "_session_messages", None) or []
            compressor = getattr(parent, "context_compressor", None)
            if compressor is None or not messages:
                return
            usage = anchored_context_tokens(messages, getattr(parent, "_usage_anchor", None))
            if usage is None:
                # The native request-pressure fallback prices the complete Turn
                # tail when the provider supplied no usable anchor.
                usage = _midturn_request_pressure_tokens(
                    parent, messages, getattr(parent, "_cached_system_prompt", None) or "",
                    estimate_request_tokens_rough(messages, tools=getattr(parent, "tools", None)))
            measurement = measurement_from_agent(parent, usage)
            rt.prepare_joint_noting(parent, trigger="force", measurement=measurement, messages=messages)
    except Exception:
        logger.warning("Main Turn-end Force check failed", exc_info=True)
