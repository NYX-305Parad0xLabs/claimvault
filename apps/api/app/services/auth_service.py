from __future__ import annotations

from datetime import datetime, timedelta
import logging
from typing import Any, Callable

from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import status
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from app.core.config import Settings
from app.models import (
    ActorType,
    AuditEvent,
    User,
    Workspace,
    WorkspaceMembership,
    WorkspaceRole,
)
from app.schemas.auth import LoginRequest, RegisterRequest


class AuthError(Exception):
    """Raised when authentication or registration fails."""

    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        super().__init__(detail)
        self.detail = detail
        self.status_code = status_code


class AuthService:
    def __init__(
        self, session_factory: Callable[[], Session], settings: Settings, logger: logging.Logger
    ) -> None:
        self._session_factory = session_factory
        self._settings = settings
        self._logger = logger
        self._pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

    def hash_password(self, password: str) -> str:
        return self._pwd_context.hash(password)

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        return self._pwd_context.verify(plain_password, hashed_password)

    def register_user(
        self, payload: RegisterRequest
    ) -> tuple[User, WorkspaceMembership, Workspace]:
        with self._session_factory() as session:
            existing = session.exec(select(User).where(User.email == payload.email)).first()
            if existing:
                raise AuthError("email already registered", status.HTTP_409_CONFLICT)

            user = User(
                email=payload.email,
                full_name=payload.full_name,
                hashed_password=self.hash_password(payload.password),
            )
            workspace = Workspace(name=payload.workspace_name)
            session.add(user)
            session.add(workspace)
            session.flush()

            membership = WorkspaceMembership(
                workspace_id=workspace.id,
                user_id=user.id,
                role=WorkspaceRole.OWNER,
            )
            session.add(membership)
            self._record_audit(
                session,
                actor_id=user.id,
                entity_type="user",
                action="register",
                metadata={"workspace_id": workspace.id},
            )
            try:
                session.commit()
            except IntegrityError as error:
                session.rollback()
                raise AuthError("workspace name already exists", status.HTTP_409_CONFLICT) from error
            session.refresh(user)
            session.refresh(workspace)
            session.refresh(membership)
            self._logger.info(
                "registered user",
                extra={
                    "user_id": user.id,
                    "workspace_id": workspace.id,
                    "role": membership.role.value,
                },
            )
            return user, membership, workspace

    def authenticate_user(self, payload: LoginRequest) -> tuple[User, WorkspaceMembership]:
        with self._session_factory() as session:
            user = session.exec(select(User).where(User.email == payload.email)).first()
            if not user or not self.verify_password(payload.password, user.hashed_password):
                raise AuthError("invalid credentials", status.HTTP_401_UNAUTHORIZED)

            statement = (
                select(WorkspaceMembership)
                .where(WorkspaceMembership.user_id == user.id)
                .order_by(WorkspaceMembership.id)
            )
            membership = session.exec(statement).first()
            if not membership:
                raise AuthError("workspace membership is required", status.HTTP_403_FORBIDDEN)

            self._record_audit(
                session,
                actor_id=user.id,
                entity_type="user",
                action="login",
                metadata={"workspace_id": membership.workspace_id},
            )
            session.commit()
            session.refresh(membership)
            self._logger.info("user authenticated", extra={"user_id": user.id})
            return user, membership

    def create_access_token(self, user_id: int, membership: WorkspaceMembership) -> str:
        expires_at = datetime.utcnow() + timedelta(minutes=self._settings.access_token_expire_minutes)
        payload = {
            "sub": str(user_id),
            "workspace_id": membership.workspace_id,
            "role": membership.role.value,
            "exp": expires_at,
        }
        token = jwt.encode(payload, self._settings.secret_key, algorithm=self._settings.token_algorithm)
        return token

    def decode_token(self, token: str) -> dict[str, str]:
        try:
            return jwt.decode(
                token,
                self._settings.secret_key,
                algorithms=[self._settings.token_algorithm],
            )
        except JWTError as error:
            raise AuthError("invalid authentication token", status.HTTP_401_UNAUTHORIZED) from error

    def get_user(self, user_id: int) -> User | None:
        with self._session_factory() as session:
            return session.get(User, user_id)

    def get_membership(self, user_id: int, workspace_id: int) -> WorkspaceMembership | None:
        with self._session_factory() as session:
            return session.exec(
                select(WorkspaceMembership).where(
                    WorkspaceMembership.user_id == user_id,
                    WorkspaceMembership.workspace_id == workspace_id,
                )
            ).first()

    def _record_audit(
        self,
        session: Session,
        actor_id: int,
        entity_type: str,
        action: str,
        metadata: dict[str, Any],
    ) -> None:
        event = AuditEvent(
            entity_type=entity_type,
            entity_id=actor_id,
            action=action,
            actor_type=ActorType.USER,
            actor_id=actor_id,
            metadata_json=metadata,
        )
        session.add(event)
