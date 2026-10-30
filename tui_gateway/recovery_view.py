"""Optional activate envelope: bounded D0 / native replay S / bounded D1.

No database/replay lock overlap; native history ownership is held only while
capturing raw facts, never while projecting or serializing their display form.
"""
from __future__ import annotations

import copy
import sqlite3
import time
from pathlib import Path

from hermes_state_recovery_view import RecoveryViewError, digest, project_view, read_view, selector
from tui_gateway import event_replay
from tui_gateway.inflight_output import snapshot
from tui_gateway.recovery_output_dependencies import active_output_dependencies, tool_occurrences as _tool_occurrences


_RETRYABLE = {"view_changed", "coverage_gap", "replay_gap"}


def parse_request(value):
    if not isinstance(value, dict) or type(value.get("version")) is not int or value.get("version") != 1:
        raise RecoveryViewError("invalid_request", "recovery_view.version must be 1")
    if not isinstance(value.get("stored_id"), str) or not isinstance(value.get("profile"), str):
        raise RecoveryViewError("invalid_request", "stored_id and profile are required")
    if "sync_version" in value and (type(value["sync_version"]) is not int or value["sync_version"] != 1):
        raise RecoveryViewError("invalid_request", "recovery_view.sync_version must be 1")
    windows = value.get("windows")
    if not isinstance(windows, list) or not 1 <= len(windows) <= 2:
        raise RecoveryViewError("invalid_request", "recovery requires one or two windows")
    selections, receipts = [], []
    for window in windows:
        if not isinstance(window, dict) or not isinstance(window.get("receipt"), dict):
            raise RecoveryViewError("invalid_request", "each window requires a REST coverage receipt")
        if value.get("sync_version") == 1 and "cursor" in window and not isinstance(window["cursor"], str):
            raise RecoveryViewError("invalid_request", "window cursor must be a string")
        selections.append(selector(window.get("selector")))
        receipt = window["receipt"]
        if (receipt.get("version") != 1 or receipt.get("profile") != value["profile"]
                or receipt.get("requested_id") != value["stored_id"] or not isinstance(receipt.get("digest"), str)):
            raise RecoveryViewError("invalid_request", "receipt owner/version mismatch")
        receipts.append(receipt)
    if not any(item["kind"] == "latest" for item in selections):
        raise RecoveryViewError("invalid_request", "recovery requires a latest window")
    details = value.get("details", [])
    if not isinstance(details, list) or len(details) > 12:
        raise RecoveryViewError("invalid_request", "details requires at most twelve row identities")
    ids = []
    for identity in details:
        row_id = identity.get("row_id") if isinstance(identity, dict) else identity
        if isinstance(row_id, bool) or not isinstance(row_id, int) or row_id <= 0:
            raise RecoveryViewError("invalid_request", "detail identity requires a positive row_id")
        ids.append(row_id)
    return selections, receipts, ids


def _failure(reason, request, sid):
    return {"version": 1, "owner": {"profile": request.get("profile"), "stored_id": request.get("stored_id"),
                                    "runtime_id": sid},
            "epoch": event_replay.replay_epoch(), "complete": False, "reason": reason}


def _proofs(raw):
    return [{"kind": "range", "lo": item["window"]["first"]["logical_order"],
             "hi": item["window"]["last"]["logical_order"]}
            for item in raw["windows"] if item["window"]["first"] is not None]


def _references(state):
    result = {}
    for event in state.get("events", []):
        payload = event.get("payload") or {}
        identity = event.get("_output_identity") or {}
        receipt = payload.get("persisted_turn") or {}
        candidates = [payload.get("message"), payload.get("source_message"), *(payload.get("source_messages") or []),
                      *(receipt.get("source_messages") or [])]
        for key in ("message_uid", "assistant_message_uid"):
            uid = payload.get(key) or identity.get(key)
            if uid:
                result[uid] = {"message_uid": uid}
        tool_uid = payload.get("tool_call_uid") or identity.get("tool_call_uid")
        if tool_uid:
            result["tool:" + tool_uid] = {"tool_call_uid": tool_uid}
        for message in candidates:
            if isinstance(message, dict) and (message.get("message_uid") or message.get("row_id")):
                key = (message.get("message_uid"), message.get("row_id"))
                result[key] = {"message_uid": message.get("message_uid"), "row_id": message.get("row_id")}
    return list(result.values())


