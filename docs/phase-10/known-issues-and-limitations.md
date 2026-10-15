# Known Limitations & Technical Constraints

**Document:** System Limitations & Operational Boundaries  
**Phase:** Phase 10  
**Status:** Documented  
**Date:** October 2026  

---

## 1. Overview

In accordance with strict engineering integrity standards, this document transparently identifies known technical limitations, resource requirements, and boundary conditions within the AgriDrone AutoMap platform.

---

## 2. Technical Limitations & Operational Boundaries

### 1. Photogrammetry Hardware Resource Requirements
- **Constraint:** Photogrammetric point cloud reconstruction, orthomosaic stitching, and digital surface model (DSM) generation are compute-intensive operations.
- **Impact:** Reconstructing surveys with >150 high-resolution drone photos requires a minimum of 16 GB to 32 GB RAM. Running large datasets on modest development laptops will result in NodeODM memory exhaustion errors.
- **Guidance:** For local testing, use surveys containing 20 to 50 photos. For production workloads, deploy NodeODM on dedicated high-memory cloud VMs (e.g., Azure D8s_v5 or compute-optimized nodes).

### 2. Basemap Connectivity in Offline / Air-Gapped Deployments
- **Constraint:** The interactive MapLibre map viewer loads open-source basemap tiles (OpenStreetMap / CartoDB) over the public Internet.
- **Impact:** In remote agricultural field stations operating without Internet connectivity, the background satellite/street map will appear blank, although the PostGIS field boundary polygons and local drone raster tiles will render normally.
- **Future Enhancement:** Package an offline vector MBTiles/PMTiles container (e.g. TileServer GL) for completely disconnected field environments.

### 3. Local Development Storage Fallback
- **Constraint:** When `AZURE_STORAGE_CONNECTION_STRING` is unconfigured, the platform defaults to local filesystem storage in `backend/storage/`.
- **Impact:** Local storage is intended solely for development, testing, and isolated edge stations. It lacks high-availability replication, geo-redundancy, and automatic lifecycle tiering.
- **Guidance:** Configure Microsoft Azure Blob Storage for all production deployments.

### 4. Distributed Rate Limiting
- **Constraint:** The brute-force protection rate limiter on `/api/v1/auth/login` tracks client IP attempts in application memory.
- **Impact:** On a horizontally autoscaled cluster with multiple backend pods behind a load balancer, each pod maintains its own rate limit counter.
- **Guidance:** In multi-pod production environments, configure the rate limiter to store sliding window timestamps in the existing Redis instance.

### 5. Multi-Language / International Font Support in PDF Reports
- **Constraint:** ReportLab PDF report generation uses standard Type-1 fonts (Helvetica, Times).
- **Impact:** Generating reports in non-Latin scripts (e.g., regional Indian scripts such as Devanagari for Marathi/Hindi farmer advisory reports) requires registering custom TrueType fonts (`TTFont`).
- **Guidance:** Documented for future localization sprints.
