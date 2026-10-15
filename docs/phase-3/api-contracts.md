# AgriDrone AutoMap — API Contracts & Specifications
## Document Reference: `docs/phase-3/api-contracts.md`
**Phase**: Phase 3 — System Architecture, Technical Validation & Implementation Blueprint  
**Status**: APPROVED ARCHITECTURE BLUEPRINT  
**Version**: 1.0.0  

---

## 1. REST API Conventions & Error Standards

All AgriDrone AutoMap REST endpoints adhere to strict API conventions under the versioned prefix `/api/v1`.

### 1.1. Status Codes
- `200 OK`: Request succeeded and returned data.
- `201 Created`: Resource successfully created.
- `202 Accepted`: Long-running background job initiated (e.g. photogrammetry, raster calculation, PDF generation). Response includes a `task_id` and polling URL.
- `400 Bad Request`: Incompatible request parameters or invalid scientific inputs (e.g., requesting NDVI on an RGB orthomosaic).
- `401 Unauthorized`: Missing or invalid Bearer token.
- `403 Forbidden`: Authenticated user lacks permission to access the requested tenant/farm resource.
- `404 Not Found`: Target entity does not exist.
- `422 Unprocessable Entity`: Request body failed Pydantic schema validation.

### 1.2. Standard Error Response Envelope
All error responses return a standardized JSON schema:
```json
{
  "error": {
    "code": "INCOMPATIBLE_SPECTRAL_INPUT",
    "message": "Algorithm NDVI requires Near-Infrared (NIR) band. The provided orthomosaic has only 3 bands (RGB).",
    "details": {
      "product_id": "8f3e29c1-4b1a-4d92-913b-e10c714890a2",
      "detected_bands": ["Red", "Green", "Blue"],
      "missing_bands": ["NIR"],
      "recommended_indices": ["VARI", "GLI", "TGI"]
    },
    "timestamp": "2026-10-14T15:00:00Z",
    "request_id": "req-98721-abc"
  }
}
```

---

## 2. API Endpoint Groups & Specifications

### Group 1: Health & Cluster Infrastructure
| Method | Endpoint | Purpose | Auth | Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/health` | Application, Database & Redis health check | Public | 200, 503 |
| `GET` | `/api/v1/cluster/status` | WebODM / NodeODM worker cluster capacity | Admin | 200, 502 |

#### Response Example: `GET /api/v1/cluster/status`
```json
{
  "cluster_status": "ONLINE",
  "active_nodes": 2,
  "total_nodes": 2,
  "queue_depth": 1,
  "nodes": [
    {
      "node_id": "node-01",
      "hostname": "nodeodm-worker-1",
      "status": "IDLE",
      "cpu_percent": 14.2,
      "ram_used_gb": 4.1,
      "ram_total_gb": 32.0,
      "active_tasks": 0
    },
    {
      "node_id": "node-02",
      "hostname": "nodeodm-worker-2",
      "status": "PROCESSING",
      "cpu_percent": 88.5,
      "ram_used_gb": 22.8,
      "ram_total_gb": 32.0,
      "active_tasks": 1
    }
  ]
}
```

---

### Group 2: Ingestion & Upload Management (Page 1)
| Method | Endpoint | Purpose | Auth | Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/surveys/{survey_id}/uploads/initiate` | Request direct Azure chunked upload SAS | Admin | 200, 400, 403 |
| `POST` | `/api/v1/surveys/{survey_id}/uploads/{upload_id}/finalize` | Complete upload and trigger raster validation | Admin | 202, 400, 404 |
| `GET` | `/api/v1/surveys/{survey_id}/files` | Retrieve file validation ledger | Admin | 200, 404 |

#### Request Example: `POST /api/v1/surveys/{survey_id}/uploads/initiate`
```json
{
  "original_filename": "DJI_Baramati_BlockB_RGB.zip",
  "file_type": "RAW_ZIP",
  "file_size_bytes": 1845493820,
  "mime_type": "application/zip",
  "expected_checksum_md5": "d41d8cd98f00b204e9800998ecf8427e"
}
```

