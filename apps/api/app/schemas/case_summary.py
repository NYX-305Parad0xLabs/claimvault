from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class WorkflowPackTaskRead(BaseModel):
    model_config = ConfigDict(frozen=True)

    title: str
    description: str
    priority: int
    status: str


class CaseSummaryPreview(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_id: int
    claim_type: str
    summary: str
    workflow_pack_name: str | None = None
    workflow_pack_summary: str | None = None
    workflow_pack_tasks: list[WorkflowPackTaskRead] = []
