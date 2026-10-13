"""Occurrence receipts at the native steer slot; dormant for unchanged clients.

The agent's existing _pending_steer_lock owns every mutation. A claimed str
batch remains withdrawable until the real append takes that same lock.
"""
from __future__ import annotations

from collections import OrderedDict
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any
from uuid import uuid4

WEB_SUBMISSION_LIMIT = 256
INTERRUPT_OPERATION_LIMIT = 64
RETIRED_EPOCH_LIMIT = 8


@dataclass
class Occurrence:
    pending_id: str
    text: str
    order: int
    state: str = "pending"
    claim: str | None = None
    message_uid: str | None = None
    reason: str | None = None
    digest: str = ""
    operation_id: str | None = None


@dataclass
class Epoch:
    turn_id: str
    active: bool = True
    entries: OrderedDict[str, Occurrence] = field(default_factory=OrderedDict)
    submissions: dict[str, str] = field(default_factory=dict)
    operations: dict[str, dict] = field(default_factory=dict)


class SteerBatch(str):
    """Text-compatible claim, never authoritative text after withdrawal."""
    def __new__(cls, text, owner, turn_id, ids, claim):
        value = super().__new__(cls, text)
        value.owner = owner
        value.turn_id = turn_id
        value.ids = tuple(ids)
        value.claim = claim
        return value


