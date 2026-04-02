"""evidence ingestion metadata

Revision ID: e4a5b6c7d8e9
Revises: d3f4e1c7b2a0
Create Date: 2026-04-01 20:45:00.000000
"""
from __future__ import annotations

from typing import Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e4a5b6c7d8e9"
down_revision: Union[str, None] = "d3f4e1c7b2a0"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None


def upgrade() -> None:
    op.add_column(
        "evidenceitem",
        sa.Column("merchant_label", sa.String(), nullable=True),
    )
    op.add_column(
        "evidenceitem",
        sa.Column("carrier_label", sa.String(), nullable=True),
    )
    op.add_column(
        "evidenceitem",
        sa.Column("platform_label", sa.String(), nullable=True),
    )
    op.add_column(
        "evidenceitem",
        sa.Column("event_date", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "evidenceitem",
        sa.Column("description", sa.String(), nullable=True),
    )
    op.add_column(
        "evidenceitem",
        sa.Column(
            "manual_relevance",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "evidenceitem",
        sa.Column("deleted_at", sa.DateTime(), nullable=True),
    )
    op.add_column(
        "evidenceitem",
        sa.Column("deleted_by", sa.Integer(), nullable=True),
    )
    with op.batch_alter_table("evidenceitem") as batch_op:
        batch_op.create_foreign_key(
            op.f("fk_evidenceitem_deleted_by"),
            "user",
            ["deleted_by"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("evidenceitem") as batch_op:
        batch_op.drop_constraint(
            op.f("fk_evidenceitem_deleted_by"),
            type_="foreignkey",
        )
    for column in (
        "deleted_by",
        "deleted_at",
        "manual_relevance",
        "description",
        "event_date",
        "platform_label",
        "carrier_label",
        "merchant_label",
    ):
        with op.batch_alter_table("evidenceitem") as batch_op:
            batch_op.drop_column(column)