def _turn_context(session):
    agent = session.get("agent")
    turn = session.get("inflight_turn")
    token = turn.get("_terminal_token") if isinstance(turn, dict) else None
    source = turn.get("_terminal_source") if isinstance(turn, dict) else None
    source_identity = tuple(source.get(key) for key in ("db_path", "session_id", "row_id", "message_uid")) if isinstance(source, dict) else None
    return (id(agent), id(turn), token, getattr(agent, "_current_turn_id", None),
            getattr(agent, "_active_session_turn_lease_holder", None), bool(session.get("running")),
            bool(session.get("_manual_compress_active")),
            (turn.get("streaming"), turn.get("status")) if isinstance(turn, dict) else None, source_identity)


def _source_hint(session):
    turn = session.get("inflight_turn")
    return turn.get("_terminal_source") if isinstance(turn, dict) else None


def _history_sync_source(session, db_path):
    """Copy native source identities only; never copy a retained output body."""
    source = _source_hint(session)
    active = bool(session.get("running")) and not session.get("_manual_compress_active")
    if isinstance(source, dict) and isinstance(source.get("db_path"), str):
        if Path(source["db_path"]).resolve() == Path(db_path).resolve():
            return {**{key: source.get(key) for key in ("row_id", "message_uid", "session_id")},
                    "_holder": getattr(session.get("agent"), "_active_session_turn_lease_holder", None), "_active": active}
    with event_replay._replay_lock:
        state = session.get("_inflight_output")
        if not isinstance(state, dict) or state.get("complete") is not True:
            return None
        for event in state.get("events", []):
            if event.get("type") not in {"message.source_committed", "message.user_committed", "message.complete"}:
                continue
            payload = event.get("payload") or {}
            receipt = payload.get("persisted_turn") or {}
            candidates = [payload.get("message"), *(receipt.get("source_messages") or [])]
            for row in candidates:
                if (isinstance(row, dict) and row.get("role") == "user" and row.get("message_uid")
                        and type(row.get("row_id")) is int):
                    return {"row_id": row["row_id"], "message_uid": row["message_uid"],
                            "session_id": row.get("session_id") or payload.get("stored_session_id"),
                            "_holder": getattr(session.get("agent"), "_active_session_turn_lease_holder", None), "_active": active}
    return None


def _settled_manual_source(session, raw, db_path):
    source = _source_hint(session)
    if not isinstance(source, dict) or not isinstance(source.get("db_path"), str):
        return False
    if Path(source["db_path"]).resolve() != Path(db_path).resolve():
        return False
    return any(_settled_reference_matches(row, {**source, "role": "user"})
               and row.get("terminal_source_uid") == source.get("message_uid")
               and row.get("terminal_status") == "error" and row.get("terminal_outputs_complete") is True
               for row in raw["identities"])


def _settled_reference_matches(row, reference):
    """Exact native address first, then an internal same-snapshot DB proof of retirement."""
    if (not row or row.get("message_uid") != reference.get("message_uid") or not reference.get("message_uid")
            or row.get("role") != reference.get("role") or not row.get("visible")
            or not (row.get("active") or row.get("compacted"))):
        return False
    addresses = [{"row_id": row.get("id"), "session_id": row.get("session_id")},
                 *row.get("_settled_reference_aliases", [])]
    return any(item["row_id"] == reference.get("row_id")
               and (reference.get("session_id") is None or item["session_id"] == reference["session_id"])
               for item in addresses)


