# AgriDrone AutoMap — User Journeys & End-to-End Workflows

## 1. Overview & System Persona Definition

This document details the step-by-step user journeys through the AgriDrone AutoMap platform. It maps out how different authorized personas interact with the system from initial login through data ingestion, photogrammetry, geospatial computation, visualization, and report generation.

### Personas Involved
1. **Agricultural Drone Operator / GIS Admin**: Responsible for flight creation, data uploading, photogrammetry execution, spectral algorithm calculation, and publishing.
2. **Authorized Farmer / Landowner**: Responsible for monitoring crop health on their owned fields, reviewing geospatial maps, inspecting diagnostics, and downloading final PDF reports.

---

## 2. Authentication Entry (Undecided Authentication Status)

> [!IMPORTANT]
> **Open Decision Status**: The exact technical authentication provider (e.g., custom OAuth2 with JWT, Azure Entra ID / Microsoft Identity, NextAuth / Auth.js with database sessions) remains an **unresolved decision** to be confirmed prior to Phase 4 / Phase 9 implementation.
> 
> The journeys below document the system flow assuming an authorized user has passed authentication and obtained a validated session token containing their tenant ID and role attributes.

```mermaid
flowchart TD
    Start([User Navigates to Platform]) --> AuthGate{Authenticated Session?}
    AuthGate -- No --> LoginPrompt[Authentication Entry Gate<br/>Credentials / SSO - Method TBD]
    LoginPrompt --> ValidateAuth[Validate Identity & Tenant Claims]
    ValidateAuth --> AuthGate
    AuthGate -- Yes --> RoleCheck{User Role}
    RoleCheck -- Admin / Drone Operator --> JourneyAdmin[Admin Workflow: Page 1 Ingestion]
    RoleCheck -- Farmer / Landowner --> JourneyFarmer[Farmer Workflow: Page 4 Portal]
```

---

## 3. Journey 1: Administrator End-to-End Drone Survey Processing Workflow

This is the primary operational workflow for drone technicians and system administrators.

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Drone Operator / Admin
    participant P1 as Page 1: Admin Dashboard
    participant API as FastAPI Backend
    participant Azure as Azure Blob Storage
    participant DB as PostgreSQL / PostGIS
    participant P2 as Page 2: WebODM Processing
    participant Celery as Celery / Redis
    participant WebODM as WebODM Instance
    participant P3 as Page 3: Algorithm Engine
    participant P5 as Page 5: Diagnostics

    Admin->>P1: Selects Farm, Field boundary & creates Survey
    P1->>DB: Persist Survey metadata record
    Admin->>P1: Uploads raw drone photos (JPG/DNG/TIFF)
    P1->>API: Stream chunks with EXIF metadata
    API->>Azure: Store raw images in private container
    API->>API: Validate GPS tags (lat/lon/alt) on >90% photos
    API-->>P1: Eligibility Ledger: "Eligible for WebODM"
    
    Admin->>P2: Navigates to WebODM Processing
    Admin->>P2: Selects processing preset (e.g. Ag Fast) & launches
    P2->>API: POST /api/v1/photogrammetry/tasks
    API->>Celery: Queue photogrammetry task
    Celery->>WebODM: Create project, upload images & start task
    loop Polling Status & Logs
        Celery->>WebODM: Check progress & retrieve logs
        Celery-->>P2: Stream log feed & progress bar
    end
    WebODM-->>Celery: Task complete, orthomosaic GeoTIFF generated
    Celery->>Azure: Download orthomosaic & store in Azure Storage
    Celery->>DB: Register orthomosaic metadata (CRS, resolution, bounds)
    Celery-->>P2: Status: Completed
    
    Admin->>P3: Navigates to Algorithm & Multi-Map Generation
    P3->>API: GET available orthomosaics
    API-->>P3: Returns registered orthomosaic metadata
    Admin->>P3: Verifies band mapping (Red, Green, Blue, NIR)
    Admin->>P3: Selects NDVI & SAVI algorithms
    P3->>API: POST /api/v1/algorithms/generate
    API->>Celery: Queue raster computation job
    Celery->>Azure: Fetch orthomosaic raster stream
    Celery->>Celery: Rasterio/NumPy index calculation & COG generation
    Celery->>Azure: Upload index GeoTIFFs to Azure Storage
    Celery->>DB: Register published map layers & stats
    Celery-->>P3: Layers Ready
    
    Admin->>P5: Navigates to Diagnostics & Actionable Insights
    P5->>API: GET field statistics & zoning breakdown
    API-->>P5: Mean, median, std-dev, class acreage
    Admin->>P5: Clicks "Generate Verified PDF Report"
    P5->>API: POST /api/v1/reports/generate
    API->>Celery: ReportLab PDF assembly job
    Celery->>Azure: Store generated PDF
    Celery->>DB: Register published report for Farmer access
    Celery-->>P5: PDF ready for preview / download
