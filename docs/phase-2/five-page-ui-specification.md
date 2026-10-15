# AgriDrone AutoMap — Five-Page UI Specification

## 1. Architectural Layout Architecture

Every page in AgriDrone AutoMap adheres to the reference template's layout hierarchy:
1. **Global Sticky Top Navbar** (`h-16`, `border-b border-slate-200 bg-white/90 backdrop-blur-md`): Brand lockup, universal navigation tabs for the 5 pages, NodeODM service status pill, user role pill, and logout.
2. **Page Header Bar**: Context breadcrumb, page title, brief operational subtitle, and primary right-aligned action button.
3. **Main Content Container**: Constrained to `max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6` with responsive vertical rhythm (`space-y-6`).

---

## 2. Page 1 — Admin Dashboard & Drone Image Ingestion (`/admin/dashboard`)

### A. Layout Structure & Wireframe
```
+-----------------------------------------------------------------------------------------------+
| NAVBAR: [Logo] AgriDrone AutoMap  |  Ingestion  WebODM  Algorithms  Farmer Portal  Diagnostics|
+-----------------------------------------------------------------------------------------------+
| HEADER: Admin Dashboard > Drone Ingestion                                                     |
| Title: Survey Management & Imagery Ingestion                                                  |
+-----------------------------------------------------------------------------------------------+
| +-----------------------------------------------+ +-----------------------------------------+ |
| | CARD 1: Spatial Hierarchy Selector           | | CARD 2: Pre-Flight Validation Card        | |
| | - Farm Select: [ GreenValley Farms (ID 12) v] | | - Status: Ready for Validation            | |
| | - Field Boundary: [ North Pivot 4 (32 ha) v]  | | - CRS: EPSG:32632 (UTM Zone 32N)          | |
| | - Survey Flight Date: [ 2026-10-14 ]          | | - Detected Bands: 5 (Blue,Green,Red,RE,NIR)| |
| | - Camera/Sensor: [ MicaSense RedEdge-P    v]  | | - Geotag Rate: 98.4% (342/348 photos)     | |
| | - Altitude: [ 80 m ]                          | | - Eligibility: [ ELIGIBLE FOR WEBODM ]    | |
| +-----------------------------------------------+ +-----------------------------------------+ |
| +-------------------------------------------------------------------------------------------+ |
| | CARD 3: Dual-Mode Ingestion Dropzone                                                      | |
| | [ Mode A: Raw Drone Photo Batch ]       [ Mode B: Pre-Stitched GeoTIFF Raster ]           | |
| |                      ( Drag and drop flight photography or browse )                       | |
| |                      Allowed: .jpg, .dng, .tif, .tiff (Max 25 GB)                         | |
| |                      [ Select Photo Batch ]   [ Select GeoTIFF Raster ]                   | |
| +-------------------------------------------------------------------------------------------+ |
| +-------------------------------------------------------------------------------------------+ |
| | CARD 4: Dataset & Eligibility Ledger Table                                                | |
| | Survey ID | Date       | Files | Size   | Type     | Validation Status  | Next Action     | |
| | SURV-101  | 2026-10-14 | 348   | 4.2 GB | Raw MS   | [ Eligible WebODM ]| [ Send to P2 ->]| |
| | SURV-102  | 2026-10-12 | 1     | 1.8 GB | GeoTIFF  | [ Direct GIS ]     | [ Send to P3 ->]| |
| +-------------------------------------------------------------------------------------------+ |
+-----------------------------------------------------------------------------------------------+
```

### B. Controls & Component Inventory
1. **Spatial Hierarchy Selector**:
   - Farm Dropdown with inline "+ New Farm" modal trigger.
   - Field Boundary Dropdown with GeoJSON/Shapefile upload modal.
   - Flight Parameters: Date picker, Sensor selector (DJI P4M, MicaSense, RGB, Custom), Altitude input.
