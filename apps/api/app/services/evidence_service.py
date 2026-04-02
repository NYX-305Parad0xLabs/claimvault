from __future__ import annotations

import hashlib
import logging
from pathlib import Path
from typing import Callable

from fastapi import status
from sqlmodel import Session, select

from app.core.config import Settings
from app.models.claim import (
    ActorType,
    AuditEvent,
    Case,
    EvidenceItem,
    EvidenceKind,
    TimelineEvent,
)
from app.schemas.evidence import EvidenceRead
from app.storage import EvidenceStorage


DISALLOWED_MIMES = {
    "application/x-msdownload",
    "application/x-msdos-program",
    "application/x-sh",
    "application/x-executable",
}


def _guess_mime(content: bytes, filename: str) -> str:
    lower = content[:8]
    if lower.startswith(b"%PDF-"):
        return "application/pdf"
    if lower.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if lower[:3] == b"GIF":
        return "image/gif"
    if lower[:2] == b"\xff\xd8":
        return "image/jpeg"
    return filename and filename.lower().endswith(".txt") and "text/plain" or "application/octet-stream"


class EvidenceServiceError(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.detail = detail
        self.status_code = status_code


class EvidenceService:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        storage: EvidenceStorage,
        settings: Settings,
        logger: logging.Logger,
    ) -> None:
        self._session_factory = session_factory
        self._storage = storage
        self._settings = settings
        self._logger = logger

    def _validate_case(self, session: Session, workspace_id: int, case_id: int) -> Case:
        case = session.get(Case, case_id)
        if not case or case.workspace_id != workspace_id:
            raise EvidenceServiceError("case not found", status.HTTP_404_NOT_FOUND)
        return case

    def list_evidence(self, workspace_id: int, case_id: int) -> list[EvidenceRead]:
        with self._session_factory() as session:
            self._validate_case(session, workspace_id, case_id)
            statement = select(EvidenceItem).where(EvidenceItem.case_id == case_id)
            records = session.exec(statement.order_by(EvidenceItem.uploaded_at.desc())).all()
            return [EvidenceRead.model_validate(record) for record in records]

    def upload_evidence(
        self,
        workspace_id: int,
        case_id: int,
        filename: str,
        content: bytes,
        actor_id: int,
        source_label: str | None = None,
    ) -> EvidenceRead:
        if not content:
            raise EvidenceServiceError("file payload is empty")
        if len(content) > self._settings.max_evidence_size_bytes:
            raise EvidenceServiceError("file exceeds maximum size", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        mime_type = _guess_mime(content, filename)
        if mime_type in DISALLOWED_MIMES:
            raise EvidenceServiceError("file type is not permitted")

        sha256 = hashlib.sha256(content).hexdigest()
        storage_key = self._storage.store(workspace_id, case_id, filename, content)

        with self._session_factory() as session:
            case = self._validate_case(session, workspace_id, case_id)
            evidence = EvidenceItem(
                case_id=case.id,
                kind=EvidenceKind.OTHER,
                original_filename=filename,
                storage_key=storage_key,
                mime_type=mime_type,
                sha256=sha256,
                size_bytes=len(content),
                source_label=source_label,
            )
            session.add(evidence)
            session.add(
                TimelineEvent(
                    case_id=case.id,
                    event_type="evidence_uploaded",
                    actor_type=ActorType.USER,
                    actor_id=actor_id,
                    body=f"Uploaded {filename}",
                    metadata_json={"storage_key": storage_key},
                )
            )
            session.add(
                AuditEvent(
                    entity_type="evidence",
                    entity_id=case.id,
                    action="upload",
                    actor_type=ActorType.USER,
                    actor_id=actor_id,
                    metadata_json={"storage_key": storage_key},
                )
            )
            session.commit()
            session.refresh(evidence)
            self._logger.info(
                "evidence stored",
                extra={"case_id": case_id, "evidence_id": evidence.id, "storage_key": storage_key},
            )
            return EvidenceRead.model_validate(evidence)

    def get_evidence(
        self, workspace_id: int, case_id: int, evidence_id: int
    ) -> tuple[EvidenceItem, Path]:
        with self._session_factory() as session:
            self._validate_case(session, workspace_id, case_id)
            evidence = session.get(EvidenceItem, evidence_id)
            if not evidence or evidence.case_id != case_id:
                raise EvidenceServiceError("evidence not found", status.HTTP_404_NOT_FOUND)
        path = self._storage.path_for(evidence.storage_key)
        return evidence, path
