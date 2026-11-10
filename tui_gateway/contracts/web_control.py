"""Opt-in Web input custody over the existing native Session and Pending owners."""
from typing import Literal

from pydantic import Field

from .base import Payload, Result
from .common import SessionParams
from .registry import event, method


class InputReceipt(Result):
    operation_id: str
    accepted: bool
    state: Literal["submitted", "waiting", "pending", "consumed", "withdrawn", "cancelled", "failed", "interrupted", "unknown"]
    destination: Literal["turn", "steer", "startup", "followup", "maintenance"] | None = None
    turn_id: str | None = None
    pending_id: str | None = None
    message_uid: str | None = None
    reason: str | None = None


class InputOperationParams(SessionParams):
    operation_id: str = Field(min_length=1, max_length=128, pattern=r"\S")


class InputOperationResult(Result):
    receipt: InputReceipt
    input: "ReceivedInput | None" = None


class InputWithdrawResult(Result):
    outcome: Literal["withdrawn", "too_late", "not_found", "unknown"]
    receipt: InputReceipt


class ReceivedInput(Result):
    text: str
    image_paths: list[str] = Field(default_factory=list)


class WaitingInput(Result):
    receipt: InputReceipt
    text: str
    image_paths: list[str] = Field(default_factory=list)


class InputStateResult(Result):
    phase: Literal["idle", "starting", "running", "settling", "maintenance", "gateway", "unavailable"]
    running: bool
    turn_id: str | None = None
    can_submit: bool
    can_stop: bool
    waiting: list[WaitingInput]
    unresolved: list[WaitingInput] = Field(default_factory=list)
    reason: str | None = None


class InputChangedPayload(Payload):
    operation_id: str | None = None


method("prompt.operation_status", params=InputOperationParams, result=InputOperationResult,
       doc="Query an opt-in input's persisted receipt without replaying the write.")
method("prompt.operation_withdraw", params=InputOperationParams, result=InputWithdrawResult,
       doc="Withdraw the exact waiting input, or delegate to its native Pending owner.")
method("session.input_state", params=SessionParams, result=InputStateResult,
       doc="Read this runtime's authoritative input phase and waiting native queue.")
event("session.input_changed", InputChangedPayload,
      doc="Input custody changed; locally refetch the same runtime's input state or receipt.")
