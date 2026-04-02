from __future__ import annotations

from typing import Callable

from fastapi import status
from sqlmodel import Session, select

from app.models.claim import Case, EvidenceItem, TimelineEvent
from app.schemas.case_summary import CaseSummaryPreview
from app.services.summary_builder import CaseSummaryBuilder


class CaseSummaryServiceError(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.detail = detail
        self.status_code = status_code


class CaseSummaryService:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        summary_builder: CaseSummaryBuilder,
    ) -> None:
        self._session_factory = session_factory
        self._summary_builder = summary_builder

    def preview_summary(self, workspace_id: int, case_id: int) -> CaseSummaryPreview:
        with self._session_factory() as session:
            case = session.get(Case, case_id)
            if not case or case.workspace_id != workspace_id:
                raise CaseSummaryServiceError("case not found", status.HTTP_404_NOT_FOUND)

            evidence = (
                session.exec(select(EvidenceItem).where(EvidenceItem.case_id == case_id))
                .all()
            )
            timeline = (
                session.exec(
                    select(TimelineEvent)
                    .where(TimelineEvent.case_id == case_id)
                    .order_by(TimelineEvent.happened_at, TimelineEvent.id)
                )
                .all()
            )

        summary_text = self._summary_builder.build_summary(case, evidence, timeline)
        return CaseSummaryPreview(
            case_id=case.id,
            claim_type=case.claim_type.value,
            summary=summary_text,
        )
