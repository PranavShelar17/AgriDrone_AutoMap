# Output and Map Delivery — WebODM Photogrammetry

This document outlines the delivery architecture for photogrammetric outputs (Orthophotos, Digital Surface Models, Digital Terrain Models) and their interactive visualization in MapLibre GL JS.

---

## 1. Raster Output Formats & Architecture

A completed photogrammetry task produces three primary geospatial deliverables:
1. **Orthophoto (`orthophoto.tif`)**: Radiometrically balanced, geometrically corrected 2D aerial mosaic (RGB or multispectral).
2. **Digital Surface Model (`dsm.tif`)**: Elevation model including crop canopy tops, trees, and farm structures.
3. **Digital Terrain Model (`dtm.tif`)**: Bare-earth elevation model derived from point-cloud ground classification.

### 1.1 Cloud-Optimized GeoTIFF (COG) Pipeline
To prevent massive multi-gigabyte raster downloads in the client browser, AgriDrone AutoMap converts completed WebODM GeoTIFFs into **Cloud-Optimized GeoTIFFs (COGs)**:
- Internally tiled (256x256 pixel blocks).
- Pre-computed pyramid overviews (power of 2 decimation).
- Deflate compression with predictor for minimal storage overhead.
- HTTP Range Request enabled on Azure Blob Storage.

---

## 2. Dynamic Tile Serving & Raster Proxy

WebODM incorporates a dynamic raster tile server (`app/api/tiler.py`). AgriDrone AutoMap proxies and wraps these tile endpoints behind its authenticated FastAPI gateway:

```
Client (MapLibre GL JS)
   │
   │  GET /api/v1/photogrammetry/tasks/{task_id}/tiles/{type}/{z}/{x}/{y}.png
   ▼
FastAPI Gateway (verify_task_access)
   │
   │  Proxy request with Server-to-Server JWT
   ▼
WebODM Tiler Service (app/api/tiler.py)
   │
   ▼
Reads internal COG and renders 256x256 PNG tile
```

### 2.1 Tile Endpoints Specification
- **TMS/XYZ Tile Stream**:
  `GET /api/v1/photogrammetry/tasks/{task_id}/tiles/{tile_type}/{z}/{x}/{y}.png`
  - `tile_type`: `orthophoto` | `dsm` | `dtm`
  - Query parameters:
    - `colormap`: Colormap identifier for elevation rasters (`viridis`, `plasma`, `magma`, `inferno`, `terrain`, `greys`).
    - `hillshade`: `1` (renders live dynamic hillshade relief on DSM/DTM).
    - `min`, `max`: Clamps elevation min/max thresholds in meters.
- **Raster Spatial Bounds**:
  `GET /api/v1/photogrammetry/tasks/{task_id}/tiles/{tile_type}/bounds`
  - Returns `[minX, minY, maxX, maxY]` in EPSG:4326 for automated map centering and bounding-box zooming.
- **Raster Technical Metadata**:
  `GET /api/v1/photogrammetry/tasks/{task_id}/tiles/{tile_type}/metadata`
  - Returns pixel dimensions, GSD resolution (cm/px), band count, NoData values, and color histograms.

---

## 3. MapLibre GL JS Integration

AgriDrone AutoMap utilizes **MapLibre GL JS** (`frontend/components/MapLibreViewer.tsx`) for GPU-accelerated raster and vector rendering.

### 3.1 Layer Management & Opacity
- **Basemap Layer**: High-contrast satellite imagery or OpenStreetMap base tiles.
- **Drone Raster Layer**: Rendered as a raster source with user-adjustable opacity slider (0% to 100%).
- **Field Boundary Layer**: Vector GeoJSON overlay from PostGIS depicting the official field boundary perimeter with dashed green styling.
- **Elevation Legends**: Dynamic gradient bar showing elevation range (min to max meters) when DSM/DTM layers are active.

### 3.2 Security & Access Controls on Map Tiles
Every tile request is authenticated via Bearer JWT. The backend enforces:
- Scoped tenant validation: Farmers can only load tiles for tasks belonging to their assigned farms.
- Unauthorized requests receive `403 Forbidden` or `404 Not Found` (never leaking internal file paths).
- Tile URLs never expose WebODM's internal server port or JWT token.
