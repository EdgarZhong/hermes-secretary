"""Bounded read-only display windows, captured on one explicit SQLite snapshot.

Only identity/order work spans the transcript. Payload crosses the SQLite boundary
for the selected windows and at most twelve requested disclosure rows.
"""
from __future__ import annotations

import hashlib
import json
import time

from hermes_state_common import _RESET_END_REASONS_SQL, _legacy_reset_child_sql, _sql_json_extract
from hermes_state_compression import _CHAIN_STEP_SQL
from hermes_state_messages import DISPLAY_VISIBLE_SQL
from hermes_state_timeline import _snapshot


class RecoveryViewError(ValueError):
    def __init__(self, reason, message=None):
        super().__init__(message or reason)
        self.reason = reason


def selector(value=None):
    value = value or {"kind": "latest"}
    if not isinstance(value, dict) or value.get("kind", "latest") not in ("latest", "anchor"):
        raise RecoveryViewError("invalid_request", "selector kind must be latest or anchor")
    result = {"kind": value.get("kind", "latest")}
    if result["kind"] == "latest":
        result["limit"] = _integer(value.get("limit", 200), 1, 500)
        return result
    uid, row_id = value.get("anchor_uid"), value.get("anchor_row_id")
    if bool(uid) == bool(row_id) or (uid is not None and not isinstance(uid, str)):
        raise RecoveryViewError("invalid_request", "one anchor_uid or anchor_row_id is required")
    result.update(before=_integer(value.get("before", 100), 0, 499),
                  after=_integer(value.get("after", 99), 0, 499))
    if result["before"] + result["after"] + 1 > 500:
        raise RecoveryViewError("invalid_request", "window exceeds 500 rows")
    result.update({"anchor_uid": uid} if uid else {"anchor_row_id": _integer(row_id, 1, 2**63 - 1)})
    return result


def _integer(value, low, high):
    if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
        raise RecoveryViewError("invalid_request", f"integer must be between {low} and {high}")
    return value


def _owned_row(conn, sid, profile):
    row = conn.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
    if row is None or row["profile_name"] not in (None, profile):
        raise RecoveryViewError("not_found")
    return dict(row)


def _lineage(db, conn, requested, profile):
    row = _owned_row(conn, requested, profile)
    seen = {requested}
    # The official compression-child choice, on this SAME connection.
    for _ in range(1000):
        child = conn.execute(_CHAIN_STEP_SQL, (row["id"],)).fetchone()
        if child is None or child[0] in seen:
            break
        row = _owned_row(conn, child[0], profile)
        seen.add(row["id"])
    # Preserve resume's legacy continuation choice without opening a second conn.
    best, current = row, row
    for _ in range(32):
        child = conn.execute(
            "SELECT child.id FROM sessions child WHERE child.parent_session_id=? "
            f"AND {_sql_json_extract('child.model_config', '$._branched_from')} IS NULL "
            f"AND {_sql_json_extract('child.model_config', '$._delegate_from')} IS NULL "
            f"AND {_sql_json_extract('child.model_config', '$._reset_from')} IS NULL "
            f"AND NOT {_legacy_reset_child_sql('child', _RESET_END_REASONS_SQL)} "
            "AND COALESCE(child.source,'')!='tool' ORDER BY child.started_at DESC, child.id DESC LIMIT 1",
            (current["id"],)).fetchone()
        if child is None or child[0] in seen:
            break
        current = _owned_row(conn, child[0], profile)
        seen.add(current["id"])
        if conn.execute("SELECT 1 FROM messages WHERE session_id=? LIMIT 1", (current["id"],)).fetchone():
            best = current
    chain, row = [best], best
    for _ in range(1000):
        parent_id = row.get("parent_session_id")
        if not parent_id or db._is_explicit_fork_child_row(row, include_reset=True):
            break
        parent = _owned_row(conn, parent_id, profile)
        if parent["end_reason"] != "compression" or parent["id"] in {item["id"] for item in chain}:
            break
        chain.append(parent)
        row = parent
    return list(reversed(chain))


