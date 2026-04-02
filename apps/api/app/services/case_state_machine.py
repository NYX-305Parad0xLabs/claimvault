from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from app.models.claim import CaseStatus


class InvalidCaseTransition(Exception):
    """Raised when an illegal status change is requested."""

    def __init__(self, current: CaseStatus, target: CaseStatus) -> None:
        allowed = CaseStateMachine.ALLOWED_TRANSITIONS.get(current, set())
        allowed_list = ", ".join(sorted(status.value for status in allowed)) or "none"
        message = (
            f"cannot transition from {current.value} to {target.value}; "
            f"allowed: {allowed_list}"
        )
        super().__init__(message)


@dataclass(frozen=True)
class CaseStateMachine:
    """Encapsulates the allowed lifecycle transitions for cases."""

    ALLOWED_TRANSITIONS: ClassVar[dict[CaseStatus, set[CaseStatus]]] = {
        CaseStatus.DRAFT: {CaseStatus.COLLECTING_EVIDENCE},
        CaseStatus.COLLECTING_EVIDENCE: {
            CaseStatus.NEEDS_USER_INPUT,
            CaseStatus.READY_FOR_EXPORT,
        },
        CaseStatus.NEEDS_USER_INPUT: {CaseStatus.COLLECTING_EVIDENCE},
        CaseStatus.READY_FOR_EXPORT: {CaseStatus.EXPORTED},
        CaseStatus.EXPORTED: {CaseStatus.SUBMITTED},
        CaseStatus.SUBMITTED: {CaseStatus.RESOLVED, CaseStatus.CLOSED},
        CaseStatus.RESOLVED: {CaseStatus.CLOSED},
    }

    def validate(self, current: CaseStatus, target: CaseStatus) -> None:
        if target not in self.ALLOWED_TRANSITIONS.get(current, set()):
            raise InvalidCaseTransition(current, target)
