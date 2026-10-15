# Raster Statistics & Diagnostics Architecture

## 1. Overview
Agronomic diagnostics in AgriDrone AutoMap are grounded strictly in validated raster statistics and biophysical canopy reflectance distributions. Phase 8 exposes descriptive, data-derived metrics on Page 5, eliminating placeholder values and fabricated crop claims.

---

## 2. Statistical Pipeline & Pixel Filtering

When raster analytics run in Phase 7, pixel values are computed and stored in the `MapProduct.statistical_summary` JSONB column and the `zonal_statistics` relational table.

### Pixel Filtering Safeguards:
1. **NoData Masking**:
   - Every input raster's NoData value (standard `-9999.0` or source-defined) is explicitly masked out.
   - Pixels outside the flight footprint or cloud-masked regions are never counted in canopy statistics.
2. **NaN and Infinite Removal**:
   - `np.isfinite(data)` guards against mathematical artifacts from band division.
3. **Exact Coverage Ratio**:
   $$\text{Coverage Percentage} = \frac{\text{Valid Pixels}}{\text{Valid Pixels} + \text{NoData Pixels}} \times 100$$
4. **Hectare Area Computation**:
   Ground area is computed directly from spatial resolution (GSD):
   $$\text{Area (ha)} = \frac{\text{Pixel Count} \times \text{GSD}_x \times \text{GSD}_y}{10,000}$$
   If projected in meters (e.g., UTM Zone 43N), exact square meters are converted to hectares.

---

## 3. Zonal Canopy Vigour Distribution
Vegetation indices are classified into four scientifically documented analytical zones:

| Zone Classification | Index Interval (NDVI/NDRE) | Color Token | Interpretation Rationale |
|---|---|---|---|
| **Non-Vegetated / Bare Soil** | $[-1.000, 0.200]$ | `#d73027` | Bare ground, rocks, standing water, non-photosynthetic matter |
| **Low Vigour** | $[0.200, 0.400]$ | `#fee08b` | Sparse emergent canopy, moisture/nutrient stress, or weed-controlled gaps |
| **Moderate Vigour** | $[0.400, 0.600]$ | `#d9ef8b` | Standard vegetative growth, intermediate biomass density |
| **High Vigour** | $[0.600, 1.000]$ | `#1a9850` | Dense, highly active photosynthetic canopy with peak chlorophyll absorption |

The database maintains exact hectare measurements and percentage distributions for each zone, displayed on Page 5 as color-coded progress bars.

---

## 4. Diagnostics API Endpoint (`/api/v1/maps/products/{product_id}/diagnostics`)
```json
{
  "product_id": "9b2bbe1c-1025-4e9b-a127-a54341838530",
  "product_type": "INDEX_NDVI",
  "display_name": "Normalized Difference Vegetation Index (NDVI)",
  "survey_code": "SRV-TEST-bc9ece",
  "field_name": "Field North",
  "farm_name": "Test Spectral Farm",
  "crs_epsg": "EPSG:32643",
  "valid_pixel_count": 4096,
  "nodata_pixel_count": 0,
  "total_pixel_count": 4096,
  "valid_percentage": 100.0,
  "covered_area_hectares": 0.0102,
  "min_value": 0.0323,
  "max_value": 0.7949,
  "mean_value": 0.7763,
  "std_value": 0.1177,
  "median_value": 0.7949,
  "unit": "dimensionless",
  "zonal_distribution": [
    {
      "zone_name": "Non-Vegetated / Bare Soil",
      "min_val": -1.0,
      "max_val": 0.2,
      "area_hectares": 0.0002,
      "area_percentage": 2.15,
      "color": "#d73027"
    },
    {
      "zone_name": "High Vigour",
      "min_val": 0.6,
      "max_val": 1.0,
      "area_hectares": 0.0098,
      "area_percentage": 96.12,
      "color": "#1a9850"
    }
  ],
  "scientific_warnings": [
    "This raster contains 100.0% valid pixels.",
    "Statistics strictly exclude 0 NoData/masked pixels."
  ],
  "analytical_limitations": [
    "Vegetation indices measure canopy greenness, reflectance, and chlorophyll absorption, not direct crop disease.",
    "Variations in index values may be caused by soil background, canopy architecture, shadowing, irrigation, or growth stage.",
    "Do not apply fertilizers, pesticides, or agronomic treatments based solely on remote sensing map layers without ground-truthing."
  ]
}
```
