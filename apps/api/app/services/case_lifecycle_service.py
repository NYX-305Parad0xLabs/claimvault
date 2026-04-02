from __future__ import annotations

from datetime import datetime
import logging

from sqlmodel import Session

from app.models.claim import ActorType, AuditEvent, Case, CaseStatus, TimelineEvent
from app.services.case_state_machine import CaseStateMachine


class CaseLifecycleService:
    """Encapsulates lifecycle enforcement, timeline tracking, and audit logging for case transitions."""

    ALLOWED_TRANSITIONS = CaseStateMachine.ALLOWED_TRANSITIONS

    def __init__(
        self,
        logger: logging.Logger,
        state_machine: CaseStateMachine | None = None,
    ) -> None:
        self._logger = logger
        self._state_machine = state_machine or CaseStateMachine()

    def transition(
        self,
        session: Session,
        case: Case,
        target_status: CaseStatus,
        *,
        actor_id: int | None,
        reason: str | None = None,
    ) -> None:
        current = case.status
        self._state_machine.validate(current, target_status)
        case.status = target_status
        case.updated_at = datetime.utcnow()
        metadata = self._build_metadata(current, target_status, reason)
        body = self._build_body(current, target_status, reason)

        session.add(
            TimelineEvent(
                case_id=case.id,
                event_type="status_transition",
                actor_type=ActorType.USER,
                actor_id=actor_id,
                body=body,
                metadata_json=metadata,
            )
        )
        session.add(
            AuditEvent(
                entity_type="case",
                entity_id=case.id,
                action="transition",
                actor_type=ActorType.USER,
                actor_id=actor_id,
                metadata_json=metadata,
            )
        )
        self._logger.info(
            "case transition recorded",
            extra={"case_id": case.id, "from": current.value, "to": target_status.value},
        )

    @staticmethod
    def _build_body(current: CaseStatus, target: CaseStatus, reason: str | None) -> str:
        base = f"Status changed from {current.value} to {target.value}"
        return f"{base} (reason: {reason})" if reason else base

    @staticmethod
    def _build_metadata(current: CaseStatus, target: CaseStatus, reason: str | None) -> dict[str, str | CaseStatus]:
        payload = {"from": current.value, "to": target.value}
        if reason:
            payload["reason"] = reason
        return payload
