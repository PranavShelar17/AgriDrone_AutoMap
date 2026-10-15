# Raster Validation, Alignment & Georeferencing — Phase 7

## 1. Input Raster Integrity Checks
Before any spectral mathematical calculation begins, the input dataset is subjected to rigorous geospatial verification:

1. **Existence and Readability**: Verifies the file is accessible in storage and can be parsed by Rasterio/GDAL.
2. **Band Count Verification**: Ensures the dataset possesses sufficient channels for the requested algorithms.
3. **Coordinate Reference System (CRS)**:
   - Verifies the raster contains a recognized spatial reference (e.g., Projected UTM EPSG:32643 or Geographic EPSG:4326).
   - Rejects unreferenced local arbitrary coordinate files without geospatial anchors.
4. **Affine Geotransform**: Confirms valid 6-element affine coefficients `(a, b, c, d, e, f)` defining pixel dimensions and upper-left coordinates.
5. **Dimensions & Extents**: Confirms consistent row/column geometry across all spectral channels.

---

## 2. Band Alignment Within Multi-Band Rasters
In AgriDrone AutoMap:
- When processing reconstructed orthophotos from WebODM (Phase 6) or pre-stitched multi-band GeoTIFFs (Phase 5), all spectral channels are already co-registered into a single multi-band raster container.
- This guarantees that pixel `(row, col)` in Band 1 physically corresponds to the identical geographic point on the ground as pixel `(row, col)` in Band 5.
- Combining bands from unrelated survey flights or disparate timestamps is strictly prohibited.

---

## 3. Output GeoTIFF Independent Verification
After writing an index GeoTIFF, `RasterAnalyticsService.validate_output_geotiff()` re-opens the file from disk and executes:

1. **Single-Band Verification**: Ensures count is exactly 1.
2. **Data Type Verification**: Confirms pixel data type is `float32`.
3. **NoData Verification**: Verifies NoData value is `-9999.0`.
4. **NaN & Infinity Audit**: Re-checks for any stray unmasked `NaN` or `inf` values. If found, the product is rejected.
5. **Dynamic Range Plausibility**: Validates that calculated normalized difference values lie within expected numerical boundaries (e.g., $[-1.0, 1.0]$ for NDVI/NDRE, $[-1.5, 1.5]$ for SAVI).
