from __future__ import annotations

from datetime import datetime

from sqlmodel import SQLModel


class EvidenceRead(SQLModel):
    id: int
    case_id: int
    original_filename: str
    mime_type: str
    sha256: str
    size_bytes: int
    uploaded_at: datetime
    storage_key: str
    source_label: str | None = None

    class Config:
        from_attributes = True
