from __future__ import annotations

from datetime import datetime
from typing import Callable, Sequence

from app.models.claim import ClaimType, Case, EvidenceItem, TimelineEvent


class CaseSummaryBuilder:
    def build_summary(
        self,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
    ) -> str:
        sorted_timeline = self._sort_timeline(timeline)
        evidence_count = len(evidence)
        timeline_count = len(sorted_timeline)
        lines: list[str] = [
            f"# Case Export: {case.title}",
            "",
            f"- Claim ID: {case.id}",
            f"- Claim Type: {case.claim_type.value}",
            f"- Status: {case.status.value}",
            f"- Merchant: {case.merchant_name or 'N/A'}",
            f"- Counterparty: {case.counterparty_name or 'N/A'}",
            f"- Order Reference: {case.order_reference or 'N/A'}",
            f"- Amount: {case.amount_value} {case.amount_currency}",
            f"- Purchase Date: {self._format_date(case.purchase_date)}",
            f"- Incident Date: {self._format_date(case.incident_date)}",
            f"- Due Date: {self._format_date(case.due_date)}",
            f"- Evidence Pieces: {evidence_count}",
            f"- Timeline Events: {timeline_count}",
            "",
            "## Summary",
            case.summary or "No summary provided.",
            "",
        ]
        lines.extend(self._render_claim_section(case, evidence, sorted_timeline))
        lines.extend(self._render_evidence_section(evidence))
        lines.extend(self._render_timeline_section(sorted_timeline))
        lines.extend(
            [
                "",
                "## Export Notes",
                "- Timeline entries are ordered chronologically in the exported bundle.",
                "- Evidence files live in the `evidence/` folder with sanitized filenames.",
            ]
        )
        return "\n".join(lines)

    def _render_claim_section(
        self,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
    ) -> list[str]:
        renderer = self._claim_renderers().get(case.claim_type, self._default_claim_section)
        return renderer(case, evidence, timeline)

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

    @staticmethod
    def _format_timeline_intro(events: Sequence[TimelineEvent]) -> str:
        return f"Latest entry: {CaseSummaryBuilder._latest_timeline_event(events)}"

    def _claim_renderers(
        self,
    ) -> dict[
        ClaimType,
        Callable[[Case, Sequence[EvidenceItem], Sequence[TimelineEvent]], list[str]],
    ]:
        return {
            ClaimType.REFUND: CaseSummaryBuilder._render_refund_section,
            ClaimType.WARRANTY: CaseSummaryBuilder._render_warranty_section,
            ClaimType.CHARGEBACK_PREP: CaseSummaryBuilder._render_chargeback_section,
            ClaimType.SHIPMENT_DAMAGE: CaseSummaryBuilder._render_shipment_section,
            ClaimType.RENTAL_DEPOSIT: CaseSummaryBuilder._render_rental_section,
        }

    @classmethod
    def _render_refund_section(
        cls,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
    ) -> list[str]:
        return [
            "## Refund focus",
            f"- Issue & ask: {case.summary or 'Describe the refund or return request'}",
            f"- Merchant: {case.merchant_name or 'Unknown'}",
            f"- Order reference: {case.order_reference or 'Not recorded'}",
            f"- Purchase date: {cls._format_date(case.purchase_date)}",
            f"- Amount: {case.amount_value} {case.amount_currency}",
            f"- Evidence types captured: {cls._format_evidence_kinds(evidence)}",
            f"- Timeline highlight: {cls._latest_timeline_event(timeline)}",
        ]

    @classmethod
    def _render_warranty_section(
        cls,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
    ) -> list[str]:
        return [
            "## Warranty focus",
            f"- Product / merchant: {case.merchant_name or case.counterparty_name or 'Unknown'}",
            f"- Purchase date: {cls._format_date(case.purchase_date)}",
            f"- Incident summary: {case.summary or 'Describe the warranty failure'}",
            "- Supporting invoice, receipt, or photo strengthens the request.",
            f"- Evidence kinds: {cls._format_evidence_kinds(evidence)}",
        ]

    @classmethod
    def _render_chargeback_section(
        cls,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
    ) -> list[str]:
        return [
            "## Chargeback prep focus",
            f"- Merchant: {case.merchant_name or 'Unknown'}",
            f"- Order reference / amount: {case.order_reference or 'TBD'} - {case.amount_value} {case.amount_currency}",
            f"- Incident date: {cls._format_date(case.incident_date)}",
            f"- Timeline highlight: {cls._latest_timeline_event(timeline)}",
            "- Document proof of attempted resolution (messages, emails, receipts).",
        ]

    @classmethod
    def _render_shipment_section(
        cls,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
    ) -> list[str]:
        return [
            "## Shipment damage focus",
            f"- Carrier / platform: {case.counterparty_name or case.merchant_name or 'TBD'}",
            f"- Incident date: {cls._format_date(case.incident_date)}",
            f"- Expected delivery window closes: {cls._format_date(case.due_date)}",
            "- Highlight tracking updates, delivery timing, and damage photos.",
            f"- Evidence kinds: {cls._format_evidence_kinds(evidence)}",
        ]

    @classmethod
    def _render_rental_section(
        cls,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
    ) -> list[str]:
        tenancy_window = (
            f"{cls._format_date(case.purchase_date)} -> {cls._format_date(case.incident_date or case.due_date)}"
        )
        return [
            "## Rental deposit focus",
            f"- Landlord / property: {case.counterparty_name or case.merchant_name or 'Unknown'}",
            f"- Tenancy window: {tenancy_window}",
            f"- Dispute summary: {case.summary or 'Describe the condition, deductions, or notices'}",
            "- Include lease notices, move-out photos, condition evidence, and receipts.",
            f"- Evidence kinds: {cls._format_evidence_kinds(evidence)}",
        ]

    @classmethod
    def _default_claim_section(
        cls,
        case: Case,
        evidence: Sequence[EvidenceItem],
        timeline: Sequence[TimelineEvent],
    ) -> list[str]:
        return [
            "## Claim focus",
            f"- Narrative: {case.summary or 'Capture the story here.'}",
            f"- Timeline highlight: {cls._latest_timeline_event(timeline)}",
            f"- Evidence kinds: {cls._format_evidence_kinds(evidence)}",
        ]

    @classmethod
    def _render_evidence_section(cls, evidence: Sequence[EvidenceItem]) -> list[str]:
        return [
            "",
            "## Evidence snapshot",
            f"- Total files: {len(evidence)}",
            f"- File types: {cls._format_evidence_kinds(evidence)}",
        ]

    @classmethod
    def _render_timeline_section(cls, timeline: Sequence[TimelineEvent]) -> list[str]:
        return [
            "",
            "## Timeline snapshot",
            f"- Events recorded: {len(timeline)}",
            f"- {cls._format_timeline_intro(timeline)}",
        ]
