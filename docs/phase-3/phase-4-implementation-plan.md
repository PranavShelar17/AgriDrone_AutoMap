# AgriDrone AutoMap — Phase 4 Implementation Plan
## Document Reference: `docs/phase-3/phase-4-implementation-plan.md`
**Phase**: Phase 3 Deliverable (Planning for Phase 4)  
**Status**: APPROVED IMPLEMENTATION PLAN  
**Version**: 1.0.0  

---

## 1. Phase 4 Objective & Scope

**Phase 4: Platform Foundation & Development Environment Setup** is the engineering foundation phase of AgriDrone AutoMap.

Its sole purpose is to establish the running development environment, initialize the production-aligned monorepo structure, establish the PostgreSQL/PostGIS database with automated migrations, stand up the FastAPI skeleton with health endpoints, wire the Next.js frontend to the backend, and configure Docker Compose with automated test suites.

> [!IMPORTANT]
> This document constitutes the **technical plan only**. In accordance with Phase 3 constraints, **no Phase 4 implementation tasks will be executed** until the user reviews and formally approves the Phase 3 deliverables.

---

## 2. Step-by-Step Implementation Sequence

```
Step 1: Workspace Organization & Monorepo Directory Setup
         │
         ▼
Step 2: Environment Configuration (.env.example & Settings)
         │
         ▼
Step 3: Docker Compose Multi-Container Orchestration (DB, Redis, WebODM, API)
         │
         ▼
Step 4: Database Initialization & Alembic PostGIS Schema Migration
         │
         ▼
Step 5: FastAPI Application Skeleton & Health Endpoints
         │
         ▼
Step 6: Frontend Foundation Alignment (Wiring Next.js to FastAPI /api/v1)
         │
         ▼
Step 7: Automated Test Suite & Continuous Integration Setup
         │
         ▼
Step 8: Foundation Verification & Quality Review
```

---

### Step 1: Workspace Organization & Monorepo Directory Setup
- Consolidate active project directories into clean `frontend/`, `backend/`, `docker/`, and `docs/` roots.
- Ensure the verified visual prototype (`prototype/`) is safely preserved as a design benchmark.
- Initialize Python virtual environment with pinned dependencies (`fastapi`, `uvicorn`, `sqlalchemy`, `geoalchemy2`, `alembic`, `celery`, `redis`, `azure-storage-blob`, `pydantic-settings`).
- Initialize Next.js dependencies with pinned versions (`next@14.2.18`, `react@18.3.1`, `lucide-react`, `tailwindcss@3.4.14`).

### Step 2: Environment Configuration & Secret Management
- Author `.env.example` defining all required configuration variables:
  - Database connection strings (`DATABASE_URL=postgresql://...`)
  - Redis message broker URL (`REDIS_URL=redis://...`)
  - Azure storage credentials and container names
  - WebODM cluster URL (`WEBODM_API_URL=http://nodeodm:3000`)
  - Secret key and JWT parameters
- Create `backend/app/core/config.py` using Pydantic `BaseSettings` with strict type validation.

### Step 3: Docker Compose Multi-Container Orchestration
- Build `docker/docker-compose.yml` orchestrating all six core services:
  1. `db`: `postgis/postgis:15-3.3` with healthcheck
  2. `redis`: `redis:7-alpine` with healthcheck
  3. `backend`: Python 3.11 with FastAPI and live reload
  4. `celery_worker`: Celery worker with GDAL 3.8 and Rasterio
  5. `nodeodm`: `opendronemap/nodeodm:latest`
  6. `frontend`: Next.js 14 App Router on port 3005
- Configure persistent Docker named volumes for PostgreSQL, Redis, and NodeODM data.

### Step 4: Database Initialization & PostGIS Migration
- Configure `alembic.ini` and `backend/alembic/env.py` to import SQLAlchemy models.
- Create initial migration revision `0001_initial_schema.py`:
  - Execute `CREATE EXTENSION IF NOT EXISTS postgis;`
  - Create `users`, `farms`, `fields`, `surveys`, `survey_files`, `photogrammetry_tasks`, `map_products`, `algorithm_jobs`, `reports`, and `audit_logs` tables.
  - Create GIST spatial indexes on `fields.boundary_geom` and `map_products.extent_geom`.
- Verify database migration execution (`alembic upgrade head`) against the PostGIS container.

### Step 5: FastAPI Application Skeleton & Core Endpoints
- Implement `backend/app/main.py` with:
  - Global CORS middleware (whitelisting `http://localhost:3000` and `http://localhost:3005`)
  - Global exception handlers returning standardized error envelopes
  - Structured request logging middleware
  - Sub-router mounting under `/api/v1` prefix
- Implement `/api/v1/health` and `/api/v1/health/readiness` endpoints verifying active connections to PostgreSQL and Redis.

### Step 6: Frontend Foundation & API Client Alignment
- Establish the production frontend in `frontend/` leveraging the approved Phase 2 design system and components.
- Implement `frontend/lib/api.ts` configuring an Axios / Fetch HTTP client pointing to `process.env.NEXT_PUBLIC_API_URL`.
- Wire the top navigation status indicator (`pulse-active`) to poll `/api/v1/cluster/status` or `/api/v1/health`.

### Step 7: Automated Test Suite & CI Setup
- Establish `backend/tests/` with `pytest`, `pytest-asyncio`, and `httpx`.
- Implement `tests/conftest.py` providing an isolated SQLite/PostGIS test database session and test HTTP client.
- Implement initial tests:
  - `test_health.py`: Validates `/api/v1/health` returns `200 OK`.
  - `test_db_connection.py`: Validates PostGIS spatial extension functions (`SELECT PostGIS_Version();`).
  - `test_pydantic_schemas.py`: Validates input validation schemas.
- Implement frontend check: `npm run build` compiling all routes with zero TypeScript or ESLint errors.

---

## 3. Measurable Phase 4 Completion Criteria

To declare Phase 4 complete, the following criteria must be satisfied and verified:
1. Running `docker-compose up -d` successfully starts all containers (`db`, `redis`, `backend`, `celery_worker`, `frontend`, `nodeodm`).
2. Visiting `http://localhost:8000/api/v1/health` returns HTTP `200 OK` with database and redis connectivity confirmed.
3. Visiting `http://localhost:8000/docs` renders the interactive OpenAPI (Swagger) documentation with all `/api/v1` route groups.
4. Running `alembic upgrade head` executes with zero SQL errors and creates all 11 PostGIS tables and GIST indexes.
5. Visiting `http://localhost:3005` in Chrome loads the AgriDrone AutoMap frontend without console errors.
6. Running `pytest` in `backend/` passes all initial health and schema tests.
7. Running `npm run build` in `frontend/` compiles with zero errors.
