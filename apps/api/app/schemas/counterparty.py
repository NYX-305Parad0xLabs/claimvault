from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import ConfigDict
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


class CounterpartyProfileCreate(SQLModel):
    name: str
    profile_type: CounterpartyType
    website: str | None = None
    support_email: str | None = None
    support_url: str | None = None
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")


class CounterpartyProfileUpdate(SQLModel):
    name: str | None = None
    profile_type: CounterpartyType | None = None
    website: str | None = None
    support_email: str | None = None
    support_url: str | None = None
    notes: str | None = None

    model_config = ConfigDict(extra="forbid")
