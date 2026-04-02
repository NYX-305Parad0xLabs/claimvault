"""domain rework

Revision ID: d3f4e1c7b2a0
Revises: a0c2e1b8d051
Create Date: 2026-04-01 20:30:00.000000
"""
from __future__ import annotations

from datetime import datetime
from typing import Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "d3f4e1c7b2a0"
down_revision: Union[str, None] = "a0c2e1b8d051"
branch_labels: Union[str, None] = None
depends_on: Union[str, None] = None

EXTRACTION_STATUS_ENUM = sa.Enum("pending", "completed", "failed", name="extractionstatus")


def upgrade() -> None:
    op.create_table(
        "counterpartyprofile",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("profile_type", sa.String(), nullable=False),
        sa.Column("metadata_json", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_counterpartyprofile_workspace_id"),
        "counterpartyprofile",
        ["workspace_id"],
        unique=False,
    )

    op.create_table(
        "claimtemplate",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("workspace_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("required_fields", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspace.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_claimtemplate_workspace_id"),
        "claimtemplate",
        ["workspace_id"],
        unique=False,
    )

    with op.batch_alter_table("case") as batch_op:
        batch_op.add_column(
            sa.Column("template_id", sa.Integer(), nullable=True),
        )
        batch_op.add_column(
            sa.Column("counterparty_profile_id", sa.Integer(), nullable=True),
        )
        batch_op.create_foreign_key(
            op.f("fk_case_template_id"),
            "claimtemplate",
            ["template_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            op.f("fk_case_counterparty_profile_id"),
            "counterpartyprofile",
            ["counterparty_profile_id"],
            ["id"],
        )

    op.create_table(
        "missing_evidence_check",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("rule_key", sa.String(), nullable=False),
        sa.Column("description", sa.String(), nullable=False),
        sa.Column("required", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("satisfied", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("last_checked_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["case.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_missing_evidence_check_case_id"),
        "missing_evidence_check",
        ["case_id"],
        unique=False,
    )

    op.create_table(
        "exportartifact",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("artifact_type", sa.String(), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("manifest_hash", sa.String(), nullable=True),
        sa.Column("archive_hash", sa.String(), nullable=True),
        sa.Column("metadata_json", sa.JSON(), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["case.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_exportartifact_case_id"),
        "exportartifact",
        ["case_id"],
        unique=False,
    )

    EXTRACTION_STATUS_ENUM.create(op.get_bind(), checkfirst=False)
    op.add_column(
        "evidenceitem",
        sa.Column(
            "extraction_status",
            EXTRACTION_STATUS_ENUM,
            nullable=False,
            server_default="pending",
        ),
    )

    op.drop_index(op.f("ix_caseexport_case_id"), table_name="caseexport")
    op.drop_table("caseexport")


def downgrade() -> None:
    with op.batch_alter_table("case") as batch_op:
        batch_op.drop_constraint(
            op.f("fk_case_counterparty_profile_id"),
            type_="foreignkey",
        )
        batch_op.drop_constraint(
            op.f("fk_case_template_id"),
            type_="foreignkey",
        )
        batch_op.drop_column("counterparty_profile_id")
        batch_op.drop_column("template_id")

    op.drop_index(op.f("ix_exportartifact_case_id"), table_name="exportartifact")
    op.drop_table("exportartifact")

    op.drop_index(
        op.f("ix_missing_evidence_check_case_id"),
        table_name="missing_evidence_check",
    )
    op.drop_table("missing_evidence_check")

    op.drop_column("evidenceitem", "extraction_status")
    EXTRACTION_STATUS_ENUM.drop(op.get_bind(), checkfirst=False)

    op.drop_index(
        op.f("ix_claimtemplate_workspace_id"),
        table_name="claimtemplate",
    )
    op.drop_table("claimtemplate")

    op.drop_index(
        op.f("ix_counterpartyprofile_workspace_id"),
        table_name="counterpartyprofile",
    )
    op.drop_table("counterpartyprofile")

    op.create_table(
        "caseexport",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("case_id", sa.Integer(), nullable=False),
        sa.Column("export_format", sa.String(), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["case_id"], ["case.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_caseexport_case_id"),
        "caseexport",
        ["case_id"],
        unique=False,
    )
