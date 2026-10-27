"""Ephemeral fingerprints for opt-in, bounded display-history synchronization.

The cache never owns transcript text. SQLite facts are captured by recovery_view;
projection and hashing run only after its snapshot/history locks have been released.
"""
from __future__ import annotations

from collections import OrderedDict
import copy
from dataclasses import dataclass
import json
from pathlib import Path
import secrets
import threading
import time


VERSION = 1
MAX_WINDOWS = 128
MAX_IDENTITIES = 500
TTL_SECONDS = 3600
_PRIVATE_FIELDS = frozenset({"api_content", "codex_reasoning_items", "codex_message_items"})
_REASONING_FIELDS = ("reasoning", "reasoning_content", "reasoning_details", "display_reasoning")
_IDENTITY_FIELDS = ("id", "session_id", "message_uid", "role", "timestamp", "display_kind")


def detail_revision(message):
    from hermes_state_recovery_view import digest
    return digest(visible_detail(message))


def visible_detail(message):
    """Exclude provider replay/opaque reasoning material from display fingerprints."""
    result = {key: value for key, value in message.items()
              if key not in _PRIVATE_FIELDS and key != "detail_revision"}
    metadata = result.get("display_metadata")
    if isinstance(metadata, dict):
        metadata = {key: value for key, value in metadata.items() if key != "turn_source"}
        if metadata:
            result["display_metadata"] = metadata
        else:
            result.pop("display_metadata", None)
    elif metadata is None:
        result.pop("display_metadata", None)
    if result.get("display_kind") == "hidden":
        return {key: value for key, value in result.items() if key in _IDENTITY_FIELDS}
    if "display_content" in result:
        result["content"] = result["display_content"]
    details = result.get("reasoning_details")
    if isinstance(details, str):
        try:
            details = json.loads(details)
        except ValueError:
            details = []
    if "reasoning_details" in result:
        from agent.reasoning_summaries import streamed_reasoning_detail_text
        visible = []
        for item in details if isinstance(details, list) else []:
            text = streamed_reasoning_detail_text(item)
            if isinstance(item, dict) and item.get("type") in ("reasoning", "thinking"):
                text = item.get("text")
            if isinstance(text, str) and text:
                visible.append({"type": "reasoning.text", "text": text})
        result["reasoning_details"] = visible
    return result


def detail_revisions(messages):
    return {str(row["id"]): detail_revision(row) for row in messages}


def with_detail_revisions(messages, *, canonical=None):
    revisions = detail_revisions(messages if canonical is None else canonical)
    return [{**row, "detail_revision": revisions[str(row["id"])]} for row in messages]


def _source_predicates():
    from hermes_state_common import QUEUED_PROMPT_METADATA_KEY, _sql_json_extract
    queued = _sql_json_extract("m.display_metadata", "$." + QUEUED_PROMPT_METADATA_KEY)
    origin = _sql_json_extract("m.display_metadata", "$.origin")
    producer = _sql_json_extract("m.display_metadata", "$.producer")
    terminal = _sql_json_extract("m.display_metadata", "$.turn_terminal.source_message_uid")
    marker_uid = _sql_json_extract("m.display_metadata", "$.turn_source.message_uid")
    marker_turn = _sql_json_extract("m.display_metadata", "$.turn_source.turn_id")
    eligible = ("m.role='user' AND COALESCE(m.display_kind,'') NOT IN "
                "('steer','hidden','model_switch','skill_invocation','compaction') "
                f"AND COALESCE({origin},'') NOT IN ('framework','notebook') "
                f"AND COALESCE({producer},'')!='noting_result'")
    marked = (f"typeof({marker_uid})='text' AND {marker_uid}=m.message_uid "
              f"AND typeof({marker_turn})='text' AND LENGTH(TRIM({marker_turn}))>0")
    known = (f"((COALESCE(m.display_kind,'') IN ('','auto_continue') AND COALESCE({queued},0)=0) OR "
             f"(NULLIF(m.message_uid,'') IS NOT NULL AND (({marked}) OR COALESCE({terminal},'')=m.message_uid)))")
    return eligible, known, queued


