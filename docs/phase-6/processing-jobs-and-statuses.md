# AgriDrone AutoMap — Processing Jobs & Lifecycle State Machine
## Document Reference: `docs/phase-6/processing-jobs-and-statuses.md`
**Phase**: Phase 6 — WebODM / OpenDroneMap Integration & Drone Photogrammetry Processing  
**Status**: APPROVED STATE SPECIFICATION  
**Version**: 1.0.0  

---

## 1. Photogrammetry Task Finite State Machine

All photogrammetry tasks adhere to a strict, auditable lifecycle:

```
               ┌─────────────┐
               │  SUBMITTED  │
               └──────┬──────┘
                      │
                      ▼
               ┌─────────────┐
               │  PREPARING  │
               └──────┬──────┘
                      │
                      ▼
               ┌─────────────┐
               │  UPLOADING  │
               └──────┬──────┘
                      │
                      ▼
               ┌─────────────┐
        ┌─────>│   RUNNING   │<────┐ (Heartbeat & Log sync)
        │      └──────┬──────┘     │
        │             │            │
 (Retry │             ├──────> CANCEL_REQUESTED ────> CANCELLED
  safe) │             │
        │             ├──────> FAILED
        │             │
        │             ▼
        │      ┌─────────────┐
        │      │ FINALIZING  │ (Downloading & registering GeoTIFF deliverables)
        │      └──────┬──────┘
        │             │
        │             ▼
        │      ┌─────────────┐
        └──────┤  COMPLETED  │ (Verified output deliverables stored)
               └─────────────┘
```

---

## 2. State Definitions & WebODM Mapping

| AgriDrone State | Progress % | Stage Description | WebODM Mapping |
| :--- | :--- | :--- | :--- |
| `SUBMITTED` | 0% | Job queued in database, dispatched to worker. | Local queue |
| `PREPARING` | 5% | Reading source files from storage, unpacking archives. | Pre-flight |
| `UPLOADING` | 15% | Streaming photo binaries to WebODM cluster. | HTTP Multipart upload |
| `RUNNING` | 20% – 90% | OpenSfM feature matching, bundle adjustment, OpenMVS point cloud densification. | Status Code 20 (`RUNNING`) |
| `FINALIZING` | 95% | Downloading GeoTIFF rasters, extracting CRS/band metadata, registering `map_products`. | Status Code 40 (`COMPLETED`) |
| `COMPLETED` | 100% | All deliverables verified in storage and database. Parent survey marked `COMPLETED`. | Status Code 40 (`COMPLETED`) |
| `CANCEL_REQUESTED`| Current % | User requested cancellation; cancel signal sent to WebODM. | Active cancel in-flight |
| `CANCELLED` | Current % | Execution aborted. Parent survey returned to `DRAFT`. | Status Code 50 (`CANCELED`) |
| `FAILED` | Current % | Unrecoverable error (OOM, non-georeferenced imagery, connection loss). Stack trace logged. | Status Code 30 (`FAILED`) |

---

## 3. Worker Reconnection & State Recovery

1. **Worker Crash Recovery**: If a worker process terminates during photogrammetry execution, the task remains marked with its last progress and timestamp. On application startup or task polling, the task reconciles against WebODM using the stored `webodm_task_uuid`.
2. **Safe Retries**: Tasks in `FAILED` or `CANCELLED` states can be re-run via `POST /api/v1/photogrammetry/tasks/{task_id}/retry`. Retrying increments `retry_count`, resets progress to 0%, clears prior errors, and initiates a clean reconstruction run without creating duplicate database entities.