2. **Dual-Mode Dropzone**:
   - Mode Toggle Buttons: "Raw Drone Photos" (batch) vs "Pre-Stitched GeoTIFF" (single raster).
   - Drag-and-drop listener highlighting on dragover (`border-emerald-500 bg-emerald-50/30`).
   - Hidden folder and file inputs allowing whole-directory uploads.
3. **Pre-Flight Validation Card**:
   - Displays real-time metadata extracted from the upload stream: CRS, GSD, Band Count, Geotag percentage.
   - Prominent eligibility badge: `ELIGIBLE FOR WEBODM`, `ELIGIBLE FOR DIRECT GIS`, or `INVALID METADATA`.
4. **Dataset & Eligibility Ledger**:
   - Paginated table showing recent surveys, file counts, sizes, status badges, and direct navigation links to Page 2 or Page 3.

### C. UI States
- **Empty State**: No surveys exist. Dropzone displays an illustrative folder icon with helper text: *"No flight surveys uploaded yet. Create a farm and upload your first aerial survey."*
- **Loading State**: Upload progress bar with transfer rate (e.g. `14.2 MB/s`), elapsed time, ETA, and pulsing upload badge.
- **Success State**: "Validation Passed" emerald banner with extracted GSD and button: *"Proceed to WebODM Photogrammetry ->"*.
- **Warning State**: "12 photos lack EXIF coordinates (96% geotagged). Minimum 90% threshold satisfied."
- **Error State**: Rose banner: *"Upload Failed: File is not a valid GeoTIFF or lacks projected coordinate reference system (CRS)."*

---

## 3. Page 2 — WebODM Photogrammetry Processing (`/admin/photogrammetry`)

### A. Layout Structure & Wireframe
```
+-----------------------------------------------------------------------------------------------+
| HEADER: Processing > WebODM Photogrammetry Console                                            |
| Title: Aerial Reconstruction & Orthomosaic Stitching                                          |
+-----------------------------------------------------------------------------------------------+
| +-----------------------------------------------+ +-----------------------------------------+ |
| | CARD 1: Task Configuration Panel              | | CARD 2: NodeODM Cluster Status          | |
| | - Select Survey: [ SURV-101 (348 photos)   v] | | - Node Status: [ NodeODM Online (Pulse) ] | |
| | - Preset: (o) Ag Fast  ( ) High Precision     | | - Active Jobs on Node: 1 / 4 Nodes      | |
| | - Target GSD: [ 2.5 cm/px ]                   | | - Host: http://nodeodm:3000             | |
| | - Generate DSM / DTM: [x] Yes                 | | - RAM Usage: 14.2 GB / 32.0 GB          | |
| | - Radiometric Calibration: [x] Enable         | |                                         | |
| | [ Start Photogrammetry Reconstruction ]       | |                                         | |
| +-----------------------------------------------+ +-----------------------------------------+ |
| +-------------------------------------------------------------------------------------------+ |
| | CARD 3: Active Task Execution & Progress Bar                                              | |
| | Task: WebODM-Task-4829 | Status: [ PROCESSING (Spin) ] | Stage: OpenSfM Feature Matching  | |
| | [===========================================>                        ] 64% Complete       | |
| | Elapsed: 18m 42s | Estimated Remaining: 10m 15s | [ Cancel Task ]                         | |
| +-------------------------------------------------------------------------------------------+ |
| +-------------------------------------------------------------------------------------------+ |
| | CARD 4: Live Task Terminal & Diagnostic Log Feed (Monospace, Auto-scrolling)              | |
| | [2026-10-14 12:22:04] INFO: Found 348 images with EXIF GPS data                           | |
| | [2026-10-14 12:23:15] INFO: Running OpenSfM feature extraction (sift)...                 | |
| | [2026-10-14 12:28:40] INFO: 342 / 348 images successfully aligned in bundle adjustment    | |
| | [2026-10-14 12:35:10] INFO: Computing dense point cloud with OpenMVS...                   | |
| +-------------------------------------------------------------------------------------------+ |
| +-------------------------------------------------------------------------------------------+ |
| | CARD 5: Generated Artifacts Ledger                                                        | |
| | Artifact Name          | Format  | Size   | Status     | Registration Action              | |
| | orthophoto.tif         | GeoTIFF | 1.8 GB | Completed  | [ Register & Open in Page 3 -> ] | |
| | dsm.tif                | GeoTIFF | 640 MB | Completed  | [ Stored in Azure Storage ]      | |
| +-------------------------------------------------------------------------------------------+ |
+-----------------------------------------------------------------------------------------------+
```

