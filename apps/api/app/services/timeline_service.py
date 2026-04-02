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
    EvidenceItem,
    TimelineEvent,
)
from app.schemas.timeline import (
    TimelineEventCreate,
    TimelineEventRead,
    TimelineNoteCreate,
)


class TimelineServiceError(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.detail = detail
        self.status_code = status_code


class TimelineService:
    def __init__(self, session_factory: Callable[[], Session], logger: logging.Logger) -> None:
        self._session_factory = session_factory
        self._logger = logger

    def _validate_case(self, session: Session, workspace_id: int, case_id: int) -> Case:
        case = session.get(Case, case_id)
        if not case or case.workspace_id != workspace_id:
            raise TimelineServiceError("case not found", status.HTTP_404_NOT_FOUND)
        return case

    def _validate_evidence(self, session: Session, case_id: int, evidence_id: int) -> EvidenceItem:
        evidence = session.get(EvidenceItem, evidence_id)
        if not evidence or evidence.case_id != case_id:
            raise TimelineServiceError("evidence not found", status.HTTP_404_NOT_FOUND)
        return evidence

    def _record_audit(
        self,
        session: Session,
        actor_id: int,
        case_id: int,
        action: str,
        metadata: dict[str, object] | None = None,
    ) -> None:
        session.add(
            AuditEvent(
                entity_type="timeline_event",
                entity_id=case_id,
                action=action,
                actor_type=ActorType.USER,
                actor_id=actor_id,
                metadata_json=metadata or {},
            )
        )

    def list_events(self, workspace_id: int, case_id: int) -> list[TimelineEventRead]:
        with self._session_factory() as session:
            self._validate_case(session, workspace_id, case_id)
            statement = (
                select(TimelineEvent)
                .where(TimelineEvent.case_id == case_id)
                .order_by(TimelineEvent.happened_at, TimelineEvent.id)
            )
            records = session.exec(statement).all()
            return [TimelineEventRead.model_validate(record) for record in records]

    def create_event(
        self,
        workspace_id: int,
        case_id: int,
        payload: TimelineEventCreate,
        actor_id: int,
    ) -> TimelineEventRead:
        with self._session_factory() as session:
            case = self._validate_case(session, workspace_id, case_id)
            if payload.evidence_id is not None:
                self._validate_evidence(session, case_id, payload.evidence_id)

            event = TimelineEvent(
                case_id=case.id,
                event_type=payload.event_type,
                body=payload.body,
                happened_at=payload.happened_at or datetime.utcnow(),
                actor_type=ActorType.USER,
                actor_id=actor_id,
                evidence_id=payload.evidence_id,
                metadata_json=payload.metadata or {},
            )
            session.add(event)
            self._record_audit(
                session,
                actor_id=actor_id,
                case_id=case_id,
                action="create_event",
                metadata=payload.metadata,
            )
            session.commit()
            session.refresh(event)
            self._logger.info(
                "timeline event recorded", extra={"case_id": case_id, "event_id": event.id}
            )
            return TimelineEventRead.model_validate(event)

    def create_note(
        self,
        workspace_id: int,
        case_id: int,
        payload: TimelineNoteCreate,
        actor_id: int,
    ) -> TimelineEventRead:
        with self._session_factory() as session:
            case = self._validate_case(session, workspace_id, case_id)
            if payload.evidence_id is not None:
                self._validate_evidence(session, case_id, payload.evidence_id)

            metadata = payload.metadata or {}
            metadata.update({"note_type": payload.note_type})
            if payload.corrects_event_id:
                original = session.get(TimelineEvent, payload.corrects_event_id)
                if not original or original.case_id != case_id or (
                    original.metadata_json.get("note_type") != "manual"
                ):
                    raise TimelineServiceError(
                        "cannot correct this note", status.HTTP_403_FORBIDDEN
                    )
                metadata["corrects_event_id"] = payload.corrects_event_id

            event = TimelineEvent(
                case_id=case.id,
                event_type="note",
                body=payload.body,
                happened_at=payload.happened_at or datetime.utcnow(),
                actor_type=ActorType.USER,
                actor_id=actor_id,
                evidence_id=payload.evidence_id,
                metadata_json=metadata,
            )
            session.add(event)
            self._record_audit(
                session,
                actor_id=actor_id,
                case_id=case_id,
                action="create_note",
                metadata=metadata,
            )
            session.commit()
            session.refresh(event)
            self._logger.info(
                "manual note recorded",
                extra={"case_id": case_id, "event_id": event.id, "corrects": payload.corrects_event_id},
            )
            return TimelineEventRead.model_validate(event)
