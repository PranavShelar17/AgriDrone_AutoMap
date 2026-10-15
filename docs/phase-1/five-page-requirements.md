# AgriDrone AutoMap — Five-Page Requirements Specification

## 1. Architectural Scope & Navigation Map

The entire AgriDrone AutoMap application is structured around **exactly five functional pages**. The navigation model guarantees clear separation of concerns, strict operational safety, and intuitive transitions between administrative/operational workflows and end-user portal experiences.

```mermaid
flowchart TD
    subgraph Navigation Flow
        Auth[Authentication Entry] -->|Authenticated Admin/Operator| P1[Page 1: Admin Dashboard & Ingestion]
        P1 -->|Dispatch Raw Photos| P2[Page 2: WebODM Photogrammetry]
        P1 -->|Direct Valid Pre-stitched Raster| P3[Page 3: Algorithm & Multi-Map Generation]
        P2 -->|Registered Orthomosaic| P3
        P3 -->|Published Map Products| P4[Page 4: Secure Farmer Portal]
        P3 -->|Computed Indices & Metrics| P5[Page 5: Diagnostics & Actionable Insights]
        P4 <-->|Cross-Navigation (Tenant View)| P5
        Auth -->|Authenticated Farmer| P4
    end
```

---

## 2. Page 1 — Admin Dashboard & Drone Image Ingestion

### A. Purpose & High-Level Scope
The primary control hub for administrators and drone technicians. Used to manage hierarchical spatial entities (Farms, Fields, Surveys), ingest raw aerial survey images or vendor-supplied pre-stitched GeoTIFF rasters, perform server-side metadata and CRS validation, and track ingestion history in an eligibility ledger.

### B. Core Components & Controls
1. **Hierarchy Selector / Creator**:
   - Farm Selector Dropdown (with "Create Farm" modal dialog).
   - Field Boundary Selector (with GeoJSON/Shapefile boundary upload or interactive polygon display).
   - Survey Session Creator (Flight Date, Sensor Model, Target Crop, Flight Altitude, Notes).
2. **Dual-Mode Upload Dropzone**:
   - Mode A: *Raw Drone Photograph Batch* (drag-and-drop supporting 10 to 1,000+ files: JPG, DNG, TIFF with EXIF GPS).
   - Mode B: *Pre-Stitched GeoTIFF Raster* (single high-resolution orthomosaic / multispectral raster: `.tif`, `.tiff`).
   - Upload controls: Pause, Resume, Cancel, Retry failed chunks.
3. **Pre-Flight Validation Panel**:
   - Real-time display of metadata extraction results:
     - Coordinate Reference System (CRS / EPSG code).
     - Spatial resolution / GSD (Ground Sample Distance in cm/pixel).
     - Band count and detected color space / photometric interpretation.
     - EXIF geotag presence verification (% of photos with valid latitude, longitude, and altitude).
4. **Ingestion & Eligibility Ledger Table**:
   - Tabular view of uploaded datasets: Dataset ID, Survey, Timestamp, File Count/Size, Detected Type, Status, and Workflow Eligibility Badge (*Eligible for WebODM*, *Eligible for Direct GIS Processing*, *Invalid/Missing Metadata*).

### C. Required Data
- **Inputs**: Farm name/owner ID, Field polygon geometry (PostGIS `GEOMETRY(Polygon, 4326)`), Survey flight date/metadata, Binary file streams.
- **Server Responses**: Upload chunk receipts, Azure Blob URIs, metadata inspection payloads (CRS, dimensions, bands, bounding box).

### D. User Actions
- Select or create Farm and Field.
- Initiate new Survey flight session.
- Drag-and-drop or browse files into the dropzone.
- Review validation feedback and confirm dataset ingestion into Azure Blob Storage.
- Route dataset to Page 2 (WebODM) or Page 3 (Direct GIS Processing).

