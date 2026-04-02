from __future__ import annotations

import json
import logging
import re
import zipfile
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from hashlib import sha256
from io import BytesIO
from pathlib import Path
from typing import Any, Sequence
from uuid import uuid4

from app.models.claim import Case, EvidenceItem, TimelineEvent
from app.services.summary_builder import CaseSummaryBuilder
from app.storage import EvidenceStorage


@dataclass(frozen=True)
class PackagingResult:
    filename: str
    content: bytes
    manifest: dict[str, Any]


class VaultPackager(ABC):
    """Defines the seam that produces a vault bundle for a case."""

    name: str

    @abstractmethod
    def package(
        self,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
    ) -> PackagingResult:
        ...


class DefaultVaultPackager(VaultPackager):
    """Current internal exporter that zips the case summary, timeline, and evidence assets."""

    name = "default"

    def __init__(
        self,
        evidence_storage: EvidenceStorage,
        summary_builder: CaseSummaryBuilder,
        logger: logging.Logger | None = None,
    ) -> None:
        self._logger = logger or logging.getLogger(__name__)
        self._storage = evidence_storage
        self._summary_builder = summary_builder

    def package(
        self,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
    ) -> PackagingResult:
        self._logger.debug("packaging export bundle internally", extra={"case_id": case.id})
        content, records = self._build_archive(case, evidence, timeline)
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        filename = f"case_{case.id}_export_{timestamp}.zip"
        manifest = {
            "packager": self.name,
            "records": [{"path": path, "sha256": digest} for path, digest in sorted(records)],
        }
        return PackagingResult(filename=filename, content=content, manifest=manifest)

    def _build_archive(
        self,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
    ) -> tuple[bytes, list[tuple[str, str]]]:
        case_payload = self._serialize_case(case)
        timeline_payload = [self._serialize_timeline(event) for event in timeline]
        evidence_payload = [self._serialize_evidence(item) for item in evidence]
        summary = self._summary_builder.build_summary(case, evidence, timeline)
        records: list[tuple[str, str]] = []
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
                evidence_path = self._storage.path_for(item.storage_key)
                content = evidence_path.read_bytes()
                arcname = f"evidence/{self._sanitize_for_zip(item.original_filename, item.id)}"
                records.append(self._write_entry(archive, arcname, content))
            checksums_text = "\n".join(
                f"{digest}  {path}" for path, digest in sorted(records, key=lambda record: record[0])
            )
            checksums_text += "\n"
            records.append(
                self._write_entry(archive, "checksums.txt", checksums_text.encode("utf-8"))
            )
        return buffer.getvalue(), records

    @staticmethod
    def _write_entry(archive: zipfile.ZipFile, arcname: str, content: bytes) -> tuple[str, str]:
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
    def _serialize_case(case: Case) -> dict[str, Any | None]:
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
    def _serialize_timeline(event: TimelineEvent) -> dict[str, Any | None]:
        return {
            "id": event.id,
            "event_type": event.event_type,
            "happened_at": event.happened_at.isoformat(),
            "actor_type": event.actor_type.value if hasattr(event.actor_type, "value") else event.actor_type,
            "actor_id": event.actor_id,
            "evidence_id": event.evidence_id,
            "body": event.body,
            "metadata_json": event.metadata_json,
        }

    @staticmethod
    def _serialize_evidence(item: EvidenceItem) -> dict[str, Any]:
        return {
            "id": item.id,
            "case_id": item.case_id,
            "kind": item.kind.value if hasattr(item.kind, "value") else item.kind,
            "original_filename": item.original_filename,
            "storage_key": item.storage_key,
            "mime_type": item.mime_type,
            "sha256": item.sha256,
            "size_bytes": item.size_bytes,
            "source_label": item.source_label,
            "uploaded_at": item.uploaded_at.isoformat(),
            "metadata_json": item.metadata_json,
        }


class LiquefyPackager(VaultPackager):
    """
    Placeholder for the future Liquefy-driven packager.

    Future responsibilities include verified packing, vault search, policy/redaction, proof-artifact
    generation, and safe restore of exported bundles.
    """

    name = "liquefy"

    def __init__(self, logger: logging.Logger | None = None) -> None:
        self._logger = logger or logging.getLogger(__name__)

    def package(
        self,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
    ) -> PackagingResult:
        # TODO: Replace this stub with the Liquefy API adapter once the repo is available.
        self._logger.warning(
            "Liquefy packager invoked while integration is pending",
            extra={"case_id": case.id},
        )
        raise NotImplementedError("Liquefy packaging is not implemented yet")
