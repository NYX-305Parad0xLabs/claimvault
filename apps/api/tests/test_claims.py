import pytest

from app.models import Workspace


@pytest.mark.asyncio
async def test_create_and_list_claim(async_client, app_instance):
    workspace_payload = {"name": "Finance Ops"}
    workspace_data = Workspace(**workspace_payload)
    session_factory = app_instance.state.session_factory
    with session_factory() as session:
        session.add(workspace_data)
        session.commit()
        session.refresh(workspace_data)

    payload = {
        "workspace_id": workspace_data.id,
        "title": "Return - faulty cable",
        "claim_type": "return",
        "summary": "Faulty cable once opened",
    }

    created = await async_client.post("/api/claims/", json=payload)
    assert created.status_code == 201
    body = created.json()
    assert body["title"] == payload["title"]
    assert body["workspace_id"] == payload["workspace_id"]

    listed = await async_client.get("/api/claims/")
    assert listed.status_code == 200
    assert any(case["title"] == payload["title"] for case in listed.json())
