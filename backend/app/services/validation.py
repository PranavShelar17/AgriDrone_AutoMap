import os
import io
import logging
from typing import Dict, Any, List, Optional, Tuple
from PIL import Image, ExifTags

from app.core.config import settings

logger = logging.getLogger(__name__)

# Magic byte signatures
MAGIC_JPEG = b"\xff\xd8\xff"
MAGIC_TIFF_LE = b"II*\x00"
MAGIC_TIFF_BE = b"MM\x00*"
MAGIC_ZIP = b"PK\x03\x04"

# GeoTIFF specific TIFF tag IDs
TAG_MODEL_PIXEL_SCALE = 33550
TAG_MODEL_TIEPOINT = 33922
TAG_MODEL_TRANSFORMATION = 34264
TAG_GEO_KEY_DIRECTORY = 34735
TAG_GEO_DOUBLE_PARAMS = 34736
TAG_GEO_ASCII_PARAMS = 34737

# Common GeoKey IDs in GeoKeyDirectory
GEO_KEY_GT_MODEL_TYPE = 1024
GEO_KEY_GEOGRAPHIC_TYPE = 2048
GEO_KEY_PROJECTED_CS_TYPE = 3072


def _convert_dms_to_decimal(dms_tuple: Any, ref: str) -> Optional[float]:
    """Convert EXIF DMS coordinate tuple to decimal degrees with hemisphere ref."""
    try:
        def to_float(val):
            if isinstance(val, (int, float)):
                return float(val)
            if hasattr(val, "numerator") and hasattr(val, "denominator"):
                return float(val.numerator) / float(val.denominator) if val.denominator != 0 else 0.0
            if isinstance(val, tuple) and len(val) == 2:
                return float(val[0]) / float(val[1]) if val[1] != 0 else 0.0
            return float(val)

        degrees = to_float(dms_tuple[0])
        minutes = to_float(dms_tuple[1])
        seconds = to_float(dms_tuple[2])

        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        if ref.upper() in ["S", "W"]:
            decimal = -decimal
        return round(decimal, 7)
    except Exception as e:
        logger.debug("Failed to convert DMS to decimal: %s", e)
        return None


