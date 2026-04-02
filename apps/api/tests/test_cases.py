import hashlib
import uuid
from datetime import datetime, timedelta

import pytest
from sqlmodel import select

from app.models import AuditEvent, CaseStatus, EvidenceItem, TimelineEvent


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


@pytest.mark.asyncio
async def test_add_note_and_timeline_order(async_client):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers)
    case_id = case["id"]

    note_resp = await async_client.post(
        f"/api/cases/{case_id}/notes",
        json={"body": "First note", "event_type": "note", "note_type": "manual"},
        headers=headers,
    )
    assert note_resp.status_code == 201

    payload = {
        "body": "Manual check",
        "event_type": "inspection",
        "happened_at": (datetime.utcnow() - timedelta(minutes=5)).isoformat(),
    }
    manual_resp = await async_client.post(
        f"/api/cases/{case_id}/timeline-events", json=payload, headers=headers
    )
    assert manual_resp.status_code == 201

    timeline = await async_client.get(f"/api/cases/{case_id}/timeline", headers=headers)
    events = timeline.json()
    assert len(events) >= 2
    assert events[0]["event_type"] == "inspection"
    assert events[-1]["event_type"] == "note"


@pytest.mark.asyncio
async def test_note_correction_appends_event(async_client):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers)
    case_id = case["id"]

    note = await async_client.post(
        f"/api/cases/{case_id}/notes",
        json={"body": "Draft note", "event_type": "note"},
        headers=headers,
    )
    note_id = note.json()["id"]

    correction = await async_client.post(
        f"/api/cases/{case_id}/notes",
        json={
            "body": "Corrected note",
            "event_type": "note",
            "corrects_event_id": note_id,
        },
        headers=headers,
    )
    assert correction.status_code == 201
    assert correction.json()["metadata_json"]["corrects_event_id"] == note_id

    timeline = await async_client.get(f"/api/cases/{case_id}/timeline", headers=headers)
    events = [e for e in timeline.json() if e["event_type"] == "note"]
    assert len(events) == 2


@pytest.mark.asyncio
async def test_timeline_event_attached_to_evidence(async_client):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers)
    case_id = case["id"]

    evidence = await async_client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("attach.txt", b"content", "text/plain")},
        headers=headers,
    )
    evidence_id = evidence.json()["id"]

    event_payload = {
        "body": "Linked evidence",
        "event_type": "inspection",
        "metadata": {"note": "linked"},
        "evidence_id": evidence_id,
    }
    response = await async_client.post(
        f"/api/cases/{case_id}/timeline-events", json=event_payload, headers=headers
    )
    assert response.status_code == 201
    assert response.json()["evidence_id"] == evidence_id


@pytest.mark.asyncio
async def test_audit_events_surface_policy(async_client):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers)
    case_id = case["id"]

    await async_client.patch(
        f"/api/cases/{case_id}",
        json={"summary": "Audit test update"},
        headers=headers,
    )

    await async_client.post(
        f"/api/cases/{case_id}/transition",
        json={"target_status": CaseStatus.COLLECTING_EVIDENCE},
        headers=headers,
    )

    await async_client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("proof.pdf", b"%PDF-audit", "application/pdf")},
        headers=headers,
    )

    await async_client.post(
        f"/api/cases/{case_id}/exports",
        json={"export_format": "zip"},
        headers=headers,
    )

    audit_response = await async_client.get(
        f"/api/cases/{case_id}/audit-events", headers=headers
    )
    assert audit_response.status_code == 200
    actions = {event["action"] for event in audit_response.json()}
    assert {"create", "update", "upload", "transition", "export"}.issubset(actions)


@pytest.mark.asyncio
async def test_audit_events_scope_enforced(async_client):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers)
    case_id = case["id"]

    other_headers = await _auth_headers(async_client)
    blocked = await async_client.get(
        f"/api/cases/{case_id}/audit-events", headers=other_headers
    )
    assert blocked.status_code == 404
