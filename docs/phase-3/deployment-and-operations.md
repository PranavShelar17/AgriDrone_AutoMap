# AgriDrone AutoMap — Deployment & Operations Architecture
## Document Reference: `docs/phase-3/deployment-and-operations.md`
**Phase**: Phase 3 — System Architecture, Technical Validation & Implementation Blueprint  
**Status**: APPROVED ARCHITECTURE BLUEPRINT  
**Version**: 1.0.0  

---

## 1. Local Development Environment (Docker Compose)

For local development and continuous integration testing, the entire platform runs via a unified, multi-service `docker-compose.yml`:

```yaml
version: '3.8'

services:
  db:
    image: postgis/postgis:15-3.3
    environment:
      POSTGRES_DB: agridrone_db
      POSTGRES_USER: agridrone_admin
      POSTGRES_PASSWORD: dev_secret_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U agridrone_admin -d agridrone_db"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://agridrone_admin:dev_secret_password@db:5432/agridrone_db
      - REDIS_URL=redis://redis:6379/0
      - AZURE_STORAGE_CONNECTION_STRING=UseDevelopmentStorage=true
      - WEBODM_API_URL=http://nodeodm:3000
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery_worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.workers.celery_app worker --loglevel=info -c 2
    environment:
      - DATABASE_URL=postgresql://agridrone_admin:dev_secret_password@db:5432/agridrone_db
      - REDIS_URL=redis://redis:6379/0
      - AZURE_STORAGE_CONNECTION_STRING=UseDevelopmentStorage=true
      - WEBODM_API_URL=http://nodeodm:3000
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  nodeodm:
    image: opendronemap/nodeodm:latest
    ports:
      - "3001:3000"
    volumes:
      - nodeodm_data:/var/www/data

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3005:3005"
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
    depends_on:
      - backend

volumes:
  postgres_data:
  redis_data:
  nodeodm_data:
```

---

## 2. Production Service Topology (Target Cloud Architecture)

In production, the microservices are isolated across managed Azure cloud infrastructure:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           PUBLIC INTERNET / TRAFFIC                         │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTPS (Port 443)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AZURE APPLICATION GATEWAY / WAF                        │
│   - TLS 1.3 Termination                 - DDoS Protection                   │
│   - Path Routing: /api/* -> Backend     - Web Application Firewall          │
└──────────────────────┬──────────────────────────────────────┬───────────────┘
                       │                                      │
                       ▼                                      ▼
┌──────────────────────────────────────────┐ ┌────────────────────────────────┐
│      AZURE CONTAINER APPS (Frontend)     │ │ AZURE CONTAINER APPS (Backend) │
│      - Next.js 14 Standalone App         │ │ - FastAPI Stateless API Cluster│
│      - Auto-scales: 2 to 10 replicas     │ │ - Auto-scales: 2 to 10 replicas│
└──────────────────────────────────────────┘ └────────┬───────────────────────┘
                                                      │
         ┌────────────────────────────────────────────┼───────────────────────┐
         │                                            │                       │
         ▼                                            ▼                       ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────┐
│  AZURE DATABASE  │ │  AZURE CACHE FOR │ │  CELERY WORKER   │ │   WEBODM     │
│  FOR POSTGRESQL  │ │      REDIS       │ │     CLUSTER      │ │ COMPUTE VM   │
│ (PostGIS Active) │ │ (Managed Redis 7)│ │  (Azure Container│ │  SCALE SET   │
│ - Multi-AZ HA    │ │ - In-Memory Bus  │ │   Apps / KEDA)   │ │- GPU/High-CPU│
└──────────────────┘ └──────────────────┘ └──────────────────┘ └──────────────┘
```

---

## 3. Recommended Production Hardware Sizing & Capacity Planning

| Service | Recommended Sizing | vCPU | RAM | Disk / Storage | Scaling Rule |
| :--- | :--- | :---: | :---: | :--- | :--- |
| **Next.js Frontend** | Container Apps | 0.5 | 1.0 GB | Stateless | Auto-scale on HTTP concurrent requests (> 100) |
| **FastAPI Backend** | Container Apps | 1.0 | 2.0 GB | Stateless | Auto-scale on HTTP concurrent requests (> 80) |
| **PostgreSQL / PostGIS** | Flexible Server (D4ds_v5) | 4 | 16 GB | 256 GB NVMe SSD | Auto-grow storage; Read replicas for analytics |
| **Redis Broker** | Azure Cache for Redis (Standard) | Shared | 2.5 GB | In-memory | Scale up based on memory threshold (> 70%) |
| **Celery Raster Worker** | Container Apps (with KEDA) | 2.0 | 4.0 GB | 50 GB scratch | Auto-scale based on Redis queue depth (`raster_compute > 5`) |
| **WebODM NodeODM Worker** | Standard_D8s_v5 (Compute Optimized) | 8 | 32 GB | 500 GB Premium SSD | Manual / Scheduled scale based on survey volume |

---

## 4. Health Checks & Observability

### 4.1. Health Endpoints
- **Liveness Probe**: `GET /api/v1/health` $\to$ Returns `200 OK` if the Python interpreter and ASGI server are responsive.
- **Readiness Probe**: `GET /api/v1/health/readiness` $\to$ Executes a lightweight `SELECT 1` on PostgreSQL and a `PING` on Redis. Returns `200 OK` only when both persistence layers are operational.

### 4.2. Logging & Metrics
- All backend services output **structured JSON logs** to `stdout`:
  ```json
  {"timestamp": "2026-10-14T15:20:00Z", "level": "INFO", "service": "api", "request_id": "req-102", "path": "/api/v1/algorithms/jobs", "status_code": 202, "duration_ms": 42.1}
  ```
- Application metrics (queue depth, processing times, HTTP error rates) are scraped via Prometheus endpoints and visualized in Azure Monitor / Grafana.

---

## 5. Disaster Recovery, Backups & Business Continuity

1. **Database Recovery (RPO < 5 mins, RTO < 30 mins)**:
   - Automated continuous backups with 35-day point-in-time restore (PITR) enabled on Azure Database for PostgreSQL.
   - Zone-redundant high availability (HA) configured with standby replica in secondary availability zone.
2. **Binary Blob Recovery (RPO 0, RTO < 1 hour)**:
   - Azure Blob Storage configured with Geo-Redundant Storage (GRS).
   - Blob Soft Delete enabled (14-day retention).
3. **Infrastructure as Code (IaC)**:
   - All cloud environments are defined declaratively via Terraform / Bicep to enable rapid, deterministic recreation in disaster recovery scenarios.