def _manual_maintenance(session, raw, db_path):
    """Prove a native busy maintenance phase, never borrow an actual Turn lease."""
    if not session.get("_manual_compress_active") or not session.get("running"):
        return False
    if raw.get("lease") is not None:
        raise RecoveryViewError("view_changed")
    turn = session.get("inflight_turn")
    if turn is None:
        return True
    if (isinstance(turn, dict) and turn.get("streaming") is False and turn.get("status") == "error"
            and _settled_manual_source(session, raw, db_path)):
        return True
    raise RecoveryViewError("runtime_unavailable")


def _native_source(session, db, raw):
    """Identity-only copy of this native Turn's observed durable user source."""
    turn = session.get("inflight_turn")
    if not session.get("running") or not isinstance(turn, dict) or turn.get("_terminal_token") is None:
        return None
    source = turn.get("_terminal_source")
    if not isinstance(source, dict):
        return None
    path = source.get("db_path")
    if not isinstance(path, str) or Path(path).resolve() != Path(db.db_path).resolve():
        raise RecoveryViewError("owner_mismatch")
    identity = {key: source.get(key) for key in ("session_id", "row_id", "message_uid")}
    if (identity["session_id"] not in raw["lineage"] or type(identity["row_id"]) is not int
            or not isinstance(identity["message_uid"], str) or not identity["message_uid"]):
        raise RecoveryViewError("view_changed")
    return identity


def _external_turn_holder(session, raw):
    """Compare opaque ownership against the valid lease from this DB snapshot."""
    holder = (raw.get("lease") or {}).get("holder", "")
    if session.get("running") or not holder:
        return None
    if holder == getattr(session.get("agent"), "_active_session_turn_lease_holder", None):
        return None
    return holder


def _capture(server, sid, session, request, selections, ids):
    lock = session["history_lock"]
    if not lock.acquire(timeout=0.25):
        raise RecoveryViewError("history_busy")
    try:
        if server._sessions.get(sid) is not session or session.get("_finalized") or session.get("_closing"):
            raise RecoveryViewError("runtime_unavailable")
        actual_profile = server.profile_name_for_home(session.get("profile_home")) or server._response_profile_name(None)
        if actual_profile != request["profile"]:
            raise RecoveryViewError("owner_mismatch")
        with server._session_db(session) as db:
            if db is None:
                raise RecoveryViewError("runtime_unavailable")
            sync_args = {}
            manual_source = _source_hint(session) if session.get("_manual_compress_active") else None
            manual_refs = [manual_source] if isinstance(manual_source, dict) else []
            if request.get("sync_version") == 1:
                sync_args = {"history_sync": True, "native_source": _history_sync_source(session, db.db_path)}
            d0 = read_view(db, request["stored_id"], actual_profile, selections, details=ids,
                           identities=manual_refs, **sync_args)
            if server._session_lookup_key(session, fallback=sid) != d0["tip_id"]:
                raise RecoveryViewError("view_changed")
            context = _turn_context(session)
            maintenance = _manual_maintenance(session, d0, db.db_path)
            source = None if maintenance else _native_source(session, db, d0)
            external = _external_turn_holder(session, d0)
            state = None if external else snapshot(session, sid, include_internal=True)
            running = bool(session.get("running")) or bool(external)
            # Snapshot S's watermark is also meaningful for confirmed idle with no
            # native output. A generating Turn NEVER falls back to plain text.
            if state is None:
                with event_replay._replay_lock:
                    state = {"events": [], "seq": event_replay._replay_next_seq.get(sid, 0),
                             "epoch": event_replay.replay_epoch(), "complete": True}
                if not external and not maintenance and (running or session.get("inflight_turn")):
                    raise RecoveryViewError("runtime_unavailable")
            d1 = read_view(db, request["stored_id"], actual_profile, selections, details=ids,
                           proofs=_proofs(d0), identities=[*_references(state), *manual_refs, *([source] if source else [])], **sync_args)
            if (context != _turn_context(session) or maintenance != _manual_maintenance(session, d1, db.db_path)
                    or (not maintenance and source != _native_source(session, db, d1))
                    or external != _external_turn_holder(session, d1)
                    or server._session_lookup_key(session, fallback=sid) != d1["tip_id"]):
                raise RecoveryViewError("view_changed")
        runtime = {"running": running, "status": "working" if external else server._session_live_status(sid, session),
                   "external_holder": external,
                   "manual_maintenance": maintenance,
                   "turn_started_at": None if external or maintenance else server._turn_started_at(session),
                   "history_version": int(session.get("history_version", 0)),
                   "turn_id": getattr(session.get("agent"), "_current_turn_id", None) or next((
                       event.get("payload", {}).get("turn_id") for event in reversed(state["events"])
                       if event.get("type") == "message.source_committed"), None),
                   "holder": external or getattr(session.get("agent"), "_active_session_turn_lease_holder", None),
                   "native_source": source,
                   "inflight": None if external or maintenance else server._inflight_snapshot(session),
                   "queued": server._queued_prompt_snapshot(session)}
    finally:
        lock.release()
    return d0, state, d1, runtime