### B. Controls & Component Inventory
1. **Task Configuration Panel**:
   - Survey dropdown filtered strictly to datasets tagged `ELIGIBLE_WEBODM`.
   - Preset radio toggles: *Agricultural Fast* (lower densification, rapid orthomosaic), *High Precision* (full point cloud, DSM, DTM), *Custom*.
   - Target GSD slider/input (cm/pixel).
   - Checkboxes for DSM generation and Radiometric calibration panel auto-detection.
2. **Cluster Health Pill**:
   - Shows live WebODM / NodeODM container connectivity with pulsing status dot.
3. **Execution Console & Progress**:
   - Dynamic progress bar updating via polling or WebSocket.
   - Cancel button triggering task termination.
4. **Diagnostic Terminal**:
   - Dark slate monospace console (`bg-slate-900 text-slate-100 p-4 rounded-xl font-mono text-xs h-64 overflow-y-auto`) streaming WebODM stdout logs.
5. **Artifact Registration Ledger**:
   - Table of generated outputs (`orthophoto.tif`, `dsm.tif`, `report.pdf`) with one-click action to store in Azure and proceed to Page 3.

### C. UI States
- **Empty State**: No task running; prompt guides operator to select an eligible survey and initiate reconstruction.
- **Loading State**: Progress bar active, terminal streaming log lines, buttons disabled except "Cancel Task".
- **Success State**: "Reconstruction Complete: Orthomosaic generated (1.8 GB, 2.4 cm GSD)." Buttons: *"Proceed to Algorithm Engine (Page 3) ->"*.
- **Warning State**: "OpenSfM notice: 6 images could not be registered due to low feature overlap. Continuing reconstruction."
- **Error State**: Red terminal highlight: *"WebODM Error: Insufficient matching features found. Ensure camera photos have at least 70% forward overlap."*

---

## 4. Page 3 — Algorithm & Multi-Map Generation (`/admin/algorithms`)

