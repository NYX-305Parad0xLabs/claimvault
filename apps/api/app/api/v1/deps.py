from __future__ import annotations

from typing import Generator

from fastapi import Depends, Request
from sqlmodel import Session

from app.services import CaseService, Services


def get_session(request: Request) -> Generator[Session, None, None]:
    session_factory = request.app.state.session_factory
    with session_factory() as session:
        yield session


def get_services(request: Request) -> Services:
    return request.app.state.services


def get_case_service(services: Services = Depends(get_services)) -> CaseService:
    return services.case_service
