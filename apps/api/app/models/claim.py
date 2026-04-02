from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from sqlmodel import SQLModel, Field


class ClaimType(str, Enum):
    RETURN = "return"
    DISPUTE = "dispute"
    WARRANTY = "warranty"


class ClaimStatus(str, Enum):
    DRAFT = "draft"
    PENDING_REVIEW = "pending_review"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class Claim(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    subject: str
    claim_type: ClaimType
    status: ClaimStatus = Field(default=ClaimStatus.DRAFT)
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class EvidenceItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    claim_id: int = Field(foreign_key="claim.id")
    filename: str
    content_type: str
    evidence_type: str
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class TimelineEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    claim_id: int = Field(foreign_key="claim.id")
    event_type: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditEvent(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    claim_id: Optional[int] = Field(default=None, foreign_key="claim.id")
    actor: str
    action: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
