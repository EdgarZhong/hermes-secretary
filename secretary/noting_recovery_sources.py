"""Reconstruct a failed Noting's inputs from existing native durable records."""
from __future__ import annotations

import copy
import json
import re
from dataclasses import dataclass

from secretary.notebook_contract import SECTIONS, section_for_type
from secretary.notebook_items import item_entry, item_row_conn, require_item_owner


class NotingRecoveryError(ValueError):
    """A named existing source is missing or outside the requested ownership."""


def decoded(value, default=None):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except ValueError:
            return default
    return value if value is not None else default


@dataclass
class RecoveredNoting:
    admission: dict
    failed_child: dict
    prefix: list
    suffix: list
    root: str
    tools: list
    working_state: dict
    base_snapshot_id: str | None
    sources: dict


def _control_data(messages):
    for message in messages:
        content = message.get("content")
        if not isinstance(content, str) or "CURRENT NOTING CONTROL" not in content:
            continue
        control = content.split("CURRENT NOTING CONTROL", 1)[1]
        try:
            data, _ = json.JSONDecoder().raw_decode(control[control.index("{"):])
        except (ValueError, TypeError):
            continue
        if isinstance(data, dict) and "working_notebook" in data:
            return data
    raise NotingRecoveryError("Missing failed child initial CURRENT NOTING CONTROL working_notebook")


def _restore_entry(conn, ref, entry):
    version = entry.get("version_id") if isinstance(entry, dict) else None
    try:
        row = item_row_conn(conn, version)
        require_item_owner(conn, row, ref)
        return item_entry(row, ref)
    except ValueError as exc:
        raise NotingRecoveryError(f"Missing owned immutable Notebook version: {version}") from exc


def _working_state(conn, ref, messages, initial):
    state = {section: [] for section in SECTIONS}
    for section in SECTIONS:
        for entry in initial.get(section, []):
            state[section].append(_restore_entry(conn, ref, entry))
    # Successful tool results are receipts of already-persisted versions. Never
    # replay maintain, which would allocate new identities and operation times.
    calls = {}
    for message in messages:
        if message.get("role") == "assistant":
            calls.update({call.get("id"): call.get("function", {}).get("name")
                          for call in message.get("tool_calls", []) if isinstance(call, dict)})
        if (message.get("role") != "tool" or
                (message.get("tool_name") or calls.get(message.get("tool_call_id"))) not in {"notebook_maintain", "notebook_create", "notebook_update", "notebook_archive"}):
            continue
        result = decoded(message.get("content"), {})
        if not isinstance(result, dict) or result.get("success") is not True:
            continue
        if result.get("archived") is True and result.get("entry_id"):
            for section in SECTIONS:
                state[section] = [entry for entry in state[section] if entry["entry_id"] != result["entry_id"]]
        receipts = list(result.get("updated_entries", []))
        if isinstance(result.get("entry"), dict):
            receipts.append(result["entry"])
        for entry in receipts:
            if not isinstance(entry, dict) or not entry.get("version_id"):
                continue
            restored = _restore_entry(conn, ref, entry)
            section = section_for_type(restored["entry_type"])
            entries = state[section]
            index = next((i for i, old in enumerate(entries) if old["entry_id"] == restored["entry_id"]), None)
            if index is None:
                entries.append(restored)
            else:
                entries[index] = restored

    return state


