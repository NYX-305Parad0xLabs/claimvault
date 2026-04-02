from __future__ import annotations

from typing import Callable, Generator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session

from app.models import User, WorkspaceMembership, WorkspaceRole
from app.services import AuthService, CaseService, EvidenceService, Services
from app.services.auth_service import AuthError

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_session(request: Request) -> Generator[Session, None, None]:
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        yield session


def get_services(request: Request) -> Services:
    return request.app.state.services


def get_case_service(services: Services = Depends(get_services)) -> CaseService:
    return services.case_service


def get_auth_service(services: Services = Depends(get_services)) -> AuthService:
    return services.auth_service


def get_evidence_service(services: Services = Depends(get_services)) -> EvidenceService:
    return services.evidence_service


def _unauthorized(detail: str = "Unauthorized") -> HTTPException:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    try:
        payload = auth_service.decode_token(token)
    except AuthError as error:
        raise _unauthorized(error.detail) from error

    user_id = payload.get("sub")
    workspace_id = payload.get("workspace_id")
    if user_id is None or workspace_id is None:
        raise _unauthorized()

    user = auth_service.get_user(int(user_id))
    if not user:
        raise _unauthorized("user not found")

    return user


def get_current_workspace_member(
    token: str = Depends(oauth2_scheme),
    auth_service: AuthService = Depends(get_auth_service),
) -> WorkspaceMembership:
    try:
        payload = auth_service.decode_token(token)
    except AuthError as error:
        raise _unauthorized(error.detail) from error

    user_id = payload.get("sub")
    workspace_id = payload.get("workspace_id")
    if user_id is None or workspace_id is None:
        raise _unauthorized()

    membership = auth_service.get_membership(int(user_id), int(workspace_id))
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="workspace membership required",
        )

    return membership


def require_workspace_role(
    *allowed_roles: WorkspaceRole,
) -> Callable[[WorkspaceMembership], WorkspaceMembership]:
    def guard_member(
        member: WorkspaceMembership = Depends(get_current_workspace_member),
    ) -> WorkspaceMembership:
        if member.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="insufficient workspace role",
            )
        return member

    return guard_member
