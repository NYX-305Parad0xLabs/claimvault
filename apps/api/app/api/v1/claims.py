from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()

REPO_ROOT = Path(__file__).resolve().parents[5]
SCHEMA_PATH = REPO_ROOT / "packages" / "contracts" / "schemas" / "claim.json"


def load_claim_contract() -> dict[str, Any]:
    if not SCHEMA_PATH.exists():
        return {}
    return json.loads(SCHEMA_PATH.read_text())


class ClaimPayload(BaseModel):
    subject: str
    details: dict[str, Any] = Field(default_factory=dict)


class ClaimRecord(ClaimPayload):
    id: int
    status: str


@router.get("", response_model=list[ClaimRecord])
async def list_claims() -> list[ClaimRecord]:
    contract = load_claim_contract()
    doc = contract.get("title", "Claim")
    return [
        ClaimRecord(id=1, subject=doc, status="draft", details={"note": "sample"})
    ]


@router.post("", response_model=ClaimRecord, status_code=201)
async def create_claim(payload: ClaimPayload) -> ClaimRecord:
    return ClaimRecord(id=1, subject=payload.subject, status="pending", details=payload.details)