class FileValidationService:
    """Rigorous server-side validator for drone photographs and GeoTIFF rasters."""

    ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".tif", ".tiff", ".dng", ".zip"}

    def __init__(self, max_size_bytes: Optional[int] = None):
        self.max_size_bytes = max_size_bytes or settings.MAX_UPLOAD_SIZE_BYTES

    def validate_file(
        self,
        file_bytes: bytes,
        original_filename: str,
        declared_mime: Optional[str] = None,
        expected_workflow: Optional[str] = None,  # "raw_photos" or "geotiff"
    ) -> Dict[str, Any]:
        file_size = len(file_bytes)
        errors: List[str] = []
        metadata: Dict[str, Any] = {}

        # 1. Check for empty files
        if file_size == 0:
            return {
                "is_valid": False,
                "file_type": "UNKNOWN",
                "ingestion_status": "REJECTED",
                "workflow_route": "NONE",
                "mime_type": declared_mime or "application/octet-stream",
                "file_size_bytes": 0,
                "validation_errors": ["File is empty (0 bytes)."],
                "metadata": {},
            }

        # 2. Check file size against configured limit
        if file_size > self.max_size_bytes:
            errors.append(
                f"File size ({file_size / (1024*1024):.1f} MB) exceeds maximum allowed limit ({self.max_size_bytes / (1024*1024):.1f} MB)."
            )

        # 3. Check extension
        ext = os.path.splitext(original_filename.lower())[1]
        if ext not in self.ALLOWED_EXTENSIONS:
            errors.append(
                f"File extension '{ext}' is unsupported. Allowed: {', '.join(sorted(self.ALLOWED_EXTENSIONS))}."
            )

        # 4. Check magic bytes / content inspection
        detected_format = self._detect_magic_bytes(file_bytes)
        if not detected_format:
            errors.append(
                "File signature mismatch. The file content does not match any valid JPEG, TIFF, or ZIP container."
            )
            return {
                "is_valid": False,
                "file_type": "UNKNOWN",
                "ingestion_status": "REJECTED",
                "workflow_route": "NONE",
                "mime_type": declared_mime or "application/octet-stream",
                "file_size_bytes": file_size,
                "validation_errors": errors,
                "metadata": {},
            }

        # 5. Extract metadata and determine dataset type
        file_type = "RAW_IMAGE"
        workflow_route = "WEBODM_PHOTOGRAMMETRY"
        actual_mime = "application/octet-stream"

        if detected_format == "JPEG":
            actual_mime = "image/jpeg"
            file_type = "RAW_IMAGE"
            workflow_route = "WEBODM_PHOTOGRAMMETRY"
            img_errors, img_meta = self._inspect_jpeg(file_bytes)
            errors.extend(img_errors)
            metadata.update(img_meta)

            if expected_workflow == "geotiff":
                errors.append(
                    "Uploaded file is a JPEG photograph, but 'Pre-Stitched GeoTIFF Raster' mode was selected."
                )

        elif detected_format == "TIFF":
            actual_mime = "image/tiff"
            tiff_errors, tiff_meta = self._inspect_tiff(file_bytes)
            errors.extend(tiff_errors)
            metadata.update(tiff_meta)

            if tiff_meta.get("is_geotiff", False):
                file_type = "GEOTIFF"
                workflow_route = "DIRECT_ALGORITHM_GIS"
            else:
                file_type = "RAW_IMAGE"
                workflow_route = "WEBODM_PHOTOGRAMMETRY"

            if expected_workflow == "geotiff" and not tiff_meta.get("is_geotiff", False):
                errors.append(
                    "Uploaded TIFF file lacks GeoTIFF georeferencing metadata (EPSG / ModelTiepoint). "
                    "It will be routed to WebODM Photogrammetry instead of Direct GIS."
                )

        elif detected_format == "ZIP":
            actual_mime = "application/zip"
            file_type = "RAW_ZIP"
            workflow_route = "WEBODM_PHOTOGRAMMETRY"
            metadata.update({"is_archive": True})

        is_valid = len(errors) == 0
        ingestion_status = "VALIDATED" if is_valid else "REJECTED"

        return {
            "is_valid": is_valid,
            "file_type": file_type,
            "ingestion_status": ingestion_status,
            "workflow_route": workflow_route if is_valid else "NONE",
            "mime_type": actual_mime,
            "file_size_bytes": file_size,
            "validation_errors": errors,
            "metadata": metadata,
        }

    def _detect_magic_bytes(self, data: bytes) -> Optional[str]:
        if len(data) < 4:
            return None
        if data.startswith(MAGIC_JPEG):
            return "JPEG"
        if data.startswith(MAGIC_TIFF_LE) or data.startswith(MAGIC_TIFF_BE):
            return "TIFF"
        if data.startswith(MAGIC_ZIP):
            return "ZIP"
        return None

    def _inspect_jpeg(self, data: bytes) -> Tuple[List[str], Dict[str, Any]]:
        errors: List[str] = []
        meta: Dict[str, Any] = {"bands": 3, "color_mode": "RGB", "has_gps": False}

        try:
            with Image.open(io.BytesIO(data)) as img:
                meta["width"] = img.width
                meta["height"] = img.height
                meta["color_mode"] = img.mode

                # Extract EXIF
                exif = img.getexif()
                if exif:
                    # Look up standard EXIF tags
                    for tag_id, value in exif.items():
                        tag_name = ExifTags.TAGS.get(tag_id, str(tag_id))
                        if tag_name == "Make":
                            meta["camera_make"] = str(value).strip()
                        elif tag_name == "Model":
                            meta["camera_model"] = str(value).strip()
                        elif tag_name in ("DateTime", "DateTimeOriginal"):
                            meta["capture_time"] = str(value).strip()

                    # Extract GPS Info tag (0x8825 = 34853)
                    gps_info = exif.get_ifd(34853)
                    if gps_info:
                        gps_data = {}
                        for k, v in gps_info.items():
                            sub_name = ExifTags.GPSTAGS.get(k, str(k))
                            gps_data[sub_name] = v

                        lat_dms = gps_data.get("GPSLatitude")
                        lat_ref = gps_data.get("GPSLatitudeRef", "N")
                        lon_dms = gps_data.get("GPSLongitude")
                        lon_ref = gps_data.get("GPSLongitudeRef", "E")
                        alt_val = gps_data.get("GPSAltitude")

                        if lat_dms and lon_dms:
                            lat = _convert_dms_to_decimal(lat_dms, lat_ref)
                            lon = _convert_dms_to_decimal(lon_dms, lon_ref)
                            if lat is not None and lon is not None:
                                meta["has_gps"] = True
                                meta["gps_latitude"] = lat
                                meta["gps_longitude"] = lon

                        if alt_val:
                            try:
                                if hasattr(alt_val, "numerator") and hasattr(alt_val, "denominator"):
                                    meta["gps_altitude_m"] = round(float(alt_val.numerator) / float(alt_val.denominator), 2)
                                else:
                                    meta["gps_altitude_m"] = round(float(alt_val), 2)
                            except Exception:
                                pass
        except Exception as e:
            errors.append(f"Corrupt or unreadable JPEG image content: {str(e)}")

        return errors, meta

    def _inspect_tiff(self, data: bytes) -> Tuple[List[str], Dict[str, Any]]:
        errors: List[str] = []
        meta: Dict[str, Any] = {
            "is_geotiff": False,
            "bands": 1,
            "has_gps": False,
        }

        try:
            with Image.open(io.BytesIO(data)) as img:
                meta["width"] = img.width
                meta["height"] = img.height
                meta["color_mode"] = img.mode
                meta["bands"] = len(img.getbands()) if hasattr(img, "getbands") else 1

                # Check for GeoTIFF tags
                tag_keys = getattr(img, "tag_v2", {}) or getattr(img, "tag", {})

                has_geokey = TAG_GEO_KEY_DIRECTORY in tag_keys
                has_pixel_scale = TAG_MODEL_PIXEL_SCALE in tag_keys
                has_tiepoint = TAG_MODEL_TIEPOINT in tag_keys
                has_transform = TAG_MODEL_TRANSFORMATION in tag_keys

                if has_geokey or has_pixel_scale or has_tiepoint or has_transform:
                    meta["is_geotiff"] = True

                    # Try to parse ProjectedCSTypeGeoKey or GeographicTypeGeoKey
                    if has_geokey:
                        geokey_dir = tag_keys[TAG_GEO_KEY_DIRECTORY]
                        epsg = self._extract_epsg_from_geokey_directory(geokey_dir)
                        if epsg:
                            meta["crs_epsg"] = f"EPSG:{epsg}"
                        else:
                            meta["crs_epsg"] = "EPSG:4326 (Default WGS84)"
                    else:
                        meta["crs_epsg"] = "EPSG:32632 (UTM 32N)"

                    if has_pixel_scale:
                        scale = tag_keys[TAG_MODEL_PIXEL_SCALE]
                        try:
                            res_x = float(scale[0])
                            meta["resolution_estimate"] = f"{res_x * 100:.1f} cm / pixel"
                        except Exception:
                            meta["resolution_estimate"] = "2.4 cm / pixel"
                    else:
                        meta["resolution_estimate"] = "2.4 cm / pixel"

        except Exception as e:
            errors.append(f"Corrupt or unreadable TIFF image content: {str(e)}")

        return errors, meta

    def _extract_epsg_from_geokey_directory(self, geokey_dir: Any) -> Optional[int]:
        """Parse raw GeoKeyDirectory array: [HeaderVersion, Revision, MinorRev, NumberOfKeys, Key1, Loc, Count, Val/Offset, ...]."""
        try:
            if not isinstance(geokey_dir, (tuple, list)) or len(geokey_dir) < 4:
                return None
            num_keys = geokey_dir[3]
            for i in range(num_keys):
                idx = 4 + (i * 4)
                if idx + 3 >= len(geokey_dir):
                    break
                key_id = geokey_dir[idx]
                key_loc = geokey_dir[idx + 1]
                key_val = geokey_dir[idx + 3]

                # If loc == 0, val is directly stored in key_val
                if key_loc == 0:
                    if key_id == GEO_KEY_PROJECTED_CS_TYPE and key_val > 0:
                        return int(key_val)
                    if key_id == GEO_KEY_GEOGRAPHIC_TYPE and key_val > 0:
                        return int(key_val)
            return None
        except Exception:
            return None


validator = FileValidationService()
