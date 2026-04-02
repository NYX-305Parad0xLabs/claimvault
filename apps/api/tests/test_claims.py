import pytest

@pytest.mark.asyncio
async def test_create_and_list_claim(async_client):
    payload = {
        "subject": "Return - faulty cable",
        "claim_type": "return",
        "created_by": "tester",
    }

    created = await async_client.post("/api/claims/", json=payload)
    assert created.status_code == 201
    assert created.json()["subject"] == payload["subject"]

    listed = await async_client.get("/api/claims/")
    assert listed.status_code == 200
    assert any(case["subject"] == payload["subject"] for case in listed.json())
