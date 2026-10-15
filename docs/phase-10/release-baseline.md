# Release Baseline & System Specifications

**Document:** Production Release Baseline — AgriDrone AutoMap  
**Version:** 1.0.0 (Release Candidate)  
**Status:** Approved  
**Date:** October 2026  

---

## 1. Runtime & Infrastructure Specifications

| Component | Technology | Target Release Version | Execution Environment |
| :--- | :--- | :--- | :--- |
| **Frontend Framework** | Next.js (App Router) | `14.2.18` | Node.js `20.x LTS` |
| **Frontend Language** | TypeScript | `5.6.3` | Strict mode enabled |
| **Frontend Styling** | Tailwind CSS | `3.4.14` | Autoprefixer + PostCSS |
| **Backend Framework** | FastAPI | `0.143.0` | Python `3.11+` |
| **ASGI Server** | Uvicorn | `0.54.0` | uvloop / standard workers |
| **Database Engine** | PostgreSQL | `16.x` | Port `5434` (dev) / `5432` (prod) |
| **Spatial Engine** | PostGIS | `3.4` | Geometry EPSG:4326 |
| **Database ORM** | SQLAlchemy | `2.1.4` | Alembic `1.20.0` migrations |
| **In-Memory Broker** | Redis | `7.2` | Port `6380` (dev) / `6379` (prod) |
| **Task Queue** | Celery | `5.6.3` | Queues: `photogrammetry`, `raster_analytics` |
| **GIS Processing** | Rasterio + NumPy | Rasterio `1.5.2`, NumPy `2.x` | Cloud-Optimized GeoTIFF generation |
| **Mapping Engine** | MapLibre GL JS | `6.14.0` | WebGL hardware-accelerated |
| **Cloud Storage** | Azure Blob Storage | `12.31.0` | Official `azure-storage-blob` SDK |
| **PDF Reporting** | ReportLab | `4.x` | Standardized agronomic templates |

---

## 2. Port Allocation Matrix (Anti-Collision Architecture)

To ensure zero conflicts with default local databases (such as system Postgres on 5432 or default Redis on 6379), dedicated development ports are established:

```
┌─────────────────────────────────────────────────────────────┐
│                 AgriDrone AutoMap Ports                     │
├──────────────────────────┬──────────────┬───────────────────┤
│ Service                  │ Host Port    │ Internal Port     │
├──────────────────────────┼──────────────┼───────────────────┤
│ Next.js Frontend         │ 3005         │ 3005              │
│ FastAPI Backend          │ 8005         │ 8000              │
│ PostgreSQL / PostGIS     │ 5434         │ 5432              │
│ Redis Broker & Cache     │ 6380         │ 6379              │
│ WebODM / NodeODM Node    │ 3001         │ 3000              │
└──────────────────────────┴──────────────┴───────────────────┘
```

---

## 3. Database Migration Baseline

The database schema is managed via Alembic. The release candidate baseline is verified at revision:

- **Current Revision:** `003_algorithms_phase7`
- **Revision History:**
  1. `001_initial_core_schema`: Users, Farms, Fields, Surveys, SurveyFiles, AuditLogs, Reports.
  2. `002_photogrammetry_phase6`: PhotogrammetryTasks, WebODM options, task tracking.
  3. `003_algorithms_phase7`: AlgorithmJobs, MapProducts, ZonalStatistics, continuous colormaps.

### Migration Validation Command:
```bash
cd backend
.venv\Scripts\alembic current
# Output: 003_algorithms_phase7 (head)
```

---

## 4. Standard Build & Test Commands

### 1. Backend Service & Tests
```bash
cd backend
# Run automated test suite (80 tests)
.venv\Scripts\pytest -v

# Run local API server
.venv\Scripts\uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload

# Run Celery background worker
.venv\Scripts\celery -A app.core.celery_app.celery_app worker -l info -Q photogrammetry,raster_analytics
```

### 2. Frontend Build & Dev
```bash
cd frontend
# Install dependencies
npm ci

# Run development server
npm run dev

# Run production build
npm run build

# Start production server
npm run start
```
