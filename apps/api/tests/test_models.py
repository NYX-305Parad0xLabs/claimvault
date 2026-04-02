from __future__ import annotations

from decimal import Decimal
from datetime import datetime

from app.models import (
    ActorType,
    AuditEvent,
    Case,
    CaseExport,
    CaseStatus,
    ClaimType,
    EvidenceItem,
    EvidenceKind,
    TimelineEvent,
    Workspace,
)


def test_case_creation_and_enums(session_factory):
    with session_factory() as session:
        workspace = Workspace(name="Operations")
        session.add(workspace)
        session.commit()
        session.refresh(workspace)

        case = Case(
            workspace_id=workspace.id,
            title="Return - faulty cable",
            claim_type=ClaimType.RETURN,
            counterparty_name="Customer A",
            merchant_name="Retailer",
            order_reference="ORD-123",
            amount_currency="USD",
            amount_value=Decimal("125.50"),
            purchase_date=datetime.utcnow(),
            incident_date=datetime.utcnow(),
            due_date=datetime.utcnow(),
            summary="Cable shorted after shipment",
        )
        session.add(case)
        session.commit()
        session.refresh(case)

        assert case.status == CaseStatus.DRAFT
        assert case.claim_type is ClaimType.RETURN
        assert case.counterparty_name == "Customer A"

        evidence = EvidenceItem(
            case_id=case.id,
            kind=EvidenceKind.RECEIPT,
            original_filename="receipt.pdf",
            storage_key="proof/receipt.pdf",
            mime_type="application/pdf",
            sha256="digest",
            size_bytes=1024,
            source_label="uploaded",
        )
        session.add(evidence)

        timeline = TimelineEvent(
            case_id=case.id,
            event_type="status_update",
            actor_type=ActorType.USER,
            body="Status moved to collecting evidence",
        )
        session.add(timeline)

        audit = AuditEvent(
            entity_type="case",
            entity_id=case.id,
            action="create",
            actor_type=ActorType.USER,
        )
        session.add(audit)

        export = CaseExport(
            case_id=case.id,
            storage_key="exports/case-1.pdf",
        )
        session.add(export)

        session.commit()

        assert evidence.kind == EvidenceKind.RECEIPT
        assert timeline.actor_type == ActorType.USER
        assert audit.entity_type == "case"
        assert export.export_format == "pdf"


def test_timeline_event_metadata(session_factory):
    with session_factory() as session:
        workspace = Workspace(name="Tracker")
        session.add(workspace)
        session.commit()
        session.refresh(workspace)

        case = Case(
            workspace_id=workspace.id,
            title="Dispute example",
            claim_type=ClaimType.DISPUTE,
            summary="Test events",
        )
        session.add(case)
        session.commit()
        session.refresh(case)

        event = TimelineEvent(
            case_id=case.id,
            event_type="note",
            actor_type=ActorType.SYSTEM,
            body="System note",
            metadata_json={"key": "value"},
        )
        session.add(event)
        session.commit()
        session.refresh(event)

        assert event.metadata_json["key"] == "value"
