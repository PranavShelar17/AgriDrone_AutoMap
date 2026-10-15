# AgriDrone AutoMap — Phase 6 API Endpoints Reference
## Document Reference: `docs/phase-6/api-endpoints.md`
**Phase**: Phase 6 — WebODM / OpenDroneMap Integration & Drone Photogrammetry Processing  
**Status**: APPROVED API SPECIFICATION  
**Version**: 1.0.0  

---

## 1. WebODM Photogrammetry API Group

All Phase 6 endpoints operate under the versioned prefix `/api/v1/photogrammetry` (with `/api/v1/cluster/status` provided as a standard alias).

| Method | Endpoint | Description | Status Codes |
| :--- | :--- | :--- | :--- |
| `GET` | `/api/v1/photogrammetry/cluster-status` | Probes WebODM / NodeODM cluster connectivity and RAM. | `200 OK` |
| `GET` | `/api/v1/cluster/status` | Alias for cluster status probe (Phase 3 spec). | `200 OK` |
| `GET` | `/api/v1/photogrammetry/eligible-datasets` | Lists survey datasets with photogrammetry eligibility flags. | `200 OK` |
| `POST` | `/api/v1/photogrammetry/tasks` | Submits and dispatches an asynchronous reconstruction job. | `202 Accepted`, `400 Bad Request`, `404 Not Found`, `409 Conflict` |
| `GET` | `/api/v1/photogrammetry/tasks` | Lists photogrammetry tasks filtered by survey or status. | `200 OK` |
| `GET` | `/api/v1/photogrammetry/tasks/{task_id}` | Retrieves detailed metrics, progress percent, and stage. | `200 OK`, `404 Not Found` |
| `GET` | `/api/v1/photogrammetry/tasks/{task_id}/logs` | Retrieves console execution logs with timestamps. | `200 OK`, `404 Not Found` |
| `GET` | `/api/v1/photogrammetry/tasks/{task_id}/artifacts` | Lists registered output deliverables (`ORTHOPHOTO`, `DSM`). | `200 OK`, `404 Not Found` |
| `POST` | `/api/v1/photogrammetry/tasks/{task_id}/cancel` | Aborts an active or queued photogrammetry task. | `200 OK`, `400 Bad Request`, `404 Not Found` |
| `POST` | `/api/v1/photogrammetry/tasks/{task_id}/retry` | Re-dispatches a failed or cancelled photogrammetry task. | `202 Accepted`, `400 Bad Request`, `404 Not Found` |

---

## 2. Request & Response Examples

### 2.1. Dispatch Reconstruction Job
`POST /api/v1/photogrammetry/tasks`

#### Request Body:
```json
{
  "survey_id": "c5fa503f-fc6b-413e-b14b-c33752b356af",
  "source_file_id": "957dd749-073c-4644-8b94-d8a75a6e529c",
  "resolution_preset": "HIGH_RES",
  "custom_resolution_cm": 2.5,
  "generate_dsm": true,
  "generate_dtm": true,
  "radiometric_calibration": false,
  "feature_quality": "high",
  "pc_quality": "medium"
}
```

#### Response (`202 Accepted`):
```json
{
  "task_id": "8f3e29c1-4b1a-4d92-913b-e10c714890a2",
  "survey_id": "c5fa503f-fc6b-413e-b14b-c33752b356af",
  "survey_code": "SRV-2026-001",
  "source_file_id": "957dd749-073c-4644-8b94-d8a75a6e529c",
  "source_filename": "DJI_0001.JPG",
  "webodm_task_uuid": null,
  "resolution_preset": "HIGH_RES",
  "generate_dsm": true,
  "generate_dtm": true,
  "radiometric_calibration": false,
  "options": {
    "resolution_preset": "HIGH_RES",
    "custom_resolution_cm": 2.5,
    "generate_dsm": true,
    "generate_dtm": true,
    "radiometric_calibration": false,
    "feature_quality": "high",
    "pc_quality": "medium"
  },
  "status": "SUBMITTED",
  "progress_percent": 0,
  "current_stage": "Job submitted to queue",
  "error_message": null,
  "retry_count": 0,
  "started_at": "2026-10-14T17:30:00Z",
  "completed_at": null,
  "generated_products_count": 0
}
```

### 2.2. Polling Task Details
`GET /api/v1/photogrammetry/tasks/8f3e29c1-4b1a-4d92-913b-e10c714890a2`

#### Response (`200 OK`):
```json
{
  "task_id": "8f3e29c1-4b1a-4d92-913b-e10c714890a2",
  "survey_id": "c5fa503f-fc6b-413e-b14b-c33752b356af",
  "survey_code": "SRV-2026-001",
  "source_file_id": "957dd749-073c-4644-8b94-d8a75a6e529c",
  "source_filename": "DJI_0001.JPG",
  "webodm_task_uuid": "e819b21a-9812-4f11-b012-7612a81901a2",
  "resolution_preset": "HIGH_RES",
  "generate_dsm": true,
  "generate_dtm": true,
  "radiometric_calibration": false,
  "status": "RUNNING",
  "progress_percent": 68,
  "current_stage": "Dense Point Cloud Matching",
  "error_message": null,
  "retry_count": 0,
  "started_at": "2026-10-14T17:30:00Z",
  "completed_at": null,
  "generated_products_count": 0
}
```

### 2.3. Task Console Logs
`GET /api/v1/photogrammetry/tasks/8f3e29c1-4b1a-4d92-913b-e10c714890a2/logs`

#### Response (`200 OK`):
```json
{
  "task_id": "8f3e29c1-4b1a-4d92-913b-e10c714890a2",
  "logs": [
    {
      "id": 1,
      "task_id": "8f3e29c1-4b1a-4d92-913b-e10c714890a2",
      "log_level": "INFO",
      "message": "Initializing photogrammetry task for survey SRV-2026-001",
      "logged_at": "2026-10-14T17:30:01Z"
    },
    {
      "id": 2,
      "task_id": "8f3e29c1-4b1a-4d92-913b-e10c714890a2",
      "log_level": "INFO",
      "message": "Running OpenSfM feature matching on 142 photos...",
      "logged_at": "2026-10-14T17:30:45Z"
    }
  ],
  "total_lines": 2
}
```