def _thinking_prefix(d0, d1):
    """Keep every old Thinking fact; only new durable tail rows may extend it."""
    old, new = d0.get("latest_thinking"), d1.get("latest_thinking")
    if old is None or new is None:
        return old == new
    if old["source"] != new["source"] or new["order"][:len(old["order"])] != old["order"]:
        return False
    if old["rows"] != new["rows"][:len(old["rows"])]:
        return False
    if any(old[key][str(row_id)] != new[key].get(str(row_id))
           for key in ("positions", "revisions") for row_id in old["order"]):
        return False
    # A formerly non-Thinking row gaining reasoning is an old-row rewrite,
    # even when it was outside the requested page. D1 additions must start
    # beyond D0's entire durable cut, in the authoritative logical order.
    cut = d0["windows"][0]["coverage"]["window"]["total"]
    tail = [new["positions"][str(row_id)] for row_id in new["order"][len(old["order"]):]]
    return all(position >= cut for position in tail) and all(left < right for left, right in zip(tail, tail[1:]))


def _same_history(d0, d1, count):
    if any(d0[key] != d1[key] for key in ("tip_id", "lineage", "rewind")):
        return False
    originals = [item for item in d0["windows"] if item["coverage"]["window"]["first"] is not None]
    proofs = d1["windows"][count:]
    return (len(originals) == len(proofs) and all(
        old["coverage"]["digest"] == new["coverage"]["digest"]
        and old["coverage"]["window"]["returned"] == new["coverage"]["window"]["returned"]
        and old.get("detail_revisions") == new.get("detail_revisions")
        for old, new in zip(originals, proofs)) and d0["detail_digest"] == d1["detail_digest"]
        and _thinking_prefix(d0, d1))


def _turn_proof(d0, d1, state, runtime):
    lease0, lease1 = d0["lease"], d1["lease"]
    if (lease0 or {}).get("holder") != (lease1 or {}).get("holder"):
        raise RecoveryViewError("view_changed")
    if runtime.get("manual_maintenance"):
        if lease0 is not None or lease1 is not None:
            raise RecoveryViewError("view_changed")
        return
    if runtime.get("external_holder"):
        if runtime["external_holder"] != (lease1 or {}).get("holder"):
            raise RecoveryViewError("view_changed")
        return
    if not runtime["running"]:
        if lease1 is not None:
            raise RecoveryViewError("runtime_unavailable")
        return
    turn_id = runtime["turn_id"]
    holder = (lease1 or {}).get("holder", "")
    if not turn_id or not holder or runtime["holder"] != holder:
        raise RecoveryViewError("runtime_unavailable")
    _prove_source(d1, state, runtime)
    for event in state["events"]:
        payload = event.get("payload") or {}
        if payload.get("turn_id") and payload["turn_id"] != turn_id:
            raise RecoveryViewError("view_changed")
        if payload.get("stored_session_id") and payload["stored_session_id"] not in d1["lineage"]:
            raise RecoveryViewError("view_changed")


