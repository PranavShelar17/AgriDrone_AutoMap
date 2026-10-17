# AgriDrone AutoMap

> **Production-Grade Agricultural Drone Mapping, Photogrammetry, Geospatial Raster Analytics, and Secure Map Visualization Platform.**

---

## 1. Project Purpose & Overview

**AgriDrone AutoMap** is an enterprise-grade platform engineered to process aerial drone survey imagery over agricultural lands, execute photogrammetric reconstructions, derive calibrated vegetation index rasters, deliver interactive multi-layer map visualizations, and generate auditable PDF reports.

The platform bridges the gap between raw aerial sensor data and actionable agronomic intelligence while maintaining strict multi-tenant data isolation, scientific accuracy, and cloud security.

---

## 2. Approved Technology Stack

The platform is built on an approved, enterprise-grade open-source and cloud technology stack:

- **Frontend**: Next.js (App Router), TypeScript, Tailwind CSS
- **Backend**: Python 3.11+, FastAPI
- **Database & Spatial Engine**: PostgreSQL, PostGIS
- **Photogrammetry Engine**: WebODM / OpenDroneMap
- **GIS & Raster Processing**: GDAL, Rasterio, NumPy
- **Interactive Mapping**: MapLibre GL JS
- **Asynchronous Task Broker**: Celery, Redis
- **Cloud Object Storage**: Microsoft Azure Blob Storage (official Azure SDK for Python)
- **PDF Report Generation**: ReportLab
- **Containerization & Deployment**: Docker, Docker Compose

*Architectural Principle*: Microsoft Azure Blob Storage is the sole primary object store for binary assets (photos, orthomosaics, COGs, PDFs). S3 and MinIO are excluded. PostgreSQL and PostGIS store structured relational records and spatial vector boundaries, not large raster binaries.

---

## 3. Strict Five-Page Core Architecture Scope

The web application is strictly constrained to **exactly five functional pages**:

1. **Page 1 — Admin Dashboard & Drone Image Ingestion** (`/admin/dashboard`): Farm/Field hierarchy management, raw drone photo upload, pre-stitched GeoTIFF ingestion, CRS and EXIF validation, and ingestion eligibility ledger.
2. **Page 2 — WebODM Photogrammetry Processing** (`/admin/photogrammetry`): WebODM task configuration, asynchronous reconstruction dispatch, real-time log streaming, and orthomosaic registration.
3. **Page 3 — Algorithm & Multi-Map Generation** (`/admin/algorithms`): Spectral band mapping, physical band validation, and scientific raster math for NDVI, NDRE, GNDVI, and SAVI.
4. **Page 4 — Secure Farmer Portal** (`/portal/surveys`): Multi-tenant spatial map viewer powered by MapLibre GL JS, layer switching, opacity controls, swipe comparison, and secure asset downloads.
5. **Page 5 — Diagnostics & Actionable Insights** (`/portal/diagnostics`): Pixel-level statistical summaries, zonal canopy health classifications, data limitation disclosures, and automated PDF report generation.

---

## 4. High-Level Processing Workflows

The platform strictly separates raw aerial photography from pre-stitched GIS rasters:

```
Workflow 1: Raw Drone Photographs
[Raw Aerial Photos with GPS EXIF]
       │
       ▼
[Page 1: Ingestion & EXIF Validation]
       │
       ▼ (Eligible for WebODM)
[Page 2: WebODM Photogrammetry Reconstruction]
       │
       ▼
[Registered Orthomosaic GeoTIFF] ──────┐
                                       │
Workflow 2: Pre-Stitched GeoTIFFs     │
[Vendor-Supplied GeoTIFF]              │
       │                               │
       ▼                               │
[Page 1: Ingestion & CRS Validation]   │
       │                               │
       ▼ (Eligible for Direct GIS)     │
       └───────────────────────────────┴─► [Page 3: Spectral Algorithm Engine]
                                                  │
                                                  ▼ (NDVI / NDRE / GNDVI / SAVI)
                                           [Cloud Optimized GeoTIFFs]
                                                  │
                                           ┌──────┴──────────────────────────┐
                                           ▼                                 ▼
                               [Page 4: Farmer Map Viewer]       [Page 5: Diagnostics & PDF Reports]
```

---

## 5. Technical Documentation Suite

