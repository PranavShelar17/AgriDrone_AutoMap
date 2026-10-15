# AgriDrone AutoMap — Functional Requirements Specification

## 1. Overview & Requirement Numbering Convention

This document specifies the formal functional requirements for the AgriDrone AutoMap platform. Each requirement is assigned a unique identifier according to its operational domain:

- `FR-SURV-xxx`: Survey & Spatial Hierarchy Management
- `FR-INGT-xxx`: File Ingestion & Metadata Validation
- `FR-PHOT-xxx`: WebODM Photogrammetry Management
- `FR-GIS-xxx`: GIS Processing & Index Generation
- `FR-MAP-xxx`: Interactive Map Visualization
- `FR-STAT-xxx`: Statistical Analytics & Zoning
- `FR-REP-xxx`: PDF Report Generation
- `FR-SEC-xxx`: User Access, Tenancy & Permissions
- `FR-ERR-xxx`: Error Handling, Resiliency & Recovery

---

## 2. Survey & Hierarchy Management (`FR-SURV`)

| Requirement ID | Title | Description | Testable Expected Outcome |
| :--- | :--- | :--- | :--- |
| **FR-SURV-001** | Farm Entity Creation | The system must allow administrators to create a Farm record with name, description, country, and assigned tenant owner ID. | A new Farm record is stored in PostgreSQL with a unique UUID and associated owner. |
| **FR-SURV-002** | Field Boundary Ingestion | The system must allow administrators to upload a field boundary polygon via GeoJSON or WKT geometry. | The polygon is stored as a PostGIS `GEOMETRY(Polygon, 4326)` and validated for topological correctness (no self-intersections). |
| **FR-SURV-003** | Survey Event Creation | The system must allow creating a Survey flight event linked to a Field, capturing Flight Date, Sensor Model, Flight Altitude (meters), and Operator Notes. | Survey record is created in status `DRAFT` linked via foreign key to the parent Field. |
| **FR-SURV-004** | Survey State Transition | The system must transition survey states (`DRAFT` $\rightarrow$ `UPLOADED` $\rightarrow$ `PROCESSING` $\rightarrow$ `COMPLETED` $\rightarrow$ `PUBLISHED`). | Invalid state transitions (e.g. attempting to publish a `DRAFT` survey) are rejected with HTTP 400. |

---

## 3. File Ingestion & Pre-Flight Validation (`FR-INGT`)

| Requirement ID | Title | Description | Testable Expected Outcome |
| :--- | :--- | :--- | :--- |
| **FR-INGT-001** | Chunked File Upload | The system must support chunked, resumable file uploads for batches of drone photographs and multi-gigabyte GeoTIFF files. | Uploads exceeding 1GB complete reliably without HTTP timeout or memory exhaustion. |
| **FR-INGT-002** | Raw Photo EXIF Validation | The system must inspect EXIF/XMP metadata on raw photo batches (`.jpg`, `.jpeg`, `.dng`, `.tif`) to verify presence of latitude, longitude, and altitude. | System calculates GPS geotag percentage; flags an error if $< 90\%$ of images contain valid geotags. |
| **FR-INGT-003** | GeoTIFF Spatial Validation | For pre-stitched raster uploads, the system must use GDAL/Rasterio to verify spatial georeferencing, affine transform, dimensions, and Coordinate Reference System (CRS). | Rasters lacking georeferencing or with undefined CRS are rejected with a descriptive validation error. |
| **FR-INGT-004** | Azure Storage Archival | All ingested files must be written directly to private Microsoft Azure Blob Storage containers structured by `{tenant_id}/{farm_id}/{survey_id}/...`. | Blob is verified in Azure Blob Storage; storage key is never exposed to client; file path reference is recorded in PostgreSQL. |
| **FR-INGT-005** | Eligibility Tagging | The system must classify each ingested dataset into an eligibility status: `ELIGIBLE_WEBODM`, `ELIGIBLE_DIRECT_GIS`, or `INVALID_METADATA`. | Dataset ledger on Page 1 displays the accurate eligibility badge matching file characteristics. |

---

## 4. WebODM Photogrammetry Processing (`FR-PHOT`)

