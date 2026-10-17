# Known Limitations & Operational Considerations — WebODM Integration

This document enumerates technical, algorithmic, computational, and licensing limitations identified during the WebODM 3.3.1 source audit and integration into AgriDrone AutoMap.

---

## 1. WebODM Full Server vs. Standalone NodeODM Engine

AgriDrone AutoMap's `WebODMService` client can communicate with either:
1. **Full WebODM Server** (Django + Celery + PostgreSQL + Nginx, port 8000/3000):
   - Exposes project hierarchies (`/api/projects/`), stored presets (`/api/presets/`), and dynamic multi-node load balancing (`/api/processingnodes/`).
   - Requires JWT token authentication (`/api/token-auth/`).
2. **Standalone NodeODM Microservice** (Node.js engine, port 3000/3001):
   - Exposes single-node `/info`, `/task/new`, `/task/{uuid}/info`, and `/task/{uuid}/output`.
   - Lacks internal user accounts and multi-project grouping.
- **Handling in AgriDrone AutoMap**:
  - The health probe detects whether the target is WebODM or NodeODM. If NodeODM is detected, projects are managed entirely within AgriDrone's PostgreSQL database, and tasks are submitted directly to the NodeODM engine.

---

## 2. 3D Gaussian Splatting Hardware Boundaries

WebODM 3.3 introduces 3D Gaussian Splatting (`/splats/`):
- **Limitation**: Gaussian splatting cannot run on CPU-only worker nodes or standard Apple Silicon/integrated GPUs inside Docker. It strictly requires:
  - NVIDIA GPU with CUDA Compute Capability >= 7.0 (Turing, Ampere, Ada Lovelace, Hopper).
  - Minimum 8 GB VRAM.
  - NVIDIA Container Toolkit installed on the Docker host.
- **Operational Rule**: If running in a standard CPU environment, Gaussian splatting is disabled in the UI to prevent node task crashes.

---

## 3. Multispectral Radiometric Calibration Prerequisites

- **Limitation**: Enabling the `MULTISPECTRAL` preset (`radiometric-calibration: camera+sun`) will fail or yield inaccurate reflectance values if:
  - Aerial photographs lack embedded DLS (Downwelling Light Sensor) irradiance EXIF tags.
  - No calibrated reflectance panel images were captured prior to flight.
- **Agricultural Recommendation**: Ordinary RGB cameras (e.g. standard DJI Mini or Phantom 4) should use the `HIGH_RES` or `FAST` preset. The `MULTISPECTRAL` preset is intended exclusively for multispectral sensors (e.g. DJI Mavic 3 Enterprise Multispectral, MicaSense RedEdge-P, Parrot Sequoia).

---

## 4. Azure Blob Storage & WebODM Local File Cache

- **Limitation**: WebODM 3.3.1 has no native Azure Blob Storage driver. It writes working files and completed deliverables to local container storage (`/app/media/...`).
- **Operational Workflow**:
  - AgriDrone AutoMap's Celery worker bridges this gap: It streams raw photographs from Azure Blob Storage into WebODM, and upon completion, downloads `orthophoto.tif` and `dsm.tif`, translates them into Cloud-Optimized GeoTIFFs (COGs), and uploads them back to Azure Blob Storage.
  - If a WebODM container is destroyed or pruned, map tiles are rendered from the archived COG stored in Azure Blob Storage via AgriDrone's fallback raster pipeline.

---

## 5. WebODM Lightning Commercial Cloud Dependency

- WebODM includes optional hooks for **WebODM Lightning** (`cloud.webodm.net`), a commercial cloud processing service operated by UAV4GEO.
- WebODM Lightning requires paid credits.
- **AgriDrone AutoMap does not fake or simulate WebODM Lightning**. AgriDrone AutoMap uses local or self-hosted NodeODM clusters by default, preserving complete open-source self-sufficiency.

---

## 6. High-Resolution Compute & RAM Thresholds

| Dataset Size (Photos) | Minimum Host RAM | Recommended CPU | Estimated Runtime (High-Res) |
|:---:|:---:|:---:|:---:|
| **< 100 images** | 8 GB | 4 Cores | 8–15 minutes |
| **100 – 300 images** | 16 GB | 8 Cores | 25–45 minutes |
| **300 – 800 images** | 32 GB | 12+ Cores | 1.5–3 hours |
| **> 800 images** | 64 GB+ / ClusterODM | Multi-node Cluster | 3+ hours |

*For low-resource development environments, always select the **Fast Orthophoto** preset.*
