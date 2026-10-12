"""Timezone-aware clock for Hermes.

``now()`` returns a tz-aware datetime in the user's configured IANA timezone. Resolution order:
``HERMES_TIMEZONE`` env var, then ``timezone`` in ``~/.hermes/config.yaml``, else server-local
time. Invalid timezone values log a warning and fall back — never crash.
"""

import locale
import logging
import os
import re
import threading
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation, ROUND_FLOOR
from pathlib import Path
from typing import Dict, Optional, Tuple
from zoneinfo import ZoneInfo

from hermes_constants import get_config_path

logger = logging.getLogger(__name__)

# Cache keyed by timezone *source* identity. This process can multiplex profiles by switching
# HERMES_HOME, so one unkeyed global would leak the first profile's timezone into later
# profile-scoped work (e.g. the desktop multiplex cron ticker persisting another profile's
# ``next_run_at``). Entries are published atomically under ``_cache_lock`` as one
# ``identity -> (name, ZoneInfo | None)`` value, so racing resolvers can never publish a mixed
# identity/value pair. Call reset_cache() after in-place config changes.
_cache_lock = threading.Lock()
_tz_cache: Dict[Tuple[str, str], Tuple[str, Optional[ZoneInfo]]] = {}

_SURROGATE_RE = re.compile(r"[\ud800-\udfff]")
# ASCII plus surrogateescape'd bytes only: the shape of native text decoded with the wrong codec.
_ESCAPED_BYTES_RE = re.compile(r"[\x00-\x7f\udc80-\udcff]*")


def _repair_surrogates(text: str, encoding: Optional[str] = None) -> str:
    """Make locale text JSON/UTF-8 safe; a no-op (same object) on valid text.

    Windows hands back zone names in the ANSI code page (``heure d'\\xe9t\\xe9``) but a UTF-8
    ``LC_CTYPE`` (UTF-8 mode, or a library flipping the process locale mid-run) decodes those
    bytes with ``surrogateescape`` into lone surrogates. Recover the bytes and decode them with
    the ANSI code page; when that is not possible, replace each surrogate with U+FFFD."""
    if text.isascii() or not _SURROGATE_RE.search(text):
        return text
    if _ESCAPED_BYTES_RE.fullmatch(text):
        try:
            return text.encode("ascii", "surrogateescape").decode(encoding or locale.getencoding())
        except (LookupError, UnicodeError):
            pass
    return _SURROGATE_RE.sub("\ufffd", text)


def safe_strftime(value: datetime, fmt: str) -> str:
    """``value.strftime(fmt)`` that never raises or returns lone surrogates over locale text.

    ``datetime.strftime`` splices ``tzname()`` into the format as UTF-8, so a zone name carrying
    surrogates (see ``_repair_surrogates``) raises ``UnicodeEncodeError`` before any string exists
    (#102910). On that failure ``%Z`` is rendered from the repaired name instead. Output for valid
    locale text is byte-identical to ``strftime`` (the system prompt must stay cache-stable)."""
    try:
        return _repair_surrogates(value.strftime(fmt))
    except UnicodeEncodeError:
        zone = _repair_surrogates(value.tzname() or "").replace("%", "%%")
        return _repair_surrogates(value.strftime(
            re.sub(r"%([%Z])", lambda m: zone if m.group(1) == "Z" else "%%", fmt)))


def _env_timezone() -> str:
    """``HERMES_TIMEZONE`` when it may speak for the active profile. Under the multiplexed
    gateway the env var holds only the DEFAULT profile's value (bridged from its config.yaml at
    startup), so every routed profile must read its own config.yaml instead."""
    from agent.secret_scope import is_multiplex_active  # lazy: secret_scope pulls in more than a clock needs

    if is_multiplex_active():
        return ""
    return os.getenv("HERMES_TIMEZONE", "").strip()


def _timezone_cache_identity() -> Tuple[str, str]:
    tz_env = _env_timezone()
    return ("environment", tz_env) if tz_env else ("config", str(get_config_path()))


