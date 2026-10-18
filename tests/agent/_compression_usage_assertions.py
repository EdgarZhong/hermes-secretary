"""Shared cold-display usage assertions for native compression boundaries."""

import json

from agent.usage_anchor import persisted_context_estimate


def assert_cold_usage_context(db, agent, session_id, base_model_config):
    """Keep exact persisted configuration and cold-read contracts together."""
    rough_tokens = agent.context_compressor.last_compression_rough_tokens
    assert type(rough_tokens) is int and rough_tokens > 0
    assert agent._usage_anchor is None and agent._turn_base_usage_anchor is None
    assert json.loads(db.get_session(session_id)["model_config"]) == {
        **base_model_config,
        "_usage_context": {
            "session_id": session_id, "tokens": rough_tokens, "rewind_count": 0,
            "model": agent.model, "source": "local_estimate",
        },
    }
    assert persisted_context_estimate(db, session_id, model=agent.model) == {
        "tokens": rough_tokens, "source": "local_estimate",
    }
