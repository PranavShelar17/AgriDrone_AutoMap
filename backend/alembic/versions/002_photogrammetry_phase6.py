"""Phase 6 photogrammetry task schema enhancements

Revision ID: 002_photogrammetry_phase6
Revises: 001_initial_core_schema
Create Date: 2026-10-14 17:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "002_photogrammetry_phase6"
down_revision: Union[str, None] = "001_initial_core_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add source_file_id referencing survey_files
    op.add_column(
        "photogrammetry_tasks",
        sa.Column("source_file_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_photogrammetry_tasks_source_file_id",
        "photogrammetry_tasks",
        "survey_files",
        ["source_file_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "idx_tasks_source_file_id",
        "photogrammetry_tasks",
        ["source_file_id"],
    )

    # 2. Add options JSONB column for custom photogrammetry parameters
    op.add_column(
        "photogrammetry_tasks",
        sa.Column("options", postgresql.JSONB(), nullable=True),
    )

    # 3. Add error_message text column for failure diagnostics
    op.add_column(
        "photogrammetry_tasks",
        sa.Column("error_message", sa.Text(), nullable=True),
    )

    # 4. Add retry_count integer column
    op.add_column(
        "photogrammetry_tasks",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )


def downgrade() -> None:
    op.drop_column("photogrammetry_tasks", "retry_count")
    op.drop_column("photogrammetry_tasks", "error_message")
    op.drop_column("photogrammetry_tasks", "options")
    op.drop_index("idx_tasks_source_file_id", table_name="photogrammetry_tasks")
    op.drop_constraint("fk_photogrammetry_tasks_source_file_id", "photogrammetry_tasks", type_="foreignkey")
    op.drop_column("photogrammetry_tasks", "source_file_id")
