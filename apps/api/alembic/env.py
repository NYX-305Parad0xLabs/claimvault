from logging.config import fileConfig

from alembic import context
from app.core.config import Settings
from app.core.db import build_engine
from app.models import metadata as models_metadata

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

settings = Settings()
engine = build_engine(settings)

target_metadata = models_metadata


def run_migrations_online() -> None:
    with engine.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    context.configure(url=settings.database_url, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()
else:
    run_migrations_online()