class PendingSteerBuffer:
    def __init__(self, turn_id: str, legacy: str | None = None):
        self.epochs: OrderedDict[str, Epoch] = OrderedDict()
        self.turn_id = turn_id
        self.sequence = 0
        self.handoff: dict | None = None
        self.start(turn_id)
        if legacy:
            self.enqueue(legacy)

    def __bool__(self):
        return any(e.state in {"pending", "claimed"} for e in self.current.entries.values())

    @property
    def current(self):
        return self.epochs[self.turn_id]

    def start(self, turn_id):
        previous = self.epochs.get(self.turn_id)
        self.turn_id = turn_id
        self.epochs.setdefault(turn_id, Epoch(turn_id))
        if previous is not None and previous.turn_id != turn_id and not previous.active:
            # A legacy steer accepted after the Web finalizer edge retains its
            # original next-turn behavior; no new Web acceptance is allowed there.
            carry = [e for e in previous.entries.values() if e.state == "pending" and e.operation_id is None]
            for entry in carry:
                self.current.entries[entry.pending_id] = previous.entries.pop(entry.pending_id)
        self.epochs.move_to_end(turn_id)
        while len(self.epochs) > RETIRED_EPOCH_LIMIT + 1:
            self.epochs.popitem(last=False)
        if self.handoff and self.handoff["state"] == "dispatching":
            self.handoff["followup"]["turn_id"] = turn_id
            self._complete_selected(self.handoff)
            # A native worker at its real epoch start has already crossed prompt admission.
            self.handoff["state"] = "followup_accepted"

    def enqueue(self, text, operation_id=None):
        self.sequence += 1
        entry = Occurrence(uuid4().hex, text, self.sequence,
                           digest=sha256(text.encode()).hexdigest(), operation_id=operation_id)
        self.current.entries[entry.pending_id] = entry
        if operation_id is not None:
            self.current.submissions[operation_id] = entry.pending_id
        return entry

    def submit(self, turn_id, operation_id, text):
        epoch = self.epochs.get(turn_id)
        if epoch is not None and operation_id in epoch.submissions:
            entry = epoch.entries[epoch.submissions[operation_id]]
            if entry.digest != sha256(text.encode()).hexdigest():
                return submit_result(False, "rejected", turn_id, reason="operation_conflict")
            return submit_result(True, "pending" if entry.state == "reserved" else wire_state(entry),
                                 turn_id, entry.pending_id, entry.reason)
        if epoch is not self.current:
            return submit_result(False, "unknown_turn", self.turn_id)
        if not epoch.active:
            return submit_result(False, "terminal_conflict", turn_id)
        if len(epoch.submissions) >= WEB_SUBMISSION_LIMIT:
            return submit_result(False, "capacity", turn_id, reason="submission_capacity")
        entry = self.enqueue(text, operation_id)
        return submit_result(True, "pending", turn_id, entry.pending_id)

    def take(self):
        ids = [e.pending_id for e in self.current.entries.values() if e.state == "pending"]
        if not ids:
            return None
        claim = uuid4().hex
        for pending_id in ids:
            self.current.entries[pending_id].state = "claimed"
            self.current.entries[pending_id].claim = claim
        return SteerBatch("\n".join(self.current.entries[i].text for i in ids),
                          self, self.turn_id, ids, claim)

    def claimed_entries(self, batch):
        epoch = self.epochs.get(batch.turn_id)
        if epoch is None:
            return []
        return [epoch.entries[i] for i in batch.ids if i in epoch.entries
                and epoch.entries[i].state == "claimed" and epoch.entries[i].claim == batch.claim]

    def requeue(self, batch):
        for entry in self.claimed_entries(batch):
            entry.state, entry.claim = "pending", None

    def withdraw(self, turn_id, pending_id):
        epoch = self.epochs.get(turn_id)
        entry = epoch.entries.get(pending_id) if epoch else None
        result = {"state": "unknown", "turn_id": turn_id, "pending_id": pending_id,
                  "text": None, "message_uid": None, "reason": None}
        if entry is None:
            return result
        result.update(message_uid=entry.message_uid, reason=entry.reason)
        if entry.state in {"pending", "claimed"}:
            result.update(state="withdrawn", text=entry.text)
            entry.state, entry.text, entry.claim = "withdrawn", "", None
        else:
            result["state"] = {"consumed": "already_consumed", "withdrawn": "already_withdrawn",
                               "reserved": "handoff_reserved"}.get(entry.state, entry.state)
        return result

    def reserve(self, turn_id, operation_id):
        epoch = self.epochs.get(turn_id)
        if epoch is not None and operation_id in epoch.operations:
            return epoch.operations[operation_id], False
        if epoch is not self.current:
            return operation_result(operation_id, turn_id, "not_active"), False
        if len(epoch.operations) >= INTERRUPT_OPERATION_LIMIT:
            return operation_result(operation_id, turn_id, "rejected", reason="operation_capacity"), False
        if self.handoff and self.handoff["state"] in {"stopping", "reserved", "dispatching"}:
            op = operation_result(operation_id, turn_id, "already_transitioned")
        elif not epoch.active:
            return operation_result(operation_id, turn_id, "not_active"), False
        else:
            ids = [e.pending_id for e in epoch.entries.values() if e.state in {"pending", "claimed"}]
            op = operation_result(operation_id, turn_id, "stopping" if ids else "nothing_pending", ids)
            if ids:
                for pending_id in ids:
                    epoch.entries[pending_id].state = "reserved"
                epoch.active = False
                self.handoff = op
        epoch.operations[operation_id] = op
        return op, op["state"] == "stopping"

    def finish(self):
        epoch = self.current
        epoch.active = False
        if self.handoff and self.handoff["turn_id"] == epoch.turn_id:
            return None
        ids = [e.pending_id for e in epoch.entries.values() if e.state in {"pending", "claimed"}]
        if not ids:
            return None
        op = operation_result("native-" + uuid4().hex, epoch.turn_id, "reserved", ids)
        epoch.operations[op["operation_id"]] = op
        self.handoff = op
        for pending_id in ids:
            epoch.entries[pending_id].state = "reserved"
        return SteerBatch("\n".join(epoch.entries[i].text for i in ids), self, epoch.turn_id, ids, None)

    def reject(self, reason, *, include_reserved=False):
        for epoch in self.epochs.values():
            epoch.active = False
            for entry in epoch.entries.values():
                if entry.state in {"pending", "claimed"} or include_reserved and entry.state == "reserved":
                    entry.state, entry.text, entry.reason = "rejected", "", reason
        if include_reserved and self.handoff and self.handoff["state"] in {"stopping", "reserved", "dispatching"}:
            self.handoff.update(state="rejected", reason=reason)

    def _complete_selected(self, op):
        epoch = self.epochs.get(op["turn_id"])
        if epoch:
            for pending_id in op["selected_ids"]:
                entry = epoch.entries.get(pending_id)
                if entry and entry.state == "reserved":
                    entry.state, entry.text = "consumed", ""

    def snapshot(self):
        epoch = self.current
        pending, receipts = [], []
        for entry in epoch.entries.values():
            if entry.state in {"pending", "claimed", "reserved"}:
                pending.append({"pending_id": entry.pending_id, "text": entry.text, "order": entry.order,
                                "state": wire_state(entry), "withdrawable": entry.state != "reserved"})
            else:
                receipts.append({"pending_id": entry.pending_id, "state": entry.state,
                                 "message_uid": entry.message_uid, "reason": entry.reason})
        return {"turn_id": epoch.turn_id, "active": epoch.active, "pending": pending,
                "receipts": receipts, "operation": public_operation(self.handoff)}


