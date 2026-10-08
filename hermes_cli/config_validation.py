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


def _validate_noting(config: Dict[str, Any], issues: List["ConfigIssue"]) -> None:
    """``noting`` shape check (02 §4.1): a malformed block must not silently mis-gate Noting."""
    from secretary.noting_policy import configuration_guidance, noting_settings_from_config

    settings = noting_settings_from_config(config)
    if settings.configuration_failure:
        _issue(issues, "error", "Noting conflicts with Hermes idle compaction",
               configuration_guidance(settings.configuration_failure))
    block = config.get("noting")
    if block is None:
        return
    if not isinstance(block, dict):
        _issue(issues, "error", f"noting must be a mapping, got {block!r}",
               "Use the documented block:\n  noting:\n    enabled: true\n    idle_delay_seconds: 500")
        return
    delay = block.get("idle_delay_seconds")
    if delay is not None and (isinstance(delay, bool) or not isinstance(delay, (int, float)) or delay < 0):
        _issue(issues, "error", f"noting.idle_delay_seconds must be a nonnegative number, got {delay!r}",
               "Seconds the main Conversation must stay turn-free after a main Turn ends before an "
               "Idle Trigger exists (default 500)")
    selection = block.get("auto_trigger_compaction_after_noting")
    if selection is not None and not isinstance(selection, dict):
        _issue(issues, "error", "noting.auto_trigger_compaction_after_noting must be a mapping",
               "It carries 'enabled' and 'threshold_tokens'; it selects the Idle runtime profile "
               "and is not itself a Trigger")
        return
    threshold = selection.get("threshold_tokens") if isinstance(selection, dict) else None
    if threshold is not None and (isinstance(threshold, bool) or not isinstance(threshold, int) or threshold <= 0):
        _issue(issues, "error",
               "noting.auto_trigger_compaction_after_noting.threshold_tokens must be a positive "
               f"token count or null, got {threshold!r}",
               "Use null to disable the profile selection, e.g. threshold_tokens: 120000")
