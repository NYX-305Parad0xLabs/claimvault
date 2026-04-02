from dataclasses import dataclass
from typing import Iterable, Mapping

from app.models.claim import ClaimType


@dataclass(frozen=True)
class WorkflowTaskDefinition:
    key: str
    title: str
    description: str
    priority: int


@dataclass(frozen=True)
class WorkflowPack:
    claim_type: ClaimType
    name: str
    summary: str
    why_chosen: str
    export_focus: str
    tasks: tuple[WorkflowTaskDefinition, ...]


_PACKS: Mapping[ClaimType, WorkflowPack] = {
    ClaimType.REFUND: WorkflowPack(
        claim_type=ClaimType.REFUND,
        name="Refund pack",
        summary="Build airtight returns and refund cases with merchant proof, order context, and timeline clarity.",
        why_chosen="Refunds are the highest-frequency workflow with clear rules for evidence and timeline capture.",
        export_focus="Highlight purchase details, resolution attempts, and the current refund ask.",
        tasks=(
            WorkflowTaskDefinition(
                key="order_reference",
                title="Capture the order reference",
                description="The merchant needs your order number to look up the transaction.",
                priority=1,
            ),
            WorkflowTaskDefinition(
                key="merchant",
                title="Record the merchant name",
                description="Document who sold the item so the refund request is routed correctly.",
                priority=1,
            ),
            WorkflowTaskDefinition(
                key="receipt",
                title="Upload a receipt or order document",
                description="Add proof of purchase such as an invoice, receipt, or confirmation email.",
                priority=2,
            ),
            WorkflowTaskDefinition(
                key="timeline_event",
                title="Log at least one timeline entry",
                description="Capture when the damage, mis-shipment, or refund request happened.",
                priority=3,
            ),
        ),
    ),
    ClaimType.RENTAL_DEPOSIT: WorkflowPack(
        claim_type=ClaimType.RENTAL_DEPOSIT,
        name="Rental deposit pack",
        summary="Document tenancy details, condition evidence, and communication so deposit disputes stand up to scrutiny.",
        why_chosen="Rental deposit disputes require curated photo evidence and timeline proof that differ from standard refunds.",
        export_focus="Emphasize tenancy window, condition reports, and any disputed deductions.",
        tasks=(
            WorkflowTaskDefinition(
                key="inspection_notes",
                title="Log move-in/out inspections",
                description="Record the condition notes from both the start and end of the tenancy.",
                priority=1,
            ),
            WorkflowTaskDefinition(
                key="damage_photos",
                title="Add condition or damage photos",
                description="Capture high-quality photos of any contested damages or repairs.",
                priority=1,
            ),
            WorkflowTaskDefinition(
                key="communication_log",
                title="Summarize landlord communications",
                description="Document notices, repair requests, or policy references in the summary.",
                priority=2,
            ),
        ),
    ),
}


def get_pack(claim_type: ClaimType) -> WorkflowPack | None:
    return _PACKS.get(claim_type)


def all_packs() -> Iterable[WorkflowPack]:
    return _PACKS.values()
