# Output Products, Storage & Provenance Metadata — Phase 7

## 1. Output Deliverables
Every successful index algorithm produces:
1. **Cloud-Optimized GeoTIFF (COG)**:
   - Single-band `float32`.
   - Lossless Deflate compression (`predictor=3`).
   - Tiled in 256×256 pixel blocks.
   - Preserves source CRS, Affine transform, and spatial resolution.
2. **`MapProduct` Record in Database**:
   - `product_type`: e.g., `INDEX_NDVI`, `INDEX_NDRE`, `INDEX_GNDVI`, `INDEX_SAVI`.
   - `blob_uri`: Storage path in `vegetation-indices` container.
   - `statistical_summary`: Complete JSONB statistical digest and provenance chain.
3. **`ZonalStatistic` Records**:
   - 4 rows representing standard agronomic canopy vigour zones.

---

## 2. Statistical Summary & Provenance Schema
Each generated `MapProduct` stores a JSONB `statistical_summary` structured as follows:

```json
{
  "min": 0.0452,
  "max": 0.8124,
  "mean": 0.5231,
  "std": 0.1642,
  "median": 0.5480,
  "p10": 0.2810,
  "p90": 0.7250,
  "valid_pixels": 3845200,
  "nodata_pixels": 254800,
  "total_pixel_count": 4100000,
  "valid_percentage": 93.79,
  "file_size_bytes": 14285020,
  "provenance": {
    "source_product_id": "ab123456-7890-abcd-ef01-234567890abc",
    "source_blob_uri": "azure://orthomosaics/surveys/101/orthophoto.tif",
    "algorithm": "NDVI",
    "formula": "(NIR - Red) / (NIR + Red)",
    "parameters": {},
    "band_mapping": {"NIR": 5, "Red": 3, "Green": 2, "Blue": 1},
    "radiometric_type": "DIGITAL_NUMBERS_16BIT",
    "calibration_notes": [
      "Values appear to be 16-bit uncalibrated Digital Numbers (DN). Index formulas computed from relative numbers."
    ],
    "processed_at": "2026-10-15T10:45:00Z"
  }
}
```

---

## 3. Zonal Vigour Classification Schema
Each generated product generates 4 zonal classification records in `zonal_statistics`:

| Zone Name | Value Range | Agronomic Meaning |
|---|---|---|
| **Water / Non-vegetated** | $[-1.0, 0.10)$ | Standing water, soil shadows, bare roads |
| **Bare Soil / Sparse Vegetation** | $[0.10, 0.25)$ | Exposed dry soil, very early crop emergence |
| **Moderate Canopy Vigour** | $[0.25, 0.50)$ | Developing vegetative canopy, intermediate density |
| **Dense / High Vigour** | $[0.50, 1.00]$ | Closed canopy, peak vegetative biomass |

Each zone record tracks:
- `zone_name`: string
- `min_val` & `max_val`: float
- `area_hectares`: float (derived from pixel resolution: `count * (res_m^2) / 10000`)
- `area_percentage`: float (`(zone_pixels / valid_pixels) * 100.0`)
