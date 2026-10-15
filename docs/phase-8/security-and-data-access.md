# Security & Data Access Architecture

## 1. Overview
Agricultural raster data, farm boundaries, and flight metadata constitute sensitive commercial and operational assets. Phase 8 adheres strictly to the security architecture established in Phase 3 while preparing for full production authentication in Phase 9.

---

## 2. Server-Mediated Raster Delivery & Secret Isolation

### Private Azure Storage Containers:
- Azure Blob Storage containers (`orthomosaics`, `vegetation-indices`, `reports`) remain strictly **Private** (no public anonymous access).
- Connection strings, storage account keys, and master credentials are kept strictly in backend environment variables (`settings.AZURE_STORAGE_CONNECTION_STRING`).
- Frontend applications never receive raw Azure credentials or long-lived master tokens.

### Protected Slippy Tile Streaming:
- MapLibre does not query Azure Blob Storage directly.
- All tile requests pass through the FastAPI backend (`/api/v1/maps/tiles/{product_id}/{z}/{x}/{y}.png`).
- The backend validates the product UUID, verifies file existence, and streams pixel buffers without exposing storage endpoints or internal directory structures.

---

## 3. Path Traversal & Injection Defenses

### Safe Path Resolution (`MapRenderingService.resolve_local_path`):
- Local storage paths are resolved against `settings.LOCAL_STORAGE_PATH`.
- Path traversal sequences (`../`, `..\\`) and directory manipulation attacks are blocked by strict container and filename sanitization.
- Arbitrary client-provided filenames or untrusted remote URLs cannot be passed to the tile generator; only registered `MapProduct.blob_uri` records from verified database IDs are accessed.

---

## 4. Tenant Boundary Enforcement
- PostGIS boundary endpoints (`/api/v1/maps/fields/{field_id}/boundary`) and product endpoints verify that requested entities belong to the authorized tenant context.
- Cross-tenant queries are blocked at the database query level with 404 responses that prevent information disclosure regarding the existence of other users' fields.
- The UI maintains the Phase 2 Tenant Guard preview mode demonstrating that unauthorized farmer accounts cannot access cross-tenant rasters.