### E. States (Empty, Loading, Error, Success)
- **Empty State**: No surveys selected; prompts user with clear visual guides to create a farm/field hierarchy and upload the first survey flight.
- **Loading State**: Upload progress bars with bytes transferred, transfer rate (MB/s), ETA, and server-side metadata hashing indicators.
- **Error State**: Flags missing GPS tags in raw photos, unprojected/unsupported CRS in GeoTIFFs, corrupted TIFF headers, or network interruptions with specific error codes.
- **Success State**: "Validation Passed" banner displaying extracted metadata summary, eligibility badge, and one-click action to proceed to photogrammetry or algorithm generation.

### F. Page-Specific Validation & Acceptance Criteria
- **AC-P1-01**: Must enforce upload file extension filtering (`.jpg`, `.jpeg`, `.dng`, `.tif`, `.tiff`).
- **AC-P1-02**: Must parse and verify EXIF metadata on raw images, requiring $\ge 90\%$ of photos in a batch to contain valid GPS coordinates before qualifying for WebODM processing.
- **AC-P1-03**: GeoTIFF uploads must be verified by GDAL/Rasterio to have a valid spatial geotransform and defined projection before marking as eligible for direct GIS processing.

---

## 3. Page 2 — WebODM Photogrammetry Processing

### A. Purpose & High-Level Scope
The photogrammetric orchestration center. Allows operators to configure OpenDroneMap (WebODM) processing pipelines, submit validated batches of aerial photos, monitor asynchronous task execution in real time, view diagnostic logs, and register completed orthomosaics directly into the system catalog.

### B. Core Components & Controls
1. **Survey / Batch Selector**:
   - Dropdown of surveys containing raw photograph collections tagged as *Eligible for WebODM*.
2. **Photogrammetry Parameter Configuration Panel**:
   - Presets: *Agricultural Fast* (low resolution, rapid orthophoto), *High Quality Precision* (full resolution, DSM, DTM), *Custom*.
   - Configurable options:
     - Orthophoto Ground Resolution (cm/pixel).
     - Feature Extraction Quality (Low, Medium, High).
     - Point Cloud Densification filter.
     - Radiometric Calibration toggle (for multispectral cameras with calibration panels/sun sensors).
3. **Execution & Job Monitoring Card**:
   - Action Button: "Start Photogrammetry Reconstruction".
   - Status Indicator: Badge showing *Draft*, *Queued*, *Running*, *Completed*, *Failed*, *Canceled*.
   - Live Progress Bar: Percentage completed reported by WebODM API.
4. **Task Terminal & Diagnostic Log Viewer**:
   - Monospace, auto-scrolling log console streaming WebODM output (stages: OpenSfM feature matching, OpenMVS densification, Poisson meshing, orthophoto generation).
5. **Output Artifact Registration Card**:
   - Displays generated artifacts: Orthophoto GeoTIFF, Digital Surface Model (DSM), Quality Report PDF.
   - Action Button: "Register & Send to Algorithm Engine (Page 3)".

### C. Required Data
- Survey raw image set references in Azure Blob Storage.
- WebODM Node API configuration (base URL, authentication token, project ID, task ID).
- Celery Task ID and Redis task status records.

### D. User Actions
- Select survey and choose processing preset.
- Launch photogrammetric task.
- Cancel or restart a running task.
- Monitor log feed during processing.
- Inspect output orthomosaic preview and register the resulting GeoTIFF to the survey record.

### E. States (Empty, Loading, Error, Success)
- **Empty State**: No active task; prompts user to select a validated raw photo survey and start a reconstruction run.
- **Loading State**: Active job execution state; progress bar increments, terminal displays real-time log output, action buttons disable except for "Cancel Job".
- **Error State**: Task failure reported; log viewer highlights WebODM crash stack trace (e.g., "Not enough matching features found", "Out of memory", "GCP alignment error").
- **Success State**: Task completed successfully; shows processing duration, output file size, GSD achieved, thumbnail preview of orthomosaic, and "Proceed to Page 3" button.