#### Response Example: `POST /api/v1/surveys/{survey_id}/uploads/initiate`
```json
{
  "upload_id": "upl-4019-91a2",
  "blob_uri": "raw-surveys/srv-2026-001/DJI_Baramati_BlockB_RGB.zip",
  "sas_upload_url": "https://agridronestorage.blob.core.windows.net/raw-surveys/srv-2026-001/DJI_Baramati_BlockB_RGB.zip?sv=2024-11-04&se=2026-10-14T15%3A15%3A00Z&sr=b&sp=rw&sig=EXAMPLE_SIG",
  "recommended_chunk_size_bytes": 8388608,
  "expires_at": "2026-10-14T15:15:00Z"
}
```

---

### Group 3: WebODM Photogrammetry Reconstruction (Page 2)
| Method | Endpoint | Purpose | Auth | Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/photogrammetry/tasks` | Dispatch WebODM reconstruction job | Admin | 202, 400, 409 |
| `GET` | `/api/v1/photogrammetry/tasks/{task_id}` | Poll task progress, current stage & metrics | Admin | 200, 404 |
| `GET` | `/api/v1/photogrammetry/tasks/{task_id}/logs` | Stream or poll execution console logs | Admin | 200, 404 |
| `POST` | `/api/v1/photogrammetry/tasks/{task_id}/cancel`| Cancel active photogrammetry task | Admin | 200, 400 |

#### Request Example: `POST /api/v1/photogrammetry/tasks`
```json
{
  "survey_id": "srv-2026-bar-001",
  "source_file_id": "fil-8812-7102",
  "resolution_preset": "HIGH_RES",
  "custom_resolution_cm": 2.5,
  "generate_dsm": true,
  "generate_dtm": true,
  "radiometric_calibration": false,
  "feature_quality": "ultra"
}
```

#### Response Example: `GET /api/v1/photogrammetry/tasks/{task_id}`
```json
{
  "task_id": "tsk-5501-89a1",
  "survey_id": "srv-2026-bar-001",
  "webodm_task_uuid": "e819b21a-9812-4f11-b012-7612a81901a2",
  "status": "RUNNING",
  "progress_percent": 68,
  "current_stage": "Dense Point Cloud Matching",
  "elapsed_seconds": 1240,
  "estimated_remaining_seconds": 580,
  "generated_products": [],
  "error_message": null
}
```

---

### Group 4: Spectral Algorithms & Multi-Map Generation (Page 3)
| Method | Endpoint | Purpose | Auth | Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/algorithms/inspect-bands` | Inspect raster bands & check algorithm compatibility | Admin | 200, 404 |
| `POST` | `/api/v1/algorithms/jobs` | Dispatch asynchronous index computation | Admin | 202, 400 |
| `GET` | `/api/v1/algorithms/jobs/{job_id}` | Poll index computation job status | Admin | 200, 404 |
| `PATCH` | `/api/v1/map-products/{product_id}/publish` | Toggle layer publication for Farmer Portal | Admin | 200, 404 |

#### Response Example: `GET /api/v1/algorithms/inspect-bands?product_id=prod-101`
```json
{
  "product_id": "prod-101",
  "sensor_type": "RGB",
  "band_count": 3,
  "detected_channels": [
    {"band_index": 1, "color": "Red", "wavelength_nm": 660},
    {"band_index": 2, "color": "Green", "wavelength_nm": 560},
    {"band_index": 3, "color": "Blue", "wavelength_nm": 480}
  ],
  "compatibility": {
    "NDVI": {"eligible": false, "reason": "Requires Near-Infrared (NIR) band not present in standard RGB sensors."},
    "NDRE": {"eligible": false, "reason": "Requires RedEdge & NIR bands."},
    "VARI": {"eligible": true, "formula": "(Green - Red) / (Green + Red - Blue)"},
    "GLI": {"eligible": true, "formula": "(2*Green - Red - Blue) / (2*Green + Red + Blue)"},
    "SAVI": {"eligible": false, "reason": "Requires NIR band."}
  }
}
```

