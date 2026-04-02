from __future__ import annotations

from datetime import datetime
import logging
from typing import Callable

from fastapi import status
from sqlmodel import Session, select

from app.models.claim import (
    ActorType,
    AuditEvent,
    Case,
    CaseStatus,
    ClaimType,
    TimelineEvent,
)
from app.schemas.case import CaseCreate, CaseRead, CaseTransitionRequest, CaseUpdate

TRANSITION_RULES = {
    CaseStatus.DRAFT: {CaseStatus.COLLECTING_EVIDENCE},
    CaseStatus.COLLECTING_EVIDENCE: {CaseStatus.READY_TO_EXPORT},
    CaseStatus.READY_TO_EXPORT: {CaseStatus.SUBMITTED},
    CaseStatus.SUBMITTED: {CaseStatus.RESOLVED, CaseStatus.CLOSED},
    CaseStatus.RESOLVED: {CaseStatus.CLOSED},
}


class CaseServiceError(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.detail = detail
        self.status_code = status_code


class CaseService:
    def __init__(self, session_factory: Callable[[], Session], logger: logging.Logger) -> None:
        self._session_factory = session_factory
        self._logger = logger

    def list_cases(
        self,
        workspace_id: int,
        *,
        limit: int = 25,
        offset: int = 0,
        status: CaseStatus | None = None,
        claim_type: ClaimType | None = None,
        merchant_name: str | None = None,
    ) -> list[CaseRead]:
        with self._session_factory() as session:
            statement = select(Case).where(Case.workspace_id == workspace_id)
            if status:
                statement = statement.where(Case.status == status)
            if claim_type:
                statement = statement.where(Case.claim_type == claim_type)
            if merchant_name:
                statement = statement.where(Case.merchant_name == merchant_name)
            cases = (
                session.exec(
                    statement.order_by(Case.created_at.desc())
                    .limit(limit)
                    .offset(offset)
                )
            ).all()
            return [CaseRead.model_validate(case) for case in cases]

    def get_case(self, workspace_id: int, case_id: int) -> CaseRead:
        with self._session_factory() as session:
            case = session.get(Case, case_id)
            if not case or case.workspace_id != workspace_id:
                raise CaseServiceError("case not found", status.HTTP_404_NOT_FOUND)
            return CaseRead.model_validate(case)

    def create_case(
        self,
        payload: CaseCreate,
        workspace_id: int,
        *,
        actor_id: int | None = None,
    ) -> CaseRead:
        with self._session_factory() as session:
            case = Case(
                workspace_id=workspace_id,
                title=payload.title,
                claim_type=payload.claim_type,
                counterparty_name=payload.counterparty_name,
                merchant_name=payload.merchant_name,
                order_reference=payload.order_reference,
                amount_currency=payload.amount_currency,
                amount_value=payload.amount_value,
                purchase_date=payload.purchase_date,
                incident_date=payload.incident_date,
                due_date=payload.due_date,
                summary=payload.summary,
            )
            session.add(case)
            session.flush()
            metadata = payload.model_dump(exclude_none=True)
            session.add(
                AuditEvent(
                    entity_type="case",
                    entity_id=case.id,
                    action="create",
                    actor_type=ActorType.USER if actor_id else ActorType.SYSTEM,
                    actor_id=actor_id,
                    metadata_json={"fields": list(metadata.keys())},
                )
            )
            session.commit()
            session.refresh(case)
            self._logger.info("case created", extra={"case_id": case.id})
            return CaseRead.model_validate(case)

    def update_case(
        self,
        workspace_id: int,
        case_id: int,
        payload: CaseUpdate,
        *,
        actor_id: int | None = None,
    ) -> CaseRead:
        with self._session_factory() as session:
            case = session.get(Case, case_id)
            if not case or case.workspace_id != workspace_id:
                raise CaseServiceError("case not found", status.HTTP_404_NOT_FOUND)

            updates = payload.model_dump(exclude_none=True)
            for attr, value in updates.items():
                setattr(case, attr, value)
            case.updated_at = datetime.utcnow()
            if updates:
                session.add(
                    AuditEvent(
                        entity_type="case",
                        entity_id=case.id,
                        action="update",
                        actor_type=ActorType.USER if actor_id else ActorType.SYSTEM,
                        actor_id=actor_id,
                        metadata_json={"updated_fields": list(updates.keys())},
                    )
                )
            session.commit()
            session.refresh(case)
            return CaseRead.model_validate(case)

    def transition_case(
        self,
        workspace_id: int,
        case_id: int,
        request: CaseTransitionRequest,
        actor_id: int,
    ) -> CaseRead:
        with self._session_factory() as session:
            case = session.get(Case, case_id)
            if not case or case.workspace_id != workspace_id:
                raise CaseServiceError("case not found", status.HTTP_404_NOT_FOUND)

            current_status = case.status
            allowed = TRANSITION_RULES.get(current_status, set())
            if request.target_status not in allowed:
                raise CaseServiceError(
                    f"cannot transition from {current_status} to {request.target_status}"
                )

            case.status = request.target_status
            case.updated_at = datetime.utcnow()
            session.add(
                TimelineEvent(
                    case_id=case.id,
                    event_type="status_transition",
                    actor_type=ActorType.USER,
                    actor_id=actor_id,
                    body=f"Status changed from {current_status} to {request.target_status}",
                    metadata_json={"from": current_status, "to": request.target_status},
                )
            )
            session.add(
                AuditEvent(
                    entity_type="case",
                    entity_id=case.id,
                    action="transition",
                    actor_type=ActorType.USER,
                    actor_id=actor_id,
                    metadata_json={"from": current_status, "to": request.target_status},
                )
            )
            session.commit()
            session.refresh(case)
            return CaseRead.model_validate(case)
