from __future__ import annotations

from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    Response,
    UploadFile,
    status,
)
from fastapi.responses import FileResponse
from pathlib import Path

from app.api.v1.deps import (
    get_audit_service,
    get_case_service,
    get_current_workspace_member,
    require_workspace_role,
    get_evidence_service,
    get_export_service,
    get_readiness_service,
    get_summary_service,
    get_timeline_service,
)
from app.models import WorkspaceMembership, WorkspaceRole
from app.models.claim import CaseStatus, ClaimType, EvidenceKind, ExtractionStatus
from app.schemas.audit import AuditEventRead
from app.schemas.case import (
    CaseCreate,
    CaseRead,
    CaseTransitionRequest,
    CaseUpdate,
)
from app.schemas.evidence import (
    EvidenceExtractionRead,
    EvidenceExtractionUpdate,
    EvidenceRead,
)
from app.schemas.case_summary import CaseSummaryPreview
from app.schemas.export import CaseExportRead, CaseExportRequest
from app.schemas.readiness import ReadinessReport
from app.schemas.timeline import (
    TimelineEventCreate,
    TimelineEventRead,
    TimelineNoteCreate,
)
from app.services.case_service import CaseService, CaseServiceError
from app.services.evidence_service import EvidenceService, EvidenceServiceError
from app.services.export_service import ExportService, ExportServiceError
from app.services.case_summary_service import CaseSummaryService, CaseSummaryServiceError
from app.services.readiness_service import ReadinessService
from app.services.timeline_service import TimelineService, TimelineServiceError
from app.services.audit_service import AuditService, AuditServiceError

router = APIRouter(prefix="/cases", tags=["cases"])


def _handle_case_error(error: CaseServiceError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.detail)


def _handle_evidence_error(error: EvidenceServiceError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.detail)


def _handle_timeline_error(error: TimelineServiceError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.detail)


def _handle_export_error(error: ExportServiceError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.detail)


def _handle_audit_error(error: AuditServiceError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.detail)


def _handle_summary_error(error: CaseSummaryServiceError) -> HTTPException:
    return HTTPException(status_code=error.status_code, detail=error.detail)


