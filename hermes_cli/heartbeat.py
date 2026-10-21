"""Heartbeat facade: native Session state, or globally enabled Conversation-owned UI wakeups.

Injection remains a plain user message without a system-prompt mutation or toolset
swap. Real user work wins the idle boundary; missed ticks coalesce. Conversation
Heartbeat execution requires the existing UI backend host to be running.
"""

from __future__ import annotations

import json
import logging
import re
import time
from dataclasses import asdict, dataclass
from typing import Any, Optional

from secretary.heartbeat import heartbeat_set_note, ui_heartbeat_enabled

logger = logging.getLogger(__name__)

MIN_INTERVAL_SECONDS = 60  # floor: re-entering more often than once a minute is a busy-loop, not a heartbeat
POLL_SECONDS = 5.0  # how often drivers poll for due heartbeats; not user-facing

HEARTBEAT_PROMPT_TEMPLATE = (
    "[Heartbeat — recurring instruction, fires every {interval}]\n{prompt}\n\n"
    "If there is nothing meaningful to do or report for this instruction "
    "right now, reply briefly that nothing has changed and stop — do not invent work."
)

_INTERVAL_RE = re.compile(
    r"^\s*(?:every\s+)?(\d+(?:\.\d+)?)\s*(s|sec|secs|seconds?|m|min|mins|minutes?|h|hr|hrs|hours?|d|days?)\s*$", re.IGNORECASE)

_UNIT_SECONDS = {
    **dict.fromkeys(("s", "sec", "secs", "second", "seconds"), 1),
    **dict.fromkeys(("m", "min", "mins", "minute", "minutes"), 60),
    **dict.fromkeys(("h", "hr", "hrs", "hour", "hours"), 3600),
    **dict.fromkeys(("d", "day", "days"), 86400),
}

# field -> (coercer, default used when the stored value is missing/falsy)
_STATE_FIELDS = {
    "prompt": (str, ""), "interval_seconds": (int, 0), "status": (str, "active"),
    "created_at": (float, 0.0), "last_fired_at": (float, 0.0), "fire_count": (int, 0),
}


def parse_interval(text: str) -> Optional[int]:
    """Parse ``10m`` / ``every 2h`` / ``every 90 minutes`` into seconds.

    None when not an interval; below ``MIN_INTERVAL_SECONDS`` returns -1 so callers can tell "too small" apart.
    """
    m = _INTERVAL_RE.match(text) if text else None
    if not m:
        return None
    seconds = int(float(m.group(1)) * _UNIT_SECONDS[m.group(2).lower()])
    return -1 if seconds < MIN_INTERVAL_SECONDS else seconds


def format_interval(seconds: int) -> str:
    """Human-readable interval (``600`` → ``10m``)."""
    seconds = int(seconds)
    units = ((86400, "d"), (3600, "h"), (60, "m"))
    return next((f"{seconds // unit}{suffix}" for unit, suffix in units if seconds % unit == 0), f"{seconds}s")


@dataclass
class HeartbeatState:
    """Serializable per-session heartbeat."""

    prompt: str
    interval_seconds: int
    status: str = "active"          # active | paused | cleared
    created_at: float = 0.0
    last_fired_at: float = 0.0
    fire_count: int = 0

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False)

    @classmethod
    def from_json(cls, raw: str) -> "HeartbeatState":
        data = json.loads(raw)
        return cls(**{name: coerce(data.get(name) or default) for name, (coerce, default) in _STATE_FIELDS.items()})

    def is_due(self, now: Optional[float] = None) -> bool:
        if (self.status != "active" or self.interval_seconds <= 0
                or (not self.prompt and not getattr(self, "_conversation_heartbeat", False) and not ui_heartbeat_enabled())):
            return False
        return (time.time() if now is None else now) - (self.last_fired_at or self.created_at) >= self.interval_seconds

    def render_prompt(self, timestamp: Optional[float] = None) -> str:
        from secretary.heartbeat import render_heartbeat
        if ui_heartbeat_enabled():
            return render_heartbeat(self.prompt, time.time() if timestamp is None else timestamp)
        return HEARTBEAT_PROMPT_TEMPLATE.format(interval=format_interval(self.interval_seconds), prompt=self.prompt)


def _get_session_db() -> Optional[Any]:
    """Persistence goes through the goals module's per-HERMES_HOME cached SessionDB (one shared connection)."""
    try:
        from hermes_cli.goals import _get_session_db as _goals_db
        return _goals_db()
    except Exception as exc:  # pragma: no cover
        logger.debug("HeartbeatManager: SessionDB bootstrap failed (%s)", exc)
        return None