| Requirement ID | Title | Description | Testable Expected Outcome |
| :--- | :--- | :--- | :--- |
| **FR-PHOT-001** | Asynchronous Task Submission | The system must submit validated raw image batches to an external WebODM instance via REST API without blocking the web backend. | FastAPI dispatches a Celery background job, returning HTTP 202 Accepted with a Celery Task ID. |
| **FR-PHOT-002** | Photogrammetry Preset Options | The system must allow administrators to select WebODM option presets (e.g., Ground Sample Distance target, feature quality, DSM generation). | WebODM task parameters accurately reflect selected preset flags in the API payload. |
| **FR-PHOT-003** | Task Progress & Log Polling | The system must periodically poll the WebODM task endpoint and stream progress percentages and log output to the Page 2 console. | Page 2 UI updates the progress bar ($0-100\%$) and appends real-time log messages. |
| **FR-PHOT-004** | Task Cancellation | Operators must be able to cancel an active WebODM processing task. | WebODM task is aborted, worker resources are freed, and task status in PostgreSQL is marked `CANCELED`. |
| **FR-PHOT-005** | Orthomosaic Ingestion | Upon WebODM task completion, the system must download the resulting orthophoto GeoTIFF, upload it to Azure Blob Storage, and record its spatial properties. | Orthomosaic record is created in PostgreSQL with CRS, GSD, bounding box, and Azure Blob URI; survey is marked `ELIGIBLE_DIRECT_GIS`. |

---

## 5. GIS Processing & Algorithm Generation (`FR-GIS`)

| Requirement ID | Title | Description | Testable Expected Outcome |
| :--- | :--- | :--- | :--- |
| **FR-GIS-001** | Spectral Band Assignment | The system must inspect raster band count and allow operators to verify/assign bands (Red, Green, Blue, Red Edge, NIR). | Band mapping configuration is stored as a JSON object on the survey raster record. |
| **FR-GIS-002** | Spectral Compatibility Gating | The system must disable vegetation index algorithms if required spectral bands are not assigned (e.g. NDVI requires NIR and Red). | Attempting to execute NDVI without NIR assigned triggers an HTTP 422 Unprocessable Entity with message explaining missing band. |
| **FR-GIS-003** | NDVI Calculation | The system must calculate NDVI using $\frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red}}$ using Rasterio and masked NumPy arrays. | Generated raster contains float values strictly clamped to $[-1.0, +1.0]$, ignoring NoData pixels. |
| **FR-GIS-004** | NDRE Calculation | The system must calculate NDRE using $\frac{\text{NIR} - \text{RedEdge}}{\text{NIR} + \text{RedEdge}}$ when NIR and Red Edge are available. | Generated raster reflects Red-Edge sensitive index with output values clamped to $[-1.0, +1.0]$. |
| **FR-GIS-005** | GNDVI Calculation | The system must calculate GNDVI using $\frac{\text{NIR} - \text{Green}}{\text{NIR} + \text{Green}}$ when NIR and Green are available. | Generated raster reflects Green-band sensitive chlorophyll index clamped to $[-1.0, +1.0]$. |
| **FR-GIS-006** | SAVI Calculation | The system must calculate SAVI using $\frac{(1 + L)(\text{NIR} - \text{Red})}{\text{NIR} + \text{Red} + L}$ using a user-specified $L$ factor (default $0.5$). | Generated raster applies soil brightness adjustment factor $L$ correctly without division by zero. |
| **FR-GIS-007** | Cloud Optimized GeoTIFF (COG) Output | All generated index rasters must be converted to Cloud Optimized GeoTIFF format with internal tiling and overviews. | Output raster passes `rio cogeo validate` and supports HTTP range-request tile reading. |

---

## 6. Interactive Map Visualization (`FR-MAP`)

| Requirement ID | Title | Description | Testable Expected Outcome |
| :--- | :--- | :--- | :--- |
| **FR-MAP-001** | MapLibre Geospatial Canvas | The system must render an interactive map canvas using MapLibre GL JS centered on the active field's bounding box. | Map loads satellite basemap and smoothly zooms to the PostGIS field boundary extent. |
| **FR-MAP-002** | Dynamic Layer Toggling | Users must be able to toggle between available survey layers (RGB Orthomosaic, NDVI, NDRE, GNDVI, SAVI). | Map canvas updates layer visibility instantly without full map reload. |
| **FR-MAP-003** | Layer Opacity Control | Users must be able to adjust layer transparency via a continuous slider ($0\%$ to $100\%$). | MapLibre layer opacity property updates smoothly in real time. |
| **FR-MAP-004** | Dual-Layer Split Comparison | Users must be able to split the screen with a draggable comparison slider to compare RGB Ortho against an Index layer. | Swiping the divider reveals underlying RGB orthomosaic vs. false-color vegetation index. |
| **FR-MAP-005** | Coordinate Pixel Value Probe | Clicking on any coordinate within the field must display the exact calculated index value at that point. | UI popup displays clicked latitude, longitude, and pixel value (e.g., `NDVI: 0.68`). |
| **FR-MAP-006** | Dynamic Agronomic Legend | The viewer must display a color ramp legend matching the active index with qualitative vegetation health class labels. | Legend displays color brackets corresponding to calibrated numerical intervals. |

