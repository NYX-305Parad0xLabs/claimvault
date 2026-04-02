from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from fastapi import status
from sqlmodel import Session, select

from app.models.claim import CounterpartyProfile
from app.schemas.counterparty import (
    CounterpartyProfileCreate,
    CounterpartyProfileRead,
    CounterpartyProfileUpdate,
)


class CounterpartyServiceError(Exception):
    def __init__(self, detail: str, status_code: int = status.HTTP_400_BAD_REQUEST) -> None:
        self.detail = detail
        self.status_code = status_code


@dataclass(frozen=True)
class CounterpartyService:
    _session_factory: Callable[[], Session]

    def list_profiles(self, workspace_id: int) -> list[CounterpartyProfileRead]:
        with self._session_factory() as session:
            statement = (
                select(CounterpartyProfile)
                .where(CounterpartyProfile.workspace_id == workspace_id)
                .order_by(CounterpartyProfile.name)
            )
            records = session.exec(statement).all()
            return [CounterpartyProfileRead.model_validate(record) for record in records]

    def get_profile(
        self,
        workspace_id: int,
        profile_id: int,
    ) -> CounterpartyProfileRead:
        with self._session_factory() as session:
            profile = session.get(CounterpartyProfile, profile_id)
            if not profile or profile.workspace_id != workspace_id:
                raise CounterpartyServiceError("counterparty profile not found", status.HTTP_404_NOT_FOUND)
            return CounterpartyProfileRead.model_validate(profile)

    def create_profile(
        self,
        workspace_id: int,
        payload: CounterpartyProfileCreate,
    ) -> CounterpartyProfileRead:
        with self._session_factory() as session:
            profile = CounterpartyProfile(
                workspace_id=workspace_id,
                name=payload.name,
                profile_type=payload.profile_type,
                website=payload.website,
                support_email=payload.support_email,
                support_url=payload.support_url,
                notes=payload.notes,
            )
            session.add(profile)
            session.commit()
            session.refresh(profile)
            return CounterpartyProfileRead.model_validate(profile)

    def update_profile(
        self,
        workspace_id: int,
        profile_id: int,
        payload: CounterpartyProfileUpdate,
    ) -> CounterpartyProfileRead:
        updates = payload.model_dump(exclude_defaults=True, exclude_none=True)
        if not updates:
            raise CounterpartyServiceError("no updates provided")
        with self._session_factory() as session:
            profile = session.get(CounterpartyProfile, profile_id)
            if not profile or profile.workspace_id != workspace_id:
                raise CounterpartyServiceError("counterparty profile not found", status.HTTP_404_NOT_FOUND)
            for attr, value in updates.items():
                setattr(profile, attr, value)
            session.add(profile)
            session.commit()
            session.refresh(profile)
            return CounterpartyProfileRead.model_validate(profile)
