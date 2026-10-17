# API Contracts — WebODM Photogrammetry Integration

All Photogrammetry endpoints are served under `/api/v1/photogrammetry` and require a valid Bearer JWT.

---

## 1. Projects API

### 1.1 List Photogrammetry Projects
- **Endpoint**: `GET /api/v1/photogrammetry/projects`
- **Access**: Farmers (scoped to owned farms) | Administrators (all projects)
- **Query Parameters**:
  - `farm_id` (optional, UUID)
  - `field_id` (optional, UUID)
  - `search` (optional, string)
  - `skip` (optional, integer, default: 0)
  - `limit` (optional, integer, default: 50)
- **Response**: `200 OK`
```json
{
  "items": [
    {
      "id": "e45f1b80-87b2-4d2b-9be0-cb75bbf2d989",
      "name": "Baramati High-Res Survey 2026",
      "description": "Sugarcane multispectral survey",
      "farm_id": "99b0c2a2-3b24-4f51-b8ea-f59792040bc1",
      "farm_name": "Patil Cane Farm",
      "field_id": "0382d56d-e4c1-42cb-b169-23114d7a7182",
      "field_name": "Plot A Cane",
      "survey_id": null,
      "survey_code": null,
      "webodm_project_id": null,
      "tags": ["sugarcane", "high-res"],
      "tasks_count": 2,
      "latest_task_status": "COMPLETED",
      "available_outputs_count": 2,
      "created_at": "2026-10-15T10:00:00Z",
      "updated_at": "2026-10-15T10:30:00Z"
    }
  ],
  "total": 1,
  "skip": 0,
  "limit": 50
}
```

### 1.2 Create Photogrammetry Project
- **Endpoint**: `POST /api/v1/photogrammetry/projects`
- **Access**: Authorized Farmer or Administrator
- **Request Body**:
```json
{
  "name": "Baramati High-Res Survey 2026",
  "description": "Sugarcane multispectral survey",
  "farm_id": "99b0c2a2-3b24-4f51-b8ea-f59792040bc1",
  "field_id": "0382d56d-e4c1-42cb-b169-23114d7a7182",
  "survey_id": null,
  "tags": ["sugarcane"]
}
```
- **Response**: `201 Created`

### 1.3 Update Project
- **Endpoint**: `PATCH /api/v1/photogrammetry/projects/{project_id}`
- **Access**: Project Owner or Administrator
- **Response**: `200 OK`

### 1.4 Delete Project
- **Endpoint**: `DELETE /api/v1/photogrammetry/projects/{project_id}`
- **Access**: Project Owner or Administrator
- **Response**: `200 OK`

---

## 2. Ground Control Points (GCP) API

### 2.1 Validate GCP Format
- **Endpoint**: `POST /api/v1/photogrammetry/gcp/validate`
- **Access**: Authenticated User
- **Request Body**:
```json
{
  "content": "+proj=utm +zone=43 +datum=WGS84 +units=m +no_defs\n385200.12 2011400.45 540.23 1250 820 DJI_001.JPG\n385220.89 2011410.60 541.02 1400 950 DJI_002.JPG\n385240.34 2011430.12 540.88 1650 1100 DJI_003.JPG\n",
  "filename": "gcp_list.txt"
}
```
- **Response**: `200 OK`
```json
{
  "valid": true,
  "crs": "+proj=utm +zone=43 +datum=WGS84 +units=m +no_defs",
  "point_count": 3,
  "distinct_count": 3,
  "points": [
    {
      "line": 2,
      "point_id": "GCP_1",
      "easting_x": 385200.12,
      "northing_y": 2011400.45,
      "elevation_z": 540.23,
      "pixel_x": 1250.0,
      "pixel_y": 820.0,
      "image_name": "DJI_001.JPG"
    }
  ],
  "errors": [],
  "warnings": []
}
```

---

## 3. Tasks & Monitoring API

