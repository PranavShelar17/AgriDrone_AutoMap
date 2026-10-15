# AgriDrone AutoMap — WebODM Architecture & Setup Guide
## Document Reference: `docs/phase-6/webodm-architecture-and-setup.md`
**Phase**: Phase 6 — WebODM / OpenDroneMap Integration & Drone Photogrammetry Processing  
**Status**: APPROVED TECHNICAL SPECIFICATION  
**Version**: 1.0.0  

---

## 1. System Topology & Architectural Separation

Photogrammetric reconstruction (Structure-from-Motion and Multi-View Stereo) is computationally intensive, requiring significant multi-threaded CPU cycles and substantial RAM. AgriDrone AutoMap strictly enforces architectural separation between the user-facing web tier and photogrammetric compute engines:

```
┌─────────────────────────┐          HTTP/JSON          ┌─────────────────────────┐
│     Next.js Frontend    │ ──────────────────────────> │   FastAPI Web Backend   │
│       (Port 3005)       │ <────────────────────────── │       (Port 8005)       │
└─────────────────────────┘                             └───────────┬─────────────┘
                                                                    │
                                                 Dispatch / Poll    │ SQL Queries
                                                                    ▼
                                                        ┌─────────────────────────┐
                                                        │   PostgreSQL + PostGIS  │
                                                        │       (Port 5434)       │
                                                        └─────────────────────────┘
                                                                    ▲
                                                                    │ State sync
                                                                    │
┌─────────────────────────┐          Redis Queue        ┌───────────┴─────────────┐
│    WebODM / NodeODM     │ <────────────────────────── │      Celery Worker      │
│   Photogrammetry Node   │ ──────────────────────────> │  (app.tasks.photogram.) │
│       (Port 3001)       │     Raw Photos / Outputs    └─────────────────────────┘
└─────────────────────────┘
```

### Key Architectural Boundaries:
1. **Frontend Isolation**: The Next.js frontend **never** communicates directly with WebODM or NodeODM. All interactions flow through FastAPI endpoints under `/api/v1/photogrammetry/`.
2. **Credential Security**: WebODM authentication credentials (tokens or passwords) remain strictly server-side in backend environment variables.
3. **Queue-Backed Decoupling**: Drone photogrammetry tasks are dispatched through Celery distributed workers backed by Redis, preventing long-running photogrammetric reconstructions from blocking HTTP request threads.
4. **Resilient Local Fallback**: When running in single-process development environments without a separate Celery worker process, an asynchronous daemon thread coordinator automatically handles background polling and state updates.

---

## 2. WebODM / NodeODM Deployment Options

AgriDrone AutoMap supports two deployment configurations for the photogrammetry processing tier:

### Option A: Direct NodeODM Container (Recommended for Local Development & CI)
NodeODM is the high-performance, lightweight headless REST processing engine powering OpenDroneMap. It requires no database and operates on port `3000` (mapped to `3001` on host):

```bash
docker run -d --name agridrone_nodeodm -p 3001:3000 opendronemap/nodeodm:latest
```

Or using Docker Compose:
```bash
docker compose --profile photogrammetry up -d nodeodm
```

### Option B: Full WebODM Cluster
For multi-node production clusters with web management:
```bash
git clone https://github.com/OpenDroneMap/WebODM --config core.autocrlf=input --depth 1
cd WebODM
./webodm.sh start --port 3001
```

---

## 3. Connectivity Verification

Once the container is launched, test connectivity from PowerShell or Bash:
```powershell
# Probe NodeODM / WebODM endpoint
curl http://localhost:3001/info
```
Expected response:
```json
{
  "version": "2.8.5",
  "taskQueueCount": 0,
  "availableMemory": 17179869184
}
```

Or probe via the AgriDrone API:
```powershell
curl http://localhost:8005/api/v1/photogrammetry/cluster-status
```
Expected response:
```json
{
  "cluster_status": "ONLINE",
  "is_connected": true,
  "api_url": "http://localhost:3001",
  "engine": "NodeODM",
  "active_nodes": 1,
  "total_nodes": 1,
  "available_ram_gb": 16.0
}
```