def _display_sql(db, conn, lineage):
    params = {f"s{i}": item["id"] for i, item in enumerate(lineage)}
    marks = ",".join(":" + key for key in params)
    # Durable display_identity is exactly the native display dedupe key. Only
    # old, unindexed rows invoke its read-only fallback; GET never backfills.
    def legacy_identity(role, content, timestamp, tool_id, calls, name, kind, metadata):
        row = dict(role=role, content=content, timestamp=timestamp, tool_call_id=tool_id,
                   tool_calls=calls, tool_name=name, display_kind=kind, display_metadata=metadata)
        return db._display_identity(db._display_dedupe_key(row))
    conn.create_function("recovery_identity", 8, legacy_identity, deterministic=True)
    sql = f"""WITH generations AS (
        SELECT message_uid, MAX(id) AS newest FROM messages
        WHERE session_id IN ({marks}) AND NULLIF(message_uid,'') IS NOT NULL GROUP BY message_uid
      ), keyed AS (
        SELECT m.id, m.active, m.message_uid,
          COALESCE(m.display_identity, recovery_identity(m.role,m.content,m.timestamp,m.tool_call_id,
                     m.tool_calls,m.tool_name,m.display_kind,m.display_metadata)) AS identity_key,
          COALESCE(m.display_order,m.id) AS first_order
        FROM messages m LEFT JOIN generations latest ON latest.message_uid=m.message_uid
        LEFT JOIN messages generation ON generation.id=latest.newest
        WHERE m.session_id IN ({marks}) AND (m.active=1 OR m.compacted=1)
          {DISPLAY_VISIBLE_SQL.replace('display_metadata', 'm.display_metadata')}
          AND (NULLIF(m.message_uid,'') IS NULL OR generation.active=1 OR generation.compacted=1)
      ), ranked AS (
        SELECT id, identity_key, MIN(first_order) OVER (PARTITION BY identity_key) AS sort_id,
          ROW_NUMBER() OVER (PARTITION BY identity_key ORDER BY active DESC,id DESC) AS preference
        FROM keyed
      ), display_rows AS (
        SELECT id AS row_id, sort_id, identity_key FROM ranked WHERE preference=1
      ), ordered AS (
        SELECT *, ROW_NUMBER() OVER (ORDER BY sort_id,row_id)-1 AS position FROM display_rows
      ) """
    return sql, params


def _identity(row):
    if row is None:
        return None
    return {"row_id": row["row_id"], "message_uid": row["message_uid"],
            "logical_order": row["sort_id"], "position": row["position"]}


def _meta(conn, sql, params, position):
    return conn.execute(sql + "SELECT o.*,m.message_uid FROM ordered o JOIN messages m ON m.id=o.row_id "
                        "WHERE position=:position", {**params, "position": position}).fetchone()


def _bounds(conn, sql, params, selection, total):
    if selection["kind"] == "range":
        rows = conn.execute(sql + "SELECT position FROM ordered WHERE sort_id BETWEEN :lo AND :hi "
                            "ORDER BY position LIMIT 501", {**params, "lo": selection["lo"], "hi": selection["hi"]}).fetchall()
        return (rows[0][0], rows[-1][0]) if rows else (0, -1)
    if selection["kind"] == "latest":
        return max(0, total - selection["limit"]), total - 1
    source = conn.execute(
        "SELECT * FROM messages WHERE " + ("message_uid=:anchor_uid" if "anchor_uid" in selection else "id=:anchor_row_id")
        + " AND session_id IN (" + ",".join(":" + key for key in params) + ") ORDER BY id DESC LIMIT 1",
        {**params, **selection}).fetchone()
    if source is None:
        raise RecoveryViewError("anchor_not_found")
    if source["message_uid"]:
        generation = conn.execute("SELECT active,compacted FROM messages WHERE message_uid=:uid AND session_id IN ("
                                  + ",".join(":" + key for key in params) + ") ORDER BY id DESC LIMIT 1",
                                  {**params, "uid": source["message_uid"]}).fetchone()
        if generation is None or not (generation[0] or generation[1]):
            raise RecoveryViewError("anchor_not_found")
    elif not (source["active"] or source["compacted"]):
        raise RecoveryViewError("anchor_not_found")
    key = source["display_identity"] or db_identity(conn, source)
    anchor = conn.execute(sql + "SELECT position FROM ordered WHERE identity_key=:key", {**params, "key": key}).fetchone()
    if anchor is None:
        raise RecoveryViewError("anchor_not_found")
    return max(0, anchor[0] - selection["before"]), min(total - 1, anchor[0] + selection["after"])


def db_identity(conn, row):
    return conn.execute("SELECT recovery_identity(?,?,?,?,?,?,?,?)", tuple(row[key] for key in (
        "role", "content", "timestamp", "tool_call_id", "tool_calls", "tool_name", "display_kind", "display_metadata"))).fetchone()[0]


def _read_window(db, conn, sql, params, selection, total):
    start, end = _bounds(conn, sql, params, selection, total)
    rows = conn.execute(sql + "SELECT m.*,o.position,o.sort_id FROM ordered o JOIN messages m ON m.id=o.row_id "
                        "WHERE position BETWEEN :start AND :end ORDER BY position LIMIT 501",
                        {**params, "start": start, "end": end}).fetchall()
    if len(rows) > 500:
        raise RecoveryViewError("coverage_gap")
    boundaries = [_meta(conn, sql, params, pos) for pos in (start, end, start - 1, end + 1)]
    window = dict(zip(("first", "last", "predecessor", "successor"), map(_identity, boundaries)))
    window.update(is_start=start == 0, is_end=end == total - 1, start=start, end=end,
                  returned=len(rows), total=total)
    messages = [db._row_to_message_dict(row, warn_context="recovery window", summary_flag=True) for row in rows]
    for message in messages:
        message.pop("position", None)
        message.pop("sort_id", None)
    return {"selector": selection, "window": window, "messages": messages}


