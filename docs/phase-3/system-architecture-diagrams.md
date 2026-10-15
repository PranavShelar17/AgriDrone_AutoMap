# AgriDrone AutoMap — System Architecture Diagrams
## Document Reference: `docs/phase-3/system-architecture-diagrams.md`
**Phase**: Phase 3 — System Architecture, Technical Validation & Implementation Blueprint  
**Status**: APPROVED ARCHITECTURE BLUEPRINT  
**Version**: 1.0.0  

---

## 1. High-Level System Architecture Diagram

This diagram illustrates the relationship and communication protocols between the Presentation Layer, Application Layer, Asynchronous Processing Tier, Database, and Cloud Storage.

```mermaid
graph TB
    subgraph ClientLayer ["Client Presentation Tier (Next.js 14 App Router)"]
        UI_Ingest["Page 1: Ingestion & Validation"]
        UI_WebODM["Page 2: WebODM Photogrammetry"]
        UI_Algo["Page 3: Spectral Algorithms"]
        UI_Portal["Page 4: Farmer Portal (MapLibre GL)"]
        UI_Diag["Page 5: Diagnostics & Reports"]
    end

    subgraph GatewayLayer ["API & Gateway Tier (FastAPI)"]
        API_Router["FastAPI Core Router (/api/v1)"]
        Auth_Guard["Auth & Tenant Authorization Middleware"]
        SAS_Service["Azure SAS Token Service"]
        Task_Dispatcher["Celery Task Dispatcher"]
    end

    subgraph StorageLayer ["Cloud Storage Tier (Microsoft Azure)"]
        Azure_Raw["raw-surveys container"]
        Azure_Ortho["orthomosaics container"]
        Azure_Indices["vegetation-indices container"]
        Azure_Reports["reports container"]
    end

    subgraph DatabaseLayer ["Persistence Tier (PostgreSQL 15 + PostGIS 3.3)"]
        DB_Meta["Relational Tables (Farms, Fields, Surveys)"]
        DB_Geo["Spatial Vector Geometries (Boundaries, EPSG:4326)"]
        DB_Jobs["Task Execution Ledger & Audit Logs"]
    end

    subgraph AsyncTier ["Asynchronous Compute Tier (Celery & Redis)"]
        Redis_Broker["Redis 7 (Message Broker & Result Backend)"]
        Worker_Raster["Worker: Raster Validation & GDAL COG Tiler"]
        Worker_Algo["Worker: Spectral Index Computation (NumPy/Rasterio)"]
        Worker_Stats["Worker: Zonal Statistics & Agronomic Metrics"]
        Worker_PDF["Worker: ReportLab PDF Compilation"]
    end

    subgraph PhotogrammetryCluster ["Photogrammetry Processing Cluster"]
        NodeODM_Mgr["WebODM / NodeODM Orchestrator"]
        NodeODM_Worker1["NodeODM Processing Node 1"]
        NodeODM_Worker2["NodeODM Processing Node 2"]
    end

    %% Client to API
    UI_Ingest -->|HTTPS REST| API_Router
    UI_WebODM -->|HTTPS REST| API_Router
    UI_Algo -->|HTTPS REST| API_Router
    UI_Portal -->|HTTPS REST / Vector GeoJSON| API_Router
    UI_Diag -->|HTTPS REST| API_Router

    %% Direct SAS Upload / Download
    UI_Ingest -.->|Direct Chunked Upload via SAS| Azure_Raw
    UI_Portal -.->|Tile Range Requests via SAS| Azure_Indices
    UI_Diag -.->|Direct PDF Download via SAS| Azure_Reports

    %% Gateway Internal Flow
    API_Router --> Auth_Guard
    Auth_Guard --> DB_Meta
    Auth_Guard --> SAS_Service
    SAS_Service --> Azure_Raw
    API_Router --> Task_Dispatcher
    Task_Dispatcher --> Redis_Broker

    %% Async Execution
    Redis_Broker --> Worker_Raster
    Redis_Broker --> Worker_Algo
    Redis_Broker --> Worker_Stats
    Redis_Broker --> Worker_PDF

    %% Worker Data Access
    Worker_Raster <-->|Read Raw / Write COG| Azure_Ortho
    Worker_Raster -->|Update Status| DB_Jobs
    Worker_Algo <-->|Read Ortho / Write Index COG| Azure_Indices
    Worker_Algo -->|Update Status| DB_Jobs
    Worker_Stats -->|Query Boundary| DB_Geo
    Worker_Stats -->|Save Metrics| DB_Meta
    Worker_PDF -->|Read Index & Stats / Write PDF| Azure_Reports
    Worker_PDF -->|Save Report Record| DB_Meta

    %% WebODM Integration
    Task_Dispatcher -->|HTTP Dispatch| NodeODM_Mgr
    NodeODM_Mgr --> NodeODM_Worker1
    NodeODM_Mgr --> NodeODM_Worker2
    NodeODM_Worker1 <-->|Read Photos / Write Ortho & DSM| Azure_Ortho
    NodeODM_Mgr -->|Task Status Polling| DB_Jobs
```