def _prove_source(d1, state, runtime):
    native = runtime.get("native_source")
    if native is not None:
        if not any(row.get("id") == native["row_id"] and row.get("message_uid") == native["message_uid"]
                   and row.get("session_id") == native["session_id"] and row.get("role") == "user"
                   and row.get("visible") and row.get("active") for row in d1["identities"]):
            raise RecoveryViewError("view_changed")
        return
    source = next((event.get("payload", {}) for event in state["events"]
                   if event.get("type") == "message.source_committed"
                   and event.get("payload", {}).get("turn_id") == runtime["turn_id"]), None)
    if source is None:
        raise RecoveryViewError("runtime_unavailable")
    uid = (source.get("source_boundary") or {}).get("user_message_uid") or (source.get("message") or {}).get("message_uid")
    if not uid or not any(row.get("message_uid") == uid and row.get("visible") and row.get("active") for row in d1["identities"]):
        raise RecoveryViewError("view_changed")


def _persisted_event(event, known, tool_results):
    payload = event.get("payload") or {}
    identity = event.get("_output_identity") or payload
    uid = identity.get("message_uid") or identity.get("assistant_message_uid")
    source = payload.get("message") or payload.get("source_message") or {}
    if not uid and isinstance(source, dict):
        uid = source.get("message_uid")
    row = known.get(uid)
    if row is None:
        return False
    tool_uid = identity.get("tool_call_uid")
    if tool_uid and row.get("visible"):
        if tool_uid not in _tool_occurrences(row):
            raise RecoveryViewError("view_changed")
        # A durable assistant call is not a durable result. Keep its live tool
        # until that exact occurrence has a real result representative.
        return tool_uid in tool_results
    return True


def _closed_source_boundary(receipt, sources, known):
    boundary = receipt.get("source_boundary") or {}
    first, last = sources[0], sources[-1]
    normal_finish = last.get("role") == "assistant" and last.get("row_id") == receipt.get("final_assistant_row_id")
    terminal_finish = known[first["message_uid"]].get("terminal_source_uid") == first["message_uid"]
    return (all(boundary.get(key) is True for key in (
                "prefix_unchanged", "compression_unchanged", "all_rows_committed"))
            and first.get("role") == "user" and first["message_uid"] == boundary.get("user_message_uid")
            and first.get("row_id") == receipt.get("user_row_id")
            and receipt.get("row_ids") == [source.get("row_id") for source in sources]
            and (normal_finish or terminal_finish))


def _completion_sources_accounted(receipt, known):
    """Prove the completed native suffix independently of the single-user fast path."""
    # Compaction retires prompt rows but preserves their exact display identity.
    # Rewind/deletion still fail the visible-row and receipt identity checks.
    sources = receipt.get("source_messages") or []
    if not sources or not all(_settled_reference_matches(known.get(source.get("message_uid")), source)
                              for source in sources):
        return False
    # A consumed steer deliberately leaves the legacy whole-Turn receipt
    # incomplete. Its closed, fully committed suffix can still account for
    # notifications; failures instead close at the native terminal source row.
    return bool(receipt.get("complete") or _closed_source_boundary(receipt, sources, known))


def _persisted_reasoning_notice(event, state, known):
    if event.get("type") != "reasoning.available":
        return False
    for completed in state["events"]:
        if completed.get("type") != "message.complete" or completed["seq"] < event["seq"]:
            continue
        receipt = (completed.get("payload") or {}).get("persisted_turn") or {}
        if _completion_sources_accounted(receipt, known):
            return True
    return False


