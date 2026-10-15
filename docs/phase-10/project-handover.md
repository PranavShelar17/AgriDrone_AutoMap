# AgriDrone AutoMap — Final Project Handover Document

**Document:** Comprehensive System Handover & Operational Manual  
**Milestone:** Phase 10 Final Handover  
**Platform Version:** 1.0.0-rc1  
**Status:** Complete & Ready for Production Deployment  
**Date:** October 2026  

---

## 1. System Overview & Core Architecture

**AgriDrone AutoMap** is an agricultural drone mapping and geospatial analysis platform. The system processes raw drone photography into photogrammetric orthomosaics and digital surface models, derives calibrated multispectral vegetation indices (NDVI, NDRE, VARI, GLI, GNDVI, SAVI), serves hardware-accelerated slippy map tiles using MapLibre GL JS, and generates auditable agronomic PDF reports.

The application strictly adheres to a **Five-Page Functional Architecture**:
1. **Admin Dashboard & Drone Image Ingestion (`/admin/dashboard`):** Digitizes PostGIS farm/field boundaries, uploads raw drone photos, extracts GPS EXIF tags, validates pre-stitched GeoTIFFs, and gates processing eligibility.
2. **WebODM Photogrammetry Processing (`/admin/photogrammetry`):** Monitors NodeODM processing nodes, dispatches asynchronous 2D/3D reconstruction jobs via Celery, streams live console logs, and registers output orthophotos.
3. **Algorithm & Multi-Map Generation (`/admin/algorithms`):** Validates multiband raster mappings, executes scientific spectral math in background workers, and computes 5-tier canopy vigour zonal statistics.
4. **Secure Farmer Portal (`/portal/surveys`):** Multi-tenant interactive map viewer powered by MapLibre GL JS, featuring layer switching, continuous legends, opacity blending, dual synchronized comparison swipe, and point pixel probing.
5. **Diagnostics & Actionable Insights (`/portal/diagnostics`):** Displays data-derived statistical cards (mean, median, std, valid coverage area), canopy health zoning charts, agronomic safeguards, and downloadable PDF reports.

---

## 2. Technology Stack Summary

- **Frontend:** Next.js 14.2 (App Router), TypeScript 5.6, Tailwind CSS 3.4.
- **Backend:** Python 3.11+, FastAPI 0.143, Uvicorn 0.54.
- **Database:** PostgreSQL 16 with native **PostGIS 3.4** spatial extension.
- **ORM & Migrations:** SQLAlchemy 2.1, GeoAlchemy2 0.20, Alembic 1.20.
- **Task Broker & Queues:** Redis 7.2, Celery 5.6.
- **GIS & Photogrammetry:** GDAL, Rasterio 1.5, NumPy 2.x, WebODM / NodeODM.
- **Interactive Maps:** MapLibre GL JS 6.14.
- **Object Storage:** Microsoft Azure Blob Storage (official `azure-storage-blob` SDK) with local dev fallback.
- **Reports:** ReportLab 4.x.
- **Containers:** Docker Engine & Docker Compose.

---

## 3. Local Setup & Execution Guide

### 1. Database & Broker Services (Docker)
```bash
# Start PostgreSQL PostGIS (port 5434) and Redis (port 6380)
docker compose up -d db redis
```

### 2. Backend API Service
```bash
cd backend
# Activate virtual environment
.venv\Scripts\activate

# Apply all database migrations
alembic upgrade head

# Seed initial evaluation accounts
python scripts/seed_phase9_users.py

# Start FastAPI server (http://localhost:8005)
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```

### 3. Background Celery Worker
```bash
cd backend
.venv\Scripts\activate
# Start Celery worker consuming both photogrammetry and raster queues
celery -A app.core.celery_app.celery_app worker -l info -Q photogrammetry,raster_analytics --pool=solo
```

### 4. Frontend Web Application
```bash
cd frontend
# Install dependencies & run development server (http://localhost:3005)
npm run dev
```

---

## 4. Evaluation Credentials Matrix

The following accounts are pre-seeded in the database:

| Role | Email Address | Password | Permissions & Scope |
| :--- | :--- | :--- | :--- |
| **System Admin** | `admin@agridrone.local` | `Admin@AgriDrone2026!` | Global access to all 5 functional pages, image ingestion, photogrammetry & algorithms |
| **Farmer (Baramati)** | `farmer@greenvalley.local` | `Farmer@AgriDrone2026!` | Restricted strictly to Baramati Precision Farm boundaries, rasters & diagnostics |
| **Farmer (Ingestion)**| `farmer2@sunrise.local` | `Farmer2@AgriDrone2026!` | Restricted strictly to Ingestion Test Farm |

---

## 5. Verification & Test Commands

```bash
# 1. Run Complete Backend Test Suite (80/80 Passed)
cd backend
.venv\Scripts\pytest -v

# 2. Run Frontend Production Compile (10/10 Routes Passed)
cd frontend
npm run build

# 3. Check Database Migration Status (Head verified)
cd backend
.venv\Scripts\alembic current
```

---

## 6. Production Deployment Readiness

The platform includes production-ready multi-stage Dockerfiles and orchestration manifests:
- `backend/Dockerfile.prod`: Python 3.11-slim with non-root user `appuser` (UID 10001).
- `frontend/Dockerfile.prod`: Next.js 14 multi-stage build with non-root user `nextjs` (UID 1001).
- `docker-compose.prod.yml`: Multi-container production stack with persistent volumes and health probes.
- `.github/workflows/ci.yml`: Automated CI/CD pipeline running backend tests, frontend builds, and migration checks.

---

## 7. Known Operational Limitations

1. **Photogrammetry RAM:** NodeODM reconstructions with >150 images require at least 16GB-32GB RAM. Use 20-50 photos for local testing.
2. **Air-Gapped Basemaps:** MapLibre default basemap requires Internet connectivity; for offline field operations, configure a local vector tile server.
3. **Storage Configuration:** In production, set `AZURE_STORAGE_CONNECTION_STRING` to enable durable cloud replication.

---

## 8. Final Handover Status & Next Actions

- **Phase 10 Status:** **COMPLETE**.
- **Application Status:** **Ready for Staging & Production Deployment**.
- **Pending Action:** In accordance with the project rules, **no cloud hosting has been provisioned, no DNS changes have been made, and no cloud costs have been incurred**. Please review the hosting recommendation in [docs/phase-10/hosting-and-deployment-decision.md](file:///c:/Users/Admin/Desktop/new%20dron%202/docs/phase-10/hosting-and-deployment-decision.md) and indicate when you are ready to authorize the production deployment target.
