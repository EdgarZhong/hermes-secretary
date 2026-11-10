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
    if "cache_write" in billing and not _number(billing["cache_write"]):
        return None
    if billing.get("input") != 1 or isinstance(billing.get("input"), bool):
        return None
    if not isinstance(billing.get("source"), str) or not billing["source"].strip():
        return None
    business = heartbeat.get("business_seconds")  # Legacy read compatibility; V4 only requires hot.
    if business is not None and not _number(business, minimum=60):
        return None
    if not isinstance(block.get("shadow_only", False), bool):
        return None
    if not all(_number(model_contract.get(key), minimum=1) for key in ("context_length", "threshold_tokens")):
        return None
    result = {key: value for key, value in block.items() if key not in {"models", "conversations"}}
    result.update(hot_interval_seconds=heartbeat["hot_seconds"], business_interval_seconds=business,
                  cache_ratio=billing["cache_read"], output_ratio=billing["output"],
                  cache_write_ratio=billing.get("cache_write"),
                  cache_ttl_seconds=item["cache_ttl_seconds"], billing=dict(billing),
                  model_identity={"provider": provider, "model": model}, model_contract=model_contract,
                  history_limit=65536)
    result.setdefault("horizon_seconds", 86400)
    result.setdefault("recency_timescale_days", 7)
    if not all(_number(result[key], minimum=1) for key in ("horizon_seconds", "recency_timescale_days")):
        return None
    timezone = result.get("timezone")
    if timezone is not None:
        try:
            ZoneInfo(timezone)
        except (TypeError, ValueError, KeyError):
            return None
    from secretary.adaptive_model_config import cache_contract
    result["cache_contract"] = cache_contract(model_contract)
    result["_hot_interval_source"] = "registered_model"
    if isinstance(item.get("cache_compatibility"), dict):
        result["cache_compatibility"] = dict(item["cache_compatibility"])
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
                from secretary.adaptive_model_config import digest, resolve_cache_contract
                if conn is not None:
                    cache = resolve_cache_contract(db, ref, parent=parent, session_id=session_id, conn=conn)
                else:
                    with db._read_ctx() as connection:
                        cache = resolve_cache_contract(db, ref, parent=parent, session_id=session_id, conn=connection)
                if cache:
                    config["cache_contract"] = cache
                    config["config_version"] = digest({key: value for key, value in config.items() if key != "config_version"})
                config["_configured_at"] = get_config_path().stat().st_mtime
            return config
    except Exception:
        logger.debug("Adaptive configuration unavailable", exc_info=True)
        return None


def plan_for_db(db, ref, *, parent=None, conn):
    """A live runtime may propose maintenance only for the persisted selection."""
    from secretary.adaptive_model_config import selection_is_current
    config = for_db(db, ref, parent=parent, conn=conn)
    try:
        return config if config and selection_is_current(db, ref, parent, conn=conn) else None
    except Exception:
        logger.debug('Adaptive maintenance selection unavailable', exc_info=True)
        return None


def validate_decision(value):
    if not isinstance(value, dict) or value.get("mode") not in {"hot", "standby", "business"}:
        raise ValueError("invalid adaptive mode")
    threshold, delay = value.get("threshold_tokens"), value.get("delay_seconds")
    if threshold is not None and (type(threshold) is not int or threshold <= 0):
        raise ValueError("invalid adaptive threshold")
    if delay is not None and not _number(delay):
        raise ValueError("invalid adaptive delay")
    # A disabled early-maintenance choice has no independently armed timer.
    if value["mode"] == "standby" or threshold is None or delay is None:
        threshold = delay = None
    result = {**value, "threshold_tokens": threshold, "delay_seconds": delay}
    json.dumps(result, allow_nan=False)
    return result


