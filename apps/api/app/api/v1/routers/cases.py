from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.v1.deps import (
    get_case_service,
    get_current_workspace_member,
    require_workspace_role,
)
from app.models import WorkspaceMembership, WorkspaceRole
from app.models.claim import CaseStatus, ClaimType
from app.schemas.case import (
    CaseCreate,
    CaseRead,
    CaseTransitionRequest,
    CaseUpdate,
)
from app.services.case_service import CaseService, CaseServiceError

router = APIRouter(prefix="/cases", tags=["cases"])


def _handle_case_error(error: CaseServiceError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.detail)


@router.get("/", response_model=list[CaseRead])
def list_cases(
    workspace_member: WorkspaceMembership = Depends(get_current_workspace_member),
    case_service: CaseService = Depends(get_case_service),
    status: CaseStatus | None = Query(None),
    claim_type: ClaimType | None = Query(None),
    merchant_name: str | None = Query(None),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[CaseRead]:
    return case_service.list_cases(
        workspace_member.workspace_id,
        limit=limit,
        offset=offset,
        status=status,
        claim_type=claim_type,
        merchant_name=merchant_name,
    )


@router.get("/{case_id}", response_model=CaseRead)
def get_case(
    case_id: int,
    workspace_member: WorkspaceMembership = Depends(get_current_workspace_member),
    case_service: CaseService = Depends(get_case_service),
) -> CaseRead:
    try:
        return case_service.get_case(workspace_member.workspace_id, case_id)
    except CaseServiceError as error:
        raise _handle_case_error(error)


@router.post("/", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate,
    case_service: CaseService = Depends(get_case_service),
    workspace_member: WorkspaceMembership = Depends(
        require_workspace_role(WorkspaceRole.OWNER, WorkspaceRole.OPERATOR)
    ),
) -> CaseRead:
    return case_service.create_case(payload, workspace_member.workspace_id)


@router.patch("/{case_id}", response_model=CaseRead)
def update_case(
    case_id: int,
    payload: CaseUpdate,
    case_service: CaseService = Depends(get_case_service),
    workspace_member: WorkspaceMembership = Depends(
        require_workspace_role(WorkspaceRole.OWNER, WorkspaceRole.OPERATOR)
    ),
) -> CaseRead:
    try:
        return case_service.update_case(workspace_member.workspace_id, case_id, payload)
    except CaseServiceError as error:
        raise _handle_case_error(error)


@router.post("/{case_id}/transition", response_model=CaseRead)
def transition_case(
    case_id: int,
    payload: CaseTransitionRequest,
    case_service: CaseService = Depends(get_case_service),
    workspace_member: WorkspaceMembership = Depends(
        require_workspace_role(WorkspaceRole.OWNER, WorkspaceRole.OPERATOR)
    ),
) -> CaseRead:
    try:
        return case_service.transition_case(
            workspace_member.workspace_id,
            case_id,
            payload,
            actor_id=workspace_member.user_id,
        )
    except CaseServiceError as error:
        raise _handle_case_error(error)
