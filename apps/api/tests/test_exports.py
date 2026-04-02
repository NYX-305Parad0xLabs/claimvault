import io
import json
import uuid
import zipfile

import pytest


async def _auth_headers(async_client):
    suffix = uuid.uuid4().hex[:8]
    payload = {
        "email": f"operator-{suffix}@example.com",
        "password": f"Pass!{suffix}",
        "full_name": "Export User",
        "workspace_name": f"Ops-{suffix}",
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
        "title": "Exportable case",
        "claim_type": claim_type,
        "summary": "Case ready for export",
        "merchant_name": "Store",
        "order_reference": "ORD-42",
        "amount_value": 123.45,
    }
    response = await async_client.post("/api/cases/", json=payload, headers=headers)
    assert response.status_code == 201
    return response.json()


async def _upload_evidence(async_client, case_id, headers):
    response = await async_client.post(
        f"/api/cases/{case_id}/evidence",
        files={"file": ("export.pdf", b"%PDF", "application/pdf")},
        headers=headers,
    )
    assert response.status_code == 201


async def _add_timeline(async_client, case_id, headers):
    response = await async_client.post(
        f"/api/cases/{case_id}/timeline-events",
        json={"event_type": "note", "body": "Export ready"},
        headers=headers,
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_export_bundle_contains_expected_artifacts(async_client):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers)
    case_id = case["id"]
    await _upload_evidence(async_client, case_id, headers)
    await _add_timeline(async_client, case_id, headers)

    export_resp = await async_client.post(
        f"/api/cases/{case_id}/exports",
        json={"export_format": "zip"},
        headers=headers,
    )
    assert export_resp.status_code == 201
    export = export_resp.json()

    download = await async_client.get(
        f"/api/cases/{case_id}/exports/{export['id']}/download",
        headers=headers,
    )
    assert download.status_code == 200
    archive = zipfile.ZipFile(io.BytesIO(download.content))
    assert {"summary.md", "case.json", "timeline.json", "evidence_manifest.json", "checksums.txt"}.issubset(
        set(archive.namelist())
    )
    evidence_entries = [name for name in archive.namelist() if name.startswith("evidence/")]
    assert evidence_entries

    case_payload = json.loads(archive.read("case.json"))
    assert case_payload["title"] == "Exportable case"
    manifest = json.loads(archive.read("evidence_manifest.json"))
    assert manifest[0]["original_filename"] == "export.pdf"
    checksums = archive.read("checksums.txt").decode().strip().splitlines()
    assert any("case.json" in line for line in checksums)
    evidence_entry = evidence_entries[0]
    evidence_checksum_line = next(line for line in checksums if evidence_entry in line)
    evidence_hash = evidence_checksum_line.split()[0]
    assert evidence_hash == manifest[0]["sha256"]


@pytest.mark.asyncio
async def test_export_is_deterministic(async_client):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers)
    case_id = case["id"]
    await _upload_evidence(async_client, case_id, headers)
    await _add_timeline(async_client, case_id, headers)

    response_one = await async_client.post(
        f"/api/cases/{case_id}/exports",
        json={"export_format": "zip"},
        headers=headers,
    )
    response_two = await async_client.post(
        f"/api/cases/{case_id}/exports",
        json={"export_format": "zip"},
        headers=headers,
    )
    assert response_one.status_code == 201
    assert response_two.status_code == 201

    download_one = await async_client.get(
        f"/api/cases/{case_id}/exports/{response_one.json()['id']}/download",
        headers=headers,
    )
    download_two = await async_client.get(
        f"/api/cases/{case_id}/exports/{response_two.json()['id']}/download",
        headers=headers,
    )
    assert download_one.content == download_two.content


@pytest.mark.asyncio
async def test_export_download_requires_workspace_membership(async_client):
    headers = await _auth_headers(async_client)
    case = await _create_case(async_client, headers)
    case_id = case["id"]
    await _upload_evidence(async_client, case_id, headers)
    await _add_timeline(async_client, case_id, headers)

    export_resp = await async_client.post(
        f"/api/cases/{case_id}/exports",
        json={"export_format": "zip"},
        headers=headers,
    )
    assert export_resp.status_code == 201
    export_id = export_resp.json()["id"]

    other_headers = await _auth_headers(async_client)
    download = await async_client.get(
        f"/api/cases/{case_id}/exports/{export_id}/download",
        headers=other_headers,
    )
    assert download.status_code in {403, 404}
