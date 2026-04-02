from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlmodel import SQLModel, Field

from app.models.claim import CaseStatus, ClaimType

from app.schemas.counterparty import CounterpartyProfileRead


class CaseCreate(SQLModel):
    title: str
    claim_type: ClaimType
    counterparty_name: Optional[str] = None
    counterparty_profile_id: Optional[int] = None
    merchant_name: Optional[str] = None
    order_reference: Optional[str] = None
    amount_currency: str = Field(default="USD")
    amount_value: Decimal = Field(default=Decimal("0.00"))
    purchase_date: Optional[datetime] = None
    incident_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    summary: Optional[str] = None


class CaseRead(SQLModel):
    id: int
    workspace_id: int
    title: str
    claim_type: ClaimType
    status: CaseStatus
    counterparty_name: Optional[str]
    counterparty_profile_id: Optional[int]
    counterparty_profile: CounterpartyProfileRead | None = None
    merchant_name: Optional[str]
    order_reference: Optional[str]
    amount_currency: str
    amount_value: Decimal
    purchase_date: Optional[datetime]
    incident_date: Optional[datetime]
    due_date: Optional[datetime]
    summary: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CaseUpdate(SQLModel):
    title: Optional[str] = None
    counterparty_name: Optional[str] = None
    counterparty_profile_id: Optional[int] = None
    merchant_name: Optional[str] = None
    order_reference: Optional[str] = None
    amount_currency: Optional[str] = None
    amount_value: Optional[Decimal] = None
    purchase_date: Optional[datetime] = None
    incident_date: Optional[datetime] = None
    due_date: Optional[datetime] = None
    summary: Optional[str] = None


class CaseTransitionRequest(SQLModel):
    target_status: CaseStatus
    reason: str | None = None