### F. Page-Specific Validation & Acceptance Criteria
- **AC-P2-01**: Only raw image datasets that passed Page 1 EXIF validation can be submitted to WebODM.
- **AC-P2-02**: WebODM task execution must run strictly asynchronously via Celery worker without blocking the FastAPI event loop.
- **AC-P2-03**: Upon WebODM completion, the resulting orthomosaic GeoTIFF must be safely transferred to Azure Blob Storage and its spatial metadata registered in PostgreSQL/PostGIS.

---

## 4. Page 3 — Algorithm & Multi-Map Generation

### A. Purpose & High-Level Scope
The precision geospatial calculation workbench. Validates spectral band availability, evaluates radiometric suitability, executes scientific raster index math (NDVI, NDRE, GNDVI, SAVI) using Rasterio and NumPy, generates Cloud Optimized GeoTIFFs (COGs), and registers map layers for visualization.

### B. Core Components & Controls
1. **Dataset & Survey Picker**:
   - Dropdown of available registered orthomosaics (either from WebODM Page 2 or direct GeoTIFF upload Page 1).
2. **Spectral Band Mapping & Verification Grid**:
   - Interactive band assigner displaying detected bands:
     - Band 1, Band 2, Band 3, etc.
     - Assignment selectors: Red, Green, Blue, Red Edge, Near-Infrared (NIR), Thermal.
     - Automatic pre-fill if spectral metadata (EXIF/XMP or GeoTIFF tags) is recognized.
     - Algorithm Compatibility Matrix showing dynamically which algorithms are eligible based on current assignments.
3. **Algorithm Execution Controls**:
   - Toggles for eligible indices:
     - **NDVI** ($\frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red}}$) — disabled if NIR or Red missing.
     - **NDRE** ($\frac{\text{NIR} - \text{RedEdge}}{\text{NIR} + \text{RedEdge}}$) — disabled if NIR or Red Edge missing.
     - **GNDVI** ($\frac{\text{NIR} - \text{Green}}{\text{NIR} + \text{Green}}$) — disabled if NIR or Green missing.
     - **SAVI** ($\frac{(1 + L)(\text{NIR} - \text{Red})}{\text{NIR} + \text{Red} + L}$) — with configurable soil adjustment factor slider $L$ (default $0.5$).
4. **Color-Ramp & Classification Styler**:
   - Color palette presets (e.g., Red-Yellow-Green, Viridis, Spectral, RdYlGn 5-Class Agronomic).
   - Value stretch controls (Min/Max clamp, e.g., $-0.2$ to $+1.0$).
5. **Layer Catalog & Generation History**:
   - Table of generated raster layers: Layer Name, Formula, Generation Date, Processing Time, Storage Size, "View in Portal (Page 4)", "View Diagnostics (Page 5)".

### C. Required Data
- Input orthomosaic GeoTIFF raster stream from Azure Blob Storage.
- Band mapping dictionary `{ "nir": 4, "red": 1, "green": 2, "red_edge": 5 }`.
- Algorithm configuration parameters (selected indices, $L$ factor, nodata values).

### D. User Actions
- Select registered orthomosaic.
- Confirm or adjust spectral band mappings.
- Select desired vegetation indices.
- Run calculation task.
- Inspect calculation summary, histogram preview, and publish verified layers to the survey record.

### E. States (Empty, Loading, Error, Success)
- **Empty State**: No orthomosaic selected; guides user to select an available orthomosaic from Page 1 or 2.
- **Loading State**: Background Celery task processing raster chunks; displays chunk progress indicator (e.g., "Processing tile 42 of 120...").
- **Error State**: Spectral mismatch (e.g., attempting NDVI on 3-band RGB imagery triggers explicit warning: *"RGB imagery lacks Near-Infrared band. NDVI cannot be computed."*); division by zero handled gracefully without NaN crashes.
- **Success State**: Generation completed; displays output raster details, histogram thumbnail, and direct navigation links to Pages 4 and 5.

