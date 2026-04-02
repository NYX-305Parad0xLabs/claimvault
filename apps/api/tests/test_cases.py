import hashlib
import uuid

import pytest
from sqlmodel import select

from app.models import AuditEvent, CaseStatus, EvidenceItem, TimelineEvent


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


@pytest.mark.asyncio
async def test_evidence_upload_and_hash(async_client, app_instance):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers)
    case_id = case["id"]
    payload = {"file": ("proof.pdf", b"%PDF-test", "application/pdf")}
    response = await async_client.post(
        f"/api/cases/{case_id}/evidence", files=payload, headers=headers
    )
    assert response.status_code == 201
    data = response.json()
    assert data["sha256"] == hashlib.sha256(b"%PDF-test").hexdigest()

    session_factory = app_instance.state.session_factory
    with session_factory() as session:
        record = session.exec(select(EvidenceItem).where(EvidenceItem.id == data["id"])).one()
    assert record.sha256 == data["sha256"]


@pytest.mark.asyncio
async def test_duplicate_filename_creates_unique_keys(async_client):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers)
    case_id = case["id"]
    file_args = {"file": ("proof.pdf", b"%PDF-test", "application/pdf")}

    a = await async_client.post(f"/api/cases/{case_id}/evidence", files=file_args, headers=headers)
    b = await async_client.post(f"/api/cases/{case_id}/evidence", files=file_args, headers=headers)
    assert a.json()["storage_key"] != b.json()["storage_key"]


@pytest.mark.asyncio
async def test_invalid_upload_rejected(async_client, app_instance):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers)
    case_id = case["id"]
    limit = app_instance.state.settings.max_evidence_size_bytes
    payload = {"file": ("large.bin", b"A" * (limit + 1), "application/octet-stream")}
    response = await async_client.post(
        f"/api/cases/{case_id}/evidence", files=payload, headers=headers
    )
    assert response.status_code == 413


@pytest.mark.asyncio
async def test_download_enforces_workspace_permissions(async_client):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers)
    case_id = case["id"]
    content = b"%PDF-download"
    upload = await async_client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("download.pdf", content, "application/pdf")},
        headers=headers,
    )
    evidence_id = upload.json()["id"]

    download = await async_client.get(
        f"/api/cases/{case_id}/evidence/{evidence_id}/download", headers=headers
    )
    assert download.status_code == 200
    assert download.content == content

    other_headers = await _auth_headers(async_client)
    blocked = await async_client.get(
        f"/api/cases/{case_id}/evidence/{evidence_id}/download", headers=other_headers
    )
    assert blocked.status_code == 404
