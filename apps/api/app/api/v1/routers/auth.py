from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.deps import (
    get_auth_service,
    get_current_user,
    get_current_workspace_member,
)
from app.models import User, WorkspaceMembership
from app.schemas.auth import LoginRequest, MeResponse, MembershipRead, RegisterRequest, TokenResponse, UserRead
from app.services.auth_service import AuthError, AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=MeResponse, status_code=status.HTTP_201_CREATED)
def register(
    payload: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> MeResponse:
    try:
        user, membership, _workspace = auth_service.register_user(payload)
    except AuthError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail)

    return MeResponse(
        user=UserRead.model_validate(user),
        membership=MembershipRead(workspace_id=membership.workspace_id, role=membership.role),
    )


@router.post("/login", response_model=TokenResponse)
def login(
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    try:
        user, membership = auth_service.authenticate_user(payload)
    except AuthError as error:
        raise HTTPException(status_code=error.status_code, detail=error.detail)

    token = auth_service.create_access_token(user.id, membership)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=MeResponse)
def me(
    user: User = Depends(get_current_user),
    membership: WorkspaceMembership = Depends(get_current_workspace_member),
) -> MeResponse:
    return MeResponse(
        user=UserRead.model_validate(user),
        membership=MembershipRead(workspace_id=membership.workspace_id, role=membership.role),
    )
