from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CaseSummaryPreview(BaseModel):
    model_config = ConfigDict(frozen=True)
    case_id: int
    claim_type: str
    summary: str
