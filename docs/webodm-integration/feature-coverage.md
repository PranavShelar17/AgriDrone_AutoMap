# Feature Coverage Matrix — WebODM Integration & Page 2

This document compares each visual and operational capability shown in the reference WebODM Dashboard against the AgriDrone AutoMap Page 2 implementation.

| WebODM Dashboard Feature | Implementation Status | AgriDrone AutoMap Component | Implementation Details |
| :--- | :--- | :--- | :--- |
| **Dashboard** | **Implemented** | Tab 1: `Projects Dashboard` | Real-time project overview, search bar, sort selector, task counters, latest status indicators. |
| **Add Project** | **Implemented** | Modal: `Create Photogrammetry Project` | Validated modal collecting project name, description, farm association, field association, and tags. |
| **Edit / Rename Project**| **Implemented** | API: `PATCH /api/v1/photogrammetry/projects/{id}` | Updates project metadata in PostgreSQL and synchronizes upstream container name. |
| **Delete Project** | **Implemented** | API: `DELETE /api/v1/photogrammetry/projects/{id}` | Confirmed deletion of project container with cascading protection for surveys and tasks. |
| **Select Images and GCP**| **Implemented** | Tab 2: `Select Images & GCP` | Multi-file drag-and-drop raw photo ingestion + surveyor GCP format parser with coordinate preview. |
| **GCP Interface** | **Implemented** | Tab 2: `Ground Control Points` | OpenDroneMap GCP format validation (`+proj=...` header + coordinate rows), point counts, and attachment. |
| **Task Management** | **Implemented** | Tab 3: `Processing Tasks` | Real WebODM lifecycle mapping (`SUBMITTED`, `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`). |
| **Live Progress & Stage**| **Implemented** | Tab 3: Hero Card Progress Bar | Dynamic progress percentage (0–100%) and 4-stage pipeline visualization. |
| **Task Cancellation** | **Implemented** | Action: `Cancel Task` | Calls WebODM cancel endpoint and updates state to `CANCELLED` via Celery worker. |
| **Task Retry** | **Implemented** | Action: `Retry Task` | Re-submits failed or cancelled task with incremented retry count and preserves options. |
| **Terminal / Console Logs**| **Implemented** | Drawer: `ODM Execution Console` | Streaming live logs from `task_logs` table with auto-scroll, log-level highlighting, and timestamps. |
| **Processing Presets** | **Implemented** | Tab 4: `Presets & Options` | 4 agricultural presets: Fast Orthophoto, Precision High-Res, Multispectral Index, Custom GSD. |
| **View Map** | **Implemented** | Tab 5: `View Map & Outputs` | Interactive MapLibre GL JS raster viewer rendering orthophotos, DSMs, and GeoTIFF downloads. |
| **Import** | **Implemented** | Survey / Dataset Association | Ingests existing drone surveys and raw photo archives directly into WebODM tasks. |
| **Processing Nodes** | **Implemented** *(Admin)*| Tab 6: `Processing Nodes` | Cluster worker status, hostname:port, queue depth, available RAM in GB, and heartbeat check. |
| **Diagnostic** | **Implemented** *(Admin)*| Tab 7: `Diagnostics` | End-to-end health probe across WebODM, storage engine, PostgreSQL/PostGIS, and Redis queues. |
| **Administration** | **Implemented** *(Admin)*| Tab 8: `Administration` | WebODM host URL, timeouts, max retries, poll intervals, storage provider, and preset rules. |
| **Lightning** | **Documented & Clarified** | Tab 8: `WebODM Lightning Notice` | Transparent architectural analysis explaining WebODM Lightning is a commercial cloud GPU service; AgriDrone uses on-premise NodeODM. |
| **Search & Sorting** | **Implemented** | Tab 1 Toolbar | Server-side and client-side filtering by name, description, farm, survey, status, and date. |
| **Tenant Isolation (RBAC)**| **Implemented** | Backend Security Middleware | Farmers access only their authorized projects/tasks; administrators manage cluster nodes and diagnostics. |
