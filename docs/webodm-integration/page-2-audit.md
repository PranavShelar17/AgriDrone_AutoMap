# AgriDrone AutoMap — Page 2: WebODM Integration & Photogrammetry Workspace Audit
## Document Reference: `docs/webodm-integration/page-2-audit.md`
**Component**: Page 2 — WebODM Photogrammetry Workspace  
**Status**: COMPLETED AUDIT  
**Date**: 2026-10-15  

---

## 1. Executive Summary

This document performs an exhaustive audit of the existing **AgriDrone AutoMap** photogrammetry integration (implemented during Phase 6 and refined through Phases 7–10) in comparison to the complete WebODM Dashboard specification and reference interface.

The WebODM reference interface features:
1. **Projects Overview & Dashboard**: Multi-project tracking, task counters, status badges, timestamps.
2. **Project Management**: "Add Project", rename, description editing, survey/farm association, deletion with safety checks.
3. **Select Images & GCP**: Multi-file drag-and-drop ingestion, file validation, Ground Control Point (GCP) file upload & verification.
4. **Processing Tasks**: Task status lifecycle (`SUBMITTED`, `QUEUED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`), live progress bars, processing stage text, console logs, cancellation, and retry.
5. **Processing Presets & Options**: Quality presets ("Fast Orthophoto", "Precision", "Multispectral", "Custom GSD"), DSM/DTM generation toggles, radiometric calibration, mesh/point-cloud parameters.
6. **View Map**: In-app interactive MapLibre map viewer displaying generated orthomosaics, surface elevation models, boundary overlays, and layer controls.
7. **Processing Nodes**: NodeODM / WebODM processing cluster status, active vs. total node counts, memory utilization, task queue depth.
8. **Diagnostic Tools**: Live health probes, connection latency, API response telemetry, task failure forensics, and troubleshooting actions.
9. **Lightning**: Investigation of WebODM Lightning (cloud compute subscription network) and clear architectural positioning.
10. **GCP Interface**: Ground Control Point file format parser, EPSG coordinate reference validation, coordinate table viewer.
11. **Administration**: Connection parameters, timeout settings, preset configurations, and audit logging (restricted to administrators).
12. **Search, Sorting & Filtering**: Multi-criteria search by project name, survey code, status, and creation date.

---

## 2. Existing Implementation Audit

### 2.1 Backend Models (`backend/app/models/`)
- **`PhotogrammetryTask` (`app/models/task.py`)**:
  - Implements: `id`, `survey_id`, `source_file_id`, `webodm_task_uuid`, `resolution_preset`, `generate_dsm`, `generate_dtm`, `radiometric_calibration`, `options`, `status`, `progress_percent`, `current_stage`, `error_message`, `retry_count`, `started_at`, `completed_at`.
  - Relationship to `Survey`, `SurveyFile`, `TaskLog`, and `MapProduct`.
- **`TaskLog` (`app/models/task.py`)**:
  - Implements: `id`, `task_id`, `log_level`, `message`, `logged_at`.
- **Audit Gap Identified**:
  - Existing tasks attach directly to `Survey` without a standalone `PhotogrammetryProject` model.
  - Adding a `PhotogrammetryProject` model (`app/models/project.py`) enables explicit multi-project workflows, custom project naming/descriptions, farm/field/survey associations, and direct mapping to WebODM's `/api/projects/` container hierarchy while preserving 100% backwards compatibility with existing tasks.

### 2.2 WebODM Service Client (`backend/app/services/webodm.py`)
- **Current Capabilities**:
  - JWT Token Authentication (`/api/token-auth/`).
  - Cluster health probe with fallback to direct NodeODM (`/info`) or full WebODM (`/api/projects/` and `/api/cluster/nodes/`).
  - Option payload generator with validation (`orthophoto-resolution`, `dsm`, `dtm`, `feature-quality`, `pc-quality`, `radiometric-calibration`).
  - Task creation with multipart image binary upload (`POST /api/projects/{id}/tasks/`).
  - Task polling (`GET /api/projects/{id}/tasks/{uuid}/`), status translation, progress percentage extraction.
  - Task console log retrieval (`GET /api/projects/{id}/tasks/{uuid}/output/`).
  - Task cancellation (`POST /api/projects/{id}/tasks/{uuid}/cancel/`).
  - Artifact download (`GET /api/projects/{id}/tasks/{uuid}/download/{asset}`).
- **Audit Gaps Identified**:
  - Missing project CRUD methods: `list_projects()`, `create_project()`, `update_project()`, `delete_project()`.
  - Missing GCP file upload handling in `create_task()`: WebODM accepts a `gcp` file part containing coordinate lists.
  - Missing cluster node administration: `list_nodes()`, `get_node_details()`.
  - Missing explicit WebODM diagnostic endpoint handling.