def _target_hot_interval(conn, ref, block, item):
    """Only this model or this target's explicit/prior configured hot period."""
    model_hb = item.get('heartbeat', {}) if isinstance(item, dict) else {}
    value = model_hb.get('hot_seconds') if isinstance(model_hb, dict) else None
    if _number(value, minimum=60):
        return value, 'registered_model'
    selected = block['conversations'][ref]
    common = selected.get('heartbeat', {})
    value = common.get('hot_seconds') if isinstance(common, dict) else None
    if _number(value, minimum=60):
        return value, 'explicit_target'
    import json
    rows = conn.execute("SELECT payload FROM secretary_adaptive_events WHERE conversation_ref=? "
                        "AND kind='heartbeat_config' ORDER BY at DESC,id DESC LIMIT 32", (ref,))
    for row in rows:
        value = json.loads(row[0])
        if value.get('verified') is True and _number(value.get('hot_interval_seconds'), minimum=60):
            return value['hot_interval_seconds'], 'prior_target_configured_hot'
    # Upgrade existing V3 target state only when it is itself an explicitly
    # configured hot interval. A legacy business/native interval is never used.
    row = conn.execute('SELECT mode,interval_seconds,config_version FROM secretary_adaptive_heartbeats '
                        'WHERE conversation_ref=?', (ref,)).fetchone()
    if row and row['mode'] == 'hot' and row['config_version'] != 'native' and _number(row['interval_seconds'], minimum=60):
        return row['interval_seconds'], 'prior_target_configured_hot'
    return None, 'missing_target_hot_interval'


def _priced_matches_cache(priced, cache):
    identity, contract = priced.get('model_identity', {}), priced.get('model_contract', {})
    return bool(priced.get('cache_contract') == cache
                and all(identity.get(key) == cache.get(key) for key in ('provider', 'model'))
                and all(contract.get(key) == cache.get(key) for key in
                        ('provider', 'model', 'api_mode', 'reasoning_config', 'reasoning_effort')))


def heartbeat_for_db(db, ref=None, *, parent=None, session_id=None, conn=None):
    """Eligible target/cache settings without requiring a priced maintenance model."""
    from hermes_cli.config import load_config_readonly, get_config_path
    from secretary.noting_scope import owning_db_scope
    from secretary.adaptive_model_config import resolve_cache_contract, digest
    try:
        if conn is None:
            with db._read_ctx() as connection:
                return heartbeat_for_db(db, ref, parent=parent, session_id=session_id, conn=connection)
        if ref is None and parent is not None:
            ref = getattr(parent, '_secretary_conversation_ref', None)
        if ref is None and session_id is not None:
            row = conn.execute('SELECT conversation_ref FROM secretary_session_bindings WHERE session_id=?',
                               (session_id,)).fetchone()
            ref = row[0] if row else None
        with owning_db_scope(db):
            raw = load_config_readonly()
            if not ref or not conversation_enabled(raw, ref):
                return None
            cache = resolve_cache_contract(db, ref, parent=parent, session_id=session_id, conn=conn)
            cache = cache or dict(provider=None, model=None, api_mode=None, reasoning_config=None, reasoning_effort=None)
            priced = for_db(db, ref, parent=parent, session_id=session_id, conn=conn)
            if priced and _priced_matches_cache(priced, cache):
                return priced
            block = raw['noting']['adaptive_idle_token_saving']
            models = block.get('models', {})
            items = models.get(cache['provider'], {}) if isinstance(models, dict) else {}
            item = items.get(cache['model'], {}) if isinstance(items, dict) else {}
            hot, source = _target_hot_interval(conn, ref, block, item)
            ttl = item.get('cache_ttl_seconds') if isinstance(item, dict) else None
            value = dict(model_identity={key: cache[key] for key in ('provider', 'model')}, model_contract=cache,
                         cache_contract=cache, hot_interval_seconds=hot,
                         cache_ttl_seconds=ttl if _number(ttl, minimum=1) else None,
                         shadow_only=block.get('shadow_only') is True, _heartbeat_only=True,
                         _hot_interval_source=source, history_limit=65536,
                         cache_compatibility=(item.get('cache_compatibility', block.get('cache_compatibility', {}))
                                              if isinstance(item, dict) else block.get('cache_compatibility', {})))
            value['config_version'] = digest(value)
            value['_configured_at'] = get_config_path().stat().st_mtime
            return value
    except Exception:
        logger.debug('Adaptive Heartbeat configuration unavailable', exc_info=True)
        return None
