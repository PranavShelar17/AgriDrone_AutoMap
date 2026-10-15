import io
import pytest
from PIL import Image
from app.services.validation import FileValidationService, MAGIC_JPEG, MAGIC_TIFF_LE


def create_test_jpeg_bytes() -> bytes:
    """Create a minimal valid in-memory JPEG."""
    img = Image.new("RGB", (100, 80), color=(73, 109, 137))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def create_test_tiff_bytes(is_geotiff: bool = False) -> bytes:
    """Create a minimal valid in-memory TIFF, optionally with GeoTIFF tags."""
    img = Image.new("RGB", (64, 64), color=(100, 200, 100))
    buf = io.BytesIO()
    if is_geotiff:
        # Include GeoKeyDirectory tag (34735) and ModelPixelScale tag (33550)
        # GeoKeyDirectory: HeaderVersion=1, Revision=1, MinorRev=0, NumberOfKeys=1,
        # KeyID=3072 (ProjectedCS), KeyLoc=0, KeyCount=1, KeyVal=32632 (UTM 32N)
        geokey_data = (1, 1, 0, 1, 3072, 0, 1, 32632)
        pixel_scale = (0.024, 0.024, 0.0)
        from PIL.TiffImagePlugin import ImageFileDirectory_v2
        ifd = ImageFileDirectory_v2()
        ifd[34735] = geokey_data
        ifd[33550] = pixel_scale
        img.save(buf, format="TIFF", tiffinfo=ifd)
    else:
        img.save(buf, format="TIFF")
    return buf.getvalue()


def test_validate_valid_jpeg():
    service = FileValidationService(max_size_bytes=10 * 1024 * 1024)
    data = create_test_jpeg_bytes()
    res = service.validate_file(data, "DJI_0042.JPG", declared_mime="image/jpeg")

    assert res["is_valid"] is True
    assert res["file_type"] == "RAW_IMAGE"
    assert res["ingestion_status"] == "VALIDATED"
    assert res["workflow_route"] == "WEBODM_PHOTOGRAMMETRY"
    assert res["metadata"]["width"] == 100
    assert res["metadata"]["height"] == 80
    assert len(res["validation_errors"]) == 0


def test_validate_standard_tiff():
    service = FileValidationService()
    data = create_test_tiff_bytes(is_geotiff=False)
    res = service.validate_file(data, "capture_01.tif", declared_mime="image/tiff")

    assert res["is_valid"] is True
    assert res["file_type"] == "RAW_IMAGE"
    assert res["workflow_route"] == "WEBODM_PHOTOGRAMMETRY"
    assert res["metadata"]["is_geotiff"] is False


def test_validate_geotiff_raster():
    service = FileValidationService()
    data = create_test_tiff_bytes(is_geotiff=True)
    res = service.validate_file(data, "ortho_mosaic.tif", declared_mime="image/tiff", expected_workflow="geotiff")

    assert res["is_valid"] is True
    assert res["file_type"] == "GEOTIFF"
    assert res["workflow_route"] == "DIRECT_ALGORITHM_GIS"
    assert res["metadata"]["is_geotiff"] is True
    assert "EPSG:32632" in res["metadata"].get("crs_epsg", "")


def test_reject_empty_file():
    service = FileValidationService()
    res = service.validate_file(b"", "empty.jpg")

    assert res["is_valid"] is False
    assert res["ingestion_status"] == "REJECTED"
    assert "File is empty" in res["validation_errors"][0]


def test_reject_disguised_file():
    service = FileValidationService()
    fake_exe = b"MZ\x90\x00\x03\x00\x00\x00not a real jpeg file content"
    res = service.validate_file(fake_exe, "malicious.jpg")

    assert res["is_valid"] is False
    assert res["ingestion_status"] == "REJECTED"
    assert any("signature mismatch" in err for err in res["validation_errors"])


def test_reject_unsupported_extension():
    service = FileValidationService()
    data = create_test_jpeg_bytes()
    res = service.validate_file(data, "flight_video.mp4")

    assert res["is_valid"] is False
    assert res["ingestion_status"] == "REJECTED"
    assert any("unsupported" in err for err in res["validation_errors"])


def test_reject_file_exceeding_size_limit():
    service = FileValidationService(max_size_bytes=50)
    data = create_test_jpeg_bytes()  # > 50 bytes
    res = service.validate_file(data, "large.jpg")

    assert res["is_valid"] is False
    assert any("exceeds maximum allowed limit" in err for err in res["validation_errors"])