def wire_state(entry):
    return {"claimed": "pending", "reserved": "handoff_reserved"}.get(entry.state, entry.state)


def submit_result(accepted, state, turn_id=None, pending_id=None, reason=None):
    return {"accepted": accepted, "state": state, "pending_id": pending_id,
            "turn_id": turn_id, "reason": reason}


def operation_result(operation_id, turn_id, state, ids=(), reason=None):
    return {"operation_id": operation_id, "turn_id": turn_id, "state": state,
            "selected_ids": list(ids), "followup": None, "reason": reason}


def public_operation(op):
    if op is None:
        return None
    result = {k: op[k] for k in ("operation_id", "turn_id", "state", "selected_ids", "followup", "reason")}
    result["selected_ids"] = list(result["selected_ids"])
    if result["followup"] is not None:
        result["followup"] = dict(result["followup"])
    if result["state"] == "reserved":
        result["state"] = "stopping"
    return result


def buffer_for(agent):
    value = vars(agent).get("_pending_steer") if agent is not None else None
    return value if isinstance(value, PendingSteerBuffer) else None


def enable_locked(agent):
    owner = buffer_for(agent)
    if owner is None:
        turn_id = vars(agent).get("_pending_steer_native_active_turn")
        if not turn_id:
            return None
        owner = PendingSteerBuffer(turn_id, vars(agent).get("_pending_steer"))
        agent._pending_steer = owner
    return owner


def notify(agent, event="steer.pending_changed", payload=None):
    callback = vars(agent).get("_pending_steer_notify")
    if callable(callback):
        try:
            callback(event, payload or {"turn_id": vars(agent).get("_current_turn_id")})
        except Exception:  # health: allow BLE001 -- transport delivery cannot reverse an accepted owner transition
            # A dead transport cannot reverse an authoritative queue transition.
            import logging
            logging.getLogger(__name__).debug("pending steer event delivery failed", exc_info=True)


def note_native_turn_started(agent, turn_id):
    agent._pending_steer_native_active_turn = turn_id
    owner = buffer_for(agent)
    if owner is not None:
        with agent._pending_steer_lock:
            owner.start(turn_id)


def finish_native_turn(agent, *, failed=False):
    agent._pending_steer_native_active_turn = None
    owner = buffer_for(agent)
    if owner is None:
        return agent._drain_pending_steer()
    with agent._pending_steer_lock:
        if failed:
            owner.reject("turn_failed", include_reserved=True)
            batch = None
        else:
            batch = owner.finish()
    notify(agent)
    return batch


def reject_native_pending(agent, reason, *, include_reserved=False):
    owner = buffer_for(agent)
    if owner is not None:
        with agent._pending_steer_lock:
            owner.reject(reason, include_reserved=include_reserved)
        notify(agent)


def native_source_message(message):
    """Observer-only identity/address, with no transcript or provider payload bytes."""
    from agent.context_compressor import _DB_PERSISTED_MARKER
    from agent.message_metadata import message_uid_or_none
    result = {"message_uid": message_uid_or_none(message), "role": message.get("role", "unknown"),
              "has_content": bool(message.get("content")),
              "has_reasoning": bool(message.get("reasoning") or message.get("reasoning_content"))}
    row_id = message.get("_row_id")
    if message.get(_DB_PERSISTED_MARKER) and type(row_id) is int and row_id > 0:
        result["row_id"] = row_id
    for source, target in (("display_kind", "display_kind"), ("tool_call_id", "tool_call_id"),
                           ("_tool_call_uid", "tool_call_uid")):
        if isinstance(message.get(source), str) and message[source]:
            result[target] = message[source]
    if calls := message.get("tool_calls"):
        uids = message.get("_tool_call_uids") or {}
        result["tool_calls"] = [{"id": call["id"], **({"tool_call_uid": uids[call["id"]]}
                                if call["id"] in uids else {})}
                               for call in calls if isinstance(call, dict) and isinstance(call.get("id"), str)]
    return result


def native_source_suffix(messages, start):
    """Only the actual current user boundary's suffix; an unknown boundary has no invented prefix."""
    if (type(start) is not int or not 0 <= start < len(messages)
            or not isinstance(messages[start], dict) or messages[start].get("role") != "user"):
        return None
    return [native_source_message(message) for message in messages[start:] if isinstance(message, dict)]