---

## 2. Upload & Pre-Flight Ingestion Workflow (Page 1)

This sequence details how client files (drone image archives or pre-stitched GeoTIFFs) are validated, staged via Azure Blob SAS tokens, and registered into the PostgreSQL database.

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Admin User (Browser)
    participant UI as Page 1: Ingestion UI
    participant API as FastAPI Backend
    participant DB as PostgreSQL / PostGIS
    participant Azure as Azure Blob Storage
    participant Celery as Celery Worker

    Admin->>UI: Selects Farm, Field & Survey
    Admin->>UI: Drops Raw Photo ZIP or GeoTIFF (up to 5GB)
    UI->>UI: Client Pre-Flight Validation (File size, Extension, MIME, Magic bytes)
    
    UI->>API: POST /api/v1/surveys/{survey_id}/uploads/initiate (Payload: file metadata)
    API->>DB: Verify Admin Ownership & Permissions on Survey
    API->>DB: Insert File Record (Status: 'PENDING_UPLOAD')
    API->>Azure: Generate 15-Minute Delegated PutBlob SAS URL
    API-->>UI: Return upload_id, blob_url, sas_token, chunk_size

    loop Direct Azure Chunked Upload
        UI->>Azure: PUT Block & PutBlockList (with Progress Bar update)
    end
    Azure-->>UI: 201 Created (Upload Complete)

    UI->>API: POST /api/v1/surveys/{survey_id}/uploads/{upload_id}/finalize
    API->>Azure: Verify Blob Attributes (Content-Length, MD5 checksum)
    API->>DB: Update File Record (Status: 'UPLOADED', blob_uri)
    API->>Celery: Dispatch raster_validation_task(upload_id)
    API-->>UI: Ingestion Accepted (Status: 'QUEUED_FOR_VALIDATION')

    Celery->>Azure: Stream Blob Header (Read EXIF GPS or GeoTIFF Tags)
    Celery->>Celery: Validate CRS (EPSG), Dimensions, Band Count, Georeference
    Celery->>DB: Update Record (Status: 'VALIDATED', CRS: 'EPSG:32643', Resolution: '0.04m')
    UI->>API: Poll GET /api/v1/surveys/{survey_id}/files
    API-->>UI: Return Validated File Ledger (Shows "Eligible for Processing")
```

---

## 3. WebODM Photogrammetry Processing Workflow (Page 2)

This workflow applies strictly to **Workflow 1: Raw Drone Photographs** that require 3D structure-from-motion reconstruction, point cloud generation, and digital elevation modeling.

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Admin User
    participant UI as Page 2: WebODM UI
    participant API as FastAPI Backend
    participant DB as PostgreSQL
    participant Redis as Redis Queue
    participant Worker as Celery Task Worker
    participant WebODM as WebODM / NodeODM Cluster
    participant Azure as Azure Blob Storage

    Admin->>UI: Selects Validated Raw Photo Dataset & Configuration Preset (e.g. High-Res 2.5cm)
    UI->>API: POST /api/v1/photogrammetry/tasks (survey_id, file_id, options)
    API->>DB: Create photogrammetry_tasks record (Status: 'SUBMITTED')
    API->>Redis: Enqueue execute_webodm_task(task_id)
    API-->>UI: Return task_id & tracking URL

    Worker->>DB: Lock Task (Status: 'DISPATCHING')
    Worker->>Azure: Fetch Photo Archive SAS URL
    Worker->>WebODM: POST /task/new (images zip SAS URL, dsm=true, dtm=true, res=2.5)
    WebODM-->>Worker: Return webodm_uuid: 'uuid-7890'
    Worker->>DB: Update Task (Status: 'RUNNING', webodm_task_uuid: 'uuid-7890')

    loop Status & Log Polling (Every 10 seconds)
        Worker->>WebODM: GET /task/{uuid}/info
        WebODM-->>Worker: Status: 'RUNNING', Progress: 64%, Stage: 'Mesh Generation'
        Worker->>DB: Update task progress & append console log line
        UI->>API: GET /api/v1/photogrammetry/tasks/{task_id}
        API-->>UI: Display real-time progress bar & console logs
    end

    WebODM-->>Worker: Status: 'COMPLETED' (Artifacts: orthophoto.tif, dsm.tif)
    Worker->>WebODM: GET /task/{uuid}/download/orthophoto.tif
    Worker->>Worker: Convert Orthophoto to Cloud-Optimized GeoTIFF (COG) via GDAL
    Worker->>Azure: Upload COG to orthomosaics/ container
    Worker->>Azure: Upload DSM to surface-models/ container
    Worker->>DB: Insert map_products records (Type: 'ORTHOPHOTO', 'DSM')
    Worker->>DB: Update Task (Status: 'COMPLETED', completed_at)
    UI->>API: Poll Task Status
    API-->>UI: Show "Completed" Badge & Link to Page 3 (Spectral Algorithms)
```

