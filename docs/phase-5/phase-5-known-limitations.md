# AgriDrone AutoMap — Phase 5 Known Limitations
## Document Reference: `docs/phase-5/phase-5-known-limitations.md`
**Phase**: Phase 5 — Admin Dashboard, Farm/Survey Management & Drone Image Ingestion  
**Status**: APPROVED LIMITATIONS DISCLOSURE  
**Version**: 1.0.0  

---

## 1. Architectural & Scope Boundaries

In accordance with the approved master prompt and technical blueprint, the following limitations are intentional for Phase 5:

1. **Storage Provider**:
   - Tested under the **Local Development Storage Adapter** (`LocalStorageService` storing to `backend/storage/raw-surveys/`).
   - Azure Blob Storage SDK integration is coded, configured, and ready in `AzureBlobStorageService`, but was not run against live Azure cloud endpoints because no Azure credentials were provided, completely preventing unwanted cloud billing.
2. **WebODM Photogrammetry Processing**:
   - Phase 5 accepts and validates raw drone photographs (`RAW_IMAGE`) and marks them as `ELIGIBLE_FOR_WEBODM_PHOTOGRAMMETRY`.
   - Actual 3D photogrammetry reconstruction, dense point cloud generation, and orthomosaic stitching belong strictly to **Phase 6**.
3. **Spectral Algorithm Computations**:
   - Phase 5 accepts and validates pre-stitched GeoTIFF rasters (`GEOTIFF`) and marks them as `ELIGIBLE_FOR_DIRECT_GIS`.
   - Calculation of vegetation indices (NDVI, NDRE, GNDVI, SAVI) belongs strictly to **Phase 7**.
4. **Interactive Map Visualizer & Farmer Portal**:
   - MapLibre GL layer rendering of multi-spectral bands belongs to **Phase 8**.
   - Farmer portal authentication, multi-tenant farm access delegation, and farmer-specific views belong to **Phase 9**.
5. **Browser Subagent Driver Network Limit**:
   - In the local execution environment, the automated Playwright driver download failed due to external CDN 404 access restrictions.
   - All frontend compilation, types, route rendering (HTTP 200), and API endpoints were independently verified through Next.js static page generation and HTTP diagnostic probes.
