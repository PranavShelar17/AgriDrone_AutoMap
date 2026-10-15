# AgriDrone AutoMap — Drone Image Ingestion Architecture
## Document Reference: `docs/phase-5/drone-image-ingestion.md`
**Phase**: Phase 5 — Admin Dashboard, Farm/Survey Management & Drone Image Ingestion  
**Status**: APPROVED INGESTION SPECIFICATION  
**Version**: 1.0.0  

---

## 1. Dual-Workflow Architecture

AgriDrone AutoMap Phase 5 implements two distinct, mutually exclusive ingestion workflows tailored to different aerial data sources:

```mermaid
flowchart TD
    File[Uploaded File Stream] --> Val[FileValidationService]
    Val -->|Inspect Magic Bytes, Headers, EXIF & GeoKeys| Decision{Dataset Classifier}
    
    Decision -->|Raw JPEG / Standard TIFF / ZIP| RouteA[Workflow 1: Raw Drone Photos]
    Decision -->|TIFF with GeoKey / ModelTiepoint| RouteB[Workflow 2: Pre-Stitched GeoTIFF]
    Decision -->|Invalid Signature / Corrupted| Reject[Rejected with Explicit Errors]
    
    RouteA --> StorageA[Store in raw-surveys Container]
    StorageA --> DbA[Record in survey_files: RAW_IMAGE]
    DbA --> NextA[Eligible for WebODM Photogrammetry (Phase 6)]
    
    RouteB --> StorageB[Store in raw-surveys Container]
    StorageB --> DbB[Record in survey_files: GEOTIFF]
    DbB --> NextB[Eligible for Direct Algorithm Multi-Map (Phase 7)]
```

### Workflow 1 — Raw Drone Photographs
- **Target Data**: Individual aerial frames captured by multispectral or RGB drone sensors (e.g., DJI Mavic 3 Enterprise, Phantom 4 Multispectral, MicaSense RedEdge-P).
- **Supported Formats**: `.jpg`, `.jpeg`, `.tif`, `.tiff`, `.zip` (batch archives).
- **Validation**:
  - Verifies magic byte file signatures (`\xff\xd8\xff` for JPEG; `II*\x00` or `MM\x00*` for TIFF).
  - Extracts EXIF metadata using Pillow: `DateTimeOriginal`, `Make`, `Model`.
  - Extracts EXIF `GPSInfo` (Latitude, Longitude, Altitude) and converts degrees-minutes-seconds tuples to signed decimal degrees.
- **Routing**: Tagged as `RAW_IMAGE` and routed to **WebODM Photogrammetry (Page 2 / Phase 6)** for 3D point cloud and orthomosaic reconstruction.

### Workflow 2 — Pre-Stitched Geospatial Rasters
- **Target Data**: Finished orthomosaic rasters pre-stitched in external photogrammetry software (e.g. Pix4D, Agisoft Metashape, or existing WebODM runs).
- **Supported Formats**: `.tif`, `.tiff` (GeoTIFF compliant).
- **Validation**:
  - Inspects TIFF Tag Directory for GeoTIFF-specific keys (`GeoKeyDirectoryTag` 34735, `ModelPixelScaleTag` 33550, `ModelTiepointTag` 33922).
  - Parses Projected or Geographic Coordinate Reference System EPSG codes (e.g. `EPSG:32632`, `EPSG:4326`).
  - Estimates ground spatial resolution in centimeters per pixel.
- **Routing**: Tagged as `GEOTIFF` and routed directly to **Algorithm Multi-Map Generation (Page 3 / Phase 7)**, completely bypassing WebODM photogrammetry.

---

## 2. Ingestion Statuses & Lifecycle

Every uploaded dataset receives a tracked state in the `survey_files` table:

| Status | Definition |
| :--- | :--- |
| **`PENDING`** | Upload request received, byte stream actively reading. |
| **`VALIDATING`** | File content undergoing magic-byte check, EXIF decoding, and GeoTIFF tag parsing. |
| **`VALIDATED`** | File passed all validation rules, hashes calculated, stored in object storage, and metadata persisted in PostgreSQL. |
| **`REJECTED`** | File rejected due to signature mismatch, extension violation, corruption, or size limit. Failure reasons preserved in database. |
| **`FAILED`** | Storage write or transactional database error during ingestion. |

---

## 3. Duplicate Handling & Retries

To prevent duplicate uploads of the same aerial photo during network retries:
1. The backend inspects `(survey_id, original_filename)` uniqueness.
2. If a re-upload occurs for an existing filename under the same survey, the storage object is updated with the new bytes, and the database record is updated in place rather than creating duplicate entries.
3. MD5 and SHA-256 checksums are calculated during streaming and persisted for integrity verification.
