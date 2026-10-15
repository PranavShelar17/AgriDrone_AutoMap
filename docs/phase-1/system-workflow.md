# AgriDrone AutoMap — System Workflow & Architecture Specification

## 1. Overall System Architecture

The AgriDrone AutoMap architecture is engineered as a decoupled, multi-tier system separating high-performance reactive web interfaces, fast asynchronous API routing, scalable task orchestration, specialized photogrammetric execution, and cloud object storage.

```mermaid
flowchart TB
    subgraph Client Layer
        Browser[Client Web Browser<br/>Chrome / Firefox / Edge / Safari]
        NextApp[Next.js App Router<br/>TypeScript + Tailwind CSS]
        MapLibre[MapLibre GL JS<br/>Interactive Map Engine]
        Browser <--> NextApp
        NextApp --> MapLibre
    end

    subgraph API & Routing Layer
        FastAPI[FastAPI Backend<br/>Python 3.11+ REST Engine]
        NextApp <-->|REST API JSON| FastAPI
        MapLibre <-->|Raster Tiles & Probes| FastAPI
    end

    subgraph Persistence Layer
        PostgreSQL[(PostgreSQL + PostGIS<br/>Metadata, Spatial Geometries, Provenance)]
        AzureStorage[(Microsoft Azure Blob Storage<br/>Private Containers: Photos, Orthos, COGs, PDFs)]
        FastAPI <-->|SQLAlchemy / GeoAlchemy2| PostgreSQL
        FastAPI <-->|Official Azure SDK for Python| AzureStorage
    end

    subgraph Task Queue & Asynchronous Compute
        Redis[(Redis Broker & Result Store)]
        CeleryWorkers[Celery Background Workers<br/>GIS & Orchestration Tasks]
        FastAPI -->|Enqueue Jobs| Redis
        Redis <--> CeleryWorkers
        CeleryWorkers <-->|Query / Update State| PostgreSQL
        CeleryWorkers <-->|Read / Write Blobs| AzureStorage
    end

    subgraph Specialized Processing Engines
        WebODM[WebODM / OpenDroneMap<br/>External Photogrammetry Cluster]
        GDAL_Rasterio[GDAL + Rasterio + NumPy<br/>In-Process Raster Math & COG Generation]
        ReportLabEngine[ReportLab Engine<br/>Vector PDF Report Compilation]
        
        CeleryWorkers <-->|HTTP REST Task Dispatch & Logs| WebODM
        CeleryWorkers --> GDAL_Rasterio
        CeleryWorkers --> ReportLabEngine
    end
```

---

## 2. Component Responsibility Matrix

| Technology Component | Operational Role & Boundaries | What It Must NOT Do |
| :--- | :--- | :--- |
| **Next.js (App Router)** | Client-side UI rendering, form handling, state presentation, MapLibre container. | Must NOT connect directly to PostgreSQL or execute GIS processing. |
| **FastAPI** | Request authentication, input validation, CRUD endpoints, SAS token generation, Celery task dispatching. | Must NOT run blocking, heavy photogrammetry or full raster calculations synchronously. |
| **PostgreSQL + PostGIS** | Relational records (farms, surveys, users), spatial field boundaries (`ST_Polygon`), raster metadata, calculation provenance. | Must NOT store raw image binaries, large GeoTIFF rasters, or point clouds. |
| **Microsoft Azure Blob Storage** | Primary, authoritative object store for all binary assets: raw photos, orthomosaics, COG index layers, PDF reports. | Does NOT execute code or GIS processing; passive object storage only. |
| **Redis** | In-memory message broker for Celery task queues; transient task status caching. | Must NOT be used as the permanent system of record. |
| **Celery Workers** | Asynchronous worker processes executing long-running tasks: WebODM dispatch, Rasterio/NumPy index math, ReportLab PDF assembly. | Does NOT handle direct external HTTP requests from clients. |
| **WebODM / OpenDroneMap** | Specialized photogrammetric reconstruction (Structure-from-Motion, point cloud, meshing, orthorectification). | Does NOT perform vegetation index math or store farmer records. |
| **GDAL / Rasterio / NumPy** | Embedded Python libraries within Celery workers for windowed raster reading, band math (NDVI/NDRE), COG generation. | Used only within backend worker context; not run on web servers. |
| **MapLibre GL JS** | In-browser client GIS map viewer, layer switching, opacity, split comparison, and point probes. | Does NOT compute vegetation indices; renders pre-generated tiles/rasters. |
| **ReportLab** | Python PDF authoring toolkit inside Celery worker compiling tables, vector charts, and thumbnails into downloadable reports. | Does NOT generate maps; assembles pre-computed data and images into PDF. |

