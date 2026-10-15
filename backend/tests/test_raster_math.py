"""Mathematical and numerical unit tests for Phase 7 vegetation indices."""

import pytest
import numpy as np
from app.services.raster_analytics import (
    RasterAnalyticsService,
    NODATA_VALUE_FLOAT32,
    BandMappingError,
)


def test_ndvi_mathematical_precision():
    """Verify NDVI = (NIR - Red) / (NIR + Red) on known deterministic matrices."""
    nir = np.array([[0.8, 0.6], [0.4, 0.5]], dtype=np.float32)
    red = np.array([[0.2, 0.2], [0.4, 0.1]], dtype=np.float32)

    band_arrays = {"NIR": nir, "Red": red}
    index_array, valid_mask, stats = RasterAnalyticsService.compute_index(band_arrays, "NDVI")

    # (0.8 - 0.2) / (0.8 + 0.2) = 0.6 / 1.0 = 0.60
    assert pytest.approx(index_array[0, 0], rel=1e-4) == 0.60
    # (0.6 - 0.2) / (0.6 + 0.2) = 0.4 / 0.8 = 0.50
    assert pytest.approx(index_array[0, 1], rel=1e-4) == 0.50
    # (0.4 - 0.4) / (0.4 + 0.4) = 0.0 / 0.8 = 0.00
    assert pytest.approx(index_array[1, 0], rel=1e-4) == 0.00
    # (0.5 - 0.1) / (0.5 + 0.1) = 0.4 / 0.6 = 0.6667
    assert pytest.approx(index_array[1, 1], rel=1e-4) == 0.6667

    assert stats["valid_pixel_count"] == 4
    assert stats["nodata_pixel_count"] == 0
    assert pytest.approx(stats["min"], rel=1e-3) == 0.00
    assert pytest.approx(stats["max"], rel=1e-3) == 0.6667


def test_ndre_mathematical_precision():
    """Verify NDRE = (NIR - RedEdge) / (NIR + RedEdge) on known values."""
    nir = np.array([[0.7, 0.9]], dtype=np.float32)
    re = np.array([[0.3, 0.3]], dtype=np.float32)

    band_arrays = {"NIR": nir, "RedEdge": re}
    index_array, valid_mask, stats = RasterAnalyticsService.compute_index(band_arrays, "NDRE")

    # (0.7 - 0.3) / (0.7 + 0.3) = 0.4 / 1.0 = 0.40
    assert pytest.approx(index_array[0, 0], rel=1e-4) == 0.40
    # (0.9 - 0.3) / (0.9 + 0.3) = 0.6 / 1.2 = 0.50
    assert pytest.approx(index_array[0, 1], rel=1e-4) == 0.50
    assert stats["valid_pixel_count"] == 2


def test_gndvi_mathematical_precision():
    """Verify GNDVI = (NIR - Green) / (NIR + Green) on known values."""
    nir = np.array([[0.85]], dtype=np.float32)
    green = np.array([[0.15]], dtype=np.float32)

    band_arrays = {"NIR": nir, "Green": green}
    index_array, valid_mask, stats = RasterAnalyticsService.compute_index(band_arrays, "GNDVI")

    # (0.85 - 0.15) / (0.85 + 0.15) = 0.70 / 1.0 = 0.70
    assert pytest.approx(index_array[0, 0], rel=1e-4) == 0.70


def test_savi_with_soil_adjustment_factors():
    """Verify SAVI = ((NIR - Red) / (NIR + Red + L)) * (1 + L) with L=0.5, L=0.0, L=1.0."""
    nir = np.array([[0.60]], dtype=np.float32)
    red = np.array([[0.20]], dtype=np.float32)
    band_arrays = {"NIR": nir, "Red": red}

    # Case 1: Default L = 0.5
    # ((0.6 - 0.2) / (0.6 + 0.2 + 0.5)) * (1 + 0.5) = (0.4 / 1.3) * 1.5 = 0.4615
    arr_05, _, stats_05 = RasterAnalyticsService.compute_index(band_arrays, "SAVI", parameters={"L": 0.5})
    assert pytest.approx(arr_05[0, 0], rel=1e-4) == 0.4615

    # Case 2: Boundary L = 0.0 (identical to NDVI)
    # ((0.6 - 0.2) / (0.6 + 0.2 + 0.0)) * 1.0 = 0.4 / 0.8 = 0.50
    arr_00, _, _ = RasterAnalyticsService.compute_index(band_arrays, "SAVI", parameters={"L": 0.0})
    assert pytest.approx(arr_00[0, 0], rel=1e-4) == 0.50

    # Case 3: Boundary L = 1.0
    # ((0.6 - 0.2) / (0.6 + 0.2 + 1.0)) * 2.0 = (0.4 / 1.8) * 2.0 = 4 / 9
    arr_10, _, _ = RasterAnalyticsService.compute_index(band_arrays, "SAVI", parameters={"L": 1.0})
    assert pytest.approx(arr_10[0, 0], rel=1e-3) == (4.0 / 9.0)