def _parent_rows(db, conn, ref, admission, child_rows):
    sources = db._foreground_source_rows_conn(conn, ref)
    # Native append-only generations survive in Full even after compaction. The
    # admission records the exact published boundary that was Active at freeze.
    interval = admission["compression_interval_id"]
    boundary_id = int(interval.rsplit(":", 1)[1]) if interval.startswith("compaction:") else None
    horizon = child_rows[0]["id"] if child_rows else float("inf")
    before = [row for row in sources if row["id"] < horizon]
    start = 0
    if boundary_id is not None:
        start = next((i for i, row in enumerate(before) if row["id"] == boundary_id), None)
        if start is None:
            raise NotingRecoveryError(f"Missing admitted compaction boundary row: {boundary_id}")
    segment = before[start:]
    # A later compaction may already have landed before child startup. Its
    # carried copies belong to the next generation, not the admitted prefix.
    end = next((i for i, row in enumerate(segment) if i > 0 and
                db._project_foreground_row(row, ref, full=True)["is_compaction"]), len(segment))
    segment = segment[:end]
    anchor = admission["anchor_message_uid"]
    positions = [i for i, row in enumerate(segment) if row["message_uid"] == anchor]
    if not positions:
        raise NotingRecoveryError(f"Missing admitted parent Anchor message: {anchor}")
    segment = segment[:positions[-1] + 1]
    winners = {}
    for index, row in enumerate(segment):
        winners[row["message_uid"]] = (index, row)
    rows = [row for _, row in sorted(winners.values())]
    return rows


def _tools(db, conn, failed, ref, admitted_at, data, root):
    pin = decoded(failed.get("tool_names"))
    tools = pin.get("tools") if isinstance(pin, dict) else pin
    if isinstance(tools, list) and all(isinstance(tool, dict) for tool in tools):
        return copy.deepcopy(tools), "failed_child.tool_names"
    original_parent = db.get_session(failed.get("parent_session_id")) or {}
    parent_pin = decoded(original_parent.get("tool_names"), {})
    parent_tools = parent_pin.get("tools") if isinstance(parent_pin, dict) else parent_pin
    if (original_parent.get("system_prompt") == root and isinstance(parent_tools, list)
            and all(isinstance(tool, dict) for tool in parent_tools)):
        return copy.deepcopy(parent_tools), "original_parent_native_pin_matching_failed_root"
    # Prelude is only a latest-value capture. It is historical evidence only
    # when it predates this admission, never just because its Conversation matches.
    capture = conn.execute("SELECT * FROM secretary_context_preludes WHERE conversation_ref=? AND captured_at<=?",
                           (ref, admitted_at)).fetchone()
    if capture is not None:
        tools = decoded(capture["tool_schemas_json"])
        if isinstance(tools, list):
            return tools, "existing_preadmission_prelude"
    schemas = data.get("callable_tool_schemas")
    if isinstance(schemas, list) and schemas and all(isinstance(schema, dict) and schema.get("name") for schema in schemas):
        return [{"type": "function", "function": copy.deepcopy(schema)} for schema in schemas], "original_control_callable_schemas_parent_array_unavailable"
    raise NotingRecoveryError("Missing failed child/original parent tool pin, pre-admission prelude and original callable_tool_schemas")


def _base_snapshot(db, conn, ref, admitted_at, data):
    explicit = data.get("base_snapshot_id")
    if explicit:
        snapshot = db.notebook_snapshot_audit_conn(conn, explicit)
        if snapshot and snapshot["conversation_ref"] == ref:
            return explicit
    initial_ids = [entry["version_id"] for section in SECTIONS for entry in data["working_notebook"].get(section, [])]
    for row in conn.execute("SELECT snapshot_id,payload_json FROM secretary_notebook_snapshots "
                            "WHERE conversation_ref=? AND created_at<=? ORDER BY created_at DESC,rowid DESC", (ref, admitted_at)):
        if decoded(row["payload_json"]) == initial_ids:
            return row["snapshot_id"]
    return None  # Complete reconstructed work does not require a surviving base pointer.


