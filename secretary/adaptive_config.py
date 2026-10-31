"""Opt-in configuration for the local adaptive maintenance seam."""
from __future__ import annotations

import hashlib
import json
import logging
import math
from zoneinfo import ZoneInfo

logger = logging.getLogger(__name__)


def _number(value, *, minimum=0):
    return (isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value) and value >= minimum)


def from_config(config):
    """Invalid or incomplete settings retain native behavior; no provider assumptions."""
    noting = config.get("noting", {}) if isinstance(config, dict) else {}
    if not isinstance(noting, dict) or noting.get("enabled", True) is not True:
        return None
    block = noting.get("adaptive", {})
    if not isinstance(block, dict) or block.get("enabled") is not True:
        return None
    required = {"hot_interval_seconds": 60, "cache_ratio": 0, "output_ratio": 0,
                "cache_ttl_seconds": 1}
    if any(not _number(block.get(key), minimum=minimum) for key, minimum in required.items()):
        return None
    if "business_interval_seconds" not in block:
        return None
    business = block.get("business_interval_seconds")
    if business is not None and not _number(business, minimum=60):
        return None
    result = dict(block)
    result["history_limit"] = 2048
    timezone = result.get("timezone")
    if timezone is not None:
        try:
            ZoneInfo(timezone)
        except (TypeError, ValueError, KeyError):
            return None
    result["config_version"] = hashlib.sha256(json.dumps(result, sort_keys=True, allow_nan=False).encode()).hexdigest()
    return result


def for_db(db):
    from hermes_cli.config import get_config_path, load_config_readonly
    from secretary.noting_scope import owning_db_scope
    try:
        with owning_db_scope(db):
            config = from_config(load_config_readonly())
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