---

### Group 5: Farmer Portal & GIS Layer Delivery (Page 4)
| Method | Endpoint | Purpose | Auth | Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/portal/farms` | List authorized farms for logged-in farmer | Farmer | 200 |
| `GET` | `/api/v1/portal/surveys/{survey_id}` | Fetch survey boundary GeoJSON & layer catalog | Farmer | 200, 403, 404 |
| `GET` | `/api/v1/portal/products/{product_id}/sas-url` | Generate temporary 15-min SAS download link | Farmer | 200, 403 |

#### Response Example: `GET /api/v1/portal/surveys/{survey_id}`
```json
{
  "survey_id": "srv-2026-bar-001",
  "survey_code": "SRV-2026-BAR-001",
  "flight_date": "2026-10-12",
  "field_name": "Gat No. 22 - Sugar Cane Block",
  "farm_name": "Baramati Agro Holding",
  "field_boundary_geojson": {
    "type": "Feature",
    "geometry": {
      "type": "Polygon",
      "coordinates": [[[74.581, 18.152], [74.586, 18.153], [74.585, 18.148], [74.581, 18.152]]]
    },
    "properties": {"area_acres": 15.64}
  },
  "published_layers": [
    {
      "product_id": "prod-101",
      "layer_name": "High-Res True Color Orthophoto",
      "product_type": "ORTHOPHOTO",
      "cog_tile_endpoint": "https://agridronestorage.blob.core.windows.net/orthomosaics/srv-001/ortho_cog.tif?sas=...",
      "resolution_cm": 2.4,
      "default_opacity": 1.0
    },
    {
      "product_id": "prod-102",
      "layer_name": "VARI Canopy Vigour Index",
      "product_type": "INDEX_VARI",
      "cog_tile_endpoint": "https://agridronestorage.blob.core.windows.net/vegetation-indices/srv-001/vari_cog.tif?sas=...",
      "colormap": "RdYlGn",
      "value_range": [-0.2, 0.65],
      "default_opacity": 0.85
    }
  ]
}
```

---

### Group 6: Diagnostics & PDF Reports (Page 5)
| Method | Endpoint | Purpose | Auth | Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/diagnostics/{survey_id}/summary` | Retrieve validated statistical distributions | Auth | 200, 404 |
| `POST` | `/api/v1/reports/generate` | Dispatch ReportLab PDF generation job | Auth | 202, 400 |
| `GET` | `/api/v1/reports/{report_id}` | Poll PDF generation status | Auth | 200, 404 |
| `GET` | `/api/v1/reports/{report_id}/download-url` | Obtain 15-minute SAS download link for PDF | Auth | 200, 403 |

#### Response Example: `GET /api/v1/diagnostics/{survey_id}/summary`
```json
{
  "survey_id": "srv-2026-bar-001",
  "analyzed_acres": 15.64,
  "mean_index_value": 0.44,
  "median_index_value": 0.46,
  "std_dev": 0.12,
  "zonal_distribution": [
    {"zone": "High Vigour", "color": "#15803d", "range": "> 0.45", "area_acres": 8.45, "percentage": 54.0},
    {"zone": "Moderate Vigour", "color": "#ca8a04", "range": "0.20 - 0.45", "area_acres": 4.85, "percentage": 31.0},
    {"zone": "Stressed / Low Vigour", "color": "#dc2626", "range": "< 0.20", "area_acres": 2.34, "percentage": 15.0}
  ],
  "disclaimer": "Reflectance values represent optical surface observations and must be verified with ground-truth soil or tissue sampling."
}
```