---

## 4. Direct Pre-Stitched Raster Processing Workflow (Page 1 $\to$ Page 3)

This workflow applies strictly to **Workflow 2: Pre-Stitched GeoTIFFs** (e.g., orthomosaics generated externally by Pix4D, DJI Terra, or Agisoft Metashape). It bypasses WebODM entirely.

```mermaid
graph TD
    A["Pre-Stitched GeoTIFF Uploaded (Page 1)"] --> B["Celery: raster_validation_task"]
    B --> C{"Is File a Valid Georeferenced GeoTIFF?"}
    C -- No --> D["Mark Status: FAILED_INVALID_RASTER<br/>Log error: Missing CRS or geotransform"]
    C -- Yes --> E["Inspect Band Count & Data Type via Rasterio"]
    E --> F["Check CRS: Is it Projected (UTM) or Geographic (WGS84)?"]
    F --> G["Convert / Retile to Cloud-Optimized GeoTIFF (COG) via GDAL"]
    G --> H["Extract Extent Bounding Box as PostGIS Polygon"]
    H --> I["Insert into map_products (Product: 'ORTHOPHOTO', is_cog=True)"]
    I --> J["Mark Survey Ingestion as COMPLETE"]
    J --> K["Directly Available on Page 3: Algorithm & Multi-Map Generation"]
```

---

## 5. Spectral Algorithm & Multi-Map Generation Workflow (Page 3)

This workflow governs spectral band mapping, scientific guardrail validation, and calculation of vegetation indices (NDVI, NDRE, GNDVI, VARI, GLI, SAVI).

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Admin User
    participant UI as Page 3: Algorithms UI
    participant API as FastAPI Backend
    participant DB as PostgreSQL
    participant Redis as Redis Queue
    participant Worker as Celery Task Worker
    participant Azure as Azure Blob Storage

    Admin->>UI: Selects Orthophoto Product
    UI->>API: GET /api/v1/algorithms/inspect-bands?product_id=prod-101
    API->>DB: Fetch Product Metadata (Bands: 3, Names: [Red, Green, Blue])
    API-->>UI: Return Band Profile (RGB Detected, NIR Absent)
    
    UI->>UI: Apply Scientific Gating: Lock NDVI & NDRE; Enable VARI, GLI, TGI
    Admin->>UI: Selects VARI Index & Color Palette ('RdYlGn')
    Admin->>UI: Clicks "Generate Multi-Map Layer"
    
    UI->>API: POST /api/v1/algorithms/jobs (product_id, algorithm: 'VARI', colormap: 'RdYlGn')
    API->>DB: Insert algorithm_jobs record (Status: 'QUEUED')
    API->>Redis: Enqueue compute_vegetation_index(job_id)
    API-->>UI: Return job_id (Status: 'QUEUED')

    Worker->>DB: Update Job (Status: 'PROCESSING')
    Worker->>Azure: Stream Orthophoto Windows via GDAL/Rasterio
    Worker->>Worker: Read Band 1 (Red), Band 2 (Green), Band 3 (Blue)
    Worker->>Worker: Apply Floating-Point Raster Math:<br/>VARI = (Green - Red) / (Green + Red - Blue)<br/>Mask DivByZero & NoData
    Worker->>Worker: Compress & Tile into Cloud-Optimized GeoTIFF (COG)
    Worker->>Azure: Upload COG to vegetation-indices/ container
    Worker->>Worker: Compute Basic Histogram & Mean/Median/StdDev
    Worker->>DB: Insert map_products record (Type: 'INDEX_VARI', Path, Stats)
    Worker->>DB: Update Job (Status: 'COMPLETED')
    
    UI->>API: Poll GET /api/v1/algorithms/jobs/{job_id}
    API-->>UI: Return Completed (Show Preview & Action to Publish to Farmer Portal)
