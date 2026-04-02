import uuid

import pytest
from sqlmodel import select

from app.models import AuditEvent, CaseStatus, TimelineEvent


async def _auth_headers(async_client):
    suffix = uuid.uuid4().hex[:8]
    email = f"user-{suffix}@example.com"
    password = f"Pass!{suffix}"
    register_payload = {
        "email": email,
        "password": password,
        "full_name": "Ops User",
        "workspace_name": f"Ops-{suffix}",
    }
    register_response = await async_client.post("/api/auth/register", json=register_payload)
    assert register_response.status_code == 201

    login_response = await async_client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def _create_case(async_client, headers, title="Return - faulty cable"):
    payload = {
        "title": title,
        "claim_type": "return",
        "summary": "Cable shorted upon delivery",
    }
    response = await async_client.post("/api/cases/", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


@pytest.mark.asyncio
async def test_case_crud(async_client):
    headers = await _auth_headers(async_client)
    created = await _create_case(async_client, headers)
    case_id = created["id"]

    listed = await async_client.get("/api/cases/", headers=headers)
    assert listed.status_code == 200
    assert any(case["id"] == case_id for case in listed.json())

    fetched = await async_client.get(f"/api/cases/{case_id}", headers=headers)
    assert fetched.status_code == 200
    assert fetched.json()["status"] == CaseStatus.DRAFT

    update_payload = {"summary": "Updated summary"}
    updated = await async_client.patch(
        f"/api/cases/{case_id}", json=update_payload, headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["summary"] == update_payload["summary"]
    assert updated.json()["status"] == CaseStatus.DRAFT


@pytest.mark.asyncio
async def test_valid_transition_creates_events(async_client, app_instance):
    headers = await _auth_headers(async_client)
    created = await _create_case(async_client, headers)
    case_id = created["id"]

    transition_response = await async_client.post(
        f"/api/cases/{case_id}/transition",
        json={"target_status": CaseStatus.COLLECTING_EVIDENCE},
        headers=headers,
    )
    assert transition_response.status_code == 200
    assert transition_response.json()["status"] == CaseStatus.COLLECTING_EVIDENCE

    session_factory = app_instance.state.session_factory
    with session_factory() as session:
        audit_events = session.exec(select(AuditEvent).where(AuditEvent.entity_id == case_id)).all()
        timeline_events = session.exec(select(TimelineEvent).where(TimelineEvent.case_id == case_id)).all()

    assert any(event.metadata_json["from"] == "draft" for event in timeline_events)
    assert any(event.action == "transition" for event in audit_events)


@pytest.mark.asyncio
async def test_invalid_transition_rejected(async_client):
    headers = await _auth_headers(async_client)
    created = await _create_case(async_client, headers)
    case_id = created["id"]

    response = await async_client.post(
        f"/api/cases/{case_id}/transition",
        json={"target_status": CaseStatus.RESOLVED},
        headers=headers,
    )
    assert response.status_code == 400
    assert response.json()["detail"].startswith("cannot transition")
