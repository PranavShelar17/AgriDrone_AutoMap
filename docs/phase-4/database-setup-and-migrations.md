# AgriDrone AutoMap — Database Setup & Migrations Guide
## Document Reference: `docs/phase-4/database-setup-and-migrations.md`
**Phase**: Phase 4 — Platform Foundation, Database Setup, Backend/Frontend Skeleton & Initial Testing  
**Status**: APPROVED DATABASE GUIDE  
**Version**: 1.0.0  

---

## 1. Database Architecture & Container Sizing

AgriDrone AutoMap utilizes **PostgreSQL 16** with the **PostGIS 3.4** spatial extension, running locally via Docker:
- **Container Name**: `agridrone_p4_db`
- **Image**: `postgis/postgis:16-3.4`
- **Host Port**: `5434` (mapped to internal container port `5432`)
- **Database Name**: `agridrone_db`
- **Database User**: `agridrone_user`
- **Password**: `local_pass`

---

## 2. PostGIS Verification

To verify that the PostGIS spatial engine is installed and active on the database container:

```powershell
# Using the backend python virtual environment
cd backend
.\.venv\Scripts\python.exe -c "
import psycopg2
conn = psycopg2.connect('postgresql://agridrone_user:local_pass@localhost:5434/agridrone_db')
cur = conn.cursor()
cur.execute('SELECT PostGIS_Full_Version();')
print(cur.fetchone()[0])
conn.close()
"
```
**Expected Output**:
`POSTGIS="3.4.3" [EXTENSION] PGSQL="160" GEOS="3.12.1" PROJ="9.4.0" LIBXML="2.9.14" LIBJSON="0.16" ...`

---

## 3. Alembic Migration Workflow

Database schema evolution is managed through **Alembic** configured in `backend/alembic.ini` and `backend/alembic/env.py`.

### 3.1. Applying Migrations
To apply all pending migrations up to the latest revision:
```powershell
cd backend
.\.venv\Scripts\alembic.exe upgrade head
```

### 3.2. Inspecting Current Database Revision
To check the currently applied revision in the database:
```powershell
.\.venv\Scripts\alembic.exe current
```
**Current Baseline Revision**: `001_initial_core_schema (head)`

### 3.3. Reverting Migrations (Rollback)
To revert the most recent migration step:
```powershell
.\.venv\Scripts\alembic.exe downgrade -1
```

### 3.4. Generating New Migrations
When SQLAlchemy models are modified in `backend/app/models/`:
```powershell
.\.venv\Scripts\alembic.exe revision --autogenerate -m "describe_schema_change"
```

---

## 4. Tables Created by Initial Core Migration (`001_initial_core_schema.py`)

| Table Name | Description | Key Spatial / Data Features |
| :--- | :--- | :--- |
| **`users`** | Authentication & RBAC accounts | `role` enum (`ADMIN`, `AGRONOMIST`, `FARMER`) |
| **`farms`** | Agricultural holdings | `boundary_geom` (`GEOMETRY(POLYGON, 4326)`) |
| **`fields`** | Discrete farm parcels | `boundary_geom` (`GEOMETRY(POLYGON, 4326)`) |
| **`surveys`** | Drone flight missions | `coverage_geom` (`GEOMETRY(POLYGON, 4326)`) |
| **`survey_files`** | Page 1 uploaded imagery & GeoTIFFs | File size, MIME, MD5, and EXIF metadata JSONB |
| **`photogrammetry_tasks`**| Page 2 WebODM 3D reconstruction jobs | Parameters, progress percentage, current stage |
| **`task_logs`** | WebODM console log streaming | Monospace log lines with timestamp |
| **`algorithms`** | Vegetation index definitions | Mathematical formula specifications (JSONB) |
| **`algorithm_jobs`** | Page 3 index calculations | Status, execution parameters, error messages |
| **`map_products`** | Pages 2, 3, 4 published rasters | `extent_geom` (`POLYGON, 4326`), COG status, CRS |
| **`zonal_statistics`** | Page 5 vigor distribution | Area (ha), percentage, vigor classification |
| **`reports`** | Page 5 compiled PDF reports | Report number, file size, Azure blob URI |
| **`audit_logs`** | Compliance & audit trail | User ID, action, entity UUID, client IP, user agent |

---

## 5. Safely Resetting Local Development Data

To completely reset the local database back to a clean state:
```powershell
# 1. Stop and remove the database container and volume
docker-compose down -v

# 2. Re-create the empty container
docker-compose up -d db redis

# 3. Re-apply Alembic migrations from scratch
cd backend
.\.venv\Scripts\alembic.exe upgrade head
```
