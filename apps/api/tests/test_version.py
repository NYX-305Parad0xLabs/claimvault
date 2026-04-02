import pytest

@pytest.mark.asyncio
async def test_version(async_client):
    response = await async_client.get("/version")
    assert response.status_code == 200
    assert "version" in response.json()
