from dataclasses import dataclass

from .audit_service import AuditService
from .auth_service import AuthService
from .case_service import CaseService
from .case_lifecycle_service import CaseLifecycleService
from .case_summary_service import CaseSummaryService
from .evidence_service import EvidenceService
from .export_service import ExportService
from .readiness_service import ReadinessService
from .timeline_service import TimelineService
from .case_assistant_service import CaseAssistantService


__all__ = [
    "AuditService",
    "AuthService",
    "CaseLifecycleService",
    "CaseService",
    "CaseSummaryService",
    "EvidenceService",
    "ExportService",
    "TimelineService",
    "Services",
]


@dataclass
class Services:
    audit_service: AuditService
    case_service: CaseService
    auth_service: AuthService
    evidence_service: EvidenceService
    export_service: ExportService
    timeline_service: TimelineService
    readiness_service: ReadinessService
    summary_service: CaseSummaryService
    assistant_service: CaseAssistantService
    lifecycle_service: CaseLifecycleService
