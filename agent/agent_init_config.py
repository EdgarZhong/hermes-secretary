"""Standalone config-coercion helpers lifted out of the agent_init facade.

Moved verbatim (over-target facades may only go down); the facade re-imports the names so
``agent.agent_init.<name>`` stays a working import/patch seam.
"""

from typing import Any, Dict, Optional


def _normalize_run_budget_seconds(value) -> Optional[float]:
    """Positive float or None (feature off). ``bool`` rejected: YAML ``true`` → 1s budget."""
    if value is None or isinstance(value, bool):
        return None
    try:
        seconds = float(value)
    except (TypeError, ValueError):
        return None
    return seconds if seconds > 0 else None  # NaN compares False → None


def _refuse_checkpoint_required_on_codex_app_server(
    checkpoint_required: bool, api_mode: Optional[str]
) -> None:
    """Fail closed at init: the codex app-server compacts its own thread without a truthful
    pre-compaction boundary (default "native" mode), so a required checkpoint can't be
    guaranteed — the compress_context() guard alone cannot cover native turns."""
    if checkpoint_required and api_mode == "codex_app_server":
        raise RuntimeError(
            "BLOCKED_MISSING_PREREQUISITE: compression.checkpoint_required "
            "is incompatible with the codex_app_server API mode: the codex "
            "agent compacts its own thread without a truthful pre-compaction "
            "transcript boundary, so a required pre-compress checkpoint "
            "cannot be guaranteed. Disable compression.checkpoint_required "
            "or use a non-app-server API mode."
        )


def _parse_config_int(raw: Any, default: int) -> int:
    """Strict int coercion: rejects bool (YAML ``true`` → 1) and fractional floats."""
    if isinstance(raw, bool):
        return default
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float):
        return int(raw) if raw.is_integer() else default
    try:
        return int(str(raw).strip())
    except (TypeError, ValueError):
        return default


def _cfg_flag(cfg: Dict[str, Any], key: str, default: bool) -> bool:
    """Legacy string-set truthiness used by the ``compression`` section."""
    return str(cfg.get(key, default)).lower() in {"true", "1", "yes"}


def _cfg_dict(cfg: Dict[str, Any], key: str) -> Dict[str, Any]:
    """``cfg[key]`` if it is a mapping, else ``{}`` (malformed sections are ignored)."""
    section = cfg.get(key, {})
    return section if isinstance(section, dict) else {}
