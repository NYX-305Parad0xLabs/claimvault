import uuid

import pytest


async def _auth_headers(async_client):
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "email": f"search-{suffix}@example.com",
        "password": f"Pass!{suffix}",
        "full_name": "Search User",
        "workspace_name": f"Search-{suffix}",
    }
    response = await async_client.post("/api/auth/register", json=payload)
    assert response.status_code == 201
    login = await async_client.post("/api/auth/login", json={"email": payload["email"], "password": payload["password"]})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_case(async_client, headers, title="Case search", claim_type="refund", summary="Search narrative"):
    payload = {
        "title": title,
        "claim_type": claim_type,
        "summary": summary,
    }
    response = await async_client.post("/api/cases/", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_search_returns_timeline_hit(async_client):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers, title="Timeline search")
    event_payload = {
        "body": "Carrier dispatched a driver after damage report",
        "event_type": "carrier_update",
    }
    timeline_resp = await async_client.post(
        f"/api/cases/{case['id']}/timeline-events", json=event_payload, headers=headers
    )
    assert timeline_resp.status_code == 201

    response = await async_client.get("/api/search", params={"query": "carrier"}, headers=headers)
    assert response.status_code == 200
    results = response.json()
    assert any(hit["source_type"] == "timeline" and hit["case_id"] == case["id"] for hit in results)


@pytest.mark.asyncio
async def test_search_returns_evidence_hit(async_client):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers, title="Evidence search")

    upload = await async_client.post(
        f"/api/cases/{case['id']}/evidence",
        files={"file": ("damage.txt", b"Damage report", "text/plain")},
        headers=headers,
    )
    assert upload.status_code == 201
    evidence_id = upload.json()["id"]

    extraction_payload = {
        "extracted_text": "Damage photo of box corner",
        "extraction_status": "manual",
    }
    update = await async_client.patch(
        f"/api/cases/{case['id']}/evidence/{evidence_id}/extraction",
        json=extraction_payload,
        headers=headers,
    )
    assert update.status_code == 200

    response = await async_client.get("/api/search", params={"query": "damage"}, headers=headers)
    assert response.status_code == 200
    results = response.json()
    assert any(hit["source_type"] == "evidence" and hit["case_id"] == case["id"] for hit in results)


@pytest.mark.asyncio
async def test_search_case_filter(async_client):
    headers = await _auth_headers(async_client)
    case_a = await _create_case(async_client, headers, title="Alpha report", summary="alpha summary")
    case_b = await _create_case(async_client, headers, title="Beta report", summary="beta summary")

    response_all = await async_client.get("/api/search", params={"query": "alpha"}, headers=headers)
    assert response_all.status_code == 200
    assert any(hit["case_id"] == case_a["id"] for hit in response_all.json())

    response_filtered = await async_client.get(
        "/api/search", params={"query": "alpha", "case_id": case_b["id"]}, headers=headers
    )
    assert response_filtered.status_code == 200
    assert not response_filtered.json()


@pytest.mark.asyncio
async def test_search_is_workspace_scoped(async_client):
    headers_a = await _auth_headers(async_client)
    await _create_case(async_client, headers_a, title="Scoped case", summary="workspace alpha")

    headers_b = await _auth_headers(async_client)
    search = await async_client.get("/api/search", params={"query": "workspace"}, headers=headers_b)
    assert search.status_code == 200
    assert not search.json()
