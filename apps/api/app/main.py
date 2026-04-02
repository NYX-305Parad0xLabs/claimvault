from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import auth_router, cases_router, health_router
from app.core.config import Settings
from app.core.db import build_engine, build_session_factory
from app.core.logger import configure_structured_logger
from app.models import metadata as models_metadata
from app.services import AuthService, CaseService, EvidenceService, Services, TimelineService
from app.storage import LocalEvidenceStorage


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = app.state.settings
    logger = app.state.logger
    logger.info("starting ClaimVault", extra={"environment": settings.environment})
    if settings.environment != "production":
        models_metadata.create_all(bind=app.state.engine)
    try:
        yield
    finally:
        logger.info("stopping ClaimVault")


def create_app() -> FastAPI:
    settings = Settings()
    logger = configure_structured_logger(settings.app_name, settings.log_level)
    engine = build_engine(settings)
    session_factory = build_session_factory(engine)

    storage = LocalEvidenceStorage(settings.evidence_root)
    services = Services(
        case_service=CaseService(session_factory, logger),
        auth_service=AuthService(session_factory, settings, logger),
        evidence_service=EvidenceService(session_factory, storage, settings, logger),
        timeline_service=TimelineService(session_factory, logger),
    )

    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        lifespan=lifespan,
        docs_url="/docs",
        openapi_url="/api/openapi.json",
    )

    app.state.settings = settings
    app.state.logger = logger
    app.state.engine = engine
    app.state.session_factory = session_factory
    app.state.services = services

    app.include_router(health_router)
    app.include_router(auth_router, prefix="/api")
    app.include_router(cases_router, prefix="/api")

    return app