_META_PREFIX = "heartbeat:"


def _conversation_store(session_id, db):
    from secretary.heartbeat_store import ConversationHeartbeatStore, enabled_for_db
    return ConversationHeartbeatStore(db, session_id) if db is not None and enabled_for_db(db) else None


def load_heartbeat(session_id: str, *, db=None) -> Optional[HeartbeatState]:
    db = (db if db is not None else _get_session_db()) if session_id else None
    if store := _conversation_store(session_id, db):
        return store.load()
    return _load_native_heartbeat(session_id, db)


def _load_native_heartbeat(session_id, db):
    if db is None:
        return None
    try:
        raw = db.get_meta(_META_PREFIX + session_id)
    except Exception as exc:
        logger.debug("HeartbeatManager: get_meta failed: %s", exc, exc_info=True)
        return None
    try:
        state = HeartbeatState.from_json(raw) if raw else None
    except Exception as exc:
        logger.warning("HeartbeatManager: could not parse stored heartbeat for %s: %s", session_id, exc, exc_info=True)
        return None
    return None if state is None or state.status == "cleared" else state


def store_has_active_heartbeat(db: Any) -> bool:
    """Probe the owning Profile's selected store; unreadable native rows retain the full sweep."""
    from secretary.heartbeat_store import enabled_for_db
    if enabled_for_db(db):
        with db._read_ctx() as conn:
            return conn.execute("SELECT 1 FROM secretary_heartbeats WHERE status='active' LIMIT 1").fetchone() is not None
    for _key, raw in db.list_meta_prefix(_META_PREFIX):
        try:
            if HeartbeatState.from_json(raw).status == "active":
                return True
        except Exception:
            return True
    return False


def save_heartbeat(session_id: str, state: HeartbeatState, *, db=None) -> None:
    if not session_id:
        return
    db = db if db is not None else _get_session_db()
    if db is None:
        from hermes_cli.goals import _warn_dropped_write
        _warn_dropped_write("HeartbeatManager", "heartbeat", session_id)
        return
    if store := _conversation_store(session_id, db):
        store.save(state)
        return
    try:
        db.set_meta(_META_PREFIX + session_id, state.to_json())
    except Exception as exc:
        logger.debug("HeartbeatManager: set_meta failed: %s", exc)