Complete technical blueprints and requirements are documented in the `docs/` directory:

### Phase 1: Requirements Analysis & Blueprint
1. [Project Overview](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-1/project-overview.md) — Objectives, personas, and assumptions.
2. [Scope and Exclusions](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-1/scope-and-exclusions.md) — Five-page boundary and out-of-scope modules.
3. [Five-Page Requirements](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-1/five-page-requirements.md) — Detailed specifications for each page.
4. [User Journeys](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-1/user-journeys.md) — End-to-end workflows and sequence diagrams.
5. [Functional Requirements](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-1/functional-requirements.md) — Numbered `FR-xxx` specifications with testable criteria.
6. [Non-Functional Requirements](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-1/non-functional-requirements.md) — Security, performance, and reliability standards.
7. [Data and File Requirements](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-1/data-and-file-requirements.md) — Supported formats, CRS, and storage structures.
8. [GIS and Algorithm Validation](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-1/gis-and-algorithm-validation.md) — Formulas, spectral gating, and numeric safety.
9. [Security and Access Requirements](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-1/security-and-access-requirements.md) — Tenancy, RBAC, and Azure SAS policies.
10. [System Workflow](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-1/system-workflow.md) — System architecture and Mermaid sequence flows.
11. [Ten-Phase Roadmap](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-1/ten-phase-roadmap.md) — Execution roadmap from Phase 1 to Phase 10.
12. [Acceptance Criteria](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-1/acceptance-criteria.md) — Measurable audit checklist.
13. [Open Decisions](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-1/open-decisions.md) — Unresolved decisions with resolution milestones.

### Phase 2: UI/UX Design & Reference Template Matching
1. [Reference Template Analysis](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-2/reference-template-analysis.md) — Inspection of `drone-main` reference assets, layout patterns, and color tokens.
2. [Design System](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-2/design-system.md) — Emerald/slate color tokens, typography, radii, shadows, buttons, inputs, tables, status badges, and UI states.
3. [Five-Page UI Specification](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-2/five-page-ui-specification.md) — Complete screen wireframes, components, controls, and states for all five pages.
4. [Responsive Design Specification](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-2/responsive-design-specification.md) — Breakpoint adaptations for Desktop, Laptop, Tablet, and Mobile.
5. [Component Inventory](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-2/component-inventory.md) — Catalog of reusable UI components and consuming page mappings.
6. [UI/UX Acceptance Checklist](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-2/ui-ux-acceptance-checklist.md) — 13 testable pass/fail criteria across design fidelity, scope, and responsiveness.
7. [Phase 2 Open Questions](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-2/phase-2-open-questions.md) — Open design decisions requiring stakeholder input.

### Phase 3: System Architecture & Implementation Blueprint
1. [System Architecture Overview](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-3/architecture-overview.md) — Overall architecture, component responsibilities, technology choices, and constraints.
2. [System Architecture Diagrams](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-3/system-architecture-diagrams.md) — Mermaid diagrams for overall system, uploads, WebODM, algorithms, reports, and security boundaries.
3. [Frontend & Backend Structure](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-3/frontend-backend-structure.md) — Monorepo structure, Next.js components, FastAPI routers, Pydantic settings, and test boundaries.
4. [Database Architecture & Data Model](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-3/database-and-data-model.md) — PostGIS schemas, spatial geometry, foreign-key relationships, indexes, and Alembic migrations.
5. [API Contracts & Specifications](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-3/api-contracts.md) — Versioned `/api/v1` REST endpoints, request/response JSON schemas, error envelopes, and status codes.
6. [Azure Blob Storage Architecture](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-3/azure-storage-architecture.md) — Containers, naming conventions, SAS token lifecycle, chunked uploads, and cost tiers.
7. [Background Jobs & WebODM Integration](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-3/background-jobs-and-webodm.md) — WebODM REST client, Celery worker queues, Redis broker, job state machines, and retries.
8. [GIS & Raster Processing Architecture](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-3/gis-processing-architecture.md) — GDAL/Rasterio validation, spectral band mapping, scientific guardrails, and COG tiling.
9. [Map & Report Delivery Architecture](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-3/map-and-report-delivery.md) — MapLibre GL JS canvas, COG tile serving, swipe comparison, and ReportLab PDF compilation.
10. [Security Architecture & Threat Mitigation](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-3/security-architecture.md) — RBAC matrix, multi-tenant query scoping, OWASP mitigation, and audit logging.
11. [Deployment & Operations Architecture](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-3/deployment-and-operations.md) — Docker Compose local dev stack, target Azure cloud topology, and hardware sizing.
12. [Technical Risk Register](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-3/technical-risk-register.md) — Risk matrix across photogrammetry, scientific data, storage, and security.
13. [Phase 3 Acceptance Checklist](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-3/phase-3-acceptance-checklist.md) — 17 measurable pass/fail architectural verification criteria.
14. [Phase 3 Open Decisions](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-3/phase-3-open-decisions.md) — Registry of open architectural decisions and resolution milestones.
15. [Phase 4 Implementation Plan](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-3/phase-4-implementation-plan.md) — Step-by-step foundation setup sequence and completion criteria.

