from __future__ import annotations

import json
import logging
import re
import zipfile
from datetime import datetime
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Callable, List, Sequence, Tuple
from uuid import uuid4

from fastapi import status
from sqlmodel import Session, select

from app.models.claim import (
    ActorType,
    AuditEvent,
    Case,
    CaseExport,
    EvidenceItem,
    TimelineEvent,
)
from app.schemas.export import CaseExportRead
from app.storage import EvidenceStorage, ExportStorage


class ExportServiceError(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class ExportService:
    def __init__(
        self,
        session_factory: Callable[[], Session],
        evidence_storage: EvidenceStorage,
        export_storage: ExportStorage,
        logger: logging.Logger,
    ) -> None:
        self._session_factory = session_factory
        self._evidence_storage = evidence_storage
        self._export_storage = export_storage
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

            archive = self._build_archive(case, evidence, timeline)
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            filename = f"case_{case_id}_export_{timestamp}.zip"
            storage_key = self._export_storage.store(workspace_id, case_id, filename, archive)

            case_export = CaseExport(case_id=case.id, export_format=export_format, storage_key=storage_key)
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
                    metadata_json={"storage_key": storage_key, "export_id": export_id},
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

    def get_export(self, workspace_id: int, case_id: int, export_id: int) -> CaseExport:
        with self._session_factory() as session:
            export = session.get(CaseExport, export_id)
            case = session.get(Case, case_id)
            if not export or not case:
                raise ExportServiceError("export not found", status.HTTP_404_NOT_FOUND)
            if export.case_id != case_id or case.workspace_id != workspace_id:
                raise ExportServiceError("export not found", status.HTTP_404_NOT_FOUND)
            return export

    def path_for_export(self, storage_key: str) -> Path:
        return self._export_storage.path_for(storage_key)

    def _build_archive(
        self,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
    ) -> bytes:
        case_payload = self._serialize_case(case)
        timeline_payload = [self._serialize_timeline(event) for event in timeline]
        evidence_payload = [self._serialize_evidence(item) for item in evidence]

        summary = self._build_summary(case, len(evidence), len(timeline))

        records: List[Tuple[str, str]] = []
        buffer = BytesIO()
        with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            records.append(self._write_entry(archive, "summary.md", summary.encode("utf-8")))
            records.append(
                self._write_entry(
                    archive,
                    "case.json",
                    json.dumps(case_payload, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8"),
                )
            )
            records.append(
                self._write_entry(
                    archive,
                    "timeline.json",
                    json.dumps(timeline_payload, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8"),
                )
            )
            records.append(
                self._write_entry(
                    archive,
                    "evidence_manifest.json",
                    json.dumps(evidence_payload, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8"),
                )
            )

            for item in evidence:
                evidence_path = self._evidence_storage.path_for(item.storage_key)
                content = evidence_path.read_bytes()
                arcname = f"evidence/{self._sanitize_for_zip(item.original_filename, item.id)}"
                records.append(self._write_entry(archive, arcname, content))

            checksums_text = "\n".join(
                f"{sha}  {path}" for path, sha in sorted(records, key=lambda record: record[0])
            )
            checksums_text += "\n"
            records.append(
                self._write_entry(archive, "checksums.txt", checksums_text.encode("utf-8"))
            )

        return buffer.getvalue()

    @staticmethod
    def _write_entry(archive: zipfile.ZipFile, arcname: str, content: bytes) -> Tuple[str, str]:
        info = zipfile.ZipInfo(arcname)
        info.date_time = (2000, 1, 1, 0, 0, 0)
        info.compress_type = zipfile.ZIP_DEFLATED
        info.create_system = 0
        info.external_attr = 0o644 << 16
        archive.writestr(info, content)
        return arcname, sha256(content).hexdigest()

    @staticmethod
    def _sanitize_for_zip(filename: str, identifier: int | None = None) -> str:
        name = Path(filename).name.strip()
        cleaned = re.sub(r"[^A-Za-z0-9_.-]", "_", name) if name else ""
        if not cleaned:
            cleaned = f"file-{uuid4().hex[:8]}"
        if identifier is not None:
            return f"{identifier}-{cleaned}"
        return cleaned

    @staticmethod
    def _serialize_case(case: Case) -> dict[str, object | str | None]:
        return {
            "id": case.id,
            "workspace_id": case.workspace_id,
            "title": case.title,
            "claim_type": case.claim_type.value,
            "status": case.status.value,
            "counterparty_name": case.counterparty_name,
            "merchant_name": case.merchant_name,
            "order_reference": case.order_reference,
            "amount_currency": case.amount_currency,
            "amount_value": float(case.amount_value),
            "purchase_date": case.purchase_date.isoformat() if case.purchase_date else None,
            "incident_date": case.incident_date.isoformat() if case.incident_date else None,
            "due_date": case.due_date.isoformat() if case.due_date else None,
            "summary": case.summary,
            "created_at": case.created_at.isoformat(),
            "updated_at": case.updated_at.isoformat(),
        }

    @staticmethod
    def _serialize_timeline(event: TimelineEvent) -> dict[str, object | str | None]:
        return {
            "id": event.id,
            "event_type": event.event_type,
            "happened_at": event.happened_at.isoformat(),
            "actor_type": event.actor_type.value,
            "actor_id": event.actor_id,
            "evidence_id": event.evidence_id,
            "body": event.body,
            "metadata_json": event.metadata_json,
        }

    @staticmethod
    def _serialize_evidence(item: EvidenceItem) -> dict[str, object]:
        return {
            "id": item.id,
            "case_id": item.case_id,
            "kind": item.kind,
            "original_filename": item.original_filename,
            "storage_key": item.storage_key,
            "mime_type": item.mime_type,
            "sha256": item.sha256,
            "size_bytes": item.size_bytes,
            "source_label": item.source_label,
            "uploaded_at": item.uploaded_at.isoformat(),
            "metadata_json": item.metadata_json,
        }

    @staticmethod
    def _build_summary(case: Case, evidence_count: int, timeline_count: int) -> str:
        lines = [
            f"# Case Export: {case.title}",
            "",
            f"- Claim ID: {case.id}",
            f"- Claim Type: {case.claim_type.value}",
            f"- Status: {case.status.value}",
            f"- Merchant: {case.merchant_name or 'N/A'}",
            f"- Counterparty: {case.counterparty_name or 'N/A'}",
            f"- Order Reference: {case.order_reference or 'N/A'}",
            f"- Amount: {case.amount_value} {case.amount_currency}",
            f"- Purchase Date: {case.purchase_date.isoformat() if case.purchase_date else 'N/A'}",
            f"- Incident Date: {case.incident_date.isoformat() if case.incident_date else 'N/A'}",
            f"- Evidence Pieces: {evidence_count}",
            f"- Timeline Events: {timeline_count}",
            "",
            "## Summary",
            case.summary or "No summary provided.",
            "",
            "## Notes",
            "- Timeline is exported sorted by timestamp.",
            "- Evidence files are included verbatim under the `evidence/` folder.",
        ]
        return "\n".join(lines)
