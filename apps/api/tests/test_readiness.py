import uuid
from datetime import datetime

import pytest


async def _auth_headers(async_client):
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "email": f"user-{suffix}@example.com",
        "password": f"Pass!{suffix}",
        "full_name": "Ops User",
        "workspace_name": f"Ops-{suffix}",
    }
    register = await async_client.post("/api/auth/register", json=payload)
    assert register.status_code == 201
    login = await async_client.post(
        "/api/auth/login", json={"email": payload["email"], "password": payload["password"]}
    )
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_case(async_client, headers, claim_type, **extras):
    payload = {
        "title": "Readiness case",
        "claim_type": claim_type,
        "summary": extras.get("summary", "Initial summary"),
        "merchant_name": extras.get("merchant_name"),
        "order_reference": extras.get("order_reference"),
        "amount_value": extras.get("amount_value", 0),
        "purchase_date": extras.get("purchase_date"),
    }
    response = await async_client.post("/api/cases/", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


async def _add_timeline(async_client, case_id, headers, event_type="note"):
    resp = await async_client.post(
        f"/api/cases/{case_id}/timeline-events",
        json={"body": "Timeline entry", "event_type": event_type},
        headers=headers,
    )
    assert resp.status_code == 201


async def _upload_evidence(async_client, case_id, headers):
    resp = await async_client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("doc.pdf", b"%PDF", "application/pdf")},
        headers=headers,
    )
    assert resp.status_code == 201


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("claim_type", "extras"),
    [
        ("return", {"merchant_name": "Shop", "order_reference": "ORD-1"}),
        ("dispute", {"merchant_name": "Shop", "amount_value": 100}),
        ("warranty", {"order_reference": "ORD-2", "purchase_date": datetime.utcnow().isoformat()}),
    ],
)
async def test_readiness_complete(async_client, claim_type, extras):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers, claim_type, **extras)
    case_id = case["id"]
    await _upload_evidence(async_client, case_id, headers)
    await _add_timeline(async_client, case_id, headers)

    resp = await async_client.get(f"/api/cases/{case_id}/readiness", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["score"] == 100
    assert data["missing"] == []
    assert data["blockers"] == []


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("claim_type", "setup"),
    [
        ("return", {}),
        ("dispute", {}),
        ("warranty", {}),
    ],
)
async def test_readiness_incomplete(async_client, claim_type, setup):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers, claim_type)
    case_id = case["id"]

    resp = await async_client.get(f"/api/cases/{case_id}/readiness", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert 0 <= data["score"] < 100
    assert data["missing"]
    assert data["blockers"] == data["missing"]


@pytest.mark.asyncio
async def test_readiness_deterministic(async_client):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers, "return", merchant_name="Store", order_reference="ORD-3")
    case_id = case["id"]
    await _upload_evidence(async_client, case_id, headers)
    await _add_timeline(async_client, case_id, headers)

    first = await async_client.get(f"/api/cases/{case_id}/readiness", headers=headers)
    second = await async_client.get(f"/api/cases/{case_id}/readiness", headers=headers)
    assert first.json() == second.json()
