from dataclasses import dataclass

from .auth_service import AuthService
from .case_service import CaseService
from .evidence_service import EvidenceService
from .timeline_service import TimelineService


__all__ = ["AuthService", "CaseService", "EvidenceService", "TimelineService", "Services"]


@dataclass
class Services:
    case_service: CaseService
    auth_service: AuthService
    evidence_service: EvidenceService
    timeline_service: TimelineService
