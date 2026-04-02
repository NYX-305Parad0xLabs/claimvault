from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.v1.deps import (
    get_current_workspace_member,
    get_search_service,
)
from app.models import WorkspaceMembership
from app.schemas.search import SearchResultRead
from app.services.search_service import SearchService

router = APIRouter(prefix="/search", tags=["search"])


@router.get("", response_model=list[SearchResultRead])
def search(
    query: str = Query(..., min_length=1),
    case_id: int | None = Query(None, ge=1),
    workspace_member: WorkspaceMembership = Depends(get_current_workspace_member),
    search_service: SearchService = Depends(get_search_service),
) -> list[SearchResultRead]:
    return search_service.search(workspace_member.workspace_id, query, case_id)
