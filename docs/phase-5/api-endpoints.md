# AgriDrone AutoMap — Phase 5 API Endpoints Specification
## Document Reference: `docs/phase-5/api-endpoints.md`
**Phase**: Phase 5 — Admin Dashboard, Farm/Survey Management & Drone Image Ingestion  
**Status**: APPROVED API CONTRACT  
**Version**: 1.0.0  

---

## 1. Endpoint Index

Base URL prefix: `/api/v1`

| Category | Method | Path | Summary | Auth / Scope |
| :--- | :--- | :--- | :--- | :--- |
| **Dashboard** | `GET` | `/dashboard/stats` | Real DB metrics & recent activity ledger | Admin / Dev |
| **Farms** | `GET` | `/farms` | List registered farms (paginated + search) | Admin / Dev |
| **Farms** | `POST` | `/farms` | Register new farm (with optional polygon) | Admin / Dev |
| **Farms** | `GET` | `/farms/{farm_id}` | Get farm detail & child fields | Admin / Dev |
| **Farms** | `PUT` | `/farms/{farm_id}` | Update farm metadata & boundary | Admin / Dev |
| **Farms** | `DELETE`| `/farms/{farm_id}` | Delete farm & cascade records | Admin / Dev |
| **Farms** | `GET` | `/farms/{farm_id}/fields` | List fields belonging to a farm | Admin / Dev |
| **Farms** | `POST` | `/farms/{farm_id}/fields` | Create a new field parcel under farm | Admin / Dev |
| **Fields** | `GET` | `/fields/{field_id}` | Get field parcel details | Admin / Dev |
| **Fields** | `PUT` | `/fields/{field_id}` | Update field parcel metadata | Admin / Dev |
| **Fields** | `DELETE`| `/fields/{field_id}` | Delete field parcel & cascade surveys | Admin / Dev |
| **Surveys** | `GET` | `/surveys` | List surveys with filtering by field/status | Admin / Dev |
| **Surveys** | `POST` | `/surveys` | Create survey flight mission | Admin / Dev |
| **Surveys** | `GET` | `/surveys/{survey_id}` | Get survey details & associated files | Admin / Dev |
| **Surveys** | `PUT` | `/surveys/{survey_id}` | Update survey parameters & notes | Admin / Dev |
| **Surveys** | `DELETE`| `/surveys/{survey_id}` | Delete / cancel survey mission | Admin / Dev |
| **Ingestion** | `POST` | `/ingestion/upload/{survey_id}`| Upload and validate drone image / GeoTIFF | Admin / Dev |
| **Ingestion** | `GET` | `/ingestion/surveys/{survey_id}/files`| List uploaded files for survey | Admin / Dev |
| **Ingestion** | `DELETE`| `/ingestion/files/{file_id}` | Delete file from storage and database | Admin / Dev |
| **Ingestion** | `GET` | `/ingestion/download/{container}/{blob_path}`| Dev-only direct stream download | Admin / Dev |
| **Health** | `GET` | `/health` | Liveness check | Public |
| **Health** | `GET` | `/health/readiness` | Readiness check (PostGIS & Redis connectivity) | Public |

---

## 2. Request & Response Payloads

### 2.1. Ingestion Upload Request
`POST /api/v1/ingestion/upload/{survey_id}`  
Content-Type: `multipart/form-data`

**Form Parameters:**
- `file`: Binary file stream (`.jpg`, `.jpeg`, `.tif`, `.tiff`, `.zip`).
- `workflow_mode`: String enum (`raw_photos` or `geotiff`).

**Sample 201 Created Response:**
```json
{
  "file_id": "0336e9e8-c602-49a7-8682-47873ebc65b9",
  "survey_id": "a28fbd5b-ce89-4d35-b7d8-64a2be5792d7",
  "original_filename": "DJI_0001.JPG",
  "file_type": "RAW_IMAGE",
  "file_size_bytes": 14298100,
  "mime_type": "image/jpeg",
  "blob_uri": "local://raw-surveys/a28fbd5b-ce89-4d35-b7d8-64a2be5792d7/DJI_0001.JPG",
  "md5_checksum": "e3b0c44298fc1c149afbf4c8996fb924",
  "ingestion_status": "VALIDATED",
  "workflow_route": "WEBODM_PHOTOGRAMMETRY",
  "validation_metadata": {
    "width": 5280,
    "height": 3956,
    "bands": 3,
    "color_mode": "RGB",
    "has_gps": true,
    "gps_latitude": 18.1524102,
    "gps_longitude": 74.5841025,
    "gps_altitude_m": 82.4,
    "camera_make": "DJI",
    "camera_model": "FC3588",
    "capture_time": "2026:10:14 10:15:32",
    "workflow_route": "WEBODM_PHOTOGRAMMETRY",
    "storage_provider": "local_dev",
    "validation_errors": []
  },
  "validation_errors": [],
  "created_at": "2026-10-14T10:22:49.385466Z"
}
```

### 2.2. Dashboard Stats Response
`GET /api/v1/dashboard/stats`  
Sample Response:
```json
{
  "total_farms": 4,
  "total_fields": 4,
  "total_surveys": 2,
  "total_datasets": 4,
  "datasets_awaiting_validation": 0,
  "datasets_validated": 2,
  "datasets_rejected": 2,
  "storage_provider": "local_dev",
  "recent_surveys": [ ... ],
  "recent_uploads": [ ... ],
  "recent_failures": [ ... ]
}
```