def _details(db, conn, sql, params, details):
    ids = [_integer(value, 1, 2**63-1) for value in details]
    if len(ids) > 12:
        raise RecoveryViewError("invalid_request", "details requires at most 12 rows")
    if not ids:
        return []
    rows = conn.execute(sql + "SELECT m.* FROM ordered o JOIN messages m ON m.id=o.row_id WHERE m.id IN ("
                        + ",".join(f":d{i}" for i in range(len(ids))) + ") ORDER BY o.position",
                        {**params, **{f"d{i}": value for i, value in enumerate(ids)}}).fetchall()
    return [db._row_to_message_dict(row, warn_context="recovery details", summary_flag=True) for row in rows]


def read_view(db, requested_id, profile, selectors, *, details=(), proofs=(), identities=()):
    """Raw D read: all owner, lineage, windows, details and lease on one conn."""
    with _snapshot(db) as conn:
        lineage = _lineage(db, conn, requested_id, profile)
        sql, params = _display_sql(db, conn, lineage)
        total = conn.execute(sql + "SELECT COUNT(*) FROM ordered", params).fetchone()[0]
        windows = [_read_window(db, conn, sql, params, item, total) for item in [*selectors, *proofs]]
        detail_rows = _details(db, conn, sql, params, details)
        lease_key = db._session_turn_lease_key_on_conn(conn, lineage[-1]["id"])
        lease = conn.execute("SELECT holder,expires_at FROM session_turn_leases WHERE conversation_id=?",
                             (lease_key,)).fetchone()
        refs = _read_identities(conn, sql, params, lineage, identities)
        tail = conn.execute(sql + "SELECT m.id,m.message_uid,m.role,m.timestamp FROM ordered o "
                            "JOIN messages m ON m.id=o.row_id WHERE m.role='user' ORDER BY o.position DESC LIMIT 1", params).fetchone()
    return {"profile": profile, "requested_id": requested_id, "tip_id": lineage[-1]["id"],
            "lineage": [row["id"] for row in lineage],
            "rewind": [(row["id"], row.get("rewind_count", 0)) for row in lineage],
            "windows": windows, "details": detail_rows, "identities": refs,
            "turn_start": dict(tail) if tail else None,
            "lease": dict(lease) if lease and lease["expires_at"] > time.time() else None}


def _read_identities(conn, sql, params, lineage, identities):
    result = []
    # Identity-only probes, bounded per query even for a long native snapshot.
    for offset in range(0, len(identities), 100):
        batch = identities[offset:offset + 100]
        predicates, bound = [], dict(params)
        for i, item in enumerate(batch):
            key = "message_uid" if item.get("message_uid") else "tool_call_uid" if item.get("tool_call_uid") else "id"
            predicates.append(f"m.{key}=:ref{i}")
            bound[f"ref{i}"] = item.get("message_uid") or item.get("tool_call_uid") or item.get("row_id")
        rows = conn.execute(sql + "SELECT m.id,m.role,m.message_uid,m.tool_call_uid,m.tool_call_uids,m.session_id,m.active,m.compacted,o.sort_id, "
                            f"{_sql_json_extract('m.display_metadata', '$.turn_terminal.source_message_uid')} AS terminal_source_uid "
                            "FROM ordered o JOIN messages m ON m.id=o.row_id WHERE "
                            + " OR ".join(predicates), bound).fetchall()
        visible = [dict(row) for row in rows]
        result.extend({**row, "visible": True} for row in visible)
        marks = ",".join(":" + key for key in params)
        known = conn.execute("SELECT m.id,m.role,m.message_uid,m.tool_call_uid,m.tool_call_uids,m.session_id,m.active,m.compacted "
                             f"FROM messages m WHERE m.session_id IN ({marks}) AND (" + " OR ".join(predicates)
                             + ") AND (NULLIF(m.message_uid,'') IS NULL OR m.id=("
                             "SELECT MAX(g.id) FROM messages g WHERE g.message_uid=m.message_uid "
                             f"AND g.session_id IN ({marks}))) ORDER BY m.id DESC", bound).fetchall()
        seen = {row["message_uid"] or row["id"] for row in visible}
        for row in known:
            key = row["message_uid"] or row["id"]
            if key not in seen:
                result.append({**dict(row), "visible": False})
                seen.add(key)
    return result


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
                                     default=str).encode("utf-8", "surrogatepass")).hexdigest()


def project_view(raw, *, home=None):
    """Display projection is deliberately OUTSIDE the DB and history locks."""
    from hermes_cli.web_history_cards import history_cards
    import asyncio
    from hermes_cli.web_routers.sessions import _project_for_display, _project_user_image_refs
    windows = []
    for item in raw["windows"]:
        messages = asyncio.run(_project_user_image_refs(item["messages"], profile=raw["profile"]))
        cards = history_cards(_project_for_display(messages, home=home, inline_images=True))
        coverage = {key: raw[key] for key in ("profile", "requested_id", "tip_id", "lineage")}
        coverage.update(version=1, window=item["window"], digest=digest(cards))
        windows.append({"selector": item["selector"], "messages": cards, "coverage": coverage})
    details = _project_for_display(raw["details"], home=home, inline_images=True)
    return {**raw, "windows": windows, "details": details, "detail_digest": digest(details)}
