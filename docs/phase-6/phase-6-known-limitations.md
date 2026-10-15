# AgriDrone AutoMap — Phase 6 Known Limitations
## Document Reference: `docs/phase-6/phase-6-known-limitations.md`
**Phase**: Phase 6 — WebODM / OpenDroneMap Integration & Drone Photogrammetry Processing  
**Status**: APPROVED LIMITATIONS REGISTER  
**Version**: 1.0.0  

---

## 1. WebODM Environment Availability

- **Local WebODM Cluster Status**: WebODM / NodeODM is not pre-installed or running on the local host on port 3001. The integration layer, client, task dispatcher, polling loop, and API contracts are fully implemented and verified via automated integration and mock tests. Full real-world photogrammetry processing requires starting the Docker container using `docker run -p 3001:3000 opendronemap/nodeodm:latest` or `docker compose --profile photogrammetry up -d nodeodm`.
- **Hardware Scale Limits**: Dense 3D reconstruction and orthomosaic generation require at least 8 GB of free RAM for 100-300 photos and 32+ GB for large agricultural surveys exceeding 500 photos.

---

## 2. Phase Boundaries & Out-of-Scope Features

1. **Vegetation Index Calculations (NDVI, NDRE, VARI, GLI, SAVI)**:
   - Strictly reserved for **Phase 7 (Algorithm & Multi-Map Generation)**.
   - Phase 6 stops at registering the georeferenced True-Color or Multispectral Orthophoto, DSM, and DTM in the `map_products` catalog.
2. **Interactive Map Visualizer & Tile Delivery**:
   - Web tile delivery (COG tile server / Titiler / MapLibre raster layers) is part of Phase 8.
   - In Phase 6, output deliverables are verified and cataloged with CRS and GSD metadata.
3. **Multi-Tenant User Login**:
   - Production farmer login and role-based permissions are scheduled for **Phase 9**.
   - Phase 6 administrative actions operate within the transparent development security boundary (`admin@agridrone.local`).
