"""End-to-end worker tests for Phase 7 raster analytics and vegetation index generation."""

import os
import tempfile
import uuid
import pytest
import numpy as np
import rasterio
from rasterio.transform import from_origin

from app.db.session import SessionLocal
from app.models.tenant import User
from app.models.farm import Farm, Field
from app.models.survey import Survey
from app.models.product import MapProduct, AlgorithmJob, ZonalStatistic
from app.services.storage import get_storage_service
from app.services.raster_analytics import RasterAnalyticsService
from app.tasks.raster_analytics import execute_algorithm_batch_workflow


@pytest.fixture
def db_session():
    db = SessionLocal()
    yield db
    db.close()


@pytest.fixture
def synthetic_multispectral_geotiff():
    """Generates a deterministic 5-band synthetic GeoTIFF with realistic multispectral values:

    Band 1: Blue (~0.05)
    Band 2: Green (~0.10)
    Band 3: Red (~0.08)
    Band 4: RedEdge (~0.25)
    Band 5: NIR (~0.65)
    """
    temp_dir = tempfile.mkdtemp(prefix="test_synthetic_muls_")
    tif_path = os.path.join(temp_dir, "synthetic_multispectral.tif")

    width, height = 64, 64
    transform = from_origin(750000.0, 2500000.0, 0.05, 0.05)  # 5cm pixel resolution

    # Create synthetic arrays with gradient and some crop variation
    blue = np.full((height, width), 0.05, dtype=np.float32)
    green = np.full((height, width), 0.12, dtype=np.float32)
    red = np.full((height, width), 0.08, dtype=np.float32)
    rededge = np.full((height, width), 0.35, dtype=np.float32)
    nir = np.full((height, width), 0.70, dtype=np.float32)

    # Add a bare soil / road patch in the middle
    red[20:30, 20:30] = 0.30
    green[20:30, 20:30] = 0.25
    nir[20:30, 20:30] = 0.32
    rededge[20:30, 20:30] = 0.31

    with rasterio.open(
        tif_path,
        "w",
        driver="GTiff",
        height=height,
        width=width,
        count=5,
        dtype="float32",
        crs="EPSG:32643",
        transform=transform,
        nodata=-9999.0,
    ) as dst:
        dst.write(blue, 1)
        dst.write(green, 2)
        dst.write(red, 3)
        dst.write(rededge, 4)
        dst.write(nir, 5)
        dst.set_band_description(1, "Blue")
        dst.set_band_description(2, "Green")
        dst.set_band_description(3, "Red")
        dst.set_band_description(4, "RedEdge")
        dst.set_band_description(5, "NIR")

    yield tif_path

    if os.path.exists(temp_dir):
        import shutil
        shutil.rmtree(temp_dir)


@pytest.fixture
def test_setup_with_orthophoto(db_session, synthetic_multispectral_geotiff):
    """Sets up a farm, field, survey, and MapProduct referencing the synthetic multispectral GeoTIFF."""
    storage = get_storage_service()

    # Upload synthetic GeoTIFF to local storage
    blob_path = f"test_surveys/{uuid.uuid4()}/synthetic_ortho.tif"
    with open(synthetic_multispectral_geotiff, "rb") as f:
        upload_res = storage.upload_file(
            file_obj=f,
            container="orthomosaics",
            blob_path=blob_path,
            content_type="image/tiff",
        )

    # Create DB records
    user = db_session.query(User).first()
    farm = Farm(owner_id=user.id, name="Test Spectral Farm", state="Punjab", district="Ludhiana")
    db_session.add(farm)
    db_session.flush()

    field = Field(farm_id=farm.id, field_name="Field North", area_hectares=10.0, crop_type="WHEAT")
    db_session.add(field)
    db_session.flush()

    from datetime import date
    survey = Survey(
        field_id=field.id,
        survey_code=f"SRV-TEST-{uuid.uuid4().hex[:6]}",
        flight_date=date.today(),
        sensor_type="MULTISPECTRAL",
        status="COMPLETED",
    )
    db_session.add(survey)
    db_session.flush()

    map_product = MapProduct(
        survey_id=survey.id,
        product_type="ORTHOPHOTO",
        blob_uri=upload_res["blob_uri"],
        is_cog=True,
        band_count=5,
        crs_epsg="EPSG:32643",
        resolution_cm_px=5.0,
        is_published=False,
    )
    db_session.add(map_product)
    db_session.commit()
    db_session.refresh(map_product)

    return {
        "farm": farm,
        "field": field,
        "survey": survey,
        "map_product": map_product,
        "tif_path": synthetic_multispectral_geotiff,
    }


