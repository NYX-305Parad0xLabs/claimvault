from __future__ import annotations

from datetime import datetime

from sqlmodel import SQLModel

from app.models.claim import ClaimStatus, ClaimType


class ClaimCreate(SQLModel):
    subject: str
    claim_type: ClaimType
    created_by: str


class ClaimRead(SQLModel):
    id: int
    subject: str
    claim_type: ClaimType
    status: ClaimStatus
    created_by: str
    created_at: datetime

    class Config:
        from_attributes = True