def test_division_by_zero_and_infinite_safeguards():
    """Ensure zero denominators, NaNs, and infinities are safely masked to NoData."""
    # Pixel [0, 0]: NIR=0, Red=0 -> Denominator is 0
    # Pixel [0, 1]: NIR=NaN -> Non-finite
    # Pixel [1, 0]: Red=Inf -> Non-finite
    # Pixel [1, 1]: NIR=0.5, Red=0.1 -> Valid calculation = (0.5-0.1)/(0.5+0.1) = 0.4/0.6 = 0.6667
    nir = np.array([[0.0, np.nan], [0.5, 0.5]], dtype=np.float32)
    red = np.array([[0.0, 0.2], [np.inf, 0.1]], dtype=np.float32)

    band_arrays = {"NIR": nir, "Red": red}
    index_array, valid_mask, stats = RasterAnalyticsService.compute_index(band_arrays, "NDVI")

    # Invalid pixels must have exact NoData float
    assert index_array[0, 0] == NODATA_VALUE_FLOAT32
    assert index_array[0, 1] == NODATA_VALUE_FLOAT32
    assert index_array[1, 0] == NODATA_VALUE_FLOAT32

    # Single valid pixel
    assert pytest.approx(index_array[1, 1], rel=1e-4) == 0.6667
    assert stats["valid_pixel_count"] == 1
    assert stats["nodata_pixel_count"] == 3
    assert stats["valid_percentage"] == 25.0


def test_source_nodata_propagation():
    """Verify that source NoData pixels are strictly propagated and not converted to 0.0."""
    nir = np.array([[0.7, 0.6], [0.5, 0.4]], dtype=np.float32)
    red = np.array([[0.2, 0.2], [0.1, 0.1]], dtype=np.float32)

    # Pixel [0, 1] is marked as NoData in source raster
    source_nodata_mask = np.array([[False, True], [False, False]], dtype=bool)

    band_arrays = {"NIR": nir, "Red": red}
    index_array, valid_mask, stats = RasterAnalyticsService.compute_index(
        band_arrays, "NDVI", source_nodata_mask=source_nodata_mask
    )

    assert index_array[0, 1] == NODATA_VALUE_FLOAT32
    assert not valid_mask[0, 1]
    assert stats["valid_pixel_count"] == 3
    assert stats["nodata_pixel_count"] == 1


def test_band_mapping_validation_rules():
    """Verify validation rules: required channels, out-of-range bands, duplicate assignments,

    and strict NDRE rejection for RGB.
    """
    # 1. Reject NDRE if RedEdge band is missing
    is_valid, err = RasterAnalyticsService.validate_band_mapping(
        band_count=3,
        mapping={"Red": 1, "Green": 2, "Blue": 3},
        algorithm_code="NDRE",
    )
    assert not is_valid
    assert "RedEdge" in err
    assert "strictly required" in err

    # 2. Reject NDVI if NIR is missing
    is_valid, err = RasterAnalyticsService.validate_band_mapping(
        band_count=3,
        mapping={"Red": 1, "Green": 2, "Blue": 3},
        algorithm_code="NDVI",
    )
    assert not is_valid
    assert "NIR" in err

    # 3. Reject duplicate physical band mapping
    is_valid, err = RasterAnalyticsService.validate_band_mapping(
        band_count=5,
        mapping={"NIR": 1, "Red": 1},  # Reusing Band 1 for both NIR and Red
        algorithm_code="NDVI",
    )
    assert not is_valid
    assert "assigned to both" in err

    # 4. Reject out-of-bounds band index
    is_valid, err = RasterAnalyticsService.validate_band_mapping(
        band_count=4,
        mapping={"NIR": 5, "Red": 2},  # Band 5 does not exist in 4-band image
        algorithm_code="NDVI",
    )
    assert not is_valid
    assert "invalid index 5" in err

    # 5. Accept valid 5-band multispectral mapping
    is_valid, err = RasterAnalyticsService.validate_band_mapping(
        band_count=5,
        mapping={"NIR": 5, "RedEdge": 4, "Red": 3, "Green": 2, "Blue": 1},
        algorithm_code="NDRE",
    )
    assert is_valid
    assert err is None


def test_zonal_statistics_classification():
    """Verify calculation of 4 agronomic vigour zones and hectare area distribution."""
    # Synthetic 100x100 index raster
    index_arr = np.full((100, 100), 0.65, dtype=np.float32)  # High vigour (Zone 4)
    index_arr[0:20, :] = 0.35  # Moderate canopy (Zone 3)
    index_arr[20:30, :] = 0.18  # Bare soil / sparse (Zone 2)
    index_arr[30:35, :] = -0.10  # Water / non-veg (Zone 1)
    index_arr[35:40, :] = NODATA_VALUE_FLOAT32  # 5 rows of NoData

    valid_mask = index_arr != NODATA_VALUE_FLOAT32
    zones = RasterAnalyticsService.calculate_zonal_statistics(
        index_arr, valid_mask, "NDVI", pixel_res_m=0.05
    )

    assert len(zones) == 4
    total_pct = sum(z["area_percentage"] for z in zones)
    assert pytest.approx(total_pct, rel=1e-2) == 100.0

    # Zone names verify
    zone_names = [z["zone_name"] for z in zones]
    assert "Water / Non-vegetated" in zone_names
    assert "Dense / High Vigour" in zone_names
