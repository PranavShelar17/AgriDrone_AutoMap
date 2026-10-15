# AgriDrone AutoMap — Local Development Guide
## Document Reference: `docs/phase-4/local-development-guide.md`
**Phase**: Phase 4 — Platform Foundation, Database Setup, Backend/Frontend Skeleton & Initial Testing  
**Status**: APPROVED OPERATIONAL GUIDE  
**Version**: 1.0.0  

---

## 1. Prerequisites

Before running AgriDrone AutoMap locally, verify the following dependencies:
- **Operating System**: Windows 10/11, macOS, or Linux.
- **Node.js**: `v18.17.0+` or `v20.x` (verified with Node `v24.21.0` and npm `11.19.0`).
- **Python**: `3.11+` (verified with Python `3.14`).
- **Docker Desktop**: Installed and running (for PostGIS and Redis containers).
- **Git**: For source version control.

---

## 2. Port Allocation Map (Avoiding Local Collisions)

To prevent port conflicts with existing Docker projects (such as SoilPilot on 3000/5432/8000), AgriDrone AutoMap uses dedicated non-conflicting ports:

| Service | Local Host Port | Container Port | Purpose |
| :--- | :---: | :---: | :--- |
| **Next.js Frontend** | **`3005`** | `3005` | Five-page user interface & launchpad hub |
| **FastAPI Backend** | **`8005`** | `8000` | REST API, OpenAPI docs, and health checks |
| **PostgreSQL / PostGIS** | **`5434`** | `5432` | Spatial vector database (`agridrone_db`) |
| **Redis Broker** | **`6380`** | `6379` | Message broker & cache |

---

## 3. Step-by-Step Local Startup Instructions

### Step 1: Start Database & Redis (Docker)
Open PowerShell or your terminal in the project root:
```powershell
# Start PostGIS and Redis containers in background
docker-compose up -d db redis

# Verify both containers are running and healthy
docker ps --filter "name=agridrone_p4"
```

### Step 2: Set Up Backend Environment & Apply Migrations
```powershell
# 1. Navigate to backend directory
cd backend

# 2. Activate Python virtual environment
.\.venv\Scripts\Activate.ps1

# 3. Copy environment configuration (if not already present)
cp .env.example .env

# 4. Apply database migrations to PostGIS
alembic upgrade head

# 5. Start the FastAPI development server on port 8005
uvicorn app.main:app --host 0.0.0.0 --port 8005 --reload
```
The backend API is now running at **`http://localhost:8005`**.  
Interactive Swagger documentation is available at **`http://localhost:8005/docs`**.

### Step 3: Start Frontend (Next.js)
Open a second PowerShell window:
```powershell
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies (if needed)
npm install

# 3. Start the Next.js development server on port 3005
npm run dev
```
The web frontend is now running at **`http://localhost:3005`**.

---

## 4. Local Service URLs & Endpoints

| View / Resource | URL | Description |
| :--- | :--- | :--- |
| **Launchpad Hub** | [http://localhost:3005](http://localhost:3005) | Overview directory with links to all 5 functional pages |
| **Page 1: Ingestion** | [http://localhost:3005/admin/dashboard](http://localhost:3005/admin/dashboard) | Drone image upload dropzone & pre-flight EXIF validation |
| **Page 2: Photogrammetry** | [http://localhost:3005/admin/photogrammetry](http://localhost:3005/admin/photogrammetry) | WebODM task parameters, cluster status & terminal logs |
| **Page 3: Algorithms** | [http://localhost:3005/admin/algorithms](http://localhost:3005/admin/algorithms) | Band mapping matrix, VARI/NDVI index calculation |
| **Page 4: Farmer Portal** | [http://localhost:3005/portal/surveys](http://localhost:3005/portal/surveys) | Interactive MapLibre canvas, swipe comparison, probe tool |
| **Page 5: Diagnostics** | [http://localhost:3005/portal/diagnostics](http://localhost:3005/portal/diagnostics) | Zonal canopy health charts, disclaimers & PDF export |
| **API Swagger Docs** | [http://localhost:8005/docs](http://localhost:8005/docs) | Interactive OpenAPI test harness |
| **API Liveness Probe** | [http://localhost:8005/api/v1/health](http://localhost:8005/api/v1/health) | Instant 200 OK process check |
| **API Readiness Probe** | [http://localhost:8005/api/v1/health/readiness](http://localhost:8005/api/v1/health/readiness) | Confirms live PostGIS and Redis connectivity |

---

## 5. Running Automated Tests

```powershell
# Run backend pytest suite (Unit, Integration, Health, Models)
cd backend
.\.venv\Scripts\pytest.exe -v

# Run frontend build and type-checking
cd ..\frontend
npm run build
```

---

## 6. Troubleshooting Common Issues

### Issue 1: "FATAL: password authentication failed for user agridrone_user"
- Verify that `DATABASE_URL` in `backend/.env` points to port `5434` with user `agridrone_user` and password `local_pass`.
- If an existing container is using different credentials, run `docker-compose down -v` and `docker-compose up -d db`.

### Issue 2: "Port 3005 is already in use"
- Check running processes: `Get-Process -Id (Get-NetTCPConnection -LocalPort 3005).OwningProcess`
- Stop the old background task or kill the process: `Stop-Process -Id <PID> -Force`

---

## 7. Shutdown & Cleanup Instructions

```powershell
# Stop Docker containers (preserves database data)
docker-compose stop

# Completely remove containers and networks
docker-compose down

# Reset local database (WARNING: destroys all test tables and records)
docker-compose down -v
```
