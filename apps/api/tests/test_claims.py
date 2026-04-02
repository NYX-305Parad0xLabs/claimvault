import pytest


async def register_and_login(async_client, email="ops@example.com", password="Sup3rSecret!") -> str:
    register_payload = {
        "email": email,
        "password": password,
        "full_name": "Ops User",
        "workspace_name": "Operations",
    }
    register_response = await async_client.post("/api/auth/register", json=register_payload)
    assert register_response.status_code == 201

    login_payload = {"email": email, "password": password}
    login_response = await async_client.post("/api/auth/login", json=login_payload)
    token = login_response.json()["access_token"]
    return token


@pytest.mark.asyncio
async def test_create_and_list_case(async_client):
    token = await register_and_login(async_client)
    headers = {"Authorization": f"Bearer {token}"}

    payload = {
        "title": "Return - faulty cable",
        "claim_type": "return",
        "summary": "Cable shorted upon delivery",
    }

    created = await async_client.post("/api/cases/", json=payload, headers=headers)
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == payload["title"]
    assert body["claim_type"] == payload["claim_type"]

    listed = await async_client.get("/api/cases/", headers=headers)
    assert listed.status_code == 200
    assert any(case["title"] == payload["title"] for case in listed.json())