def _settled_source_frames_match(events, source):
    return all(_settled_reference_matches(source, event.get("payload", {}).get("message") or {})
               for event in events if event.get("type") in {"message.user_committed", "message.source_committed"})


def _idle_snapshot_accounted(state, known):
    sources = [event.get("payload") or {} for event in state["events"]
               if event.get("type") == "message.source_committed"]
    for payload in sources:
        source = payload.get("message") or {}
        uid, turn_id = source.get("message_uid"), payload.get("turn_id")
        if not uid or not source.get("row_id") or not turn_id:
            continue
        if any((event.get("payload") or {}).get("turn_id") not in (None, turn_id) for event in state["events"]):
            continue
        row = known.get(uid)
        # source_committed proves this exact source once existed. The bounded
        # D1 identity query now proves it deleted/retired; all of that Turn is
        # obsolete. An unknown output WITHOUT this source proof is rejected.
        if row is None or not row.get("visible"):
            return True
        if (row.get("terminal_source_uid") == uid and _settled_reference_matches(row, source)
                and _settled_source_frames_match(state["events"], row)):
            return True
    return False


def _terminal_output_frames(events, lineage):
    """Require the native typed owner and exact legacy pairing, including draft tools."""
    by_seq = {event["seq"]: event for event in events}
    turns = set()
    opened = {event.get("payload", {}).get("message_uid") for event in events
              if event["type"] == "message.output_state" and event.get("payload", {}).get("state") == "open"}
    closed = {event.get("payload", {}).get("message_uid") for event in events
              if event["type"] == "message.output_state" and event.get("payload", {}).get("state") in {"closed", "uncommitted"}}
    paired = set()
    typed = {"message.output_delta", "tool.output", "message.output_state"}
    for event in events:
        if event["type"] not in typed:
            continue
        payload = event.get("payload") or {}
        if not payload.get("turn_id") or payload.get("stored_session_id") not in lineage:
            return False
        turns.add(payload["turn_id"])
        if event["type"] == "message.output_state":
            continue
        source = by_seq.get(payload.get("source_event_seq"))
        expected = payload.get("native_type") if event["type"] == "message.output_delta" else "tool." + str(payload.get("phase"))
        if source is None or source["type"] != expected or source.get("payload") != payload.get("native_payload"):
            return False
        uid = payload.get("message_uid") or payload.get("assistant_message_uid")
        if uid not in closed:
            return False
        paired.add(source["seq"])
    legacy = {"message.delta", "reasoning.delta", "message.interim", "tool.generating", "tool.start", "tool.complete"}
    return len(turns) == 1 and opened <= closed and all(
        event["seq"] in paired for event in events if event["type"] in legacy)


def _terminal_snapshot_accounted(state, d1, known):
    from hermes_state_turn_terminal import _reconcile_outputs
    from tui_gateway.turn_terminal import observed_output_events
    events = state["events"]
    if not events or events[-1]["type"] != "message.complete":
        return False
    payload = events[-1].get("payload") or {}
    receipt = payload.get("persisted_turn") or {}
    sources = receipt.get("source_messages") or []
    if payload.get("status") not in {"error", "interrupted", "cancelled"} or not _completion_sources_accounted(receipt, known):
        return False
    source = known[sources[0]["message_uid"]]
    if (source.get("terminal_source_uid") != source["message_uid"]
            or source.get("terminal_status") != ("interrupted" if payload["status"] == "cancelled" else payload["status"])
            or source.get("terminal_outputs_complete") is not True
            or not _closed_source_boundary(receipt, sources, known)):
        return False
    # Legacy submit need not emit user_committed. Its native completion receipt
    # still proves the exact source; any additional source frame must agree.
    if not _settled_source_frames_match(events, source):
        return False
    if not _terminal_output_frames(events, d1["lineage"]):
        return False
    allowed = {"message.user_committed", "message.source_committed", "message.start", "message.complete",
               "message.delta", "reasoning.delta", "message.interim", "message.output_delta", "message.output_state",
               "message.output_committed", "tool.generating", "tool.start", "tool.complete", "tool.output",
               "reasoning.available", "thinking.delta", "status.update"}
    if any(event["type"] not in allowed for event in events):
        return False
    outcome = {"outputs": observed_output_events(events)}
    _reconcile_outputs(outcome, [row for row in known.values()
                                 if row.get("visible") and (row.get("active") or row.get("compacted"))])
    return outcome.get("outputs_complete", True) and digest(outcome.get("outputs", [])) == source.get("terminal_outputs_digest")


