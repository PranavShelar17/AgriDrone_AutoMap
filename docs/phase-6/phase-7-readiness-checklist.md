# AgriDrone AutoMap — Phase 7 Readiness Checklist
## Document Reference: `docs/phase-6/phase-7-readiness-checklist.md`
**Target Phase**: Phase 7 — Spectral Algorithms & Multi-Map Generation Engine  
**Status**: READINESS VERIFICATION COMPLETE  
**Version**: 1.0.0  

---

## 1. Prerequisites Met in Phase 6

| Prerequisite | Status | Verification Reference |
| :--- | :--- | :--- |
| **Photogrammetry Task Lifecycle** | ✅ READY | `photogrammetry_tasks` and `task_logs` managed with `SUBMITTED`, `RUNNING`, `COMPLETED`, `FAILED`, `CANCELLED` states. |
| **Map Products Catalog** | ✅ READY | `map_products` table wired with `ORTHOPHOTO`, `DSM`, `DTM` types, spatial EPSG CRS, resolution cm/px, and storage URIs. |
| **Dataset Ingestion & Eligibility** | ✅ READY | Raw photo datasets routed to WebODM; pre-stitched GeoTIFF rasters correctly preserved for direct Phase 7 ingestion. |
| **Celery Queue Infrastructure** | ✅ READY | Celery application configured with Redis broker on port `6380`, ready to host `raster_compute` queue in Phase 7. |
| **Frontend WebODM Center** | ✅ READY | Page 2 operational with live cluster health, options presets, real-time progress bar, monospace terminal, and artifact table with "Proceed to Algorithms" handoff link. |
| **Backend Test Suite** | ✅ READY | 34 automated unit and integration tests passing in 19 seconds. |

---

## 2. Phase 7 Scope Hand-Off

When the user initiates **Phase 7**, the system will implement:
1. **Spectral Band Inspection Service**: Detect RGB vs Multispectral (Red, Green, Blue, RedEdge, NIR) bands from registered `map_products` orthophotos.
2. **Algorithm Eligibility Matrix**: Validate mathematical feasibility of vegetation indices (NDVI, NDRE, GNDVI, VARI, GLI, SAVI) based on available sensor channels.
3. **GDAL / Rasterio / NumPy Computation Engine**: High-performance asynchronous numpy floating-point band math producing Cloud-Optimized GeoTIFF (COG) index rasters.
4. **Zonal Health Classification**: Automated statistical distribution and histogram thresholding (High Vigour, Moderate, Stressed, Bare Soil) written to `zonal_statistics`.
5. **Page 3 (Algorithm & Multi-Map Generation) UI**: Interactive band selector, algorithm execution triggers, side-by-side comparison, and layer publication toggle.

> [!IMPORTANT]
> Do NOT start Phase 7 automatically. Wait for explicit user review and approval of Phase 6 deliverables.
