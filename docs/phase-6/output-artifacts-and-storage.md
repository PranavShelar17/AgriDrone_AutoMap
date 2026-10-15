# AgriDrone AutoMap — Output Artifacts & Storage Specification
## Document Reference: `docs/phase-6/output-artifacts-and-storage.md`
**Phase**: Phase 6 — WebODM / OpenDroneMap Integration & Drone Photogrammetry Processing  
**Status**: APPROVED SPECIFICATION  
**Version**: 1.0.0  

---

## 1. Output Deliverables Inventory

When a WebODM photogrammetry task completes successfully, the worker downloads and registers the resulting raster assets:

| Deliverable Product | Type Code | Typical Format | Bands | Description |
| :--- | :--- | :--- | :--- | :--- |
| **Orthomosaic** | `ORTHOPHOTO` | GeoTIFF (COG) | 3 – 5 bands (RGB / Multispectral) | Georeferenced aerial mosaic stitched with sub-pixel alignment. Input for Phase 7 vegetation algorithms. |
| **Digital Surface Model** | `DSM` | GeoTIFF (Single-band) | 1 band (Elevation in meters) | Top surface elevation including crop canopy heights, structures, and trees. |
| **Digital Terrain Model** | `DTM` | GeoTIFF (Single-band) | 1 band (Bare-earth elevation) | Filtered bare-earth elevation model removing canopy vegetation. |

---

## 2. Storage Strategy & Container Organization

All raster deliverables are stored in the approved object storage hierarchy:

### Azure Blob Storage:
- **Container**: `orthomosaics` (`AZURE_CONTAINER_ORTHO`)
- **Path Pattern**: `{survey_id}/orthophoto_{task_id}.tif`
- **Blob URI**: `https://<account_name>.blob.core.windows.net/orthomosaics/<survey_id>/orthophoto_<task_id>.tif`

### Local Development Fallback:
- **Path Pattern**: `backend/storage/orthomosaics/{survey_id}/orthophoto_{task_id}.tif`
- **URI Schema**: `local://orthomosaics/{survey_id}/orthophoto_{task_id}.tif`

---

## 3. Database Metadata Registration (`map_products` Table)

Every verified deliverable is recorded in the `map_products` table:

```sql
INSERT INTO map_products (
    id,
    survey_id,
    source_task_id,
    product_type,
    blob_uri,
    is_cog,
    band_count,
    crs_epsg,
    resolution_cm_px,
    is_published,
    created_at
) VALUES (
    gen_random_uuid(),
    'c5fa503f-fc6b-413e-b14b-c33752b356af',
    '8f3e29c1-4b1a-4d92-913b-e10c714890a2',
    'ORTHOPHOTO',
    'local://orthomosaics/c5fa503f-fc6b-413e-b14b-c33752b356af/orthophoto_8f3e29c1.tif',
    TRUE,
    3,
    'EPSG:32643',
    2.5,
    FALSE,
    NOW()
);
```

### Verification Rules:
1. **No Phantom Artifacts**: A record is inserted into `map_products` **only after** the file has been successfully downloaded from WebODM and written to storage.
2. **Metadata Integrity**: The GeoTIFF is parsed to extract actual spatial coordinate reference system (CRS e.g. `EPSG:32643`) and number of raster bands.
3. **Publication Control**: All generated artifacts default to `is_published = FALSE`. Only after agronomist approval in Phase 7 are layers published to the Farmer Portal.
