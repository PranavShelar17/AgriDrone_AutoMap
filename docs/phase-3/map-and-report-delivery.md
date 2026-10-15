# AgriDrone AutoMap — Map & Report Delivery Architecture
## Document Reference: `docs/phase-3/map-and-report-delivery.md`
**Phase**: Phase 3 — System Architecture, Technical Validation & Implementation Blueprint  
**Status**: APPROVED ARCHITECTURE BLUEPRINT  
**Version**: 1.0.0  

---

## 1. Interactive Map Delivery Architecture (Page 4)

The farmer-facing interactive map viewer is powered by **MapLibre GL JS 4+** in the Next.js frontend, rendering both vector cadastral boundaries and multi-layer raster drone imagery.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                   MAPLIBRE GL JS CLIENT CANVAS (Browser)                    │
│   - Base Map Tiles (CartoDB / OpenStreetMap / Esri Satellite)               │
│   - Vector Layer: Farm Cadastral Parcel (GeoJSON from PostGIS)              │
│   - Raster Layer A: True-Color Orthomosaic COG Tiles                        │
│   - Raster Layer B: Colormapped Vegetation Index (VARI/NDVI) COG Tiles      │
│   - Split-Screen Comparison Slider (Layer A vs Layer B)                     │
│   - Pixel Value Probe Inspector (Click coordinates -> Index value)          │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                ▼                                             ▼
┌───────────────────────────────┐             ┌───────────────────────────────┐
│       FASTAPI BACKEND         │             │    DYNAMIC TILE SERVER /      │
│ - Serves Field Vector GeoJSON │             │     AZURE BLOB COG TILES      │
│ - Resolves Layer SAS Tokens   │             │ - Serves Web Mercator XYZ     │
│ - Provides Layer Metadata     │             │   tms tiles ({z}/{x}/{y}.png) │
│ - Verifies Tenant Permissions │             │ - Reads Cloud-Optimized Tiffs │
└───────────────────────────────┘             └───────────────────────────────┘
```

---

## 2. Raster Tile Serving Strategies

Multi-gigabyte drone rasters cannot be pushed directly to a web browser. The architecture defines two supported raster delivery mechanisms:

### Option A: Dynamic COG Tiler (TiTiler / FastAPI Raster Tile Endpoint) — *Recommended*
- A lightweight dynamic tile endpoint (`/api/v1/tiles/{product_id}/{z}/{x}/{y}.png`) reads the Cloud-Optimized GeoTIFF stored in Azure Blob Storage via HTTP range requests.
- The server applies the requested colormap (e.g. `RdYlGn` or `Viridis`) on the fly and returns pre-rendered $256 \times 256$ PNG tiles.
- **Advantages**: Compatible with all standard web map viewers, fast initial render, minimal client memory usage, zero raster decoding in JavaScript.

### Option B: Client-Side COG Protocol (geotiff.js + WebGL Shader)
- MapLibre uses a custom WebGL raster layer with `geotiff.js` to fetch byte ranges directly from Azure Blob Storage via SAS URLs.
- Colormapping is executed in the client GPU via WebGL fragment shaders.
- **Advantages**: Zero server compute for tile rendering.
- **Trade-offs**: Higher client CPU/GPU requirements on low-end mobile devices.

*Decision*: In accordance with Phase 3 open decisions, Option A (Dynamic Tiling via backend FastAPI / TiTiler proxy) is the primary architecture recommendation to guarantee smooth performance across farmer mobile devices.

---

## 3. Interactive Map Controls & Features

1. **Split-Screen Comparison Mode**:
   - Implemented using the MapLibre split-screen compare control.
   - The user can drag a vertical divider to inspect the True-Color Orthomosaic on the left and the Calibrated Vegetation Index (VARI/NDVI) on the right.
2. **Layer Opacity & Colormap Legend**:
   - Opacity slider ($0\%$ to $100\%$) allows blending the index layer with the base satellite layer.
   - Continuous color ramp displays the physical index scale (e.g. $-0.2$ to $+0.8$) paired with semantic health categories (High Vigour, Moderate, Stressed, Bare Soil).
3. **Pixel Value Inspector (Probe Tool)**:
   - Clicking any point within the field boundary executes a point query returning:
     - Geographic Coordinate (Latitude, Longitude in WGS84)
     - UTM Projected Coordinate (Easting, Northing)
     - Raw Index Value (e.g. `VARI = 0.52`)
     - Classification (`"High Vigour"`)

---

## 4. ReportLab PDF Generation Architecture (Page 5)

AgriDrone AutoMap generates publication-grade, multi-page PDF audit reports using **ReportLab 4+** running within Celery worker processes.

```
[Report Generation Request] ──► [Celery Worker: tasks_report.compile_pdf]
                                        │
                                        ├── Fetch Survey & Farm Metadata from PostGIS
                                        ├── Fetch High-Res Overview Render from Azure
                                        ├── Fetch Zonal Area Statistics & Histogram
                                        ├── Render ReportLab Document Template
                                        │     ├── Page 1: Executive Cover & Field Map
                                        │     ├── Page 2: Index Visualizations & Histograms
                                        │     └── Page 3: Zonal Breakdown & Disclaimers
                                        └── Upload PDF to Azure reports/ Container
```

### 4.1. Report Structure & Agronomic Content
1. **Header & Cadastral Block**:
   - Farm Name, Village, Taluka, District, State.
   - Survey Code, Flight Date, Pilot, Drone Model, Sensor Type, Flight Altitude (AGL).
   - Total Surveyed Acreage / Hectares.
2. **Visual Map Figures**:
   - True-Color Orthomosaic thumbnail with cadastral field boundary overlay.
   - Calibrated Vegetation Index map with embedded color ramp bar and scale indicator.
3. **Statistical & Zonal Breakdown**:
   - Global metrics: Mean, Median, Minimum, Maximum, Standard Deviation.
   - Area distribution table (Acreage and percentage across High Vigour, Moderate Vigour, Stressed, and Non-Vegetated zones).
   - Pixel frequency distribution histogram.
4. **Mandatory Scientific Disclaimer**:
   - *"Notice: This report reflects optical surface reflectance measurements captured by an uncrewed aerial vehicle on the specified survey date. Spectral vegetation indices are diagnostic indicators of relative canopy vigour and do not constitute an autonomous diagnosis of specific crop diseases, insect infestations, or yield projections. Recommendations must be verified via ground-truth field inspection and certified soil/tissue laboratory testing."*

---

## 5. Secure Asset Delivery & SAS Token Governance

All compiled PDF reports and raw GeoTIFF exports are protected by strict access controls:
1. File downloads are **never served directly through public URLs**.
2. When a user requests a file download, FastAPI validates the user's tenant ownership.
3. FastAPI generates a temporary **15-minute expiring Azure SAS URL** (`BlobSasPermissions(read=True)`).
4. The frontend triggers a direct browser download from Azure Blob Storage.
5. Once the SAS token expires, the URL becomes invalid, preventing unauthorized link sharing.
