# Spectral Band Mapping & Sensor Identification — Phase 7

## 1. Why Band Mapping is Required
Unlike standard RGB consumer images where Band 1 is Red, Band 2 is Green, and Band 3 is Blue, agricultural drone sensors **do not adhere to a single universal band arrangement**:

| Sensor Hardware | Band 1 | Band 2 | Band 3 | Band 4 | Band 5 |
|---|---|---|---|---|---|
| **DJI P4 Multispectral** | Blue | Green | Red | RedEdge | NIR |
| **MicaSense RedEdge-P** | Blue | Green | Red | RedEdge | NIR |
| **Parrot Sequoia** | Green | Red | RedEdge | NIR | — |
| **Consumer RGB Drone** | Red | Green | Blue | — | — |

If an algorithm blindly assumes Band 1 is Red and Band 2 is NIR, calculating NDVI on a DJI P4 Multispectral image would calculate `(Green - Blue) / (Green + Blue)` instead of `(NIR - Red) / (NIR + Red)`.

---

## 2. Automated Spectral Detection
When inspecting an orthomosaic raster (`GET /api/v1/algorithms/inspect/{id}`), `RasterAnalyticsService` conducts a multi-level inspection:
1. **Header Metadata & Tags**: Inspects TIFF band descriptions, color interpretations, and sensor tags.
2. **Channel Count Analysis**:
   - $\ge 5$ bands $\to$ Classified as `MULTISPECTRAL` (default: Blue, Green, Red, RedEdge, NIR).
   - $4$ bands $\to$ Classified as `MULTISPECTRAL` (default: Green, Red, RedEdge, NIR).
   - $3$ bands $\to$ Classified as `RGB` (default: Red, Green, Blue).
3. **Wavelength Analysis**: Reads nominal wavelength metadata if embedded by photogrammetry software.

---

## 3. Interactive Mapping & Scientific Gating Rules
The user can review and customize the channel mapping on Page 3 before launching an algorithm run:

1. **Physical Band Uniqueness**: One physical band cannot be assigned to two different spectral roles (e.g., Band 1 cannot be mapped to both NIR and Red).
2. **Index-Specific Requirements**:
   - `NDVI`: Requires `NIR` and `Red`.
   - `NDRE`: Requires `NIR` and `RedEdge`.
   - `GNDVI`: Requires `NIR` and `Green`.
   - `SAVI`: Requires `NIR` and `Red`.
   - `VARI` / `GLI`: Require `Green`, `Red`, and `Blue`.
3. **RGB-Only Guard**: If Near-Infrared is not mapped, all multispectral indices are locked in the UI and rejected by the API with an explicit explanation:
   > *"Near-Infrared (NIR) band is NOT assigned. Standard 3-band RGB imagery lacks the physical Near-Infrared reflectance required for genuine NDVI, NDRE, GNDVI, or SAVI calculations. All NIR algorithms are locked."*
4. **RedEdge Guard**: If RedEdge is not mapped:
   > *"NDRE cannot be generated because this dataset does not contain a validated RedEdge band (705-745nm)."*
