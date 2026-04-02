from __future__ import annotations

import logging
from typing import Callable

from sqlmodel import Session, select

from app.models.claim import Claim, ClaimStatus
from app.schemas.claim import ClaimCreate, ClaimRead


class ClaimService:
    def __init__(self, session_factory: Callable[[], Session], logger: logging.Logger) -> None:
        self._session_factory = session_factory
        self._logger = logger

    def list_claims(self) -> list[ClaimRead]:
        with self._session_factory() as session:
            statement = select(Claim).order_by(Claim.created_at.desc())
            claims = session.exec(statement).all()
            return [ClaimRead.model_validate(claim) for claim in claims]

    def create_claim(self, payload: ClaimCreate) -> ClaimRead:
        with self._session_factory() as session:
            claim = Claim(
                subject=payload.subject,
                claim_type=payload.claim_type,
                created_by=payload.created_by,
                status=ClaimStatus.DRAFT,
            )
            session.add(claim)
            session.commit()
            session.refresh(claim)
            self._logger.info("claim created", extra={"claim_id": claim.id})
            return ClaimRead.model_validate(claim)
