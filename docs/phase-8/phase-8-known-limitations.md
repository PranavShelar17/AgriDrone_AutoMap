# Phase 8 Known Limitations & Future Considerations

## 1. Scope Boundaries Preserved
Phase 8 focuses exclusively on **interactive GIS mapping, multi-layer visualization, comparison workflows, and data-derived diagnostics**. Certain high-level features remain intentionally deferred according to the approved project roadmap:

---

## 2. Identified Limitations

### 1. Production Farmer Authentication (Deferred to Phase 9)
- Authentication in Phase 8 operates under the development boundary established in Phase 3.
- The UI contains a prototype "Tenant Guard (Denial State)" toggle to test unauthorized tenant rejection behavior.
- Full production farmer authentication with multi-tenant login, session cookies, and SMS OTP is scheduled for **Phase 9: Secure Farmer Portal & Mobile-First Experience**.

### 2. Multi-Polygon or Island Field Geometry
- PostGIS boundary endpoints currently support standard single polygons (`POLYGON`). Fields with complex internal holes (e.g. farm buildings excluded from the field interior) or multi-polygons (`MULTIPOLYGON`) have their outer boundary extracted correctly for bounding box calculations, but complex ring styling will be enhanced in Phase 9.

### 3. Client-Side Offline Raster Caching
- While browser HTTP caching stores downloaded PNG tiles (`Cache-Control: 86400`), there is currently no service-worker-based offline map store for farmers in remote fields with zero internet connectivity. This is targeted for Phase 9 progressive web app (PWA) development.

### 4. Vector Tile Polygons for High-Density Farm Catalogs
- When displaying thousands of fields simultaneously across an entire district, vector tiles (`.pbf` via MapLibre) will be more efficient than GeoJSON. Phase 8 uses GeoJSON because operations are scoped to individual selected farms and fields.
