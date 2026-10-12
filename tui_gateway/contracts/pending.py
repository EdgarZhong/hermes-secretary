"""Additive occurrence-based native steer and atomic interrupt contracts."""
from pydantic import Field

from .base import Params, Payload, Result
from .common import SessionParams
from .registry import event, method
from typing import Literal


class PendingSessionParams(SessionParams):
    session_id: str = Field(min_length=1)


class PendingTurnParams(PendingSessionParams):
    turn_id: str = Field(min_length=1)


class PendingOperationParams(PendingTurnParams):
    operation_id: str = Field(min_length=1, max_length=128)


class SteerPendingParams(PendingOperationParams):
    text: str = Field(min_length=1)


class SteerPendingResult(Result):
    accepted: bool
    state: Literal["pending", "consumed", "withdrawn", "rejected", "inactive", "compressing",
                   "terminal_conflict", "unknown_turn", "capacity"]
    pending_id: str | None
    turn_id: str | None
    reason: str | None


class FollowupReceipt(Result):
    session_id: str
    stored_session_id: str
    turn_id: str | None


class InterruptPendingResult(Result):
    operation_id: str
    turn_id: str
    state: Literal["stopping", "dispatching", "followup_accepted", "nothing_pending", "not_active",
                   "already_transitioned", "rejected", "unknown"]
    selected_ids: list[str]
    followup: FollowupReceipt | None
    reason: str | None


class PendingOccurrence(Result):
    pending_id: str
    text: str
    order: int
    state: Literal["pending", "handoff_reserved"]
    withdrawable: bool


class PendingReceipt(Result):
    pending_id: str
    state: Literal["consumed", "withdrawn", "rejected"]
    message_uid: str | None
    reason: str | None


class SteerPendingSnapshotResult(Result):
    turn_id: str | None
    active: bool
    pending: list[PendingOccurrence]
    receipts: list[PendingReceipt]
    operation: InterruptPendingResult | None


class SteerWithdrawParams(PendingTurnParams):
    pending_id: str = Field(min_length=1)


class SteerWithdrawResult(Result):
    state: Literal["withdrawn", "already_withdrawn", "already_consumed", "handoff_reserved", "rejected", "unknown"]
    turn_id: str
    pending_id: str
    text: str | None
    message_uid: str | None
    reason: str | None


class SteerPendingChangedPayload(Payload):
    turn_id: str | None


class SteerConsumedPayload(Payload):
    turn_id: str
    pending_ids: list[str]
    message_uid: str | None


method("session.steer_pending", params=SteerPendingParams, result=SteerPendingResult,
       doc="Enqueue one occurrence in the active native steer buffer with an idempotent receipt.")
method("session.steer_pending_snapshot", params=PendingSessionParams, result=SteerPendingSnapshotResult,
       doc="Read exact pending/terminal native steer receipts, never inferred correction offsets.")
method("session.steer_withdraw", params=SteerWithdrawParams, result=SteerWithdrawResult,
       doc="Withdraw exactly one occurrence until its true native insertion or handoff owns it.")
method("session.interrupt_pending", params=PendingOperationParams, result=InterruptPendingResult,
       doc="Atomically reserve remaining steer occurrences, stop, and admit one pending-only followup.")
method("session.interrupt_pending_status", params=PendingOperationParams, result=InterruptPendingResult,
       doc="Query an interrupt handoff without resubmitting a prompt after uncertain acceptance.")
event("steer.pending_changed", SteerPendingChangedPayload,
      doc="Native steer inventory or operation changed; refetch the owning runtime's snapshot/status.")
event("steer.consumed", SteerConsumedPayload,
      doc="Exact occurrence ids entered one real user row or one accepted native followup prompt.")
