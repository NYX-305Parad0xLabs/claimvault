from fastapi import APIRouter, Request

router = APIRouter(tags=["health"])


@router.get("/healthz")
def health(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    return {
        "status": "ok",
        "service": settings.app_name,
        "environment": settings.environment,
    }


@router.get("/version")
def version(request: Request) -> dict[str, str]:
    return {"version": request.app.state.settings.version}
