from fastapi import APIRouter, Depends, status

from app.api.v1.deps import get_case_service
from app.schemas.case import CaseCreate, CaseRead
from app.services.case_service import CaseService

router = APIRouter(prefix="/claims", tags=["claims"])


@router.get("/", response_model=list[CaseRead])
def list_cases(case_service: CaseService = Depends(get_case_service)) -> list[CaseRead]:
    return case_service.list_cases()


@router.post("/", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate, case_service: CaseService = Depends(get_case_service)
) -> CaseRead:
    return case_service.create_case(payload)
