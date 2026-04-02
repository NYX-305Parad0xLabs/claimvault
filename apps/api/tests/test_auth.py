from __future__ import annotations

from httpx import AsyncClient
import pytest

from app.models import User, WorkspaceMembership, WorkspaceRole


async def register_user(async_client: AsyncClient, email: str, password: str) -> dict:
    payload = {
        "email": email,
        "password": password,
        "full_name": "Ops User",
        "workspace_name": "Claims Ops",
    }
    response = await async_client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_register_and_login(async_client: AsyncClient):
    email, password = "ops@example.com", "Op3rator!"
    await register_user(async_client, email, password)

    login_response = await async_client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]
    assert token

    me_response = await async_client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200
    assert me_response.json()["user"]["email"] == email


@pytest.mark.asyncio
async def test_login_invalid_credentials(async_client: AsyncClient):
    response = await async_client.post(
        "/api/auth/login", json={"email": "missing@example.com", "password": "wrongpass"}
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_unauthorized_access(async_client: AsyncClient):
    response = await async_client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_viewer_denied_on_case_creation(async_client: AsyncClient, app_instance):
    owner_email, owner_password = "owner@example.com", "Owner123!"
    registered = await register_user(async_client, owner_email, owner_password)
    workspace_id = registered["membership"]["workspace_id"]

    auth_service = app_instance.state.services.auth_service
    viewer_user = User(
        email="viewer@example.com",
        full_name="Viewer",
        hashed_password=auth_service.hash_password("Viewer123!"),
    )

    session_factory = app_instance.state.session_factory
    with session_factory() as session:
        session.add(viewer_user)
        session.flush()
        membership = WorkspaceMembership(
            workspace_id=workspace_id,
            user_id=viewer_user.id,
            role=WorkspaceRole.VIEWER,
        )
        session.add(membership)
        session.commit()

    login_response = await async_client.post(
        "/api/auth/login", json={"email": viewer_user.email, "password": "Viewer123!"}
    )
    token = login_response.json()["access_token"]

    payload = {"title": "Blocked case", "claim_type": "refund"}
    response = await async_client.post(
        "/api/cases/", json=payload, headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
