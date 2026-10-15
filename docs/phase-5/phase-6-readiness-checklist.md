# AgriDrone AutoMap — Phase 6 Readiness Checklist
## Document Reference: `docs/phase-6/phase-6-readiness-checklist.md`
**Target Phase**: Phase 6 — WebODM Photogrammetry Processing Engine  
**Status**: READINESS VERIFICATION COMPLETE  
**Version**: 1.0.0  

---

## 1. Prerequisites Met in Phase 5

| Prerequisite | Status | Verification Reference |
| :--- | :--- | :--- |
| **Survey Mission Hierarchy** | ✅ READY | Can create farms, field parcels, and flight surveys via API and UI. |
| **Drone Image Ingestion** | ✅ READY | Raw photo batches (`RAW_IMAGE`) validated, stored, and marked with MD5/SHA256 checksums in `survey_files`. |
| **Metadata & GPS Extraction** | ✅ READY | Pillow EXIF engine extracts flight capture dates, camera models, and GPS coordinates for georeferencing. |
| **Workflow Route Classification** | ✅ READY | Datasets automatically tagged as `WEBODM_PHOTOGRAMMETRY` vs `DIRECT_ALGORITHM_GIS`. |
| **Database Schema for WebODM** | ✅ READY | `photogrammetry_tasks` and `task_logs` tables created and indexed in migration `001_initial_core_schema`. |
| **Docker Compose Environment** | ✅ READY | Database (PostGIS on 5434) and Redis (on 6380) running and healthy. Dedicated WebODM integration port reserved on 3001. |

---

## 2. Phase 6 Scope Hand-Off

When the user initiates **Phase 6**, the system will implement:
1. **WebODM Local Cluster Setup**: Docker compose integration for WebODM Node and Worker instances.
2. **WebODM API Client**: Python service in `backend/app/services/webodm.py` authenticating with WebODM REST API.
3. **Task Dispatcher & Celery Worker**: Asynchronous queue dispatching raw survey photo batches from object storage to WebODM nodes.
4. **Reconstruction Progress Polling**: Real-time polling of processing stages (feature matching, point cloud densification, DEM generation, orthophoto stitching).
5. **Output Ingestion**: Automatic download and COG conversion of completed orthomosaics and DSMs into Azure / local storage and the `map_products` database table.

> [!IMPORTANT]
> Do NOT start Phase 6 automatically. Wait for explicit user review and approval of Phase 5 deliverables.
