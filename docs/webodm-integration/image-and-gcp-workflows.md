# Image Ingestion and Ground Control Points (GCP) Workflows

This document details the image classification, validation gates, upload mechanisms, and Ground Control Point (GCP) georeferencing standards implemented in AgriDrone AutoMap's WebODM integration.

---

## 1. Aerial Imagery Ingestion & Routing Strategy

A primary rule of the AgriDrone AutoMap architecture is **strict workflow separation based on file type and geospatial readiness**:

```
Uploaded Dataset
   │
   ├── Raw Drone Photographs (JPEG/TIFF or ZIP archive)
   │     └── Route: Photogrammetry Reconstruction Pipeline (WebODM / SfM)
   │           └── Outputs: Orthophoto, DSM, DTM, 3D Mesh
   │
   ├── Pre-stitched GeoTIFF Raster (Single georeferenced raster)
   │     └── Route: Direct GIS Analytics Pipeline (Phase 7 Algorithms)
   │           └── Outputs: NDVI, NDRE, GNDVI, SAVI, Zonal Stats
   │
   └── GCP Coordinate File (.txt)
         └── Route: Photogrammetry Georeferencing Attachment
               └── Outputs: Precision Georeferencing (< 3 cm accuracy)
```

### 1.1 Dataset Classification & Validation Rules
Before any dataset can be ingested into a photogrammetry task, it undergoes strict validation via `/api/v1/photogrammetry/eligible-datasets`:
1. **File Type Filter**:
   - `RAW_IMAGE` (JPEG/DNG): Validated single drone frame containing EXIF GPS tags.
   - `RAW_ZIP`: Archive containing >= 5 raw drone photographs.
   - `GEOTIFF`: **Explicitly Rejected from Photogrammetry**. Pre-stitched orthomosaics cannot undergo SfM reconstruction; they bypass directly to Phase 7 GIS calculations.
2. **Ingestion Status Gate**:
   - Only files with `ingestion_status == 'VALIDATED'` are eligible for task submission.
   - Files in `PENDING`, `UPLOADING`, or `FAILED_VALIDATION` states are flagged with explicit rejection reasons.

---

## 2. Ground Control Points (GCP) Standard

Ground Control Points provide real-world survey-grade coordinates (RTK/PPK GNSS) to anchor photogrammetric reconstructions, eliminating lens distortion drift and achieving centimeter-level absolute positioning.

### 2.1 File Format Specification
AgriDrone AutoMap enforces the standard OpenDroneMap GCP format (`gcp_list.txt`):
- **Header Line (Line 1)**: Must define the Coordinate Reference System (CRS).
  - Accepted Formats:
    - Proj4 string: `+proj=utm +zone=43 +datum=WGS84 +units=m +no_defs`
    - EPSG code: `EPSG:32643` or `EPSG:4326`
    - WKT representation
- **Coordinate Lines (Lines 2+)**: Space or tab-delimited records:
  ```
  X Y Z pixel_x pixel_y image_name [point_identifier]
  ```
  - `X`: Easting / Longitude
  - `Y`: Northing / Latitude
  - `Z`: Ellipsoidal / Orthometric Elevation in meters
  - `pixel_x`, `pixel_y`: 2D pixel coordinates in image (optional for automatic GCP detection)
  - `image_name`: Drone image filename (e.g. `DJI_0102.JPG`)
  - `point_identifier`: Unique GCP tag (e.g. `GCP_1`)

### 2.2 Validation Algorithm (`validate_gcp_format`)
The backend parser (`app/services/webodm.py:validate_gcp_format`) executes rigorous checks:
1. **Empty File Check**: Rejects blank files or files with only comments.
2. **CRS Representation**: Flags headers lacking recognizable spatial tokens (`EPSG`, `+PROJ`, `WGS`, `UTM`).
3. **Minimum Points Gate**: Requires **at least 3 distinct non-collinear GCP locations**. If fewer than 3 unique coordinate pairs are detected, validation fails immediately.
4. **Number Parsing**: Validates that X, Y, Z are parseable floating-point numbers.
5. **No Silent Transformations**: Coordinates are preserved verbatim. AgriDrone AutoMap does not alter or reproject GCPs without explicit confirmation.

---

## 3. Upload & Task Attachment Workflow

1. **Client-Side Validation**:
   - When a user uploads a GCP file in the Ingestion Drawer, the frontend immediately posts the file text to `POST /api/v1/photogrammetry/gcp/validate`.
   - The UI displays the parsed CRS, total points, unique point count, and a coordinate inspection preview table.
2. **Survey Attachment**:
   - The GCP file is saved as a `SurveyFile` with `file_type='GCP'`.
3. **Task Assembly**:
   - During task creation, the user selects the validated GCP file.
   - The Celery worker fetches the GCP content from Azure Blob Storage and attaches it as `("gcp", ("gcp_list.txt", gcp_bytes, "text/plain"))` in the multipart request sent to WebODM.
   - WebODM automatically passes `--gcp gcp_list.txt` to the underlying OpenDroneMap engine.
