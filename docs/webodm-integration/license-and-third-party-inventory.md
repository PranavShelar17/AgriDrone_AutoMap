# Software License & Third-Party Inventory — AGPL-3.0 & Trademark Compliance

**Primary Upstream Software**: WebODM (OpenDroneMap Project)  
**Upstream Version**: 3.3.1  
**Upstream License**: **GNU Affero General Public License v3.0 (AGPL-3.0)**  
**Trademark Steward**: UAV4GEO (https://uav4geo.com)  
**Host Application**: AgriDrone AutoMap  

---

## 1. AGPL-3.0 Compliance & Architectural Integration Boundary

WebODM is licensed under the GNU Affero General Public License v3.0 (`WebODM-master/WebODM-master/LICENSE.md`). Section 13 of the AGPL-3.0 contains specific provisions regarding network interaction with modified versions of the program.

### 1.1 Architectural Isolation Strategy
To maintain legal integrity, avoid license contamination, and protect proprietary farm management intellectual property:
1. **Separate Service Integration**:
   - WebODM runs as a **standalone, independent network service** inside its own containerized runtime (or remote cluster).
   - AgriDrone AutoMap communicates with WebODM solely over standard HTTP/REST network protocols using public, documented endpoints (`/api/token-auth/`, `/api/projects/`, `/api/tasks/`).
2. **Zero Code Copying**:
   - No Django models, viewsets, or database migrations from WebODM have been copied or embedded into the AgriDrone FastAPI codebase.
   - All AgriDrone AutoMap frontend components (Next.js 14 App Router, TypeScript, Tailwind CSS) and backend services (FastAPI, PostGIS schemas) were authorially created from scratch.
3. **Unmodified WebODM Container**:
   - The WebODM container is deployed unmodified from upstream releases. If modifications to WebODM's source code are ever required, those specific changes must be released under AGPL-3.0 in accordance with license obligations.

---

## 2. Trademark Compliance (UAV4GEO Guidelines)

In strict adherence to `WebODM-master/WebODM-master/TRADEMARK.md`:
1. **Product Naming**:
   - The product is named **AgriDrone AutoMap**. The WebODM mark is used purely descriptively to explain photogrammetry integration (e.g. *"Powered by WebODM Photogrammetry Engine"*).
2. **No False Endorsement**:
   - AgriDrone AutoMap does not use UAV4GEO logos or marks in any manner implying endorsement, partnership, or certification by UAV4GEO.
3. **Clear Attribution**:
   - WebODM is attributed to Piero Toffanin and the OpenDroneMap / UAV4GEO community in all technical documentation.

---

## 3. Third-Party Software Inventory

| Software / Library | Version | License | Role in Integrated System |
|:---|:---:|:---:|:---|
| **WebODM** | 3.3.1 | GNU AGPL-3.0 | Headless Structure-from-Motion (SfM) processing engine |
| **NodeODM** | 2.x | GNU GPL-3.0 | Worker microservice executing OpenDroneMap CLI pipelines |
| **OpenDroneMap (ODM)** | 3.x | GNU GPL-3.0 | Core photogrammetry pipeline (OpenSfM, OpenMVS, GDAL) |
| **FastAPI** | 0.110+ | MIT | AgriDrone AutoMap sovereign backend gateway & API |
| **SQLAlchemy** | 2.0+ | MIT | Database ORM for PostgreSQL / PostGIS |
| **Next.js** | 14.x | MIT | AgriDrone AutoMap sovereign frontend application |
| **MapLibre GL JS** | 4.x | BSD-3-Clause | GPU-accelerated web map raster and vector visualizer |
| **Azure SDK for Python** | 12.x | MIT | Official Microsoft Azure Blob Storage SDK |
| **Celery** | 5.3+ | BSD-3-Clause | Distributed asynchronous task queue |
| **Redis** | 7.2 | BSD-3-Clause | In-memory message broker and caching layer |
| **GDAL / Rasterio** | 3.8+ / 1.5+ | MIT / BSD | Geospatial raster analysis and COG conversion |
| **ReportLab** | 4.x | BSD-3-Clause | PDF agricultural survey and diagnostic report generation |

---

## 4. Legal & Licensing Recommendations

1. **Deployment Architecture**: Continue deploying WebODM as an independently managed container (e.g. `opendronemap/webodm:latest` or `opendronemap/nodeodm:latest`) separated by network API boundaries.
2. **Human Review Gate**: Before commercial public distribution or SaaS deployment, an intellectual property attorney should verify the network service boundary under current jurisdiction case law regarding AGPL-3.0 Section 13.
