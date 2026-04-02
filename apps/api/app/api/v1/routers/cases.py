from fastapi import APIRouter, Depends, status

from app.api.v1.deps import (
    get_case_service,
    get_current_workspace_member,
    require_workspace_role,
)
from app.models import WorkspaceMembership, WorkspaceRole
from app.schemas.case import CaseCreate, CaseRead
from app.services.case_service import CaseService

router = APIRouter(prefix="/cases", tags=["cases"])


@router.get("/", response_model=list[CaseRead])
def list_cases(
    workspace_member: WorkspaceMembership = Depends(get_current_workspace_member),
    case_service: CaseService = Depends(get_case_service),
) -> list[CaseRead]:
    return case_service.list_cases(workspace_member.workspace_id)


@router.post("/", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate,
    case_service: CaseService = Depends(get_case_service),
    workspace_member: WorkspaceMembership = Depends(
        require_workspace_role(WorkspaceRole.OWNER, WorkspaceRole.OPERATOR)
    ),
) -> CaseRead:
    return case_service.create_case(payload, workspace_member.workspace_id)
