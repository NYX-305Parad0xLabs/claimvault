from __future__ import annotations

import logging
from typing import Callable

from sqlmodel import Session, select

from app.models.claim import Case
from app.schemas.case import CaseCreate, CaseRead


class CaseService:
    def __init__(self, session_factory: Callable[[], Session], logger: logging.Logger) -> None:
        self._session_factory = session_factory
        self._logger = logger

    def list_cases(self, workspace_id: int) -> list[CaseRead]:
        with self._session_factory() as session:
            statement = select(Case).where(Case.workspace_id == workspace_id).order_by(Case.created_at.desc())
            cases = session.exec(statement).all()
            return [CaseRead.model_validate(case) for case in cases]

    def create_case(self, payload: CaseCreate, workspace_id: int) -> CaseRead:
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
            session.commit()
            session.refresh(case)
            self._logger.info("case created", extra={"case_id": case.id})
            return CaseRead.model_validate(case)
