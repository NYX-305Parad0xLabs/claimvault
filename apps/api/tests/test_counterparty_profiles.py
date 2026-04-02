import uuid

import pytest

async def _auth_headers(async_client):
    suffix = uuid.uuid4().hex[:8]
    email = f"user-{suffix}@example.com"
    password = f"Pass!{suffix}"
    payload = {
        "email": email,
        "password": password,
        "full_name": "Ops User",
        "workspace_name": f"Ops-{suffix}",
    }
    register = await async_client.post("/api/auth/register", json=payload)
    assert register.status_code == 201

    login = await async_client.post("/api/auth/login", json={"email": email, "password": password})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_case(async_client, headers, title="Return - faulty cable"):
    payload = {
        "title": title,
        "claim_type": "refund",
        "summary": "Cable shorted upon delivery",
    }
    response = await async_client.post("/api/cases/", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


async def _create_profile(async_client, headers, name="Supplier"):
    payload = {
        "name": name,
        "profile_type": "merchant",
        "website": "https://merchant.example",
        "support_email": "ops@example.com",
        "support_url": "https://merchant.example/support",
        "notes": "Preferred partner",
    }
    response = await async_client.post("/api/counterparties/", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_counterparty_profile_lifecycle(async_client):
    headers = await _auth_headers(async_client)
    profile = await _create_profile(async_client, headers, name="Merchant Ops")
    profile_id = profile["id"]

    listed = await async_client.get("/api/counterparties/", headers=headers)
    assert listed.status_code == 200
    assert any(entry["id"] == profile_id for entry in listed.json())

    detail = await async_client.get(f"/api/counterparties/{profile_id}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["name"] == "Merchant Ops"

    updated = await async_client.patch(
        f"/api/counterparties/{profile_id}",
        json={"notes": "Updated notes"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["notes"] == "Updated notes"

    case = await _create_case(async_client, headers)
    case_id = case["id"]
    patched = await async_client.patch(
        f"/api/cases/{case_id}",
        json={
            "counterparty_profile_id": profile_id,
            "counterparty_name": profile["name"],
        },
        headers=headers,
    )
    assert patched.status_code == 200
    assert patched.json()["counterparty_profile"]["id"] == profile_id
    assert patched.json()["counterparty_name"] == profile["name"]


@pytest.mark.asyncio
async def test_counterparty_profile_workspace_isolation(async_client):
    headers = await _auth_headers(async_client)
    profile = await _create_profile(async_client, headers, name="Isolated Merchant")

    other_headers = await _auth_headers(async_client)
    restricted = await async_client.get(
        f"/api/counterparties/{profile['id']}", headers=other_headers
    )
    assert restricted.status_code == 404

    blocked_patch = await async_client.patch(
        f"/api/counterparties/{profile['id']}",
        json={"notes": "Should fail"},
        headers=other_headers,
    )
    assert blocked_patch.status_code == 404