### A. Layout Structure & Wireframe
```
+-----------------------------------------------------------------------------------------------+
| HEADER: GIS Analytics > Algorithm & Multi-Map Generation                                      |
| Title: Spectral Band Mapping & Vegetation Index Generation                                    |
+-----------------------------------------------------------------------------------------------+
| +-------------------------------------------------------------------------------------------+ |
| | CARD 1: Orthomosaic Dataset Selection                                                     | |
| | Select Orthomosaic: [ SURV-101 - North Pivot 4 (MicaSense 5-Band Ortho)                 v] | |
| | Source: WebODM Ingestion | CRS: EPSG:32632 | Dimensions: 12400 x 9800 px | Bands: 5       | |
| +-------------------------------------------------------------------------------------------+ |
| +-------------------------------------------------------------------------------------------+ |
| | CARD 2: Spectral Band Mapping & Verification Grid                                         | |
| | Raster Band | Detected Name | Assigned Spectral Role  | Status                            | |
| | Band 1      | Blue (475 nm) | [ Blue             v]   | [ Valid ]                         | |
| | Band 2      | Green (560 nm)| [ Green            v]   | [ Valid ]                         | |
| | Band 3      | Red (668 nm)  | [ Red              v]   | [ Valid ]                         | |
| | Band 4      | RE (717 nm)   | [ Red Edge         v]   | [ Valid ]                         | |
| | Band 5      | NIR (840 nm)  | [ Near-Infrared    v]   | [ Valid ]                         | |
| +-------------------------------------------------------------------------------------------+ |
| +-------------------------------------------------------------------------------------------+ |
| | CARD 3: Algorithm Selection & Parameter Matrix                                            | |
| | [x] NDVI  ((NIR - Red) / (NIR + Red))                   | [ Eligible: NIR & Red Verified ]| |
| | [x] NDRE  ((NIR - RE) / (NIR + RE))                     | [ Eligible: NIR & RE Verified ] | |
| | [ ] GNDVI ((NIR - Green) / (NIR + Green))               | [ Eligible: NIR & Green Valid ] | |
| | [x] SAVI  ((1+L)(NIR - Red)/(NIR + Red + L))            | [ Eligible ] Soil Factor L: [0.5] |
| |                                                                                           | |
| | Color Palette Preset: [ 5-Class Agronomic (RdYlGn) v]   Value Range: [ -0.20 ] to [ 0.85 ]| |
| | [ Generate Selected Vegetation Index Layers ]                                             | |
| +-------------------------------------------------------------------------------------------+ |
| +-------------------------------------------------------------------------------------------+ |
| | CARD 4: Generated Map Layers Catalog                                                      | |
| | Layer Name  | Index | Format | Size   | Generated At        | Quick Actions               | |
| | NDVI Layer  | NDVI  | COG    | 320 MB | 2026-10-14 12:45    | [ View in Portal (P4) ]     | |
| | NDRE Layer  | NDRE  | COG    | 315 MB | 2026-10-14 12:46    | [ View Diagnostics (P5) ]   | |
| +-------------------------------------------------------------------------------------------+ |
+-----------------------------------------------------------------------------------------------+
```

### B. Controls & Component Inventory
1. **Orthomosaic Selector**:
   - Dropdown of all registered orthomosaics (both WebODM-stitched and pre-stitched GeoTIFFs).
2. **Spectral Band Verification Grid**:
   - Interactive assignment table displaying internal raster bands with dropdowns for spectral roles (Red, Green, Blue, Red Edge, NIR).
   - Validation badge verifying whether physical requirements are satisfied.
3. **Algorithm Gating & Selection Matrix**:
   - Checkboxes for NDVI, NDRE, GNDVI, and SAVI.
   - **Strict Gating Logic**: If NIR is unassigned, all four index checkboxes are **disabled with an explicit alert**: *"Near-Infrared band is not assigned. Ordinary RGB imagery cannot generate NIR vegetation indices."*
   - SAVI Soil Adjustment slider ($L = 0.0$ to $1.0$, default $0.5$).
4. **Color Ramp & Styling Configurator**:
   - Palette picker: *5-Class Agronomic (RdYlGn)*, *Viridis*, *Spectral*.
   - Value stretch sliders (min clamp, max clamp).
5. **Generated Layers Ledger**:
   - Tabular list of produced Cloud Optimized GeoTIFFs with links to Page 4 and Page 5.

### C. UI States
- **Empty State**: No orthomosaic selected; prompts user to select a registered orthomosaic.
- **Loading State**: Background Celery task processing raster chunks; displays chunk progress indicator: *"Computing NDVI raster chunk 34 of 80..."*.
- **Success State**: Emerald confirmation banner: *"3 vegetation index layers successfully generated and converted to COG format."*
- **Warning State**: *"SAVI factor L set to 0.5. Verify soil condition if canopy cover exceeds 70%."*
- **Error State**: Rose banner: *"Invalid Spectral Configuration: Red band is assigned to multiple raster channels. Each spectral role must map to a unique band."*

---

## 5. Page 4 — Secure Farmer Portal (`/portal/surveys`)

