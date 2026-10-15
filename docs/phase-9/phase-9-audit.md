# Phase 9 Audit — AgriDrone AutoMap Authentication & Farmer Portal Baseline

**Status:** Completed & Verified  
**Date:** October 2026  
**Author:** AgriDrone Senior Engineering & Security Architecture Team  

---

## 1. Executive Summary

Prior to Phase 9, the AgriDrone AutoMap platform implemented robust GIS photogrammetry, vegetation index calculation, zonal analytics, and interactive WebGL mapping capabilities across Phases 1 through 8. However, all backend REST endpoints and frontend views operated without identity verification, allowing unrestricted access and posing Insecure Direct Object Reference (IDOR) vulnerabilities across multi-tenant agricultural assets.

This audit reviews the system state at the conclusion of Phase 8 and documents the baseline architecture, existing models, sensitive data paths, and requirements for implementing Phase 9 Authentication, Authorization, and Secure Farmer Portal isolation.

---

## 2. Review of Completed Phases (Phases 1–8)

### Phase 1: Requirements & Acceptance Criteria
- Established the 5 core functional platform pages:
  1. Ingestion (`/admin/dashboard`)
  2. WebODM Photogrammetry (`/admin/photogrammetry`)
  3. GIS Algorithms & Spectral Indices (`/admin/algorithms`)
  4. Secure Farmer Portal (`/portal/surveys`)
  5. Diagnostics & Actionable Insights (`/portal/diagnostics`)
- Defined strict tenant isolation requirement: farmers must never see or probe fields, drone surveys, or vegetation maps belonging to other farms.

### Phase 2: UI/UX Design System
- Built standard design system using Tailwind CSS, Emerald/Slate color palettes, Lucide icons, responsive navigation drawers, and accessible forms.
- Included prototype mock banner (`PHASE 2 VISUAL PROTOTYPE`) and hardcoded user pills (`Tenant ID: 12`, `Admin Operator`).

### Phase 3: Architecture & Open Decisions
- Inspected [docs/phase-3/phase-3-open-decisions.md](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-3/phase-3-open-decisions.md).
- **Open Decision #3 (Authentication & Multi-Tenant Authorization)** evaluated Option A (Self-hosted Bcrypt + PyJWT) vs Option B (Managed Cloud IdP). Option A was selected for zero external vendor lock-in, zero cloud identity costs, and full air-gapped / local edge deployability.
- Schema defined core entities: `users`, `farms`, `fields`, `surveys`, `survey_files`, `photogrammetry_tasks`, `algorithm_jobs`, `map_products`, and `audit_logs`.

### Phase 4: Application Foundation
- FastAPI backend on port 8005, Next.js frontend on port 3005.
- PostgreSQL 16 + PostGIS on port 5434, Redis 7.2 on port 6380.
- Database connection pooling, health and readiness probes (`/health`, `/ready`).

### Phase 5: Farms, Fields, Surveys & Ingestion
- Ingestion endpoints: `POST /api/v1/ingestion/surveys/{id}/files`, `GET /api/v1/ingestion/surveys/{id}/files`.
- Farm & Field CRUD: `POST /api/v1/farms`, `POST /api/v1/fields`.
- File storage abstraction supporting both Azure Blob Storage and local fallback (`backend/storage/`).

### Phase 6: WebODM Integration
- Asynchronous Celery task processing with WebODM/NodeODM for 2D orthomosaic and DSM generation.
- Endpoints: `POST /api/v1/photogrammetry/tasks`, `GET /api/v1/photogrammetry/tasks/{id}`.

### Phase 7: GIS Algorithms & Generated Raster Products
- Scientific multispectral index generation (`INDEX_NDVI`, `INDEX_NDRE`, `INDEX_VARI`, `INDEX_GLI`, `ELEVATION_DSM`).
- Zonal statistics and histogram extraction stored directly in PostgreSQL JSONB fields.
- Endpoints: `POST /api/v1/algorithms/batch`, `GET /api/v1/algorithms/jobs/{id}`.

