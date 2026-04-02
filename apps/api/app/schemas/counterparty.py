from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlmodel import SQLModel, Field

from app.models.claim import CounterpartyType


class CounterpartyProfileRead(SQLModel):
    id: int
    workspace_id: int
    name: str
    profile_type: CounterpartyType
    website: str | None = None
    support_email: str | None = None
    support_url: str | None = None
    notes: str | None = None
    metadata_json: dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    class Config:
        from_attributes = True
