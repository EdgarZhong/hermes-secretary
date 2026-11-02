"""Opt-in configuration for the local adaptive maintenance seam."""
from __future__ import annotations

import json
import logging
import math
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


def _number(value, *, minimum=0):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= minimum)


def conversation_enabled(config, ref):
    noting = config.get("noting", {}) if isinstance(config, dict) else {}
    if not isinstance(noting, dict) or noting.get("enabled", True) is not True:
        return False
    block = noting.get("adaptive_idle_token_saving", {})
    if not isinstance(block, dict) or block.get("enabled") is not True:
        return False
    conversations = block.get("conversations", {})
    selected = conversations.get(ref) if isinstance(conversations, dict) else None
    return isinstance(selected, dict) and selected.get("enabled") is True


def enabled_for_db(db, ref):
    from hermes_cli.config import load_config_readonly
    from secretary.noting_scope import owning_db_scope
    try:
        with owning_db_scope(db):
            return conversation_enabled(load_config_readonly(), ref)
    except Exception:
        logger.debug("Adaptive Conversation switch unavailable", exc_info=True)
        return False


def from_config(config, ref=None, *, model_contract=None):
    """Require explicit Conversation opt-in and its exact native picker identity."""
    from secretary.adaptive_model_config import digest
    if not model_contract or not conversation_enabled(config, ref):
        return None
    block = config["noting"]["adaptive_idle_token_saving"]
    models = block.get("models", {})
    provider, model = model_contract.get("provider"), model_contract.get("model")
    items = models.get(provider, {}) if isinstance(models, dict) else {}
    item = items.get(model) if isinstance(items, dict) else None
    if not isinstance(item, dict):
        return None
    heartbeat, billing = item.get("heartbeat"), item.get("billing")
    if not isinstance(heartbeat, dict) or not isinstance(billing, dict):
        return None
    required = ((heartbeat.get("hot_seconds"), 60), (item.get("cache_ttl_seconds"), 1),
                (billing.get("cache_read"), 0), (billing.get("output"), 0))
    if any(not _number(value, minimum=minimum) for value, minimum in required):
        return None
    if billing.get("input") != 1 or isinstance(billing.get("input"), bool):
        return None
    if not isinstance(billing.get("source"), str) or not billing["source"].strip():
        return None
    if "business_seconds" not in heartbeat:
        return None
    business = heartbeat["business_seconds"]
    if business is not None and not _number(business, minimum=60):
        return None
    if not isinstance(block.get("shadow_only", False), bool):
        return None
    if not all(_number(model_contract.get(key), minimum=1) for key in ("context_length", "threshold_tokens")):
        return None
    result = {key: value for key, value in block.items() if key not in {"models", "conversations"}}
    result.update(hot_interval_seconds=heartbeat["hot_seconds"], business_interval_seconds=business,
                  cache_ratio=billing["cache_read"], output_ratio=billing["output"],
                  cache_ttl_seconds=item["cache_ttl_seconds"], billing=dict(billing),
                  model_identity={"provider": provider, "model": model}, model_contract=model_contract,
                  history_limit=2048)
    timezone = result.get("timezone")
    if timezone is not None:
        try:
            ZoneInfo(timezone)
        except (TypeError, ValueError, KeyError):
            return None
    result["config_version"] = digest(result)
    return result


def for_db(db, ref=None, *, parent=None, session_id=None, conn=None):
    from hermes_cli.config import get_config_path, load_config_readonly
    from secretary.noting_scope import owning_db_scope
    from secretary.adaptive_model_config import resolve_contract
    try:
        if ref is None and parent is not None:
            ref = getattr(parent, "_secretary_conversation_ref", None)
        if ref is None and session_id is not None:
            if conn is None:
                ref = db.resolve_conversation_ref(session_id)
            else:
                row = conn.execute("SELECT conversation_ref FROM secretary_session_bindings WHERE session_id=?",
                                   (session_id,)).fetchone()
                ref = row[0] if row else None
        if not ref:
            return None
        with owning_db_scope(db):
            raw = load_config_readonly()
            # No native capability construction for a disabled/unselected Conversation.
            if not conversation_enabled(raw, ref):
                return None
            contract = resolve_contract(db, ref, raw, parent=parent, session_id=session_id, conn=conn)
            config = from_config(raw, ref, model_contract=contract)
            if config is not None:
                config["_configured_at"] = get_config_path().stat().st_mtime
            return config
    except Exception:
        logger.debug("Adaptive configuration unavailable", exc_info=True)
        return None


def validate_decision(value):
    if not isinstance(value, dict) or value.get("mode") not in {"hot", "business"}:
        raise ValueError("invalid adaptive mode")
    threshold, delay = value.get("threshold_tokens"), value.get("delay_seconds")
    if threshold is not None and (type(threshold) is not int or threshold <= 0):
        raise ValueError("invalid adaptive threshold")
    if delay is not None and not _number(delay):
        raise ValueError("invalid adaptive delay")
    # A disabled early-maintenance choice has no independently armed timer.
    if threshold is None or delay is None:
        threshold = delay = None
    result = {**value, "threshold_tokens": threshold, "delay_seconds": delay}
    json.dumps(result, allow_nan=False)
    return result