---

## 7. Statistical Analytics & Zoning (`FR-STAT`)

| Requirement ID | Title | Description | Testable Expected Outcome |
| :--- | :--- | :--- | :--- |
| **FR-STAT-001** | Field Boundary Clipping | Statistical computations must be strictly clipped to the PostGIS field boundary polygon, masking out external pixels. | Pixels outside the field polygon boundary are excluded from statistical metrics. |
| **FR-STAT-002** | Core Metrics Calculation | The system must calculate Mean, Median, Standard Deviation, Minimum, and Maximum for valid pixels of each generated index. | Metrics match independent NumPy verification within $0.001$ precision and are stored in PostgreSQL. |
| **FR-STAT-003** | Zonal Health Classification | The system must partition field pixels into predefined agronomic brackets (e.g., Dense Canopy, Moderate Canopy, Stressed/Sparse, Bare Soil). | System reports both square meters/hectares and percentage of total field area for each bracket. |
| **FR-STAT-004** | Limitations Disclosure | If high variability or potential sensor/cloud artifacts are detected, the system must display clear data limitations notices. | Page 5 displays standard agronomic disclaimer requiring on-site ground scouting. |

---

## 8. PDF Report Generation (`FR-REP`)

| Requirement ID | Title | Description | Testable Expected Outcome |
| :--- | :--- | :--- | :--- |
| **FR-REP-001** | ReportLab PDF Assembly | The system must asynchronously compile an auditable, multi-page PDF summary report using ReportLab. | Celery worker produces a formatted PDF document containing survey metadata, overview map, histograms, and zonal stats. |
| **FR-REP-002** | Scientific Metadata Header | The PDF must include Farm Name, Field Name, Flight Date, Altitude, Camera/Sensor Model, and Processing Timestamp. | Header section is populated with verified metadata from PostgreSQL. |
| **FR-REP-003** | Agronomic Disclaimers | Every generated PDF must include the standard legal/agronomic disclaimer stating that index maps do not constitute definitive disease diagnosis. | Disclaimer text is present in the document footer/notes section. |
| **FR-REP-004** | Secure Report Archival | Generated PDFs must be stored in private Azure Blob Storage and linked to the survey record. | PDF is accessible to authorized farmers via time-limited SAS download link. |

---

## 9. Security, Tenancy & Permissions (`FR-SEC`)

| Requirement ID | Title | Description | Testable Expected Outcome |
| :--- | :--- | :--- | :--- |
| **FR-SEC-001** | Strict Tenant Isolation | The system must ensure that farmers can only view, query, and download data belonging to their assigned tenant/farm ID. | Direct API requests for unauthorized farm/survey IDs return HTTP 403 Forbidden. |
| **FR-SEC-002** | Role-Based Authorization | The system must separate Admin/Operator capabilities (uploading, WebODM, index creation) from Farmer capabilities (read-only viewer and downloads). | Farmers attempting to access Page 1, 2, or 3 endpoints are denied with HTTP 403 Forbidden. |
| **FR-SEC-003** | Secure Azure SAS Generation | All direct client downloads of GeoTIFFs and PDFs must utilize short-lived (maximum 15 minutes) Shared Access Signature (SAS) tokens generated on-demand. | SAS token expires after 15 minutes; storage account master keys are never exposed in API responses or client bundles. |
| **FR-SEC-004** | Input Sanitization | All file uploads, polygon geometries, and form inputs must be strictly sanitized and validated against malicious payloads. | File names are sanitized against path traversal (`../`); invalid WKT geometries are rejected. |

---

## 10. Error Handling & System Recovery (`FR-ERR`)

| Requirement ID | Title | Description | Testable Expected Outcome |
| :--- | :--- | :--- | :--- |
| **FR-ERR-001** | WebODM Node Failure Resiliency | If the WebODM instance crashes or becomes unreachable, the Celery task must record the failure state without crashing the worker. | Task status transitions to `FAILED` with descriptive error logged; system remains operational. |
| **FR-ERR-002** | Mathematical Edge Case Protection | Raster math operations must handle division by zero ($\text{NIR} + \text{Red} == 0$), NaN, and infinity values safely. | Pixels where denominator is 0 are assigned NoData without terminating execution. |
| **FR-ERR-003** | Resumable Task Recovery | Interrupted background jobs must be logged with failure reasons and allow operators to trigger a clean retry. | Operator can click "Retry Processing" on Page 2 or Page 3 without creating duplicate database records. |
