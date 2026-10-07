"""Shape validators for config.yaml, split out of the (over-cap) ``hermes_cli.config`` facade.

These are small pure functions over the loaded config mapping. ``ConfigIssue`` and the shared
``_issue`` recorder live in ``hermes_cli.config`` and are imported lazily inside :func:`_issue`
so this module can be imported from there without a cycle; the facade re-exports the validators
so existing callers keep importing them from ``hermes_cli.config``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:  # pragma: no cover - typing only
    from hermes_cli.config import ConfigIssue


def _issue(issues: List["ConfigIssue"], severity: str, message: str, hint: str) -> None:
    from hermes_cli.config import ConfigIssue

    issues.append(ConfigIssue(severity, message, hint))


def _validate_voice(config: Dict[str, Any], issues: List["ConfigIssue"]) -> None:
    voice_cfg = config.get("voice")
    if not (isinstance(voice_cfg, dict) and "submit_mode" in voice_cfg):
        return
    submit_mode = voice_cfg.get("submit_mode")
    normalized = submit_mode.strip().lower() if isinstance(submit_mode, str) else None
    if normalized not in {"direct", "draft"}:
        _issue(issues, "error", f"voice.submit_mode must be 'direct' or 'draft', got {submit_mode!r}",
               "Set voice.submit_mode to direct (submit immediately) or draft (edit before sending)")


def _validate_timezone(config: Dict[str, Any], issues: List["ConfigIssue"]) -> None:
    """``timezone`` must be an IANA name the runtime can load.

    ``hermes_time._get_zoneinfo()`` swallows an invalid name behind a single WARNING in the
    gateway log, then runs the agent clock AND every cron schedule on server-local time.
    Surface it here, where doctor and the startup check both look. Silent when the
    interpreter has no tz database at all (bare Windows without ``tzdata``) — nothing can be
    judged there.
    """
    if "timezone" not in config:
        return
    tz = config.get("timezone")
    hint = ("Use an IANA zone name such as America/New_York or Asia/Tokyo (see "
            "`timedatectl list-timezones`). With an invalid value the agent clock and cron "
            "schedules silently fall back to server-local time. HERMES_TIMEZONE overrides "
            "this key when set.")
    if tz is not None and not isinstance(tz, str):
        _issue(issues, "error", f"timezone must be an IANA zone name string, got {tz!r}", hint)
        return
    if not (isinstance(tz, str) and tz.strip()):
        return
    name = tz.strip()
    try:
        import zoneinfo
        zoneinfo.ZoneInfo("UTC")  # is a tz database available at all?
    except Exception:
        return
    try:
        zoneinfo.ZoneInfo(name)
    except Exception:
        _issue(issues, "error", f"timezone {name!r} is not a valid IANA zone name", hint)
