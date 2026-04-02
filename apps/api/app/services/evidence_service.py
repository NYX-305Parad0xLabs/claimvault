from __future__ import annotations

import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

from fastapi import status
from sqlmodel import Session, select

from app.core.config import Settings
from app.models.claim import (
    ActorType,
    AuditEvent,
    Case,
    EvidenceItem,
    EvidenceKind,
    ExtractionStatus,
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


def _guess_mime(content: bytes, filename: str, declared_mime: str | None) -> str:
    if declared_mime and declared_mime != "application/octet-stream":
        return declared_mime
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

    def _build_metadata(
        self,
        *,
        merchant_label: str | None,
        carrier_label: str | None,
        platform_label: str | None,
        event_date: datetime | None,
        description: str | None,
        manual_relevance: bool,
        source_label: str | None,
        extraction_status: ExtractionStatus,
    ) -> dict[str, Any]:
        metadata: dict[str, Any] = {
            "manual_relevance": manual_relevance,
            "extraction_status": extraction_status.value,
        }
        if merchant_label:
            metadata["merchant_label"] = merchant_label
        if carrier_label:
            metadata["carrier_label"] = carrier_label
        if platform_label:
            metadata["platform_label"] = platform_label
        if event_date:
            metadata["event_date"] = event_date.isoformat()
        if description:
            metadata["description"] = description
        if source_label:
            metadata["source_label"] = source_label
        return metadata

    def _validate_mime(self, mime_type: str) -> None:
        if mime_type in DISALLOWED_MIMES:
            raise EvidenceServiceError("file type is not permitted")
        allowed = getattr(self._settings, "allowed_evidence_mime_types", ())
        if allowed and mime_type not in allowed:
            raise EvidenceServiceError("file mime type is not supported")

    def list_evidence(self, workspace_id: int, case_id: int) -> list[EvidenceRead]:
        with self._session_factory() as session:
            self._validate_case(session, workspace_id, case_id)
            statement = select(EvidenceItem).where(
                EvidenceItem.case_id == case_id, EvidenceItem.deleted_at.is_(None)
            )
            records = session.exec(statement.order_by(EvidenceItem.uploaded_at.desc())).all()
            return [EvidenceRead.model_validate(record) for record in records]

    def upload_evidence(
        self,
        workspace_id: int,
        case_id: int,
        filename: str,
        content: bytes,
        *,
        kind: EvidenceKind | None = None,
        actor_id: int,
        source_label: str | None = None,
        declared_mime: str | None = None,
        merchant_label: str | None = None,
        carrier_label: str | None = None,
        platform_label: str | None = None,
        event_date: datetime | None = None,
        description: str | None = None,
        extraction_status: ExtractionStatus | None = None,
        manual_relevance: bool = False,
    ) -> EvidenceRead:
        if not content:
            raise EvidenceServiceError("file payload is empty")
        if len(content) > self._settings.max_evidence_size_bytes:
            raise EvidenceServiceError("file exceeds maximum size", status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        extraction_status = extraction_status or ExtractionStatus.PENDING
        mime_type = _guess_mime(content, filename, declared_mime)
        self._validate_mime(mime_type)

        sha256 = hashlib.sha256(content).hexdigest()
        storage_key = self._storage.store(workspace_id, case_id, filename, content)
        metadata = self._build_metadata(
            merchant_label=merchant_label,
            carrier_label=carrier_label,
            platform_label=platform_label,
            event_date=event_date,
            description=description,
            manual_relevance=manual_relevance,
            source_label=source_label,
            extraction_status=extraction_status,
        )

        with self._session_factory() as session:
            case = self._validate_case(session, workspace_id, case_id)
            evidence = EvidenceItem(
                case_id=case.id,
                kind=kind or EvidenceKind.OTHER,
                original_filename=filename,
                storage_key=storage_key,
                mime_type=mime_type,
                sha256=sha256,
                size_bytes=len(content),
                merchant_label=merchant_label,
                carrier_label=carrier_label,
                platform_label=platform_label,
                event_date=event_date,
                description=description,
                manual_relevance=manual_relevance,
                source_label=source_label,
                extraction_status=extraction_status,
                metadata_json=metadata,
            )
            session.add(evidence)
            session.add(
                TimelineEvent(
                    case_id=case.id,
                    event_type="evidence_uploaded",
                    actor_type=ActorType.USER,
                    actor_id=actor_id,
                    body=f"Uploaded {filename}",
                    metadata_json={**metadata, "storage_key": storage_key},
                )
            )
            session.add(
                AuditEvent(
                    entity_type="evidence",
                    entity_id=case.id,
                    action="upload",
                    actor_type=ActorType.USER,
                    actor_id=actor_id,
                    metadata_json={**metadata, "storage_key": storage_key},
                )
            )
            session.commit()
            session.refresh(evidence)
            self._logger.info(
                "evidence stored",
                extra={
                    "case_id": case_id,
                    "evidence_id": evidence.id,
                    "storage_key": storage_key,
                },
            )
            return EvidenceRead.model_validate(evidence)

    def fetch_evidence(
        self, workspace_id: int, case_id: int, evidence_id: int
    ) -> EvidenceItem:
        with self._session_factory() as session:
            self._validate_case(session, workspace_id, case_id)
            evidence = session.get(EvidenceItem, evidence_id)
            if not evidence or evidence.case_id != case_id or evidence.deleted_at:
                raise EvidenceServiceError("evidence not found", status.HTTP_404_NOT_FOUND)
            return evidence

    def get_evidence(
        self, workspace_id: int, case_id: int, evidence_id: int
    ) -> tuple[EvidenceItem, Path]:
        evidence = self.fetch_evidence(workspace_id, case_id, evidence_id)
        path = self._storage.path_for(evidence.storage_key)
        return evidence, path

    def delete_evidence(
        self,
        workspace_id: int,
        case_id: int,
        evidence_id: int,
        *,
        actor_id: int,
        reason: str | None = None,
    ) -> None:
        with self._session_factory() as session:
            case = self._validate_case(session, workspace_id, case_id)
            evidence = session.get(EvidenceItem, evidence_id)
            if not evidence or evidence.case_id != case_id:
                raise EvidenceServiceError("evidence not found", status.HTTP_404_NOT_FOUND)
            if evidence.deleted_at:
                raise EvidenceServiceError("evidence already removed", status.HTTP_410_GONE)

            evidence.deleted_at = datetime.utcnow()
            evidence.deleted_by = actor_id
            metadata = {
                "storage_key": evidence.storage_key,
                "manual_relevance": evidence.manual_relevance,
                "merchant_label": evidence.merchant_label,
                "carrier_label": evidence.carrier_label,
                "platform_label": evidence.platform_label,
            }
            if reason:
                metadata["reason"] = reason

            session.add(
                TimelineEvent(
                    case_id=case.id,
                    event_type="evidence_removed",
                    actor_type=ActorType.USER,
                    actor_id=actor_id,
                    body=f"Evidence removed: {evidence.original_filename}",
                    metadata_json=metadata,
                )
            )
            session.add(
                AuditEvent(
                    entity_type="evidence",
                    entity_id=case.id,
                    action="delete",
                    actor_type=ActorType.USER,
                    actor_id=actor_id,
                    metadata_json=metadata,
                )
            )
            session.commit()