def _source_row(conn, sql, params, native_source):
    eligible, known, queued = _source_predicates()
    native = None
    if native_source:
        native = conn.execute(sql + "SELECT m.id,m.session_id,m.message_uid,o.position FROM ordered o "
                           f"JOIN messages m ON m.id=o.row_id WHERE {eligible} AND m.id=:source_id "
                           "AND m.message_uid=:source_uid AND m.session_id=:source_session", {
                               **params, "source_id": native_source.get("row_id"),
                               "source_uid": native_source.get("message_uid"),
                               "source_session": native_source.get("session_id")}).fetchone()
        if native is not None and native_source.get("_active"):
            return dict(native)
    row = conn.execute(sql + "SELECT m.id,m.session_id,m.message_uid,o.position FROM ordered o "
                       f"JOIN messages m ON m.id=o.row_id WHERE {eligible} AND {known} "
                       "ORDER BY o.position DESC LIMIT 1", params).fetchone()
    if native is not None and (row is None or native["position"] >= row["position"]):
        row = native
    if row is None:
        return None
    # Legacy typed rows can be a true Turn OR an append-only delivery. Without
    # native provenance, never hydrate an older region and call it the latest Turn.
    ambiguous = conn.execute(sql + "SELECT 1 FROM ordered o JOIN messages m ON m.id=o.row_id "
                            f"WHERE {eligible} AND NOT {known} AND COALESCE({queued},0)=0 "
                            "AND o.position>:proven_source LIMIT 1", {**params, "proven_source": row["position"]}).fetchone()
    return None if ambiguous else dict(row)


def read_latest_thinking(db, conn, sql, params, total, native_source=None):
    """Read only Thinking candidates within the recent 500, on the caller's snapshot.

    Complete facts of a candidate row are needed for the SAME full-detail revision
    as its ordinary detail endpoint, even when its tools have not been expanded.
    No non-Thinking payload outside the requested windows is hydrated.
    """
    from hermes_state_common import _sql_json_extract
    source = _source_row(conn, sql, params, native_source)
    if source is None:
        return {"source": None, "messages": [], "positions": {}}
    start = max(total - MAX_IDENTITIES, source["position"], 0)
    terminal = _sql_json_extract("m.display_metadata", "$.turn_terminal.outputs")
    detail_value = "CASE WHEN part.type='object' THEN part.value ELSE '{}' END"
    readable_details = ("EXISTS (SELECT 1 FROM json_each(CASE WHEN json_valid(m.reasoning_details) "
        "THEN m.reasoning_details ELSE '[]' END) part WHERE "
        f"json_extract({detail_value},'$.type') IN ('reasoning.text','reasoning.summary','reasoning','thinking') "
        f"AND (COALESCE(json_extract({detail_value},'$.text'),'')!='' OR "
        f"COALESCE(json_extract({detail_value},'$.summary'),'')!=''))")
    rows = conn.execute(sql + "SELECT m.*,o.position FROM ordered o JOIN messages m ON m.id=o.row_id "
                        "WHERE o.position>=:thinking_start AND ((m.role='assistant' AND ("
                        "COALESCE(m.reasoning,'')!='' OR COALESCE(m.reasoning_content,'')!='' "
                        f"OR {readable_details})) OR (m.role='user' AND EXISTS ("
                        f"SELECT 1 FROM json_each({terminal}) part WHERE "
                        f"json_extract({detail_value},'$.kind')='reasoning' "
                        f"AND COALESCE(json_extract({detail_value},'$.text'),'')!=''))) ORDER BY o.position",
                        {**params, "thinking_start": start}).fetchall()
    messages, positions = [], {}
    for row in rows:
        positions[str(row["id"])] = row["position"]
        message = db._row_to_message_dict(row, warn_context="latest Thinking", summary_flag=True)
        message.pop("position", None)
        messages.append(message)
    return {"source": {"row_id": source["id"], "session_id": source["session_id"],
                       "message_uid": source["message_uid"]}, "messages": messages, "positions": positions}