### Phase 4: Platform Foundation & Development Setup
1. [Phase 4 Implementation Log](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-4/phase-4-implementation-log.md) — Starting baseline, created files, decisions, and actual test results.
2. [Local Development Guide](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-4/local-development-guide.md) — Prerequisites, port allocation, step-by-step startup, and troubleshooting.
3. [Environment Configuration](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-4/environment-configuration.md) — Variable inventory, secret governance, and safe placeholders.
4. [Database Setup & Migrations](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-4/database-setup-and-migrations.md) — PostGIS verification, Alembic workflow, and schema tables.
5. [Phase 4 Test & Verification Report](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-4/phase-4-test-report.md) — Full pytest (10/10 passed) and Next.js (9/9 compiled) results.

### Phase 5: Admin Dashboard, Farm/Survey Management & Drone Image Ingestion
1. [Phase 5 Implementation Log](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-5/phase-5-implementation-log.md) — Chronological execution log, architectural decisions, and verification findings.
2. [Farm & Field Management Guide](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-5/farm-field-management.md) — Spatial hierarchy, CRUD workflows, PostGIS Polygon validation, and area calculations.
3. [Survey Flight Management Guide](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-5/survey-management.md) — Survey lifecycle, mission code sequence generation, and relational integrity.
4. [Drone Image Ingestion Architecture](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-5/drone-image-ingestion.md) — Dual-workflow architecture (Raw Photos for WebODM vs GeoTIFFs for Direct GIS).
5. [File Validation Rules Specification](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-5/file-validation-rules.md) — Magic byte signatures, EXIF GPS extraction, GeoTIFF CRS/scale tags, and rejection criteria.
6. [Azure Blob Storage Setup Guide](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-5/azure-blob-storage-setup.md) — Official Azure Python SDK adapter, private containers, SAS security, and local dev fallback adapter.
7. [API Endpoints Specification](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-5/api-endpoints.md) — Full `/api/v1` REST contract, schemas, and error responses.
8. [Database Schema & Migrations](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-5/database-migrations.md) — Alembic `001_initial_core_schema` table definitions and schema alignment.
9. [Security & Access Boundaries](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-5/security-and-access-boundaries.md) — Dev admin boundary, credential isolation, and path traversal protection.
10. [Phase 5 Test & Verification Report](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-5/phase-5-test-report.md) — 23 unit/integration tests (100% pass) and frontend build verification.
11. [Phase 5 Known Limitations](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-5/phase-5-known-limitations.md) — Explicit phase boundaries and environment notes.
### Phase 6: WebODM / OpenDroneMap Integration & Drone Photogrammetry Processing
1. [Phase 6 Implementation Log](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-6/phase-6-implementation-log.md) — Chronological execution log, database migrations, and verification findings.
2. [WebODM Architecture & Setup Guide](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-6/webodm-architecture-and-setup.md) — NodeODM and WebODM cluster topology, service boundaries, and Docker setup.
3. [WebODM Configuration Specification](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-6/webodm-configuration.md) — Server-side environment variables, presets (Fast, Precision, Custom), and resource sizing.
4. [Photogrammetry Workflow Blueprint](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-6/photogrammetry-workflow.md) — 16-stage end-to-end workflow from photo staging to deliverable registration.
5. [Dataset Eligibility & Validation Specification](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-6/dataset-eligibility-and-validation.md) — Eligibility rules separating raw photos from GeoTIFF rasters with explicit rejection rationales.
6. [Processing Jobs & Lifecycle State Machine](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-6/processing-jobs-and-statuses.md) — Auditable states (`SUBMITTED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED`), polling loops, and retries.
7. [Output Artifacts & Storage Specification](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-6/output-artifacts-and-storage.md) — Deliverables cataloging (`ORTHOPHOTO`, `DSM`, `DTM`), CRS extraction, and Azure Blob storage paths.
8. [API Endpoints Reference](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-6/api-endpoints.md) — Full `/api/v1/photogrammetry` and `/api/v1/cluster/status` REST contracts.
9. [Security & Error Handling Architecture](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-6/security-and-error-handling.md) — Parameter whitelisting, command injection mitigation, concurrency guards, and error codes.
10. [Phase 6 Test & Verification Report](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-6/phase-6-test-report.md) — 34 automated backend tests (100% pass) and Next.js production build verification.
11. [Phase 6 Known Limitations](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-6/phase-6-known-limitations.md) — Hardware limits, offline cluster handling, and strict Phase 6 boundaries.
12. [Phase 7 Readiness Checklist](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-6/phase-7-readiness-checklist.md) — Prerequisites and scope hand-off for Spectral Algorithms & Multi-Map Generation.