```

### Detailed Steps:
1. **Survey Initiation**: Operator logs in, selects farm "GreenValley", field "Pivot-4", and inputs flight parameters (Date: 2026-10-14, Altitude: 80m, Sensor: MicaSense RedEdge-P).
2. **Raw Photo Ingestion**: Operator drags 350 geotagged TIFF files into the dropzone. System uploads chunks to Azure Blob Storage while FastAPI extracts EXIF data. Over 98% of photos contain valid GPS tags. The ledger marks the dataset *Eligible for WebODM*.
3. **Photogrammetry Execution**: Operator moves to Page 2, chooses "Ag Multispectral Precision" preset, and triggers reconstruction. Celery worker forwards files to the WebODM node. Operator watches the live OpenDroneMap log console as feature extraction, bundle adjustment, and orthophoto generation run. Upon completion, the multi-band orthomosaic is registered in PostGIS and archived in Azure.
4. **Spectral Index Generation**: Operator proceeds to Page 3. The system scans the orthomosaic and auto-identifies 5 spectral bands (Blue, Green, Red, RedEdge, NIR). The operator verifies band indices, checks NDVI and NDRE, selects the 5-class agronomic color palette, and triggers generation. Celery executes Rasterio/NumPy block calculations, generates Cloud Optimized GeoTIFFs, and registers the layers.
5. **Quality Review & Report Publishing**: Operator reviews statistical zoning on Page 5, notes that no cloud artifacts were present, triggers ReportLab PDF generation, and publishes the survey deliverables for farmer access.

---

## 4. Journey 2: Direct GIS Processing Workflow for Pre-Stitched GeoTIFFs

This workflow skips WebODM entirely for pre-stitched, georeferenced raster products (e.g., provided by specialized third-party processing labs or aerial contractors).

```mermaid
sequenceDiagram
    autonumber
    actor Admin as Drone Operator / Admin
    participant P1 as Page 1: Admin Dashboard
    participant API as FastAPI Backend
    participant Azure as Azure Blob Storage
    participant DB as PostgreSQL / PostGIS
    participant P3 as Page 3: Algorithm Engine
    participant Celery as Celery / Redis
    participant P5 as Page 5: Diagnostics

    Admin->>P1: Selects Farm, Field & creates Survey
    Admin->>P1: Uploads pre-stitched orthomosaic GeoTIFF (.tif)
    P1->>API: Stream GeoTIFF file
    API->>Azure: Store GeoTIFF in private container
    API->>API: Validate with GDAL/Rasterio: CRS, bounds, dimensions, bands
    API->>DB: Register raster as "Pre-Stitched Orthomosaic"
    API-->>P1: Eligibility Ledger: "Eligible for Direct GIS Processing"
    
    Note over Admin, P3: Bypasses Page 2 (WebODM) entirely
    
    Admin->>P3: Navigates directly to Algorithm Engine
    P3->>API: Retrieve pre-stitched raster metadata
    Admin->>P3: Confirms band mapping & selects indices
    P3->>API: POST /api/v1/algorithms/generate
    API->>Celery: Queue Rasterio calculation
    Celery->>Azure: Stream bands, calculate indices, generate COGs
    Celery->>Azure: Store index GeoTIFFs
    Celery->>DB: Register map layers & field statistics
    Celery-->>P3: Processing Complete
    
    Admin->>P5: Review diagnostics and generate final PDF report
