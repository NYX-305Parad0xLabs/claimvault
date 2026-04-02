import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

from app.main import create_app
from app.models import metadata as models_metadata


@pytest_asyncio.fixture(autouse=True)
def cli_env(monkeypatch, tmp_path):
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path / 'claimvault.db'}")
    monkeypatch.setenv("CLAIMVAULT_DATA_DIR", str(tmp_path))
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("SECRET_KEY", "test-secret")
    monkeypatch.setenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")
    monkeypatch.setenv("TOKEN_ALGORITHM", "HS256")
    yield


@pytest.fixture
def app_instance():
    app = create_app()
    models_metadata.create_all(bind=app.state.engine)
    return app


@pytest.fixture
def session_factory(app_instance):
    return app_instance.state.session_factory


@pytest_asyncio.fixture
async def async_client(app_instance) -> AsyncClient:
    transport = ASGITransport(app=app_instance)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client