def test_raster_inspection_synthetic(synthetic_multispectral_geotiff):
    """Verify raster inspection accurately extracts 5 bands, GSD, and sensor type."""
    inspection = RasterAnalyticsService.inspect_raster(synthetic_multispectral_geotiff)

    assert inspection.band_count == 5
    assert inspection.width == 64
    assert inspection.height == 64
    assert inspection.detected_sensor == "MULTISPECTRAL"
    assert inspection.crs_epsg == "EPSG:32643"
    assert inspection.suggested_band_mapping["NIR"] == 5
    assert inspection.suggested_band_mapping["RedEdge"] == 4
    assert inspection.suggested_band_mapping["Red"] == 3
    assert "NDVI" in inspection.supported_algorithms
    assert "NDRE" in inspection.supported_algorithms


def test_execute_multi_map_batch_workflow(db_session, test_setup_with_orthophoto):
    """Verify multi-algorithm batch execution (NDVI, NDRE, GNDVI, SAVI) produces valid

    Cloud-Optimized GeoTIFF outputs, MapProduct records, and ZonalStatistic records.
    """
    map_product = test_setup_with_orthophoto["map_product"]
    batch_id = uuid.uuid4()

    band_mapping = {"Blue": 1, "Green": 2, "Red": 3, "RedEdge": 4, "NIR": 5}

    # Create 4 jobs: NDVI, NDRE, GNDVI, SAVI
    job_ndvi = AlgorithmJob(
        batch_id=batch_id,
        input_product_id=map_product.id,
        algorithm_code="NDVI",
        parameters={"band_mapping": band_mapping},
        status="QUEUED",
        progress_percent=0,
    )
    job_ndre = AlgorithmJob(
        batch_id=batch_id,
        input_product_id=map_product.id,
        algorithm_code="NDRE",
        parameters={"band_mapping": band_mapping},
        status="QUEUED",
        progress_percent=0,
    )
    job_gndvi = AlgorithmJob(
        batch_id=batch_id,
        input_product_id=map_product.id,
        algorithm_code="GNDVI",
        parameters={"band_mapping": band_mapping},
        status="QUEUED",
        progress_percent=0,
    )
    job_savi = AlgorithmJob(
        batch_id=batch_id,
        input_product_id=map_product.id,
        algorithm_code="SAVI",
        parameters={"band_mapping": band_mapping, "L": 0.5},
        status="QUEUED",
        progress_percent=0,
    )

    db_session.add_all([job_ndvi, job_ndre, job_gndvi, job_savi])
    db_session.commit()

    # Execute workflow synchronously
    execute_algorithm_batch_workflow(str(batch_id))

    # Verify all jobs completed
    completed_jobs = db_session.query(AlgorithmJob).filter(AlgorithmJob.batch_id == batch_id).all()
    assert len(completed_jobs) == 4

    for j in completed_jobs:
        assert j.status == "COMPLETED", f"Job {j.algorithm_code} failed: {j.error_message}"
        assert j.progress_percent == 100
        assert j.output_product_id is not None

        # Verify output MapProduct
        output_mp = db_session.query(MapProduct).filter(MapProduct.id == j.output_product_id).first()
        assert output_mp is not None
        assert output_mp.product_type == f"INDEX_{j.algorithm_code}"
        assert output_mp.band_count == 1
        assert output_mp.is_cog is True
        assert output_mp.crs_epsg == "EPSG:32643"

        # Verify statistical summary is populated
        summary = output_mp.statistical_summary
        assert summary is not None
        assert "min" in summary
        assert "max" in summary
        assert summary["valid_pixels"] > 0
        assert summary["valid_percentage"] > 90.0

        # Verify zonal statistics
        z_stats = db_session.query(ZonalStatistic).filter(ZonalStatistic.map_product_id == output_mp.id).all()
        assert len(z_stats) == 4
        total_pct = sum(float(zs.area_percentage) for zs in z_stats)
        assert pytest.approx(total_pct, rel=1e-2) == 100.0


def test_ndre_rejected_on_rgb_imagery(db_session, test_setup_with_orthophoto):
    """Verify that NDRE is strictly rejected when RedEdge band is not available or mapped."""
    map_product = test_setup_with_orthophoto["map_product"]
    batch_id = uuid.uuid4()

    # Provide only 3-band RGB mapping without RedEdge
    rgb_mapping = {"Red": 1, "Green": 2, "Blue": 3}

    job_ndre = AlgorithmJob(
        batch_id=batch_id,
        input_product_id=map_product.id,
        algorithm_code="NDRE",
        parameters={"band_mapping": rgb_mapping},
        status="QUEUED",
        progress_percent=0,
    )
    db_session.add(job_ndre)
    db_session.commit()

    execute_algorithm_batch_workflow(str(batch_id))

    db_session.refresh(job_ndre)
    assert job_ndre.status == "FAILED"
    assert "RedEdge" in job_ndre.error_message
    assert "strictly required" in job_ndre.error_message