### A. Layout Structure & Wireframe
```
+-----------------------------------------------------------------------------------------------+
| HEADER: Farmer Portal > Field Map Viewer                                                      |
| Farm: GreenValley Farms | Field: North Pivot 4 | Survey: 2026-10-14 (Corn - V6 Stage)         |
+-----------------------------------------------------------------------------------------------+
| +-------------------------------------------------------+ +---------------------------------+ |
| | MAP CONTAINER (MapLibre GL JS)                        | | SIDE PANEL: Controls & Legend   | |
| | +---------------------------------------------------+ | |                                 | |
| | | [ Satellite v ]  [ Zoom + / - ]  [ Split Swipe ]   | | | ACTIVE LAYER SELECTION:         | |
| | |                                                   | | | ( ) RGB True Color Orthomosaic  | |
| | |                                                   | | | (o) NDVI - Canopy Vigor         | |
| | |                  [ FIELD POLYGON ]                | | | ( ) NDRE - Chlorophyll Index    | |
| | |                                                   | | | ( ) SAVI - Soil Adjusted Vigor  | |
| | |                                                   | | |                                 | |
| | |                                                   | | | LAYER OPACITY: [=========] 85%  | |
| | |                                                   | | |                                 | |
| | |                                                   | | | DYNAMIC SCIENTIFIC LEGEND:      | |
| | |                                                   | | | [##] > 0.65  High Canopy (18 ha)| |
| | |                                                   | | | [##] 0.45-65 Moderate    (9 ha) | |
| | |   POPUP: Lat 45.1204, Lon 9.3402 | NDVI: 0.72     | | | [##] 0.30-45 Trans.      (3 ha) | |
| | |                                                   | | | [##] 0.15-30 Stressed    (1 ha) | |
| | |                                                   | | | [##] < 0.15  Bare/Water  (1 ha) | |
| | +---------------------------------------------------+ | |                                 | |
| | Basemap: Satellite | GSD: 2.5 cm | Clamped: -0.2 to 0.8 | [ Download Official Report (PDF)]| |
| +-------------------------------------------------------+ +---------------------------------+ |
+-----------------------------------------------------------------------------------------------+
```

### B. Controls & Component Inventory
1. **Tenant-Filtered Context Header**:
   - Dropdown of fields strictly owned by the logged-in farmer.
   - Survey timeline selector to compare historical flights.
2. **Interactive Map Canvas (MapLibre GL JS)**:
   - Base layer switcher (Satellite Imagery vs Clean Topographic).
   - High-performance raster layer overlay rendered via COG range-requests.
   - Vector field boundary outline.
   - Split-screen comparison swipe slider (comparing RGB Orthomosaic on left vs NDVI on right).
3. **Layer Control Panel**:
   - Radio buttons for available map layers.
   - Smooth continuous opacity slider ($0-100\%$).
4. **Dynamic Scientific Legend**:
   - Color ramp swatches paired with numeric intervals and agronomic labels.
5. **Pixel Value Probe Popup**:
   - Clicking on the map renders an anchor popup displaying coordinates and exact index value.
6. **Secure Download Drawer**:
   - Button to request temporary, short-lived (15-min) Azure SAS link for PDF report or GeoTIFF.

### C. UI States
- **Empty State**: Farmer has fields, but no surveys processed yet: *"No completed survey maps available yet for this field. Maps will appear once drone processing completes."*
- **Loading State**: MapLibre canvas shows subtle loading shimmer while fetching raster overviews.
- **Success State**: Crisp multi-layer map rendering with active legend and responsive click inspection.
- **Access Denied State**: Attempting to view another farmer's survey triggers clear tenant guard: *"Access Denied: You do not have permission to view surveys for this farm entity."*
- **Error State**: Rose banner: *"Map Tile Service Unavailable. Please refresh the viewer or contact your administrator."*

---

## 6. Page 5 — Diagnostics & Actionable Insights (`/portal/diagnostics`)

