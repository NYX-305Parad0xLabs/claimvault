from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import (
    get_counterparty_service,
    get_current_workspace_member,
    require_workspace_role,
)
from app.models import WorkspaceMembership, WorkspaceRole
from app.schemas.counterparty import (
    CounterpartyProfileCreate,
    CounterpartyProfileRead,
    CounterpartyProfileUpdate,
)
from app.services.counterparty_service import CounterpartyService, CounterpartyServiceError

router = APIRouter(prefix="/counterparties", tags=["counterparties"])


def _handle_counterparty_error(error: CounterpartyServiceError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.detail)


@router.get("/", response_model=list[CounterpartyProfileRead])
def list_counterparties(
    workspace_member: WorkspaceMembership = Depends(get_current_workspace_member),
    counterparty_service: CounterpartyService = Depends(get_counterparty_service),
) -> list[CounterpartyProfileRead]:
    return counterparty_service.list_profiles(workspace_member.workspace_id)


@router.post(
    "/",
    response_model=CounterpartyProfileRead,
    status_code=status.HTTP_201_CREATED,
)
def create_counterparty(
    payload: CounterpartyProfileCreate,
    workspace_member: WorkspaceMembership = Depends(
        require_workspace_role(WorkspaceRole.OWNER, WorkspaceRole.OPERATOR)
    ),
    counterparty_service: CounterpartyService = Depends(get_counterparty_service),
) -> CounterpartyProfileRead:
    try:
        return counterparty_service.create_profile(workspace_member.workspace_id, payload)
    except CounterpartyServiceError as error:
        raise _handle_counterparty_error(error)


@router.get("/{profile_id}", response_model=CounterpartyProfileRead)
def get_counterparty(
    profile_id: int,
    workspace_member: WorkspaceMembership = Depends(get_current_workspace_member),
    counterparty_service: CounterpartyService = Depends(get_counterparty_service),
) -> CounterpartyProfileRead:
    try:
        return counterparty_service.get_profile(workspace_member.workspace_id, profile_id)
    except CounterpartyServiceError as error:
        raise _handle_counterparty_error(error)


@router.patch("/{profile_id}", response_model=CounterpartyProfileRead)
def update_counterparty(
    profile_id: int,
    payload: CounterpartyProfileUpdate,
    workspace_member: WorkspaceMembership = Depends(
        require_workspace_role(WorkspaceRole.OWNER, WorkspaceRole.OPERATOR)
    ),
    counterparty_service: CounterpartyService = Depends(get_counterparty_service),
) -> CounterpartyProfileRead:
    try:
        return counterparty_service.update_profile(
            workspace_member.workspace_id,
            profile_id,
            payload,
        )
    except CounterpartyServiceError as error:
        raise _handle_counterparty_error(error)