### WebODM Photogrammetry Integration Suite (Comprehensive Architecture & Capabilities)
1. [Source Code Audit](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/webodm-integration/source-code-audit.md) — Full inspection of WebODM 3.3.1 Django viewsets, Celery workers, tiler, and models.
2. [Feature Inventory](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/webodm-integration/feature-inventory.md) — Comprehensive capability inventory across Groups A through O.
3. [Integration Architecture](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/webodm-integration/integration-architecture.md) — FastAPI gateway, asynchronous Celery bridge, and storage synchronization.
4. [Implementation Plan](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/webodm-integration/implementation-plan.md) — 17-step phased roadmap.
5. [API Contracts](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/webodm-integration/api-contracts.md) — Endpoints for projects, tasks, GCP, options schema, presets, tiles proxy, and 3D assets.
6. [Project & Task Workflows](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/webodm-integration/project-and-task-workflows.md) — Lifecycle, state transitions, concurrency, and failure recovery.
7. [Image & GCP Workflows](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/webodm-integration/image-and-gcp-workflows.md) — Aerial classification, OpenDroneMap GCP format (`gcp_list.txt`), and validation algorithms.
8. [Output & Map Delivery](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/webodm-integration/output-and-map-delivery.md) — COG conversion, dynamic tile serving proxy, bounds, metadata, and MapLibre GL JS integration.
9. [Advanced Visualization](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/webodm-integration/advanced-visualization.md) — 3D textured meshes (`.glb`), dense point clouds (`.laz`), Potree, 3D Gaussian splats, panoramas, and colormaps.
10. [Processing Node Management](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/webodm-integration/processing-node-management.md) — NodeODM telemetry, capacity, options schema discovery, and administrator RBAC.
11. [Security & Permissions](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/webodm-integration/security-and-permissions.md) — Full RBAC matrix, tile proxy authentication, downloads, and anti-IDOR protections.
12. [Azure Storage Integration](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/webodm-integration/azure-storage-integration.md) — Container hierarchy, block-blob transfers, and short-lived SAS link security.
13. [License & Third-Party Inventory](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/webodm-integration/license-and-third-party-inventory.md) — AGPL-3.0 compliance boundaries, UAV4GEO trademark compliance, and third-party software inventory.
14. [Test Results Report](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/webodm-integration/test-results.md) — 17 passing integration tests (100% pass) and frontend build verification.
15. [Known Limitations](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/webodm-integration/known-limitations.md) — WebODM vs NodeODM, 3D Gaussian splat GPU prerequisites, multispectral camera calibration, and RAM thresholds.
16. [Feature Coverage Matrix](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/webodm-integration/feature-coverage-matrix.md) — 28-item status verification matrix across Groups A through O.

---

## 6. Local Development Quick-Start

AgriDrone AutoMap runs locally with non-conflicting dedicated development ports:
- **Frontend (Next.js)**: `http://localhost:3005`
- **Backend API (FastAPI)**: `http://localhost:8005` (Swagger Docs: `http://localhost:8005/docs`)
- **Database (PostGIS)**: `localhost:5434`
- **Redis Message Broker**: `localhost:6380`
- **WebODM / NodeODM Node**: `localhost:3001`

