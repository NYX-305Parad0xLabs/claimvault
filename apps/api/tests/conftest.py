import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import create_app
from app.models import metadata as models_metadata


@pytest_asyncio.fixture(autouse=True)
def cli_env(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'claimvault.db'}")
    monkeypatch.setenv("CLAIMVAULT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ENVIRONMENT", "test")
    yield


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    app = create_app()
    models_metadata.create_all(bind=app.state.engine)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
