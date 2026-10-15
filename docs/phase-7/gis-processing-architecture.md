# GIS Processing Architecture — Phase 7

## 1. Architectural Overview
The AgriDrone AutoMap Phase 7 GIS engine processes large geospatial rasters (drone orthomosaics, multispectral flight products, and pre-stitched GeoTIFFs) using a decoupled, asynchronous, pipeline-driven architecture.

```
                    ┌─────────────────────────────────────────┐
                    │ Next.js Admin UI: Algorithm & Multi-Map │
                    └───────────────────┬─────────────────────┘
                                        │ HTTP / JSON
                                        ▼
                    ┌─────────────────────────────────────────┐
                    │ FastAPI Endpoints: /api/v1/algorithms   │
                    └───────────────────┬─────────────────────┘
                                        │ 202 Accepted (Batch ID)
                                        ▼
                    ┌─────────────────────────────────────────┐
                    │ Redis Broker / Celery Task Dispatcher   │
                    │ (Fallback: Background Thread Pool)      │
                    └───────────────────┬─────────────────────┘
                                        │ Asynchronous Job Run
                                        ▼
 ┌───────────────────────────────────────────────────────────────────────────┐
 │ Background Task: execute_algorithm_batch_workflow                         │
 │                                                                           │
 │  1. Resolve & Stream Source Raster (Azure Blob Storage or Local Dev)      │
 │  2. Rasterio Inspection: CRS, Affine Transform, Dimensions, Bands, NoData │
 │  3. Spectral Channel Mapping Validation & Sensor Gating                   │
 │  4. Pure NumPy Mathematical Array Computation (NDVI, NDRE, GNDVI, SAVI)   │
 │  5. Numerical Safeguards: Zero-division masking, NoData propagation       │
 │  6. Write Cloud-Optimized GeoTIFF (Deflate, Predictor=3, Tiled 256x256)   │
 │  7. Output GeoTIFF Re-open Verification (Independent Check)               │
 │  8. 4-Zone Agronomic Vigour Statistics Calculation (Hectares & %)         │
 │  9. Upload Resulting Index Raster to `vegetation-indices` Container       │
 │ 10. Register Database Records: MapProduct & ZonalStatistic                │
 │ 11. Update AlgorithmJob to COMPLETED / FAILED                             │
 └───────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Core Architectural Components

### A. Rasterio & GDAL Integration
- **Rasterio 1.5.2** is utilized for high-performance reading and writing of geospatial GeoTIFFs.
- Reads source bands selectively into 2D `np.float32` arrays without unnecessarily reading unused channels into RAM.
- Copies geospatial metadata directly from the source:
  - Coordinate Reference System (CRS)
  - 6-element Affine transformation matrix `[a, b, c, d, e, f]`
  - Spatial pixel resolution
  - Geographic bounding box

### B. Pure NumPy Vectorized Array Operations
- All spectral calculations execute over vectorized 2D NumPy arrays using `float32` precision.
- Safeguards against memory bloat and floating-point overflow.
- Eliminates Python-level pixel iteration loops, computing millions of pixels in fractions of a second.

### C. Cloud-Optimized GeoTIFF (COG) Output Format
All generated index maps are formatted as Cloud-Optimized GeoTIFFs:
- **Tiling**: 256×256 block size allows MapLibre and GIS clients to fetch only visible tiles rather than downloading the entire file.
- **Compression**: Deflate compression with predictor=3 (floating-point horizontal differencing) achieves maximum lossless compression ratio for continuous vegetation indices.
- **Metadata Embedding**: Custom GeoTIFF tags (`ALGORITHM`, `FORMULA`, `PARAMETERS`, `BAND_MAPPING`, `PROCESSED_AT`, `SOFTWARE`) are directly written to the TIFF header for full provenance tracking.

### D. Asynchronous Worker Lifecycle & State Transitions
Jobs advance through deterministic status transitions:
1. `QUEUED`: Job record persisted in PostgreSQL; task enqueued to Redis.
2. `PREPARING`: Worker downloaded/resolved source raster file on disk.
3. `VALIDATING`: Source metadata and spectral channel mappings validated.
4. `RUNNING`: Spectral bands loaded and mathematical array computation underway.
5. `STORING`: Cloud-Optimized GeoTIFF written, verified, and uploaded to storage.
6. `COMPLETED`: MapProduct and ZonalStatistic records saved; progress is 100%.
7. `FAILED`: Terminal failure recorded with explicit, user-friendly diagnostic message.
