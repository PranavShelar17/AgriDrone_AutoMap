# AgriDrone AutoMap — File Validation Rules Specification
## Document Reference: `docs/phase-5/file-validation-rules.md`
**Phase**: Phase 5 — Admin Dashboard, Farm/Survey Management & Drone Image Ingestion  
**Status**: APPROVED VALIDATION RULES  
**Version**: 1.0.0  

---

## 1. Zero-Trust File Validation Principles

Browser-supplied filenames, Content-Type MIME headers, and client assertions are strictly treated as untrusted user input. The backend enforces server-side validation against raw byte streams.

### Validation Pipeline Order:
1. **Empty Stream Check**: Files with length $0$ bytes are immediately rejected.
2. **File Size Enforcement**: Evaluated against `settings.MAX_UPLOAD_SIZE_BYTES` (default: 500 MB).
3. **Extension Allowlist**: Only `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.dng`, `.zip` are allowed.
4. **Magic Byte Signature Inspection**: Actual binary headers are examined to defeat file-extension spoofing (e.g., `.exe` renamed to `.jpg`).
5. **Format & Metadata Decoding**: Decoded via Pillow to ensure the image stream is intact and parse EXIF / GeoTIFF tags.
6. **Workflow Alignment**: Verifies that the uploaded file matches the selected mode (e.g. rejecting a standard JPEG when GeoTIFF mode is selected).

---

## 2. Magic Byte Signature Directory

| Format | Magic Bytes (Hex) | Offset | Mime Type Assigned |
| :--- | :--- | :--- | :--- |
| **JPEG** | `FF D8 FF` | 0 | `image/jpeg` |
| **TIFF (Little-Endian)** | `49 49 2A 00` (`II*\x00`) | 0 | `image/tiff` |
| **TIFF (Big-Endian)** | `4D 4D 00 2A` (`MM\x00*`) | 0 | `image/tiff` |
| **ZIP Archive** | `50 4B 03 04` (`PK\x03\x04`) | 0 | `application/zip` |

Any file whose leading bytes do not match these signatures is rejected with:
`"File signature mismatch. The file content does not match any valid JPEG, TIFF, or ZIP container."`

---

## 3. Metadata Extraction Specifications

### 3.1. Raw Photographs (JPEG / TIFF)
- **Dimensions**: `width`, `height` in pixels.
- **Color Mode**: RGB, RGBA, Grayscale, or Multispectral bands count.
- **Camera Tags**: `camera_make` (EXIF Tag 271), `camera_model` (EXIF Tag 272).
- **Capture Timestamp**: `capture_time` (EXIF Tag 36867 `DateTimeOriginal` or 306 `DateTime`).
- **GPS Coordinates**:
  - `GPSLatitude` and `GPSLongitude` DMS rational tuples converted to signed decimal degrees:
    $$\text{Decimal} = (\text{Deg} + \frac{\text{Min}}{60} + \frac{\text{Sec}}{3600}) \times (\text{Ref} \in \{'S', 'W'\} ? -1 : 1)$$
  - `GPSAltitude`: Elevation Above Sea Level in meters.

### 3.2. Pre-Stitched GeoTIFF Rasters
- **GeoKeyDirectoryTag (34735)**: Parsed to extract `ProjectedCSTypeGeoKey` (3072) or `GeographicTypeGeoKey` (2048), mapping directly to EPSG codes (e.g. `EPSG:32632`, `EPSG:4326`).
- **ModelPixelScaleTag (33550)**: Used to compute ground resolution (cm/pixel).
- **ModelTiepointTag (33922)**: Raster-to-world tiepoint coordinates for spatial registration.
- **Workflow Tagging**: Tagged with `is_geotiff = True` and routed to `DIRECT_ALGORITHM_GIS`.
