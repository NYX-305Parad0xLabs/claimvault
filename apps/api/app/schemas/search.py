from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class SearchResultRead(BaseModel):
    model_config = ConfigDict(frozen=True)

    case_id: int
    case_title: str
    source_type: Literal["case", "timeline", "evidence"]
    source_id: int | None
    match_field: str
    snippet: str
    score: int
    details: dict[str, Any] = Field(default_factory=dict)