### 1. Start Database, Redis & Optional NodeODM (Docker):
```bash
# Start PostGIS and Redis
docker compose up -d db redis

# Optional: Spin up local NodeODM processing node on port 3001
docker compose --profile photogrammetry up -d nodeodm
```

### 2. Start Backend API & Worker:
```bash
cd backend
.\.venv\Scripts\Activate.ps1
alembic upgrade head
uvicorn app.main:app --port 8005 --reload
```
*Optional Celery Worker (in a separate terminal)*:
```bash
celery -A app.core.celery_app.celery_app worker -l info -Q photogrammetry
### Phase 7: GIS Algorithms, Vegetation Indices & Multi-Map Generation
1. [Phase 7 Implementation Log](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-7/phase-7-implementation-log.md) — Chronological execution and milestone audit.
2. [GIS Processing Architecture](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-7/gis-processing-architecture.md) — System data flow, Rasterio/GDAL integration, and COG writer.
3. [Supported Algorithms & Formulas](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-7/supported-algorithms-and-formulas.md) — NDVI, NDRE, GNDVI, SAVI, VARI, GLI mathematical formulas.
4. [Spectral Band Mapping](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-7/spectral-band-mapping.md) — Physical sensor channel arrangements and scientific gating.
5. [Raster Validation & Alignment](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-7/raster-validation-and-alignment.md) — CRS, geotransform, and independent output verification.
6. [Radiometric Data & Limitations](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-7/radiometric-data-and-limitations.md) — Digital numbers vs calibrated surface reflectance.
7. [Multi-Map Generation Workflow](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-7/multi-map-generation-workflow.md) — Multi-algorithm batch processing and isolation.
8. [Output Products & Metadata](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-7/output-products-and-metadata.md) — COGs, JSONB provenance, and 4-zone vigour stats.
9. [API Endpoints](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-7/api-endpoints.md) — Complete REST specification for `/api/v1/algorithms`.
10. [Background Jobs & Error Handling](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-7/background-jobs-and-error-handling.md) — Celery worker lifecycle and fault tolerance.
11. [Phase 7 Test Report](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-7/phase-7-test-report.md) — Automated test results and synthetic validation logs.
12. [Known Limitations](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-7/phase-7-known-limitations.md) — Scope boundaries and scientific disclosures.
13. [Phase 8 Readiness Checklist](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-7/phase-8-readiness-checklist.md) — Handover criteria for interactive map viewer.

### Phase 8: Interactive GIS Maps, Multi-Layer Visualization & Diagnostics
1. [Phase 8 Implementation Log](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-8/phase-8-implementation-log.md) — Chronological execution, architecture decisions, and milestone summary.
2. [MapLibre Integration](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-8/maplibre-integration.md) — WebGL map container, lifecycle management, basemap, and layer ordering.
3. [Raster Visualization & Delivery](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-8/raster-visualization-and-delivery.md) — 256x256 XYZ slippy tile engine, windowed reading, and point probing.
4. [Layer Management & Legends](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-8/layer-management-and-legends.md) — Continuous RdYlGn, Viridis, and Terrain color ramps, opacity sliders, and NoData indicators.
5. [Raster Comparison Workflow](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-8/raster-comparison-workflow.md) — Dual synchronized MapLibre view, camera tracking, and compatibility validation.
6. [Field Boundaries & Spatial Data](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-8/field-boundaries-and-spatial-data.md) — PostGIS `ST_AsGeoJSON` boundary delivery, centroid and bbox calculation, and vector styling.
7. [Raster Statistics & Diagnostics](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-8/raster-statistics-and-diagnostics.md) — Pixel statistics, valid coverage %, and 4-zone vigour distributions.
8. [Diagnostic Limitations & Safeguards](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-8/diagnostic-interpretation-limitations.md) — Prohibited claims, environmental confounding factors, and mandatory ground-truthing.
9. [Security & Data Access](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-8/security-and-data-access.md) — Private Azure storage, path traversal guards, and tenant boundary enforcement.
10. [Performance & Caching](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-8/performance-and-caching.md) — Out-of-bounds rejection, COG block windowing, and HTTP caching.
11. [Phase 8 Test Report](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-8/phase-8-test-report.md) — Automated verification of 63 backend tests and 9 frontend pages.
12. [Known Limitations](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-8/phase-8-known-limitations.md) — Scope boundaries and deferred Phase 9 items.
13. [Phase 9 Readiness Checklist](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-8/phase-9-readiness-checklist.md) — Handover criteria for farmer portal & mobile experience.

---

## 6. Beginner's Guide: Exploring Interactive GIS Maps & Diagnostics

### How to Start the Application:
1. **Start Database and Redis Containers**:
   ```bash
   docker compose up -d
   ```
2. **Start FastAPI Backend**:
   ```bash
   cd backend
   .\.venv\Scripts\Activate.ps1
   uvicorn app.main:app --port 8000 --reload
   ```
3. **Start Next.js Frontend**:
   ```bash
   cd frontend
   npm run dev -- -p 3005
   ```
4. Open your browser to [http://localhost:3005](http://localhost:3005).

---

### Step-by-Step User Journey:

#### 1. Select a Farm and Field:
- Navigate to **Page 4: Secure Farmer Portal** at [http://localhost:3005/portal/surveys](http://localhost:3005/portal/surveys).
- Use the **Assigned Farm** dropdown to select your farm (e.g. *Test Spectral Farm*).
- Select your target field (e.g. *Field North*).
- The map automatically centers and displays the PostGIS field boundary polygon in translucent emerald with a high-contrast dashed border!

#### 2. Select a Validated Map Product:
- Under **Survey Flight Date**, choose the flight you want to explore.
- In the right-hand panel, browse the list of **Validated Map Products** (such as *RGB Orthomosaic*, *NDVI Canopy Vigor*, *NDRE Chlorophyll*, *GNDVI*, or *SAVI*).
- Click on any product to display its colorized raster overlay directly on the map.

#### 3. Adjust Layer Visibility and Opacity:
- Use the **Overlay Opacity** slider in the sidebar or top bar to smoothly adjust transparency from 10% to 100%. This allows blending the vegetation index over the underlying drone orthomosaic or aerial basemap.
- Click the **Layer Visible / Hidden** button to quickly toggle the overlay on and off.
- Click **Fit Extent** anytime you want to re-center the map on your field boundary.

#### 4. Read the Dynamic Legend:
- Inspect the floating legend in the bottom-left corner of the map.
- For vegetation indices, the continuous Red-Yellow-Green bar illustrates canopy vigour:
  - **Red / Orange (< 0.2)**: Bare soil, non-photosynthetic material, or water.
  - **Yellow (0.2 - 0.4)**: Sparse or stressed canopy.
  - **Light Green (0.4 - 0.6)**: Moderate vegetative development.
  - **Deep Green (> 0.6)**: Dense, healthy photosynthetic canopy.
- Note the **NoData / Masked** badge: areas outside the flight survey are 100% transparent and never counted as zero or bare soil.

#### 5. Probe Exact Pixel Values at Any Point:
- Click anywhere on the drone map.
- The map sends an instant coordinate probe to the backend and displays a floating badge showing the exact measured index value (e.g. `NDVI = 0.7949`) at that specific spot on your field!

#### 6. Compare Two Products Side-by-Side:
- Click the **Compare Layers** button in the header bar.
- The viewer opens a dual synchronized split-screen.
- Select Product A (e.g. *RGB Orthomosaic*) for the left view and Product B (e.g. *NDVI Canopy Vigor*) for the right view.
- Pan or zoom either map — both views automatically track together in real time, keeping your field aligned!
- A green **Compatibility Banner** confirms spatial overlap and gives guidance.

#### 7. View Detailed Diagnostics & Agronomic Insights:
- Click **View Diagnostics (Page 5)** or open [http://localhost:3005/portal/diagnostics](http://localhost:3005/portal/diagnostics).
- View data-derived statistical cards:
  - **Mean Index Value**, **Median (p50)**, and **Standard Deviation**.
  - **Valid Coverage %**: Shows the proportion of valid pixels vs. masked NoData pixels.
  - **Covered Area**: Shows exact ground area in hectares.
- View the **Canopy Vigour & Spectral Zoning Distribution** bar charts, showing the exact hectare breakdown across each vegetative health tier.
- Read the **Scientific Interpretation Safeguards**: understand that vegetation greenness is an indicator of canopy light reflection, not a direct disease diagnosis, and requires field scouting before applying chemicals or fertilizers.

#### 8. Troubleshooting:
- **No Boundary Appears?**: The field record in PostGIS does not have polygon coordinates. The map will gracefully center on the raster GeoTIFF bounds instead.
- **Product Shows "Metadata Only"?**: The database record exists, but the physical GeoTIFF file is not on disk. The system marks it with a grey badge and avoids requesting tiles for missing files.
- **Blank Tiles?**: Ensure your backend server is running on port 8000 and the PostgreSQL database is online.

---

---

## 7. Phase 9: Authentication, Authorization & Secure Farmer Portal

Phase 9 integrates enterprise-grade first-party authentication, fine-grained role-based access control, and complete resource-level data isolation into the AgriDrone AutoMap platform.

### Key Architecture Features
- **Self-Hosted First-Party Identity**: Secure Bcrypt password hashing (12 rounds) and HS256 PyJWT tokens with 8-hour lifespan. Zero external vendor lock-in and $0 cloud identity fees.
- **Dual Session Delivery**: Standard `Authorization: Bearer <token>` for API calls, alongside `HttpOnly`, `SameSite=Lax` cookies for browser-native MapLibre GL raster tile streaming.
- **Relational Anti-IDOR Enforcement**: Traverses database relationships (`resource -> survey -> field -> farm.owner_id == user.id`) on every protected endpoint.
- **Privacy-Preserving 404s**: Unauthorized attempts to access another farmer's farm, field, raster, tile, or report return generic `HTTP 404 Not Found` responses, eliminating resource enumeration.
- **Rate-Limiting & Audit Logging**: 20 requests/minute brute-force threshold on `/auth/login` and audit logs recorded in `audit_logs`.
- **Accessible Login UI**: Modern Emerald/Slate design at `/login` with visible focus rings, ARIA error announcements, loading states, anti-open-redirect validation, and one-click demo credentials.

### Evaluation Accounts & Test Credentials

| Role | Email Address | Password | Permissions & Scope |
| :--- | :--- | :--- | :--- |
| **System Admin** | `admin@agridrone.local` | `Admin@AgriDrone2026!` | Global access across all 5 modules, image upload, photogrammetry & algorithms |
| **Farmer (Baramati)** | `farmer@greenvalley.local` | `Farmer@AgriDrone2026!` | Isolated access strictly to Baramati Precision Farm rasters and diagnostics |
| **Farmer (Ingestion)**| `farmer2@sunrise.local` | `Farmer2@AgriDrone2026!` | Isolated access strictly to Ingestion Test Farm |

### Verification & Testing Commands

```bash
# Backend Automated Security & Regression Suite (80/80 Passed)
cd backend
.venv\Scripts\activate
pytest -v

