from dataclasses import dataclass

from .auth_service import AuthService
from .case_service import CaseService
from .evidence_service import EvidenceService


__all__ = ["AuthService", "CaseService", "Services"]


@dataclass
class Services:
    case_service: CaseService
    auth_service: AuthService
    evidence_service: EvidenceService
