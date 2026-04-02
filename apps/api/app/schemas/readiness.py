from __future__ import annotations

from typing import List

from pydantic import BaseModel


class ReadinessReport(BaseModel):
    score: int
    missing: List[str]
    recommended: List[str]
    blockers: List[str]

    class Config:
        frozen = True