### 3.1 Create Task
- **Endpoint**: `POST /api/v1/photogrammetry/tasks`
- **Access**: Farmer (owning survey) | Administrator
- **Payload**:
```json
{
  "survey_id": "99b0c2a2-3b24-4f51-b8ea-f59792040bc1",
  "project_id": "e45f1b80-87b2-4d2b-9be0-cb75bbf2d989",
  "resolution_preset": "HIGH_RES",
  "custom_resolution_cm": 2.5,
  "generate_dsm": true,
  "generate_dtm": true,
  "radiometric_calibration": false,
  "feature_quality": "high",
  "pc_quality": "medium"
}
```
- **Response**: `202 Accepted` (Dispatched to Celery worker)

### 3.2 Get Task Status
- **Endpoint**: `GET /api/v1/photogrammetry/tasks/{task_id}`
- **Response**: `200 OK`

### 3.3 Stream Task Console Logs
- **Endpoint**: `GET /api/v1/photogrammetry/tasks/{task_id}/logs?limit=500`
- **Response**: `200 OK`

### 3.4 Cancel Running Task
- **Endpoint**: `POST /api/v1/photogrammetry/tasks/{task_id}/cancel`
- **Response**: `200 OK`

### 3.5 Retry Task
- **Endpoint**: `POST /api/v1/photogrammetry/tasks/{task_id}/retry`
- **Response**: `202 Accepted`

---

## 4. Administration & Diagnostics (Admin Only)

### 4.1 Processing Nodes Telemetry
- **Endpoint**: `GET /api/v1/photogrammetry/nodes`
- **Access**: `ADMIN` only (`403 Forbidden` for farmers)
- **Response**: `200 OK` (list of cluster nodes, RAM, queue counts)

### 4.2 System Diagnostics Probe
- **Endpoint**: `GET /api/v1/photogrammetry/diagnostics`
- **Access**: `ADMIN` only (`403 Forbidden` for farmers)
- **Response**: `200 OK` (connectivity across WebODM, DB, Redis, Storage + runbook recommendations)

### 4.3 Administrator Configuration
- **Endpoint**: `GET /api/v1/photogrammetry/admin/config`
- **Access**: `ADMIN` only (`403 Forbidden` for farmers)
- **Response**: `200 OK` (timeouts, poll intervals, storage engines, preset options)

---

## 5. Processing Options & Presets API

### 5.1 Get Processing Options Schema
- **Endpoint**: `GET /api/v1/photogrammetry/options/schema`
- **Access**: Authenticated User
- **Description**: Returns the dynamic OpenDroneMap option specifications (names, types, defaults, choices, and descriptions).
- **Response**: `200 OK`
```json
[
  {
    "name": "dsm",
    "type": "bool",
    "default": true,
    "description": "Generate a Digital Surface Model (DSM) including canopy tops and structures."
  },
  {
    "name": "feature-quality",
    "type": "choice",
    "choices": ["ultra", "high", "medium", "low", "lowest"],
    "default": "high",
    "description": "Quality of feature detection in OpenSfM matching."
  }
]
```

### 5.2 Get Preset Catalog
- **Endpoint**: `GET /api/v1/photogrammetry/presets`
- **Access**: Authenticated User
- **Description**: Returns recommended agricultural configuration presets.
- **Response**: `200 OK`
```json
[
  {
    "id": 1,
    "name": "Fast 2D Orthophoto",
    "code": "FAST",
    "target_gsd_cm": 5.0,
    "dsm": false,
    "dtm": false,
    "feature_quality": "medium",
    "pc_quality": "low",
    "recommended_for": "Initial field boundary check, flight verification"
  },
  {
    "id": 2,
    "name": "Field Precision (High-Res)",
    "code": "HIGH_RES",
    "target_gsd_cm": 2.5,
    "dsm": true,
    "dtm": true,
    "feature_quality": "high",
    "pc_quality": "medium",
    "recommended_for": "Canopy height models, elevation gradients, standard crop monitoring"
  }
]
```

