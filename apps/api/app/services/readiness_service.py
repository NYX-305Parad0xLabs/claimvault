from __future__ import annotations

from dataclasses import dataclass
import logging
from typing import Callable

from sqlalchemy import func
from sqlmodel import Session, select

from app.models.claim import (
    Case,
    ClaimType,
    EvidenceItem,
    MissingEvidenceCheck,
    TimelineEvent,
)
from app.schemas.readiness import ReadinessReport


@dataclass
class Rule:
    name: str
    description: str
    weight: int
    required: bool
    predicate: Callable[[Case, dict[str, int]], bool]


class ReadinessService:
    def __init__(self, session_factory: Callable[[], Session], logger: logging.Logger) -> None:
        self._session_factory = session_factory
        self._logger = logger
        self._rules = {
            ClaimType.REFUND: [
                Rule(
                    "order_reference",
                    "Provide the customer order reference",
                    20,
                    True,
                    lambda case, ctx: bool(case.order_reference),
                ),
                Rule(
                    "merchant",
                    "Capture the merchant/retailer name",
                    20,
                    True,
                    lambda case, ctx: bool(case.merchant_name),
                ),
                Rule(
                    "receipt",
                    "Upload at least one receipt or order document",
                    25,
                    True,
                    lambda case, ctx: ctx["evidence_count"] >= 1,
                ),
                Rule(
                    "timeline_event",
                    "Add at least one timeline entry before export",
                    20,
                    True,
                    lambda case, ctx: ctx["timeline_count"] >= 1,
                ),
                Rule(
                    "supporting_docs",
                    "Include more than one supporting document when available",
                    15,
                    False,
                    lambda case, ctx: ctx["evidence_count"] >= 2,
                ),
            ],
            ClaimType.CHARGEBACK_PREP: [
                Rule(
                    "amount",
                    "Record the disputed amount",
                    20,
                    True,
                    lambda case, ctx: case.amount_value and case.amount_value > 0,
                ),
                Rule(
                    "merchant",
                    "Capture the disputed merchant",
                    20,
                    True,
                    lambda case, ctx: bool(case.merchant_name),
                ),
                Rule(
                    "summary",
                    "Provide a summary of the dispute incident",
                    20,
                    True,
                    lambda case, ctx: bool(case.summary),
                ),
                Rule(
                    "timeline_event",
                    "Log at least one timeline entry documenting the dispute",
                    20,
                    True,
                    lambda case, ctx: ctx["timeline_count"] >= 1,
                ),
                Rule(
                    "supporting_doc",
                    "Attach at least one supporting document",
                    20,
                    True,
                    lambda case, ctx: ctx["evidence_count"] >= 1,
                ),
            ],
            ClaimType.WARRANTY: [
                Rule(
                    "order_reference",
                    "Include the order/product reference tied to the warranty.",
                    20,
                    True,
                    lambda case, ctx: bool(case.order_reference),
                ),
                Rule(
                    "purchase_date",
                    "Record the purchase date",
                    20,
                    True,
                    lambda case, ctx: bool(case.purchase_date),
                ),
                Rule(
                    "issue_summary",
                    "Detail the issue or symptoms in the summary",
                    20,
                    True,
                    lambda case, ctx: bool(case.summary),
                ),
                Rule(
                    "evidence",
                    "Upload at least one supporting piece of evidence",
                    20,
                    True,
                    lambda case, ctx: ctx["evidence_count"] >= 1,
                ),
                Rule(
                    "timeline_event",
                    "Log at least one timeline entry for the warranty incident",
                    20,
                    False,
                    lambda case, ctx: ctx["timeline_count"] >= 1,
                ),
            ],
            ClaimType.SHIPMENT_DAMAGE: [
                Rule(
                    "damage_report",
                    "Add a damage report or photo note describing the shipment issue",
                    20,
                    True,
                    lambda case, ctx: bool(case.summary),
                ),
                Rule(
                    "timeline_event",
                    "Capture each inspection step in the timeline",
                    20,
                    True,
                    lambda case, ctx: ctx["timeline_count"] >= 1,
                ),
                Rule(
                    "evidence",
                    "Upload a photo, inspection report, or carrier note",
                    20,
                    True,
                    lambda case, ctx: ctx["evidence_count"] >= 1,
                ),
            ],
            ClaimType.RENTAL_DEPOSIT: [
                Rule(
                    "inspection_notes",
                    "Log move-in/out inspections and findings",
                    20,
                    True,
                    lambda case, ctx: ctx["timeline_count"] >= 2,
                ),
                Rule(
                    "damage_photos",
                    "Include photos or reports tied to repair requests",
                    20,
                    True,
                    lambda case, ctx: ctx["evidence_count"] >= 1,
                ),
                Rule(
                    "communication_log",
                    "Summarize tenant/property communications or agreements",
                    20,
                    True,
                    lambda case, ctx: bool(case.summary),
                ),
            ],
        }

    def _gather_context(self, session: Session, case_id: int) -> tuple[Case, dict[str, int]]:
        case = session.get(Case, case_id)
        if not case:
            raise ValueError("case not found")

        timeline_count = session.exec(
            select(func.count()).select_from(TimelineEvent).where(TimelineEvent.case_id == case_id)
        ).one()
        evidence_count = session.exec(
            select(func.count()).select_from(EvidenceItem).where(EvidenceItem.case_id == case_id)
        ).one()
        return case, {"timeline_count": timeline_count, "evidence_count": evidence_count}

    def evaluate(self, workspace_id: int, case_id: int) -> ReadinessReport:
        with self._session_factory() as session:
            case, ctx = self._gather_context(session, case_id)
            if case.workspace_id != workspace_id:
                raise ValueError("case not found")
            rules = self._rules.get(case.claim_type, [])
            required_weight = sum(rule.weight for rule in rules if rule.required)
            earned_required = 0
            missing = []
            recommended = []
            checks: list[MissingEvidenceCheck] = []
            for rule in rules:
                satisfied = rule.predicate(case, ctx)
                checks.append(
                    MissingEvidenceCheck(
                        case_id=case.id,
                        rule_key=rule.name,
                        description=rule.description,
                        required=rule.required,
                        satisfied=satisfied,
                    )
                )
                if rule.required:
                    if satisfied:
                        earned_required += rule.weight
                    else:
                        missing.append(rule.description)
                elif not satisfied:
                    recommended.append(rule.description)
            score = int(round((earned_required / required_weight) * 100)) if required_weight else 0
            blockers = missing.copy()
            if checks:
                session.add_all(checks)
            self._logger.info(
                "readiness evaluated",
                extra={"case_id": case_id, "claim_type": case.claim_type, "score": score},
            )
            return ReadinessReport(
                score=min(100, max(0, score)),
                missing=missing,
                recommended=recommended,
                blockers=blockers,
            )
