from __future__ import annotations

import json
import logging
from hashlib import sha256 as hashlib_sha256
from pathlib import Path
from typing import Callable

from fastapi import status
from sqlmodel import Session, select

from app.models.claim import ActorType, AuditEvent, Case, ExportArtifact, EvidenceItem, TimelineEvent
from app.schemas.export import CaseExportRead
from app.services.case_summary_service import CaseSummaryService, CaseSummaryServiceError
from app.services.packager import VaultPackager
from app.storage import ExportStorage


class ExportServiceError(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class ExportService:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        export_storage: ExportStorage,
        packager: VaultPackager,
        summary_service: CaseSummaryService,
        logger: logging.Logger,
    ) -> None:
        self._session_factory = session_factory
        self._export_storage = export_storage
        self._packager = packager
        self._summary_service = summary_service
        self._logger = logger

    def create_export(
        self,
        workspace_id: int,
        case_id: int,
        actor_id: int,
        export_format: str = "zip",
    ) -> CaseExportRead:
        if export_format != "zip":
            raise ExportServiceError("unsupported export format", status.HTTP_400_BAD_REQUEST)

        with self._session_factory() as session:
            case = session.get(Case, case_id)
            if not case or case.workspace_id != workspace_id:
                raise ExportServiceError("case not found", status.HTTP_404_NOT_FOUND)

            evidence = (
                session.exec(select(EvidenceItem).where(EvidenceItem.case_id == case_id).order_by(EvidenceItem.id))
                .all()
            )
            timeline = (
                session.exec(
                    select(TimelineEvent)
                    .where(
                        TimelineEvent.case_id == case_id,
                        TimelineEvent.event_type != "case_exported",
                    )
                    .order_by(TimelineEvent.happened_at, TimelineEvent.id)
                )
                .all()
            )

            try:
                preview = self._summary_service.preview_summary(workspace_id, case_id)
            except CaseSummaryServiceError as error:
                raise ExportServiceError(error.detail, error.status_code)
            packaging = self._packager.package(case, evidence, timeline, preview.summary)
            storage_key = self._export_storage.store(
                workspace_id,
                case_id,
                packaging.filename,
                packaging.content,
            )

            manifest_content = json.dumps(packaging.manifest, sort_keys=True, ensure_ascii=False).encode("utf-8")
            case_export = ExportArtifact(
                case_id=case.id,
                artifact_type="bundle",
                storage_key=storage_key,
                manifest_hash=hashlib_sha256(manifest_content).hexdigest(),
                archive_hash=hashlib_sha256(packaging.content).hexdigest(),
                metadata_json={
                    "records": len(packaging.manifest.get("records", [])),
                    "packager": self._packager.name,
                },
            )
            session.add(case_export)
            session.flush()
            export_id = case_export.id

            session.add(
                TimelineEvent(
                    case_id=case.id,
                    event_type="case_exported",
                    actor_type=ActorType.USER,
                    actor_id=actor_id,
                    body="Case export generated",
                    metadata_json={
                        "storage_key": storage_key,
                        "export_id": export_id,
                        "packager": self._packager.name,
                    },
                )
            )
            session.add(
                AuditEvent(
                    entity_type="case",
                    entity_id=case.id,
                    action="export",
                    actor_type=ActorType.USER,
                    actor_id=actor_id,
                    metadata_json={
                        "case_export_id": export_id,
                        "storage_key": storage_key,
                        "packager": self._packager.name,
                        "manifest_entries": len(packaging.manifest.get("records", [])),
                    },
                )
            )
            session.commit()
            session.refresh(case_export)

            self._logger.info(
                "case exported",
                extra={
                    "case_id": case.id,
                    "case_export_id": case_export.id,
                    "storage_key": storage_key,
                },
            )

            return CaseExportRead.model_validate(case_export.model_dump())

    def get_export(self, workspace_id: int, case_id: int, export_id: int) -> ExportArtifact:
        with self._session_factory() as session:
            export = session.get(ExportArtifact, export_id)
            case = session.get(Case, case_id)
            if not export or not case:
                raise ExportServiceError("export not found", status.HTTP_404_NOT_FOUND)
            if export.case_id != case_id or case.workspace_id != workspace_id:
                raise ExportServiceError("export not found", status.HTTP_404_NOT_FOUND)
            return export

    def path_for_export(self, storage_key: str) -> Path:
        return self._export_storage.path_for(storage_key)
