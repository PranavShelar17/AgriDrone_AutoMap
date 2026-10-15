# Multi-Map Generation Workflow — Phase 7

## 1. Overview
A single multispectral drone flight dataset can yield multiple distinct spatial analytics products. For example, a 5-band DJI P4 Multispectral orthophoto can simultaneously generate:
1. **NDVI Map**: Baseline crop vigour and canopy coverage.
2. **NDRE Map**: High-biomass chlorophyll concentration.
3. **GNDVI Map**: Photosynthetic greenness and early senescence detection.
4. **SAVI Map**: Soil-adjusted vegetation index for early emergence.

The Phase 7 Multi-Map Generation Workflow allows an administrator to trigger all compatible indices in a single request.

---

## 2. End-to-End Processing Steps

```
[User Selects Dataset & Indices on Page 3]
                   │
                   ▼
[POST /api/v1/algorithms/jobs (202 Accepted)]
                   │
                   ├──> Creates batch_id (UUID)
                   ├──> Persists individual AlgorithmJob records
                   └──> Dispatches background worker
                                   │
                                   ▼
                [Asynchronous Batch Execution]
                   │
                   ├── Step 1: Pre-flight raster file resolution
                   ├── Step 2: Validate spectral channels per algorithm
                   ├── Step 3: Compute mathematical index arrays
                   ├── Step 4: Calculate 4-zone vigour stats
                   ├── Step 5: Write Cloud-Optimized GeoTIFFs
                   ├── Step 6: Validate output rasters
                   ├── Step 7: Upload to storage container
                   └── Step 8: Register MapProduct & ZonalStatistic records
                                   │
                                   ▼
                [Live Status Polling & Delivery]
                   │
                   └──> GET /api/v1/algorithms/batches/{id}
```

---

## 3. Partial Success & Failure Isolation
When multiple algorithms are selected in a single batch:
- Each algorithm executes in its own transaction block.
- If one algorithm fails (for example, NDRE fails because RedEdge was not mapped), other valid algorithms (NDVI and SAVI) continue to process and succeed.
- The overall batch status is reported accurately as `PARTIALLY_COMPLETED`.
- The system never falsely reports that all products succeeded if only a subset was generated.
