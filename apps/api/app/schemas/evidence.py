from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlmodel import Field, SQLModel

from app.models.claim import EvidenceKind, ExtractionStatus


class EvidenceRead(SQLModel):
    id: int
    case_id: int
    original_filename: str
    mime_type: str
    sha256: str
    size_bytes: int
    uploaded_at: datetime
    storage_key: str
    kind: EvidenceKind
    source_label: str | None = None
    merchant_label: str | None = None
    carrier_label: str | None = None
    platform_label: str | None = None
    event_date: datetime | None = None
    description: str | None = None
    manual_relevance: bool = False
    extraction_status: ExtractionStatus
    extracted_text: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)

    class Config:
        from_attributes = True

class EvidenceExtractionRead(SQLModel):
    extraction_status: ExtractionStatus
    extracted_text: str | None = None


class EvidenceExtractionUpdate(SQLModel):
    extraction_status: ExtractionStatus | None = None
    extracted_text: str | None = None
