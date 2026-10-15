# AgriDrone AutoMap — Photogrammetry Processing Workflow
## Document Reference: `docs/phase-6/photogrammetry-workflow.md`
**Phase**: Phase 6 — WebODM / OpenDroneMap Integration & Drone Photogrammetry Processing  
**Status**: APPROVED WORKFLOW BLUEPRINT  
**Version**: 1.0.0  

---

## 1. End-to-End Processing Workflow

The photogrammetry workflow progresses through 16 structured, auditable stages:

```
[1. Select Farm & Survey]
           │
           ▼
[2. Evaluate Dataset Eligibility (JPEG/TIFF raw)]
           │
           ▼
[3. Configure Presets (GSD, DSM, DTM, Quality)]
           │
           ▼
[4. Submit Task via POST /api/v1/photogrammetry/tasks]
           │
           ├───> Check Concurrency (409 Conflict if active task exists)
           ├───> Create photogrammetry_tasks record (Status: 'SUBMITTED')
           └───> Enqueue Celery Worker (Queue: photogrammetry)
                     │
                     ▼
           [5. Worker State: PREPARING]
           │   ├── Download files from storage (Azure or local fallback)
           │   └── Unpack ZIP archive or stage raw photos
           │
           ▼
           [6. Cluster Pre-Flight Check]
           │   └── Probe WebODM API connectivity (Fail fast with clear error if offline)
           │
           ▼
           [7. Worker State: UPLOADING]
           │   └── Stream multipart/form-data image payloads to WebODM
           │
           ▼
           [8. WebODM Task Creation]
           │   ├── Acquire webodm_task_uuid
           │   └── Update task status to 'RUNNING'
           │
           ▼
           [9. Status & Console Log Polling Loop]
           │   ├── Poll WebODM every 10s for progress percentage
           │   ├── Fetch new stdout lines and insert into task_logs
           │   └── Monitor for CANCEL_REQUESTED interrupts
           │
           ▼
           [10. Worker State: FINALIZING]
           │   ├── Download orthophoto.tif, dsm.tif, dtm.tif
           │   ├── Upload GeoTIFFs to storage (orthomosaics/{survey_id}/)
           │   ├── Inspect raster CRS (EPSG), band count, and resolution
           │   └── Register deliverables in map_products table
           │
           ▼
           [11. Worker State: COMPLETED]
           │   ├── Update task status to 'COMPLETED' (progress: 100%)
           │   └── Update parent survey status to 'COMPLETED'
           │
           ▼
[12. Deliverables Ready for Phase 7 (Vegetation Algorithms)]
```

---

## 2. Real-Time Status Synchronization & Logging

At each step, execution events are recorded immutably in the PostgreSQL `task_logs` table:
- `id`: Auto-incrementing BigInteger
- `task_id`: UUID foreign key to `photogrammetry_tasks.id`
- `log_level`: `INFO`, `WARNING`, or `ERROR`
- `message`: Diagnostic log text
- `logged_at`: UTC timestamp

The frontend terminal polls `/api/v1/photogrammetry/tasks/{task_id}/logs` every 3 seconds while active, appending incoming log lines to the monospace terminal with auto-scroll.

---

## 3. Failure & Interruption Recovery

If any stage fails:
1. **Network Timeout / Node Failure**: The task is marked `FAILED` with a detailed `error_message` stored in the database.
2. **Original Imagery Protected**: Original source photographs in `raw-surveys` are **never deleted or modified** upon task failure.
3. **Safe Retries**: The administrator can click "Retry Task" on the interface, which increments `retry_count`, resets status to `SUBMITTED`, and safely re-dispatches the job without creating orphaned records.
