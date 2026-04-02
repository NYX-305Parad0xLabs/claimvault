from dataclasses import dataclass

from .auth_service import AuthService
from .case_service import CaseService


__all__ = ["AuthService", "CaseService", "Services"]


@dataclass
class Services:
    case_service: CaseService
    auth_service: AuthService
