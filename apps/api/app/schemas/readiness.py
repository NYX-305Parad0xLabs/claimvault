from __future__ import annotations

from typing import List

from pydantic import BaseModel, ConfigDict


class ReadinessCheck(BaseModel):
    model_config = ConfigDict(frozen=True)

    rule_key: str
    description: str
    required: bool
    satisfied: bool
    weight: int


class ReadinessReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    score: int
    missing: List[str]
    recommended: List[str]
    blockers: List[str]
    checks: List[ReadinessCheck] = []
