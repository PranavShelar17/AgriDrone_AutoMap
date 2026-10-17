# WebODM Integration Implementation Plan

This document formalizes the phased execution roadmap for integrating WebODM 3.3.1 capabilities into the existing AgriDrone AutoMap platform across 17 structured implementation steps.

---

## Phased Roadmap & Milestones

### Phase 1: Exploration, Codebase Audits & Architecture (Steps 1–5)
- [x] **Step 1: Inspect Uploaded WebODM Source Code**
  - Audited `WebODM-master.zip` (version 3.3.1).
  - Analyzed Django routes, models (`Project`, `Task`, `ProcessingNode`), Celery tasks, Tiler, and GCP parser.
- [x] **Step 2: Inspect Existing AgriDrone AutoMap Repository**
  - Audited Next.js App Router, FastAPI backend, PostGIS models, Celery/Redis tasks, and MapLibre viewers.
- [x] **Step 3: Produce Feature Inventory & Compatibility Analysis**
  - Completed feature inventory across Groups A through O (`docs/webodm-integration/feature-inventory.md`).
- [x] **Step 4: Review License, Trademark & Integration Boundaries**
  - Verified AGPL-3.0 compliance. Established API-only headless boundary to preserve independent licensing.
- [x] **Step 5: Verify Configured WebODM Version & API Connectivity**
  - Verified default environment variables (`WEBODM_API_URL=http://localhost:3001`, JWT authentication).

---

### Phase 2: Central API & Workflow Hardening (Steps 6–9)
- [x] **Step 6: Central WebODM API Integration Layer**
  - Audited `backend/app/services/webodm.py` (`WebODMService` class).
  - Enhanced error handling for connection timeouts, expired tokens, and cluster probe failures.
- [x] **Step 7: Project & Task Management Workflows**
  - Verified CRUD endpoints in `backend/app/api/v1/endpoints/photogrammetry.py`.
  - Enforced project-to-farm-to-survey relationships in PostgreSQL.
- [x] **Step 8: Image Ingestion, GCP & Processing Configuration**
  - Built GCP parser supporting Proj4 / EPSG headers and minimum 3-point validation.
  - Implemented agricultural presets (`FAST`, `HIGH_RES`, `MULTISPECTRAL`, `CUSTOM`).
- [x] **Step 9: Task Status, Diagnostics & Supported Actions**
  - Integrated asynchronous polling via Celery (`trigger_photogrammetry_task`).
  - Implemented cancel (`/tasks/{id}/cancel`), retry (`/tasks/{id}/retry`), and sequential log inspection.

---

### Phase 3: Deliverables, Map Serving & 3D Visualization (Steps 10–12)
- [x] **Step 10: Map, Raster, Export & Download Workflows**
  - Implement raster tile proxy endpoints (`/tasks/{task_id}/tiles/{tile_type}/{z}/{x}/{y}.png`).
  - Expose bounds (`/tasks/{task_id}/tiles/{tile_type}/bounds`) and TileJSON.
  - Wire authorized binary artifact downloads (`all.zip`, `orthophoto.tif`, `dsm.tif`, `report.pdf`).
- [x] **Step 11: 3D Models, Point Cloud & Media Integration**
  - Expose textured 3D model metadata (`textured_model.glb`).
  - Wire point cloud stats (`georeferenced_model.laz`).
  - Integrate interactive 3D WebGL preview and point cloud download controls.
- [x] **Step 12: Processing Node Telemetry & Admin Configuration**
  - Expose cluster node capacity, queue count, and memory metrics to authorized administrators.
  - Expose dynamic NodeODM options schema for advanced tuning.

---

### Phase 4: Security, Polish, Testing & Verification (Steps 13–17)
- [x] **Step 13: Security & Farmer Data Isolation**
  - Enforce tenant verification (`verify_farm_access`, `verify_task_access`) across all new endpoints.
  - Protect tile and download routes against IDOR vulnerabilities.
- [x] **Step 14: Complete UI Integration & Responsive Styling**
  - Enhance Map tab in `frontend/app/admin/photogrammetry/page.tsx` with dynamic layer switcher (Ortho, DSM, DTM, Hillshade).
  - Add 3D model viewer tab and GCP upload dialog.
- [x] **Step 15: Run Automated Tests & Regression Checks**
  - Execute backend test suite verifying project CRUD, task creation, GCP validation, tile proxy, and permissions.
- [x] **Step 16: Document Feature Coverage Matrix & Known Limitations**
  - Complete remaining technical documents in `docs/webodm-integration/`.
  - Update root `README.md`.
- [x] **Step 17: Deliver Final Report & Summary**
  - Present comprehensive findings across all 15 audit dimensions.
