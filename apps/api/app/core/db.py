from __future__ import annotations

from typing import Callable

from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, Session, create_engine

from app.core.config import Settings


def build_engine(settings: Settings) -> Engine:
    connect_args = {}
    if settings.database_url.startswith("sqlite"):
        connect_args["check_same_thread"] = False

    return create_engine(
        settings.database_url,
        echo=settings.environment != "production",
        connect_args=connect_args,
    )


def build_session_factory(engine: Engine) -> Callable[[], Session]:
    return sessionmaker(engine, class_=Session, expire_on_commit=False)


def create_tables(engine: Engine) -> None:
    SQLModel.metadata.create_all(bind=engine)
