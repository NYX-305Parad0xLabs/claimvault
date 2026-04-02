import hashlib
import uuid
from datetime import datetime, timedelta

import pytest
from sqlmodel import select

from app.models import (
    AuditEvent,
    CaseStatus,
    CounterpartyProfile,
    CounterpartyType,
    EvidenceItem,
    ExtractionStatus,
    TimelineEvent,
)


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
async def test_case_detail_includes_counterparty_profile(async_client, app_instance):
    headers = await _auth_headers(async_client)
    me = await async_client.get("/api/auth/me", headers=headers)
    workspace_id = me.json()["membership"]["workspace_id"]
    session_factory = app_instance.state.session_factory
    with session_factory() as session:
        profile = CounterpartyProfile(
            workspace_id=workspace_id,
            name="Merchant Partner",
            profile_type=CounterpartyType.MERCHANT,
            website="https://merchant.example",
            support_email="ops@merchant.example",
            support_url="https://merchant.example/support",
            notes="Preferred partner",
        )
        session.add(profile)
        session.commit()
        session.refresh(profile)

    payload = {
        "title": "Counterparty case",
        "claim_type": "refund",
        "summary": "Counterparty detail story",
        "counterparty_profile_id": profile.id,
    }
    created = await async_client.post("/api/cases/", json=payload, headers=headers)
    assert created.status_code == 201
    data = created.json()
    assert data["counterparty_profile"]["name"] == profile.name
    assert data["counterparty_profile"]["support_email"] == profile.support_email
    assert data["counterparty_profile"]["profile_type"] == CounterpartyType.MERCHANT


@pytest.mark.asyncio
async def test_valid_transition_creates_events(async_client, app_instance):
    headers = await _auth_headers(async_client)
    created = await _create_case(async_client, headers)
    case_id = created["id"]

    reason = "Gather proof from warehouse"
    transition_response = await async_client.post(
        f"/api/cases/{case_id}/transition",
        json={"target_status": CaseStatus.COLLECTING_EVIDENCE, "reason": reason},
        headers=headers,
    )
    assert transition_response.status_code == 200
    assert transition_response.json()["status"] == CaseStatus.COLLECTING_EVIDENCE

    session_factory = app_instance.state.session_factory
    with session_factory() as session:
        audit_events = session.exec(select(AuditEvent).where(AuditEvent.entity_id == case_id)).all()
        timeline_events = session.exec(select(TimelineEvent).where(TimelineEvent.case_id == case_id)).all()

    assert any(event.metadata_json.get("reason") == reason for event in timeline_events)
    assert any(event.action == "transition" for event in audit_events)


@pytest.mark.asyncio
async def test_state_machine_allows_loop(async_client):
    headers = await _auth_headers(async_client)
    created = await _create_case(async_client, headers)
    case_id = created["id"]

    await async_client.post(
        f"/api/cases/{case_id}/transition",
        json={"target_status": CaseStatus.COLLECTING_EVIDENCE},
        headers=headers,
    )
    resp = await async_client.post(
        f"/api/cases/{case_id}/transition",
        json={"target_status": CaseStatus.NEEDS_USER_INPUT},
        headers=headers,
    )
    assert resp.status_code == 200
    resp = await async_client.post(
        f"/api/cases/{case_id}/transition",
        json={"target_status": CaseStatus.COLLECTING_EVIDENCE},
        headers=headers,
    )
    assert resp.status_code == 200


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
    detail = response.json()["detail"]
    assert "cannot transition" in detail
    assert "collecting_evidence" in detail


@pytest.mark.asyncio
async def test_evidence_upload_and_hash(async_client, app_instance):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers)
    case_id = case["id"]
    payload = {"file": ("proof.pdf", b"%PDF-test", "application/pdf")}
    metadata_payload = {
        "merchant_label": "Retailer Ops",
        "platform_label": "claimvault",
        "manual_relevance": "true",
        "description": "Customer receipt",
        "event_date": datetime.utcnow().isoformat(),
        "extraction_status": ExtractionStatus.EXTRACTED.value,
    }
    response = await async_client.post(
        f"/api/cases/{case_id}/evidence",
        files=payload,
        data=metadata_payload,
        headers=headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["sha256"] == hashlib.sha256(b"%PDF-test").hexdigest()
    assert data["merchant_label"] == metadata_payload["merchant_label"]
    assert data["manual_relevance"] is True
    assert data["description"] == metadata_payload["description"]
    assert data["extraction_status"] == ExtractionStatus.EXTRACTED

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
async def test_evidence_detail_and_delete(async_client):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers)
    case_id = case["id"]
    files = {"file": ("proof.pdf", b"%PDF-test", "application/pdf")}
    metadata_payload = {
        "merchant_label": "Operations",
        "manual_relevance": "true",
        "description": "Manual receipt",
        "event_date": datetime.utcnow().isoformat(),
        "platform_label": "claimvault",
        "extraction_status": ExtractionStatus.EXTRACTED.value,
    }
    upload = await async_client.post(
        f"/api/cases/{case_id}/evidence",
        files=files,
        data=metadata_payload,
        headers=headers,
    )
    assert upload.status_code == 201
    evidence_id = upload.json()["id"]

    detail = await async_client.get(
        f"/api/cases/{case_id}/evidence/{evidence_id}", headers=headers
    )
    assert detail.status_code == 200
    detail_data = detail.json()
    assert detail_data["merchant_label"] == metadata_payload["merchant_label"]
    assert detail_data["manual_relevance"] is True
    assert detail_data["description"] == metadata_payload["description"]

    other_headers = await _auth_headers(async_client)
    blocked = await async_client.get(
        f"/api/cases/{case_id}/evidence/{evidence_id}", headers=other_headers
    )
    assert blocked.status_code == 404

    deleted = await async_client.delete(
        f"/api/cases/{case_id}/evidence/{evidence_id}",
        headers=headers,
        params={"reason": "cleanup"},
    )
    assert deleted.status_code == 204

    detail_after = await async_client.get(
        f"/api/cases/{case_id}/evidence/{evidence_id}", headers=headers
    )
    assert detail_after.status_code == 404

    listing = await async_client.get(f"/api/cases/{case_id}/evidence", headers=headers)
    assert all(item["id"] != evidence_id for item in listing.json())


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