---

## 6. Map Tiles, Bounds & Metadata API

### 6.1 Dynamic Map Tile Proxy
- **Endpoint**: `GET /api/v1/photogrammetry/tasks/{task_id}/tiles/{tile_type}/{z}/{x}/{y}.png`
- **Access**: Project Owner or Administrator
- **Path Parameters**:
  - `task_id` (UUID): Photogrammetry task identifier
  - `tile_type` (string): `orthophoto` | `dsm` | `dtm`
  - `z`, `x`, `y` (integers): Slippy map tile coordinates
- **Query Parameters**:
  - `colormap` (optional, string): `viridis` | `terrain` | `plasma` | `magma` | `greys`
  - `hillshade` (optional, boolean): Render shaded relief for elevation rasters
- **Response**: `200 OK` with `image/png` binary content or transparent 1x1 fallback tile.

### 6.2 Deliverable Geospatial Bounds
- **Endpoint**: `GET /api/v1/photogrammetry/tasks/{task_id}/tiles/{tile_type}/bounds`
- **Access**: Project Owner or Administrator
- **Response**: `200 OK`
```json
{
  "task_id": "e45f1b80-87b2-4d2b-9be0-cb75bbf2d989",
  "tile_type": "orthophoto",
  "bounds": [74.58012, 18.15045, 74.59560, 18.16580]
}
```

### 6.3 Technical Raster Metadata
- **Endpoint**: `GET /api/v1/photogrammetry/tasks/{task_id}/tiles/{tile_type}/metadata`
- **Access**: Project Owner or Administrator
- **Response**: `200 OK`
```json
{
  "task_id": "e45f1b80-87b2-4d2b-9be0-cb75bbf2d989",
  "tile_type": "orthophoto",
  "width": 8192,
  "height": 8192,
  "bands": 3,
  "gsd_cm": 2.45,
  "crs": "EPSG:32643",
  "has_alpha": true
}
```

---

## 7. Deliverables & 3D Visualization API

### 7.1 Inspect 3D Models & Point Cloud Assets
- **Endpoint**: `GET /api/v1/photogrammetry/tasks/{task_id}/3d-assets`
- **Access**: Project Owner or Administrator
- **Response**: `200 OK`
```json
{
  "task_id": "e45f1b80-87b2-4d2b-9be0-cb75bbf2d989",
  "status": "COMPLETED",
  "textured_mesh": {
    "format": "GLB (glTF 2.0)",
    "available": true,
    "filename": "textured_model.glb",
    "download_url": "/api/v1/photogrammetry/tasks/e45f1b80-87b2-4d2b-9be0-cb75bbf2d989/download/textured_model.glb"
  },
  "point_cloud": {
    "format": "LAZ (Compressed LiDAR/SfM Point Cloud)",
    "available": true,
    "filename": "georeferenced_model.laz",
    "download_url": "/api/v1/photogrammetry/tasks/e45f1b80-87b2-4d2b-9be0-cb75bbf2d989/download/georeferenced_model.laz",
    "estimated_points": 1250000
  },
  "quality_report": {
    "format": "PDF Summary Report",
    "available": true,
    "filename": "report.pdf",
    "download_url": "/api/v1/photogrammetry/tasks/e45f1b80-87b2-4d2b-9be0-cb75bbf2d989/download/report.pdf"
  }
}
```

### 7.2 Download Photogrammetry Asset
- **Endpoint**: `GET /api/v1/photogrammetry/tasks/{task_id}/download/{asset_name}`
- **Access**: Project Owner or Administrator
- **Whitelisted Assets**:
  - `orthophoto.tif`, `dsm.tif`, `dtm.tif`, `textured_model.glb`, `georeferenced_model.laz`, `report.pdf`, `all.zip`, `cameras.json`
- **Response**: `200 OK` (binary attachment stream or redirect to pre-authenticated short-lived Azure SAS URL).

