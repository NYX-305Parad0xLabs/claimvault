from dataclasses import dataclass

from .claim_service import ClaimService


@dataclass
class Services:
    claim_service: ClaimService
