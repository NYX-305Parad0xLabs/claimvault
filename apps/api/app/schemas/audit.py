from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AuditEventRead(BaseModel):
    id: int
    entity_type: str
    entity_id: int
    action: str
    actor_type: str
    actor_id: int | None
    happened_at: datetime
    metadata_json: dict[str, Any]

    class Config:
        from_attributes = True