### A. Layout Structure & Wireframe
```
+-----------------------------------------------------------------------------------------------+
| HEADER: Analytics > Diagnostics & Actionable Insights                                         |
| Title: Field Statistics, Zonal Breakdown & Report Generation                                  |
+-----------------------------------------------------------------------------------------------+
| +-------------------------------------------------------------------------------------------+ |
| | STATISTICAL SUMMARY METRIC CARDS                                                          | |
| | [ Mean Index Value ]    [ Median Value ]    [ Standard Deviation ]   [ Total Field Area ] | |
| |       0.64                    0.68                 +/- 0.14                32.4 Hectares  | |
| | (Healthy Vigor)        (Dense Canopy)       (Moderate Variability)   (100% Valid Pixels)  | |
| +-------------------------------------------------------------------------------------------+ |
| +-----------------------------------------------+ +-----------------------------------------+ |
| | CARD 1: Zonal Canopy Health Distribution      | | CARD 2: Field Limitation Disclosures    | |
| | - Dense Canopy (>0.65):   18.2 ha (56.2%)     | | [!] Radiometric Status: Relative DN     | |
| | - Moderate Vigor (0.45-65):9.1 ha (28.1%)     | | [!] Cloud Shadow Artifacts: None        | |
| | - Transitional (0.30-45):  3.2 ha  (9.9%)     | | [!] Disclaimers & Limitations:          | |
| | - Stressed / Low (0.15-30):1.1 ha  (3.4%)     | |     Index maps measure canopy optical   | |
| | - Bare Ground (<0.15):     0.8 ha  (2.4%)     | |     reflectance. Ground scouting is     | |
| | [ Horizontal Stacked Distribution Bar Chart ] | |     required to confirm agronomic causes| |
| +-----------------------------------------------+ +-----------------------------------------+ |
| +-------------------------------------------------------------------------------------------+ |
| | CARD 3: PDF Survey Summary Report Generator                                               | |
| | Configuration: [x] Include RGB Thumbnail  [x] Include Histogram  [x] Include Field Notes  | |
| | Notes for Farmer: [ Field showed rapid canopy closure since last flight. Spot scouting...] | |
| | [ Generate Official PDF Report (ReportLab) ]                                              | |
| |                                                                                           | |
| | PREVIOUS COMPILED REPORTS:                                                                | |
| | - Report_SURV-101_20261014.pdf (2.4 MB)  -- [ Download via Secure SAS Link ]             | |
| +-------------------------------------------------------------------------------------------+ |
+-----------------------------------------------------------------------------------------------+
```

### B. Controls & Component Inventory
1. **Statistical KPI Metric Cards**:
   - 4-card grid showing Mean, Median, StdDev, and Mapped Acreage/Hectares.
2. **Zonal Canopy Health Breakdown**:
   - Interactive bar chart and structured data table displaying hectares and percentage per vigor bracket.
3. **Data Limitations & Disclaimers Disclosure Box**:
   - High-visibility callout specifying sensor calibration mode (Relative DN vs Calibrated Reflectance) and strict disclaimers against automated disease diagnosis.
4. **ReportLab PDF Generator Card**:
   - Checkboxes for report contents (RGB thumbnail, histogram, agronomist notes).
   - "Generate Official PDF Report" action button.
   - List of previously generated reports with secure download links.

### C. UI States
- **Empty State**: No index layers calculated yet; prompts operator to compute an index on Page 3.
- **Loading State**: PDF compilation in progress; spinner: *"Assembling geospatial histograms and formatting PDF report with ReportLab..."*.
- **Success State**: *"PDF Report successfully generated and archived in Azure Blob Storage."*
- **Warning State**: *"High spatial variability detected (StdDev > 0.22). Verify whether field includes mixed cultivars or uneven topography."*
- **Error State**: *"Calculation Error: No valid pixels found within field boundary polygon. Check boundary alignment."*
