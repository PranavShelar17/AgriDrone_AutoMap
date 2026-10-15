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