class HeartbeatManager:
    """Session-locator facade for native or Conversation state and due-tick decisions.

    Drivers (CLI thread / gateway task) call :meth:`due_prompt` on a poll cadence while the session is
    idle; a non-None return is the user-role message to inject.
    """

    def __init__(self, session_id: str, *, db=None):
        self.session_id = session_id
        self._db = db if db is not None else _get_session_db()
        self._state: Optional[HeartbeatState] = _load_native_heartbeat(session_id, self._db)
        self._last_claim: Optional[tuple[float, int]] = None  # (last_fired_at, fire_count) before the last due_prompt
        self._conversation_claim = None

    def _store(self):
        if self._db is None:
            self._db = _get_session_db()
        return _conversation_store(self.session_id, self._db)

    @property
    def state(self) -> Optional[HeartbeatState]:
        return store.load() if (store := self._store()) else self._state

    def has_heartbeat(self) -> bool:
        return (state := self.state) is not None and state.status in {"active", "paused"}

    def is_active(self) -> bool:
        return (state := self.state) is not None and state.status == "active"

    def status_line(self) -> str:
        s = self.state
        if s is None:
            return "No heartbeat. Set one with /heartbeat every <interval> <prompt>."
        every = format_interval(s.interval_seconds)
        fired = f", fired {s.fire_count}×" if s.fire_count else ""
        if s.status == "active":
            next_in = max(0, int((s.last_fired_at or s.created_at) + s.interval_seconds - time.time()))
            return f"♥ Heartbeat (every {every}, next in ~{next_in}s{fired}): {s.prompt}"
        icon = "⏸ " if s.status == "paused" else ""
        return f"{icon}Heartbeat ({s.status}, every {every}{fired}): {s.prompt}"

    def set(self, prompt: str, interval_seconds: int) -> HeartbeatState:
        prompt = (prompt or "").strip()
        store = self._store()
        if self._db is None and ui_heartbeat_enabled():
            raise ValueError("Heartbeat Conversation storage unavailable")
        if not prompt and store is None:
            raise ValueError("heartbeat prompt is empty")
        interval_seconds = int(interval_seconds)
        if interval_seconds < MIN_INTERVAL_SECONDS:
            raise ValueError(f"interval must be at least {MIN_INTERVAL_SECONDS}s")
        state = HeartbeatState(prompt=prompt, interval_seconds=interval_seconds, status="active", created_at=time.time())
        if store is not None:
            return store.save(state)
        self._state = state
        save_heartbeat(self.session_id, self._state, db=self._db)
        return self._state

    def _set_status(self, status: str, *, reanchor: bool = False) -> Optional[HeartbeatState]:
        if store := self._store():
            return store.set_status(status, reanchor=reanchor)
        if not self._state:
            return None
        self._state.status = status
        if reanchor:
            self._state.last_fired_at = time.time()
        save_heartbeat(self.session_id, self._state, db=self._db)
        return self._state

    def pause(self) -> Optional[HeartbeatState]:
        return self._set_status("paused")

    def resume(self) -> Optional[HeartbeatState]:
        # Re-anchor so resuming doesn't instantly fire a stale tick.
        return self._set_status("active", reanchor=True)

    def clear(self) -> bool:
        cleared = self._set_status("cleared") is not None
        self._state = None
        return cleared

    def due_prompt(self, now: Optional[float] = None) -> Optional[str]:
        """Return the injection prompt if the heartbeat is due, else None.

        The fire is recorded immediately (before the turn runs) so overlapping polls or a long turn can never
        double-fire the same tick. Missed ticks coalesce: the anchor resets to NOW, not the theoretical
        schedule.
        """
        if store := self._store():
            result = store.claim(now)
            if result is None:
                return None
            state, claim = result
            self._conversation_claim = (store, claim)
            from secretary.heartbeat import render_heartbeat
            from secretary.noting_scope import owning_db_scope
            with owning_db_scope(store.db):
                return render_heartbeat(state.prompt, state.last_fired_at)
        s = self._state
        if s is None or not s.prompt or not s.is_due(now):
            return None
        self._last_claim = (s.last_fired_at, s.fire_count)
        s.last_fired_at = now if now is not None else time.time()
        s.fire_count += 1
        save_heartbeat(self.session_id, s, db=self._db)
        return HEARTBEAT_PROMPT_TEMPLATE.format(interval=format_interval(s.interval_seconds), prompt=s.prompt)

    def abandon_fire(self) -> bool:
        """Rewind the fire recorded by the last :meth:`due_prompt` whose turn never started, so the tick stays
        due for the next poll instead of being silently consumed. Mirrors ``LoopManager.abandon_tick``. Skipped
        (False) when the persisted state moved on — a pause/resume/clear that landed in between wins."""
        if self._conversation_claim is not None:
            store, claim = self._conversation_claim
            self._conversation_claim = None
            return store.refund(claim)
        claim, s = self._last_claim, self._state
        if claim is None or s is None:
            return False
        current = load_heartbeat(self.session_id, db=self._db)
        if current is None or current.status != "active" or (current.last_fired_at, current.fire_count) != (
                s.last_fired_at, s.fire_count):
            return False
        s.last_fired_at, s.fire_count = claim
        self._last_claim = None
        save_heartbeat(self.session_id, s, db=self._db)
        return True

    def fire_is_current(self) -> bool:
        if self._conversation_claim is None:
            return True
        store, claim = self._conversation_claim
        from secretary.heartbeat_store import enabled_for_db
        return enabled_for_db(store.db) and store.claim_is_current(claim)


def migrate_heartbeat_to_session(old_session_id: str, new_session_id: str) -> bool:
    """Native: copy/archive on compression. Conversation mode: confirm the shared owner without copying."""
    if not old_session_id or not new_session_id or old_session_id == new_session_id:
        return False
    try:
        db = _get_session_db()
        if store := _conversation_store(old_session_id, db):
            child = _conversation_store(new_session_id, db)
            return bool(store.load() and child and child.conversation_ref == store.conversation_ref)
        state = load_heartbeat(old_session_id)
        if state is None or load_heartbeat(new_session_id) is not None:
            return False
        save_heartbeat(new_session_id, state)
        state.status = "cleared"
        save_heartbeat(old_session_id, state)
        return True
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("HeartbeatManager: migration failed: %s", exc)
        return False


__all__ = [
    "HeartbeatState", "HeartbeatManager", "parse_interval", "format_interval", "load_heartbeat", "save_heartbeat",
    "migrate_heartbeat_to_session", "HEARTBEAT_PROMPT_TEMPLATE", "MIN_INTERVAL_SECONDS", "POLL_SECONDS", "heartbeat_set_note",
]
