# AgriDrone AutoMap — GIS & Raster Processing Architecture
## Document Reference: `docs/phase-3/gis-processing-architecture.md`
**Phase**: Phase 3 — System Architecture, Technical Validation & Implementation Blueprint  
**Status**: APPROVED ARCHITECTURE BLUEPRINT  
**Version**: 1.0.0  

---

## 1. Geospatial Processing Principles

AgriDrone AutoMap utilizes **GDAL 3.8+**, **Rasterio 1.3+**, and **NumPy** for all raster manipulation and vegetation index calculations.

### Core Geospatial Axioms:
1. **Never Assume Band Ordering**: Spectral band sequence cannot be reliably inferred from a filename alone. Band mapping must be validated via GeoTIFF metadata tags or explicitly mapped by an administrator prior to calculation.
2. **Scientific Integrity Guardrail**: Genuine vegetation indices (NDVI, NDRE, GNDVI, SAVI) physically require Near-Infrared (NIR) reflectance. Generating NDVI from an ordinary 3-band RGB camera produces mathematically meaningless results. The system strictly disables NIR indices when RGB input is detected, offering valid visible-spectrum alternatives (VARI, GLI, TGI).
3. **NoData & Divide-by-Zero Protection**: All mathematical expressions strictly protect against zero denominators and propagate NoData / alpha masks.
4. **Cloud-Optimized GeoTIFF (COG) Delivery**: All derived raster products are formatted as Cloud-Optimized GeoTIFFs (tiled $256 \times 256$, internal pyramid overviews, Deflate/LZW compression) to enable streaming web visualization.

---

## 2. Inbound Raster Validation Pipeline

Before any uploaded raster (GeoTIFF) is accepted into the processing queue, the worker executes the multi-stage validation pipeline:

```
[Inbound GeoTIFF Blob]
       │
       ▼ Stage 1: File Integrity & Format Check
[Rasterio Header Read] ──► Valid GeoTIFF / BigTIFF? (Fail if corrupt)
       │
       ▼ Stage 2: Georeferencing Verification
[Affine Geotransform & CRS] ──► Non-zero transform? Valid EPSG? (Fail if unreferenced)
       │
       ▼ Stage 3: Spectral Band Inspection
[Band Count & Data Types] ──► Read band count, color interpretations, bit depth
       │
       ▼ Stage 4: Cloud-Optimized Tiling Check
[Tiling & Overviews Check] ──► If not COG, schedule background GDAL tiling
       │
       ▼ Stage 5: PostGIS Footprint Registration
[Extract Extent Polygon] ──► Reproject bounding box to EPSG:4326 & save to DB
```

### Detailed Validation Rules:
- **CRS Check**: Must possess a valid Coordinate Reference System. If provided in a local projected coordinate system (e.g. UTM Zone 43N - `EPSG:32643`), the footprint is reprojected to WGS84 (`EPSG:4326`) for PostGIS indexing and MapLibre alignment.
- **Data Type Normalization**: Aerial sensor inputs commonly arrive as 8-bit unsigned integers (`uint8` [0–255]) or 16-bit integers (`uint16` [0–65535]). The processing pipeline normalizes raw digital numbers (DN) to normalized surface reflectance floats in the range `[0.0, 1.0]` before applying index formulas.

---

## 3. Approved Vegetation Index Mathematical Formulas

