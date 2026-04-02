from __future__ import annotations

from decimal import Decimal
from datetime import datetime

from app.models import (
    ActorType,
    AuditEvent,
    Case,
    CaseStatus,
    ClaimType,
    CounterpartyProfile,
    CounterpartyType,
    ExportArtifact,
    EvidenceItem,
    EvidenceKind,
    MissingEvidenceCheck,
    TimelineEvent,
    Workspace,
)
from sqlmodel import select


def test_case_creation_and_enums(session_factory):
    with session_factory() as session:
        workspace = Workspace(name="Operations")
        session.add(workspace)
        session.commit()
        session.refresh(workspace)

        case = Case(
            workspace_id=workspace.id,
            title="Return - faulty cable",
            claim_type=ClaimType.REFUND,
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
        assert case.claim_type is ClaimType.REFUND
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

        export = ExportArtifact(
            case_id=case.id,
            storage_key="exports/case-1.zip",
            manifest_hash="abc",
            archive_hash="def",
            metadata_json={"packager": "default"},
        )
        session.add(export)

        session.commit()

        assert evidence.kind == EvidenceKind.RECEIPT
        assert timeline.actor_type == ActorType.USER
        assert audit.entity_type == "case"
        assert export.manifest_hash == "abc"
        assert export.archive_hash == "def"
        assert export.metadata_json["packager"] == "default"


def test_missing_evidence_check(session_factory):
    with session_factory() as session:
        workspace = Workspace(name="Tracker")
        session.add(workspace)
        session.commit()
        session.refresh(workspace)

        counterparty = CounterpartyProfile(
            workspace_id=workspace.id,
            name="Merchant",
            profile_type=CounterpartyType.MERCHANT,
        )
        session.add(counterparty)
        session.commit()
        session.refresh(counterparty)

        case = Case(
            workspace_id=workspace.id,
            title="Missing rule case",
            claim_type=ClaimType.REFUND,
            counterparty_profile_id=counterparty.id,
        )
        session.add(case)
        session.commit()
        session.add(
            MissingEvidenceCheck(
                case_id=case.id,
                rule_key="order_reference",
                description="Order reference required",
                required=True,
                satisfied=False,
            )
        )
        session.commit()
        checks = session.exec(
            select(MissingEvidenceCheck).where(MissingEvidenceCheck.case_id == case.id)
        ).all()
        assert checks
        assert checks[0].rule_key == "order_reference"


def test_timeline_event_metadata(session_factory):
    with session_factory() as session:
        workspace = Workspace(name="Tracker")
        session.add(workspace)
        session.commit()
        session.refresh(workspace)

        case = Case(
            workspace_id=workspace.id,
            title="Dispute example",
            claim_type=ClaimType.CHARGEBACK_PREP,
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
