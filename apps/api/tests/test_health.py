import pytest

@pytest.mark.asyncio
async def test_health(async_client):
    response = await async_client.get("/healthz")
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "ClaimVault"