```

---

## 6. Report Generation Workflow (Page 5)

This sequence details how validated statistical distributions, metadata, and maps are compiled into a durable PDF report via ReportLab.

```mermaid
sequenceDiagram
    autonumber
    actor User as Agronomist / Admin / Farmer
    participant UI as Page 5: Diagnostics UI
    participant API as FastAPI Backend
    participant DB as PostgreSQL / PostGIS
    participant Redis as Redis Queue
    participant Worker as Celery Task Worker
    participant Azure as Azure Blob Storage

    User->>UI: Requests "Download Official PDF Diagnostic Report"
    UI->>API: POST /api/v1/reports/generate (survey_id, index_layer_id, notes)
    API->>DB: Verify Ownership & Insert reports record (Status: 'QUEUED')
    API->>Redis: Enqueue compile_pdf_report(report_id)
    API-->>UI: Return report_id (Status: 'QUEUED')

    Worker->>DB: Fetch Survey Metadata, Farm/Field Geometry, Index Stats
    Worker->>Azure: Download Index Overview Thumbnail & Colormap Legend
    Worker->>Worker: Assemble ReportLab Document Template:
    Note over Worker: 1. Cover & Field Identification Header<br/>2. Survey Metadata (Sensor, Flight Date, Altitude)<br/>3. Orthomosaic & Index Map Imagery<br/>4. Zonal Health Statistics Table & Histogram<br/>5. Scientific Disclaimers & Ground-Truth Caveats
    Worker->>Worker: Compile PDF Byte Stream
    Worker->>Azure: Upload PDF to reports/ container (Blob: reports/rep_9021.pdf)
    Worker->>DB: Update reports record (Status: 'COMPLETED', blob_uri, file_size)

    loop Polling
        UI->>API: GET /api/v1/reports/{report_id}
        API-->>UI: Status: 'COMPLETED', download_available: true
    end

    User->>UI: Clicks "Download PDF"
    UI->>API: GET /api/v1/reports/{report_id}/download-url
    API->>Azure: Generate 15-Minute Read SAS Token
    API-->>UI: Return Temporary Signed Download Link
    UI->>Azure: GET /reports/rep_9021.pdf?sas_token=... (Direct Download)
```

---

## 7. Security & Authorization Boundaries

This diagram illustrates trust boundaries, network zones, and data access isolation across User Roles (Admin, Agronomist, Farmer).

```mermaid
graph TB
    subgraph PublicInternet ["Public Internet (Untrusted Zone)"]
        FarmerClient["Farmer Browser (Authenticated)"]
        AdminClient["Admin / Agronomist Browser (Authenticated)"]
        Attacker["Malicious / Unauthenticated Actor"]
    end

    subgraph EdgeBoundary ["Edge & Perimeter Security"]
        TLS["TLS 1.3 Termination (HTTPS)"]
        CORS["CORS Policy (Strict Domain Whitelist)"]
        RateLimit["Rate Limiting & DDoS Shield"]
    end

    subgraph AppBoundary ["Application Security Boundary (FastAPI)"]
        JWT_Verify["JWT Authentication & Session Validator"]
        RBAC["Role-Based Access Control (Admin vs Farmer)"]
        TenantFilter["Multi-Tenant Isolation Filter (WHERE farm_id = current_user.farm_id)"]
        SAS_Issuer["Privileged SAS Token Signer (Internal Secret)"]
    end

    subgraph InternalVNet ["Private Subnet / Isolated Backend Network"]
        PostgreSQL[("PostgreSQL / PostGIS (Port 5432 - No Public IP)")]
        RedisQueue[("Redis 7 (Port 6379 - Password Protected)")]
        CeleryWorker["Celery Worker Nodes (No Public Inbound)"]
        WebODMCluster["WebODM Nodes (Internal Docker Network)"]
    end

    subgraph CloudStorageZone ["Private Cloud Storage Zone (Microsoft Azure)"]
        AzureBlob["Azure Blob Storage Account<br/>(Public Anonymous Access: DISABLED)"]
    end

    %% Edge Inbound
    FarmerClient --> TLS
    AdminClient --> TLS
    Attacker -.->|Blocked| TLS

    TLS --> CORS --> RateLimit
    RateLimit --> JWT_Verify
    JWT_Verify --> RBAC

    %% Authorization Routing
    RBAC -->|Admin Role| API_AdminOps["Admin Operations (Ingest, WebODM, Algo)"]
    RBAC -->|Farmer Role| TenantFilter
    TenantFilter -->|Restricted Scoped Query| PostgreSQL

    %% Privileged Internal Access
    API_AdminOps --> PostgreSQL
    API_AdminOps --> RedisQueue
    RedisQueue --> CeleryWorker
    CeleryWorker --> WebODMCluster

    %% Storage Mediation
    TenantFilter --> SAS_Issuer
    SAS_Issuer -->|Generate 15-Min Scoped SAS URL| FarmerClient
    FarmerClient -.->|Direct Read of Specific Blob via SAS| AzureBlob
    CeleryWorker <-->|Managed Identity / Server Key| AzureBlob

    %% Isolation Assertions
    style Attacker fill:#fee2e2,stroke:#ef4444,stroke-width:2px;
    style AzureBlob fill:#dbeafe,stroke:#3b82f6,stroke-width:2px;
    style PostgreSQL fill:#ecfdf5,stroke:#059669,stroke-width:2px;
```
