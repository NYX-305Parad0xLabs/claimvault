from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, Optional

from sqlalchemy import JSON, Boolean, Column, DateTime, Numeric, text
from sqlmodel import Field, SQLModel


class ClaimType(str, Enum):
    """Supported claim types for Case records."""

    REFUND = "refund"
    WARRANTY = "warranty"
    CHARGEBACK_PREP = "chargeback_prep"
    SHIPMENT_DAMAGE = "shipment_damage"
    RENTAL_DEPOSIT = "rental_deposit"


class CaseStatus(str, Enum):
    """Lifecycle states for a case."""

    DRAFT = "draft"
    COLLECTING_EVIDENCE = "collecting_evidence"
    NEEDS_USER_INPUT = "needs_user_input"
    READY_FOR_EXPORT = "ready_for_export"
    EXPORTED = "exported"
    SUBMITTED = "submitted"
    RESOLVED = "resolved"
    CLOSED = "closed"


class EvidenceKind(str, Enum):
    """Kinds of evidence uploaded to a case."""

    RECEIPT = "receipt"
    SCREENSHOT = "screenshot"
    ORDER_CONFIRMATION = "order_confirmation"
    SHIPMENT_TRACKING = "shipment_tracking"
    CHAT_EXPORT = "chat_export"
    EMAIL_PDF = "email_pdf"
    PRODUCT_PHOTO = "product_photo"
    MOVE_OUT_PHOTO = "move_out_photo"
    INVOICE = "invoice"
    HANDWRITTEN_NOTE = "handwritten_note"
    OTHER = "other"

    TRACKING_DOC = SHIPMENT_TRACKING
    PHOTO = PRODUCT_PHOTO
    NOTE = HANDWRITTEN_NOTE


class ExtractionStatus(str, Enum):
    """Evidence extraction progress."""

    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"


class ActorType(str, Enum):
    """Actors that can trigger timeline or audit events."""

    USER = "user"
    SYSTEM = "system"
    INTEGRATION = "integration"


class WorkspaceRole(str, Enum):
    """Roles that determine workspace access levels."""

    OWNER = "owner"
    OPERATOR = "operator"
    VIEWER = "viewer"


class CounterpartyType(str, Enum):
    """Types of entities that can be counterparty profiles."""

    MERCHANT = "merchant"
    LANDLORD = "landlord"
    CARRIER = "carrier"
    MANUFACTURER = "manufacturer"


class User(SQLModel, table=True):
    """Platform operator or auditor."""

    id: Optional[int] = Field(default=None, primary_key=True)
    email: str = Field(index=True, unique=True)
    hashed_password: str
    full_name: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Workspace(SQLModel, table=True):
    """Top-level workspace that groups cases and evidence."""

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class WorkspaceMembership(SQLModel, table=True):
    """Association of users to workspaces with roles."""

    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    role: WorkspaceRole
    created_at: datetime = Field(default_factory=datetime.utcnow)


class CounterpartyProfile(SQLModel, table=True):
    """Lightweight counterparty data (merchant, landlord, carrier, manufacturer)."""

    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    name: str
    profile_type: CounterpartyType
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, server_default="{}"),
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ClaimTemplate(SQLModel, table=True):
    """Future-ready template capturing required evidence sets."""

    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    name: str
    description: Optional[str] = None
    required_fields: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, server_default="{}"),
    )
    active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class Case(SQLModel, table=True):
    """Claim case with metadata, thresholds, and status lifecycle."""

    id: Optional[int] = Field(default=None, primary_key=True)
    workspace_id: int = Field(foreign_key="workspace.id", index=True)
    template_id: Optional[int] = Field(default=None, foreign_key="claimtemplate.id", index=True)
    title: str
    claim_type: ClaimType
    status: CaseStatus = Field(default=CaseStatus.DRAFT)
    counterparty_name: Optional[str] = None
    counterparty_profile_id: Optional[int] = Field(default=None, foreign_key="counterpartyprofile.id")
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
    merchant_label: Optional[str] = None
    carrier_label: Optional[str] = None
    platform_label: Optional[str] = None
    event_date: Optional[datetime] = None
    description: Optional[str] = None
    manual_relevance: bool = Field(
        default=False,
        sa_column=Column(Boolean, nullable=False, server_default=text("0")),
    )
    source_label: Optional[str] = None
    extraction_status: ExtractionStatus = Field(default=ExtractionStatus.PENDING)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    extracted_text: Optional[str] = None
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, server_default="{}"),
    )
    deleted_at: Optional[datetime] = Field(default=None, sa_column=Column(DateTime))
    deleted_by: Optional[int] = Field(
        default=None,
        foreign_key="user.id",
        index=True,
    )


class TimelineEvent(SQLModel, table=True):
    """Append-only timeline entry for cases."""

    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="case.id", index=True)
    evidence_id: Optional[int] = Field(default=None, foreign_key="evidenceitem.id", index=True)
    event_type: str
    happened_at: datetime = Field(default_factory=datetime.utcnow)
    actor_type: ActorType
    actor_id: Optional[int] = None
    body: str
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, server_default="{}"),
    )


class MissingEvidenceCheck(SQLModel, table=True):
    """Structured record of each rule evaluated for readiness."""

    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="case.id", index=True)
    rule_key: str
    description: str
    required: bool = True
    satisfied: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_checked_at: datetime = Field(default_factory=datetime.utcnow)


class ExportArtifact(SQLModel, table=True):
    """Deterministic export bundle metadata."""

    id: Optional[int] = Field(default=None, primary_key=True)
    case_id: int = Field(foreign_key="case.id", index=True)
    artifact_type: str = Field(default="bundle")
    storage_key: str
    manifest_hash: Optional[str] = None
    archive_hash: Optional[str] = None
    metadata_json: dict[str, Any] = Field(
        default_factory=dict,
        sa_column=Column(JSON, nullable=False, server_default="{}"),
    )
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
