from fastapi import FastAPI

from app.api.v1.claims import router as claim_router
from app.core.config import settings

app = FastAPI(
    title="ClaimVault API",
    version="0.1.0",
    openapi_url="/api/openapi.json",
)

# health + version endpoints
@app.get("/api/health", tags=["health"])
async def health() -> dict[str, str]:
    return {"status": "ok", "api": "claimvault", "env": settings.fastapi_env}

app.include_router(claim_router, prefix="/api/claims", tags=["claims"])