### F. Page-Specific Validation & Acceptance Criteria
- **AC-P3-01**: Must strictly forbid execution of NDVI, NDRE, GNDVI, or SAVI if required spectral bands are not verified.
- **AC-P3-02**: All pixel math operations must utilize masked NumPy arrays ignoring NoData values and clamping results to $[-1.0, +1.0]$.
- **AC-P3-03**: Output rasters must preserve the exact input spatial geotransform and CRS of the source orthomosaic.

---

## 5. Page 4 — Secure Farmer Portal

### A. Purpose & High-Level Scope
The primary user-facing visualization and discovery environment for authorized farmers and landowners. Delivers a responsive, intuitive, high-performance spatial map viewer (MapLibre GL JS) to inspect published survey layers, view legends, toggle base layers, and download verified outputs.

### B. Core Components & Controls
1. **Tenant Survey Switcher**:
   - Farm / Field selector filtered strictly to the logged-in user's tenant ownership.
   - Timeline selector / Date slider showing historical surveys for the chosen field.
2. **Interactive Geospatial Map Canvas (MapLibre GL JS)**:
   - Base map selector (Satellite Basemap, OpenStreetMap, Topo).
   - High-resolution raster layer overlay with smooth zoom and pan.
   - Field boundary vector overlay (polygon outline).
3. **Layer Control & Opacity Panel**:
   - Radio / Checkbox toggle for active layers:
     - True Color RGB Orthomosaic
     - NDVI Map Layer
     - NDRE Map Layer
     - GNDVI Map Layer
     - SAVI Map Layer
   - Layer opacity slider ($0\%$ to $100\%$).
   - Dual-layer swipe / split-screen comparison slider (e.g., RGB Orthomosaic vs. NDVI).
4. **Dynamic Scientific Legend**:
   - Color ramp display mapped to index values (e.g., $-1.0$ to $+1.0$).
   - Qualitative agronomic classification brackets (e.g., Bare Soil / Water: $< 0.1$, Sparse / Stressed Vegetation: $0.1 - 0.33$, Moderate Canopy: $0.34 - 0.66$, Dense / Vigorous Canopy: $> 0.66$).
5. **Deliverables & Download Drawer**:
   - Secure download links for:
     - Survey Summary Report (PDF)
     - Full Resolution Orthomosaic (GeoTIFF via authorized SAS URL)
     - Vegetation Index Layer (GeoTIFF via authorized SAS URL)
   - Action link: "View In-Depth Diagnostics (Page 5)".

### C. Required Data
- Authenticated user tenant ID and allowed farm/field list.
- PostGIS boundary geometry for the field.
- Raster tile service URLs (XYZ / TMS or COG range requests) for published survey layers.
- Published ReportLab PDF and GeoTIFF download metadata.

### D. User Actions
- Select field and historical survey date.
- Toggle between RGB and vegetation index layers.
- Adjust layer opacity and compare before/after or RGB vs. NDVI using swipe comparison.
- Click on map to read localized index values at pointer coordinates (pixel value probe).
- Download official PDF report or GeoTIFF.

### E. States (Empty, Loading, Error, Success)
- **Empty State**: No surveys published yet for the selected field; shows friendly notice: *"No processed survey maps are available yet for this field. Please check back once drone processing is complete."*
- **Loading State**: Map tiles loading placeholder with subtle spinner; smooth fading as tiles render.
- **Error State**: Raster layer fails to load or access token expired; displays non-intrusive alert with "Refresh Map" option.
- **Success State**: Responsive, crisp vector and raster rendering with active legend and responsive coordinate inspector.

