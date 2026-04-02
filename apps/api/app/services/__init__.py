from dataclasses import dataclass

from .auth_service import AuthService
from .case_service import CaseService
from .evidence_service import EvidenceService
from .export_service import ExportService
from .readiness_service import ReadinessService
from .timeline_service import TimelineService


__all__ = [
    "AuthService",
    "CaseService",
    "EvidenceService",
    "ExportService",
    "TimelineService",
    "Services",
]


@dataclass
class Services:
    case_service: CaseService
    auth_service: AuthService
    evidence_service: EvidenceService
    export_service: ExportService
    timeline_service: TimelineService
    readiness_service: ReadinessService
