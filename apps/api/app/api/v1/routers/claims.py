from fastapi import APIRouter, Depends, status

from app.api.v1.deps import get_claim_service
from app.schemas.claim import ClaimCreate, ClaimRead
from app.services.claim_service import ClaimService

router = APIRouter(prefix="/claims", tags=["claims"])


@router.get("/", response_model=list[ClaimRead])
def list_claims(claim_service: ClaimService = Depends(get_claim_service)) -> list[ClaimRead]:
    return claim_service.list_claims()


@router.post("/", response_model=ClaimRead, status_code=status.HTTP_201_CREATED)
def create_claim(
    payload: ClaimCreate, claim_service: ClaimService = Depends(get_claim_service)
) -> ClaimRead:
    return claim_service.create_claim(payload)
