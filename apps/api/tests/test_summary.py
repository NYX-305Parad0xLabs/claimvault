import uuid

import pytest


async def _auth_headers(async_client):
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "email": f"summary-{suffix}@example.com",
        "password": f"Pass!{suffix}",
        "full_name": "Summary User",
        "workspace_name": f"Summary-{suffix}",
    }
    response = await async_client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    login = await async_client.post(
        "/api/auth/login", json={"email": payload["email"], "password": payload["password"]}
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_case(async_client, headers, claim_type="refund"):
    payload = {
        "title": "Summary previewing",
        "claim_type": claim_type,
        "summary": "Summary ready for the template",
        "merchant_name": "Store",
        "order_reference": "ORD-99",
        "amount_value": 200.0,
    }
    response = await async_client.post("/api/cases/", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_summary_preview_returns_refund_template(async_client):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers, claim_type="refund")
    response = await async_client.get(
        f"/api/cases/{case['id']}/summary-preview", headers=headers
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["claim_type"] == "refund"
    assert "## Refund focus" in payload["summary"]


@pytest.mark.asyncio
async def test_summary_preview_includes_warranty_section(async_client):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers, claim_type="warranty")
    response = await async_client.get(
        f"/api/cases/{case['id']}/summary-preview", headers=headers
    )
    assert response.status_code == 200
    payload = response.json()
    assert "## Warranty focus" in payload["summary"]
