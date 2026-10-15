# AgriDrone AutoMap — System Architecture Overview
## Document Reference: `docs/phase-3/architecture-overview.md`
**Phase**: Phase 3 — System Architecture, Technical Validation & Implementation Blueprint  
**Status**: APPROVED ARCHITECTURE BLUEPRINT  
**Version**: 1.0.0  

---

## 1. Executive Architectural Summary

**AgriDrone AutoMap** is an enterprise-grade geospatial platform designed for agricultural drone survey processing, automated photogrammetry, calibrated multi-spectral raster calculations, secure interactive web GIS delivery, and automated agronomic reporting.

The system is architected around a **decoupled, event-driven, micro-service-aligned monolith** architecture. It strictly isolates CPU/RAM-heavy geospatial photogrammetry and raster math from user-facing synchronous web traffic, ensuring high availability, multi-tenant isolation, and auditable data provenance.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       PRESENTATION TIER (Next.js 14)                         │
│   Page 1: Ingestion  │  Page 2: WebODM  │  Page 3: Algorithms               │
│   Page 4: Farmer Portal (MapLibre)      │  Page 5: Diagnostics & Reports    │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ HTTPS / REST (Versioned /api/v1)
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    API GATEWAY & BUSINESS TIER (FastAPI)                    │
│   - JWT / Session Auth Verification        - Geospatial Metadata Ledger     │
│   - Azure Blob SAS Token Issuer            - Asynchronous Task Dispatcher   │
│   - Input Validation & Guardrails          - Report Orchestration           │
└──────────────┬───────────────────────┬──────────────────────┬───────────────┘
               │                       │                      │
     SQL / PostGIS Queries    Celery Job Queue     SAS Direct Upload/Download
               │                       │                      │
               ▼                       ▼                      ▼
┌───────────────────────────┐ ┌──────────────────┐ ┌──────────────────────────┐
│     PERSISTENCE TIER      │ │ ASYNC WORKER TIER│ │    CLOUD STORAGE TIER    │
│    PostgreSQL 15+ &       │ │  Celery Workers  │ │ Microsoft Azure Blob     │
│    PostGIS 3.3+           │ │  Redis 7+ Broker │ │ Storage (Official SDK)   │
│ - Multi-Tenant Relational │ └────────┬─────────┘ │ - Raw Photos & Archives  │
│ - Spatial Polygons (CRS)  │          │           │ - WebODM Orthos & DSMs   │
│ - Job Ledger & Provenance │          ▼           │ - COGs & Indices         │
└───────────────────────────┘ ┌──────────────────┐ │ - PDF Audit Reports      │
                              │ PHOTOGRAMMETRY & │ └──────────────────────────┘
                              │ GIS ENGINE       │
                              │ - WebODM/NodeODM │
                              │ - GDAL/Rasterio  │
                              │ - ReportLab PDF  │
                              └──────────────────┘
