"""Raster Analytics & Vegetation Indices Processing Engine.

Phase 7 GIS Algorithms & Remote Sensing Module.
Calculates scientifically defensible spectral vegetation indices (NDVI, NDRE, GNDVI, SAVI, VARI, GLI)
from multispectral and RGB drone orthomosaics with robust numerical safeguards, NoData propagation,
zonal statistics, and Cloud-Optimized GeoTIFF export.
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict

import numpy as np
import rasterio
from rasterio.crs import CRS
from rasterio.transform import Affine
from rasterio.enums import Resampling

logger = logging.getLogger(__name__)

# Standard NoData value for all generated index rasters
NODATA_VALUE_FLOAT32 = -9999.0
NUMERICAL_EPSILON = 1e-6


@dataclass
class BandSummary:
    band_index: int  # 1-based index
    data_type: str
    nodata_value: Optional[float]
    min_value: float
    max_value: float
    mean_value: float
    std_value: float
    description: Optional[str] = None


@dataclass
class RasterInspection:
    file_path: str
    width: int
    height: int
    band_count: int
    crs_epsg: Optional[str]
    crs_wkt: Optional[str]
    bounds: Tuple[float, float, float, float]  # left, bottom, right, top
    transform: List[float]  # 6-element Affine tuple
    resolution_x: float
    resolution_y: float
    gsd_cm: float
    detected_sensor: str  # "MULTISPECTRAL" or "RGB"
    radiometric_type: str  # "REFLECTANCE_FLOAT", "DIGITAL_NUMBERS_16BIT", "DIGITAL_NUMBERS_8BIT", "UNKNOWN"
    calibration_notes: List[str]
    suggested_band_mapping: Dict[str, int]
    supported_algorithms: List[str]
    bands: List[BandSummary]


class RasterAnalyticsError(Exception):
    """Base exception for raster analytics operations."""
    pass


class BandMappingError(RasterAnalyticsError):
    """Raised when band mapping is invalid or required bands are missing."""
    pass


class NumericalProcessingError(RasterAnalyticsError):
    """Raised when numerical calculation produces invalid or all-nodata outputs."""
    pass


class RasterAnalyticsService:
    """Core GIS and remote sensing service for drone orthomosaics."""

    # Supported algorithm definitions
    ALGORITHM_SPECS = {
        "NDVI": {
            "name": "Normalized Difference Vegetation Index",
            "required_bands": ["NIR", "Red"],
            "sensor": "MULTISPECTRAL",
            "formula": "(NIR - Red) / (NIR + Red)",
            "expected_range": (-1.0, 1.0),
            "description": "Standardized index measuring live green plant canopy density and photosynthetic vigour.",
        },
        "NDRE": {
            "name": "Normalized Difference Red Edge",
            "required_bands": ["NIR", "RedEdge"],
            "sensor": "MULTISPECTRAL",
            "formula": "(NIR - RedEdge) / (NIR + RedEdge)",
            "expected_range": (-1.0, 1.0),
            "description": "Utilizes narrow RedEdge band to assess chlorophyll absorption without saturation in dense vegetation.",
        },
        "GNDVI": {
            "name": "Green Normalized Difference Vegetation Index",
            "required_bands": ["NIR", "Green"],
            "sensor": "MULTISPECTRAL",
            "formula": "(NIR - Green) / (NIR + Green)",
            "expected_range": (-1.0, 1.0),
            "description": "Uses green band instead of red, providing enhanced sensitivity to varying chlorophyll levels in dense crops.",
        },
        "SAVI": {
            "name": "Soil-Adjusted Vegetation Index",
            "required_bands": ["NIR", "Red"],
            "sensor": "MULTISPECTRAL",
            "formula": "((NIR - Red) / (NIR + Red + L)) * (1 + L)",
            "expected_range": (-1.5, 1.5),
            "description": "Minimizes soil brightness influences in sparse canopies using a configurable soil adjustment factor L.",
            "default_parameters": {"L": 0.5},
        },
        "VARI": {
            "name": "Visible Atmospherically Resistant Index",
            "required_bands": ["Green", "Red", "Blue"],
            "sensor": "RGB",
            "formula": "(Green - Red) / (Green + Red - Blue)",
            "expected_range": (-1.0, 1.0),
            "description": "Visible spectrum index estimating vegetation fraction while minimizing atmospheric distortion.",
        },
        "GLI": {
            "name": "Green Leaf Index",
            "required_bands": ["Green", "Red", "Blue"],
            "sensor": "RGB",
            "formula": "(2 * Green - Red - Blue) / (2 * Green + Red + Blue)",
            "expected_range": (-1.0, 1.0),
            "description": "Evaluates green leaf reflection against soil background from standard RGB sensors.",
        },
    }

    @classmethod
    def inspect_raster(cls, file_path: str) -> RasterInspection:
        """Thoroughly inspects a raster file, extracting geospatial metadata, per-band stats,

        sensor type, and suggested spectral channel mapping.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Raster file not found: {file_path}")

        try:
            with rasterio.open(file_path) as src:
                width = src.width
                height = src.height
                band_count = src.count

                # Extract CRS
                crs_epsg = None
                crs_wkt = None
                if src.crs:
                    if src.crs.is_epsg_code:
                        crs_epsg = f"EPSG:{src.crs.to_epsg()}"
                    else:
                        crs_epsg = str(src.crs)
                    crs_wkt = src.crs.to_wkt()

                # Extract transform and resolution
                transform = src.transform
                res_x = abs(transform[0])
                res_y = abs(transform[4])

                # Estimate GSD in centimeters
                # If projected (meters): res * 100
                # If geographic (degrees): approx 111320 meters per degree
                is_projected = src.crs.is_projected if src.crs else False
                if is_projected:
                    gsd_cm = round(((res_x + res_y) / 2.0) * 100.0, 2)
                else:
                    gsd_cm = round(((res_x + res_y) / 2.0) * 111320.0 * 100.0, 2)

                bounds = (src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top)

                # Inspect bands and collect statistics (using downsampled overview if large)
                bands_summary: List[BandSummary] = []
                max_overall_val = 0.0
                min_overall_val = 0.0

                for b_idx in range(1, band_count + 1):
                    dtype_str = str(src.dtypes[b_idx - 1])
                    nodata_val = src.nodatavals[b_idx - 1]
                    b_desc = src.descriptions[b_idx - 1] if src.descriptions else None

                    # Read sample for fast stats calculation
                    # For rasters > 2000x2000, read step-sliced sample to keep response responsive
                    step = max(1, int(max(width, height) / 1000))
                    sample = src.read(b_idx, out_shape=(height // step, width // step), resampling=Resampling.nearest)
                    sample = sample.astype(np.float64)

                    # Filter nodata
                    if nodata_val is not None:
                        valid_sample = sample[sample != nodata_val]
                    else:
                        valid_sample = sample[np.isfinite(sample)]

                    if valid_sample.size > 0:
                        b_min = float(np.min(valid_sample))
                        b_max = float(np.max(valid_sample))
                        b_mean = float(np.mean(valid_sample))
                        b_std = float(np.std(valid_sample))
                        max_overall_val = max(max_overall_val, b_max)
                        min_overall_val = min(min_overall_val, b_min)
                    else:
                        b_min, b_max, b_mean, b_std = 0.0, 0.0, 0.0, 0.0

                    bands_summary.append(
                        BandSummary(
                            band_index=b_idx,
                            data_type=dtype_str,
                            nodata_value=nodata_val,
                            min_value=round(b_min, 4),
                            max_value=round(b_max, 4),
                            mean_value=round(b_mean, 4),
                            std_value=round(b_std, 4),
                            description=b_desc,
                        )
                    )

                # Determine radiometric scale and sensor type
                calibration_notes = []
                if max_overall_val <= 1.05 and min_overall_val >= -0.05:
                    radiometric_type = "REFLECTANCE_FLOAT"
                    calibration_notes.append("Pixel values appear to be in standardized surface reflectance range [0.0, 1.0].")
                elif max_overall_val > 255:
                    radiometric_type = "DIGITAL_NUMBERS_16BIT"
                    calibration_notes.append("Values appear to be 16-bit uncalibrated Digital Numbers (DN) or scaled integers.")
                    calibration_notes.append("Scientific notice: Index formulas will be computed from relative digital numbers without surface reflectance normalization.")
                else:
                    radiometric_type = "DIGITAL_NUMBERS_8BIT"
                    calibration_notes.append("Values appear to be 8-bit RGB Digital Numbers (0-255).")

                # Detect sensor and construct suggested band mapping
                suggested_mapping: Dict[str, int] = {}
                supported_algorithms: List[str] = []

                # Check tags or band descriptions for explicit spectral bands
                has_explicit_nir = False
                has_explicit_rededge = False

                for b in bands_summary:
                    desc_lower = (b.description or "").lower()
                    if "nir" in desc_lower or "near-infrared" in desc_lower or "near infrared" in desc_lower:
                        suggested_mapping["NIR"] = b.band_index
                        has_explicit_nir = True
                    elif "rededge" in desc_lower or "red edge" in desc_lower or "re" == desc_lower:
                        suggested_mapping["RedEdge"] = b.band_index
                        has_explicit_rededge = True
                    elif "red" in desc_lower:
                        suggested_mapping["Red"] = b.band_index
                    elif "green" in desc_lower:
                        suggested_mapping["Green"] = b.band_index
                    elif "blue" in desc_lower:
                        suggested_mapping["Blue"] = b.band_index

                if band_count >= 5:
                    detected_sensor = "MULTISPECTRAL"
                    if not suggested_mapping:
                        # Standard 5-band sensor (e.g. Micasense RedEdge, DJI P4 Multispectral):
                        # 1: Blue, 2: Green, 3: Red, 4: RedEdge, 5: NIR
                        suggested_mapping = {
                            "Blue": 1,
                            "Green": 2,
                            "Red": 3,
                            "RedEdge": 4,
                            "NIR": 5,
                        }
                    supported_algorithms = ["NDVI", "NDRE", "GNDVI", "SAVI", "VARI", "GLI"]
                elif band_count == 4:
                    detected_sensor = "MULTISPECTRAL"
                    if not suggested_mapping:
                        # Common 4-band configuration (Green, Red, RedEdge, NIR or RGB+NIR)
                        suggested_mapping = {
                            "Green": 1,
                            "Red": 2,
                            "RedEdge": 3,
                            "NIR": 4,
                        }
                    supported_algorithms = ["NDVI", "NDRE", "GNDVI", "SAVI"]
                elif band_count == 3:
                    detected_sensor = "RGB"
                    if not suggested_mapping:
                        suggested_mapping = {
                            "Red": 1,
                            "Green": 2,
                            "Blue": 3,
                        }
                    supported_algorithms = ["VARI", "GLI"]
                    calibration_notes.append(
                        "Sensor identified as standard 3-band RGB. Multispectral indices (NDVI, NDRE, GNDVI, SAVI) "
                        "require a validated Near-Infrared (NIR) band and are strictly unavailable."
                    )
                else:
                    detected_sensor = "SINGLE_BAND_OR_OTHER"
                    calibration_notes.append(f"Unexpected band count: {band_count}. Manual band mapping required.")

                return RasterInspection(
                    file_path=file_path,
                    width=width,
                    height=height,
                    band_count=band_count,
                    crs_epsg=crs_epsg,
                    crs_wkt=crs_wkt,
                    bounds=bounds,
                    transform=[transform.a, transform.b, transform.c, transform.d, transform.e, transform.f],
                    resolution_x=res_x,
                    resolution_y=res_y,
                    gsd_cm=gsd_cm,
                    detected_sensor=detected_sensor,
                    radiometric_type=radiometric_type,
                    calibration_notes=calibration_notes,
                    suggested_band_mapping=suggested_mapping,
                    supported_algorithms=supported_algorithms,
                    bands=bands_summary,
                )

        except Exception as e:
            logger.error("Failed to inspect raster %s: %s", file_path, str(e))
            raise RasterAnalyticsError(f"Raster inspection failed: {str(e)}") from e

    @classmethod
    def validate_band_mapping(
        cls,
        band_count: int,
        mapping: Dict[str, int],
        algorithm_code: str,
    ) -> Tuple[bool, Optional[str]]:
        """Validates that user/auto band mapping satisfies all requirements for the chosen algorithm.

        Returns (is_valid, error_reason).
        """
        algo_code = algorithm_code.upper()
        if algo_code not in cls.ALGORITHM_SPECS:
            return False, f"Unknown algorithm code: '{algo_code}'. Supported: {list(cls.ALGORITHM_SPECS.keys())}"

        spec = cls.ALGORITHM_SPECS[algo_code]
        required_bands = spec["required_bands"]

        # Check required bands are mapped
        missing_bands = [b for b in required_bands if b not in mapping or mapping[b] is None]
        if missing_bands:
            if algo_code == "NDRE" and "RedEdge" in missing_bands:
                return (
                    False,
                    "NDRE cannot be generated because this dataset does not contain a validated RedEdge band. "
                    "RedEdge (705-745nm) is strictly required for NDRE calculation.",
                )
            if algo_code in ("NDVI", "GNDVI", "SAVI") and "NIR" in missing_bands:
                return (
                    False,
                    f"{algo_code} cannot be generated because Near-Infrared (NIR) is not mapped or unavailable. "
                    "RGB-only imagery cannot compute NIR-based vegetation indices.",
                )
            return False, f"Algorithm {algo_code} requires bands {required_bands}, but {missing_bands} are missing from mapping."

        # Check band indices are valid 1-based integers within [1, band_count]
        used_indices = {}
        for b_name in required_bands:
            idx = mapping[b_name]
            if not isinstance(idx, int) or idx < 1 or idx > band_count:
                return False, f"Band '{b_name}' mapped to invalid index {idx}. Must be an integer between 1 and {band_count}."
            if idx in used_indices:
                other_band = used_indices[idx]
                return (
                    False,
                    f"Physical Band {idx} is assigned to both '{other_band}' and '{b_name}'. "
                    "Different spectral channels must map to distinct physical bands.",
                )
            used_indices[idx] = b_name

        return True, None

    @classmethod
    def compute_index(
        cls,
        band_arrays: Dict[str, np.ndarray],
        algorithm_code: str,
        parameters: Optional[Dict[str, Any]] = None,
        source_nodata_mask: Optional[np.ndarray] = None,
    ) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
        """Pure NumPy spectral index calculator with division-by-zero protection,

        NoData masking, and numerical validation.

        Returns:
            index_array: np.ndarray (float32) with NODATA_VALUE_FLOAT32 for invalid pixels
            valid_mask: np.ndarray (bool) indicating valid calculated pixels
            calc_stats: Dict with min, max, mean, std, valid_count, nodata_count
        """
        algo_code = algorithm_code.upper()
        if algo_code not in cls.ALGORITHM_SPECS:
            raise RasterAnalyticsError(f"Unsupported algorithm: {algo_code}")

        params = parameters or {}
        first_band = next(iter(band_arrays.values()))
        height, width = first_band.shape
        total_pixels = height * width

        # Base valid mask: finite in all inputs, not in source nodata mask
        valid_mask = np.ones((height, width), dtype=bool)
        if source_nodata_mask is not None:
            valid_mask &= ~source_nodata_mask

        for b_name, arr in band_arrays.items():
            valid_mask &= np.isfinite(arr)

        index_array = np.full((height, width), NODATA_VALUE_FLOAT32, dtype=np.float32)

        if algo_code == "NDVI":
            nir = band_arrays["NIR"].astype(np.float32)
            red = band_arrays["Red"].astype(np.float32)
            denom = nir + red
            valid_calc = valid_mask & (np.abs(denom) > NUMERICAL_EPSILON)
            index_array[valid_calc] = (nir[valid_calc] - red[valid_calc]) / denom[valid_calc]
            valid_mask = valid_calc

        elif algo_code == "NDRE":
            nir = band_arrays["NIR"].astype(np.float32)
            re = band_arrays["RedEdge"].astype(np.float32)
            denom = nir + re
            valid_calc = valid_mask & (np.abs(denom) > NUMERICAL_EPSILON)
            index_array[valid_calc] = (nir[valid_calc] - re[valid_calc]) / denom[valid_calc]
            valid_mask = valid_calc

        elif algo_code == "GNDVI":
            nir = band_arrays["NIR"].astype(np.float32)
            green = band_arrays["Green"].astype(np.float32)
            denom = nir + green
            valid_calc = valid_mask & (np.abs(denom) > NUMERICAL_EPSILON)
            index_array[valid_calc] = (nir[valid_calc] - green[valid_calc]) / denom[valid_calc]
            valid_mask = valid_calc

        elif algo_code == "SAVI":
            L = float(params.get("L", 0.5))
            if L < 0.0 or L > 1.0:
                raise ValueError(f"SAVI soil factor L must be in range [0.0, 1.0], got {L}")
            nir = band_arrays["NIR"].astype(np.float32)
            red = band_arrays["Red"].astype(np.float32)
            denom = nir + red + L
            valid_calc = valid_mask & (np.abs(denom) > NUMERICAL_EPSILON)
            index_array[valid_calc] = ((nir[valid_calc] - red[valid_calc]) / denom[valid_calc]) * (1.0 + L)
            valid_mask = valid_calc

        elif algo_code == "VARI":
            green = band_arrays["Green"].astype(np.float32)
            red = band_arrays["Red"].astype(np.float32)
            blue = band_arrays["Blue"].astype(np.float32)
            denom = green + red - blue
            valid_calc = valid_mask & (np.abs(denom) > NUMERICAL_EPSILON)
            index_array[valid_calc] = (green[valid_calc] - red[valid_calc]) / denom[valid_calc]
            valid_mask = valid_calc

        elif algo_code == "GLI":
            green = band_arrays["Green"].astype(np.float32)
            red = band_arrays["Red"].astype(np.float32)
            blue = band_arrays["Blue"].astype(np.float32)
            denom = 2.0 * green + red + blue
            valid_calc = valid_mask & (np.abs(denom) > NUMERICAL_EPSILON)
            index_array[valid_calc] = (2.0 * green[valid_calc] - red[valid_calc] - blue[valid_calc]) / denom[valid_calc]
            valid_mask = valid_calc

        valid_count = int(np.count_nonzero(valid_mask))
        nodata_count = int(total_pixels - valid_count)
        valid_percentage = round((valid_count / total_pixels) * 100.0, 2) if total_pixels > 0 else 0.0

        if valid_count == 0:
            logger.warning("Algorithm %s produced 0 valid pixels across %d total pixels.", algo_code, total_pixels)
            calc_stats = {
                "min": None,
                "max": None,
                "mean": None,
                "std": None,
                "median": None,
                "p10": None,
                "p90": None,
                "valid_pixel_count": 0,
                "nodata_pixel_count": total_pixels,
                "total_pixel_count": total_pixels,
                "valid_percentage": 0.0,
            }
            return index_array, valid_mask, calc_stats

        valid_vals = index_array[valid_mask]
        calc_stats = {
            "min": round(float(np.min(valid_vals)), 4),
            "max": round(float(np.max(valid_vals)), 4),
            "mean": round(float(np.mean(valid_vals)), 4),
            "std": round(float(np.std(valid_vals)), 4),
            "median": round(float(np.median(valid_vals)), 4),
            "p10": round(float(np.percentile(valid_vals, 10)), 4),
            "p90": round(float(np.percentile(valid_vals, 90)), 4),
            "valid_pixel_count": valid_count,
            "nodata_pixel_count": nodata_count,
            "total_pixel_count": total_pixels,
            "valid_percentage": valid_percentage,
        }

        return index_array, valid_mask, calc_stats

    @classmethod
    def calculate_zonal_statistics(
        cls,
        index_array: np.ndarray,
        valid_mask: np.ndarray,
        algorithm_code: str,
        pixel_res_m: float = 0.05,
    ) -> List[Dict[str, Any]]:
        """Calculates 4 agronomic vigour/canopy density zones for the calculated index array.

        Returns list of zone dicts with area in hectares and percentage distribution.
        """
        algo_code = algorithm_code.upper()
        valid_pixels = index_array[valid_mask]
        total_valid = len(valid_pixels)

        pixel_area_m2 = pixel_res_m * pixel_res_m
        sqm_to_ha = 0.0001

        if total_valid == 0:
            return []

        # Define agronomic classification thresholds per algorithm
        if algo_code in ("NDVI", "GNDVI"):
            zones_def = [
                ("Water / Non-vegetated", -1.0, 0.10),
                ("Bare Soil / Sparse Vegetation", 0.10, 0.25),
                ("Moderate Canopy Vigour", 0.25, 0.50),
                ("Dense / High Vigour", 0.50, 1.0),
            ]
        elif algo_code == "NDRE":
            zones_def = [
                ("Senescent / Non-vegetated", -1.0, 0.15),
                ("Low Chlorophyll / Emergence", 0.15, 0.30),
                ("Moderate Chlorophyll", 0.30, 0.50),
                ("High Canopy Chlorophyll", 0.50, 1.0),
            ]
        elif algo_code == "SAVI":
            zones_def = [
                ("Non-vegetated Ground", -1.5, 0.10),
                ("Low Vegetative Emergence", 0.10, 0.30),
                ("Active Canopy Growth", 0.30, 0.60),
                ("Peak Crop Density", 0.60, 1.5),
            ]
        else:  # VARI, GLI
            zones_def = [
                ("Bare Ground / Dry Residue", -1.0, 0.05),
                ("Early Green Emergence", 0.05, 0.20),
                ("Moderate Green Canopy", 0.20, 0.45),
                ("Dense Green Leaf Coverage", 0.45, 1.0),
            ]

        results = []
        for zone_name, lower_b, upper_b in zones_def:
            if upper_b >= 1.0:
                in_zone = (valid_pixels >= lower_b) & (valid_pixels <= upper_b)
            else:
                in_zone = (valid_pixels >= lower_b) & (valid_pixels < upper_b)

            count = int(np.count_nonzero(in_zone))
            area_ha = round(count * pixel_area_m2 * sqm_to_ha, 4)
            pct = round((count / total_valid) * 100.0, 2) if total_valid > 0 else 0.0

            results.append({
                "zone_name": zone_name,
                "min_val": round(lower_b, 3),
                "max_val": round(upper_b, 3),
                "pixel_count": count,
                "area_hectares": area_ha,
                "area_percentage": pct,
            })

        return results

    @classmethod
    def write_geotiff(
        cls,
        output_path: str,
        index_array: np.ndarray,
        source_profile: Dict[str, Any],
        metadata_tags: Optional[Dict[str, str]] = None,
    ) -> str:
        """Writes single-band Cloud-Optimized GeoTIFF with Deflate compression and embedded metadata."""
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        profile = source_profile.copy()
        profile.update({
            "driver": "GTiff",
            "count": 1,
            "dtype": "float32",
            "nodata": NODATA_VALUE_FLOAT32,
            "tiled": True,
            "blockxsize": 256,
            "blockysize": 256,
            "compress": "deflate",
            "predictor": 3,  # Floating-point predictor for optimal compression
        })

        with rasterio.open(output_path, "w", **profile) as dst:
            dst.write(index_array.astype(np.float32), 1)
            dst.set_band_description(1, metadata_tags.get("ALGORITHM", "VEGETATION_INDEX") if metadata_tags else "INDEX")

            if metadata_tags:
                dst.update_tags(**metadata_tags)

        logger.info("Successfully wrote index GeoTIFF to: %s", output_path)
        return output_path

    @classmethod
    def validate_output_geotiff(
        cls,
        output_path: str,
        expected_algo: str,
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Re-opens generated GeoTIFF to independently verify CRS, dimensions,

        absence of stray NaNs, and numerical plausibility.
        """
        if not os.path.exists(output_path):
            return False, {}, f"Output file does not exist at path: {output_path}"

        try:
            with rasterio.open(output_path) as src:
                if src.count != 1:
                    return False, {}, f"Expected 1 band in output raster, found {src.count}"

                if str(src.dtypes[0]) != "float32":
                    return False, {}, f"Expected float32 data type, found {src.dtypes[0]}"

                if src.nodata != NODATA_VALUE_FLOAT32:
                    return False, {}, f"Expected NoData value {NODATA_VALUE_FLOAT32}, found {src.nodata}"

                data = src.read(1)
                valid_mask = (data != NODATA_VALUE_FLOAT32) & np.isfinite(data)

                # Check for stray NaNs that weren't masked
                stray_nans = np.count_nonzero(np.isnan(data))
                if stray_nans > 0:
                    return False, {}, f"Found {stray_nans} unmasked NaN values in output raster."

                valid_count = int(np.count_nonzero(valid_mask))
                total_count = data.size

                if valid_count == 0:
                    return False, {}, "Raster contains 0 valid pixels (all NoData)."

                valid_vals = data[valid_mask]
                v_min = float(np.min(valid_vals))
                v_max = float(np.max(valid_vals))
                v_mean = float(np.mean(valid_vals))
                v_std = float(np.std(valid_vals))

                summary = {
                    "width": src.width,
                    "height": src.height,
                    "crs": str(src.crs),
                    "min": round(v_min, 4),
                    "max": round(v_max, 4),
                    "mean": round(v_mean, 4),
                    "std": round(v_std, 4),
                    "valid_pixels": valid_count,
                    "nodata_pixels": total_count - valid_count,
                    "valid_percentage": round((valid_count / total_count) * 100.0, 2),
                    "file_size_bytes": os.path.getsize(output_path),
                }

                # Plausibility check for standard normalized indices
                if expected_algo.upper() in ("NDVI", "NDRE", "GNDVI"):
                    if v_min < -1.5 or v_max > 1.5:
                        logger.warning(
                            "Output %s values [%.2f, %.2f] exceed typical normalized range [-1.0, 1.0].",
                            expected_algo, v_min, v_max
                        )

                return True, summary, None

        except Exception as e:
            logger.error("Failed to validate output GeoTIFF %s: %s", output_path, str(e))
            return False, {}, f"Output validation failed: {str(e)}"