| Index Code | Index Name | Required Sensor Channels | Mathematical Formula | Valid Output Range | Agronomic Significance |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **NDVI** | Normalized Difference Vegetation Index | Red (660nm), NIR (840nm) | $\frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red}}$ | $[-1.0, +1.0]$ | Standard measure of photosynthetic activity and biomass density. |
| **NDRE** | Normalized Difference Red Edge Index | RedEdge (705nm), NIR (840nm) | $\frac{\text{NIR} - \text{RedEdge}}{\text{NIR} + \text{RedEdge}}$ | $[-1.0, +1.0]$ | Sensitive to chlorophyll content in dense, mature canopies; resists saturation. |
| **GNDVI** | Green Normalized Difference Vegetation Index | Green (560nm), NIR (840nm) | $\frac{\text{NIR} - \text{Green}}{\text{NIR} + \text{Green}}$ | $[-1.0, +1.0]$ | Highly sensitive to chlorophyll concentration variations. |
| **SAVI** | Soil-Adjusted Vegetation Index | Red, NIR, $L$-factor | $\frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red} + L} \times (1 + L)$ | $[-1.0, +1.0]$ | Minimizes soil brightness influence in early-stage crops ($L = 0.5$ default). |
| **VARI** | Visible Atmospherically Resistant Index | Red, Green, Blue | $\frac{\text{Green} - \text{Red}}{\text{Green} + \text{Red} - \text{Blue}}$ | $[-1.0, +1.0]$ | Estimates vegetation fraction and greenness using standard RGB drone sensors. |
| **GLI** | Green Leaf Index | Red, Green, Blue | $\frac{2 \times \text{Green} - \text{Red} - \text{Blue}}{2 \times \text{Green} + \text{Red} + \text{Blue}}$ | $[-1.0, +1.0]$ | Effective RGB proxy for canopy cover in smallholder farms. |

---

## 4. NumPy Raster Math Implementation Pattern

The Celery worker processes rasters in windowed memory blocks using `Rasterio` and `NumPy` to prevent out-of-memory errors on massive files (e.g. $20,000 \times 20,000$ pixels):

```python
import numpy as np
import rasterio

def calculate_vari_window(red: np.ndarray, green: np.ndarray, blue: np.ndarray, nodata_mask: np.ndarray) -> np.ndarray:
    """
    Computes Visible Atmospherically Resistant Index (VARI) with zero-division safety.
    Formula: (Green - Red) / (Green + Red - Blue)
    """
    # Cast to float32
    r = red.astype(np.float32)
    g = green.astype(np.float32)
    b = blue.astype(np.float32)

    numerator = g - r
    denominator = g + r - b

    # Create safety mask: exclude zero or near-zero denominators and source NoData
    valid_mask = (np.abs(denominator) > 1e-6) & (~nodata_mask)

    # Pre-allocate output array filled with standard NoData value (-9999.0)
    output = np.full(r.shape, -9999.0, dtype=np.float32)

    # Execute vector math only on valid pixels
    output[valid_mask] = numerator[valid_mask] / denominator[valid_mask]

    # Clip mathematically valid values to the theoretical range [-1.0, 1.0]
    np.clip(output, -1.0, 1.0, out=output, where=valid_mask)

    return output
```

---

## 5. Cloud-Optimized GeoTIFF (COG) Generation Workflow

Once the floating-point index array is calculated, GDAL converts the working raster into a Cloud-Optimized GeoTIFF:

```bash
# Internal tiling and overview pyramid generation
gdal_translate -of COG -co COMPRESS=DEFLATE -co PREDICTOR=2 -co OVERVIEWS=AUTO -co NUM_THREADS=ALL_CPUS temp_index.tif final_vari_cog.tif
```

- **Tile Size**: $256 \times 256$ pixels.
- **Overviews**: Sub-sampled resolution pyramids ($1:2, 1:4, 1:8, 1:16, 1:32$) embedded within the file structure.
- **Streaming Benefit**: When MapLibre requests a specific zoom level or bounding box, HTTP range-requests read only the necessary byte offsets from Azure Blob Storage rather than loading the multi-gigabyte file.

---

## 6. Scientific Provenance & Audit Logging

Every generated map product stores full provenance metadata in the `map_products.statistical_summary` JSONB field:
```json
{
  "algorithm": "VARI",
  "software_stack": {
    "gdal_version": "3.8.4",
    "rasterio_version": "1.3.9",
    "numpy_version": "1.26.4"
  },
  "input_product_id": "prod-101",
  "band_mapping": {
    "red_band": 1,
    "green_band": 2,
    "blue_band": 3
  },
  "pixel_statistics": {
    "valid_pixel_count": 8492010,
    "nodata_pixel_count": 120400,
    "min_value": -0.245,
    "max_value": 0.682,
    "mean_value": 0.441,
    "median_value": 0.458,
    "standard_deviation": 0.124
  },
  "executed_at": "2026-10-14T15:12:00Z"
}
```