# Frontend Production Build (10/10 Routes Prerendered)
cd frontend
npm run build
```

### Phase 9 Documentation Suite
1. [Phase 9 Audit](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-9/phase-9-audit.md)
2. [Authentication Decision ADR](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-9/authentication-decision.md)
3. [Authentication & Session Design](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-9/authentication-and-session-design.md)
4. [Roles & Permissions Specification](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-9/roles-and-permissions.md)
5. [Farmer Resource Ownership & Anti-IDOR](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-9/farmer-resource-ownership.md)
6. [Protected API Inventory](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-9/protected-api-inventory.md)
7. [Private File & Map Access](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-9/private-file-and-map-access.md)
8. [Database Changes & Schema Integrity](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-9/database-changes.md)
9. [Automated Security Test Results](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-9/security-test-results.md)
10. [Phase 9 Acceptance Checklist](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-9/phase-9-acceptance-checklist.md)
11. [Known Limitations & Open Issues](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-9/phase-9-open-issues.md)
12. [Phase 10 Handover Brief](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-9/phase-10-handover.md)

---

---

## 8. Phase 10: End-to-End Testing, Deployment, Monitoring & Final Handover

Phase 10 represents the final planned engineering phase of the AgriDrone AutoMap project, establishing an end-to-end verified release baseline, production containerization manifests, automated CI/CD quality pipelines, disaster recovery runbooks, and comprehensive technical documentation.

### Key Deliverables & Achievements
- **End-to-End Test Suite**: Automated verification across all 7 core workflows (A through G). **80 / 80 backend tests passed (100%)** and **10 / 10 frontend routes compiled successfully** with zero TypeScript errors.
- **Production Containerization**: Multi-stage, non-root production Dockerfiles ([`backend/Dockerfile.prod`](file:///c:/Users/Admin/Desktop/new%20dron%202/backend/Dockerfile.prod) and [`frontend/Dockerfile.prod`](file:///c:/Users/Admin/Desktop/new%20dron%202/frontend/Dockerfile.prod)) and orchestration manifest ([`docker-compose.prod.yml`](file:///c:/Users/Admin/Desktop/new%20dron%202/docker-compose.prod.yml)).
- **Continuous Integration (CI/CD)**: GitHub Actions workflow ([`.github/workflows/ci.yml`](file:///c:/Users/Admin/Desktop/new%20dron%202/.github/workflows/ci.yml)) automating linting, type checks, PostGIS database migrations, and pytest execution on every PR.
- **Database Safety & PITR**: Formal backup and recovery standard ([`docs/phase-10/backup-and-recovery-plan.md`](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/backup-and-recovery-plan.md)) covering PostgreSQL/PostGIS dump procedures and Azure storage synchronization.
- **Operational Monitoring & Runbooks**: Health probes (`/health`, `/health/readiness`), alert thresholds, and incident response runbooks ([`docs/phase-10/incident-response-runbook.md`](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/incident-response-runbook.md)).
- **Production Deployment Guide**: Beginner-friendly step-by-step operator guide ([`docs/phase-10/deployment-runbook.md`](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/deployment-runbook.md)).

### Phase 10 Documentation Suite (`docs/phase-10/`)
1. [Initial Project Audit](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/phase-10-initial-audit.md)
2. [Release Baseline Specifications](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/release-baseline.md)
3. [End-to-End Test Plan](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/end-to-end-test-plan.md)
4. [End-to-End Test Results](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/end-to-end-test-results.md)
5. [Automated Quality Checks](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/automated-quality-checks.md)
6. [System Security Review](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/security-review.md)
7. [Backup & Recovery Plan](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/backup-and-recovery-plan.md)
8. [Deployment Architecture](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/deployment-architecture.md)
9. [Environment Configuration Standard](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/environment-configuration.md)
10. [Hosting Decision ADR](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/hosting-and-deployment-decision.md)
11. [CI/CD Release Process](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/ci-cd-release-process.md)
12. [Monitoring & Alerting](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/monitoring-and-alerting.md)
13. [Incident Response Runbook](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/incident-response-runbook.md)
14. [Performance & Scalability Review](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/performance-review.md)
15. [UI Regression & Accessibility](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/ui-regression-and-accessibility.md)
16. [Deployment Runbook](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/deployment-runbook.md)
17. [Known Issues & Limitations](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/known-issues-and-limitations.md)
18. [Final Acceptance Checklist](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/final-acceptance-checklist.md)
19. [Project Handover Manual](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/project-handover.md)

---

## 9. Current Project Status

- **Current Active Phase**: **Phase 10: End-to-End Testing, Deployment, Monitoring & Final Handover**
- **Status**: **Phase 10 Complete — All Phases 1–10 Successfully Verified (v1.0.0-rc1 Release Candidate)**
- **Quality Metrics**: **80/80 Backend Tests Passed (100%)**, **10/10 Frontend Routes Prerendered Successfully**, **Zero Unhandled Exceptions**.
- **Deployment Status**: Production manifests, Dockerfiles, and CI/CD pipelines are fully prepared and tested. **No unapproved cloud resources or public deployments have been created pending formal user approval.**

---

## 10. Next Actions for Project Owner

1. Review the Hosting Recommendation ADR in [docs/phase-10/hosting-and-deployment-decision.md](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/hosting-and-deployment-decision.md).
2. Review the Deployment Runbook in [docs/phase-10/deployment-runbook.md](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/deployment-runbook.md).
3. Authorize your preferred production hosting target (Option 1: Microsoft Azure Unified Cloud, or Option 3: Self-Hosted Docker Compose Edge) to commence public production provisioning.





