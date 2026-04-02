from __future__ import annotations

from datetime import datetime
from typing import Callable, Sequence

from app.models.claim import (
    Case,
    ClaimType,
    CounterpartyProfile,
    EvidenceItem,
    TimelineEvent,
)
from app.schemas.readiness import ReadinessReport
from app.workflow.packs import WorkflowPack


class CaseSummaryBuilder:
    def build_summary(
        self,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
        readiness: ReadinessReport,
        counterparty: CounterpartyProfile | None,
        workflow_pack: WorkflowPack | None,
    ) -> str:
        sorted_timeline = self._sort_timeline(timeline)
        lines: list[str] = [
            f"# ClaimVault Case summary — {case.title}",
            "",
            "## Case details",
            f"- Claim ID: {case.id}",
            f"- Claim type: {case.claim_type.value}",
            f"- Status: {case.status.value}",
            f"- Merchant: {case.merchant_name or 'Unrecorded merchant'}",
            f"- Counterparty: {case.counterparty_name or 'Not recorded'}",
            f"- Order reference: {case.order_reference or 'Not captured'}",
            f"- Amount: {case.amount_value} {case.amount_currency}",
            f"- Purchase date: {self._format_date(case.purchase_date)}",
            f"- Incident date: {self._format_date(case.incident_date)}",
            f"- Due date: {self._format_date(case.due_date)}",
            "",
            "## Narrative",
            case.summary or "No narrative recorded yet.",
        ]
        lines.extend(self._render_counterparty_section(case, counterparty))
        lines.extend(self._render_readiness_section(readiness))
        if workflow_pack:
            lines.extend(
                [
                    "",
                    "## Workflow pack",
                    f"- Pack: {workflow_pack.name}",
                    f"- Focus: {workflow_pack.summary}",
                    f"- Export tone: {workflow_pack.export_focus}",
                    f"- Why chosen: {workflow_pack.why_chosen}",
                ]
            )
        lines.extend(self._render_claim_section(case, evidence, sorted_timeline, readiness, counterparty))
        lines.extend(self._render_evidence_section(evidence))
        lines.extend(self._render_timeline_section(sorted_timeline))
        lines.extend(
            [
                "",
                "## Export notes",
                "- Timeline entries and evidence filenames are preserved in export bundles.",
                "- This summary is deterministic and reflects the current readiness state.",
            ]
        )
        return "\n".join(lines)

    def _render_counterparty_section(
        self,
        case: Case,
        counterparty: CounterpartyProfile | None,
    ) -> list[str]:
        lines = ["", "## Counterparty context"]
        if counterparty:
            lines.extend(
                [
                    f"- Name: {counterparty.name}",
                    f"- Type: {counterparty.profile_type.value}",
                    f"- Website: {counterparty.website or 'Not provided'}",
                    f"- Support email: {counterparty.support_email or 'Not provided'}",
                    f"- Support URL: {counterparty.support_url or 'Not provided'}",
                    f"- Notes: {counterparty.notes or 'No additional notes'}",
                ]
            )
        else:
            lines.extend(
                [
                    f"- Manual entry: {case.counterparty_name or 'Not recorded'}",
                    "- Add a counterparty profile to capture verified support details.",
                ]
            )
        return lines

    def _render_readiness_section(self, readiness: ReadinessReport) -> list[str]:
        lines = [
            "",
            "## Readiness check",
            f"- Score: {readiness.score}/100",
        ]
        lines.append(
            "- Blockers:"
            if readiness.blockers
            else "- Blockers: none identified"
        )
        if readiness.blockers:
            for blocker in readiness.blockers:
                lines.append(f"  - {blocker}")
        lines.append(
            "- Missing required items:"
            if readiness.missing
            else "- Missing required items: none"
        )
        if readiness.missing:
            for item in readiness.missing:
                lines.append(f"  - {item}")
        lines.append(
            "- Recommended enhancements:"
            if readiness.recommended
            else "- Recommended enhancements: none"
        )
        if readiness.recommended:
            for item in readiness.recommended:
                lines.append(f"  - {item}")
        return lines

    def _render_claim_section(
        self,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
        readiness: ReadinessReport,
        counterparty: CounterpartyProfile | None,
    ) -> list[str]:
        renderer = self._claim_renderers().get(
            case.claim_type,
            self._default_claim_section,
        )
        return renderer(case, evidence, timeline, readiness, counterparty)

    @staticmethod
    def _sort_timeline(events: Sequence[TimelineEvent]) -> list[TimelineEvent]:
        return sorted(events, key=lambda event: (event.happened_at, event.id or 0))

    @staticmethod
    def _format_date(value: datetime | None) -> str:
        if not value:
            return "Not recorded"
        return value.date().isoformat()

    @staticmethod
    def _latest_timeline_event(events: Sequence[TimelineEvent]) -> str:
        if not events:
            return "No timeline entries yet."
        latest = events[-1]
        body = (latest.body or "").replace("\n", " ").strip()
        return body or "Latest event has no summary."

    @staticmethod
    def _format_evidence_kinds(evidence: Sequence[EvidenceItem]) -> str:
        kinds = {
            getattr(item.kind, "value", item.kind) if hasattr(item.kind, "value") else item.kind
            for item in evidence
        }
        if not kinds:
            return "None recorded"
        return ", ".join(sorted(str(kind) for kind in kinds))

    def _claim_renderers(
        self,
    ) -> dict[
        ClaimType,
        Callable[
            [Case, Sequence[EvidenceItem], Sequence[TimelineEvent], ReadinessReport, CounterpartyProfile | None],
            list[str],
        ],
    ]:
        return {
            ClaimType.REFUND: self._render_refund_section,
            ClaimType.WARRANTY: self._render_warranty_section,
            ClaimType.CHARGEBACK_PREP: self._render_chargeback_section,
            ClaimType.SHIPMENT_DAMAGE: self._render_shipment_section,
            ClaimType.RENTAL_DEPOSIT: self._render_rental_section,
        }

    def _render_refund_section(
        self,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
        readiness: ReadinessReport,
        counterparty: CounterpartyProfile | None,
    ) -> list[str]:
        merchant_label = case.merchant_name or case.counterparty_name or "Unknown merchant"
        highlight = self._latest_timeline_event(timeline)
        lines = [
            "",
            "## Refund focus",
            f"- Issue and ask: {case.summary or 'Describe the refund or return request'}",
            f"- Merchant: {merchant_label}",
            f"- Order reference: {case.order_reference or 'Not recorded'}",
            f"- Purchase date: {self._format_date(case.purchase_date)}",
            f"- Amount: {case.amount_value} {case.amount_currency}",
            f"- Evidence types: {self._format_evidence_kinds(evidence)}",
            f"- Timeline highlight: {highlight}",
        ]
        return lines

    def _render_warranty_section(
        self,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
        readiness: ReadinessReport,
        counterparty: CounterpartyProfile | None,
    ) -> list[str]:
        provider = counterparty.name if counterparty else case.merchant_name or "Manufacturer unknown"
        highlight = self._latest_timeline_event(timeline)
        lines = [
            "",
            "## Warranty focus",
            f"- Product owner: {provider}",
            f"- Purchase date: {self._format_date(case.purchase_date)}",
            f"- Incident summary: {case.summary or 'Detail the failure or defect symptoms'}",
            f"- Evidence types: {self._format_evidence_kinds(evidence)}",
            f"- Timeline highlight: {highlight}",
        ]
        return lines

    def _render_chargeback_section(
        self,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
        readiness: ReadinessReport,
        counterparty: CounterpartyProfile | None,
    ) -> list[str]:
        highlight = self._latest_timeline_event(timeline)
        lines = [
            "",
            "## Chargeback prep focus",
            f"- Merchant: {case.merchant_name or 'Unknown merchant'}",
            f"- Order reference / amount: {case.order_reference or 'Not set'} / {case.amount_value} {case.amount_currency}",
            f"- Incident date: {self._format_date(case.incident_date)}",
            f"- Evidence types: {self._format_evidence_kinds(evidence)}",
            f"- Timeline highlight: {highlight}",
        ]
        return lines

    def _render_shipment_section(
        self,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
        readiness: ReadinessReport,
        counterparty: CounterpartyProfile | None,
    ) -> list[str]:
        carrier_label = counterparty.name if counterparty else case.counterparty_name or case.merchant_name or "Carrier unknown"
        highlight = self._latest_timeline_event(timeline)
        lines = [
            "",
            "## Shipment damage focus",
            f"- Carrier / platform: {carrier_label}",
            f"- Incident date: {self._format_date(case.incident_date)}",
            f"- Delivery window ends: {self._format_date(case.due_date)}",
            "- Highlight tracking updates, delivery timing, and damage photos.",
            f"- Evidence types: {self._format_evidence_kinds(evidence)}",
            f"- Timeline highlight: {highlight}",
        ]
        return lines

    def _render_rental_section(
        self,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
        readiness: ReadinessReport,
        counterparty: CounterpartyProfile | None,
    ) -> list[str]:
        landlord_label = counterparty.name if counterparty else case.counterparty_name or "Landlord not set"
        tenancy_window = (
            f"{self._format_date(case.purchase_date)} -> {self._format_date(case.incident_date or case.due_date)}"
        )
        lines = [
            "",
            "## Rental deposit focus",
            f"- Landlord / property: {landlord_label}",
            f"- Tenancy window: {tenancy_window}",
            f"- Dispute summary: {case.summary or 'Describe the condition, deductions, or notices'}",
            "- Include lease notices, move-out photos, condition evidence, and receipts.",
            f"- Timeline highlight: {self._latest_timeline_event(timeline)}",
            f"- Evidence types: {self._format_evidence_kinds(evidence)}",
        ]
        return lines

    def _default_claim_section(
        self,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
        readiness: ReadinessReport,
        counterparty: CounterpartyProfile | None,
    ) -> list[str]:
        return [
            "",
            "## Claim focus",
            f"- Narrative: {case.summary or 'Capture the story here.'}",
            f"- Timeline highlight: {self._latest_timeline_event(timeline)}",
            f"- Evidence kinds: {self._format_evidence_kinds(evidence)}",
        ]

    def _render_evidence_section(self, evidence: Sequence[EvidenceItem]) -> list[str]:
        relevant = sum(1 for item in evidence if getattr(item, "manual_relevance", False))
        lines = [
            "",
            "## Evidence snapshot",
            f"- Files captured: {len(evidence)}",
            f"- File types: {self._format_evidence_kinds(evidence)}",
        ]
        if relevant:
            lines.append(f"- Manual relevance flags: {relevant}")
        return lines

    def _render_timeline_section(self, timeline: Sequence[TimelineEvent]) -> list[str]:
        return [
            "",
            "## Timeline snapshot",
            f"- Events recorded: {len(timeline)}",
            f"- Latest entry: {self._latest_timeline_event(timeline)}",
        ]
