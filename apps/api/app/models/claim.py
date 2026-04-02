from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from sqlalchemy import JSON, Column, DateTime, Numeric
from sqlmodel import Field, SQLModel


class ClaimType(str, Enum):
    """Supported claim types for Case records."""
    RETURN = "return"
    DISPUTE = "dispute"
    WARRANTY = "warranty"


class CaseStatus(str, Enum):
    """Valid lifecycle statuses for a Case."""
    DRAFT = "draft"
    COLLECTING_EVIDENCE = "collecting_evidence"
    READY_TO_EXPORT = "ready_to_export"
    SUBMITTED = "submitted"
    RESOLVED = "resolved"
    CLOSED = "closed"


class EvidenceKind(str, Enum):
    """Kinds of evidence uploaded to a case."""
    RECEIPT = "receipt"
    SCREENSHOT = "screenshot"
    EMAIL_PDF = "email_pdf"
    TRACKING_DOC = "tracking_doc"
    CHAT_EXPORT = "chat_export"
    PHOTO = "photo"
    NOTE = "note"
    OTHER = "other"


class ActorType(str, Enum):
    """Actors that can trigger timeline or audit events."""
    USER = "user"
    SYSTEM = "system"
    INTEGRATION = "integration"


class User(SQLModel, table=True):
    """Platform operator or auditor."""

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True)
    full_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Workspace(SQLModel, table=True):
    """Top-level workspace that groups cases and evidence."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Case(SQLModel, table=True):
    """Claim case with metadata, thresholds, and status lifecycle."""

    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    title: str
    claim_type: ClaimType
    status: CaseStatus = Field(default=CaseStatus.DRAFT)
    counterparty_name: Optional[str] = None
    merchant_name: Optional[str] = None
    order_reference: Optional[str] = None
    amount_currency: str = Field(default="USD")
    amount_value: Decimal = Field(
        sa_column=Column(Numeric(12, 2), nullable=False), default=Decimal("0.00")
    )
    purchase_date: Optional[datetime] = Field(sa_column=Column(DateTime))
    incident_date: Optional[datetime] = Field(sa_column=Column(DateTime))
    due_date: Optional[datetime] = Field(sa_column=Column(DateTime))
    summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class EvidenceItem(SQLModel, table=True):
    """Evidence uploaded to a case."""

    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="case.id", index=True)
    kind: EvidenceKind
    original_filename: str
    storage_key: str
    mime_type: str
    sha256: str
    size_bytes: int
    source_label: Optional[str] = None
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    extracted_text: Optional[str] = None
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, server_default="{}"),
    )


class TimelineEvent(SQLModel, table=True):
    """Append-only timeline entry for cases."""

    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="case.id", index=True)
    event_type: str
    happened_at: datetime = Field(default_factory=datetime.utcnow)
    actor_type: ActorType
    actor_id: Optional[int] = None
    body: str
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, server_default="{}"),
    )


class CaseExport(SQLModel, table=True):
    """Exported bundle produced for reviewers."""

    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="case.id", index=True)
    export_format: str = Field(default="pdf")
    storage_key: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class AuditEvent(SQLModel, table=True):
    """Append-only audit log for every key entity mutation."""

    id: Optional[int] = Field(default=None, primary_key=True)
    entity_type: str
    entity_id: int
    action: str
    actor_type: ActorType
    actor_id: Optional[int] = None
    happened_at: datetime = Field(default_factory=datetime.utcnow)
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, server_default="{}"),
    )
