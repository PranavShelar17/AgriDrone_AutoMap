# Raster Visualization & Delivery Architecture

## 1. Overview
Drone orthomosaics and multispectral index rasters can range from hundreds of megabytes to several gigabytes in size. Transmitting raw GeoTIFF files directly to client browsers introduces extreme bandwidth overhead, slow page rendering, and browser tab memory crashes.

AgriDrone AutoMap solves this through a **server-side dynamic XYZ Slippy Tile Engine** powered by FastAPI, Rasterio, GDAL, NumPy, and Pillow.

---

## 2. Dynamic Slippy Tile Server (`/api/v1/maps/tiles/{product_id}/{z}/{x}/{y}.png`)

### Slippy Tile Coordinate Pipeline:
1. **Request Reception**: The browser requests a standard 256x256 Web Mercator tile at zoom level `z`, column `x`, and row `y`.
2. **Bounding Box Calculation**:
   $$\text{Span} = \frac{2 \times 20037508.342789244}{2^z}$$
   $$\text{min}_x = -20037508.342789244 + x \times \text{Span}$$
   $$\text{max}_x = -20037508.342789244 + (x + 1) \times \text{Span}$$
   $$\text{max}_y = 20037508.342789244 - y \times \text{Span}$$
   $$\text{min}_y = 20037508.342789244 - (y + 1) \times \text{Span}$$
3. **Spatial Intersection Gate**: The tile bounding box in EPSG:3857 is compared against the raster's projected bounds. If disjoint, a pre-compiled transparent 256x256 PNG is returned in under **0.1 ms** without reading any disk blocks.
4. **Windowed Reprojection**:
   Using `rasterio.warp.reproject`, only the intersecting sub-window of the GeoTIFF is read, reprojected, and resampled directly into a 256x256 NumPy array.
5. **Color Ramp Application**:
   - Single-band floating point arrays (e.g. NDVI between -1.0 and +1.0) are mapped through continuous piecewise color stops.
   - Elevation models (DSM/DTM) are dynamically scaled between dataset min and max values.
   - Orthophotos stream multi-band RGB channels directly.
6. **NoData Alpha Masking**:
   Pixels with value `-9999.0`, non-finite values (NaN/Inf), or outside the field polygon receive an alpha channel of `0` (100% transparent). Valid canopy pixels receive alpha `255`.
7. **Streaming & Caching**:
   The resulting RGBA image is compressed to PNG and served with `Cache-Control: public, max-age=86400`.

---

## 3. Layer Visualization Metadata (`/api/v1/maps/layers/{product_id}/visualization`)
Before rendering, MapLibre requests layer metadata to configure zoom extents and legends:

```json
{
  "product_id": "9b2bbe1c-1025-4e9b-a127-a54341838530",
  "product_type": "INDEX_NDVI",
  "survey_id": "46b6c986-2484-4207-997a-c4f01016ad39",
  "crs_epsg": "EPSG:32643",
  "is_cog": true,
  "bounds": [77.43163, 22.58841, 77.43166, 22.58844],
  "center": [77.43165, 22.58842],
  "tile_url_template": "/api/v1/maps/tiles/9b2bbe1c-1025-4e9b-a127-a54341838530/{z}/{x}/{y}.png",
  "legend": {
    "title": "Normalized Difference Vegetation Index (NDVI)",
    "unit": "dimensionless",
    "colormap_type": "CONTINUOUS",
    "min_value": -1.0,
    "max_value": 1.0,
    "stops": [...]
  }
}
```

---

## 4. Interactive Point Value Probing (`/api/v1/maps/products/{product_id}/probe`)
When a farmer or agronomist clicks anywhere on the MapLibre map:
1. MapLibre captures the clicked geographic coordinate `(lat, lon)` in WGS84.
2. The coordinate is sent to the backend probing endpoint.
3. The backend reprojects the coordinate into the raster's native projection (e.g., UTM Zone 43N).
4. `src.index(x, y)` computes the exact row and column pixel offset.
5. A 1x1 raster window is read using `rasterio.windows.Window`.
6. The exact unrounded scientific index value (e.g. `NDVI = 0.7949`) is returned in real time.