def project_latest_thinking(raw, *, home=None):
    from hermes_cli.web_routers.sessions import _project_for_display
    full = _project_for_display(raw["messages"], home=home, inline_images=True)
    rows = []
    for original in full:
        if original.get("display_kind") == "hidden":
            continue
        original = visible_detail(original)
        row = {key: original[key] for key in _IDENTITY_FIELDS if key in original}
        row.update({key: original[key] for key in _REASONING_FIELDS if original.get(key)})
        terminal = (original.get("display_metadata") or {}).get("turn_terminal")
        if isinstance(terminal, dict):
            outputs = [item for item in terminal.get("outputs", [])
                       if isinstance(item, dict) and item.get("kind") == "reasoning" and item.get("text")]
            if outputs:
                row["display_metadata"] = {"turn_terminal": {"outputs": outputs}}
        if any(row.get(key) for key in _REASONING_FIELDS) or "display_metadata" in row:
            rows.append(row)
    ids = {str(row["id"]) for row in rows}
    return {"source": raw["source"], "order": [row["id"] for row in rows], "rows": rows,
            "positions": {key: value for key, value in raw["positions"].items() if key in ids},
            "revisions": {key: value for key, value in detail_revisions(full).items() if key in ids}}


@dataclass(frozen=True)
class _Fingerprint:
    owner: tuple
    revisions: dict
    thinking_revisions: dict
    coverage: dict
    expires: float


class HistorySyncCache:
    def __init__(self, *, max_windows=MAX_WINDOWS, ttl=TTL_SECONDS, clock=time.monotonic):
        self._windows = OrderedDict()
        self._lock = threading.Lock()
        self._max_windows, self._ttl, self._clock = max_windows, ttl, clock

    def exchange(self, owner, cursor, revisions, thinking_revisions, coverage):
        # Copies/hash work stay outside the short in-memory cache lock.
        now = self._clock()
        token = secrets.token_urlsafe(24)
        entry = _Fingerprint(owner, dict(revisions), dict(thinking_revisions), copy.deepcopy(coverage), now + self._ttl)
        cacheable = len(set(revisions) | set(thinking_revisions)) <= MAX_IDENTITIES
        with self._lock:
            expired = [key for key, item in self._windows.items() if item.expires <= now]
            for key in expired:
                self._windows.pop(key, None)
            previous = self._windows.get(cursor) if isinstance(cursor, str) else None
            if previous is not None and previous.owner != owner:
                previous = None
            if previous is not None:
                self._windows.move_to_end(cursor)
            if cacheable:
                self._windows[token] = entry
                while len(self._windows) > self._max_windows:
                    self._windows.popitem(last=False)
        return token, previous


_CACHE = HistorySyncCache()


def synchronize_window(projected, window, cursor=None, *, cache=None):
    from hermes_state_recovery_view import digest
    cache = _CACHE if cache is None else cache
    thinking = projected["latest_thinking"]
    revisions = window["detail_revisions"]
    owner = (str(Path(projected["db_path"]).resolve()), projected["profile"], projected["requested_id"],
             digest(window["selector"]), VERSION)
    token, previous = cache.exchange(owner, cursor, revisions, thinking["revisions"], window["coverage"])
    mode = "delta" if previous is not None else "snapshot"
    old_rows = previous.revisions if previous else {}
    old_thinking = previous.thinking_revisions if previous else {}
    sync = {"version": VERSION, "cursor": token, "mode": mode,
            "order": [row["id"] for row in window["messages"]], "revisions": revisions,
            "latest_thinking": {**thinking, "rows": [row for row in thinking["rows"]
                if old_thinking.get(str(row["id"])) != thinking["revisions"][str(row["id"])]]}}
    if previous is not None:
        sync["base_cursor"] = cursor
    return {"sync": sync, "messages": [row for row in window["messages"]
            if old_rows.get(str(row["id"])) != revisions[str(row["id"])]]}
