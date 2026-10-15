# API Endpoints Specification — Phase 7

All Phase 7 endpoints are hosted under the versioned prefix `/api/v1/algorithms`.

---

## 1. Supported Algorithms
- **Route**: `GET /api/v1/algorithms/supported`
- **Response**: `200 OK`
- **Payload**: List of `AlgorithmSpecResponse` objects containing algorithm code, display name, formula, required bands, expected output range, and default parameters.

---

## 2. List Eligible Source Rasters
- **Route**: `GET /api/v1/algorithms/eligible-rasters`
- **Query Parameters**: `survey_id` (UUID, optional)
- **Response**: `200 OK`
- **Payload**: `EligibleRastersResponse` containing orthomosaics (from `map_products`) and pre-stitched GeoTIFFs (from `survey_files`) with sensor type, band count, resolution, and eligibility flags.

---

## 3. Inspect Source Raster
- **Route**: `GET /api/v1/algorithms/inspect/{source_id}`
- **Query Parameters**: `source_type` ("MAP_PRODUCT" | "SURVEY_FILE")
- **Response**: `200 OK`
- **Payload**: `RasterInspectionResponse` detailing dimensions, CRS, bounds, GSD, detected sensor type, radiometric classification, suggested band mapping, and per-band statistics.

---

## 4. Validate Band Mapping
- **Route**: `POST /api/v1/algorithms/validate-mapping`
- **Request Body**:
  ```json
  {
    "band_count": 5,
    "mapping": {"NIR": 5, "RedEdge": 4, "Red": 3, "Green": 2, "Blue": 1},
    "algorithm_codes": ["NDVI", "NDRE", "SAVI"]
  }
  ```
- **Response**: `200 OK`
- **Payload**: `BandMappingValidateResponse` with per-algorithm compatibility flags and diagnostic error messages.

---

## 5. Submit Multi-Map Algorithm Batch
- **Route**: `POST /api/v1/algorithms/jobs`
- **Status**: `202 Accepted`
- **Request Body**:
  ```json
  {
    "source_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "source_type": "MAP_PRODUCT",
    "band_mapping": {"NIR": 5, "RedEdge": 4, "Red": 3, "Green": 2, "Blue": 1},
    "algorithms": [
      {"algorithm_code": "NDVI"},
      {"algorithm_code": "NDRE"},
      {"algorithm_code": "SAVI", "parameters": {"L": 0.5}}
    ]
  }
  ```
- **Response**: `AlgorithmBatchResponse` with `batch_id`, status `QUEUED`, and created job descriptors.

---

## 6. Get Batch Status
- **Route**: `GET /api/v1/algorithms/batches/{batch_id}`
- **Response**: `200 OK`
- **Payload**: `AlgorithmBatchResponse` with aggregate status (`QUEUED`, `RUNNING`, `COMPLETED`, `PARTIALLY_COMPLETED`, `FAILED`), completed job count, and per-job progress percentages.

---

## 7. List / Get Algorithm Jobs
- **Route**: `GET /api/v1/algorithms/jobs`
- **Query Parameters**: `survey_id` (optional), `status` (optional), `limit` (int, default 50)
- **Route**: `GET /api/v1/algorithms/jobs/{job_id}`
- **Response**: `200 OK`
- **Payload**: `AlgorithmJobResponse`

---

## 8. Retry Failed Job
- **Route**: `POST /api/v1/algorithms/jobs/{job_id}/retry`
- **Response**: `200 OK`
- **Payload**: `AlgorithmJobResponse` with reset status and incremented `retry_count`.

---

## 9. Get Map Product Details & Zonal Statistics
- **Route**: `GET /api/v1/algorithms/products/{product_id}`
- **Response**: `200 OK`
- **Payload**: `MapProductDetailResponse` with signed access URL, COG verification status, statistical summary, and 4-zone vigour breakdown.
