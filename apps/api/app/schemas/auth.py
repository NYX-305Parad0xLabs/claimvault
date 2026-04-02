from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, EmailStr, Field

from app.models import WorkspaceRole


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    workspace_name: str = Field(min_length=3)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = Field(default="bearer")


class UserRead(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    created_at: datetime

    class Config:
        from_attributes = True


class MembershipRead(BaseModel):
    workspace_id: int
    role: WorkspaceRole


class MeResponse(BaseModel):
    user: UserRead
    membership: MembershipRead
