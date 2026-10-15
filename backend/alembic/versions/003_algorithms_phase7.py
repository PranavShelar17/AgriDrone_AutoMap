"""Phase 7 algorithm and vegetation index schema enhancements

Revision ID: 003_algorithms_phase7
Revises: 002_photogrammetry_phase6
Create Date: 2026-10-15 10:45:00.000000

"""
from typing import Sequence, Union
import json
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "003_algorithms_phase7"
down_revision: Union[str, None] = "002_photogrammetry_phase6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add batch_id to algorithm_jobs to group multi-map batch executions
    op.add_column(
        "algorithm_jobs",
        sa.Column("batch_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_index(
        "idx_algorithm_jobs_batch_id",
        "algorithm_jobs",
        ["batch_id"],
    )

    # 2. Add progress_percent and current_stage for granular background telemetry
    op.add_column(
        "algorithm_jobs",
        sa.Column("progress_percent", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "algorithm_jobs",
        sa.Column("current_stage", sa.String(length=100), nullable=True, server_default="QUEUED"),
    )

    # 3. Add output_product_id referencing map_products
    op.add_column(
        "algorithm_jobs",
        sa.Column("output_product_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_algorithm_jobs_output_product_id",
        "algorithm_jobs",
        "map_products",
        ["output_product_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "idx_algorithm_jobs_output_product_id",
        "algorithm_jobs",
        ["output_product_id"],
    )

    # 4. Add retry_count to algorithm_jobs
    op.add_column(
        "algorithm_jobs",
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
    )

    # 5. Add foreign key from algorithm_jobs.input_product_id to map_products.id
    op.create_foreign_key(
        "fk_algorithm_jobs_input_product_id",
        "algorithm_jobs",
        "map_products",
        ["input_product_id"],
        ["id"],
        ondelete="RESTRICT",
    )
    op.create_index(
        "idx_algorithm_jobs_input_product_id",
        "algorithm_jobs",
        ["input_product_id"],
    )

    # 6. Seed algorithms table with standard vegetation indices
    algorithms_table = sa.table(
        "algorithms",
        sa.column("code", sa.String),
        sa.column("display_name", sa.String),
        sa.column("required_sensor", sa.String),
        sa.column("formula_spec", postgresql.JSONB),
        sa.column("description", sa.Text),
    )

    seed_algorithms = [
        {
            "code": "NDVI",
            "display_name": "Normalized Difference Vegetation Index",
            "required_sensor": "MULTISPECTRAL",
            "formula_spec": {
                "formula": "(NIR - Red) / (NIR + Red)",
                "required_bands": ["NIR", "Red"],
                "min_val": -1.0,
                "max_val": 1.0,
                "description": "Standardized index calculating relative vegetative vigour and biomass canopy coverage."
            },
            "description": "Standardized index measuring live green plant canopy density and photosynthetic activity. Requires NIR and Red bands."
        },
        {
            "code": "NDRE",
            "display_name": "Normalized Difference Red Edge",
            "required_sensor": "MULTISPECTRAL",
            "formula_spec": {
                "formula": "(NIR - RedEdge) / (NIR + RedEdge)",
                "required_bands": ["NIR", "RedEdge"],
                "min_val": -1.0,
                "max_val": 1.0,
                "description": "Index sensitive to chlorophyll content in mid-to-late growth stages and dense vegetative canopies."
            },
            "description": "Utilizes the narrow RedEdge spectral band to assess chlorophyll absorption without saturation in dense vegetation."
        },
        {
            "code": "GNDVI",
            "display_name": "Green Normalized Difference Vegetation Index",
            "required_sensor": "MULTISPECTRAL",
            "formula_spec": {
                "formula": "(NIR - Green) / (NIR + Green)",
                "required_bands": ["NIR", "Green"],
                "min_val": -1.0,
                "max_val": 1.0,
                "description": "Alternative index sensitive to chlorophyll concentration and photosynthetic activity."
            },
            "description": "Uses the green band instead of the red band, providing wider sensitivity to varying chlorophyll levels in dense crops."
        },
        {
            "code": "SAVI",
            "display_name": "Soil-Adjusted Vegetation Index",
            "required_sensor": "MULTISPECTRAL",
            "formula_spec": {
                "formula": "((NIR - Red) / (NIR + Red + L)) * (1 + L)",
                "required_bands": ["NIR", "Red"],
                "parameters": {
                    "L": {
                        "type": "float",
                        "default": 0.5,
                        "min": 0.0,
                        "max": 1.0,
                        "description": "Canopy background soil adjustment factor (default 0.5 for intermediate vegetation)."
                    }
                },
                "min_val": -1.5,
                "max_val": 1.5,
                "description": "Vegetation index that introduces a soil-brightness correction factor L to attenuate soil reflectance effects."
            },
            "description": "Minimizes soil brightness influences in sparse canopies or early crop emergence stages using a configurable parameter L."
        },
        {
            "code": "VARI",
            "display_name": "Visible Atmospherically Resistant Index",
            "required_sensor": "RGB",
            "formula_spec": {
                "formula": "(Green - Red) / (Green + Red - Blue)",
                "required_bands": ["Green", "Red", "Blue"],
                "min_val": -1.0,
                "max_val": 1.0,
                "description": "Visible spectrum index estimating vegetation fraction while minimizing atmospheric distortion."
            },
            "description": "Computable from standard RGB orthophotos when near-infrared sensors are not available."
        },
        {
            "code": "GLI",
            "display_name": "Green Leaf Index",
            "required_sensor": "RGB",
            "formula_spec": {
                "formula": "(2 * Green - Red - Blue) / (2 * Green + Red + Blue)",
                "required_bands": ["Green", "Red", "Blue"],
                "min_val": -1.0,
                "max_val": 1.0,
                "description": "Calculates green leaf reflection against soil and residue using standard RGB cameras."
            },
            "description": "Evaluates crop greenness and canopy ground cover fraction using standard RGB sensor imagery."
        },
    ]

    for algo in seed_algorithms:
        op.execute(
            sa.text(
                "INSERT INTO algorithms (code, display_name, required_sensor, formula_spec, description) "
                "VALUES (:code, :display_name, :required_sensor, :formula_spec, :description) "
                "ON CONFLICT (code) DO UPDATE SET "
                "display_name = EXCLUDED.display_name, "
                "required_sensor = EXCLUDED.required_sensor, "
                "formula_spec = EXCLUDED.formula_spec, "
                "description = EXCLUDED.description;"
            ).bindparams(
                code=algo["code"],
                display_name=algo["display_name"],
                required_sensor=algo["required_sensor"],
                formula_spec=json.dumps(algo["formula_spec"]),
                description=algo["description"],
            )
        )


def downgrade() -> None:
    op.drop_constraint("fk_algorithm_jobs_input_product_id", "algorithm_jobs", type_="foreignkey")
    op.drop_index("idx_algorithm_jobs_input_product_id", table_name="algorithm_jobs")
    op.drop_constraint("fk_algorithm_jobs_output_product_id", "algorithm_jobs", type_="foreignkey")
    op.drop_index("idx_algorithm_jobs_output_product_id", table_name="algorithm_jobs")
    op.drop_column("algorithm_jobs", "retry_count")
    op.drop_column("algorithm_jobs", "output_product_id")
    op.drop_column("algorithm_jobs", "current_stage")
    op.drop_column("algorithm_jobs", "progress_percent")
    op.drop_index("idx_algorithm_jobs_batch_id", table_name="algorithm_jobs")
    op.drop_column("algorithm_jobs", "batch_id")