---

## 3. Workflow A: Drone Image Ingestion & Pre-Flight Validation

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Drone Operator (Page 1)
    participant UI as Next.js Dashboard
    participant API as FastAPI Ingestion
    participant Azure as Azure Blob Storage
    participant DB as PostgreSQL / PostGIS

    Admin->>UI: Selects Farm & Field, creates Survey
    UI->>API: POST /api/v1/surveys
    API->>DB: Insert Survey (Status: DRAFT)
    API-->>UI: Survey Created (UUID)

    Admin->>UI: Drags & Drops Image Batch (Raw Photos or GeoTIFF)
    loop Resumable Chunked Transfer
        UI->>API: POST /api/v1/ingest/upload-chunk
        API->>Azure: Append block / stream to temporary blob
    end
    UI->>API: POST /api/v1/ingest/finalize-upload
    API->>Azure: Commit composite blob
    
    alt Upload Type: Raw Photo Batch
        API->>API: Extract EXIF metadata via ExifTool / Pillow
        API->>API: Check GPS tags: Lat, Lon, Altitude
        alt Valid Geotags (>= 90%)
            API->>DB: Update Survey: Status = UPLOADED, Eligibility = ELIGIBLE_WEBODM
            API-->>UI: Validation Passed: Ready for WebODM (Page 2)
        else Missing Geotags (< 90%)
            API->>DB: Update Survey: Status = INVALID, Notes = "Insufficient GPS tags"
            API-->>UI: Validation Error: GPS coordinates missing on raw photos
        end
    else Upload Type: Pre-Stitched GeoTIFF
        API->>API: Inspect with GDAL / Rasterio: CRS, Bounds, Transform, Band Count
        alt Valid Georeference & CRS
            API->>DB: Insert Raster Record, Eligibility = ELIGIBLE_DIRECT_GIS
            API-->>UI: Validation Passed: Ready for Direct GIS Processing (Page 3)
        else Missing Projection or Georeference
            API->>DB: Update Survey: Status = INVALID, Notes = "Missing CRS / Geotransform"
            API-->>UI: Validation Error: GeoTIFF is not georeferenced
        end
    end
```

---

## 4. Workflow B: WebODM Photogrammetry Reconstruction

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Drone Operator (Page 2)
    participant UI as Next.js WebODM Page
    participant API as FastAPI Backend
    participant Celery as Celery Photogrammetry Worker
    participant WebODM as WebODM Instance (REST API)
    participant Azure as Azure Blob Storage
    participant DB as PostgreSQL

    Admin->>UI: Selects Survey & Processing Preset (e.g. Ag Fast)
    Admin->>UI: Clicks "Start Reconstruction"
    UI->>API: POST /api/v1/photogrammetry/tasks
    API->>DB: Create PhotogrammetryTask (Status: QUEUED)
    API->>Celery: Enqueue `run_webodm_reconstruction(survey_id)`
    API-->>UI: HTTP 202 Accepted (Task UUID)

    Celery->>Azure: Download raw photo batch from survey storage
    Celery->>WebODM: Authenticate & Create Project / Task via WebODM API
    Celery->>WebODM: Upload raw photos to WebODM node
    Celery->>WebODM: Start Task with configured options
    Celery->>DB: Update PhotogrammetryTask: Status = PROCESSING

    loop Task Polling & Streaming Logs (every 5 seconds)
        Celery->>WebODM: GET /api/projects/{id}/tasks/{id}
        WebODM-->>Celery: Status (RUNNING), Progress (45%), Recent Logs
        Celery->>DB: Update Task Progress & save log snippet
        UI->>API: GET /api/v1/photogrammetry/tasks/{id}/status
        API-->>UI: Return Progress % & Log updates
    end

    WebODM-->>Celery: Task Status: COMPLETED
    Celery->>WebODM: Download `orthophoto.tif` and `dsm.tif`
    Celery->>Azure: Upload `orthophoto.tif` to survey Azure container
    Celery->>DB: Register Orthomosaic: CRS, GSD, Extent, Band Count, Azure URI
    Celery->>DB: Update Task Status = COMPLETED, Survey Status = ELIGIBLE_DIRECT_GIS
    Celery-->>UI: Task Complete notification via Status API
```