### 2.3 API Endpoints (`backend/app/api/v1/endpoints/photogrammetry.py`)
- **Current Endpoints**:
  - `GET /api/v1/photogrammetry/cluster-status` — Probes WebODM/NodeODM health.
  - `GET /api/v1/photogrammetry/eligible-datasets` — Returns validated drone datasets with eligibility rationale.
  - `POST /api/v1/photogrammetry/tasks` — Dispatches task.
  - `GET /api/v1/photogrammetry/tasks` — Lists tasks.
  - `GET /api/v1/photogrammetry/tasks/{task_id}` — Task detail.
  - `GET /api/v1/photogrammetry/tasks/{task_id}/logs` — Console logs.
  - `GET /api/v1/photogrammetry/tasks/{task_id}/artifacts` — Output artifacts.
  - `POST /api/v1/photogrammetry/tasks/{task_id}/cancel` — Cancels task.
  - `POST /api/v1/photogrammetry/tasks/{task_id}/retry` — Retries task.
- **Audit Gaps Identified**:
  - Missing Project management endpoints:
    - `GET /api/v1/photogrammetry/projects` (list projects with task counts, status summaries, search & sorting)
    - `POST /api/v1/photogrammetry/projects` (create project linked to farm/survey)
    - `GET /api/v1/photogrammetry/projects/{project_id}` (get project detail)
    - `PATCH /api/v1/photogrammetry/projects/{project_id}` (update project)
    - `DELETE /api/v1/photogrammetry/projects/{project_id}` (delete project)
  - Missing GCP validation endpoint:
    - `POST /api/v1/photogrammetry/gcp/validate` (parse and validate GCP file structure, coordinate system, and point counts)
  - Missing Processing Nodes endpoint:
    - `GET /api/v1/photogrammetry/nodes` (list active processing nodes, RAM, workload)
  - Missing Diagnostic endpoint:
    - `GET /api/v1/photogrammetry/diagnostics` (full system diagnostics including WebODM, storage, database, Redis, worker)
  - Missing Admin Settings endpoint:
    - `GET /api/v1/photogrammetry/admin/config` (inspect active photogrammetry engine configuration)

### 2.4 Frontend Page 2 (`frontend/app/admin/photogrammetry/page.tsx`)
- **Current State**:
  - Single-view photogrammetry dispatch dashboard.
  - Basic survey dropdown, eligibility cards, preset radio buttons, active task progress bar, and raw log viewer.
- **Audit Gaps Identified**:
  - Lacks dedicated tabs/views for the full WebODM workspace:
    1. **Projects Dashboard**: Project cards/table, status badges, task counters, "Add Project" modal.
    2. **Image & GCP Ingestion**: Multi-file dropzone, image file checklist, GCP upload with format detection.
    3. **Tasks & Processing**: Filterable task table, stage indicator, progress, live logs terminal, cancellation/retry.
    4. **Processing Presets**: Visual preset selector (Fast, High-Res, Multispectral, Custom) with explanations.
    5. **Map Preview & Outputs**: Integrated MapLibre map viewer for orthophotos and DSM directly on Page 2.
    6. **Processing Nodes**: Node cluster metrics, queue status, memory bars.
    7. **Diagnostics**: Real-time diagnostic cards, ping/connectivity test, troubleshooting guidelines.
    8. **Administration**: Engine settings, preset management, audit logs.
  - Title and styling should align with agricultural technology design system:
    - Title: **WebODM Photogrammetry Workspace**
    - Subtitle: *“Manage drone surveys, configure photogrammetry, monitor processing, and explore generated map products.”*

---

## 3. WebODM Feature Matrix & Mapping

| WebODM Screenshot Feature | AgriDrone Implementation Status | Action for Page 2 |
| :--- | :--- | :--- |
| **Dashboard** | Partially Supported | Upgrade to full Projects & Tasks unified dashboard with metrics |
| **Add Project** | Missing in API & UI | Implement `PhotogrammetryProject` model, API CRUD, and Add Project modal |
| **Edit / Delete Project** | Missing in API & UI | Implement edit/delete endpoints with safety confirmations |
| **Select Images and GCP** | Basic file selector | Implement drag-and-drop multi-image uploader + GCP parser/validator |
| **Task Lists & Status** | Implemented | Enhance with search, multi-column sorting, stage tags, and action buttons |
| **Processing Presets** | Hardcoded options | Implement structured presets (Fast, Precision, Multispectral, Custom) |
| **View Map** | Handled in Phase 8 | Integrate interactive MapLibre viewer directly inside Page 2 modal/panel |
| **Processing Nodes** | Cluster probe only | Implement node listing endpoint and dedicated Processing Nodes tab |
| **Diagnostic** | Cluster probe only | Implement dedicated Diagnostic tab with full telemetry and corrective runbook |
| **GCP Interface** | Unsupported | Implement GCP file upload, coordinate parsing, and validation preview |
| **Lightning** | External commercial cloud | Document purpose honestly; clearly explain relation to local NodeODM |
| **Administration** | Missing in photogrammetry | Implement admin configuration panel with role verification |
| **Search & Sorting** | Basic client filter | Implement server-side multi-field search, status filtering, and sorting |

