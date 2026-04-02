from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class TimelineEventCreate(BaseModel):
    body: str
    event_type: str
    happened_at: datetime | None = None
    evidence_id: int | None = None
    metadata: dict[str, Any] | None = None


class TimelineNoteCreate(TimelineEventCreate):
    note_type: str = "manual"
    corrects_event_id: int | None = None
    event_type: str = "note"


class TimelineEventRead(BaseModel):
    id: int
    case_id: int
    event_type: str
    body: str
    happened_at: datetime
    actor_type: str
    evidence_id: int | None
    metadata_json: dict[str, Any]

    class Config:
        from_attributes = True
