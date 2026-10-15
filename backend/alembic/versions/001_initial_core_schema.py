"""Initial core schema with PostGIS extension and core tables

Revision ID: 001_initial_core_schema
Revises: 
Create Date: 2026-10-14 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision: str = "001_initial_core_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Enable PostGIS Extension
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")

    # 2. Users table
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("role", sa.Enum("ADMIN", "AGRONOMIST", "FARMER", name="user_role_enum"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_users_email", "users", ["email"], unique=True)

    # 3. Farms table
    op.create_table(
        "farms",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("owner_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("village", sa.String(length=100), nullable=True),
        sa.Column("district", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("boundary_geom", geoalchemy2.Geometry(geometry_type="POLYGON", srid=4326), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_farms_owner_id", "farms", ["owner_id"])

    # 4. Fields table
    op.create_table(
        "fields",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("farm_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("farms.id", ondelete="CASCADE"), nullable=False),
        sa.Column("field_name", sa.String(length=150), nullable=False),
        sa.Column("crop_type", sa.String(length=100), nullable=True),
        sa.Column("area_hectares", sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column("boundary_geom", geoalchemy2.Geometry(geometry_type="POLYGON", srid=4326), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_fields_farm_id", "fields", ["farm_id"])

    # 5. Surveys table
    op.create_table(
        "surveys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("field_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("fields.id", ondelete="CASCADE"), nullable=False),
        sa.Column("survey_code", sa.String(length=50), nullable=False),
        sa.Column("flight_date", sa.Date(), nullable=False),
        sa.Column("drone_model", sa.String(length=100), nullable=True),
        sa.Column("sensor_type", sa.String(length=50), nullable=False, server_default="RGB"),
        sa.Column("flight_altitude_m", sa.Numeric(precision=6, scale=2), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="DRAFT"),
        sa.Column("coverage_geom", geoalchemy2.Geometry(geometry_type="POLYGON", srid=4326), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_surveys_field_id", "surveys", ["field_id"])
    op.create_index("idx_surveys_code", "surveys", ["survey_code"], unique=True)
    op.create_index("idx_surveys_status", "surveys", ["status"])

    # 6. Survey Files table
    op.create_table(
        "survey_files",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=50), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("blob_uri", sa.String(length=500), nullable=False),
        sa.Column("md5_checksum", sa.String(length=32), nullable=True),
        sa.Column("validation_metadata", postgresql.JSONB(), nullable=True),
        sa.Column("ingestion_status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_survey_files_survey_id", "survey_files", ["survey_id"])

    # 7. Photogrammetry Tasks table
    op.create_table(
        "photogrammetry_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("webodm_task_uuid", sa.String(length=64), nullable=True),
        sa.Column("resolution_preset", sa.String(length=30), nullable=False, server_default="HIGH_RES"),
        sa.Column("generate_dsm", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("generate_dtm", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("radiometric_calibration", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="SUBMITTED"),
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("current_stage", sa.String(length=100), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_tasks_survey_id", "photogrammetry_tasks", ["survey_id"])
    op.create_index("idx_tasks_webodm_uuid", "photogrammetry_tasks", ["webodm_task_uuid"], unique=True)

    # 8. Task Logs table
    op.create_table(
        "task_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("photogrammetry_tasks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("log_level", sa.String(length=20), nullable=False, server_default="INFO"),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("logged_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_task_logs_task_id", "task_logs", ["task_id"])

    # 9. Algorithms table
    op.create_table(
        "algorithms",
        sa.Column("code", sa.String(length=30), primary_key=True),
        sa.Column("display_name", sa.String(length=100), nullable=False),
        sa.Column("required_sensor", sa.String(length=50), nullable=False),
        sa.Column("formula_spec", postgresql.JSONB(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
    )

    # 10. Algorithm Jobs table
    op.create_table(
        "algorithm_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("input_product_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("algorithm_code", sa.String(length=30), sa.ForeignKey("algorithms.code"), nullable=False),
        sa.Column("parameters", postgresql.JSONB(), nullable=True),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="QUEUED"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    # 11. Map Products table
    op.create_table(
        "map_products",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_task_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("photogrammetry_tasks.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_job_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("algorithm_jobs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("product_type", sa.String(length=50), nullable=False),
        sa.Column("blob_uri", sa.String(length=500), nullable=False),
        sa.Column("is_cog", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("band_count", sa.Integer(), nullable=False),
        sa.Column("crs_epsg", sa.String(length=20), nullable=False),
        sa.Column("resolution_cm_px", sa.Numeric(precision=8, scale=2), nullable=True),
        sa.Column("extent_geom", geoalchemy2.Geometry(geometry_type="POLYGON", srid=4326), nullable=True),
        sa.Column("statistical_summary", postgresql.JSONB(), nullable=True),
        sa.Column("is_published", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_map_products_survey_id", "map_products", ["survey_id"])
    op.create_index("idx_map_products_published", "map_products", ["is_published"])

    # 12. Zonal Statistics table
    op.create_table(
        "zonal_statistics",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("map_product_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("map_products.id", ondelete="CASCADE"), nullable=False),
        sa.Column("zone_name", sa.String(length=100), nullable=False),
        sa.Column("min_val", sa.Numeric(precision=6, scale=3), nullable=False),
        sa.Column("max_val", sa.Numeric(precision=6, scale=3), nullable=False),
        sa.Column("area_hectares", sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column("area_percentage", sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )

    # 13. Reports table
    op.create_table(
        "reports",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("survey_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("generated_by_user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("report_number", sa.String(length=50), nullable=False),
        sa.Column("report_title", sa.String(length=200), nullable=False),
        sa.Column("blob_uri", sa.String(length=500), nullable=False),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="QUEUED"),
        sa.Column("report_parameters", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_reports_survey_id", "reports", ["survey_id"])
    op.create_index("idx_reports_number", "reports", ["report_number"], unique=True)

    # 14. Audit Logs table
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), primary_key=True, autoincrement=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(length=50), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("ip_address", postgresql.INET(), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_audit_logs_timestamp", "audit_logs", ["timestamp"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("reports")
    op.drop_table("zonal_statistics")
    op.drop_table("map_products")
    op.drop_table("algorithm_jobs")
    op.drop_table("algorithms")
    op.drop_table("task_logs")
    op.drop_table("photogrammetry_tasks")
    op.drop_table("survey_files")
    op.drop_table("surveys")
    op.drop_table("fields")
    op.drop_table("farms")
    op.drop_table("users")
    op.execute("DROP ENUM IF EXISTS user_role_enum;")
