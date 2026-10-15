"""Map Rendering & Geospatial Visualization Service.

Phase 8 Interactive GIS Maps Engine.
Generates Web Mercator XYZ slippy raster tiles from single-band vegetation indices,
elevation models (DSM/DTM), and multi-band RGB orthophotos with color ramp styling,
NoData alpha masking, coordinate reprojection, and point sampling.
"""

import io
import os
import math
import logging
from typing import Dict, Any, List, Optional, Tuple
from functools import lru_cache

import numpy as np
from PIL import Image
import rasterio
from rasterio.warp import transform_bounds, reproject, Resampling
from rasterio.transform import from_bounds
from rasterio.crs import CRS

from app.core.config import settings

logger = logging.getLogger(__name__)

# Web Mercator bounds constants
WEB_MERCATOR_MAX_EXTENT = 20037508.342789244
WEB_MERCATOR_CRS = "EPSG:3857"
WGS84_CRS = "EPSG:4326"
DEFAULT_TILE_SIZE = 256
INDEX_NODATA = -9999.0

# Pre-generate a 256x256 transparent PNG for lightning-fast out-of-bounds tile responses
_empty_img = Image.new("RGBA", (DEFAULT_TILE_SIZE, DEFAULT_TILE_SIZE), (0, 0, 0, 0))
_buf = io.BytesIO()
_empty_img.save(_buf, format="PNG", optimize=True)
TRANSPARENT_TILE_BYTES = _buf.getvalue()


class ColorRamps:
    """Standardized color ramps for remote sensing indices and elevation."""

    # RdYlGn for NDVI, NDRE, SAVI, VARI, GLI
    # [threshold, (R, G, B)]
    RD_YL_GN = [
        (-1.0, (165, 0, 38)),     # Deep Crimson (water/non-veg)
        (0.0, (215, 48, 39)),     # Red
        (0.2, (252, 141, 89)),    # Orange-Red (bare soil / very low)
        (0.35, (254, 224, 139)),  # Yellow (sparse / stressed)
        (0.5, (217, 239, 139)),   # Yellow-Green (moderate)
        (0.65, (145, 207, 96)),   # Light Green (good vigour)
        (0.8, (26, 152, 80)),     # Deep Green (high vigour)
        (1.0, (0, 104, 55)),      # Forest Green (dense canopy)
    ]

    # Viridis for GNDVI
    VIRIDIS = [
        (0.0, (68, 1, 84)),       # Purple
        (0.25, (59, 82, 139)),    # Blue
        (0.5, (33, 145, 140)),    # Teal
        (0.75, (94, 201, 98)),    # Light Green
        (1.0, (253, 231, 37)),    # Bright Yellow
    ]

    # Terrain elevation for DSM / DTM
    TERRAIN = [
        (0.0, (43, 131, 186)),    # Blue / lowest
        (0.25, (171, 221, 164)),  # Pale green
        (0.5, (255, 255, 191)),   # Pale yellow
        (0.75, (253, 174, 97)),   # Orange
        (1.0, (215, 25, 28)),     # Red / highest
    ]


