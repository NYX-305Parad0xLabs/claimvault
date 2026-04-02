from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import auth_router, cases_router, health_router
from app.core.config import Settings
from app.core.db import build_engine, build_session_factory
from app.core.logger import configure_structured_logger
from app.models import metadata as models_metadata
from app.services import (
    AuditService,
    AuthService,
    CaseService,
    CaseSummaryService,
    EvidenceService,
    ExportService,
    ReadinessService,
    Services,
    TimelineService,
)
from app.services.case_assistant_service import NoopCaseAssistantService
from app.services.packager import DefaultVaultPackager, LiquefyPackager, VaultPackager
from app.services.summary_builder import CaseSummaryBuilder
from app.storage import LocalEvidenceStorage, LocalExportStorage


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

    evidence_storage = LocalEvidenceStorage(settings.evidence_root)
    export_storage = LocalExportStorage(settings.export_root)
    summary_builder = CaseSummaryBuilder()
    packager: VaultPackager
    if settings.vault_packager.lower() == "liquefy":
        packager = LiquefyPackager(logger)
    else:
        packager = DefaultVaultPackager(evidence_storage, summary_builder, logger)
    services = Services(
        audit_service=AuditService(session_factory, logger),
        case_service=CaseService(session_factory, logger),
        auth_service=AuthService(session_factory, settings, logger),
        evidence_service=EvidenceService(session_factory, evidence_storage, settings, logger),
        export_service=ExportService(session_factory, export_storage, packager, logger),
        summary_service=CaseSummaryService(session_factory, summary_builder),
        timeline_service=TimelineService(session_factory, logger),
        readiness_service=ReadinessService(session_factory, logger),
        assistant_service=NoopCaseAssistantService(),
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
