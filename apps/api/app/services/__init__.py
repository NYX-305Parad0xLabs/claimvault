from dataclasses import dataclass

from .case_service import CaseService


__all__ = ["CaseService", "Services"]


@dataclass
class Services:
    case_service: CaseService
