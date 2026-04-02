"""add counterparty profile metadata

Revision ID: f7a8b9c0d1e2
Revises: e4a5b6c7d8e9
Create Date: 2026-04-01 21:30:00.000000
"""
from __future__ import annotations

from typing import Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f7a8b9c0d1e2"
down_revision: Union[str, None] = "e4a5b6c7d8e9"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column(
        "counterpartyprofile",
        sa.Column("website", sa.String(), nullable=True),
    )
    op.add_column(
        "counterpartyprofile",
        sa.Column("support_email", sa.String(), nullable=True),
    )
    op.add_column(
        "counterpartyprofile",
        sa.Column("support_url", sa.String(), nullable=True),
    )
    op.add_column(
        "counterpartyprofile",
        sa.Column("notes", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("counterpartyprofile", "notes")
    op.drop_column("counterpartyprofile", "support_url")
    op.drop_column("counterpartyprofile", "support_email")
    op.drop_column("counterpartyprofile", "website")