def _resolve_timezone_name(config_path=None) -> str:
    """Read the configured IANA timezone string (or ``""``). Does file I/O — callers cache."""
    tz_env = _env_timezone() if config_path is None else ""
    if tz_env:
        return tz_env
    try:
        # Prefer the shared cached effective-config loader (mtime-keyed + libyaml, managed overlay
        # included so an administrator can pin ``timezone``): a direct safe_load of a large
        # config.yaml costs ~100 ms and this ran inside the FIRST system prompt build. The bare
        # parse is the stdlib-safe fallback for bootstrap consumers without hermes_cli importable.
        try:
            from hermes_cli.config_effective import load_user_config_effective
            cfg = load_user_config_effective(config_path or get_config_path())
        except Exception:
            import hermes_yaml as yaml
            config_path = config_path or get_config_path()
            cfg = (yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}) if config_path.exists() else {}
        if cfg:
            tz_cfg = cfg.get("timezone", "")
            if isinstance(tz_cfg, str) and tz_cfg.strip():
                return tz_cfg.strip()
    except Exception:
        pass
    return ""


def _timezone_entry(config_path=None) -> Tuple[str, Optional[ZoneInfo]]:
    """Cached ``(configured name, ZoneInfo | None)`` for the active profile."""
    cache_identity = ("config", str(config_path)) if config_path is not None else _timezone_cache_identity()
    with _cache_lock:
        entry = _tz_cache.get(cache_identity)
        if entry is not None:
            return entry
    # Resolve outside the lock (config file I/O); first writer wins so concurrent resolvers of the
    # same identity converge on one ZoneInfo object.
    name = _resolve_timezone_name(config_path)
    tz = None
    if name:
        try:
            tz = ZoneInfo(name)
        except Exception as exc:
            logger.warning("Invalid timezone '%s': %s. Falling back to server local time.", name, exc)
    with _cache_lock:
        return _tz_cache.setdefault(cache_identity, (name, tz))


def get_timezone() -> Optional[ZoneInfo]:
    """Return the active profile's configured ZoneInfo, or None (server-local)."""
    return _timezone_entry()[1]


def get_timezone_name() -> str:
    """The active profile's configured IANA timezone string, or ``""`` (server-local). Same
    resolution and cache as :func:`get_timezone`; for handing ``TZ`` to sandboxed children."""
    return _timezone_entry()[0]


def reset_cache() -> None:
    """Clear the cached timezone so the next call re-resolves it (after config/env changes)."""
    with _cache_lock:
        _tz_cache.clear()


def now() -> datetime:
    """Current time as a tz-aware datetime: configured zone, else server-local."""
    tz = get_timezone()
    return datetime.now(tz) if tz is not None else datetime.now().astimezone()


def format_timestamp(value, *, profile_home=None):
    """Render an absolute instant with an explicit offset; never mutate stored values.

    Existing timezone-aware ISO text keeps its exact spelling. An explicit owner reads
    that profile's config rather than a launch-profile environment timezone.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        if value.tzinfo is None:
            raise ValueError("An absolute timestamp must include a timezone")
        return value.isoformat()
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass  # Numeric epoch strings remain accepted at legacy output boundaries.
        else:
            if parsed.tzinfo is None:
                raise ValueError("An absolute timestamp must include a timezone")
            return value
    config_path = Path(profile_home) / "config.yaml" if profile_home is not None else None
    tz = _timezone_entry(config_path)[1]
    try:
        instant = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError("Invalid absolute timestamp") from exc
    if not instant.is_finite():
        raise ValueError("Invalid absolute timestamp")
    whole = int(instant.to_integral_value(rounding=ROUND_FLOOR))
    moment = datetime.fromtimestamp(whole, tz=timezone.utc).astimezone(tz)
    rendered = moment.isoformat(timespec="seconds")
    # time.time() can carry sub-microsecond digits. Keep the original numeric
    # precision in ISO text rather than silently rounding the stored instant.
    fraction = format(instant - whole, "f")[1:].rstrip("0") if instant != whole else ""
    return rendered[:19] + fraction + rendered[19:]


def readable_schedule_display(schedule, display):
    """Render an existing absolute one-shot label without changing stored intent."""
    if (isinstance(schedule, dict) and schedule.get("kind") == "once"
            and isinstance(display, str) and display.startswith("once at ")):
        try:
            instant = datetime.fromisoformat(schedule["run_at"].replace("Z", "+00:00"))
            if instant.tzinfo is None:
                instant = instant.replace(tzinfo=now().tzinfo)
            return "once at " + format_timestamp(instant)
        except (KeyError, TypeError, ValueError):
            pass
    return display
