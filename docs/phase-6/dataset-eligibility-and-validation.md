# AgriDrone AutoMap — Dataset Eligibility & Validation Specification
## Document Reference: `docs/phase-6/dataset-eligibility-and-validation.md`
**Phase**: Phase 6 — WebODM / OpenDroneMap Integration & Drone Photogrammetry Processing  
**Status**: APPROVED VALIDATION SPECIFICATION  
**Version**: 1.0.0  

---

## 1. Eligibility Classification Matrix

Not all uploaded files can enter photogrammetry processing. The system classifies datasets strictly based on ingestion verification results:

| Uploaded File Type | Ingestion Status | Workflow Route | Eligible for WebODM? | System Behavior |
| :--- | :--- | :--- | :--- | :--- |
| **Raw Photo Batch (JPEG / TIFF)** | `VALIDATED` | `WEBODM_PHOTOGRAMMETRY` | ✅ **ELIGIBLE** | Available for selection in Page 2. Full Structure-from-Motion workflow. |
| **ZIP Archive of Raw Photos** | `VALIDATED` | `WEBODM_PHOTOGRAMMETRY` | ✅ **ELIGIBLE** | Automatically unpacked into constituent photos on worker. |
| **Pre-Stitched GeoTIFF Raster** | `VALIDATED` | `DIRECT_ALGORITHM_GIS` | ❌ **INELIGIBLE** | Bypasses photogrammetry. Routes directly to Phase 7 GIS algorithms. |
| **Corrupt / Non-Image File** | `REJECTED` | `NONE` | ❌ **INELIGIBLE** | Submission blocked with rejection diagnostic explanation. |
| **File Missing from Storage** | Any | Any | ❌ **INELIGIBLE** | Submission blocked with storage accessibility error. |

---

## 2. Ineligibility Rationales Explained

The system never leaves users guessing why a dataset cannot be submitted:

1. **Pre-Stitched GeoTIFF Rasters**:
   - *Rationale*: *"Pre-stitched GeoTIFF rasters bypass WebODM photogrammetry and route directly to Phase 7 GIS algorithms."*
   - *Why*: GeoTIFFs are already orthorectified 2D rasters. Submitting an orthomosaic as an input to a 3D bundle-adjustment photogrammetry pipeline is mathematically invalid and will cause OpenSfM feature matching to fail.
2. **Ingestion Rejected Datasets**:
   - *Rationale*: *"Rejected: [List of specific validation errors]"*
   - *Why*: Files that fail magic byte verification, have corrupted headers, or lack necessary camera tags cannot be reconstructed reliably.
3. **Active Processing Conflict**:
   - *Rationale*: *"Survey currently has an active photogrammetry reconstruction job running."*
   - *Why*: Launching multiple photogrammetry tasks concurrently against the same survey results in duplicate resource consumption and database race conditions.

---

## 3. Server-Side Pre-Flight Verification

Even if an API client crafts a direct `POST /api/v1/photogrammetry/tasks` request, the backend re-validates all eligibility constraints before touching the database or worker queue:

```python
# Validation guard in photogrammetry.py
if source_file.ingestion_status != "VALIDATED":
    raise HTTPException(status_code=400, detail="Dataset ingestion status is not VALIDATED.")

if source_file.file_type == "GEOTIFF":
    raise HTTPException(status_code=400, detail="Pre-stitched GeoTIFF rasters cannot be submitted for WebODM photogrammetry.")

if not storage.file_exists(container, blob_path):
    raise HTTPException(status_code=400, detail="Dataset file is not accessible on the storage backend.")
```
