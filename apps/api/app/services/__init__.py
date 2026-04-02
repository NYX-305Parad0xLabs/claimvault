from dataclasses import dataclass

from .audit_service import AuditService
from .auth_service import AuthService
from .case_service import CaseService
from .evidence_service import EvidenceService
from .export_service import ExportService
from .readiness_service import ReadinessService
from .timeline_service import TimelineService


__all__ = [
    "AuditService",
    "AuthService",
    "CaseService",
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