---

## 4. Architectural Boundaries & Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   Next.js WebODM Photogrammetry Workspace                  │
│                     (Title: WebODM Photogrammetry Workspace)                │
│                                                                             │
│  [Projects]  [Ingest Images & GCP]  [Tasks]  [Presets]  [Nodes]  [Diag]  [Admin]
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTP / Bearer Auth
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Web Backend (Port 8005)                     │
│  /api/v1/photogrammetry/projects         /api/v1/photogrammetry/tasks       │
│  /api/v1/photogrammetry/gcp/validate     /api/v1/photogrammetry/nodes       │
│  /api/v1/photogrammetry/diagnostics      /api/v1/photogrammetry/admin/config│
└──────────────┬───────────────────────┬──────────────────────┬───────────────┘
               │                       │                      │
     PostGIS / SQL Queries    Celery / Redis Jobs    HTTP / JSON Protocol
               │                       │                      │
               ▼                       ▼                      ▼
┌──────────────────────────┐ ┌───────────────────┐ ┌──────────────────────────┐
│   PostgreSQL + PostGIS   │ │   Celery Worker   │ │     WebODM / NodeODM     │
│   - photogrammetry_proj. │ │   (Redis Queue)   │ │   (Port 3001 or Cloud)   │
│   - photogrammetry_tasks │ └─────────┬─────────┘ └──────────────────────────┘
│   - task_logs            │           │ Download Artifacts
│   - map_products         │           ▼
└──────────────────────────┘ ┌────────────────────────────────────────────────┐
                             │       Azure Blob Storage / Local Storage       │
                             │       raw-surveys / orthomosaics / dsm         │
                             └────────────────────────────────────────────────┘
```

---

## 5. Implementation Roadmap for Page 2

1. **Step 1 — Data Model Enhancement**:
   - Create `PhotogrammetryProject` SQLAlchemy model in `backend/app/models/project.py`.
   - Add `project_id` foreign key to `PhotogrammetryTask` (nullable for backwards compatibility).
   - Export new model in `backend/app/models/__init__.py`.
   - Create and run database migration script.

2. **Step 2 — WebODM Service Client Extension**:
   - Extend `WebODMService` in `backend/app/services/webodm.py` with:
     - Project CRUD (`list_projects`, `create_project`, `update_project`, `delete_project`).
     - Node listing (`list_cluster_nodes`).
     - GCP file attachment in multipart task dispatch.
     - Diagnostic checks (`run_full_diagnostics`).

3. **Step 3 — Backend API Endpoints (`photogrammetry.py`)**:
   - Project endpoints: `GET /projects`, `POST /projects`, `GET /projects/{id}`, `PATCH /projects/{id}`, `DELETE /projects/{id}`.
   - GCP validation: `POST /gcp/validate`.
   - Cluster nodes: `GET /nodes`.
   - Diagnostic tools: `GET /diagnostics`.
   - Administrative settings: `GET /admin/config`.
   - Enforce tenant isolation for Farmers vs Admins across all project and task queries.

4. **Step 4 — Frontend TypeScript Types & API Client**:
   - Update `frontend/lib/api.ts` with new project, node, GCP, and diagnostic schemas and methods.

5. **Step 5 — Complete Redesign of Page 2 UI**:
   - Update `frontend/app/admin/photogrammetry/page.tsx`:
     - Professional header: **WebODM Photogrammetry Workspace**
     - Subtitle: *"Manage drone surveys, configure photogrammetry, monitor processing, and explore generated map products."*
     - Tabbed navigation:
       - **Projects Dashboard** (cards, stats, add/edit project modal)
       - **Upload Images & GCP** (multi-file dropzone, GCP file format preview, validation)
       - **Tasks & Monitor** (real-time progress, logs, cancel/retry)
       - **Presets & Options** (interactive preset cards, custom parameters)
       - **Map Preview** (embedded MapLibre viewer for orthophoto & elevation)
       - **Processing Nodes** (cluster node health, queue depth, RAM)
       - **Diagnostics** (connectivity ping, system checks, failure runbook)
       - **Administration** (engine configuration, node management, audit trail)

6. **Step 6 — Comprehensive Documentation Suite**:
   - Write all 9 remaining documentation files in `docs/webodm-integration/`.

7. **Step 7 — Automated Tests**:
   - Unit and integration tests covering project management, GCP parsing, task operations, tenant authorization, and node inspection.
