"""Detect when the gateway is running stale code after a hot ``git pull``.

The gateway's ``sys.modules`` is frozen at boot.  If the checkout is updated
underneath it, a first-time lazy import can resolve a freshly-pulled module
against a stale cached dependency -> ImportError.  We snapshot the revision at
startup so risky callers (e.g. ``/model`` switching) can refuse with a clear
"restart the gateway" message.  If the revision can't be read (non-git install,
IO error) the boot snapshot stays ``None`` and detection no-ops — never a false positive.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Mapping

logger = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_boot_fingerprint: str | None = None

# Process-wide policy for the MODEL-OPERATION guards only. ``None`` = startup has not
# resolved it; the native default is enabled, so embedded callers and tests that never
# reach a backend entry point keep today's protection. ``resolve_model_guard_policy``
# settles it once from the launch config; a later config edit or a request for another
# Profile must not change it mid-process.
_model_guard_enabled: bool | None = None
_MODEL_GUARD_CONFIG_KEY = ("gateway", "model_code_skew_guard")


def _fingerprint() -> str | None:
    """Current checkout fingerprint via the CLI's worktree-aware git-rev reader
    (``hermes_cli.main`` is always already imported in a gateway process)."""
    try:
        from hermes_cli.main import _read_git_revision_fingerprint

        return _read_git_revision_fingerprint(_PROJECT_ROOT)
    except Exception:
        return None


def record_boot_fingerprint() -> None:
    """Snapshot the checkout revision at gateway startup (idempotent)."""
    global _boot_fingerprint
    if _boot_fingerprint is None:
        _boot_fingerprint = _fingerprint()


def record_boot_state() -> None:
    """Backend-startup seam: snapshot the revision and settle the model-guard policy."""
    record_boot_fingerprint()
    resolve_model_guard_policy()


def _short(fingerprint: str) -> str:
    """Render a ``git:<ref>:<sha>`` fingerprint as a compact label."""
    sha = fingerprint.rsplit(":", 1)[-1]
    return sha[:10] if sha and sha != "unresolved" and len(sha) > 10 else (sha or fingerprint)


def current_code_sha() -> str | None:
    """Full SHA for the checkout currently on disk, or None when unresolved."""
    fingerprint = _fingerprint()
    if fingerprint is None:
        return None
    sha = fingerprint.rsplit(":", 1)[-1]
    return sha if sha and sha != "unresolved" else None


def detect_code_skew() -> tuple[str, str] | None:
    """``(boot_rev, disk_rev)`` short labels if the checkout drifted since boot, else ``None``."""
    current = _fingerprint() if _boot_fingerprint is not None else None
    if current is None or current == _boot_fingerprint:
        return None
    return _short(_boot_fingerprint), _short(current)


def _model_guard_config_value(config: Mapping[str, Any] | None) -> Any:
    node: Any = config
    for part in _MODEL_GUARD_CONFIG_KEY:
        if not isinstance(node, Mapping):
            return None
        node = node.get(part)
    return node


def _model_guard_enabled_from_config(config: Mapping[str, Any] | None) -> bool:
    """Only a recognized false value disables the guard; unset/malformed stays native-on."""
    value = _model_guard_config_value(config)
    if value is None:
        return True
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"0", "false", "no", "off"}:
            return False
        if text in {"1", "true", "yes", "on"}:
            return True
    logger.warning(
        "gateway.model_code_skew_guard has an unrecognized value %r; keeping the model "
        "code-skew guards enabled", value)
    return True


def resolve_model_guard_policy(config: Mapping[str, Any] | None = None) -> bool:
    """Resolve the model-operation skew policy ONCE for this backend process.

    Reads the launch profile's effective user config (no ``DEFAULT_CONFIG`` merge needed:
    an absent key means the native enabled default). Called from the gateway, dashboard
    and TUI process entry points before any request can be served. The first call wins:
    later config edits or another Profile's config do not change the process policy, so a
    change takes effect only after restarting the backend. Returns the settled boolean.
    """
    global _model_guard_enabled
    if _model_guard_enabled is not None:
        return _model_guard_enabled
    if config is None:
        try:
            from hermes_cli.config_effective import load_user_config_effective

            config = load_user_config_effective()
        except Exception:
            logger.debug("could not read the launch config for the model code-skew guard", exc_info=True)
            config = {}
    enabled = _model_guard_enabled_from_config(config)
    _model_guard_enabled = enabled
    if enabled:
        logger.debug("model code-skew guards enabled")
    else:
        logger.warning(
            "gateway.model_code_skew_guard=false: model-operation code-skew guards are "
            "disabled for this process. Raw skew detection, cron skew handling and backend "
            "retirement/watchdog remain active; restart the backend to re-enable the guards.")
    return enabled


def model_guard_skew() -> tuple[str, str] | None:
    """Skew for the MODEL-OPERATION guards, or ``None`` when this process opted out.

    The one policy seam shared by the TUI/Desktop model RPCs, the gateway ``/model``
    switch and the dashboard model routes. Raw detection is untouched: cron and the
    backend retirement watchdog call :func:`detect_code_skew` directly.
    """
    if _model_guard_enabled is False:
        return None
    return detect_code_skew()