def _clean_snapshot(state, d1, *, running):
    known = {row["message_uid"]: row for row in d1["identities"] if row.get("message_uid")}
    if not running and (_idle_snapshot_accounted(state, known) or _terminal_snapshot_accounted(state, d1, known)):
        return {**state, "events": []}
    tools = {row["tool_call_uid"] for row in d1["identities"]
             if row.get("tool_call_uid") and row.get("role") == "tool"}
    pairs = {event["payload"]["source_event_seq"]: event["payload"] for event in state["events"]
             if event.get("type") in ("message.output_delta", "tool.output")}
    discarded, events = set(), []
    for original in state["events"]:
        event = {**original}
        if event["seq"] in pairs:
            event.setdefault("_output_identity", pairs[event["seq"]])
        if _persisted_event(event, known, tools):
            discarded.add(event["seq"])
        elif running:
            events.append(copy.deepcopy(event))
        elif _persisted_reasoning_notice(event, state, known):
            discarded.add(event["seq"])
        elif event.get("type") not in ("message.start", "message.complete", "thinking.delta", "status.update"):
            # An idle runtime cannot lend the previous Turn's unpersisted output
            # to a rewritten transcript. Lack of evidence is a retryable failure.
            raise RecoveryViewError("runtime_unavailable")
    retained = {event["seq"] for event in events}
    if running:
        retained.update(active_output_dependencies(state["events"], events, known))
    result = []
    for original in state["events"]:
        if original["seq"] not in retained:
            continue
        event = copy.deepcopy(original)
        if (event.get("payload") or {}).get("source_event_seq") in discarded:
            continue
        event.pop("_output_identity", None)
        result.append(event)
    return {**state, "events": result}


def _coverage(d0, d1, count):
    old_latest = next((item for item in d0["windows"] if item["selector"]["kind"] == "latest"), None)
    new_latest = next((item for item in d1["windows"][:count] if item["selector"]["kind"] == "latest"), None)
    if old_latest and new_latest:
        old, new = old_latest["coverage"]["window"], new_latest["coverage"]["window"]
        if old["last"] and new["first"] and new["first"]["position"] > old["last"]["position"] + 1:
            raise RecoveryViewError("coverage_gap")


