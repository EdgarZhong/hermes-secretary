"""Identity dependencies of surviving native output inside one bounded snapshot."""
from __future__ import annotations

import json


def tool_occurrences(row):
    try:
        mapping = json.loads(row.get("tool_call_uids") or "{}")
    except (TypeError, ValueError):
        mapping = {}
    values = mapping.values() if isinstance(mapping, dict) else ()
    result = {value for item in values for value in (item if isinstance(item, list) else [item]) if isinstance(value, str)}
    if row.get("tool_call_uid"):
        result.add(row["tool_call_uid"])
    return result


def _scope(event):
    payload = event.get("payload") or {}
    source = payload.get("source_message") or {}
    uid = payload.get("message_uid") or payload.get("assistant_message_uid") or source.get("message_uid")
    scope = tuple(payload.get(key) for key in ("turn_id", "stored_session_id", "conversation_ref")) + (uid,)
    return scope if all(isinstance(value, str) and value for value in scope) else None


def _paired_scope(event, by_seq, surviving):
    payload = event.get("payload") or {}
    source = by_seq.get(payload.get("source_event_seq"))
    expected = payload.get("native_type") if event["type"] == "message.output_delta" else "tool." + str(payload.get("phase"))
    if (source is None or source["seq"] not in surviving or source.get("type") != expected
            or source.get("payload") != payload.get("native_payload")):
        return None
    return _scope(event)


def _committed_row(event, known):
    payload = event.get("payload") or {}
    source = payload.get("source_message") or {}
    row = known.get(source.get("message_uid"))
    if (row is None or row.get("id") != source.get("row_id") or row.get("role") != source.get("role")
            or row.get("session_id") != payload.get("stored_session_id") or not row.get("visible")
            or not (row.get("active") or row.get("compacted"))):
        return None
    return row


def _committed_calls(source, row):
    try:
        mapping = json.loads(row.get("tool_call_uids") or "{}")
    except (TypeError, ValueError):
        return None
    if not isinstance(mapping, dict):
        return None
    calls = source.get("tool_calls") or []
    for call in calls:
        if not isinstance(call, dict) or not isinstance(call.get("tool_call_uid"), str):
            return None
        occurrences = mapping.get(call.get("id"))
        if call["tool_call_uid"] not in (occurrences if isinstance(occurrences, list) else [occurrences]):
            return None
    return calls


def active_output_dependencies(original, live, known):
    """Keep only existing exact-scope owner/commit facts, never durable output bodies.

    A durable call list does not prove a result. Its surviving typed tool frames
    still need their native owner and call identities when replay starts empty.
    Result identities referenced by that unchanged call list must also survive,
    so an already completed sibling cannot be reconstructed as a queued call.
    """
    by_seq = {event["seq"]: event for event in original}
    surviving = {event["seq"] for event in live}
    scopes = {_paired_scope(event, by_seq, surviving) for event in live
              if event.get("type") in {"message.output_delta", "tool.output"}}
    scopes.discard(None)
    owners = {_scope(event) for event in original if event.get("type") == "message.output_state"
              and (event.get("payload") or {}).get("state") == "open"}
    scopes &= owners
    needed = {event["seq"] for event in original
              if event.get("type") == "message.output_state" and _scope(event) in scopes}
    result_scopes = set()
    for event in original:
        if event.get("type") != "message.output_committed" or _scope(event) not in scopes:
            continue
        source = (event.get("payload") or {}).get("source_message") or {}
        row = _committed_row(event, known)
        if source.get("role") != "assistant" or row is None:
            continue
        calls = _committed_calls(source, row)
        if calls is None:
            continue
        needed.add(event["seq"])
        result_scopes.update((_scope(event)[:3], call["tool_call_uid"]) for call in calls)
    for event in original:
        if event.get("type") != "message.output_committed":
            continue
        source = (event.get("payload") or {}).get("source_message") or {}
        scope = _scope(event)
        if source.get("role") != "tool" or scope is None:
            continue
        row = _committed_row(event, known)
        if (row is not None and row.get("tool_call_uid") == source.get("tool_call_uid")
                and (scope[:3], source.get("tool_call_uid")) in result_scopes):
            needed.add(event["seq"])
    return needed
