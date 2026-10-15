"""Phase 10 / Page 2 Photogrammetry Projects and GCP enhancements

Revision ID: 004_photogrammetry_projects_and_gcp
Revises: 003_algorithms_phase7
Create Date: 2026-10-15 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "004_webodm_projects"
down_revision: Union[str, None] = "003_algorithms_phase7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create photogrammetry_projects table
    op.create_table(
        "photogrammetry_projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("farms.id", ondelete="SET NULL"), nullable=True),
        sa.Column("field_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fields.id", ondelete="SET NULL"), nullable=True),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("surveys.id", ondelete="SET NULL"), nullable=True),
        sa.Column("webodm_project_id", sa.Integer(), nullable=True),
        sa.Column("created_by_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(30), nullable=False, server_default="ACTIVE"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("idx_photogrammetry_projects_name", "photogrammetry_projects", ["name"])
    op.create_index("idx_photogrammetry_projects_farm_id", "photogrammetry_projects", ["farm_id"])
    op.create_index("idx_photogrammetry_projects_survey_id", "photogrammetry_projects", ["survey_id"])
    op.create_index("idx_photogrammetry_projects_webodm_id", "photogrammetry_projects", ["webodm_project_id"])

    # 2. Add project_id, gcp_file_id, gcp_applied to photogrammetry_tasks
    op.add_column("photogrammetry_tasks", sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("photogrammetry_projects.id", ondelete="SET NULL"), nullable=True))
    op.add_column("photogrammetry_tasks", sa.Column("gcp_file_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("survey_files.id", ondelete="SET NULL"), nullable=True))
    op.add_column("photogrammetry_tasks", sa.Column("gcp_applied", sa.Boolean(), nullable=False, server_default="false"))
    op.create_index("idx_photogrammetry_tasks_project_id", "photogrammetry_tasks", ["project_id"])


def downgrade() -> None:
    op.drop_index("idx_photogrammetry_tasks_project_id", table_name="photogrammetry_tasks")
    op.drop_column("photogrammetry_tasks", "gcp_applied")
    op.drop_column("photogrammetry_tasks", "gcp_file_id")
    op.drop_column("photogrammetry_tasks", "project_id")

    op.drop_index("idx_photogrammetry_projects_webodm_id", table_name="photogrammetry_projects")
    op.drop_index("idx_photogrammetry_projects_survey_id", table_name="photogrammetry_projects")
    op.drop_index("idx_photogrammetry_projects_farm_id", table_name="photogrammetry_projects")
    op.drop_index("idx_photogrammetry_projects_name", table_name="photogrammetry_projects")
    op.drop_table("photogrammetry_projects")
