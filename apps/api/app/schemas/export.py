from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class CaseExportRequest(BaseModel):
    model_config = ConfigDict(frozen=True)
    export_format: Literal["zip"] = "zip"


class CaseExportRead(BaseModel):
    model_config = ConfigDict(frozen=True)
    id: int
    case_id: int
    export_format: str
    storage_key: str
    created_at: datetime
