from __future__ import annotations

import logging
from typing import Callable

from fastapi import status
from sqlmodel import Session, select

from app.models.claim import AuditEvent, Case


class AuditServiceError(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.detail = detail
        self.status_code = status_code


class AuditService:
    def __init__(self, session_factory: Callable[[], Session], logger: logging.Logger) -> None:
        self._session_factory = session_factory
        self._logger = logger

    def _validate_case(self, session: Session, workspace_id: int, case_id: int) -> Case:
        case = session.get(Case, case_id)
        if not case or case.workspace_id != workspace_id:
            raise AuditServiceError("case not found", status.HTTP_404_NOT_FOUND)
        return case

    def list_case_events(
        self,
        workspace_id: int,
        case_id: int,
        *,
        limit: int = 50,
        offset: int = 0,
    ) -> list[AuditEvent]:
        with self._session_factory() as session:
            self._validate_case(session, workspace_id, case_id)
            statement = (
                select(AuditEvent)
                .where(AuditEvent.entity_id == case_id)
                .order_by(AuditEvent.happened_at.desc(), AuditEvent.id.desc())
                .limit(limit)
                .offset(offset)
            )
            records = session.exec(statement).all()
            self._logger.debug(
                "loaded audit events",
                extra={"case_id": case_id, "workspace_id": workspace_id, "count": len(records)},
            )
            return records