```

---

## 2. Core Architectural Principles

1. **Separation of Concerns & Workload Isolation**:
   - Web application servers (Next.js and FastAPI) are strictly non-blocking. Heavy computation (point cloud dense matching, orthomosaic stitching, radiometric raster mathematics, PDF compilation) is delegated exclusively to background Celery workers and WebODM cluster nodes.
2. **Cloud Storage as Binary Authority (Azure Blob Storage)**:
   - PostgreSQL and PostGIS store metadata, relational hierarchies, vector boundaries, and job states. Binary raster blobs (GeoTIFFs, COGs, Dense Point Clouds) and aerial photo archives are stored exclusively in Microsoft Azure Blob Storage. Neither the database nor local container filesystems serve as durable binary stores.
3. **Strict Five-Page Functional Boundary**:
   - The user-facing application is strictly partitioned into the five approved pages:
     - **Page 1**: Ingestion & Pre-flight Validation
     - **Page 2**: Photogrammetry Reconstruction Orchestration
     - **Page 3**: Multi-Spectral Index Computation
     - **Page 4**: Secure Farmer GIS Portal (MapLibre GL JS)
     - **Page 5**: Agronomic Diagnostics & ReportLab PDF Insights
   - No tangential features (e-commerce, social features, speculative disease AI) are permitted.
4. **Authentic Geospatial & Agronomic Integrity**:
   - System guardrails forbid calculating Near-Infrared (NIR) dependent indices (NDVI, NDRE) from standard 3-band RGB imagery.
   - Vegetation indices are categorized strictly as **optical surface reflectance observations**, not autonomous crop disease diagnoses or yield guarantees.
5. **Least-Privilege Multi-Tenant Data Isolation**:
   - Cross-tenant data leakage is prevented at the database and object storage layers. Farmer portal queries strictly enforce tenant/farm ownership constraints server-side. File access is mediated through short-lived (15-minute) Shared Access Signature (SAS) tokens generated only after explicit identity and ownership verification.

---

## 3. Component Responsibilities & Boundaries

| Component | Technology | Primary Responsibilities | Data Owned | Upstream / Downstream Dependencies |
| :--- | :--- | :--- | :--- | :--- |
| **Frontend UI** | Next.js 14, TypeScript, Tailwind CSS | Rendering the 5 approved views, client-side pre-flight checks, MapLibre GL JS map rendering, user interaction, state reflection. | Transient client state, auth tokens in memory/cookies. | Calls FastAPI `/api/v1` routes; downloads via Azure SAS URLs. |
| **Backend API** | Python 3.11+, FastAPI, Pydantic v2 | Request validation, business logic, authorization enforcement, SAS token generation, dispatching Celery tasks, querying PostGIS. | None (stateless service). | Communicates with PostgreSQL, Redis, Azure Blob Storage, and WebODM API. |
| **Relational Database** | PostgreSQL 15+ with PostGIS 3.3+ extension | Durable persistence of farms, fields, surveys, file metadata, task ledgers, spatial boundaries (EPSG:4326/3857), audit logs. | Relational records, spatial polygons, job state histories. | Queried by FastAPI and updated by Celery workers. |
| **Task Broker & Cache** | Redis 7+ | In-memory message transport for Celery tasks, task rate-limiting, ephemeral pub/sub status notifications. | Task message queues, worker heartbeats, cache keys. | Receives dispatches from FastAPI; consumed by Celery workers. |
| **Background Workers** | Celery 5.3+, Python 3.11+ | Executing asynchronous raster validation, WebODM status polling, vegetation index calculations, zonal statistics, PDF generation. | Temporary working files in scratch volume (ephemeral). | Reads/writes to Azure Blob Storage, updates PostgreSQL via SQLAlchemy/GeoAlchemy2. |
| **Photogrammetry Engine** | WebODM / NodeODM | Structure-from-Motion (SfM), point cloud densification, mesh surface generation, orthomosaic generation, digital elevation modeling. | WebODM task SQLite / local working volumes. | Receives tasks from Celery/FastAPI; outputs orthomosaics to Azure Storage. |
| **Raster Processing Engine** | GDAL 3.8+, Rasterio 1.3+, NumPy | Cloud-Optimized GeoTIFF (COG) tiling, CRS reprojection, band math (NDVI, NDRE, VARI, GLI, SAVI), NoData masking, zonal stats. | In-memory NumPy arrays during computation. | Operates within Celery worker processes. |
| **Cloud Object Store** | Microsoft Azure Blob Storage | Secure, scalable binary asset storage for raw photo archives, orthophotos, surface models, COGs, and PDF reports. | All binary files and raster blobs. | Accessed via Azure Python SDK from FastAPI and Celery; read by client via SAS. |
| **Map Rendering Engine** | MapLibre GL JS 4+ | Client-side WebGL rendering of vector field boundaries, raster COG tile layers, colormap legends, split-screen swipe comparison. | Browser WebGL context. | Consumes vector GeoJSON from FastAPI and raster tiles/images from storage. |
| **Report Engine** | ReportLab 4+ | Compiling auditable, publication-grade agronomic PDF reports containing field metadata, index maps, histograms, and disclaimers. | Output PDF byte-streams. | Runs in Celery workers; stores compiled PDFs in Azure Storage. |

---

## 4. Architectural Assumptions & Technical Limitations

1. **Photogrammetry Hardware Constraints**:
   - WebODM reconstruction is compute- and memory-intensive. Minimum production requirements for a NodeODM worker are 4 vCPUs and 16 GB RAM (handling surveys up to 500 images). Surveys exceeding 1,000 images require 8+ vCPUs and 32 GB RAM or chunked sub-region processing.
2. **Raw Aerial Photography vs Pre-Stitched GeoTIFF Separation**:
   - Raw drone photos must undergo WebODM photogrammetry (Workflow 1). Pre-stitched orthomosaic GeoTIFFs bypass WebODM entirely and proceed directly to CRS/Raster validation and Algorithm computation (Workflow 2).
3. **COG (Cloud-Optimized GeoTIFF) Requirement for Map Streaming**:
   - MapLibre GL JS cannot directly decode a multi-gigabyte uncompressed GeoTIFF in browser memory. All orthomosaics and index rasters are converted to Cloud-Optimized GeoTIFFs (internal overviews, 256x256 tiles, LZW/Deflate compression) to enable dynamic windowed HTTP range-request tile streaming.
4. **Authentication Method Decoupling**:
   - The specific identity provider (OAuth2/OIDC, Azure AD B2C, or self-hosted JWT) remains an open decision from Phase 1. The architecture defines an abstract, decoupled `AuthManager` interface that enforces tenant authorization at API boundaries regardless of whether tokens originate from social auth, enterprise SSO, or internal credentials.
5. **No Production Cloud Resources in Phase 3**:
   - In accordance with Phase 3 constraints, all Azure, WebODM, and database specifications represent verified architecture designs. No billable cloud resources, live Azure blobs, or live database migrations are provisioned during this planning phase.
