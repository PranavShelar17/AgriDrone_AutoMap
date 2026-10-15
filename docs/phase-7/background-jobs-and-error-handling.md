# Background Jobs, Worker Fault Tolerance & Error Handling — Phase 7

## 1. Asynchronous Architecture
Large drone orthomosaics can easily exceed 500 megapixels and 1 GB in uncompressed size. Executing vegetation index calculations synchronously within FastAPI request handlers would tie up web server worker threads, trigger HTTP gateway timeouts (504), and crash browser connections.

Phase 7 executes all raster processing in background workers via **Celery + Redis**, with an automatic in-process daemon threading fallback for lightweight local development.

---

## 2. Worker Lifecycle & Error Handling

```
Job Initialized [QUEUED]
        │
        ├──> Source raster missing? ──> [FAILED] "Source raster file not accessible"
        │
        ├──> Band mapping invalid? ───> [FAILED] "NDRE requires RedEdge (705-745nm)"
        │
        ├──> Corrupt TIFF data? ──────> [FAILED] "Rasterio open failed: corrupt header"
        │
        ├──> 0 valid pixels? ─────────> [FAILED] "All denominators zero or masked"
        │
        ├──> Output COG corrupt? ─────> [FAILED] "Output raster validation failed"
        │
        ├──> Storage upload error? ───> [FAILED] "Blob upload failed"
        │
        └──> All stages verified ─────> [COMPLETED] 100% Progress
```

---

## 3. Worker Crash & Retry Idempotency
- **Worker Crash Recovery**: If a worker process is terminated abruptly (OOM or power failure), unacknowledged tasks are re-queued by Celery or can be manually triggered via `POST /api/v1/algorithms/jobs/{job_id}/retry`.
- **Idempotency**: Retrying a job updates the existing record with an incremented `retry_count`, overwriting any partial intermediate files cleanly without creating duplicate orphaned output rows in `map_products`.
- **Temporary File Hygiene**: Intermediate raster files are written to isolated temporary directories (`tempfile.mkdtemp(prefix="agridrone_batch_")`) and strictly purged in a `finally` block regardless of success or exception.
