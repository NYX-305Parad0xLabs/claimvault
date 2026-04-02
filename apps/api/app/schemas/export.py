from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict


class CaseExportRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    export_format: Literal["zip"] = "zip"


class CaseExportRead(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: int
    case_id: int
    artifact_type: str
    storage_key: str
    manifest_hash: str | None
    archive_hash: str | None
    metadata_json: dict[str, Any]
    created_at: datetime
