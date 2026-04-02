import uuid

import pytest
from sqlmodel import select

from app.models import AuditEvent, ExtractionStatus, TimelineEvent


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


@pytest.mark.asyncio
async def test_extraction_endpoints_update_and_audit(async_client, app_instance):
    headers = await _auth_headers(async_client)
    created = await _create_case(async_client, headers)
    case_id = created["id"]

    upload = await async_client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("receipt.txt", b"receipt", "text/plain")},
        headers=headers,
    )
    assert upload.status_code == 201
    evidence_id = upload.json()["id"]

    get_resp = await async_client.get(
        f"/api/cases/{case_id}/evidence/{evidence_id}/extraction", headers=headers
    )
    assert get_resp.status_code == 200
    assert get_resp.json()["extraction_status"] == ExtractionStatus.PENDING
    assert get_resp.json()["extracted_text"] is None

    update_resp = await async_client.patch(
        f"/api/cases/{case_id}/evidence/{evidence_id}/extraction",
        json={
            "extracted_text": "Customer receipt for headset",
            "extraction_status": ExtractionStatus.MANUAL.value,
        },
        headers=headers,
    )
    assert update_resp.status_code == 200
    assert update_resp.json()["extraction_status"] == ExtractionStatus.MANUAL
    assert update_resp.json()["extracted_text"] == "Customer receipt for headset"

    session_factory = app_instance.state.session_factory
    with session_factory() as session:
        timeline_events = session.exec(
            select(TimelineEvent).where(
                TimelineEvent.case_id == case_id,
                TimelineEvent.event_type == "extraction_updated",
            )
        ).all()
        audit_events = session.exec(
            select(AuditEvent).where(
                AuditEvent.entity_id == case_id,
                AuditEvent.action == "extraction_update",
            )
        ).all()

    assert timeline_events, "Timeline should record extraction changes"
    assert audit_events, "Audit spine should log manual extraction"


@pytest.mark.asyncio
async def test_extraction_update_rejects_empty_payload(async_client):
    headers = await _auth_headers(async_client)
    created = await _create_case(async_client, headers)
    case_id = created["id"]

    upload = await async_client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("receipt.txt", b"receipt", "text/plain")},
        headers=headers,
    )
    evidence_id = upload.json()["id"]

    response = await async_client.patch(
        f"/api/cases/{case_id}/evidence/{evidence_id}/extraction",
        json={},
        headers=headers,
    )
    assert response.status_code == 400
    assert "provide extracted text or status" in response.json()["detail"]
