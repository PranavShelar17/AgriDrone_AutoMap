# Known Limitations & Scientific Disclosures — Phase 7

## 1. Data & Sensor Disclosures
1. **Synthetic vs Real Drone Data**:
   - Automated tests in Phase 7 utilize deterministic synthetic multi-band GeoTIFF rasters with known floating-point numbers.
   - When real drone multispectral data is ingested in production, index calculations will execute identically through the verified pipeline, but cross-sensor calibration requires pre-flight panel calibration.
2. **RGB-Only Imagery**:
   - Standard consumer RGB drone cameras lack physical Near-Infrared (NIR) and RedEdge sensors.
   - Genuine NDVI, NDRE, GNDVI, and SAVI cannot be computed from RGB images. VARI and GLI are provided as visible-light alternatives.
3. **Uncalibrated Digital Numbers**:
   - When reflectance panel images or irradiance sensor metadata are missing, calculations represent relative optical contrasts rather than absolute surface reflectance.

---

## 2. Deferred Functionality (Scope Boundaries)
1. **Interactive Layer Comparison & Map Visualization**:
   - Reserved strictly for **Phase 8** (MapLibre GL JS multi-layer viewer, split-screen swipe, and dynamic raster styling).
2. **Disease & Yield Diagnosis**:
   - In accordance with the system design, Phase 7 generates spectral indicator rasters only. No unvalidated crop health diagnoses, disease classifications, or fertilizer prescriptions are produced.
3. **Production Authentication & Farmer Portal**:
   - Reserved for **Phase 9**.