```

### Key Differences from Journey 1:
- Zero raw photo upload; single large GeoTIFF file upload.
- WebODM step is explicitly bypassed, saving substantial processing time and computing resources.
- Georeferencing, projection (CRS), and band structure must be validated on Page 1 before proceeding to Page 3.

---

## 5. Journey 3: Farmer / Landowner Geospatial Discovery & Review Workflow

This workflow represents the end-user experience for authorized farm owners and agronomists.

```mermaid
sequenceDiagram
    autonumber
    actor Farmer as Authorized Farmer
    participant P4 as Page 4: Farmer Portal
    participant API as FastAPI Backend
    participant DB as PostgreSQL / PostGIS
    participant Tile as Map Tile Service (FastAPI / COG)
    participant Azure as Azure Blob Storage
    participant P5 as Page 5: Diagnostics

    Farmer->>P4: Logs into platform (Tenant credentials)
    P4->>API: GET /api/v1/portal/farms
    API->>DB: Query farms associated with Farmer Tenant ID
    DB-->>API: Returns authorized farms and fields
    API-->>P4: Populates Farm & Field selector
    
    Farmer->>P4: Selects "Field 12 - South Section"
    P4->>API: GET /api/v1/portal/fields/12/surveys
    API->>DB: Query published surveys for Field 12
    API-->>P4: Returns survey timeline list
    
    Farmer->>P4: Selects Survey from "October 14, 2026"
    P4->>API: GET /api/v1/portal/surveys/45/layers
    API-->>P4: Returns available layers: RGB Ortho, NDVI, NDRE
    
    loop Interactive Map Exploration
        Farmer->>P4: Toggles NDVI Layer & adjusts opacity
        P4->>Tile: Request MapLibre raster tiles
        Tile->>Azure: Fetch byte-range from COG in Azure Storage
        Tile-->>P4: Render NDVI raster overlay with dynamic legend
        Farmer->>P4: Clicks on suspicious low-vigor patch in field
        P4->>API: GET pixel value probe at lat/lon
        API-->>P4: Value: NDVI 0.22 (Low Canopy Density)
    end
    
    Farmer->>P4: Clicks "Download Official Survey Report"
    P4->>API: GET /api/v1/portal/surveys/45/report-download
    API->>API: Authorize tenant ownership
    API->>Azure: Generate short-lived (15-min) SAS download token
    API-->>P4: Returns temporary Azure SAS download link
    Farmer->>Azure: Direct secure download of PDF report
    
    Farmer->>P5: Clicks "View Full Field Diagnostics"
    P5->>API: GET /api/v1/portal/surveys/45/diagnostics
    API-->>P5: Returns statistical distribution & limitations notice
    Farmer->>P5: Reviews vegetative zoning percentages & limitations
```

### Detailed Steps:
1. **Tenant-Filtered Access**: The farmer accesses the portal. The farm selector displays only the farms and fields owned by that farmer. Any attempt to query outside this tenancy returns an HTTP 403 Forbidden.
2. **Survey Timeline Selection**: Farmer picks a specific field and browses historical surveys to view seasonal crop development.
3. **Interactive Map Exploration**:
   - Farmer views the base satellite map overlaid with their field boundary polygon.
   - Activates the RGB True Color orthomosaic to inspect visual field anomalies (e.g., bare patches, standing water).
   - Switches to the NDVI layer. The MapLibre map renders the high-contrast agronomic color ramp with an interactive legend.
   - Uses the split-screen swipe tool to compare the visual RGB imagery directly against the NDVI vigor map.
4. **Secure Asset Download**: Farmer clicks the download button for the official survey report. The backend generates a secure, 15-minute SAS download link directly from Azure Blob Storage. The farmer downloads the PDF report without exposing internal storage keys.
5. **Deep Diagnostic Inspection**: Farmer transitions to Page 5 to inspect the area distribution breakdown (e.g., 72% High Vigor, 18% Moderate Vigor, 10% Stressed/Bare Ground) and reads the clear agronomic disclaimers regarding ground scouting.