class MapRenderingService:
    """Core raster tile and point inspection service."""

    @staticmethod
    def resolve_local_path(blob_uri: str) -> str:
        """Resolves storage URI (local:// or relative) to local filesystem path."""
        if not blob_uri:
            raise ValueError("Empty blob_uri provided")

        if blob_uri.startswith("local://"):
            parts = blob_uri.replace("local://", "").split("/", 1)
            container = parts[0]
            blob_path = parts[1] if len(parts) > 1 else ""
            base_dir = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                settings.LOCAL_STORAGE_PATH,
            )
            return os.path.abspath(os.path.join(base_dir, container, blob_path))

        if os.path.isabs(blob_uri):
            return blob_uri

        # Relative path fallback
        base_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
            settings.LOCAL_STORAGE_PATH,
        )
        return os.path.abspath(os.path.join(base_dir, blob_uri))

    @staticmethod
    def tile_to_web_mercator_bounds(z: int, x: int, y: int) -> Tuple[float, float, float, float]:
        """Calculates EPSG:3857 bounding box [min_x, min_y, max_x, max_y] for slippy tile (z, x, y)."""
        n = 2.0 ** z
        tile_span = (2.0 * WEB_MERCATOR_MAX_EXTENT) / n
        min_x = -WEB_MERCATOR_MAX_EXTENT + (x * tile_span)
        max_x = -WEB_MERCATOR_MAX_EXTENT + ((x + 1) * tile_span)
        max_y = WEB_MERCATOR_MAX_EXTENT - (y * tile_span)
        min_y = WEB_MERCATOR_MAX_EXTENT - ((y + 1) * tile_span)
        return min_x, min_y, max_x, max_y

    @classmethod
    def get_raster_metadata(cls, file_path: str) -> Dict[str, Any]:
        """Extracts CRS, WGS84 bounds, center, and value range from GeoTIFF."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Raster file not found: {file_path}")

        with rasterio.open(file_path) as src:
            src_crs = src.crs or CRS.from_epsg(4326)
            bounds = src.bounds

            # Transform bounds to EPSG:4326
            wgs84_bounds = transform_bounds(src_crs, WGS84_CRS, bounds.left, bounds.bottom, bounds.right, bounds.top)
            center_lon = (wgs84_bounds[0] + wgs84_bounds[2]) / 2.0
            center_lat = (wgs84_bounds[1] + wgs84_bounds[3]) / 2.0

            # Transform bounds to EPSG:3857 for fast tile intersection checking
            mercator_bounds = transform_bounds(src_crs, WEB_MERCATOR_CRS, bounds.left, bounds.bottom, bounds.right, bounds.top)

            return {
                "width": src.width,
                "height": src.height,
                "band_count": src.count,
                "crs_epsg": str(src.crs) if src.crs else "EPSG:4326",
                "wgs84_bounds": list(wgs84_bounds),  # [minLon, minLat, maxLon, maxLat]
                "center": [center_lon, center_lat],
                "mercator_bounds": list(mercator_bounds),
                "nodata": src.nodatavals[0] if src.nodatavals else None,
            }

    @classmethod
    def render_tile(
        cls,
        file_path: str,
        product_type: str,
        z: int,
        x: int,
        y: int,
        tile_size: int = DEFAULT_TILE_SIZE,
    ) -> bytes:
        """Renders a single 256x256 PNG map tile for slippy coordinates (z, x, y).

        Supports single-band vegetation indices, DSM/DTM elevation, and 3-band RGB orthophotos.
        Returns transparent PNG if tile does not intersect raster bounds.
        """
        if not os.path.exists(file_path):
            logger.warning("Raster tile requested for missing file: %s", file_path)
            return TRANSPARENT_TILE_BYTES

        # Calculate Web Mercator bounds for this tile
        tile_min_x, tile_min_y, tile_max_x, tile_max_y = cls.tile_to_web_mercator_bounds(z, x, y)

        with rasterio.open(file_path) as src:
            src_crs = src.crs or CRS.from_epsg(4326)

            # Check fast intersection in EPSG:3857
            raster_merc = transform_bounds(src_crs, WEB_MERCATOR_CRS, *src.bounds)
            if (
                tile_max_x < raster_merc[0]
                or tile_min_x > raster_merc[2]
                or tile_max_y < raster_merc[1]
                or tile_min_y > raster_merc[3]
            ):
                return TRANSPARENT_TILE_BYTES

            tile_transform = from_bounds(tile_min_x, tile_min_y, tile_max_x, tile_max_y, tile_size, tile_size)

            p_type = product_type.upper()

            # Orthophoto Multi-band RGB rendering
            if p_type == "ORTHOPHOTO" and src.count >= 3:
                rgba = np.zeros((tile_size, tile_size, 4), dtype=np.uint8)
                for band_idx, ch in enumerate([0, 1, 2], start=1):
                    ch_dst = np.zeros((tile_size, tile_size), dtype=np.float32)
                    reproject(
                        source=rasterio.band(src, band_idx),
                        destination=ch_dst,
                        src_transform=src.transform,
                        src_crs=src_crs,
                        dst_transform=tile_transform,
                        dst_crs=WEB_MERCATOR_CRS,
                        resampling=Resampling.bilinear,
                        src_nodata=src.nodatavals[band_idx - 1] if src.nodatavals else 0,
                        dst_nodata=0,
                    )
                    # Clip to 0-255 uint8
                    rgba[:, :, ch] = np.clip(ch_dst, 0, 255).astype(np.uint8)

                # Set alpha mask: where any channel > 0
                valid_mask = (rgba[:, :, 0] > 0) | (rgba[:, :, 1] > 0) | (rgba[:, :, 2] > 0)
                rgba[:, :, 3] = np.where(valid_mask, 255, 0).astype(np.uint8)

                img = Image.fromarray(rgba, mode="RGBA")
                buf = io.BytesIO()
                img.save(buf, format="PNG", optimize=True)
                return buf.getvalue()

            # Single-band Index or DSM/DTM rendering
            dst_arr = np.full((tile_size, tile_size), fill_value=INDEX_NODATA, dtype=np.float32)
            src_nodata = src.nodatavals[0] if src.nodatavals else INDEX_NODATA

            reproject(
                source=rasterio.band(src, 1),
                destination=dst_arr,
                src_transform=src.transform,
                src_crs=src_crs,
                dst_transform=tile_transform,
                dst_crs=WEB_MERCATOR_CRS,
                resampling=Resampling.bilinear,
                src_nodata=src_nodata,
                dst_nodata=INDEX_NODATA,
            )

            # Determine valid pixels
            valid_mask = (dst_arr != INDEX_NODATA) & np.isfinite(dst_arr)
            if not np.any(valid_mask):
                return TRANSPARENT_TILE_BYTES

            rgba = cls._colorize_raster(dst_arr, valid_mask, p_type)
            img = Image.fromarray(rgba, mode="RGBA")
            buf = io.BytesIO()
            img.save(buf, format="PNG", optimize=True)
            return buf.getvalue()

    @classmethod
    def _colorize_raster(cls, data: np.ndarray, valid_mask: np.ndarray, product_type: str) -> np.ndarray:
        """Applies colormap gradient and transparency mask to single-band float array."""
        h, w = data.shape
        rgba = np.zeros((h, w, 4), dtype=np.uint8)

        if not np.any(valid_mask):
            return rgba

        # Select color ramp and value normalization
        if product_type in ("DSM", "DTM"):
            ramp = ColorRamps.TERRAIN
            valid_vals = data[valid_mask]
            min_v = float(np.min(valid_vals))
            max_v = float(np.max(valid_vals))
            if abs(max_v - min_v) < 1e-4:
                norm_vals = np.zeros_like(data)
            else:
                norm_vals = np.clip((data - min_v) / (max_v - min_v), 0.0, 1.0)
        elif product_type == "INDEX_GNDVI":
            ramp = ColorRamps.VIRIDIS
            norm_vals = np.clip(data, 0.0, 1.0)
        else:
            # Default RdYlGn for NDVI, NDRE, SAVI, VARI, GLI
            ramp = ColorRamps.RD_YL_GN
            norm_vals = data  # Raw index value mapped against ramp thresholds

        # Interpolate RGB across ramp stops for valid pixels
        r_chan = np.zeros((h, w), dtype=np.float32)
        g_chan = np.zeros((h, w), dtype=np.float32)
        b_chan = np.zeros((h, w), dtype=np.float32)

        # Vectorized piecewise linear interpolation across ramp intervals
        for i in range(len(ramp) - 1):
            t_low, c_low = ramp[i]
            t_high, c_high = ramp[i + 1]

            if i == 0:
                mask_seg = valid_mask & (norm_vals <= t_low)
                r_chan[mask_seg] = c_low[0]
                g_chan[mask_seg] = c_low[1]
                b_chan[mask_seg] = c_low[2]

            mask_interp = valid_mask & (norm_vals > t_low) & (norm_vals <= t_high)
            span = t_high - t_low
            if span > 0:
                fraction = (norm_vals[mask_interp] - t_low) / span
                r_chan[mask_interp] = c_low[0] + fraction * (c_high[0] - c_low[0])
                g_chan[mask_interp] = c_low[1] + fraction * (c_high[1] - c_low[1])
                b_chan[mask_interp] = c_low[2] + fraction * (c_high[2] - c_low[2])

        # Values above highest threshold
        last_t, last_c = ramp[-1]
        mask_above = valid_mask & (norm_vals > last_t)
        r_chan[mask_above] = last_c[0]
        g_chan[mask_above] = last_c[1]
        b_chan[mask_above] = last_c[2]

        rgba[:, :, 0] = np.clip(r_chan, 0, 255).astype(np.uint8)
        rgba[:, :, 1] = np.clip(g_chan, 0, 255).astype(np.uint8)
        rgba[:, :, 2] = np.clip(b_chan, 0, 255).astype(np.uint8)
        rgba[:, :, 3] = np.where(valid_mask, 255, 0).astype(np.uint8)

        return rgba

    @classmethod
    def sample_raster_point(cls, file_path: str, lat: float, lon: float) -> Optional[float]:
        """Samples the exact raster value at a geographic (WGS84) coordinate."""
        if not os.path.exists(file_path):
            return None

        try:
            with rasterio.open(file_path) as src:
                src_crs = src.crs or CRS.from_epsg(4326)

                # Reproject lon/lat from EPSG:4326 to raster CRS
                from rasterio.warp import transform
                xs, ys = transform(WGS84_CRS, src_crs, [lon], [lat])
                target_x, target_y = xs[0], ys[0]

                # Check if within raster bounds
                b = src.bounds
                if not (b.left <= target_x <= b.right and b.bottom <= target_y <= b.top):
                    return None

                # Convert to pixel coordinates
                row, col = src.index(target_x, target_y)
                if not (0 <= row < src.height and 0 <= col < src.width):
                    return None

                # Read 1x1 window
                from rasterio.windows import Window
                val = src.read(1, window=Window(col, row, 1, 1))[0, 0]

                nodata = src.nodatavals[0] if src.nodatavals else INDEX_NODATA
                if val == nodata or not np.isfinite(val):
                    return None

                return round(float(val), 4)

        except Exception as e:
            logger.warning("Failed to probe raster point (%f, %f): %s", lat, lon, str(e))
            return None