### Phase 8: Interactive GIS Maps & Diagnostics
- MapLibre GL JS map integration with dynamic raster tile rendering (`/api/v1/maps/tiles/{id}/{z}/{x}/{y}.png`).
- Continuous colormaps, point probing (`/api/v1/maps/products/{id}/probe`), dual comparison slider, and scientific diagnostics.

---

## 3. Data Model & Entity Hierarchy

The database model forms a strict hierarchical ownership tree rooted at `Farm.owner_id`:

```
User (owner_id / user_id)
 └── Farm (owner_id == User.id)
      └── Field (farm_id == Farm.id)
           └── Survey (field_id == Field.id)
                ├── SurveyFile (survey_id == Survey.id)
                ├── PhotogrammetryTask (survey_id == Survey.id)
                ├── AlgorithmJob (survey_id == Survey.id)
                ├── MapProduct (survey_id == Survey.id)
                └── Report (survey_id == Survey.id)
```

### Pre-existing Models Inspected:
- `backend/app/models/user.py`: Defined `User` with `email`, `hashed_password`, `role` (`ADMIN`, `AGRONOMIST`, `FARMER`), and `is_active`.
- `backend/app/models/farm.py`: Defined `Farm` with `owner_id` (foreign key to `users.id`).
- `backend/app/models/report.py`: Defined `Report` with `survey_id` and `generated_by_user_id`.
- `backend/app/models/audit_log.py`: Defined `AuditLog` with `user_id`, `action`, `resource_type`, `ip_address`, `details`.

---

## 4. Sensitive APIs Requiring Authentication & IDOR Protection

All REST endpoints below expose proprietary agricultural intelligence or private drone imagery and must be guarded:

| Endpoint Pattern | Sensitivity | Phase 9 Protection Applied |
| :--- | :--- | :--- |
| `GET /api/v1/farms` | Farm business data | Filtered to owner for `FARMER`; all for `ADMIN` |
| `GET /api/v1/farms/{id}` | Farm boundaries & fields | Ownership verification; privacy-preserving 404 |
| `GET /api/v1/fields/{id}/boundary` | Precise geospatial geometry | Ownership verification |
| `GET /api/v1/surveys/{id}` | Flight metadata & stats | Ownership verification |
| `POST /api/v1/ingestion/surveys/{id}/files` | Raw aerial drone photos | Restricted to `ADMIN` / `AGRONOMIST` |
| `GET /api/v1/ingestion/surveys/{id}/files` | Image manifest & EXIF | Ownership verification |
| `GET /api/v1/maps/products/{id}/visualization` | GeoTIFF layer metadata | Ownership verification |
| `GET /api/v1/maps/tiles/{id}/{z}/{x}/{y}.png` | Live rendered map tiles | Dual Header & Query Token ownership guard |
| `GET /api/v1/maps/products/{id}/probe` | Precision spectral sampling | Ownership verification |
| `GET /api/v1/maps/products/{id}/diagnostics` | Scientific crop health summary | Ownership verification |
| `GET /api/v1/reports/{id}/download` | Agricultural PDF audit report | Server-side verified download |

---

## 5. Audit Findings & Action Items

1. **Password Hashing Missing**: The `hashed_password` column existed in `users`, but no bcrypt helper was wired in `app/core/security.py`.
2. **Missing Token Management**: PyJWT needed configuration with `HS256`, timing-safe signature checking, and expiration enforcement.
3. **Missing Auth Router**: Endpoints `/auth/login`, `/auth/logout`, `/auth/me`, `/auth/register-farmer`, and `/auth/assign-farm` needed implementation.
4. **Endpoint Ownership Guards**: Endpoints accepted raw UUIDs without verifying whether the requesting farmer owned the resource's ancestor farm.
5. **Tile Server Authentication**: MapLibre GL raster source requests tiles via native browser image tags without standard custom HTTP headers. A fallback token query parameter (`?token=...`) was needed in conjunction with session cookies.
6. **Frontend State & Navigation**: Navbar displayed static mock data; login page was absent; farmer portal needed empty states when unassigned.

All findings have been targeted and resolved in Phase 9.
