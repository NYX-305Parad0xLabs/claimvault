from __future__ import annotations

from datetime import datetime
import logging
from typing import Callable

from fastapi import status
from sqlmodel import Session, select

from app.models.claim import ActorType, AuditEvent, Case, CaseStatus, ClaimType, CounterpartyProfile, TimelineEvent
from app.schemas.case import CaseCreate, CaseRead, CaseTransitionRequest, CaseUpdate
from app.services.case_state_machine import CaseStateMachine, InvalidCaseTransition


class CaseServiceError(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.detail = detail
        self.status_code = status_code


class CaseService:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        logger: logging.Logger,
        state_machine: CaseStateMachine | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._logger = logger
        self._state_machine = state_machine or CaseStateMachine()

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
            return [self._build_case_read(case) for case in cases]

    def get_case(self, workspace_id: int, case_id: int) -> CaseRead:
        with self._session_factory() as session:
            case = session.get(Case, case_id)
            if not case or case.workspace_id != workspace_id:
                raise CaseServiceError("case not found", status.HTTP_404_NOT_FOUND)
            profile = self._maybe_load_counterparty_profile(
                session, workspace_id, case.counterparty_profile_id
            )
            return self._build_case_read(case, profile)

    def create_case(
        self,
        payload: CaseCreate,
        workspace_id: int,
        *,
        actor_id: int | None = None,
    ) -> CaseRead:
        with self._session_factory() as session:
            profile = None
            profile_id = payload.counterparty_profile_id
            if profile_id is not None:
                profile = self._validate_counterparty_profile(
                    session, workspace_id, profile_id
                )
            counterparty_name = payload.counterparty_name or (profile.name if profile else None)
            case = Case(
                workspace_id=workspace_id,
                title=payload.title,
                claim_type=payload.claim_type,
                counterparty_name=counterparty_name,
                counterparty_profile_id=profile_id,
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
            return self._build_case_read(case, profile)

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
            if "counterparty_profile_id" in updates:
                profile_id = updates["counterparty_profile_id"]
                if profile_id is not None:
                    self._validate_counterparty_profile(session, workspace_id, profile_id)
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
            profile = self._maybe_load_counterparty_profile(
                session, workspace_id, case.counterparty_profile_id
            )
            return self._build_case_read(case, profile)

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
            try:
                self._state_machine.validate(current_status, request.target_status)
            except InvalidCaseTransition as exc:
                raise CaseServiceError(str(exc))

            case.status = request.target_status
            case.updated_at = datetime.utcnow()
            session.add(
                TimelineEvent(
                    case_id=case.id,
                    event_type="status_transition",
                    actor_type=ActorType.USER,
                    actor_id=actor_id,
                    body=self._build_transition_body(
                        current_status, request.target_status, request.reason
                    ),
                    metadata_json=self._build_transition_metadata(
                        current_status, request.target_status, request.reason
                    ),
                )
            )
            session.add(
                AuditEvent(
                    entity_type="case",
                    entity_id=case.id,
                    action="transition",
                    actor_type=ActorType.USER,
                    actor_id=actor_id,
                    metadata_json=self._build_transition_metadata(
                        current_status, request.target_status, request.reason
                    ),
                )
            )
            session.commit()
            session.refresh(case)
            profile = self._maybe_load_counterparty_profile(
                session, workspace_id, case.counterparty_profile_id
            )
            return self._build_case_read(case, profile)

    def _build_case_read(
        self,
        case: Case,
        profile: CounterpartyProfile | None = None,
    ) -> CaseRead:
        payload = case.model_dump()
        payload["counterparty_profile"] = profile.model_dump() if profile else None
        return CaseRead.model_validate(payload)

    def _maybe_load_counterparty_profile(
        self,
        session: Session,
        workspace_id: int,
        profile_id: int | None,
    ) -> CounterpartyProfile | None:
        if profile_id is None:
            return None
        return self._validate_counterparty_profile(session, workspace_id, profile_id)

    def _validate_counterparty_profile(
        self,
        session: Session,
        workspace_id: int,
        profile_id: int,
    ) -> CounterpartyProfile:
        profile = session.get(CounterpartyProfile, profile_id)
        if not profile or profile.workspace_id != workspace_id:
            raise CaseServiceError("counterparty profile not found", status.HTTP_404_NOT_FOUND)
        return profile

    @staticmethod
    def _build_transition_body(
        current: CaseStatus, target: CaseStatus, reason: str | None
    ) -> str:
        base = f"Status changed from {current.value} to {target.value}"
        return f"{base} (reason: {reason})" if reason else base

    @staticmethod
    def _build_transition_metadata(
        current: CaseStatus, target: CaseStatus, reason: str | None
    ) -> dict[str, str | CaseStatus]:
        metadata = {"from": current.value, "to": target.value}
        if reason:
            metadata["reason"] = reason
        return metadata