@router.get("/", response_model=list[CaseRead])
def list_cases(
    workspace_member: WorkspaceMembership = Depends(get_current_workspace_member),
    case_service: CaseService = Depends(get_case_service),
    status: CaseStatus | None = Query(None),
    claim_type: ClaimType | None = Query(None),
    merchant_name: str | None = Query(None),
    limit: int = Query(25, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> list[CaseRead]:
    return case_service.list_cases(
        workspace_member.workspace_id,
        limit=limit,
        offset=offset,
        status=status,
        claim_type=claim_type,
        merchant_name=merchant_name,
    )


@router.get("/{case_id}", response_model=CaseRead)
def get_case(
    case_id: int,
    workspace_member: WorkspaceMembership = Depends(get_current_workspace_member),
    case_service: CaseService = Depends(get_case_service),
) -> CaseRead:
    try:
        return case_service.get_case(workspace_member.workspace_id, case_id)
    except CaseServiceError as error:
        raise _handle_case_error(error)


@router.post("/", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
def create_case(
    payload: CaseCreate,
    case_service: CaseService = Depends(get_case_service),
    workspace_member: WorkspaceMembership = Depends(
        require_workspace_role(WorkspaceRole.OWNER, WorkspaceRole.OPERATOR)
    ),
) -> CaseRead:
    return case_service.create_case(
        payload,
        workspace_member.workspace_id,
        actor_id=workspace_member.user_id,
    )


@router.patch("/{case_id}", response_model=CaseRead)
def update_case(
    case_id: int,
    payload: CaseUpdate,
    case_service: CaseService = Depends(get_case_service),
    workspace_member: WorkspaceMembership = Depends(
        require_workspace_role(WorkspaceRole.OWNER, WorkspaceRole.OPERATOR)
    ),
) -> CaseRead:
    try:
        return case_service.update_case(
            workspace_member.workspace_id,
            case_id,
            payload,
            actor_id=workspace_member.user_id,
        )
    except CaseServiceError as error:
        raise _handle_case_error(error)


@router.post("/{case_id}/transition", response_model=CaseRead)
def transition_case(
    case_id: int,
    payload: CaseTransitionRequest,
    case_service: CaseService = Depends(get_case_service),
    workspace_member: WorkspaceMembership = Depends(
        require_workspace_role(WorkspaceRole.OWNER, WorkspaceRole.OPERATOR)
    ),
) -> CaseRead:
    try:
        return case_service.transition_case(
            workspace_member.workspace_id,
            case_id,
            payload,
            actor_id=workspace_member.user_id,
        )
    except CaseServiceError as error:
        raise _handle_case_error(error)


@router.get("/{case_id}/evidence", response_model=list[EvidenceRead])
def list_evidence(
    case_id: int,
    workspace_member: WorkspaceMembership = Depends(get_current_workspace_member),
    evidence_service: EvidenceService = Depends(get_evidence_service),
) -> list[EvidenceRead]:
    try:
        return evidence_service.list_evidence(workspace_member.workspace_id, case_id)
    except EvidenceServiceError as error:
        raise _handle_evidence_error(error)


@router.get("/{case_id}/evidence/{evidence_id}", response_model=EvidenceRead)
def get_evidence_detail(
    case_id: int,
    evidence_id: int,
    workspace_member: WorkspaceMembership = Depends(get_current_workspace_member),
    evidence_service: EvidenceService = Depends(get_evidence_service),
) -> EvidenceRead:
    try:
        evidence = evidence_service.fetch_evidence(
            workspace_member.workspace_id, case_id, evidence_id
        )
    except EvidenceServiceError as error:
        raise _handle_evidence_error(error)
    return EvidenceRead.model_validate(evidence)


@router.get(
    "/{case_id}/evidence/{evidence_id}/extraction",
    response_model=EvidenceExtractionRead,
)
def get_evidence_extraction(
    case_id: int,
    evidence_id: int,
    workspace_member: WorkspaceMembership = Depends(get_current_workspace_member),
    evidence_service: EvidenceService = Depends(get_evidence_service),
) -> EvidenceExtractionRead:
    try:
        evidence = evidence_service.fetch_evidence(
            workspace_member.workspace_id, case_id, evidence_id
        )
    except EvidenceServiceError as error:
        raise _handle_evidence_error(error)
    return EvidenceExtractionRead(
        extraction_status=evidence.extraction_status,
        extracted_text=evidence.extracted_text,
    )


@router.delete("/{case_id}/evidence/{evidence_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_evidence(
    case_id: int,
    evidence_id: int,
    reason: str | None = Query(None),
    evidence_service: EvidenceService = Depends(get_evidence_service),
    workspace_member: WorkspaceMembership = Depends(
        require_workspace_role(WorkspaceRole.OWNER, WorkspaceRole.OPERATOR)
    ),
) -> Response:
    try:
        evidence_service.delete_evidence(
            workspace_member.workspace_id,
            case_id,
            evidence_id,
            actor_id=workspace_member.user_id,
            reason=reason,
        )
    except EvidenceServiceError as error:
        raise _handle_evidence_error(error)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/{case_id}/evidence", response_model=EvidenceRead, status_code=status.HTTP_201_CREATED)
async def upload_evidence(
    case_id: int,
    file: UploadFile = File(...),
    kind: EvidenceKind | None = Query(None),
    source_label: str | None = Form(None),
    merchant_label: str | None = Form(None),
    carrier_label: str | None = Form(None),
    platform_label: str | None = Form(None),
    event_date: datetime | None = Form(None),
    description: str | None = Form(None),
    extraction_status: ExtractionStatus | None = Form(None),
    manual_relevance: bool = Form(False),
    evidence_service: EvidenceService = Depends(get_evidence_service),
    workspace_member: WorkspaceMembership = Depends(
        require_workspace_role(WorkspaceRole.OWNER, WorkspaceRole.OPERATOR)
    ),
) -> EvidenceRead:
    content = await file.read()
    try:
        return evidence_service.upload_evidence(
            workspace_member.workspace_id,
            case_id,
            file.filename,
            content,
            kind=kind,
            actor_id=workspace_member.user_id,
            source_label=source_label or "upload",
            declared_mime=file.content_type,
            merchant_label=merchant_label,
            carrier_label=carrier_label,
            platform_label=platform_label,
            event_date=event_date,
            description=description,
            extraction_status=extraction_status,
            manual_relevance=manual_relevance,
        )
    except EvidenceServiceError as error:
        raise _handle_evidence_error(error)


@router.get("/{case_id}/evidence/{evidence_id}/download")
def download_evidence(
    case_id: int,
    evidence_id: int,
    evidence_service: EvidenceService = Depends(get_evidence_service),
    workspace_member: WorkspaceMembership = Depends(get_current_workspace_member),
) -> FileResponse:
    try:
        evidence, path = evidence_service.get_evidence(
            workspace_member.workspace_id, case_id, evidence_id
        )
    except EvidenceServiceError as error:
        raise _handle_evidence_error(error)
    return FileResponse(path, media_type=evidence.mime_type, filename=evidence.original_filename)


@router.patch(
    "/{case_id}/evidence/{evidence_id}/extraction",
    response_model=EvidenceRead,
)
def update_evidence_extraction(
    case_id: int,
    evidence_id: int,
    payload: EvidenceExtractionUpdate,
    evidence_service: EvidenceService = Depends(get_evidence_service),
    workspace_member: WorkspaceMembership = Depends(
        require_workspace_role(WorkspaceRole.OWNER, WorkspaceRole.OPERATOR)
    ),
) -> EvidenceRead:
    try:
        return evidence_service.update_extraction(
            workspace_member.workspace_id,
            case_id,
            evidence_id,
            actor_id=workspace_member.user_id,
            extracted_text=payload.extracted_text,
            extraction_status=payload.extraction_status,
        )
    except EvidenceServiceError as error:
        raise _handle_evidence_error(error)


@router.get("/{case_id}/readiness", response_model=ReadinessReport)
def check_readiness(
    case_id: int,
    readiness_service: ReadinessService = Depends(get_readiness_service),
    workspace_member: WorkspaceMembership = Depends(get_current_workspace_member),
) -> ReadinessReport:
    try:
        return readiness_service.evaluate(workspace_member.workspace_id, case_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="case not found")


@router.get("/{case_id}/summary-preview", response_model=CaseSummaryPreview)
def preview_summary(
    case_id: int,
    summary_service: CaseSummaryService = Depends(get_summary_service),
    workspace_member: WorkspaceMembership = Depends(get_current_workspace_member),
) -> CaseSummaryPreview:
    try:
        return summary_service.preview_summary(workspace_member.workspace_id, case_id)
    except CaseSummaryServiceError as error:
        raise _handle_summary_error(error)


@router.get("/{case_id}/timeline", response_model=list[TimelineEventRead])
def get_timeline(
    case_id: int,
    workspace_member: WorkspaceMembership = Depends(get_current_workspace_member),
    timeline_service: TimelineService = Depends(get_timeline_service),
) -> list[TimelineEventRead]:
    try:
        return timeline_service.list_events(workspace_member.workspace_id, case_id)
    except TimelineServiceError as error:
        raise _handle_timeline_error(error)


@router.get("/{case_id}/audit-events", response_model=list[AuditEventRead])
def list_audit_events(
    case_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    audit_service: AuditService = Depends(get_audit_service),
    workspace_member: WorkspaceMembership = Depends(get_current_workspace_member),
) -> list[AuditEventRead]:
    try:
        events = audit_service.list_case_events(
            workspace_member.workspace_id,
            case_id,
            limit=limit,
            offset=offset,
        )
    except AuditServiceError as error:
        raise _handle_audit_error(error)
    return [AuditEventRead.model_validate(event) for event in events]


@router.post("/{case_id}/timeline-events", response_model=TimelineEventRead, status_code=status.HTTP_201_CREATED)
def create_timeline_event(
    case_id: int,
    payload: TimelineEventCreate,
    timeline_service: TimelineService = Depends(get_timeline_service),
    workspace_member: WorkspaceMembership = Depends(
        require_workspace_role(WorkspaceRole.OWNER, WorkspaceRole.OPERATOR)
    ),
) -> TimelineEventRead:
    try:
        return timeline_service.create_event(
            workspace_member.workspace_id,
            case_id,
            payload,
            actor_id=workspace_member.user_id,
        )
    except TimelineServiceError as error:
        raise _handle_timeline_error(error)


@router.post("/{case_id}/notes", response_model=TimelineEventRead, status_code=status.HTTP_201_CREATED)
def create_note(
    case_id: int,
    payload: TimelineNoteCreate,
    timeline_service: TimelineService = Depends(get_timeline_service),
    workspace_member: WorkspaceMembership = Depends(
        require_workspace_role(WorkspaceRole.OWNER, WorkspaceRole.OPERATOR)
    ),
) -> TimelineEventRead:
    try:
        return timeline_service.create_note(
            workspace_member.workspace_id,
            case_id,
            payload,
            actor_id=workspace_member.user_id,
        )
    except TimelineServiceError as error:
        raise _handle_timeline_error(error)


@router.post("/{case_id}/exports", response_model=CaseExportRead, status_code=status.HTTP_201_CREATED)
def create_export(
    case_id: int,
    payload: CaseExportRequest,
    export_service: ExportService = Depends(get_export_service),
    workspace_member: WorkspaceMembership = Depends(
        require_workspace_role(WorkspaceRole.OWNER, WorkspaceRole.OPERATOR)
    ),
) -> CaseExportRead:
    try:
        return export_service.create_export(
            workspace_member.workspace_id,
            case_id,
            actor_id=workspace_member.user_id,
            export_format=payload.export_format,
        )
    except ExportServiceError as error:
        raise _handle_export_error(error)


@router.get("/{case_id}/exports/{export_id}/download")
def download_export(
    case_id: int,
    export_id: int,
    export_service: ExportService = Depends(get_export_service),
    workspace_member: WorkspaceMembership = Depends(get_current_workspace_member),
) -> FileResponse:
    try:
        case_export = export_service.get_export(
            workspace_member.workspace_id, case_id, export_id
        )
    except ExportServiceError as error:
        raise _handle_export_error(error)
    path = export_service.path_for_export(case_export.storage_key)
    return FileResponse(path, media_type="application/zip", filename=Path(case_export.storage_key).name)
