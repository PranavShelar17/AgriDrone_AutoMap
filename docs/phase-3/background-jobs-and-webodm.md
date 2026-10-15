# AgriDrone AutoMap — Background Jobs & WebODM Integration
## Document Reference: `docs/phase-3/background-jobs-and-webodm.md`
**Phase**: Phase 3 — System Architecture, Technical Validation & Implementation Blueprint  
**Status**: APPROVED ARCHITECTURE BLUEPRINT  
**Version**: 1.0.0  

---

## 1. Asynchronous Architecture Rationale

Photogrammetry (OpenDroneMap/WebODM) and raster calculations (GDAL/Rasterio/NumPy) are compute- and memory-intensive operations that can take anywhere from **30 seconds** (for simple index computations) to **several hours** (for dense multi-hundred-photo 3D reconstructions).

To maintain high availability and sub-second response times for the FastAPI web server, **all heavy processing is executed asynchronously** through **Celery 5.3+** distributed workers backed by **Redis 7+**.

```
[FastAPI Endpoint]
       │
       ▼ (Validates request, writes 'QUEUED' record to PostgreSQL)
[Celery Task Dispatcher]
       │
       ▼ (Pushes JSON message)
[Redis Message Broker]
       │
       ├──> [Worker Queue: photogrammetry] ──> Dispatches & polls WebODM Cluster
       ├──> [Worker Queue: raster_compute]  ──> Executes GDAL/NumPy Index Math
       └──> [Worker Queue: reports]         ──> Compiles ReportLab PDF Documents
```

---

## 2. WebODM Photogrammetry Integration Architecture

### 2.1. WebODM Service Boundaries
FastAPI and Celery interact with WebODM via its standard REST API (`/api/projects/` and `/api/projects/{id}/tasks/`):
- WebODM runs in an isolated network segment (or dedicated Docker container).
- Celery workers act as the bridge between AgriDrone AutoMap and the WebODM cluster.
- **Survey-to-Task Binding**: Each photogrammetric reconstruction maps 1-to-1 with a `photogrammetry_tasks` record in PostgreSQL storing the `webodm_task_uuid`.

### 2.2. Processing Configuration Parameters
When dispatching a task to WebODM, the Celery worker passes standard photogrammetric flags:
```json
{
  "name": "Survey_SRV-2026-001_Reconstruction",
  "options": [
    {"name": "auto-boundary", "value": true},
    {"name": "dsm", "value": true},
    {"name": "dtm", "value": true},
    {"name": "orthophoto-resolution", "value": 2.5},
    {"name": "feature-quality", "value": "high"},
    {"name": "pc-quality", "value": "medium"},
    {"name": "radiometric-calibration", "value": "none"},
    {"name": "max-concurrency", "value": 4}
  ]
}
```

### 2.3. Task Polling & Status Synchronization Loop
1. The worker submits the photo archive (or pre-signed Azure SAS download URLs) to WebODM.
2. WebODM acknowledges task creation and returns a task UUID.
3. The Celery polling task (`poll_webodm_task_status`) executes periodically (every 10 seconds):
   - Queries `GET /api/projects/{proj_id}/tasks/{task_uuid}/`
   - Extracts current stage (`"Feature Matching"`, `"Point Cloud Densification"`, `"Orthophoto Generation"`) and percentage.
   - Appends new console log output to the `task_logs` table.
   - Updates `photogrammetry_tasks.progress_percent` in PostgreSQL.
4. **Output Discovery & Registration**:
   - Upon receiving status `COMPLETED` from WebODM, the worker downloads `orthophoto.tif` and `dsm.tif`.
   - The worker runs GDAL to tile the raster into a Cloud-Optimized GeoTIFF (COG) with internal overviews.
   - The COG is uploaded to Azure Blob Storage (`orthomosaics/{survey_id}/orthophoto_cog_{task_id}.tif`).
   - A new `map_products` record is inserted with CRS, resolution, and extent geometry.
   - The photogrammetry task is marked `COMPLETED`.

---

## 3. Celery Worker Task Inventory

| Task Name | Queue | Estimated Duration | Retry Policy | Timeout |
| :--- | :--- | :--- | :--- | :--- |
| `tasks_ingest.validate_raster_file` | `ingest` | 5 – 30 seconds | Max 2 retries, 5s backoff | 120s |
| `tasks_webodm.dispatch_reconstruction` | `photogrammetry` | 10 – 30 seconds | Max 3 retries, 10s backoff | 300s |
| `tasks_webodm.poll_reconstruction_status` | `photogrammetry` | 15 mins – 3 hours | Polling loop with heartbeat | 4 hours |
| `tasks_raster.compute_vegetation_index` | `raster_compute` | 30s – 5 minutes | Max 2 retries, 10s backoff | 15 mins |
| `tasks_raster.convert_to_cog` | `raster_compute` | 1 – 10 minutes | Max 2 retries, 10s backoff | 30 mins |
| `tasks_report.generate_pdf_report` | `reports` | 10 – 60 seconds | Max 3 retries, 5s backoff | 5 mins |
| `tasks_cleanup.prune_scratch_volume` | `maintenance` | 1 – 5 minutes | Daily cron, no retry | 15 mins |

---

## 4. Job State Machines & Lifecycle

To ensure strict auditable state tracking, all background processing adheres to a finite state machine enforced by PostgreSQL check constraints:

```
                  ┌──────────────┐
                  │  SUBMITTED   │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
                  │ DISPATCHING  │
                  └──────┬───────┘
                         │
                         ▼
                  ┌──────────────┐
           ┌─────►│   RUNNING    │◄────┐ (Heartbeat updates)
           │      └──────┬───────┘     │
           │             │             │
(Retry on timeout)       ├───► FAILED ─┘
           │             │
           │             ▼
           │      ┌──────────────┐
           └──────┤  COMPLETED   │ (Requires verified Azure COG asset)
                  └──────────────┘
```

### State Definitions:
1. **`SUBMITTED` / `QUEUED`**: Task registered in PostgreSQL and pushed to Redis.
2. **`DISPATCHING`**: Worker has claimed the message and is communicating with external service (Azure/WebODM).
3. **`RUNNING`**: WebODM or GDAL computation actively executing.
4. **`COMPLETED`**: Processing finished successfully, output verified on Azure Blob Storage, and registered in `map_products`.
5. **`FAILED`**: Unrecoverable error encountered (e.g. non-georeferenced imagery, memory exhaustion, invalid band configuration). Detailed stack trace stored in database.
6. **`CANCELLED`**: Explicitly aborted by administrator before completion.

---

## 5. Resilience, Failure Handling & Resource Isolation

1. **Worker Isolation via Separate Docker Containers**:
   - Photogrammetry polling and GDAL raster math run in dedicated worker containers to prevent heavy GDAL C-library memory allocations from crashing the FastAPI web process.
2. **Dead-Letter Queue (DLQ) & Poison Message Mitigation**:
   - Tasks that fail more than their designated maximum retries are routed to a Redis dead-letter queue (`celery_failed_tasks`) and flagged in the database with `status = 'FAILED'`, triggering an administrative alert.
3. **Graceful Worker Shutdown**:
   - Celery workers handle `SIGTERM` signals by waiting up to 60 seconds for active disk flushes before releasing task locks.
