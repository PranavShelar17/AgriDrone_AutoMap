# Layer Management & Dynamic Legends

## 1. Overview
Agricultural mapping requires fluid switching between different optical and spectral views of the same crop canopy. Phase 8 provides an integrated layer management interface and dynamic color ramp legend system that accurately depicts index values without misleading color stretches.

---

## 2. Layer Controls & Interactivity

The MapLibre viewer provides comprehensive layer manipulation tools:

### Controls Matrix:
- **Product Switching**: Radio selectors switch between Orthophotos, NDVI, NDRE, GNDVI, SAVI, VARI, GLI, and DSM without page reloads.
- **Layer Visibility Toggle**: `Eye` button toggles layer visibility (`map.setLayoutProperty(id, 'visibility', 'visible' | 'none')`) without destroying the underlying WebGL texture.
- **Continuous Opacity Slider**: Smooth 0% to 100% alpha blending (`map.setPaintProperty(id, 'raster-opacity', opacity)`), allowing users to blend vegetation stress overlays with underlying RGB imagery or basemaps.
- **Fit Extent**: Centers and zooms the viewport to the exact bounding box of the field boundary or raster product.
- **Point Probe Badge**: Interactive click-to-probe displays continuous spectral values, coordinates, and classification descriptors in a floating, dismissible HUD badge.

---

## 3. Standardized Remote Sensing Color Ramps

Color ramps are scientifically calibrated to reflect biophysical vegetation characteristics:

### A. Normalized Difference Indices (NDVI, NDRE, SAVI, VARI, GLI)
- **Ramp**: Red $\rightarrow$ Yellow $\rightarrow$ Green (`RdYlGn`)
- **Range**: Continuous $[-1.0, 1.0]$

| Value Interval | Color Hex | Visual Description | Agronomic / Biophysical Meaning |
|---|---|---|---|
| $< 0.0$ | `#a50026` / `#d73027` | Deep Red | Water bodies, shadows, inorganic matter |
| $0.0 - 0.20$ | `#fc8e59` | Orange-Red | Bare soil, dry crop residue, non-vegetated |
| $0.20 - 0.40$ | `#fee08b` | Yellow | Sparse canopy, stressed vegetation, early emergence |
| $0.40 - 0.60$ | `#d9ef8b` | Yellow-Green | Moderate vegetative vigour, intermediate canopy |
| $0.60 - 0.80$ | `#91cf60` | Light Green | High photosynthetic vigour, active vegetative growth |
| $> 0.80$ | `#1a9850` / `#006837` | Forest Green | Dense canopy, peak chlorophyll absorption |

### B. Green Normalized Difference Vegetation Index (GNDVI)
- **Ramp**: Perceptually uniform `Viridis` (Purple $\rightarrow$ Blue $\rightarrow$ Teal $\rightarrow$ Green $\rightarrow$ Yellow)
- **Rationale**: Enhanced sensitivity to chlorophyll concentrations in dense, closed-canopy crops where standard red absorption saturates.

### C. Digital Surface / Terrain Models (DSM, DTM)
- **Ramp**: Hypsometric `Terrain` gradient (Blue $\rightarrow$ Green $\rightarrow$ Yellow $\rightarrow$ Orange $\rightarrow$ Red)
- **Scale**: Dynamically calibrated between the minimum and maximum surface elevation detected within the valid raster footprint (in meters above sea level).

### D. RGB True Color Orthomosaics
- **Channels**: Standard Red (Band 1), Green (Band 2), Blue (Band 3).
- **Legend**: Classified as "True Color Imagery" with tonal ranges rather than numeric index intervals.

---

## 4. NoData Transparency Indicator
In drone analytics, areas outside the survey footprint, flight boundaries, or masked clouds must never be confused with bare soil or zero values. All legends feature an explicit **NoData Indicator** with a diagonal checkerboard pattern indicating 100% transparency.