def _envelope(server, sid, session, request, selections, receipts, ids):
    d0, state, d1, runtime = _capture(server, sid, session, request, selections, ids)
    home = session.get("profile_home")
    d0, d1 = project_view(d0, home=home), project_view(d1, home=home)
    if not _same_history(d0, d1, len(selections)):
        raise RecoveryViewError("view_changed")
    _turn_proof(d0, d1, state, runtime)
    _coverage(d0, d1, len(selections))
    state = _clean_snapshot(state, d1, running=runtime["running"] and not runtime.get("manual_maintenance"))
    suffix = event_replay.read_replay_cut(sid, state["seq"])
    if suffix["truncated"] or suffix["epoch"] != state["epoch"]:
        raise RecoveryViewError("replay_gap")
    windows = []
    for item, receipt, requested in zip(d1["windows"], receipts, request["windows"]):
        matched = item["coverage"] == receipt
        synchronized = {}
        if request.get("sync_version") == 1:
            from hermes_state_history_sync import synchronize_window
            synchronized = synchronize_window(d1, item, requested.get("cursor"))
            matched = matched and synchronized["sync"]["mode"] == "delta" and not synchronized["messages"]
        windows.append({"selector": item["selector"], "coverage": item["coverage"], "matched": matched,
                        **({"sync": synchronized["sync"]} if synchronized else {}),
                        **({} if matched else {"messages": synchronized.get("messages", item["messages"])})})
    return {"version": 1, "owner": {"profile": d1["profile"], "stored_id": request["stored_id"],
                                    "tip_id": d1["tip_id"], "runtime_id": sid},
            "epoch": state["epoch"], "complete": True, "windows": windows,
            "details": d1["details"], "detail_digest": d1["detail_digest"],
            "state_snapshot": state, "stream_cut": {"snapshot_seq": state["seq"], "latest_seq": suffix["latest_seq"],
                                                       "events": suffix["events"], "truncated": False},
            "running": runtime["running"], "status": runtime["status"],
            **({"live_output_available": False} if runtime.get("external_holder") else {}),
            "turn_started_at": runtime["turn_started_at"],
            **({"inflight": runtime["inflight"]} if runtime["inflight"] else {}),
            **({"queued": runtime["queued"]} if runtime["queued"] else {})}


def activate_payload(server, sid, session, request):
    selections, receipts, ids = parse_request(request)
    result = None
    for _attempt in range(2):
        try:
            result = _envelope(server, sid, session, request, selections, receipts, ids)
            break
        except RecoveryViewError as exc:
            result = _failure(exc.reason, request, sid)
            if exc.reason not in _RETRYABLE:
                break
        except sqlite3.Error:
            result = _failure("read_failed", request, sid)
            break
    payload = {"session_id": sid, "session_key": server._session_lookup_key(session, fallback=sid),
               "message_count": 0, "messages": [], "messages_omitted": True,
               "info": server._fallback_session_info(session), "recovery_view_version": 1,
               "recovery_view": result, "running": result.get("running", bool(session.get("running"))),
               "status": result.get("status", "resuming"), "started_at": float(session.get("created_at") or time.time())}
    if result["complete"]:
        payload["state_snapshot"] = result["state_snapshot"]
        payload["message_count"] = max((item["coverage"]["window"]["total"] for item in result["windows"]), default=0)
        payload["turn_started_at"] = result["turn_started_at"]
        for key in ("inflight", "queued"):
            if key in result:
                payload[key] = result[key]
    for key, value in (("open_requests", server._open_requests(sid)),
                       ("pending_approval", server._pending_approval_request_payload(str(session.get("session_key") or ""))),
                       ("pending_connection", server._pending_connection_request_payload(sid))):
        if value:
            payload[key] = value
    return server._attach_todo_state(payload, session)


def activate(server, rid, params, session):
    sid = str(params.get("session_id") or "")
    recovery = params.get("recovery_view")
    if recovery is not None:
        try:
            parse_request(recovery)
        except RecoveryViewError as exc:
            return server._err(rid, -32602, str(exc))
    with server._session_resume_lock:
        refusal = server._reattach_refusal(rid, sid, session)
        if refusal is not None:
            return refusal
        acquired = session["history_lock"].acquire(timeout=0.25) if recovery is not None else session["history_lock"].acquire()
        if acquired:
            try:
                server._rebind_live_transport(sid, session, server.current_transport() or server._stdio_transport)
            finally:
                session["history_lock"].release()
    if recovery is None:
        return server._ok(rid, server._live_session_payload(
            sid, session, touch=True, omit_messages=server.is_truthy_value(params.get("omit_messages", False))))
    if not acquired:
        return server._ok(rid, {"session_id": sid, "messages": [], "message_count": 0, "info": {},
                               "recovery_view_version": 1, "recovery_view": _failure("history_busy", recovery, sid)})
    return server._ok(rid, activate_payload(server, sid, session, recovery))
