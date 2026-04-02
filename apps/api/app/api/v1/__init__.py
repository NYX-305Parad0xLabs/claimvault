"""API v1 routers for ClaimVault."""

from .routers.auth import router as auth_router
from .routers.cases import router as cases_router
from .routers.counterparties import router as counterparties_router
from .routers.health import router as health_router
from .routers.search import router as search_router

__all__ = [
    "auth_router",
    "cases_router",
    "counterparties_router",
    "health_router",
    "search_router",
]
