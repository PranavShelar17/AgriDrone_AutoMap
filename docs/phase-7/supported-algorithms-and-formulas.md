# Supported Vegetation Indices & Exact Formulas — Phase 7

## 1. Introduction to Spectral Vegetation Indices
Plants interact with solar radiation in specific wavelengths:
- **Chlorophyll Absorption**: Healthy green leaves absorb blue (~450 nm) and red (~670 nm) light for photosynthesis.
- **Cell Structure Scattering**: The internal mesophyll cell structure strongly scatters and reflects Near-Infrared (NIR, ~750–900 nm) radiation.
- **RedEdge Sensitivity**: The narrow spectral transition zone between red absorption and NIR reflection (~705–745 nm) responds sensitively to chlorophyll variations without saturating in dense canopies.

Spectral indices leverage these physical properties by contrasting absorption and reflection channels.

---

## 2. Algorithm Catalog & Mathematical Formulas

### A. NDVI — Normalized Difference Vegetation Index
- **Formula**:
  $$\text{NDVI} = \frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red}}$$
- **Required Bands**: Near-Infrared (NIR) and Red.
- **Expected Range**: $[-1.0, +1.0]$.
- **Agricultural Purpose**: Standardized baseline indicator of canopy density, fractional ground cover, and relative vegetative vigour.
- **Interpretation & Caveats**: Values from 0.4 to 0.8 typically represent active vegetative growth. However, NDVI tends to saturate in dense, closed canopies (such as mature maize or sugarcane), making fine chlorophyll distinctions difficult at peak biomass.

---

### B. NDRE — Normalized Difference Red Edge
- **Formula**:
  $$\text{NDRE} = \frac{\text{NIR} - \text{RedEdge}}{\text{NIR} + \text{RedEdge}}$$
- **Required Bands**: Near-Infrared (NIR) and RedEdge (~705–745 nm).
- **Expected Range**: $[-1.0, +1.0]$.
- **Agricultural Purpose**: Evaluates chlorophyll concentration and nitrogen uptake in mid-to-late crop development stages.
- **Sensor Gating Rule**: **Strictly locked for RGB-only imagery.** NDRE cannot be generated without a physical RedEdge sensor (e.g. Micasense RedEdge, DJI P4 Multispectral, Parrot Sequoia).

---

### C. GNDVI — Green Normalized Difference Vegetation Index
- **Formula**:
  $$\text{GNDVI} = \frac{\text{NIR} - \text{Green}}{\text{NIR} + \text{Green}}$$
- **Required Bands**: Near-Infrared (NIR) and Green.
- **Expected Range**: $[-1.0, +1.0]$.
- **Agricultural Purpose**: Sensitive to chlorophyll content across a broader dynamic range than NDVI. Useful for detecting early canopy stress, senescence, and water variations.

---

### D. SAVI — Soil-Adjusted Vegetation Index
- **Formula**:
  $$\text{SAVI} = \left( \frac{\text{NIR} - \text{Red}}{\text{NIR} + \text{Red} + L} \right) \times (1 + L)$$
- **Required Bands**: Near-Infrared (NIR), Red, and configurable soil calibration factor $L \in [0.0, 1.0]$.
- **Default Parameter**: $L = 0.5$ (standard default for intermediate canopy cover).
  - $L = 1.0$: Very low vegetation cover / exposed bare soil background.
  - $L = 0.5$: Intermediate vegetative cover.
  - $L = 0.0$: Equivalent to standard NDVI.
- **Expected Range**: $[-1.5, +1.5]$.
- **Agricultural Purpose**: Attenuates soil brightness influences during early crop emergence or sparse plantings (orchards, young seedlings).

---

### E. VARI — Visible Atmospherically Resistant Index
- **Formula**:
  $$\text{VARI} = \frac{\text{Green} - \text{Red}}{\text{Green} + \text{Red} - \text{Blue}}$$
- **Required Bands**: Green, Red, Blue.
- **Expected Range**: $[-1.0, +1.0]$.
- **Agricultural Purpose**: Visible-spectrum vegetation fraction estimator computable from standard consumer RGB drone cameras when NIR sensors are unavailable.

---

### F. GLI — Green Leaf Index
- **Formula**:
  $$\text{GLI} = \frac{2 \times \text{Green} - \text{Red} - \text{Blue}}{2 \times \text{Green} + \text{Red} + \text{Blue}}$$
- **Required Bands**: Green, Red, Blue.
- **Expected Range**: $[-1.0, +1.0]$.
- **Agricultural Purpose**: Distinguishes green canopy leaves from soil, residue, and straw backgrounds using RGB sensors.

---

## 3. Scientific Disclaimers
1. Vegetation indices are relative spectral measurements of optical reflectance.
2. They do **NOT** independently diagnose specific crop diseases (e.g., fungal blight vs viral mosaic).
3. They do **NOT** directly quantify yield or prove nitrogen deficiency without ground-truthed calibration and soil sampling.