def native_source_boundary(agent, messages, start, history, compression_count):
    """Facts anchored in the host's pre-turn snapshot; no relaxed completion assertion."""
    from agent.message_metadata import message_uid_or_none
    source = native_source_suffix(messages, start)
    if source is None:
        return None
    prefix_unchanged = start == len(history) and all(
        (before_id := native_source_message(before).get("row_id")) is not None
        and before_id == native_source_message(after).get("row_id")
        for before, after in zip(history, messages[:start]))
    return {"user_message_uid": message_uid_or_none(messages[start]),
            "after_message_uid": message_uid_or_none(messages[start - 1]) if start else None,
            "prefix_unchanged": prefix_unchanged,
            "compression_unchanged": type(compression_count) is int and compression_count == getattr(
                getattr(agent, "context_compressor", None), "compression_count", None),
            "all_rows_committed": len(source) == len(messages) - start
                and all(message.get("row_id") is not None for message in source)}


def native_insertion_projection(agent, messages, position):
    """Observe the insertion under its owner lock; observer failure cannot veto the insert."""
    try:
        predecessor = native_source_message(messages[position - 1]) if position else None
        projection = {"after_message_uid": predecessor["message_uid"] if predecessor else None,
                      "predecessor": predecessor}
        start = getattr(agent, "_persist_user_message_idx", None)
        prefix = messages[:position]
        if (source := native_source_suffix(prefix, start)) is not None:
            projection["source_messages"] = source
        observer = vars(agent).get("_pending_steer_source_boundary")
        boundary = observer(prefix, start) if callable(observer) else None
        if boundary is not None:
            projection["source_boundary"] = {**boundary, "insertion_at_tail": position == len(messages)}
        return projection
    except Exception:  # health: allow BLE001 -- optional observation must not change the native insertion
        import logging
        logging.getLogger(__name__).debug("pending source projection unavailable", exc_info=True)
        return {}


def append_claimed_batch(agent, messages, batch, *, index=None):
    """Insertion and occurrence disposition have one winner against withdraw."""
    from agent.message_metadata import stamp_message_uid
    from agent.prompt_builder import steer_user_row
    owner = batch.owner
    with agent._pending_steer_lock:
        entries = owner.claimed_entries(batch)
        if not entries:
            return False
        author_text = "\n".join(entry.text for entry in entries)
        row = steer_user_row(author_text)
        uid = stamp_message_uid(row)
        # list.insert normalizes out-of-range/negative indexes. Capture THAT native
        # position rather than assuming every call is a tail append.
        position = len(messages) if index is None else min(
            max(index if index >= 0 else len(messages) + index, 0), len(messages))
        projection = native_insertion_projection(agent, messages, position)
        if index is None:
            messages.append(row)
        else:
            messages.insert(index, row)
        payload = {"turn_id": batch.turn_id, "pending_ids": [entry.pending_id for entry in entries],
                   "message_uid": uid, "message": {**row, "display_content": author_text},
                   **projection}
        for entry in entries:
            entry.state, entry.text, entry.claim, entry.message_uid = "consumed", "", None, uid
    notify(agent, "steer.consumed", payload)
    notify(agent)
    return True


def requeue_if_owned(agent, text):
    lock = getattr(agent, "_pending_steer_lock", None)
    if lock is None:
        return False
    with lock:
        owner = text.owner if isinstance(text, SteerBatch) else buffer_for(agent)
        if owner is None:
            # Match the old locked-string requeue exactly. Keep detection and
            # mutation in this lock so opt-in cannot replace the slot between them.
            existing = agent._pending_steer
            agent._pending_steer = existing + "\n" + text if existing else text
        elif isinstance(text, SteerBatch):
            owner.requeue(text)
        else:
            # This legacy string was drained before opt-in enabled the owner.
            # Import it once at the head, ahead of arrivals accepted during that gap.
            order = min((entry.order for entry in owner.current.entries.values()), default=owner.sequence + 1) - 1
            entry = owner.enqueue(text)
            entry.order = order
            owner.current.entries.move_to_end(entry.pending_id, last=False)
    return True


def append_steer_row(agent, messages, text):
    if isinstance(text, SteerBatch):
        return append_claimed_batch(agent, messages, text)
    from agent.prompt_builder import steer_user_row
    messages.append(steer_user_row(text))
    return True