---

## 5. Workflow C: Direct Raster Processing (Bypassing WebODM)

```mermaid
flowchart TD
    Start[Pre-Stitched GeoTIFF Uploaded on Page 1] --> Validate[GDAL/Rasterio CRS & Affine Check]
    Validate --> Route[Eligibility: ELIGIBLE_DIRECT_GIS]
    Route --> BypassNotice[Page 2 WebODM: Bypassed Entirely]
    BypassNotice --> Page3[Direct Navigation to Page 3: Algorithm Engine]
    Page3 --> SpectralAssign[Verify & Assign Spectral Bands]
    SpectralAssign --> MathExecution[Execute Rasterio/NumPy Index Calculation]
```

*Architectural Principle*: Pre-stitched orthomosaics provided by third-party processing labs or existing farm archives **must never be submitted to WebODM**. They skip Page 2 entirely and proceed directly to Page 3.

---

## 6. Workflow D: GIS Vegetation Index Generation & Report Compilation

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Operator / Admin (Page 3 & Page 5)
    participant UI as Next.js Algorithm & Diagnostics
    participant API as FastAPI Backend
    participant Celery as Celery GIS Worker
    participant Azure as Azure Blob Storage
    participant DB as PostgreSQL / PostGIS

    Admin->>UI: Selects Orthomosaic, assigns bands (NIR=5, Red=3)
    Admin->>UI: Selects NDVI & SAVI (L=0.5), clicks "Generate Maps"
    UI->>API: POST /api/v1/algorithms/generate
    API->>Celery: Enqueue `compute_vegetation_indices(params)`
    API-->>UI: Task Queued

    Celery->>Azure: Stream multi-band orthomosaic via GDAL VSI / range read
    Celery->>Celery: Windowed Rasterio reading & NumPy masked calculation
    Celery->>Celery: Clamp values [-1.0, 1.0], assign NoData (NaN)
    Celery->>Celery: Build Cloud Optimized GeoTIFF (COG) with overviews
    Celery->>Azure: Upload `ndvi.tif` and `savi.tif` to Azure Storage
    
    Celery->>DB: Query field boundary polygon from PostGIS
    Celery->>Celery: Clip raster to polygon, compute zonal stats:
    Note over Celery: Mean, Median, StdDev, Area per Health Class
    Celery->>DB: Insert MapLayer records & FieldStatistics
    Celery-->>UI: Index Generation Complete

    Admin->>UI: Navigates to Page 5, reviews statistics & clicks "Compile PDF Report"
    UI->>API: POST /api/v1/reports/generate
    API->>Celery: Enqueue `generate_pdf_report(survey_id)`
    Celery->>DB: Fetch survey metadata, field stats & notes
    Celery->>ReportLabEngine: Render vector layout, histograms, and disclaimers
    Celery->>Azure: Upload `survey_report.pdf`
    Celery->>DB: Register Report, mark Survey PUBLISHED
    Celery-->>UI: PDF Report Ready for Farmer Download
```