def _find_admission(db, conn, ref, failed, messages, data):
    parent_id = failed.get("parent_session_id")
    if not parent_id or db.resolve_conversation_ref_conn(conn, parent_id, read_only=True) != ref:
        raise NotingRecoveryError("Failed child parent lineage is not bound to the requested Conversation")
    registration = conn.execute("SELECT a.* FROM secretary_noting_children c "
                                "JOIN secretary_noting_admissions a USING(admission_id) "
                                "WHERE c.child_session_id=? AND a.conversation_ref=?", (failed["id"], ref)).fetchone()
    if registration is not None:
        return dict(registration)
    audit = decoded(failed.get("model_config"), {}).get("_noting_recovery", {})
    admission = db.noting_admission_conn(conn, audit.get("admission_id"))
    if admission and admission["conversation_ref"] == ref:
        return admission
    # Older recovery tools rebound the single child registry slot. Locate its
    # surviving admission from the original child/control rather than erasing it.
    candidates = [dict(row) for row in conn.execute(
        "SELECT * FROM secretary_noting_admissions WHERE conversation_ref=? AND admitted_at<=? ORDER BY admitted_at DESC,admission_id DESC",
        (ref, failed["started_at"]))]
    from hermes_time import format_timestamp
    content = messages[0].get("content", "") if messages else ""
    stamp = re.search(r"<timestamp>([^<]+)</timestamp>", content) if isinstance(content, str) else None
    if stamp:
        candidates = [row for row in candidates if format_timestamp(row["admitted_at"]) == stamp[1]]
    through_time = (data.get("evidence_coverage") or {}).get("through_time")
    through_role = (data.get("evidence_coverage") or {}).get("through_role")
    if through_time:
        sources = db._foreground_source_rows_conn(conn, ref)
        candidates = [admission for admission in candidates if any(
            row["message_uid"] == admission["anchor_message_uid"]
            and format_timestamp(row["timestamp"]) == through_time
            and (not through_role or row["role"] == through_role) for row in sources)]
    if not candidates:
        raise NotingRecoveryError("Missing original admission matching failed child lineage/control time and coverage")
    return candidates[0]


def reconstruct_noting(db, conversation_ref, failed_child_session_id):
    failed = db.get_session(failed_child_session_id)
    if failed is None:
        raise NotingRecoveryError("Missing failed child Session")
    from secretary.noting_child import active_noting_task
    if active_noting_task(failed_child_session_id, db=db) is not None:
        raise NotingRecoveryError("The requested child still owns an active native Noting task")
    with db._read_ctx() as conn:
        rows = conn.execute("SELECT * FROM messages WHERE session_id=? ORDER BY id", (failed_child_session_id,)).fetchall()
        messages = db._rows_to_conversation(rows, session_id=failed_child_session_id,
                                            include_ancestors=False, repair_alternation=False)
        data = _control_data(messages)
        if data.get("conversation_ref") != conversation_ref:
            raise NotingRecoveryError("Failed child control Conversation differs from the requested Conversation")
        admission = _find_admission(db, conn, conversation_ref, failed, messages, data)
        parent_rows = _parent_rows(db, conn, conversation_ref, admission, rows)
        prefix = db._rows_to_conversation(parent_rows, session_id=failed["parent_session_id"],
                                          include_ancestors=False, repair_alternation=False, include_summary_markers=True)
        root = failed.get("system_prompt")
        if not isinstance(root, str):
            parent = db.get_session(failed.get("parent_session_id")) or {}
            root = parent.get("system_prompt")
        if not isinstance(root, str):
            raise NotingRecoveryError("Missing failed child and original parent root system prompt")
        tools, tool_source = _tools(db, conn, failed, conversation_ref, admission["admitted_at"], data, root)
        working = _working_state(conn, conversation_ref, messages, data["working_notebook"])
        base = _base_snapshot(db, conn, conversation_ref, admission["admitted_at"], data)
    suffix = copy.deepcopy(messages)
    for message in suffix:
        # The new durable child owns its replay suffix; original rows stay intact.
        for key in list(message):
            if key.startswith("_") or key in {"message_uid", "tool_call_uids", "tool_call_uid"}:
                message.pop(key, None)
    return RecoveredNoting(admission, failed, prefix, suffix, root, tools, working,
                           base,
                           {"parent": "admitted_compaction_interval_and_native_transcript_generations",
                            "root": "failed_child.system_prompt" if failed.get("system_prompt") is not None else "original_parent.system_prompt",
                            "tools": tool_source, "notebook": "initial_control_and_successful_immutable_version_receipts"})