### F. Page-Specific Validation & Acceptance Criteria
- **AC-P4-01**: Must enforce strict tenant isolation; user cannot view, request, or tile rasters from farms outside their authorized access list.
- **AC-P4-02**: All file download URLs must be short-lived, signed Azure SAS links (e.g., 15-minute expiration) generated on-demand by the backend.
- **AC-P4-03**: Must display clear, explanatory badges if a survey only has RGB imagery and no multispectral index maps.

---

## 6. Page 5 — Diagnostics & Actionable Insights

### A. Purpose & High-Level Scope
The agronomic evaluation and reporting dashboard. Provides transparent, data-supported statistical observations derived from actual raster pixel data, documents processing limitations, flags data anomalies, and generates publication-grade PDF reports via ReportLab.

### B. Core Components & Controls
1. **Survey & Index Context Header**:
   - Displays Field Name, Crop Type, Flight Date, Sensor, Selected Index (e.g., NDVI).
2. **Statistical Distribution Summary Cards**:
   - **Mean Index Value** (e.g., $0.62$).
   - **Median Index Value** (e.g., $0.65$).
   - **Standard Deviation** (e.g., $\pm 0.14$, indicating spatial variability).
   - **Minimum & Maximum Clamped Values**.
   - **Total Mapped Area** (Hectares / Acres).
3. **Zonal Vegetation Breakdown Chart & Table**:
   - Categorized area breakdown:
     - High Vigour / Dense Biomass ($> 0.6$): Area & % of field.
     - Moderate Vigour ($0.3 - 0.6$): Area & % of field.
     - Low Vigour / Stressed ($0.1 - 0.3$): Area & % of field.
     - Non-Vegetated / Bare Ground ($< 0.1$): Area & % of field.
   - Interactive bar/donut chart visualization.
4. **Data Quality & Limitations Disclosure Box**:
   - System limitations reporting:
     - Cloud / Shadow Cover Detection flags.
     - Sun angle / Hotspot reflections warning.
     - Radiometric calibration status (Calibrated Reflectance vs. Relative DN).
     - Explicit disclaimer: *"Index variability reflects canopy reflectance differences; ground scouting is required to verify agronomic root causes (moisture, pests, soil compaction)."*
5. **PDF Report Generator & Archive Card**:
   - Configuration options: Include RGB Ortho thumbnail, Include Histogram, Include Field Notes.
   - Primary Action Button: "Generate Verified PDF Report".
   - Recent Reports List: Download previously compiled reports with timestamp and file size.

### C. Required Data
- NumPy statistical array outputs stored in PostgreSQL (mean, median, standard deviation, percentile buckets, area per class).
- Survey metadata, field boundaries, and user notes.
- ReportLab PDF generator service endpoint.

### D. User Actions
- Select survey and active index layer for diagnostic review.
- Filter or adjust zonal threshold brackets.
- Read data quality warnings and limitation notes.
- Trigger PDF report generation.
- Download generated PDF report.

### E. States (Empty, Loading, Error, Success)
- **Empty State**: Survey index has not been computed yet; prompts user to run Page 3 calculations first.
- **Loading State**: PDF generation in progress; displays spinner: *"Compiling geospatial charts and assembling PDF report..."*
- **Error State**: Statistics calculation failed due to corrupted raster or zero valid pixels within field boundary; alerts user with actionable error message.
- **Success State**: Fully populated statistical dashboard with interactive charts, clear data limitations disclosure, and instant PDF download availability.

### F. Page-Specific Validation & Acceptance Criteria
- **AC-P5-01**: Area calculations must be derived from actual pixel spatial resolution ($GSD^2 \times \text{pixel count}$) clipped to the field polygon geometry.
- **AC-P5-02**: The platform must explicitly refrain from automated pathogen diagnosis, yield forecasting, or fertilizer chemical prescriptions.
- **AC-P5-03**: Generated PDF reports must contain standard header/footer metadata, date of flight, sensor identity, data limitations disclaimer, and complete calculation provenance.
