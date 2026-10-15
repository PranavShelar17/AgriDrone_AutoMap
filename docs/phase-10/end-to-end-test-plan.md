# End-to-End Test Plan — AgriDrone AutoMap

**Document:** Comprehensive E2E Test Strategy & Verification Plan  
**Phase:** Phase 10  
**Status:** Approved  
**Date:** October 2026  

---

## 1. Objectives & Scope

This test plan defines the end-to-end verification workflows across all five core platform pages and supporting authentication gates. It ensures that all individual phase deliverables (Phases 1–9) operate harmoniously as a unified, production-ready system.

---

## 2. Test Workflows Matrix

### Workflow A: Farm & Survey Hierarchy Management
- **Objective:** Verify that PostGIS farm and field entities persist accurately and enforce tenant-level ownership.
- **Test Scenarios:**
  - `E2E-A1`: Admin creates a new farm and field boundary.
  - `E2E-A2`: Admin schedules a new drone survey flight date.
  - `E2E-A3`: Farmer logs in and queries `/api/v1/farms` — only owned farms are returned.
  - `E2E-A4`: Farmer attempts direct query for competitor's farm ID — system responds with `HTTP 404 Not Found`.

### Workflow B: Drone Image Ingestion & Storage Validation
- **Objective:** Validate file ingestion rules, metadata extraction, and storage abstraction.
- **Test Scenarios:**
  - `E2E-B1`: Upload valid aerial drone JPEG with embedded GPS EXIF tags — confirmed valid.
  - `E2E-B2`: Upload corrupted image or unsupported format (e.g., `.exe` or `.txt`) — rejected with `400 Bad Request`.
  - `E2E-B3`: Upload file exceeding `MAX_UPLOAD_SIZE_BYTES` (500MB) — rejected with `413 Payload Too Large`.
  - `E2E-B4`: Upload pre-stitched GeoTIFF with CRS validation (EPSG:4326 / EPSG:3857) — registered as eligible for direct GIS analysis.
  - `E2E-B5`: Verify storage abstraction: file saved to configured Azure container or local dev fallback directory (`backend/storage/raw-surveys`).

### Workflow C: WebODM Photogrammetry Processing
- **Objective:** Validate WebODM cluster status polling and Celery asynchronous task execution.
- **Test Scenarios:**
  - `E2E-C1`: Query cluster status via `/api/v1/photogrammetry/nodes` — returns node liveness and available CPU/RAM cores.
  - `E2E-C2`: Submit photogrammetry reconstruction task for eligible survey photos — Celery worker queues task, tracks progress, and transitions through `QUEUED -> RUNNING -> COMPLETED`.
  - `E2E-C3`: Test error handling when WebODM node is simulated offline — task safely transitions to `FAILED` with non-sensitive error detail.

### Workflow D: GIS Multispectral Algorithms & Zonal Analytics
- **Objective:** Validate mathematical correctness of vegetation index formulas and NoData mask handling.
- **Test Scenarios:**
  - `E2E-D1`: Validate band mapping checks: reject 3-band RGB image for NIR-dependent indices (NDVI, NDRE, GNDVI).
  - `E2E-D2`: Calculate NDVI: $(NIR - Red) / (NIR + Red)$ on verified 4-band test raster — pixel values constrained strictly to $[-1.0, 1.0]$.
  - `E2E-D3`: Calculate NDRE: $(NIR - RedEdge) / (NIR + RedEdge)$ and SAVI with soil adjustment factor $L=0.5$.
  - `E2E-D4`: Zero-denominator protection: verify that $(NIR + Red) == 0$ pixels are assigned `NODATA_VALUE_FLOAT32` (-9999.0) without division-by-zero crashes.
  - `E2E-D5`: Verify zonal statistics: canopy health bins (Very Low, Low, Moderate, High, Very High) sum up accurately to 100% of valid field area.

### Workflow E: Interactive MapLibre Maps & Tile Streaming
- **Objective:** Verify WebGL map rendering, dynamic tile delivery, opacity blending, and point probing.
- **Test Scenarios:**
  - `E2E-E1`: MapLibre GL map initializes with correct PostGIS field boundary polygon centering.
  - `E2E-E2`: Request XYZ raster tile `/api/v1/maps/tiles/{id}/{z}/{x}/{y}.png` with valid session cookie — returns 256x256 RGBA colorized tile.
  - `E2E-E3`: Request tile with unauthenticated or competitor session — returns `404 Not Found`.
  - `E2E-E4`: Opacity slider dynamically adjusts raster layer opacity from 10% to 100%.
  - `E2E-E5`: Point probe `/api/v1/maps/products/{id}/probe?lat=...&lon=...` returns exact measured index value and classification label.
  - `E2E-E6`: Compare Layers mode renders dual synchronized map viewports with shared zoom and pan.

### Workflow F: Diagnostics & Agronomic PDF Report Generation
- **Objective:** Verify data-derived statistics and ReportLab PDF document compilation.
- **Test Scenarios:**
  - `E2E-F1`: Diagnostics summary displays real min, max, mean, std, and valid pixel counts.
  - `E2E-F2`: Agronomic safeguards banner confirms that vegetation greenness is an indicator of canopy light reflectance, not an autonomous diagnosis.
  - `E2E-F3`: Generate agronomic PDF report — creates valid multi-page document with farm metadata, survey code, zonal breakdown table, and disclaimer.
  - `E2E-F4`: Download report via `/api/v1/reports/{id}/download` — enforces ownership validation before returning short-lived SAS link.

### Workflow G: Authentication, Authorization & Anti-IDOR
- **Objective:** Verify security boundary, rate limiting, and tenant data isolation.
- **Test Scenarios:**
  - `E2E-G1`: Unauthenticated request to protected endpoint rejected with `401 Unauthorized`.
  - `E2E-G2`: Login with valid credentials returns HS256 JWT and sets `HttpOnly` session cookie.
  - `E2E-G3`: Rate limiter triggers `429 Too Many Requests` after 20 failed login attempts within 60 seconds.
  - `E2E-G4`: Anti-IDOR: Farmer 1 cannot read, probe, or download Farmer 2's survey files, tasks, raster products, or reports.
  - `E2E-G5`: Logout invalidates client session and clears cookies.
